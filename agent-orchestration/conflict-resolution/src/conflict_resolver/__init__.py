"""
DORA Compliance Agent Conflict Resolution System

This module provides comprehensive conflict detection, analysis, and resolution
capabilities for the DORA compliance agent orchestration platform.
"""

import asyncio
import logging
import time
import uuid
import hashlib
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from collections import defaultdict, Counter, deque
import json
import yaml
import threading
import heapq

# Third-party imports
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge, Summary
from opentelemetry import trace

# Configure logging
logger = logging.getLogger(__name__)

# Metrics
conflict_detections = PrometheusCounter('conflicts_detected_total', 'Total conflicts detected', ['conflict_type'])
conflict_resolutions = PrometheusCounter('conflicts_resolved_total', 'Total conflicts resolved', ['resolution_strategy', 'success'])
resolution_time = Histogram('conflict_resolution_duration_seconds', 'Conflict resolution duration')
active_conflicts = Gauge('active_conflicts', 'Currently active conflicts')
deadlock_incidents = PrometheusCounter('deadlock_incidents_total', 'Total deadlock incidents')
preemption_events = PrometheusCounter('preemption_events_total', 'Total preemption events')

# Get tracer
tracer = trace.get_tracer(__name__)

# ============================================================================
# Core Enums and Data Structures
# ============================================================================

class ConflictType(Enum):
    """Types of conflicts that can occur"""
    RESOURCE_ALLOCATION = "resource_allocation"
    DATA_ACCESS = "data_access"
    WORKFLOW_DEPENDENCY = "workflow_dependency"
    AGENT_COMPETITION = "agent_competition"
    DEADLOCK = "deadlock"

class ResolutionStrategy(Enum):
    """Strategies for resolving conflicts"""
    PRIORITY_PREEMPTION = "priority_preemption"
    FAIR_SHARE = "fair_share"
    QUOTA_ENFORCEMENT = "quota_enforcement"
    LOCK_ESCALATION = "lock_escalation"
    DEPENDENCY_ORDERING = "dependency_ordering"
    CAPABILITY_MATCHING = "capability_matching"
    LOAD_BALANCING = "load_balancing"
    ABORT_TRANSACTION = "abort_transaction"

class ConflictPriority(Enum):
    """Priority levels for conflicts"""
    CRITICAL = 10
    HIGH = 7
    MEDIUM = 5
    LOW = 3
    BACKGROUND = 1

class ResourceType(Enum):
    """Types of resources that can conflict"""
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE_CONNECTIONS = "database_connections"
    EXTERNAL_API_QUOTA = "external_api_quota"
    LICENSE = "license"

@dataclass
class ResourceRequest:
    """Represents a resource request from an agent or workflow"""
    requester_id: str
    resource_type: ResourceType
    amount: float
    priority: ConflictPriority
    timestamp: datetime
    timeout: Optional[timedelta] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConflictInfo:
    """Information about a detected conflict"""
    conflict_id: str
    conflict_type: ConflictType
    detected_at: datetime
    involved_entities: List[str]
    resource_requests: List[ResourceRequest] = field(default_factory=list)
    deadlock_cycle: Optional[List[str]] = None
    priority: ConflictPriority = ConflictPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResolutionAction:
    """Action to be taken to resolve a conflict"""
    action_type: str
    target_entity: str
    parameters: Dict[str, Any]
    execution_order: int = 0

@dataclass
class ConflictResolution:
    """Result of conflict resolution"""
    conflict_id: str
    strategy: ResolutionStrategy
    actions: List[ResolutionAction]
    estimated_cost: float
    success_probability: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConflictMetrics:
    """Metrics for tracking conflict resolution performance"""
    total_conflicts: Counter = field(default_factory=Counter)
    resolution_times: List[float] = field(default_factory=list)
    resolution_success_rate: Dict[str, List[bool]] = field(default_factory=dict)
    deadlock_incidents: List[datetime] = field(default_factory=list)
    preemption_events: List[datetime] = field(default_factory=list)
    
    def record_conflict(self, conflict_type: str, resolution_time: float, success: bool):
        self.total_conflicts[conflict_type] += 1
        self.resolution_times.append(resolution_time)
        
        if conflict_type not in self.resolution_success_rate:
            self.resolution_success_rate[conflict_type] = []
        self.resolution_success_rate[conflict_type].append(success)

