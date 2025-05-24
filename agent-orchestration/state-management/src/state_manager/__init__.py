"""
DORA Compliance Agent State Management System

This module provides a robust state management system for tracking workflow execution,
agent states, and system-wide state with ACID transactions, event sourcing, caching,
and versioning capabilities.
"""

import asyncio
import json
import uuid
import hashlib
import time
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, AsyncIterator, Tuple
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
import pickle
import zlib

# Third-party imports
import asyncpg
import aioredis
import boto3
from prometheus_client import Counter, Histogram, Gauge, Summary
from opentelemetry import trace

# Configure logging
logger = logging.getLogger(__name__)

# Metrics
state_operations = Counter('state_operations_total', 'Total state operations', ['operation', 'entity_type'])
state_operation_duration = Histogram('state_operation_duration_seconds', 'State operation duration', ['operation', 'entity_type'])
cache_hits = Counter('cache_hits_total', 'Cache hits', ['cache_level', 'entity_type'])
cache_misses = Counter('cache_misses_total', 'Cache misses', ['cache_level', 'entity_type'])
transaction_duration = Histogram('transaction_duration_seconds', 'Transaction duration')
lock_wait_time = Histogram('lock_wait_time_seconds', 'Lock wait time')
active_locks = Gauge('active_locks', 'Currently active locks')
state_size = Summary('state_size_bytes', 'Size of state objects', ['entity_type'])

# Get tracer
tracer = trace.get_tracer(__name__)

# ============================================================================
# Core Enums and Data Structures
# ============================================================================

class EntityType(Enum):
    """Types of entities managed by the state system"""
    WORKFLOW = "workflow"
    TASK = "task"
    AGENT = "agent"
    RESOURCE = "resource"
    SYSTEM = "system"

class StateOperation(Enum):
    """Types of state operations"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"

class WorkflowState(Enum):
    """Workflow execution states"""
    CREATED = "created"
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskState(Enum):
    """Task execution states"""
    CREATED = "created"
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class AgentState(Enum):
    """Agent health and availability states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

class LockType(Enum):
    """Types of locks for concurrency control"""
    SHARED = "shared"
    EXCLUSIVE = "exclusive"

@dataclass
class StateChangeEvent:
    """Event representing a state change"""
    event_id: str
    entity_type: EntityType
    entity_id: str
    event_type: str
    timestamp: datetime
    version: int
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    actor: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'entity_type': self.entity_type.value,
            'entity_id': self.entity_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'version': self.version,
            'data': self.data,
            'metadata': self.metadata,
            'actor': self.actor
        }

@dataclass
class VersionInfo:
    """Version information for state entities"""
    version: int
    timestamp: datetime
    checksum: str
    size: int
    actor: str

@dataclass
class LockInfo:
    """Information about acquired locks"""
    lock_id: str
    entity_type: EntityType
    entity_id: str
    lock_type: LockType
    acquired_at: datetime
    expires_at: datetime
    holder: str

class OptimisticLockException(Exception):
    """Exception raised when optimistic locking fails"""
    pass

class PessimisticLockException(Exception):
    """Exception raised when pessimistic locking fails"""
    pass

class StateNotFoundException(Exception):
    """Exception raised when requested state is not found"""
    pass

# ============================================================================
# Storage Interfaces
# ============================================================================

