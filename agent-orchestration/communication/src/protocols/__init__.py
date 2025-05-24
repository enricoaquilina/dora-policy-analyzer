"""
DORA Compliance Agent Communication Protocols

This module provides standardized communication protocols for inter-agent
communication and external system integration.
"""

import asyncio
import json
import uuid
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union, Protocol
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
import base64
import hashlib
import hmac

# Third-party imports
import aiohttp
import aioredis
import aiokafka
import websockets
import pika
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from prometheus_client import Counter, Histogram, Gauge
from opentelemetry import trace

# Configure logging
logger = logging.getLogger(__name__)

# Metrics
messages_sent = Counter('agent_messages_sent_total', 'Total sent messages', ['agent_type', 'destination', 'transport'])
messages_received = Counter('agent_messages_received_total', 'Total received messages', ['agent_type', 'source', 'transport'])
message_duration = Histogram('agent_message_duration_seconds', 'Message processing time', ['message_type', 'transport'])
active_connections = Gauge('agent_active_connections', 'Active connections', ['protocol', 'agent_type'])
message_errors = Counter('agent_message_errors_total', 'Message errors', ['error_type', 'transport'])

# Get tracer
tracer = trace.get_tracer(__name__)

# ============================================================================
# Core Enums and Data Structures
# ============================================================================

class MessageType(Enum):
    """Message types for agent communication"""
    TASK_REQUEST = "task_request"
    TASK_STATUS = "task_status"
    TASK_RESULT = "task_result"
    TASK_CANCEL = "task_cancel"
    HEARTBEAT = "heartbeat"
    EVENT = "event"
    COMMAND = "command"
    RESPONSE = "response"
    ERROR = "error"
    ACK = "ack"

class TransportType(Enum):
    """Supported transport protocols"""
    HTTP = "http"
    GRPC = "grpc"
    KAFKA = "kafka"
    WEBSOCKET = "websocket"
    AMQP = "amqp"

class SecurityLevel(Enum):
    """Security levels for messages"""
    NONE = "none"
    BASIC = "basic"
    ENCRYPTED = "encrypted"
    SIGNED = "signed"
    FULL = "full"  # Encrypted + Signed

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AgentInfo:
    """Information about an agent"""
    agent_id: str
    agent_type: str
    instance_id: Optional[str] = None
    version: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)

@dataclass
class SecurityInfo:
    """Security information for messages"""
    encrypted: bool = False
    signed: bool = False
    signature: Optional[str] = None
    auth_token: Optional[str] = None
    encryption_key_id: Optional[str] = None

@dataclass
class RoutingInfo:
    """Routing information for messages"""
    priority: MessagePriority = MessagePriority.MEDIUM
    ttl: Optional[int] = None  # Time to live in seconds
    retry_count: int = 0
    max_retries: int = 3
    broadcast: bool = False
    routing_key: Optional[str] = None

@dataclass
class TracingInfo:
    """Distributed tracing information"""
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)

@dataclass
class MessageHeader:
    """Standard message header"""
    message_id: str
    correlation_id: str
    causation_id: Optional[str]
    timestamp: datetime
    version: str
    source: AgentInfo
    destination: AgentInfo
    message_type: MessageType
    content_type: str = "application/json"
    encoding: str = "utf-8"
    security: SecurityInfo = field(default_factory=SecurityInfo)
    routing: RoutingInfo = field(default_factory=RoutingInfo)
    tracing: TracingInfo = field(default_factory=TracingInfo)

    def to_dict(self) -> Dict[str, Any]:
        """Convert header to dictionary"""
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "source": asdict(self.source),
            "destination": asdict(self.destination),
            "message_type": self.message_type.value,
            "content_type": self.content_type,
            "encoding": self.encoding,
            "security": asdict(self.security),
            "routing": asdict(self.routing),
            "tracing": asdict(self.tracing)
        }