# ============================================================================
# Conflict Detection Components
# ============================================================================

class ConflictDetector(ABC):
    """Abstract base class for conflict detectors"""
    
    @abstractmethod
    async def detect_conflicts(self) -> List[ConflictInfo]:
        """Detect and return a list of conflicts"""
        pass
    
    @abstractmethod
    async def monitor_continuously(self, interval: float = 5.0):
        """Continuously monitor for conflicts"""
        pass

class ResourceConflictDetector(ConflictDetector):
    """Detects conflicts in resource allocation"""
    
    def __init__(self, resource_limits: Dict[ResourceType, float]):
        self.resource_limits = resource_limits
        self.active_requests: Dict[ResourceType, List[ResourceRequest]] = defaultdict(list)
        self.allocated_resources: Dict[ResourceType, float] = defaultdict(float)
        
    async def add_resource_request(self, request: ResourceRequest):
        """Add a new resource request for monitoring"""
        self.active_requests[request.resource_type].append(request)
        
    async def remove_resource_request(self, request_id: str):
        """Remove a resource request"""
        for resource_type, requests in self.active_requests.items():
            self.active_requests[resource_type] = [
                req for req in requests if req.requester_id != request_id
            ]
    
    async def detect_conflicts(self) -> List[ConflictInfo]:
        """Detect resource allocation conflicts"""
        conflicts = []
        
        for resource_type, requests in self.active_requests.items():
            if not requests:
                continue
                
            # Calculate total demand
            total_demand = sum(req.amount for req in requests)
            available = self.resource_limits.get(resource_type, 0.0)
            
            if total_demand > available:
                # Resource conflict detected
                conflict = ConflictInfo(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type=ConflictType.RESOURCE_ALLOCATION,
                    detected_at=datetime.utcnow(),
                    involved_entities=[req.requester_id for req in requests],
                    resource_requests=requests,
                    priority=max(req.priority for req in requests),
                    metadata={
                        "resource_type": resource_type.value,
                        "total_demand": total_demand,
                        "available": available,
                        "oversubscription_ratio": total_demand / available
                    }
                )
                conflicts.append(conflict)
                
                conflict_detections.labels(conflict_type="resource_allocation").inc()
                logger.warning(f"Resource conflict detected: {resource_type.value} oversubscribed by {total_demand - available}")
        
        return conflicts
    
    async def monitor_continuously(self, interval: float = 5.0):
        """Continuously monitor for resource conflicts"""
        while True:
            try:
                conflicts = await self.detect_conflicts()
                if conflicts:
                    for conflict in conflicts:
                        logger.info(f"Detected resource conflict: {conflict.conflict_id}")
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in resource conflict monitoring: {e}")
                await asyncio.sleep(interval)

