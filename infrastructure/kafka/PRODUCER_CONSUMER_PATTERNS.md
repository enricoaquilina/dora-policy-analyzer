# Producer and Consumer Patterns for DORA Compliance System

This document outlines the recommended patterns for producing and consuming messages in the DORA Compliance System's Kafka infrastructure.

## Overview

The DORA compliance system uses Apache Kafka for asynchronous communication between microservices and AI agents. Each component should follow specific patterns to ensure reliability, scalability, and maintainability.

## Producer Patterns

### 1. Idempotent Producers

All producers must be configured for idempotency to prevent duplicate messages during retries.

```python
# Python example using kafka-python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['dora-kafka-cluster-kafka-bootstrap:9092'],
    security_protocol='SASL_SSL',
    sasl_mechanism='SCRAM-SHA-256',
    sasl_plain_username='dora-agent-user',
    sasl_plain_password='<password-from-secret>',
    
    # Idempotency settings
    enable_idempotence=True,
    acks='all',
    retries=3,
    max_in_flight_requests_per_connection=1,
    
    # Serialization
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8') if k else None,
    
    # Performance
    compression_type='snappy',
    batch_size=16384,
    linger_ms=10
)
```

### 2. Agent Event Producer Pattern

```python
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

class AgentEventProducer:
    def __init__(self, producer: KafkaProducer, agent_id: str, agent_type: str):
        self.producer = producer
        self.agent_id = agent_id
        self.agent_type = agent_type
    
    def send_event(self, event_type: str, status: str, 
                   message: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None,
                   task_id: Optional[str] = None) -> None:
        """Send an agent event to Kafka."""
        
        event = {
            "eventId": str(uuid.uuid4()),
            "agentId": self.agent_id,
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "eventType": event_type,
            "agentType": self.agent_type,
            "status": status,
            "version": "1.0.0",
            "message": message,
            "metadata": metadata or {},
            "taskId": task_id
        }
        
        # Use agent_id as partition key for ordering
        self.producer.send(
            topic='agent-events',
            key=self.agent_id,
            value=event
        )
    
    def send_heartbeat(self, resource_usage: Optional[Dict] = None) -> None:
        """Send heartbeat with optional resource usage."""
        self.send_event(
            event_type="HEARTBEAT",
            status="HEALTHY",
            metadata={"resource_usage": resource_usage} if resource_usage else None
        )
    
    def send_task_completion(self, task_id: str, result: Dict[str, Any]) -> None:
        """Send task completion event."""
        self.send_event(
            event_type="TASK_COMPLETED",
            status="HEALTHY",
            task_id=task_id,
            metadata={"result_summary": result}
        )
```

### 3. Compliance Report Producer Pattern

```python
class ComplianceReportProducer:
    def __init__(self, producer: KafkaProducer):
        self.producer = producer
    
    def send_gap_assessment(self, organization_id: str, 
                           assessment_data: Dict[str, Any]) -> None:
        """Send gap assessment results."""
        
        report = {
            "reportId": str(uuid.uuid4()),
            "organizationId": organization_id,
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "reportType": "GAP_ASSESSMENT",
            "data": assessment_data,
            "version": "1.0"
        }
        
        # Use organization_id as partition key
        self.producer.send(
            topic='gap-assessments',
            key=organization_id,
            value=report
        )
    
    def send_risk_assessment(self, organization_id: str,
                            risk_data: Dict[str, Any]) -> None:
        """Send risk assessment results."""
        
        report = {
            "reportId": str(uuid.uuid4()),
            "organizationId": organization_id,
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "reportType": "RISK_ASSESSMENT", 
            "riskScore": risk_data.get("overall_score"),
            "riskLevel": risk_data.get("risk_level"),
            "data": risk_data,
            "version": "1.0"
        }
        
        self.producer.send(
            topic='risk-assessments',
            key=organization_id,
            value=report
        )
```

### 4. Audit Event Producer Pattern

```python
class AuditEventProducer:
    def __init__(self, producer: KafkaProducer):
        self.producer = producer
    
    def send_user_activity(self, user_id: str, action: str,
                          resource: str, details: Dict[str, Any]) -> None:
        """Send user activity audit event."""
        
        audit_event = {
            "eventId": str(uuid.uuid4()),
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "userId": user_id,
            "action": action,
            "resource": resource,
            "details": details,
            "ipAddress": details.get("ip_address"),
            "userAgent": details.get("user_agent"),
            "sessionId": details.get("session_id")
        }
        
        # Use timestamp-based partitioning for audit logs
        partition_key = f"{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        
        self.producer.send(
            topic='user-activities',
            key=partition_key,
            value=audit_event
        )
```

## Consumer Patterns