@dataclass
class Message:
    """Standard message structure"""
    header: MessageHeader
    payload: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "header": self.header.to_dict(),
            "payload": self.payload
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        header_data = data["header"]
        
        # Reconstruct header
        header = MessageHeader(
            message_id=header_data["message_id"],
            correlation_id=header_data["correlation_id"],
            causation_id=header_data.get("causation_id"),
            timestamp=datetime.fromisoformat(header_data["timestamp"]),
            version=header_data["version"],
            source=AgentInfo(**header_data["source"]),
            destination=AgentInfo(**header_data["destination"]),
            message_type=MessageType(header_data["message_type"]),
            content_type=header_data.get("content_type", "application/json"),
            encoding=header_data.get("encoding", "utf-8"),
            security=SecurityInfo(**header_data.get("security", {})),
            routing=RoutingInfo(**header_data.get("routing", {})),
            tracing=TracingInfo(**header_data.get("tracing", {}))
        )
        
        return cls(header=header, payload=data["payload"])
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

# ============================================================================
# Transport Protocol Interfaces
# ============================================================================

class Transport(ABC):
    """Abstract base class for transport protocols"""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the transport"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the transport"""
        pass
    
    @abstractmethod
    async def send_message(self, message: Message, destination: str) -> bool:
        """Send a message to a destination"""
        pass
    
    @abstractmethod
    async def receive_messages(self, handler: Callable[[Message], None]) -> None:
        """Start receiving messages and call handler for each"""
        pass
    
    @abstractmethod
    def get_transport_type(self) -> TransportType:
        """Get the transport type"""
        pass

class MessageHandler(Protocol):
    """Protocol for message handlers"""
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle a received message and optionally return a response"""
        pass

# ============================================================================
# HTTP/REST Transport Implementation
# ============================================================================

class HTTPTransport(Transport):
    """HTTP/REST transport implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get("host", "0.0.0.0")
        self.port = config.get("port", 8080)
        self.tls_enabled = config.get("tls", False)
        self.cert_file = config.get("cert_file")
        self.key_file = config.get("key_file")
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.app: Optional[aiohttp.web.Application] = None
        self.server: Optional[aiohttp.web.AppRunner] = None
        self.handlers: Dict[str, MessageHandler] = {}
        
    async def start(self) -> None:
        """Start HTTP server and client"""
        # Create client session
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "DORA-Agent-Communication/1.0"}
        )
        
        # Create server application
        self.app = aiohttp.web.Application()
        self.app.router.add_post("/api/v1/messages", self._handle_http_message)
        self.app.router.add_get("/api/v1/health", self._handle_health_check)
        
        # Start server
        self.server = aiohttp.web.AppRunner(self.app)
        await self.server.setup()
        
        if self.tls_enabled and self.cert_file and self.key_file:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self.cert_file, self.key_file)
            site = aiohttp.web.TCPSite(self.server, self.host, self.port, ssl_context=ssl_context)
        else:
            site = aiohttp.web.TCPSite(self.server, self.host, self.port)
        
        await site.start()
        logger.info(f"HTTP transport started on {self.host}:{self.port} (TLS: {self.tls_enabled})")
    
    async def stop(self) -> None:
        """Stop HTTP server and client"""
        if self.server:
            await self.server.cleanup()
        if self.session:
            await self.session.close()
        logger.info("HTTP transport stopped")
    
    async def send_message(self, message: Message, destination: str) -> bool:
        """Send message via HTTP POST"""
        if not self.session:
            raise RuntimeError("HTTP transport not started")
        
        with tracer.start_as_current_span("http_send_message") as span:
            span.set_attribute("destination", destination)
            span.set_attribute("message_type", message.header.message_type.value)
            
            try:
                url = f"http{'s' if self.tls_enabled else ''}://{destination}/api/v1/messages"
                headers = {
                    "Content-Type": "application/json",
                    "X-Correlation-ID": message.header.correlation_id,
                    "X-Message-Type": message.header.message_type.value
                }
                
                if message.header.security.auth_token:
                    headers["Authorization"] = f"Bearer {message.header.security.auth_token}"
                
                start_time = time.time()
                async with self.session.post(url, json=message.to_dict(), headers=headers) as response:
                    response.raise_for_status()
                    duration = time.time() - start_time
                    
                    # Record metrics
                    messages_sent.labels(
                        agent_type=message.header.source.agent_type,
                        destination=message.header.destination.agent_id,
                        transport="http"
                    ).inc()
                    
                    message_duration.labels(
                        message_type=message.header.message_type.value,
                        transport="http"
                    ).observe(duration)
                    
                    span.set_attribute("response_status", response.status)
                    span.set_attribute("duration", duration)
                    
                    logger.debug(f"Message sent via HTTP to {destination} (status: {response.status})")
                    return True
                    
            except Exception as e:
                message_errors.labels(error_type=type(e).__name__, transport="http").inc()
                span.record_exception(e)
                span.set_attribute("error", True)
                logger.error(f"Failed to send message via HTTP to {destination}: {e}")
                return False
    
    async def receive_messages(self, handler: Callable[[Message], None]) -> None:
        """Register message handler for HTTP transport"""
        # HTTP is request-response, so we don't actively receive messages
        # Messages come through the _handle_http_message endpoint
        pass
    
    def get_transport_type(self) -> TransportType:
        """Get transport type"""
        return TransportType.HTTP
    
    async def _handle_http_message(self, request: aiohttp.web.Request) -> aiohttp.web.Response:
        """Handle incoming HTTP message"""
        try:
            data = await request.json()
            message = Message.from_dict(data)
            
            # Record metrics
            messages_received.labels(
                agent_type=message.header.destination.agent_type,
                source=message.header.source.agent_id,
                transport="http"
            ).inc()
            
            # Handle the message (this would be implemented by the agent)
            logger.debug(f"Received HTTP message: {message.header.message_type.value}")
            
            return aiohttp.web.json_response({"status": "received"})
            
        except Exception as e:
            message_errors.labels(error_type=type(e).__name__, transport="http").inc()
            logger.error(f"Error handling HTTP message: {e}")
            return aiohttp.web.json_response(
                {"error": str(e)}, 
                status=400
            )
    
    async def _handle_health_check(self, request: aiohttp.web.Request) -> aiohttp.web.Response:
        """Handle health check request"""
        return aiohttp.web.json_response({
            "status": "healthy",
            "transport": "http",
            "timestamp": datetime.utcnow().isoformat()
        })