class DeadlockDetector(ConflictDetector):
    """Detects deadlocks in workflow dependencies"""
    
    def __init__(self):
        self.wait_graph: Dict[str, Set[str]] = defaultdict(set)
        self.resource_locks: Dict[str, str] = {}  # resource -> holder
        self.lock_requests: Dict[str, Set[str]] = defaultdict(set)  # resource -> waiters
        
    def add_lock_request(self, entity_id: str, resource_id: str):
        """Add a lock request to the wait graph"""
        if resource_id in self.resource_locks:
            holder = self.resource_locks[resource_id]
            self.wait_graph[entity_id].add(holder)
            self.lock_requests[resource_id].add(entity_id)
        
    def remove_lock_request(self, entity_id: str, resource_id: str):
        """Remove a lock request from the wait graph"""
        if resource_id in self.lock_requests:
            self.lock_requests[resource_id].discard(entity_id)
        
        # Remove from wait graph
        for waiters in self.wait_graph.values():
            waiters.discard(entity_id)
    
    def grant_lock(self, entity_id: str, resource_id: str):
        """Grant a lock to an entity"""
        self.resource_locks[resource_id] = entity_id
        self.remove_lock_request(entity_id, resource_id)
    
    def release_lock(self, entity_id: str, resource_id: str):
        """Release a lock held by an entity"""
        if self.resource_locks.get(resource_id) == entity_id:
            del self.resource_locks[resource_id]
            
            # Grant to next waiter if any
            if resource_id in self.lock_requests and self.lock_requests[resource_id]:
                next_waiter = next(iter(self.lock_requests[resource_id]))
                self.grant_lock(next_waiter, resource_id)
    
    async def detect_deadlock_cycle(self) -> Optional[List[str]]:
        """Detect cycles in the wait-for graph using DFS"""
        def dfs(node: str, visited: Set[str], path: List[str]) -> Optional[List[str]]:
            if node in path:
                # Found cycle
                cycle_start = path.index(node)
                return path[cycle_start:]
            
            if node in visited:
                return None
                
            visited.add(node)
            path.append(node)
            
            for neighbor in self.wait_graph.get(node, set()):
                cycle = dfs(neighbor, visited, path)
                if cycle:
                    return cycle
                    
            path.pop()
            return None
        
        visited = set()
        for node in self.wait_graph:
            if node not in visited:
                cycle = dfs(node, visited, [])
                if cycle:
                    return cycle
        
        return None
    
    async def detect_conflicts(self) -> List[ConflictInfo]:
        """Detect deadlock conflicts"""
        conflicts = []
        
        cycle = await self.detect_deadlock_cycle()
        if cycle:
            conflict = ConflictInfo(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.DEADLOCK,
                detected_at=datetime.utcnow(),
                involved_entities=cycle,
                deadlock_cycle=cycle,
                priority=ConflictPriority.CRITICAL,
                metadata={
                    "cycle_length": len(cycle),
                    "wait_graph_size": len(self.wait_graph)
                }
            )
            conflicts.append(conflict)
            
            deadlock_incidents.inc()
            logger.critical(f"Deadlock detected: {' -> '.join(cycle)}")
        
        return conflicts
    
    async def monitor_continuously(self, interval: float = 10.0):
        """Continuously monitor for deadlocks"""
        while True:
            try:
                conflicts = await self.detect_conflicts()
                if conflicts:
                    for conflict in conflicts:
                        logger.critical(f"Deadlock detected: {conflict.conflict_id}")
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in deadlock monitoring: {e}")
                await asyncio.sleep(interval)

class AgentCompetitionDetector(ConflictDetector):
    """Detects conflicts in agent task assignment"""
    
    def __init__(self):
        self.task_assignments: Dict[str, List[str]] = defaultdict(list)  # task -> agents
        self.agent_capabilities: Dict[str, Set[str]] = defaultdict(set)
        self.agent_loads: Dict[str, float] = defaultdict(float)
        
    def register_agent(self, agent_id: str, capabilities: Set[str], current_load: float = 0.0):
        """Register an agent with its capabilities and load"""
        self.agent_capabilities[agent_id] = capabilities
        self.agent_loads[agent_id] = current_load
    
    def add_task_candidate(self, task_id: str, agent_id: str):
        """Add an agent as a candidate for a task"""
        self.task_assignments[task_id].append(agent_id)
    
    def calculate_assignment_score(self, task_id: str, agent_id: str, required_capabilities: Set[str]) -> float:
        """Calculate how well an agent matches a task"""
        agent_caps = self.agent_capabilities.get(agent_id, set())
        capability_match = len(required_capabilities & agent_caps) / len(required_capabilities) if required_capabilities else 1.0
        load_factor = 1.0 - self.agent_loads.get(agent_id, 0.0)  # Lower load is better
        
        return capability_match * 0.7 + load_factor * 0.3
    
    async def detect_conflicts(self) -> List[ConflictInfo]:
        """Detect agent competition conflicts"""
        conflicts = []
        
        for task_id, candidates in self.task_assignments.items():
            if len(candidates) > 1:
                # Multiple agents competing for the same task
                conflict = ConflictInfo(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type=ConflictType.AGENT_COMPETITION,
                    detected_at=datetime.utcnow(),
                    involved_entities=candidates,
                    priority=ConflictPriority.MEDIUM,
                    metadata={
                        "task_id": task_id,
                        "candidate_count": len(candidates),
                        "agent_loads": {agent: self.agent_loads.get(agent, 0.0) for agent in candidates}
                    }
                )
                conflicts.append(conflict)
                
                conflict_detections.labels(conflict_type="agent_competition").inc()
                logger.info(f"Agent competition detected for task {task_id}: {len(candidates)} candidates")
        
        return conflicts
    
    async def monitor_continuously(self, interval: float = 3.0):
        """Continuously monitor for agent competition"""
        while True:
            try:
                conflicts = await self.detect_conflicts()
                if conflicts:
                    for conflict in conflicts:
                        logger.info(f"Agent competition detected: {conflict.conflict_id}")
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in agent competition monitoring: {e}")
                await asyncio.sleep(interval)