### 1. Reliable Consumer Configuration

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'agent-events',
    bootstrap_servers=['dora-kafka-cluster-kafka-bootstrap:9092'],
    security_protocol='SASL_SSL',
    sasl_mechanism='SCRAM-SHA-256',
    sasl_plain_username='dora-orchestrator-user',
    sasl_plain_password='<password-from-secret>',
    
    # Consumer group for load balancing
    group_id='agent-event-processor',
    
    # Offset management
    auto_offset_reset='earliest',
    enable_auto_commit=False,  # Manual commit for reliability
    
    # Deserialization
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    key_deserializer=lambda k: k.decode('utf-8') if k else None,
    
    # Performance
    fetch_min_bytes=1024,
    fetch_max_wait_ms=500,
    max_poll_records=100
)
```

### 2. Agent Event Consumer Pattern

```python
import logging
from typing import Dict, Any

class AgentEventConsumer:
    def __init__(self, consumer: KafkaConsumer):
        self.consumer = consumer
        self.logger = logging.getLogger(__name__)
    
    def process_events(self) -> None:
        """Process agent events with error handling and manual commits."""
        
        try:
            for message in self.consumer:
                try:
                    # Process the event
                    self.handle_agent_event(message.value)
                    
                    # Commit offset after successful processing
                    self.consumer.commit()
                    
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
                    # Send to dead letter queue
                    self.send_to_dlq(message)
                    # Continue processing next message
                    self.consumer.commit()
        
        except KeyboardInterrupt:
            self.logger.info("Consumer interrupted")
        finally:
            self.consumer.close()
    
    def handle_agent_event(self, event: Dict[str, Any]) -> None:
        """Handle specific agent event types."""
        
        event_type = event.get('eventType')
        agent_id = event.get('agentId')
        
        if event_type == 'HEARTBEAT':
            self.update_agent_health_status(agent_id, event)
        elif event_type == 'TASK_COMPLETED':
            self.process_task_completion(agent_id, event)
        elif event_type == 'ERROR':
            self.handle_agent_error(agent_id, event)
        else:
            self.logger.warning(f"Unknown event type: {event_type}")
    
    def update_agent_health_status(self, agent_id: str, event: Dict[str, Any]) -> None:
        """Update agent health status in the system."""
        # Implementation for health status update
        pass
    
    def process_task_completion(self, agent_id: str, event: Dict[str, Any]) -> None:
        """Process task completion and trigger next steps."""
        # Implementation for task completion handling
        pass
    
    def handle_agent_error(self, agent_id: str, event: Dict[str, Any]) -> None:
        """Handle agent error events."""
        # Implementation for error handling
        pass
    
    def send_to_dlq(self, message) -> None:
        """Send failed message to dead letter queue."""
        # Implementation for DLQ handling
        pass
```

### 3. Batch Processing Consumer Pattern

```python
class BatchComplianceProcessor:
    def __init__(self, consumer: KafkaConsumer, batch_size: int = 100):
        self.consumer = consumer
        self.batch_size = batch_size
        self.batch = []
    
    def process_in_batches(self) -> None:
        """Process compliance reports in batches for efficiency."""
        
        try:
            for message in self.consumer:
                self.batch.append(message.value)
                
                if len(self.batch) >= self.batch_size:
                    self.process_batch()
                    self.batch.clear()
                    self.consumer.commit()
        
        except KeyboardInterrupt:
            if self.batch:
                self.process_batch()
                self.consumer.commit()
        finally:
            self.consumer.close()
    
    def process_batch(self) -> None:
        """Process a batch of compliance reports."""
        try:
            # Bulk process the batch
            results = self.bulk_analyze_compliance(self.batch)
            
            # Store results
            self.store_batch_results(results)
            
        except Exception as e:
            logging.error(f"Batch processing failed: {e}")
            # Handle individual messages
            for item in self.batch:
                try:
                    self.process_single_item(item)
                except Exception as item_error:
                    logging.error(f"Item processing failed: {item_error}")
```

### 4. Stream Processing Consumer Pattern

```python
from kafka import TopicPartition
from collections import defaultdict
import time

class RealTimeRiskProcessor:
    def __init__(self, consumer: KafkaConsumer):
        self.consumer = consumer
        self.risk_scores = defaultdict(list)
        self.window_size = 300  # 5 minutes
    
    def process_real_time_risk(self) -> None:
        """Process risk events in real-time with windowing."""
        
        for message in self.consumer:
            try:
                event = message.value
                org_id = event.get('organizationId')
                timestamp = event.get('timestamp', time.time() * 1000)
                risk_score = event.get('riskScore', 0)
                
                # Add to time window
                self.add_to_window(org_id, timestamp, risk_score)
                
                # Calculate moving average
                avg_risk = self.calculate_window_average(org_id, timestamp)
                
                # Check for risk threshold breaches
                if avg_risk > 0.8:  # High risk threshold
                    self.trigger_risk_alert(org_id, avg_risk)
                
                self.consumer.commit()
                
            except Exception as e:
                logging.error(f"Real-time processing error: {e}")
                self.consumer.commit()  # Skip problematic message
    
    def add_to_window(self, org_id: str, timestamp: float, risk_score: float) -> None:
        """Add risk score to time window."""
        self.risk_scores[org_id].append((timestamp, risk_score))
        
        # Clean old entries
        cutoff = timestamp - (self.window_size * 1000)
        self.risk_scores[org_id] = [
            (ts, score) for ts, score in self.risk_scores[org_id]
            if ts > cutoff
        ]
    
    def calculate_window_average(self, org_id: str, timestamp: float) -> float:
        """Calculate average risk score in the time window."""
        if not self.risk_scores[org_id]:
            return 0.0
        
        scores = [score for _, score in self.risk_scores[org_id]]
        return sum(scores) / len(scores)
    
    def trigger_risk_alert(self, org_id: str, risk_score: float) -> None:
        """Trigger risk alert for high-risk organizations."""
        # Implementation for risk alerting
        pass