# ============================================================================
# Kafka Transport Implementation
# ============================================================================

class KafkaTransport(Transport):
    """Apache Kafka transport implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.brokers = config.get("brokers", ["localhost:9092"])
        self.group_id = config.get("group_id", "dora-agents")
        self.topic_prefix = config.get("topic_prefix", "agent")
        
        self.producer: Optional[aiokafka.AIOKafkaProducer] = None
        self.consumer: Optional[aiokafka.AIOKafkaConsumer] = None
        self.message_handler: Optional[Callable[[Message], None]] = None
        
    async def start(self) -> None:
        """Start Kafka producer and consumer"""
        # Create producer
        self.producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=self.brokers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type="snappy",
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=1
        )
        await self.producer.start()
        
        # Create consumer
        self.consumer = aiokafka.AIOKafkaConsumer(
            f"{self.topic_prefix}-messages",
            bootstrap_servers=self.brokers,
            group_id=self.group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        await self.consumer.start()
        
        logger.info(f"Kafka transport started (brokers: {self.brokers})")
    
    async def stop(self) -> None:
        """Stop Kafka producer and consumer"""
        if self.producer:
            await self.producer.stop()
        if self.consumer:
            await self.consumer.stop()
        logger.info("Kafka transport stopped")
    
    async def send_message(self, message: Message, destination: str) -> bool:
        """Send message via Kafka"""
        if not self.producer:
            raise RuntimeError("Kafka transport not started")
        
        with tracer.start_as_current_span("kafka_send_message") as span:
            span.set_attribute("destination", destination)
            span.set_attribute("message_type", message.header.message_type.value)
            
            try:
                topic = f"{self.topic_prefix}-{message.header.destination.agent_type}"
                key = message.header.destination.agent_id
                
                start_time = time.time()
                await self.producer.send_and_wait(
                    topic,
                    value=message.to_dict(),
                    key=key.encode('utf-8')
                )
                duration = time.time() - start_time
                
                # Record metrics
                messages_sent.labels(
                    agent_type=message.header.source.agent_type,
                    destination=message.header.destination.agent_id,
                    transport="kafka"
                ).inc()
                
                message_duration.labels(
                    message_type=message.header.message_type.value,
                    transport="kafka"
                ).observe(duration)
                
                span.set_attribute("topic", topic)
                span.set_attribute("duration", duration)
                
                logger.debug(f"Message sent via Kafka to topic {topic}")
                return True
                
            except Exception as e:
                message_errors.labels(error_type=type(e).__name__, transport="kafka").inc()
                span.record_exception(e)
                span.set_attribute("error", True)
                logger.error(f"Failed to send message via Kafka: {e}")
                return False
    
    async def receive_messages(self, handler: Callable[[Message], None]) -> None:
        """Start receiving messages from Kafka"""
        if not self.consumer:
            raise RuntimeError("Kafka transport not started")
        
        self.message_handler = handler
        
        async for msg in self.consumer:
            try:
                message = Message.from_dict(msg.value)
                
                # Record metrics
                messages_received.labels(
                    agent_type=message.header.destination.agent_type,
                    source=message.header.source.agent_id,
                    transport="kafka"
                ).inc()
                
                # Handle the message
                if self.message_handler:
                    await self.message_handler(message)
                
                # Commit offset
                await self.consumer.commit()
                
            except Exception as e:
                message_errors.labels(error_type=type(e).__name__, transport="kafka").inc()
                logger.error(f"Error processing Kafka message: {e}")
    
    def get_transport_type(self) -> TransportType:
        """Get transport type"""
        return TransportType.KAFKA

# ============================================================================
# WebSocket Transport Implementation
# ============================================================================

class WebSocketTransport(Transport):
    """WebSocket transport implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get("host", "0.0.0.0")
        self.port = config.get("port", 8081)
        self.path = config.get("path", "/ws")
        
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.message_handler: Optional[Callable[[Message], None]] = None
        self.server = None
        
    async def start(self) -> None:
        """Start WebSocket server"""
        self.server = await websockets.serve(
            self._handle_websocket_connection,
            self.host,
            self.port,
            path=self.path
        )
        logger.info(f"WebSocket transport started on ws://{self.host}:{self.port}{self.path}")
    
    async def stop(self) -> None:
        """Stop WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("WebSocket transport stopped")
    
    async def send_message(self, message: Message, destination: str) -> bool:
        """Send message via WebSocket"""
        connection = self.connections.get(destination)
        if not connection:
            logger.warning(f"No WebSocket connection found for {destination}")
            return False
        
        with tracer.start_as_current_span("websocket_send_message") as span:
            span.set_attribute("destination", destination)
            span.set_attribute("message_type", message.header.message_type.value)
            
            try:
                start_time = time.time()
                await connection.send(message.to_json())
                duration = time.time() - start_time
                
                # Record metrics
                messages_sent.labels(
                    agent_type=message.header.source.agent_type,
                    destination=destination,
                    transport="websocket"
                ).inc()
                
                message_duration.labels(
                    message_type=message.header.message_type.value,
                    transport="websocket"
                ).observe(duration)
                
                span.set_attribute("duration", duration)
                
                logger.debug(f"Message sent via WebSocket to {destination}")
                return True
                
            except Exception as e:
                message_errors.labels(error_type=type(e).__name__, transport="websocket").inc()
                span.record_exception(e)
                span.set_attribute("error", True)
                logger.error(f"Failed to send WebSocket message to {destination}: {e}")
                return False
    
    async def receive_messages(self, handler: Callable[[Message], None]) -> None:
        """Register message handler for WebSocket transport"""
        self.message_handler = handler
    
    def get_transport_type(self) -> TransportType:
        """Get transport type"""
        return TransportType.WEBSOCKET
    
    async def _handle_websocket_connection(self, websocket, path):
        """Handle new WebSocket connection"""
        agent_id = None
        try:
            # Register connection (agent_id would be extracted from handshake)
            agent_id = f"ws-{id(websocket)}"  # Simplified for demo
            self.connections[agent_id] = websocket
            
            active_connections.labels(protocol="websocket", agent_type="unknown").inc()
            
            async for message_data in websocket:
                try:
                    message = Message.from_json(message_data)
                    
                    # Record metrics
                    messages_received.labels(
                        agent_type=message.header.destination.agent_type,
                        source=message.header.source.agent_id,
                        transport="websocket"
                    ).inc()
                    
                    # Handle the message
                    if self.message_handler:
                        await self.message_handler(message)
                        
                except Exception as e:
                    message_errors.labels(error_type=type(e).__name__, transport="websocket").inc()
                    logger.error(f"Error processing WebSocket message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.debug(f"WebSocket connection closed for {agent_id}")
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            if agent_id and agent_id in self.connections:
                del self.connections[agent_id]
                active_connections.labels(protocol="websocket", agent_type="unknown").dec()

# ============================================================================
# Security Handler
# ============================================================================

class SecurityHandler:
    """Handles message encryption, signing, and authentication"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.encryption_key = config.get("encryption_key")
        self.signing_key = config.get("signing_key")
        self.jwt_secret = config.get("jwt_secret", "default-secret")
        self.cipher = Fernet(self.encryption_key) if self.encryption_key else None
        
    def encrypt_message(self, message: Message) -> Message:
        """Encrypt message payload"""
        if not self.cipher:
            return message
        
        payload_bytes = json.dumps(message.payload).encode('utf-8')
        encrypted_payload = self.cipher.encrypt(payload_bytes)
        
        # Update message
        message.payload = {"encrypted_data": base64.b64encode(encrypted_payload).decode('utf-8')}
        message.header.security.encrypted = True
        
        return message
    
    def decrypt_message(self, message: Message) -> Message:
        """Decrypt message payload"""
        if not message.header.security.encrypted or not self.cipher:
            return message
        
        encrypted_data = base64.b64decode(message.payload["encrypted_data"])
        decrypted_bytes = self.cipher.decrypt(encrypted_data)
        message.payload = json.loads(decrypted_bytes.decode('utf-8'))
        
        return message
    
    def sign_message(self, message: Message) -> Message:
        """Sign message with digital signature"""
        if not self.signing_key:
            return message
        
        # Create signature of the message content
        message_content = json.dumps(message.to_dict(), sort_keys=True)
        signature = hmac.new(
            self.signing_key.encode('utf-8'),
            message_content.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        message.header.security.signed = True
        message.header.security.signature = signature
        
        return message
    
    def verify_signature(self, message: Message) -> bool:
        """Verify message signature"""
        if not message.header.security.signed or not self.signing_key:
            return True  # No signature to verify
        
        # Extract signature
        signature = message.header.security.signature
        message.header.security.signature = None
        
        # Recreate signature
        message_content = json.dumps(message.to_dict(), sort_keys=True)
        expected_signature = hmac.new(
            self.signing_key.encode('utf-8'),
            message_content.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Restore signature
        message.header.security.signature = signature
        
        return hmac.compare_digest(signature, expected_signature)
    
    def create_jwt_token(self, agent_info: AgentInfo) -> str:
        """Create JWT token for agent authentication"""
        payload = {
            "agent_id": agent_info.agent_id,
            "agent_type": agent_info.agent_type,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.InvalidTokenError:
            return None

# ============================================================================
# Communication Manager
# ============================================================================

class CommunicationManager:
    """Central manager for all communication protocols"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_info = AgentInfo(
            agent_id=config["agent_id"],
            agent_type=config["agent_type"],
            instance_id=config.get("instance_id"),
            version=config.get("version", "1.0.0")
        )
        
        self.transports: Dict[TransportType, Transport] = {}
        self.security_handler = SecurityHandler(config.get("security", {}))
        self.message_handlers: Dict[MessageType, Callable[[Message], Optional[Message]]] = {}
        
        self._setup_transports()
    
    def _setup_transports(self):
        """Setup configured transports"""
        transport_configs = self.config.get("transports", {})
        
        if "http" in transport_configs:
            self.transports[TransportType.HTTP] = HTTPTransport(transport_configs["http"])
        
        if "kafka" in transport_configs:
            self.transports[TransportType.KAFKA] = KafkaTransport(transport_configs["kafka"])
        
        if "websocket" in transport_configs:
            self.transports[TransportType.WEBSOCKET] = WebSocketTransport(transport_configs["websocket"])
    
    async def start(self):
        """Start all configured transports"""
        for transport in self.transports.values():
            await transport.start()
        
        # Start message receiving for each transport
        for transport in self.transports.values():
            asyncio.create_task(transport.receive_messages(self._handle_received_message))
        
        logger.info(f"Communication manager started for agent {self.agent_info.agent_id}")
    
    async def stop(self):
        """Stop all transports"""
        for transport in self.transports.values():
            await transport.stop()
        logger.info("Communication manager stopped")
    
    def register_handler(self, message_type: MessageType, handler: Callable[[Message], Optional[Message]]):
        """Register handler for specific message type"""
        self.message_handlers[message_type] = handler
    
    async def send_message(self, 
                         message_type: MessageType,
                         destination_agent: AgentInfo,
                         payload: Dict[str, Any],
                         transport_type: TransportType = TransportType.HTTP,
                         correlation_id: Optional[str] = None,
                         priority: MessagePriority = MessagePriority.MEDIUM) -> bool:
        """Send a message to another agent"""
        
        # Create message
        message = Message(
            header=MessageHeader(
                message_id=str(uuid.uuid4()),
                correlation_id=correlation_id or str(uuid.uuid4()),
                causation_id=None,
                timestamp=datetime.utcnow(),
                version="1.0.0",
                source=self.agent_info,
                destination=destination_agent,
                message_type=message_type,
                routing=RoutingInfo(priority=priority)
            ),
            payload=payload
        )
        
        # Apply security
        if self.config.get("security", {}).get("encryption", False):
            message = self.security_handler.encrypt_message(message)
        
        if self.config.get("security", {}).get("signing", False):
            message = self.security_handler.sign_message(message)
        
        if self.config.get("security", {}).get("authentication", False):
            token = self.security_handler.create_jwt_token(self.agent_info)
            message.header.security.auth_token = token
        
        # Send via selected transport
        transport = self.transports.get(transport_type)
        if not transport:
            logger.error(f"Transport {transport_type} not available")
            return False
        
        return await transport.send_message(message, destination_agent.agent_id)
    
    async def _handle_received_message(self, message: Message):
        """Handle received message"""
        with tracer.start_as_current_span("handle_received_message") as span:
            span.set_attribute("message_type", message.header.message_type.value)
            span.set_attribute("source_agent", message.header.source.agent_id)
            
            try:
                # Verify security
                if message.header.security.signed:
                    if not self.security_handler.verify_signature(message):
                        logger.warning("Message signature verification failed")
                        return
                
                if message.header.security.encrypted:
                    message = self.security_handler.decrypt_message(message)
                
                # Find handler
                handler = self.message_handlers.get(message.header.message_type)
                if not handler:
                    logger.warning(f"No handler for message type: {message.header.message_type}")
                    return
                
                # Handle message
                response = await handler(message)
                
                # Send response if provided
                if response:
                    response.header.correlation_id = message.header.correlation_id
                    response.header.causation_id = message.header.message_id
                    
                    # Send response back to sender
                    transport_type = TransportType.HTTP  # Default response transport
                    await self.send_message(
                        message_type=response.header.message_type,
                        destination_agent=message.header.source,
                        payload=response.payload,
                        transport_type=transport_type,
                        correlation_id=response.header.correlation_id
                    )
                
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Error handling received message: {e}")

# Export main classes
__all__ = [
    'CommunicationManager',
    'Message',
    'MessageHeader',
    'MessageType',
    'TransportType',
    'AgentInfo',
    'SecurityHandler',
    'HTTPTransport',
    'KafkaTransport', 
    'WebSocketTransport',
    'SecurityLevel',
    'MessagePriority'
] 