# ============================================================================
# Policy Management
# ============================================================================

class PolicyManager:
    """Manages conflict resolution policies"""
    
    def __init__(self, policy_config: Optional[Dict[str, Any]] = None):
        self.policies = policy_config or self._default_policies()
        self._lock = threading.RLock()
        
    def _default_policies(self) -> Dict[str, Any]:
        """Return default conflict resolution policies"""
        return {
            "detection_interval": 5,
            "resolution_timeout": 30,
            "max_retries": 3,
            "resource_conflicts": {
                "cpu": {
                    "strategy": "priority_preemption",
                    "preemption_threshold": 0.8,
                    "grace_period": 10
                },
                "memory": {
                    "strategy": "fair_share",
                    "min_allocation": "1GB",
                    "max_allocation": "16GB"
                }
            },
            "data_conflicts": {
                "strategy": "lock_escalation",
                "lock_timeout": 30,
                "retry_interval": 1,
                "max_wait_time": 300
            },
            "workflow_conflicts": {
                "strategy": "dependency_ordering",
                "deadlock_timeout": 60,
                "max_dependency_depth": 10,
                "circular_dependency_action": "abort_lowest_priority"
            },
            "agent_conflicts": {
                "strategy": "capability_matching",
                "load_balance_factor": 0.3,
                "capability_weight": 0.7,
                "prefer_local_agents": True
            },
            "priority_settings": {
                "base_priorities": {
                    "critical": 10,
                    "high": 7,
                    "medium": 5,
                    "low": 3,
                    "background": 1
                },
                "aging_factor": 0.1,
                "sla_multipliers": {
                    "platinum": 1.5,
                    "gold": 1.2,
                    "silver": 1.0,
                    "bronze": 0.8
                }
            }
        }
    
    def get_policy(self, path: str, default: Any = None) -> Any:
        """Get a policy value by dot-separated path"""
        with self._lock:
            keys = path.split('.')
            value = self.policies
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
    
    def update_policy(self, path: str, value: Any):
        """Update a policy value by dot-separated path"""
        with self._lock:
            keys = path.split('.')
            current = self.policies
            
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            current[keys[-1]] = value
            logger.info(f"Updated policy {path} to {value}")
    
    def apply_policies(self, new_policies: Dict[str, Any]):
        """Replace current policies with new ones"""
        with self._lock:
            self.policies = new_policies
            logger.info("Applied new policy configuration")
    
    def get_resolution_strategy(self, conflict_type: ConflictType) -> ResolutionStrategy:
        """Get the resolution strategy for a conflict type"""
        strategy_map = {
            ConflictType.RESOURCE_ALLOCATION: self.get_policy("resource_conflicts.cpu.strategy", "priority_preemption"),
            ConflictType.DATA_ACCESS: self.get_policy("data_conflicts.strategy", "lock_escalation"),
            ConflictType.WORKFLOW_DEPENDENCY: self.get_policy("workflow_conflicts.strategy", "dependency_ordering"),
            ConflictType.AGENT_COMPETITION: self.get_policy("agent_conflicts.strategy", "capability_matching"),
            ConflictType.DEADLOCK: "abort_transaction"  # Always abort for deadlocks
        }
        
        strategy_name = strategy_map.get(conflict_type, "priority_preemption")
        try:
            return ResolutionStrategy(strategy_name)
        except ValueError:
            logger.warning(f"Unknown strategy {strategy_name}, using priority_preemption")
            return ResolutionStrategy.PRIORITY_PREEMPTION