class StateStore(ABC):
    """Abstract interface for state storage"""
    
    @abstractmethod
    async def create(self, entity_type: EntityType, entity_id: str, data: Dict[str, Any], 
                    version: int = 1, actor: str = "system") -> bool:
        """Create new state entity"""
        pass
    
    @abstractmethod
    async def get(self, entity_type: EntityType, entity_id: str, 
                 version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get state entity by ID and optional version"""
        pass
    
    @abstractmethod
    async def update(self, entity_type: EntityType, entity_id: str, data: Dict[str, Any],
                    expected_version: Optional[int] = None, actor: str = "system") -> int:
        """Update state entity with optional optimistic locking"""
        pass
    
    @abstractmethod
    async def delete(self, entity_type: EntityType, entity_id: str, actor: str = "system") -> bool:
        """Delete state entity"""
        pass
    
    @abstractmethod
    async def list_entities(self, entity_type: EntityType, 
                           filters: Optional[Dict[str, Any]] = None,
                           limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List entities with optional filtering"""
        pass
    
    @abstractmethod
    async def get_version_info(self, entity_type: EntityType, entity_id: str) -> List[VersionInfo]:
        """Get version history for entity"""
        pass

class EventStore(ABC):
    """Abstract interface for event storage"""
    
    @abstractmethod
    async def append_event(self, event: StateChangeEvent) -> bool:
        """Append event to the event log"""
        pass
    
    @abstractmethod
    async def get_events(self, entity_type: EntityType, entity_id: str,
                        from_version: int = 0, to_version: Optional[int] = None) -> List[StateChangeEvent]:
        """Get events for entity within version range"""
        pass
    
    @abstractmethod
    async def get_events_by_time(self, entity_type: EntityType, entity_id: str,
                               from_time: datetime, to_time: Optional[datetime] = None) -> List[StateChangeEvent]:
        """Get events for entity within time range"""
        pass

class CacheStore(ABC):
    """Abstract interface for caching"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached value with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass

class LockStore(ABC):
    """Abstract interface for distributed locking"""
    
    @abstractmethod
    async def acquire_lock(self, entity_type: EntityType, entity_id: str,
                          lock_type: LockType, ttl: int = 300, holder: str = "unknown") -> Optional[str]:
        """Acquire a lock, returns lock_id if successful"""
        pass
    
    @abstractmethod
    async def release_lock(self, lock_id: str) -> bool:
        """Release a lock"""
        pass
    
    @abstractmethod
    async def refresh_lock(self, lock_id: str, ttl: int = 300) -> bool:
        """Refresh lock TTL"""
        pass
    
    @abstractmethod
    async def check_lock(self, entity_type: EntityType, entity_id: str) -> Optional[LockInfo]:
        """Check if entity is locked"""
        pass

# ============================================================================
# PostgreSQL Implementation
# ============================================================================

class PostgreSQLStateStore(StateStore):
    """PostgreSQL implementation of state storage"""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool
        
    async def create(self, entity_type: EntityType, entity_id: str, data: Dict[str, Any], 
                    version: int = 1, actor: str = "system") -> bool:
        """Create new state entity"""
        with tracer.start_as_current_span("state_store_create") as span:
            span.set_attribute("entity_type", entity_type.value)
            span.set_attribute("entity_id", entity_id)
            
            try:
                serialized_data = json.dumps(data, default=str)
                checksum = hashlib.sha256(serialized_data.encode()).hexdigest()
                
                async with self.pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO state_entities (
                            entity_type, entity_id, version, data, checksum, 
                            created_at, updated_at, actor
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, entity_type.value, entity_id, version, serialized_data, 
                         checksum, datetime.utcnow(), datetime.utcnow(), actor)
                
                state_operations.labels(operation="create", entity_type=entity_type.value).inc()
                state_size.labels(entity_type=entity_type.value).observe(len(serialized_data))
                
                logger.debug(f"Created {entity_type.value} entity {entity_id} version {version}")
                return True
                
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Failed to create {entity_type.value} entity {entity_id}: {e}")
                return False
    
    async def get(self, entity_type: EntityType, entity_id: str, 
                 version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get state entity by ID and optional version"""
        with tracer.start_as_current_span("state_store_get") as span:
            span.set_attribute("entity_type", entity_type.value)
            span.set_attribute("entity_id", entity_id)
            span.set_attribute("version", version or "latest")
            
            try:
                async with self.pool.acquire() as conn:
                    if version is not None:
                        row = await conn.fetchrow("""
                            SELECT data, version, checksum, updated_at, actor
                            FROM state_entities 
                            WHERE entity_type = $1 AND entity_id = $2 AND version = $3
                        """, entity_type.value, entity_id, version)
                    else:
                        row = await conn.fetchrow("""
                            SELECT data, version, checksum, updated_at, actor
                            FROM state_entities 
                            WHERE entity_type = $1 AND entity_id = $2 
                            ORDER BY version DESC LIMIT 1
                        """, entity_type.value, entity_id)
                
                if row:
                    data = json.loads(row['data'])
                    data['_version'] = row['version']
                    data['_checksum'] = row['checksum']
                    data['_updated_at'] = row['updated_at'].isoformat()
                    data['_actor'] = row['actor']
                    
                    state_operations.labels(operation="read", entity_type=entity_type.value).inc()
                    return data
                
                state_operations.labels(operation="read_miss", entity_type=entity_type.value).inc()
                return None
                
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Failed to get {entity_type.value} entity {entity_id}: {e}")
                return None
    
    async def update(self, entity_type: EntityType, entity_id: str, data: Dict[str, Any],
                    expected_version: Optional[int] = None, actor: str = "system") -> int:
        """Update state entity with optional optimistic locking"""
        with tracer.start_as_current_span("state_store_update") as span:
            span.set_attribute("entity_type", entity_type.value)
            span.set_attribute("entity_id", entity_id)
            span.set_attribute("expected_version", expected_version or "any")
            
            try:
                serialized_data = json.dumps(data, default=str)
                checksum = hashlib.sha256(serialized_data.encode()).hexdigest()
                
                async with self.pool.acquire() as conn:
                    async with conn.transaction():
                        # Get current version
                        current_row = await conn.fetchrow("""
                            SELECT version FROM state_entities 
                            WHERE entity_type = $1 AND entity_id = $2 
                            ORDER BY version DESC LIMIT 1
                        """, entity_type.value, entity_id)
                        
                        if not current_row:
                            raise StateNotFoundException(f"Entity {entity_type.value}:{entity_id} not found")
                        
                        current_version = current_row['version']
                        
                        # Check optimistic lock
                        if expected_version is not None and current_version != expected_version:
                            raise OptimisticLockException(
                                f"Expected version {expected_version}, but current version is {current_version}"
                            )
                        
                        new_version = current_version + 1
                        
                        # Insert new version
                        await conn.execute("""
                            INSERT INTO state_entities (
                                entity_type, entity_id, version, data, checksum, 
                                created_at, updated_at, actor
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """, entity_type.value, entity_id, new_version, serialized_data,
                             checksum, datetime.utcnow(), datetime.utcnow(), actor)
                        
                        state_operations.labels(operation="update", entity_type=entity_type.value).inc()
                        state_size.labels(entity_type=entity_type.value).observe(len(serialized_data))
                        
                        logger.debug(f"Updated {entity_type.value} entity {entity_id} to version {new_version}")
                        return new_version
                        
            except (OptimisticLockException, StateNotFoundException):
                raise
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Failed to update {entity_type.value} entity {entity_id}: {e}")
                raise
    
    async def delete(self, entity_type: EntityType, entity_id: str, actor: str = "system") -> bool:
        """Delete state entity (soft delete by marking as deleted)"""
        with tracer.start_as_current_span("state_store_delete") as span:
            span.set_attribute("entity_type", entity_type.value)
            span.set_attribute("entity_id", entity_id)
            
            try:
                async with self.pool.acquire() as conn:
                    result = await conn.execute("""
                        UPDATE state_entities 
                        SET deleted_at = $3, deleted_by = $4
                        WHERE entity_type = $1 AND entity_id = $2 AND deleted_at IS NULL
                    """, entity_type.value, entity_id, datetime.utcnow(), actor)
                
                deleted_count = int(result.split()[-1])
                if deleted_count > 0:
                    state_operations.labels(operation="delete", entity_type=entity_type.value).inc()
                    logger.debug(f"Deleted {entity_type.value} entity {entity_id}")
                    return True
                
                return False
                
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Failed to delete {entity_type.value} entity {entity_id}: {e}")
                return False
    
    async def list_entities(self, entity_type: EntityType, 
                           filters: Optional[Dict[str, Any]] = None,
                           limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List entities with optional filtering"""
        with tracer.start_as_current_span("state_store_list") as span:
            span.set_attribute("entity_type", entity_type.value)
            span.set_attribute("limit", limit)
            span.set_attribute("offset", offset)
            
            try:
                async with self.pool.acquire() as conn:
                    # Get latest version of each entity
                    rows = await conn.fetch("""
                        SELECT DISTINCT ON (entity_id) entity_id, data, version, checksum, updated_at, actor
                        FROM state_entities 
                        WHERE entity_type = $1 AND deleted_at IS NULL
                        ORDER BY entity_id, version DESC
                        LIMIT $2 OFFSET $3
                    """, entity_type.value, limit, offset)
                
                entities = []
                for row in rows:
                    data = json.loads(row['data'])
                    data['_version'] = row['version']
                    data['_checksum'] = row['checksum']
                    data['_updated_at'] = row['updated_at'].isoformat()
                    data['_actor'] = row['actor']
                    entities.append(data)
                
                state_operations.labels(operation="list", entity_type=entity_type.value).inc()
                return entities
                
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Failed to list {entity_type.value} entities: {e}")
                return []
    
    async def get_version_info(self, entity_type: EntityType, entity_id: str) -> List[VersionInfo]:
        """Get version history for entity"""
        with tracer.start_as_current_span("state_store_version_info") as span:
            span.set_attribute("entity_type", entity_type.value)
            span.set_attribute("entity_id", entity_id)
            
            try:
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch("""
                        SELECT version, updated_at, checksum, 
                               LENGTH(data) as size, actor
                        FROM state_entities 
                        WHERE entity_type = $1 AND entity_id = $2
                        ORDER BY version ASC
                    """, entity_type.value, entity_id)
                
                versions = []
                for row in rows:
                    versions.append(VersionInfo(
                        version=row['version'],
                        timestamp=row['updated_at'],
                        checksum=row['checksum'],
                        size=row['size'],
                        actor=row['actor']
                    ))
                
                return versions
                
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Failed to get version info for {entity_type.value} entity {entity_id}: {e}")
                return []

# ============================================================================
# Redis Cache Implementation
# ============================================================================

class RedisCacheStore(CacheStore):
    """Redis implementation of caching"""
    
    def __init__(self, redis_pool: aioredis.Redis):
        self.redis = redis_pool
        
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            data = await self.redis.get(key)
            if data:
                # Decompress and deserialize
                decompressed = zlib.decompress(data)
                value = pickle.loads(decompressed)
                cache_hits.labels(cache_level="redis", entity_type="unknown").inc()
                return value
            
            cache_misses.labels(cache_level="redis", entity_type="unknown").inc()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached value with optional TTL"""
        try:
            # Serialize and compress
            serialized = pickle.dumps(value)
            compressed = zlib.compress(serialized)
            
            if ttl:
                await self.redis.setex(key, ttl, compressed)
            else:
                await self.redis.set(key, compressed)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        try:
            result = await self.redis.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            result = await self.redis.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False

# ============================================================================
# In-Memory Cache Implementation
# ============================================================================

class InMemoryCacheStore(CacheStore):
    """In-memory cache implementation with TTL support"""
    
    def __init__(self, max_size: int = 10000):
        self.cache: Dict[str, Tuple[Any, Optional[float]]] = {}
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, (value, expiry) in self.cache.items():
            if expiry and current_time > expiry:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
    
    def _evict_lru(self):
        """Evict least recently used entries if cache is full"""
        if len(self.cache) >= self.max_size:
            # Find LRU key
            lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            del self.cache[lru_key]
            del self.access_times[lru_key]
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        self._cleanup_expired()
        
        if key in self.cache:
            value, expiry = self.cache[key]
            if expiry is None or time.time() <= expiry:
                self.access_times[key] = time.time()
                cache_hits.labels(cache_level="memory", entity_type="unknown").inc()
                return value
            else:
                # Expired
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
        
        cache_misses.labels(cache_level="memory", entity_type="unknown").inc()
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached value with optional TTL"""
        self._cleanup_expired()
        self._evict_lru()
        
        expiry = time.time() + ttl if ttl else None
        self.cache[key] = (value, expiry)
        self.access_times[key] = time.time()
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        self._cleanup_expired()
        return key in self.cache

# ============================================================================
# Redis Lock Store Implementation
# ============================================================================

class RedisLockStore(LockStore):
    """Redis implementation of distributed locking"""
    
    def __init__(self, redis_pool: aioredis.Redis):
        self.redis = redis_pool
        
    async def acquire_lock(self, entity_type: EntityType, entity_id: str,
                          lock_type: LockType, ttl: int = 300, holder: str = "unknown") -> Optional[str]:
        """Acquire a lock, returns lock_id if successful"""
        lock_id = str(uuid.uuid4())
        lock_key = f"lock:{entity_type.value}:{entity_id}"
        
        start_time = time.time()
        
        try:
            # Try to acquire lock
            lock_data = {
                'lock_id': lock_id,
                'lock_type': lock_type.value,
                'holder': holder,
                'acquired_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
            }
            
            # Use SET with NX (only if not exists) and EX (expiry)
            result = await self.redis.set(
                lock_key, 
                json.dumps(lock_data), 
                nx=True, 
                ex=ttl
            )
            
            if result:
                active_locks.inc()
                lock_wait_time.observe(time.time() - start_time)
                logger.debug(f"Acquired {lock_type.value} lock {lock_id} for {entity_type.value}:{entity_id}")
                return lock_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to acquire lock for {entity_type.value}:{entity_id}: {e}")
            return None
    
    async def release_lock(self, lock_id: str) -> bool:
        """Release a lock"""
        try:
            # Find the lock by scanning (in production, you'd want a more efficient approach)
            async for key in self.redis.scan_iter(match="lock:*"):
                lock_data_str = await self.redis.get(key)
                if lock_data_str:
                    lock_data = json.loads(lock_data_str)
                    if lock_data.get('lock_id') == lock_id:
                        await self.redis.delete(key)
                        active_locks.dec()
                        logger.debug(f"Released lock {lock_id}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to release lock {lock_id}: {e}")
            return False
    
    async def refresh_lock(self, lock_id: str, ttl: int = 300) -> bool:
        """Refresh lock TTL"""
        try:
            # Find and refresh the lock
            async for key in self.redis.scan_iter(match="lock:*"):
                lock_data_str = await self.redis.get(key)
                if lock_data_str:
                    lock_data = json.loads(lock_data_str)
                    if lock_data.get('lock_id') == lock_id:
                        lock_data['expires_at'] = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
                        await self.redis.setex(key, ttl, json.dumps(lock_data))
                        logger.debug(f"Refreshed lock {lock_id} with TTL {ttl}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to refresh lock {lock_id}: {e}")
            return False
    
    async def check_lock(self, entity_type: EntityType, entity_id: str) -> Optional[LockInfo]:
        """Check if entity is locked"""
        lock_key = f"lock:{entity_type.value}:{entity_id}"
        
        try:
            lock_data_str = await self.redis.get(lock_key)
            if lock_data_str:
                lock_data = json.loads(lock_data_str)
                return LockInfo(
                    lock_id=lock_data['lock_id'],
                    entity_type=entity_type,
                    entity_id=entity_id,
                    lock_type=LockType(lock_data['lock_type']),
                    acquired_at=datetime.fromisoformat(lock_data['acquired_at']),
                    expires_at=datetime.fromisoformat(lock_data['expires_at']),
                    holder=lock_data['holder']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to check lock for {entity_type.value}:{entity_id}: {e}")
            return None

# ============================================================================
# PostgreSQL Event Store Implementation
# ============================================================================

class PostgreSQLEventStore(EventStore):
    """PostgreSQL implementation of event store"""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool
        
    async def append_event(self, event: StateChangeEvent) -> bool:
        """Append event to the event log"""
        with tracer.start_as_current_span("event_store_append") as span:
            span.set_attribute("entity_type", event.entity_type.value)
            span.set_attribute("entity_id", event.entity_id)
            span.set_attribute("event_type", event.event_type)
            
            try:
                async with self.pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO state_events (
                            event_id, entity_type, entity_id, event_type, 
                            version, timestamp, data, metadata, actor
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """, 
                    event.event_id, event.entity_type.value, event.entity_id,
                    event.event_type, event.version, event.timestamp,
                    json.dumps(event.data), json.dumps(event.metadata), event.actor)
                
                logger.debug(f"Appended event {event.event_id} for {event.entity_type.value}:{event.entity_id}")
                return True
                
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Failed to append event {event.event_id}: {e}")
                return False
    
    async def get_events(self, entity_type: EntityType, entity_id: str,
                        from_version: int = 0, to_version: Optional[int] = None) -> List[StateChangeEvent]:
        """Get events for entity within version range"""
        with tracer.start_as_current_span("event_store_get_events") as span:
            span.set_attribute("entity_type", entity_type.value)
            span.set_attribute("entity_id", entity_id)
            span.set_attribute("from_version", from_version)
            span.set_attribute("to_version", to_version or "latest")
            
            try:
                async with self.pool.acquire() as conn:
                    if to_version is not None:
                        rows = await conn.fetch("""
                            SELECT event_id, entity_type, entity_id, event_type,
                                   version, timestamp, data, metadata, actor
                            FROM state_events 
                            WHERE entity_type = $1 AND entity_id = $2 
                                  AND version >= $3 AND version <= $4
                            ORDER BY version ASC
                        """, entity_type.value, entity_id, from_version, to_version)
                    else:
                        rows = await conn.fetch("""
                            SELECT event_id, entity_type, entity_id, event_type,
                                   version, timestamp, data, metadata, actor
                            FROM state_events 
                            WHERE entity_type = $1 AND entity_id = $2 AND version >= $3
                            ORDER BY version ASC
                        """, entity_type.value, entity_id, from_version)
                
                events = []
                for row in rows:
                    events.append(StateChangeEvent(
                        event_id=row['event_id'],
                        entity_type=EntityType(row['entity_type']),
                        entity_id=row['entity_id'],
                        event_type=row['event_type'],
                        timestamp=row['timestamp'],
                        version=row['version'],
                        data=json.loads(row['data']),
                        metadata=json.loads(row['metadata']),
                        actor=row['actor']
                    ))
                
                return events
                
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Failed to get events for {entity_type.value}:{entity_id}: {e}")
                return []
    
    async def get_events_by_time(self, entity_type: EntityType, entity_id: str,
                               from_time: datetime, to_time: Optional[datetime] = None) -> List[StateChangeEvent]:
        """Get events for entity within time range"""
        with tracer.start_as_current_span("event_store_get_events_by_time") as span:
            span.set_attribute("entity_type", entity_type.value)
            span.set_attribute("entity_id", entity_id)
            span.set_attribute("from_time", from_time.isoformat())
            span.set_attribute("to_time", to_time.isoformat() if to_time else "now")
            
            try:
                async with self.pool.acquire() as conn:
                    if to_time is not None:
                        rows = await conn.fetch("""
                            SELECT event_id, entity_type, entity_id, event_type,
                                   version, timestamp, data, metadata, actor
                            FROM state_events 
                            WHERE entity_type = $1 AND entity_id = $2 
                                  AND timestamp >= $3 AND timestamp <= $4
                            ORDER BY timestamp ASC
                        """, entity_type.value, entity_id, from_time, to_time)
                    else:
                        rows = await conn.fetch("""
                            SELECT event_id, entity_type, entity_id, event_type,
                                   version, timestamp, data, metadata, actor
                            FROM state_events 
                            WHERE entity_type = $1 AND entity_id = $2 AND timestamp >= $3
                            ORDER BY timestamp ASC
                        """, entity_type.value, entity_id, from_time)
                
                events = []
                for row in rows:
                    events.append(StateChangeEvent(
                        event_id=row['event_id'],
                        entity_type=EntityType(row['entity_type']),
                        entity_id=row['entity_id'],
                        event_type=row['event_type'],
                        timestamp=row['timestamp'],
                        version=row['version'],
                        data=json.loads(row['data']),
                        metadata=json.loads(row['metadata']),
                        actor=row['actor']
                    ))
                
                return events
                
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Failed to get events by time for {entity_type.value}:{entity_id}: {e}")
                return []

# ============================================================================
# Enhanced Transaction Manager with Event Sourcing
# ============================================================================

class TransactionManager:
    """Manages database transactions with rollback capabilities and event sourcing"""
    
    def __init__(self, state_store: StateStore, event_store: Optional[EventStore] = None):
        self.state_store = state_store
        self.event_store = event_store
        self.operations: List[Tuple[str, Any]] = []
        self.rollback_operations: List[Tuple[str, Any]] = []
        self.events: List[StateChangeEvent] = []
        
    async def create_entity(self, entity_type: EntityType, entity_id: str, 
                           data: Dict[str, Any], actor: str = "system"):
        """Create entity within transaction"""
        operation = ("create", (entity_type, entity_id, data, actor))
        self.operations.append(operation)
        
        # Prepare rollback
        rollback_op = ("delete", (entity_type, entity_id, actor))
        self.rollback_operations.append(rollback_op)
        
        # Create event
        if self.event_store:
            event = StateChangeEvent(
                event_id=str(uuid.uuid4()),
                entity_type=entity_type,
                entity_id=entity_id,
                event_type="entity_created",
                timestamp=datetime.utcnow(),
                version=1,
                data=data.copy(),
                metadata={"transaction": True},
                actor=actor
            )
            self.events.append(event)
    
    async def update_entity(self, entity_type: EntityType, entity_id: str, 
                           data: Dict[str, Any], expected_version: Optional[int] = None,
                           actor: str = "system"):
        """Update entity within transaction"""
        # Get current state for rollback
        current_state = await self.state_store.get(entity_type, entity_id)
        if current_state:
            rollback_op = ("update", (entity_type, entity_id, current_state, 
                                    current_state.get('_version'), actor))
            self.rollback_operations.append(rollback_op)
        
        operation = ("update", (entity_type, entity_id, data, expected_version, actor))
        self.operations.append(operation)
        
        # Create event
        if self.event_store and current_state:
            event = StateChangeEvent(
                event_id=str(uuid.uuid4()),
                entity_type=entity_type,
                entity_id=entity_id,
                event_type="entity_updated",
                timestamp=datetime.utcnow(),
                version=current_state.get('_version', 1) + 1,
                data=data.copy(),
                metadata={
                    "transaction": True,
                    "previous_version": current_state.get('_version', 1)
                },
                actor=actor
            )
            self.events.append(event)
    
    async def delete_entity(self, entity_type: EntityType, entity_id: str, actor: str = "system"):
        """Delete entity within transaction"""
        # Get current state for rollback
        current_state = await self.state_store.get(entity_type, entity_id)
        if current_state:
            rollback_op = ("create", (entity_type, entity_id, current_state, 
                                    current_state.get('_version'), actor))
            self.rollback_operations.append(rollback_op)
        
        operation = ("delete", (entity_type, entity_id, actor))
        self.operations.append(operation)
        
        # Create event
        if self.event_store and current_state:
            event = StateChangeEvent(
                event_id=str(uuid.uuid4()),
                entity_type=entity_type,
                entity_id=entity_id,
                event_type="entity_deleted",
                timestamp=datetime.utcnow(),
                version=current_state.get('_version', 1),
                data=current_state.copy(),
                metadata={"transaction": True},
                actor=actor
            )
            self.events.append(event)
    
    async def commit(self):
        """Commit all transaction operations and events"""
        with tracer.start_as_current_span("transaction_commit") as span:
            span.set_attribute("operation_count", len(self.operations))
            span.set_attribute("event_count", len(self.events))
            
            start_time = time.time()
            
            try:
                # Execute all state operations
                for op_type, args in self.operations:
                    if op_type == "create":
                        await self.state_store.create(*args)
                    elif op_type == "update":
                        await self.state_store.update(*args)
                    elif op_type == "delete":
                        await self.state_store.delete(*args)
                
                # Store all events
                if self.event_store:
                    for event in self.events:
                        await self.event_store.append_event(event)
                
                # Clear operations after successful commit
                self.operations.clear()
                self.rollback_operations.clear()
                self.events.clear()
                
                transaction_duration.observe(time.time() - start_time)
                logger.debug(f"Committed transaction with {len(self.operations)} operations and {len(self.events)} events")
                
            except Exception as e:
                span.record_exception(e)
                await self.rollback()
                raise
    
    async def rollback(self):
        """Rollback all transaction operations"""
        with tracer.start_as_current_span("transaction_rollback") as span:
            span.set_attribute("rollback_operation_count", len(self.rollback_operations))
            
            try:
                # Execute rollback operations in reverse order
                for op_type, args in reversed(self.rollback_operations):
                    try:
                        if op_type == "create":
                            await self.state_store.create(*args)
                        elif op_type == "update":
                            await self.state_store.update(*args)
                        elif op_type == "delete":
                            await self.state_store.delete(*args)
                    except Exception as e:
                        logger.error(f"Error during rollback operation {op_type}: {e}")
                
                # Clear operations after rollback
                self.operations.clear()
                self.rollback_operations.clear()
                self.events.clear()
                
                logger.warning(f"Rolled back transaction with {len(self.rollback_operations)} operations")
                
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Failed to rollback transaction: {e}")
                raise

# ============================================================================
# Main State Manager
# ============================================================================

class StateManager:
    """Main state management system orchestrating all components"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize storage backends
        self.state_store: Optional[StateStore] = None
        self.event_store: Optional[EventStore] = None
        self.l1_cache: Optional[CacheStore] = None
        self.l2_cache: Optional[CacheStore] = None
        self.lock_store: Optional[LockStore] = None
        
        # Connection pools
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis_pool: Optional[aioredis.Redis] = None
        
    async def initialize(self):
        """Initialize all storage backends and connections"""
        logger.info("Initializing State Manager...")
        
        # Initialize database pool
        db_config = self.config.get('database', {})
        self.db_pool = await asyncpg.create_pool(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 5432),
            database=db_config.get('database', 'dora_state'),
            user=db_config.get('user', 'postgres'),
            password=db_config.get('password', ''),
            min_size=db_config.get('min_connections', 5),
            max_size=db_config.get('max_connections', 20)
        )
        
        # Initialize Redis pool
        redis_config = self.config.get('redis', {})
        self.redis_pool = aioredis.from_url(
            redis_config.get('url', 'redis://localhost:6379'),
            encoding='utf-8',
            decode_responses=False
        )
        
        # Initialize storage backends
        self.state_store = PostgreSQLStateStore(self.db_pool)
        self.event_store = PostgreSQLEventStore(self.db_pool)
        self.l1_cache = InMemoryCacheStore(max_size=self.config.get('l1_cache_size', 10000))
        self.l2_cache = RedisCacheStore(self.redis_pool)
        self.lock_store = RedisLockStore(self.redis_pool)
        
        # Create database schema if needed
        await self._create_schema()
        
        logger.info("State Manager initialized successfully")
    
    async def _create_schema(self):
        """Create database schema for state management"""
        async with self.db_pool.acquire() as conn:
            # Create state entities table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS state_entities (
                    id SERIAL PRIMARY KEY,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id VARCHAR(255) NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    data JSONB NOT NULL,
                    checksum VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP NULL,
                    actor VARCHAR(255) NOT NULL DEFAULT 'system',
                    deleted_by VARCHAR(255) NULL,
                    
                    UNIQUE(entity_type, entity_id, version)
                );
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_state_entities_type_id 
                ON state_entities(entity_type, entity_id);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_state_entities_updated 
                ON state_entities(updated_at);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_state_entities_deleted 
                ON state_entities(deleted_at) WHERE deleted_at IS NULL;
            """)
            
            # Create events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS state_events (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(255) UNIQUE NOT NULL,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id VARCHAR(255) NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    version INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data JSONB NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    actor VARCHAR(255) NOT NULL DEFAULT 'system'
                );
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_state_events_entity 
                ON state_events(entity_type, entity_id, version);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_state_events_timestamp 
                ON state_events(timestamp);
            """)
    
    async def shutdown(self):
        """Shutdown all connections and clean up resources"""
        logger.info("Shutting down State Manager...")
        
        if self.db_pool:
            await self.db_pool.close()
        
        if self.redis_pool:
            await self.redis_pool.close()
        
        logger.info("State Manager shutdown complete")
    
    # ========================================================================
    # Public State Management API
    # ========================================================================
    
    async def create_workflow_state(self, workflow_id: str, workflow_data: Dict[str, Any], 
                                   actor: str = "system") -> bool:
        """Create new workflow state"""
        return await self.state_store.create(EntityType.WORKFLOW, workflow_id, workflow_data, actor=actor)
    
    async def get_workflow_state(self, workflow_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get workflow state with caching"""
        cache_key = f"workflow:{workflow_id}:{version or 'latest'}"
        
        # L1 cache check
        if cached_state := await self.l1_cache.get(cache_key):
            return cached_state
        
        # L2 cache check
        if cached_state := await self.l2_cache.get(cache_key):
            await self.l1_cache.set(cache_key, cached_state, ttl=300)
            return cached_state
        
        # Load from database
        state = await self.state_store.get(EntityType.WORKFLOW, workflow_id, version)
        if state:
            # Cache in both levels
            await self.l2_cache.set(cache_key, state, ttl=3600)
            await self.l1_cache.set(cache_key, state, ttl=300)
        
        return state
    
    async def update_workflow_state(self, workflow_id: str, workflow_data: Dict[str, Any],
                                   expected_version: Optional[int] = None, actor: str = "system") -> int:
        """Update workflow state and invalidate caches"""
        new_version = await self.state_store.update(
            EntityType.WORKFLOW, workflow_id, workflow_data, expected_version, actor
        )
        
        # Invalidate caches
        await self._invalidate_entity_cache(EntityType.WORKFLOW, workflow_id)
        
        return new_version
    
    async def create_agent_state(self, agent_id: str, agent_data: Dict[str, Any], 
                                actor: str = "system") -> bool:
        """Create new agent state"""
        return await self.state_store.create(EntityType.AGENT, agent_id, agent_data, actor=actor)
    
    async def get_agent_state(self, agent_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get agent state with caching"""
        cache_key = f"agent:{agent_id}:{version or 'latest'}"
        
        # L1 cache check
        if cached_state := await self.l1_cache.get(cache_key):
            return cached_state
        
        # L2 cache check
        if cached_state := await self.l2_cache.get(cache_key):
            await self.l1_cache.set(cache_key, cached_state, ttl=300)
            return cached_state
        
        # Load from database
        state = await self.state_store.get(EntityType.AGENT, agent_id, version)
        if state:
            # Cache in both levels
            await self.l2_cache.set(cache_key, state, ttl=1800)  # Shorter TTL for agent state
            await self.l1_cache.set(cache_key, state, ttl=300)
        
        return state
    
    async def update_agent_state(self, agent_id: str, agent_data: Dict[str, Any],
                                expected_version: Optional[int] = None, actor: str = "system") -> int:
        """Update agent state and invalidate caches"""
        new_version = await self.state_store.update(
            EntityType.AGENT, agent_id, agent_data, expected_version, actor
        )
        
        # Invalidate caches
        await self._invalidate_entity_cache(EntityType.AGENT, agent_id)
        
        return new_version
    
    @asynccontextmanager
    async def transaction(self):
        """Create a new transaction context"""
        txn = TransactionManager(self.state_store, self.event_store)
        try:
            yield txn
        except Exception:
            await txn.rollback()
            raise
    
    @asynccontextmanager
    async def exclusive_lock(self, entity_type: EntityType, entity_id: str, 
                            ttl: int = 300, holder: str = "unknown"):
        """Acquire exclusive lock in context manager"""
        lock_id = await self.lock_store.acquire_lock(entity_type, entity_id, LockType.EXCLUSIVE, ttl, holder)
        
        if not lock_id:
            raise PessimisticLockException(f"Could not acquire exclusive lock for {entity_type.value}:{entity_id}")
        
        try:
            yield lock_id
        finally:
            await self.lock_store.release_lock(lock_id)
    
    async def _invalidate_entity_cache(self, entity_type: EntityType, entity_id: str):
        """Invalidate all cache entries for an entity"""
        # Pattern for cache keys
        pattern = f"{entity_type.value}:{entity_id}:*"
        
        # For L1 cache, we need to track keys (simplified approach)
        # In production, you'd want a more sophisticated cache key tracking system
        
        # For L2 cache (Redis), scan and delete matching keys
        if self.redis_pool:
            async for key in self.redis_pool.scan_iter(match=pattern):
                await self.redis_pool.delete(key)

    # ========================================================================
    # Task State Management
    # ========================================================================
    
    async def create_task_state(self, task_id: str, task_data: Dict[str, Any], 
                               actor: str = "system") -> bool:
        """Create new task state"""
        return await self.state_store.create(EntityType.TASK, task_id, task_data, actor=actor)
    
    async def get_task_state(self, task_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get task state with caching"""
        cache_key = f"task:{task_id}:{version or 'latest'}"
        
        # L1 cache check
        if cached_state := await self.l1_cache.get(cache_key):
            return cached_state
        
        # L2 cache check
        if cached_state := await self.l2_cache.get(cache_key):
            await self.l1_cache.set(cache_key, cached_state, ttl=180)
            return cached_state
        
        # Load from database
        state = await self.state_store.get(EntityType.TASK, task_id, version)
        if state:
            # Cache in both levels (shorter TTL for task state)
            await self.l2_cache.set(cache_key, state, ttl=900)  # 15 minutes
            await self.l1_cache.set(cache_key, state, ttl=180)  # 3 minutes
        
        return state
    
    async def update_task_state(self, task_id: str, task_data: Dict[str, Any],
                               expected_version: Optional[int] = None, actor: str = "system") -> int:
        """Update task state and invalidate caches"""
        new_version = await self.state_store.update(
            EntityType.TASK, task_id, task_data, expected_version, actor
        )
        
        # Invalidate caches
        await self._invalidate_entity_cache(EntityType.TASK, task_id)
        
        return new_version
    
    async def list_tasks(self, filters: Optional[Dict[str, Any]] = None,
                        limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List tasks with optional filtering"""
        return await self.state_store.list_entities(EntityType.TASK, filters, limit, offset)
    
    # ========================================================================
    # Resource State Management
    # ========================================================================
    
    async def create_resource_state(self, resource_id: str, resource_data: Dict[str, Any], 
                                   actor: str = "system") -> bool:
        """Create new resource state"""
        return await self.state_store.create(EntityType.RESOURCE, resource_id, resource_data, actor=actor)
    
    async def get_resource_state(self, resource_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get resource state with caching"""
        cache_key = f"resource:{resource_id}:{version or 'latest'}"
        
        # L1 cache check
        if cached_state := await self.l1_cache.get(cache_key):
            return cached_state
        
        # L2 cache check
        if cached_state := await self.l2_cache.get(cache_key):
            await self.l1_cache.set(cache_key, cached_state, ttl=300)
            return cached_state
        
        # Load from database
        state = await self.state_store.get(EntityType.RESOURCE, resource_id, version)
        if state:
            # Cache in both levels
            await self.l2_cache.set(cache_key, state, ttl=1800)  # 30 minutes
            await self.l1_cache.set(cache_key, state, ttl=300)   # 5 minutes
        
        return state
    
    async def update_resource_state(self, resource_id: str, resource_data: Dict[str, Any],
                                   expected_version: Optional[int] = None, actor: str = "system") -> int:
        """Update resource state and invalidate caches"""
        new_version = await self.state_store.update(
            EntityType.RESOURCE, resource_id, resource_data, expected_version, actor
        )
        
        # Invalidate caches
        await self._invalidate_entity_cache(EntityType.RESOURCE, resource_id)
        
        return new_version
    
    async def list_resources(self, filters: Optional[Dict[str, Any]] = None,
                            limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List resources with optional filtering"""
        return await self.state_store.list_entities(EntityType.RESOURCE, filters, limit, offset)
    
    # ========================================================================
    # System State Management
    # ========================================================================
    
    async def create_system_state(self, system_id: str, system_data: Dict[str, Any], 
                                 actor: str = "system") -> bool:
        """Create new system state"""
        return await self.state_store.create(EntityType.SYSTEM, system_id, system_data, actor=actor)
    
    async def get_system_state(self, system_id: str = "global", version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get system state with caching"""
        cache_key = f"system:{system_id}:{version or 'latest'}"
        
        # L1 cache check
        if cached_state := await self.l1_cache.get(cache_key):
            return cached_state
        
        # L2 cache check
        if cached_state := await self.l2_cache.get(cache_key):
            await self.l1_cache.set(cache_key, cached_state, ttl=600)
            return cached_state
        
        # Load from database
        state = await self.state_store.get(EntityType.SYSTEM, system_id, version)
        if state:
            # Cache in both levels (longer TTL for system state)
            await self.l2_cache.set(cache_key, state, ttl=3600)  # 1 hour
            await self.l1_cache.set(cache_key, state, ttl=600)   # 10 minutes
        
        return state
    
    async def update_system_state(self, system_id: str, system_data: Dict[str, Any],
                                 expected_version: Optional[int] = None, actor: str = "system") -> int:
        """Update system state and invalidate caches"""
        new_version = await self.state_store.update(
            EntityType.SYSTEM, system_id, system_data, expected_version, actor
        )
        
        # Invalidate caches
        await self._invalidate_entity_cache(EntityType.SYSTEM, system_id)
        
        return new_version
    
    # ========================================================================
    # Event Sourcing and Recovery
    # ========================================================================
    
    async def get_entity_events(self, entity_type: EntityType, entity_id: str,
                               from_version: int = 0, to_version: Optional[int] = None) -> List[StateChangeEvent]:
        """Get event history for an entity"""
        if self.event_store:
            return await self.event_store.get_events(entity_type, entity_id, from_version, to_version)
        return []
    
    async def get_entity_events_by_time(self, entity_type: EntityType, entity_id: str,
                                       from_time: datetime, to_time: Optional[datetime] = None) -> List[StateChangeEvent]:
        """Get events for entity within time range"""
        if self.event_store:
            return await self.event_store.get_events_by_time(entity_type, entity_id, from_time, to_time)
        return []
    
    async def reconstruct_state_from_events(self, entity_type: EntityType, entity_id: str,
                                           up_to_version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Reconstruct entity state from event history"""
        if not self.event_store:
            return None
            
        events = await self.event_store.get_events(entity_type, entity_id, 0, up_to_version)
        if not events:
            return None
            
        # Start with empty state
        state = {}
        
        # Apply events in order
        for event in events:
            if event.event_type == "entity_created":
                state = event.data.copy()
            elif event.event_type == "entity_updated":
                state.update(event.data)
            elif event.event_type == "entity_deleted":
                return None  # Entity was deleted
                
        return state if state else None
    
    async def rollback_entity_to_version(self, entity_type: EntityType, entity_id: str,
                                        target_version: int, actor: str = "system") -> bool:
        """Rollback entity state to a specific version"""
        try:
            # Get the target version state
            target_state = await self.state_store.get(entity_type, entity_id, target_version)
            if not target_state:
                logger.error(f"Target version {target_version} not found for {entity_type.value}:{entity_id}")
                return False
            
            # Get current version
            current_state = await self.state_store.get(entity_type, entity_id)
            if not current_state:
                logger.error(f"Current state not found for {entity_type.value}:{entity_id}")
                return False
            
            # Create rollback transaction
            async with self.transaction() as txn:
                await txn.update_entity(
                    entity_type, 
                    entity_id, 
                    target_state, 
                    expected_version=current_state.get('_version'),
                    actor=f"{actor}:rollback"
                )
                await txn.commit()
            
            # Invalidate caches
            await self._invalidate_entity_cache(entity_type, entity_id)
            
            logger.info(f"Rolled back {entity_type.value}:{entity_id} from version {current_state.get('_version')} to {target_version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback {entity_type.value}:{entity_id} to version {target_version}: {e}")
            return False
    
    async def rollback_entity_to_time(self, entity_type: EntityType, entity_id: str,
                                     target_time: datetime, actor: str = "system") -> bool:
        """Rollback entity state to a specific point in time"""
        try:
            # Find the latest version at or before the target time
            versions = await self.state_store.get_version_info(entity_type, entity_id)
            if not versions:
                logger.error(f"No versions found for {entity_type.value}:{entity_id}")
                return False
            
            target_version = None
            for version_info in reversed(versions):  # Start from latest
                if version_info.timestamp <= target_time:
                    target_version = version_info.version
                    break
            
            if target_version is None:
                logger.error(f"No version found at or before {target_time} for {entity_type.value}:{entity_id}")
                return False
            
            # Rollback to that version
            return await self.rollback_entity_to_version(entity_type, entity_id, target_version, actor)
            
        except Exception as e:
            logger.error(f"Failed to rollback {entity_type.value}:{entity_id} to time {target_time}: {e}")
            return False

# Export main classes
__all__ = [
    'StateManager',
    'EntityType',
    'WorkflowState',
    'TaskState', 
    'AgentState',
    'StateChangeEvent',
    'OptimisticLockException',
    'PessimisticLockException',
    'StateNotFoundException'
] 