```

## Error Handling Patterns

### 1. Dead Letter Queue Pattern

```python
class DeadLetterQueueHandler:
    def __init__(self, dlq_producer: KafkaProducer):
        self.dlq_producer = dlq_producer
    
    def send_to_dlq(self, original_topic: str, message: Any, 
                    error: Exception, retry_count: int = 0) -> None:
        """Send failed message to appropriate dead letter queue."""
        
        dlq_message = {
            "originalTopic": original_topic,
            "originalMessage": message,
            "errorMessage": str(error),
            "errorType": type(error).__name__,
            "retryCount": retry_count,
            "timestamp": int(time.time() * 1000),
            "processingAttempts": retry_count + 1
        }
        
        dlq_topic = f"{original_topic}-dlq"
        
        self.dlq_producer.send(
            topic=dlq_topic,
            value=dlq_message,
            key=message.get('id') or str(uuid.uuid4())
        )
```

### 2. Retry Pattern with Exponential Backoff

```python
import time
import random
from typing import Callable, Any

class RetryHandler:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Retry function with exponential backoff."""
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries:
                    raise e
                
                # Exponential backoff with jitter
                delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)
```

## Monitoring and Metrics

### 1. Producer Metrics

```python
import time
from prometheus_client import Counter, Histogram, Gauge

# Metrics
messages_sent = Counter('kafka_messages_sent_total', 'Total messages sent', ['topic'])
send_duration = Histogram('kafka_send_duration_seconds', 'Message send duration', ['topic'])
producer_errors = Counter('kafka_producer_errors_total', 'Producer errors', ['topic', 'error_type'])

class MetricsProducer:
    def __init__(self, producer: KafkaProducer):
        self.producer = producer
    
    def send_with_metrics(self, topic: str, key: str, value: Any) -> None:
        """Send message with metrics collection."""
        
        start_time = time.time()
        try:
            future = self.producer.send(topic, key=key, value=value)
            future.get(timeout=10)  # Wait for acknowledgment
            
            messages_sent.labels(topic=topic).inc()
            send_duration.labels(topic=topic).observe(time.time() - start_time)
            
        except Exception as e:
            producer_errors.labels(topic=topic, error_type=type(e).__name__).inc()
            raise
```

### 2. Consumer Metrics

```python
messages_processed = Counter('kafka_messages_processed_total', 'Total messages processed', ['topic'])
processing_duration = Histogram('kafka_processing_duration_seconds', 'Message processing duration', ['topic'])
consumer_errors = Counter('kafka_consumer_errors_total', 'Consumer errors', ['topic', 'error_type'])
consumer_lag = Gauge('kafka_consumer_lag', 'Consumer lag', ['topic', 'partition'])

class MetricsConsumer:
    def __init__(self, consumer: KafkaConsumer):
        self.consumer = consumer
    
    def process_with_metrics(self, message_handler: Callable) -> None:
        """Process messages with metrics collection."""
        
        for message in self.consumer:
            start_time = time.time()
            topic = message.topic
            
            try:
                message_handler(message.value)
                
                messages_processed.labels(topic=topic).inc()
                processing_duration.labels(topic=topic).observe(time.time() - start_time)
                
                self.consumer.commit()
                
            except Exception as e:
                consumer_errors.labels(topic=topic, error_type=type(e).__name__).inc()
                # Handle error appropriately
```

## Best Practices Summary

1. **Always use idempotent producers** to prevent duplicate messages
2. **Commit offsets manually** after successful processing
3. **Use appropriate partition keys** for message ordering
4. **Implement proper error handling** with DLQ patterns
5. **Monitor producer and consumer metrics** for observability
6. **Use compression** to reduce network overhead
7. **Configure appropriate timeouts** for reliability
8. **Implement graceful shutdown** for clean resource cleanup
9. **Use schemas** for message validation and evolution
10. **Test failure scenarios** to ensure system resilience

---

For more detailed configuration examples, see the individual service implementations and the main Kafka documentation. 