# ============================================================================
# Resolution Strategies
# ============================================================================

class ConflictResolver:
    """Main conflict resolution engine"""
    
    def __init__(self, policy_manager: PolicyManager):
        self.policy_manager = policy_manager
        self.metrics = ConflictMetrics()
        self.active_resolutions: Dict[str, ConflictResolution] = {}
        
    def calculate_dynamic_priority(self, base_priority: ConflictPriority, 
                                 age: timedelta, sla_factor: float = 1.0) -> float:
        """Calculate dynamic priority with aging and SLA factors"""
        aging_factor = self.policy_manager.get_policy("priority_settings.aging_factor", 0.1)
        age_boost = min(age.total_seconds() / 3600 * aging_factor, 2.0)
        return base_priority.value * sla_factor + age_boost
    
    async def resolve_resource_conflict(self, conflict: ConflictInfo) -> ConflictResolution:
        """Resolve resource allocation conflicts using priority preemption"""
        strategy = ResolutionStrategy.PRIORITY_PREEMPTION
        actions = []
        
        # Sort requests by dynamic priority
        now = datetime.utcnow()
        sorted_requests = sorted(
            conflict.resource_requests,
            key=lambda req: self.calculate_dynamic_priority(
                req.priority, 
                now - req.timestamp
            ),
            reverse=True
        )
        
        # Calculate available resources
        resource_type = ResourceType(conflict.metadata.get("resource_type"))
        available = conflict.metadata.get("available", 0.0)
        
        # Allocate resources by priority
        allocated = 0.0
        granted_requests = []
        preempted_requests = []
        
        for request in sorted_requests:
            if allocated + request.amount <= available:
                # Grant the request
                allocated += request.amount
                granted_requests.append(request)
                
                actions.append(ResolutionAction(
                    action_type="grant_resource",
                    target_entity=request.requester_id,
                    parameters={
                        "resource_type": resource_type.value,
                        "amount": request.amount,
                        "grant_time": datetime.utcnow().isoformat()
                    },
                    execution_order=len(actions)
                ))
            else:
                # Preempt the request
                preempted_requests.append(request)
                
                actions.append(ResolutionAction(
                    action_type="preempt_resource",
                    target_entity=request.requester_id,
                    parameters={
                        "resource_type": resource_type.value,
                        "amount": request.amount,
                        "reason": "higher_priority_request",
                        "grace_period": self.policy_manager.get_policy(
                            "resource_conflicts.cpu.grace_period", 10
                        )
                    },
                    execution_order=len(actions)
                ))
        
        preemption_events.inc()
        
        return ConflictResolution(
            conflict_id=conflict.conflict_id,
            strategy=strategy,
            actions=actions,
            estimated_cost=len(preempted_requests) * 0.5,  # Cost of preemption
            success_probability=0.9,
            metadata={
                "granted_count": len(granted_requests),
                "preempted_count": len(preempted_requests),
                "total_allocated": allocated
            }
        )
    
    async def resolve_deadlock_conflict(self, conflict: ConflictInfo) -> ConflictResolution:
        """Resolve deadlock by aborting lowest priority participant"""
        strategy = ResolutionStrategy.ABORT_TRANSACTION
        actions = []
        
        # Find the lowest priority entity in the deadlock cycle
        cycle = conflict.deadlock_cycle or []
        if not cycle:
            logger.error("Deadlock conflict without cycle information")
            return ConflictResolution(
                conflict_id=conflict.conflict_id,
                strategy=strategy,
                actions=[],
                estimated_cost=1.0,
                success_probability=0.0
            )
        
        # For simplicity, abort the first entity in the cycle
        # In a real system, you'd calculate priorities and costs
        victim_entity = cycle[0]
        
        actions.append(ResolutionAction(
            action_type="abort_transaction",
            target_entity=victim_entity,
            parameters={
                "reason": "deadlock_resolution",
                "deadlock_cycle": cycle,
                "abort_time": datetime.utcnow().isoformat()
            },
            execution_order=0
        ))
        
        return ConflictResolution(
            conflict_id=conflict.conflict_id,
            strategy=strategy,
            actions=actions,
            estimated_cost=1.0,  # Cost of aborting a transaction
            success_probability=0.95,
            metadata={
                "victim_entity": victim_entity,
                "cycle_broken": True,
                "cycle_length": len(cycle)
            }
        )
    
    async def resolve_agent_competition(self, conflict: ConflictInfo) -> ConflictResolution:
        """Resolve agent competition using capability matching"""
        strategy = ResolutionStrategy.CAPABILITY_MATCHING
        actions = []
        
        task_id = conflict.metadata.get("task_id")
        candidates = conflict.involved_entities
        agent_loads = conflict.metadata.get("agent_loads", {})
        
        # Calculate scores for each candidate
        # In a real system, you'd get actual capability requirements
        required_capabilities = set()  # Would be retrieved from task definition
        
        best_agent = None
        best_score = -1.0
        
        for agent_id in candidates:
            # Simplified scoring: prefer less loaded agents
            load = agent_loads.get(agent_id, 0.0)
            score = 1.0 - load  # Higher score for lower load
            
            if score > best_score:
                best_score = score
                best_agent = agent_id
        
        if best_agent:
            # Assign task to best agent
            actions.append(ResolutionAction(
                action_type="assign_task",
                target_entity=best_agent,
                parameters={
                    "task_id": task_id,
                    "assignment_reason": "capability_matching",
                    "score": best_score,
                    "assignment_time": datetime.utcnow().isoformat()
                },
                execution_order=0
            ))
            
            # Notify other agents
            for agent_id in candidates:
                if agent_id != best_agent:
                    actions.append(ResolutionAction(
                        action_type="reject_assignment",
                        target_entity=agent_id,
                        parameters={
                            "task_id": task_id,
                            "reason": "assigned_to_better_candidate",
                            "selected_agent": best_agent
                        },
                        execution_order=1
                    ))
        
        return ConflictResolution(
            conflict_id=conflict.conflict_id,
            strategy=strategy,
            actions=actions,
            estimated_cost=0.1,  # Low cost for reassignment
            success_probability=0.98,
            metadata={
                "selected_agent": best_agent,
                "selection_score": best_score,
                "candidates_count": len(candidates)
            }
        )
    
    async def resolve_conflict(self, conflict: ConflictInfo) -> ConflictResolution:
        """Main conflict resolution method"""
        start_time = time.time()
        
        try:
            with tracer.start_as_current_span("resolve_conflict") as span:
                span.set_attribute("conflict_type", conflict.conflict_type.value)
                span.set_attribute("conflict_id", conflict.conflict_id)
                
                # Route to appropriate resolution strategy
                if conflict.conflict_type == ConflictType.RESOURCE_ALLOCATION:
                    resolution = await self.resolve_resource_conflict(conflict)
                elif conflict.conflict_type == ConflictType.DEADLOCK:
                    resolution = await self.resolve_deadlock_conflict(conflict)
                elif conflict.conflict_type == ConflictType.AGENT_COMPETITION:
                    resolution = await self.resolve_agent_competition(conflict)
                else:
                    # Default fallback resolution
                    resolution = ConflictResolution(
                        conflict_id=conflict.conflict_id,
                        strategy=ResolutionStrategy.ABORT_TRANSACTION,
                        actions=[],
                        estimated_cost=1.0,
                        success_probability=0.5
                    )
                
                # Track the resolution
                self.active_resolutions[conflict.conflict_id] = resolution
                
                # Record metrics
                resolution_time_seconds = time.time() - start_time
                resolution_time.observe(resolution_time_seconds)
                self.metrics.record_conflict(
                    conflict.conflict_type.value,
                    resolution_time_seconds,
                    len(resolution.actions) > 0
                )
                
                conflict_resolutions.labels(
                    resolution_strategy=resolution.strategy.value,
                    success="true"
                ).inc()
                
                logger.info(f"Resolved conflict {conflict.conflict_id} using {resolution.strategy.value}")
                return resolution
                
        except Exception as e:
            resolution_time_seconds = time.time() - start_time
            self.metrics.record_conflict(
                conflict.conflict_type.value,
                resolution_time_seconds,
                False
            )
            
            conflict_resolutions.labels(
                resolution_strategy="error",
                success="false"
            ).inc()
            
            logger.error(f"Failed to resolve conflict {conflict.conflict_id}: {e}")
            raise

# ============================================================================
# Main Conflict Resolution Manager
# ============================================================================

class ConflictResolutionManager:
    """Main manager for the conflict resolution system"""
    
    def __init__(self, policy_config: Optional[Dict[str, Any]] = None):
        self.policy_manager = PolicyManager(policy_config)
        self.resolver = ConflictResolver(self.policy_manager)
        
        # Initialize detectors
        self.resource_detector = ResourceConflictDetector({
            ResourceType.CPU: 100.0,
            ResourceType.MEMORY: 1000.0,  # GB
            ResourceType.STORAGE: 10000.0  # GB
        })
        
        self.deadlock_detector = DeadlockDetector()
        self.agent_detector = AgentCompetitionDetector()
        
        self.detectors = [
            self.resource_detector,
            self.deadlock_detector,
            self.agent_detector
        ]
        
        self.monitoring_tasks: List[asyncio.Task] = []
        self.running = False
        
    async def start(self):
        """Start the conflict resolution system"""
        if self.running:
            return
            
        self.running = True
        
        # Start monitoring tasks for each detector
        for detector in self.detectors:
            task = asyncio.create_task(detector.monitor_continuously())
            self.monitoring_tasks.append(task)
        
        # Start main resolution loop
        resolution_task = asyncio.create_task(self._resolution_loop())
        self.monitoring_tasks.append(resolution_task)
        
        logger.info("Conflict resolution system started")
    
    async def stop(self):
        """Stop the conflict resolution system"""
        if not self.running:
            return
            
        self.running = False
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        self.monitoring_tasks.clear()
        
        logger.info("Conflict resolution system stopped")
    
    async def _resolution_loop(self):
        """Main resolution loop"""
        while self.running:
            try:
                # Collect conflicts from all detectors
                all_conflicts = []
                for detector in self.detectors:
                    conflicts = await detector.detect_conflicts()
                    all_conflicts.extend(conflicts)
                
                # Resolve conflicts in priority order
                all_conflicts.sort(key=lambda c: c.priority.value, reverse=True)
                
                for conflict in all_conflicts:
                    if conflict.conflict_id not in self.resolver.active_resolutions:
                        try:
                            resolution = await self.resolver.resolve_conflict(conflict)
                            await self._execute_resolution(resolution)
                        except Exception as e:
                            logger.error(f"Failed to resolve conflict {conflict.conflict_id}: {e}")
                
                # Sleep before next iteration
                interval = self.policy_manager.get_policy("detection_interval", 5)
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in resolution loop: {e}")
                await asyncio.sleep(5)  # Error recovery delay
    
    async def _execute_resolution(self, resolution: ConflictResolution):
        """Execute a conflict resolution"""
        logger.info(f"Executing resolution for conflict {resolution.conflict_id}")
        
        # Sort actions by execution order
        sorted_actions = sorted(resolution.actions, key=lambda a: a.execution_order)
        
        for action in sorted_actions:
            try:
                await self._execute_action(action)
            except Exception as e:
                logger.error(f"Failed to execute action {action.action_type} for {action.target_entity}: {e}")
        
        # Mark resolution as complete
        if resolution.conflict_id in self.resolver.active_resolutions:
            del self.resolver.active_resolutions[resolution.conflict_id]
        
        active_conflicts.dec()
    
    async def _execute_action(self, action: ResolutionAction):
        """Execute a single resolution action"""
        # This would integrate with the actual system components
        # For now, just log the actions
        logger.info(f"Executing {action.action_type} on {action.target_entity}: {action.parameters}")
        
        # In a real system, this would:
        # - Send messages to agents
        # - Update resource allocations
        # - Abort transactions
        # - Reassign tasks
        # etc.

# Export main classes
__all__ = [
    'ConflictResolutionManager',
    'ConflictInfo',
    'ConflictType',
    'ResolutionStrategy',
    'PolicyManager',
    'ConflictResolver',
    'ResourceConflictDetector',
    'DeadlockDetector',
    'AgentCompetitionDetector'
] 