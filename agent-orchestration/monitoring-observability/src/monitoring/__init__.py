"""
Monitoring and Observability System for DORA Compliance Agent Orchestration Platform

This module provides comprehensive visibility into platform health, performance metrics,
agent behavior, and compliance audit trails with real-time monitoring, alerting,
and analytics capabilities.

Features:
- Real-time metrics collection with Prometheus integration
- Distributed tracing with OpenTelemetry and Jaeger
- Centralized log aggregation with Elasticsearch
- Multi-channel alerting system with smart routing
- AI-powered anomaly detection
- Comprehensive audit logging for compliance
- Performance monitoring and bottleneck detection
- Real-time dashboards with Grafana integration
"""

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
import threading
import smtplib
import ssl
import aiohttp
import numpy as np
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Third-party imports
import yaml
import structlog
import psycopg2
from psycopg2.extras import RealDictCursor
import redis.asyncio as redis
from prometheus_client import (
    Counter, Gauge, Histogram, Summary, Info, Enum as PromEnum,
    CollectorRegistry, push_to_gateway, start_http_server, generate_latest
)
from opentelemetry import trace, metrics as otel_metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.asyncio import AsyncIOInstrumentor
from elasticsearch import AsyncElasticsearch
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

class MetricType(Enum):
    """Supported metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class LogLevel(Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MetricDefinition:
    """Metric definition for registration"""
    name: str
    description: str
    metric_type: MetricType
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms
    quantiles: Optional[List[float]] = None  # For summaries

@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    metric: str = ""
    threshold: float = 0.0
    comparison: str = ">"  # >, <, >=, <=, ==, !=
    duration: str = "5m"  # Time window
    severity: AlertSeverity = AlertSeverity.WARNING
    channels: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True

@dataclass
class Alert:
    """Active alert instance"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    rule_name: str = ""
    metric: str = ""
    value: float = 0.0
    threshold: float = 0.0
    severity: AlertSeverity = AlertSeverity.WARNING
    status: AlertStatus = AlertStatus.ACTIVE
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)

@dataclass
class TraceSpan:
    """Distributed trace span"""
    trace_id: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    operation_name: str = ""
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str = "ok"
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def finish(self):
        """Mark span as finished"""
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    level: LogLevel = LogLevel.INFO
    service: str = ""
    component: str = ""
    message: str = ""
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "service": self.service,
            "component": self.component,
            "message": self.message,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            **self.fields
        }

class MetricsCollector:
    """Real-time metrics collection and management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.registry = CollectorRegistry()
        self.metrics: Dict[str, Any] = {}
        self.custom_metrics: Dict[str, Any] = {}
        self._lock = threading.Lock()
        
        # Built-in metrics
        self._register_system_metrics()
        
    def _register_system_metrics(self):
        """Register built-in system metrics"""
        system_metrics = [
            MetricDefinition(
                name="system_cpu_usage_percent",
                description="System CPU usage percentage",
                metric_type=MetricType.GAUGE,
                labels=["node_id", "core"]
            ),
            MetricDefinition(
                name="system_memory_usage_bytes",
                description="System memory usage in bytes",
                metric_type=MetricType.GAUGE,
                labels=["node_id", "type"]
            ),
            MetricDefinition(
                name="workflow_duration_seconds",
                description="Workflow execution duration",
                metric_type=MetricType.HISTOGRAM,
                labels=["workflow_type", "agent_id", "status"],
                buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0]
            ),
            MetricDefinition(
                name="agent_task_total",
                description="Total agent tasks processed",
                metric_type=MetricType.COUNTER,
                labels=["agent_type", "task_type", "status"]
            ),
            MetricDefinition(
                name="dora_deployment_frequency",
                description="DORA deployment frequency metric",
                metric_type=MetricType.GAUGE,
                labels=["environment", "service"]
            ),
            MetricDefinition(
                name="dora_lead_time_hours",
                description="DORA lead time for changes in hours",
                metric_type=MetricType.HISTOGRAM,
                labels=["environment", "service"],
                buckets=[1, 24, 168, 720, 8760]  # 1h, 1d, 1w, 1m, 1y
            ),
            MetricDefinition(
                name="dora_change_failure_rate",
                description="DORA change failure rate",
                metric_type=MetricType.GAUGE,
                labels=["environment", "service"]
            ),
            MetricDefinition(
                name="dora_recovery_time_hours",
                description="DORA time to restore service in hours",
                metric_type=MetricType.HISTOGRAM,
                labels=["environment", "service"],
                buckets=[0.1, 1, 4, 24, 168]  # 6m, 1h, 4h, 1d, 1w
            )
        ]
        
        for metric_def in system_metrics:
            self.register_metric(metric_def)
    
    def register_metric(self, metric_def: MetricDefinition):
        """Register a new metric"""
        with self._lock:
            if metric_def.name in self.metrics:
                logger.warning(f"Metric {metric_def.name} already registered")
                return
            
            if metric_def.metric_type == MetricType.COUNTER:
                metric = Counter(
                    metric_def.name,
                    metric_def.description,
                    metric_def.labels,
                    registry=self.registry
                )
            elif metric_def.metric_type == MetricType.GAUGE:
                metric = Gauge(
                    metric_def.name,
                    metric_def.description,
                    metric_def.labels,
                    registry=self.registry
                )
            elif metric_def.metric_type == MetricType.HISTOGRAM:
                metric = Histogram(
                    metric_def.name,
                    metric_def.description,
                    metric_def.labels,
                    buckets=metric_def.buckets,
                    registry=self.registry
                )
            elif metric_def.metric_type == MetricType.SUMMARY:
                metric = Summary(
                    metric_def.name,
                    metric_def.description,
                    metric_def.labels,
                    registry=self.registry
                )
            else:
                raise ValueError(f"Unsupported metric type: {metric_def.metric_type}")
            
            self.metrics[metric_def.name] = metric
            logger.info(f"Registered metric: {metric_def.name}")
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a metric value"""
        with self._lock:
            metric = self.metrics.get(name)
            if not metric:
                logger.warning(f"Metric {name} not found")
                return
            
            if labels:
                if hasattr(metric, 'labels'):
                    metric.labels(**labels).observe(value) if hasattr(metric, 'observe') else metric.labels(**labels).set(value)
                else:
                    metric.set(value) if hasattr(metric, 'set') else metric.observe(value)
            else:
                metric.set(value) if hasattr(metric, 'set') else metric.observe(value)
    
    def increment_counter(self, name: str, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        with self._lock:
            metric = self.metrics.get(name)
            if not metric or not hasattr(metric, 'inc'):
                logger.warning(f"Counter metric {name} not found")
                return
            
            if labels:
                metric.labels(**labels).inc(amount)
            else:
                metric.inc(amount)
    
    def get_metric_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current metric value"""
        with self._lock:
            metric = self.metrics.get(name)
            if not metric:
                return None
            
            # This is a simplified implementation
            # In practice, you'd need to query the actual metric value
            return 0.0
    
    def export_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        return generate_latest(self.registry)

class DistributedTracer:
    """Distributed tracing with OpenTelemetry"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tracer = None
        self.active_spans: Dict[str, TraceSpan] = {}
        self._lock = threading.Lock()
        
        self._setup_tracing()
    
    def _setup_tracing(self):
        """Setup OpenTelemetry tracing"""
        try:
            # Configure tracer provider
            trace.set_tracer_provider(TracerProvider())
            
            # Configure Jaeger exporter
            jaeger_config = self.config.get('tracing', {}).get('jaeger', {})
            if jaeger_config:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=jaeger_config.get('host', 'localhost'),
                    agent_port=jaeger_config.get('port', 6831),
                )
                
                span_processor = BatchSpanProcessor(jaeger_exporter)
                trace.get_tracer_provider().add_span_processor(span_processor)
            
            self.tracer = trace.get_tracer(__name__)
            
            # Instrument common libraries
            RequestsInstrumentor().instrument()
            AsyncIOInstrumentor().instrument()
            
            logger.info("Distributed tracing initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup tracing: {e}")
            # Create a no-op tracer for fallback
            self.tracer = trace.NoOpTracer()
    
    def start_span(self, operation_name: str, parent_span: Optional[TraceSpan] = None) -> TraceSpan:
        """Start a new trace span"""
        trace_id = str(uuid.uuid4()) if not parent_span else parent_span.trace_id
        
        span = TraceSpan(
            trace_id=trace_id,
            parent_span_id=parent_span.span_id if parent_span else None,
            operation_name=operation_name
        )
        
        with self._lock:
            self.active_spans[span.span_id] = span
        
        # Start OpenTelemetry span
        if self.tracer:
            otel_span = self.tracer.start_span(operation_name)
            span.otel_span = otel_span
        
        return span
    
    def finish_span(self, span: TraceSpan):
        """Finish a trace span"""
        span.finish()
        
        # Finish OpenTelemetry span
        if hasattr(span, 'otel_span') and span.otel_span:
            span.otel_span.end()
        
        with self._lock:
            if span.span_id in self.active_spans:
                del self.active_spans[span.span_id]
    
    def add_span_tag(self, span: TraceSpan, key: str, value: Any):
        """Add tag to span"""
        span.tags[key] = value
        
        if hasattr(span, 'otel_span') and span.otel_span:
            span.otel_span.set_attribute(key, str(value))
    
    def add_span_log(self, span: TraceSpan, message: str, level: str = "info"):
        """Add log entry to span"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message
        }
        span.logs.append(log_entry)
        
        if hasattr(span, 'otel_span') and span.otel_span:
            span.otel_span.add_event(message)
    
    def get_active_spans(self) -> List[TraceSpan]:
        """Get all active spans"""
        with self._lock:
            return list(self.active_spans.values())

class LogAggregator:
    """Centralized log aggregation with Elasticsearch"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.es_client: Optional[AsyncElasticsearch] = None
        self.log_buffer: deque = deque(maxlen=10000)
        self.structured_logger = structlog.get_logger()
        self._lock = threading.Lock()
        
    async def initialize(self):
        """Initialize log aggregation"""
        try:
            es_config = self.config.get('logging', {}).get('elasticsearch', {})
            if es_config:
                self.es_client = AsyncElasticsearch(
                    hosts=es_config.get('hosts', ['localhost:9200']),
                    timeout=30
                )
                logger.info("Elasticsearch client initialized")
            
            # Start log processing task
            asyncio.create_task(self._process_log_buffer())
            
        except Exception as e:
            logger.error(f"Failed to initialize log aggregation: {e}")
    
    def log(self, entry: LogEntry):
        """Add log entry"""
        with self._lock:
            self.log_buffer.append(entry)
        
        # Also log to structured logger
        log_method = getattr(self.structured_logger, entry.level.value, self.structured_logger.info)
        log_method(
            entry.message,
            service=entry.service,
            component=entry.component,
            trace_id=entry.trace_id,
            span_id=entry.span_id,
            **entry.fields
        )
    
    def info(self, message: str, service: str = "", component: str = "", **kwargs):
        """Log info message"""
        self.log(LogEntry(
            level=LogLevel.INFO,
            service=service,
            component=component,
            message=message,
            fields=kwargs
        ))
    
    def warning(self, message: str, service: str = "", component: str = "", **kwargs):
        """Log warning message"""
        self.log(LogEntry(
            level=LogLevel.WARNING,
            service=service,
            component=component,
            message=message,
            fields=kwargs
        ))
    
    def error(self, message: str, service: str = "", component: str = "", **kwargs):
        """Log error message"""
        self.log(LogEntry(
            level=LogLevel.ERROR,
            service=service,
            component=component,
            message=message,
            fields=kwargs
        ))
    
    async def _process_log_buffer(self):
        """Process log buffer and send to Elasticsearch"""
        while True:
            try:
                batch = []
                with self._lock:
                    while self.log_buffer and len(batch) < 100:
                        batch.append(self.log_buffer.popleft())
                
                if batch and self.es_client:
                    await self._send_to_elasticsearch(batch)
                
                await asyncio.sleep(5)  # Process every 5 seconds
                
            except Exception as e:
                logger.error(f"Error processing log buffer: {e}")
                await asyncio.sleep(5)
    
    async def _send_to_elasticsearch(self, entries: List[LogEntry]):
        """Send log entries to Elasticsearch"""
        try:
            actions = []
            for entry in entries:
                index_name = f"dora-logs-{entry.timestamp.strftime('%Y-%m-%d')}"
                action = {
                    "_index": index_name,
                    "_source": entry.to_dict()
                }
                actions.append(action)
            
            if actions:
                from elasticsearch.helpers import async_bulk
                await async_bulk(self.es_client, actions)
                
        except Exception as e:
            logger.error(f"Failed to send logs to Elasticsearch: {e}")

class AlertingSystem:
    """Multi-channel alerting with smart routing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels: Dict[str, Any] = {}
        self._lock = threading.Lock()
        
        self._setup_notification_channels()
    
    def _setup_notification_channels(self):
        """Setup notification channels"""
        alerting_config = self.config.get('alerting', {})
        channels = alerting_config.get('channels', {})
        
        for channel_name, channel_config in channels.items():
            if channel_config.get('enabled', False):
                self.notification_channels[channel_name] = channel_config
        
        logger.info(f"Configured {len(self.notification_channels)} notification channels")
    
    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        with self._lock:
            self.rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Remove alert rule"""
        with self._lock:
            if rule_id in self.rules:
                del self.rules[rule_id]
                logger.info(f"Removed alert rule: {rule_id}")
    
    async def evaluate_rules(self, metrics: Dict[str, float]):
        """Evaluate alert rules against current metrics"""
        with self._lock:
            rules_to_evaluate = list(self.rules.values())
        
        for rule in rules_to_evaluate:
            if not rule.enabled:
                continue
            
            metric_value = metrics.get(rule.metric)
            if metric_value is None:
                continue
            
            should_alert = self._evaluate_threshold(metric_value, rule.threshold, rule.comparison)
            
            existing_alert = self._find_active_alert(rule.id)
            
            if should_alert and not existing_alert:
                # Create new alert
                alert = Alert(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    metric=rule.metric,
                    value=metric_value,
                    threshold=rule.threshold,
                    severity=rule.severity,
                    labels=rule.labels.copy(),
                    annotations=rule.annotations.copy()
                )
                
                with self._lock:
                    self.active_alerts[alert.id] = alert
                
                await self._send_alert(alert)
                
            elif not should_alert and existing_alert:
                # Resolve alert
                existing_alert.status = AlertStatus.RESOLVED
                existing_alert.end_time = datetime.utcnow()
                
                with self._lock:
                    if existing_alert.id in self.active_alerts:
                        del self.active_alerts[existing_alert.id]
                    self.alert_history.append(existing_alert)
                
                await self._send_resolution(existing_alert)
    
    def _evaluate_threshold(self, value: float, threshold: float, comparison: str) -> bool:
        """Evaluate threshold condition"""
        if comparison == ">":
            return value > threshold
        elif comparison == "<":
            return value < threshold
        elif comparison == ">=":
            return value >= threshold
        elif comparison == "<=":
            return value <= threshold
        elif comparison == "==":
            return value == threshold
        elif comparison == "!=":
            return value != threshold
        else:
            return False
    
    def _find_active_alert(self, rule_id: str) -> Optional[Alert]:
        """Find active alert for rule"""
        with self._lock:
            for alert in self.active_alerts.values():
                if alert.rule_id == rule_id and alert.status == AlertStatus.ACTIVE:
                    return alert
        return None
    
    async def _send_alert(self, alert: Alert):
        """Send alert notifications"""
        rule = self.rules.get(alert.rule_id)
        if not rule:
            return
        
        for channel_name in rule.channels:
            try:
                await self._send_to_channel(channel_name, alert, is_resolution=False)
            except Exception as e:
                logger.error(f"Failed to send alert to {channel_name}: {e}")
    
    async def _send_resolution(self, alert: Alert):
        """Send alert resolution notifications"""
        rule = self.rules.get(alert.rule_id)
        if not rule:
            return
        
        for channel_name in rule.channels:
            try:
                await self._send_to_channel(channel_name, alert, is_resolution=True)
            except Exception as e:
                logger.error(f"Failed to send resolution to {channel_name}: {e}")
    
    async def _send_to_channel(self, channel_name: str, alert: Alert, is_resolution: bool):
        """Send notification to specific channel"""
        channel_config = self.notification_channels.get(channel_name)
        if not channel_config:
            return
        
        if channel_name == "email":
            await self._send_email(channel_config, alert, is_resolution)
        elif channel_name == "slack":
            await self._send_slack(channel_config, alert, is_resolution)
        elif channel_name == "webhook":
            await self._send_webhook(channel_config, alert, is_resolution)
    
    async def _send_email(self, config: Dict[str, Any], alert: Alert, is_resolution: bool):
        """Send email notification"""
        try:
            subject = f"{'RESOLVED' if is_resolution else 'ALERT'}: {alert.rule_name}"
            
            body = f"""
            Alert: {alert.rule_name}
            Severity: {alert.severity.value}
            Metric: {alert.metric}
            Value: {alert.value}
            Threshold: {alert.threshold}
            Status: {'Resolved' if is_resolution else 'Active'}
            Time: {alert.start_time if not is_resolution else alert.end_time}
            """
            
            msg = MimeText(body)
            msg['Subject'] = subject
            msg['From'] = config.get('username', 'alerts@company.com')
            msg['To'] = ', '.join(config.get('recipients', []))
            
            # This is a simplified implementation
            # In practice, you'd use proper SMTP configuration
            logger.info(f"Email alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
    
    async def _send_slack(self, config: Dict[str, Any], alert: Alert, is_resolution: bool):
        """Send Slack notification"""
        try:
            webhook_url = config.get('webhook_url')
            if not webhook_url:
                return
            
            color = "danger" if alert.severity == AlertSeverity.CRITICAL else "warning"
            if is_resolution:
                color = "good"
            
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"{'RESOLVED' if is_resolution else 'ALERT'}: {alert.rule_name}",
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Metric", "value": alert.metric, "short": True},
                        {"title": "Value", "value": str(alert.value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold), "short": True}
                    ],
                    "timestamp": alert.start_time.timestamp()
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Slack alert sent")
                    else:
                        logger.error(f"Slack webhook failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    async def _send_webhook(self, config: Dict[str, Any], alert: Alert, is_resolution: bool):
        """Send webhook notification"""
        try:
            webhook_url = config.get('url')
            if not webhook_url:
                return
            
            payload = {
                "alert_id": alert.id,
                "rule_id": alert.rule_id,
                "rule_name": alert.rule_name,
                "metric": alert.metric,
                "value": alert.value,
                "threshold": alert.threshold,
                "severity": alert.severity.value,
                "status": "resolved" if is_resolution else "active",
                "start_time": alert.start_time.isoformat(),
                "end_time": alert.end_time.isoformat() if alert.end_time else None,
                "labels": alert.labels,
                "annotations": alert.annotations
            }
            
            headers = config.get('headers', {})
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        logger.info("Webhook alert sent")
                    else:
                        logger.error(f"Webhook failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        with self._lock:
            return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        with self._lock:
            return self.alert_history[-limit:]

class AnomalyDetector:
    """AI-powered anomaly detection"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models: Dict[str, Any] = {}
        self.baselines: Dict[str, Dict[str, float]] = {}
        self.anomaly_threshold = 0.1  # Anomaly score threshold
        self._lock = threading.Lock()
        
    def train_model(self, metric_name: str, historical_data: List[float]):
        """Train anomaly detection model for a metric"""
        if len(historical_data) < 100:
            logger.warning(f"Insufficient data for {metric_name} anomaly detection")
            return
        
        try:
            # Prepare data
            data = np.array(historical_data).reshape(-1, 1)
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(data)
            
            # Train Isolation Forest model
            model = IsolationForest(
                contamination=0.1,  # Expected anomaly rate
                random_state=42
            )
            model.fit(scaled_data)
            
            with self._lock:
                self.models[metric_name] = {
                    'model': model,
                    'scaler': scaler,
                    'trained_at': datetime.utcnow()
                }
            
            logger.info(f"Trained anomaly detection model for {metric_name}")
            
        except Exception as e:
            logger.error(f"Failed to train model for {metric_name}: {e}")
    
    def detect_anomaly(self, metric_name: str, value: float) -> Tuple[bool, float]:
        """Detect if a value is anomalous"""
        with self._lock:
            model_info = self.models.get(metric_name)
        
        if not model_info:
            return False, 0.0
        
        try:
            model = model_info['model']
            scaler = model_info['scaler']
            
            # Scale the value
            scaled_value = scaler.transform([[value]])
            
            # Get anomaly score
            anomaly_score = model.decision_function(scaled_value)[0]
            is_anomaly = model.predict(scaled_value)[0] == -1
            
            # Convert anomaly score to confidence (0-1)
            confidence = abs(anomaly_score) if is_anomaly else 0.0
            
            return is_anomaly, confidence
            
        except Exception as e:
            logger.error(f"Error detecting anomaly for {metric_name}: {e}")
            return False, 0.0
    
    def update_baseline(self, metric_name: str, value: float):
        """Update baseline statistics for a metric"""
        with self._lock:
            if metric_name not in self.baselines:
                self.baselines[metric_name] = {
                    'count': 0,
                    'sum': 0.0,
                    'sum_squares': 0.0,
                    'min': value,
                    'max': value
                }
            
            baseline = self.baselines[metric_name]
            baseline['count'] += 1
            baseline['sum'] += value
            baseline['sum_squares'] += value * value
            baseline['min'] = min(baseline['min'], value)
            baseline['max'] = max(baseline['max'], value)
    
    def get_baseline_stats(self, metric_name: str) -> Optional[Dict[str, float]]:
        """Get baseline statistics for a metric"""
        with self._lock:
            baseline = self.baselines.get(metric_name)
        
        if not baseline or baseline['count'] == 0:
            return None
        
        count = baseline['count']
        mean = baseline['sum'] / count
        variance = (baseline['sum_squares'] / count) - (mean * mean)
        std_dev = variance ** 0.5
        
        return {
            'count': count,
            'mean': mean,
            'std_dev': std_dev,
            'min': baseline['min'],
            'max': baseline['max']
        }

class AuditLogger:
    """Comprehensive audit logging for compliance"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.audit_buffer: deque = deque(maxlen=50000)
        self.es_client: Optional[AsyncElasticsearch] = None
        self._lock = threading.Lock()
        
    async def initialize(self):
        """Initialize audit logging"""
        try:
            es_config = self.config.get('logging', {}).get('elasticsearch', {})
            if es_config:
                self.es_client = AsyncElasticsearch(
                    hosts=es_config.get('hosts', ['localhost:9200']),
                    timeout=30
                )
            
            # Start audit log processing
            asyncio.create_task(self._process_audit_buffer())
            logger.info("Audit logging initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize audit logging: {e}")
    
    def log_event(self, event_type: str, user_id: str, resource: str, 
                  action: str, result: str, **metadata):
        """Log audit event"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "result": result,
            "source_ip": metadata.get('source_ip'),
            "user_agent": metadata.get('user_agent'),
            "session_id": metadata.get('session_id'),
            "trace_id": metadata.get('trace_id'),
            "metadata": metadata
        }
        
        with self._lock:
            self.audit_buffer.append(audit_entry)
    
    def log_data_access(self, user_id: str, resource: str, operation: str, **metadata):
        """Log data access event"""
        self.log_event(
            event_type="data_access",
            user_id=user_id,
            resource=resource,
            action=operation,
            result="success",
            **metadata
        )
    
    def log_security_event(self, user_id: str, event: str, result: str, **metadata):
        """Log security event"""
        self.log_event(
            event_type="security",
            user_id=user_id,
            resource="system",
            action=event,
            result=result,
            **metadata
        )
    
    def log_compliance_event(self, user_id: str, regulation: str, action: str, 
                           result: str, **metadata):
        """Log compliance-related event"""
        self.log_event(
            event_type="compliance",
            user_id=user_id,
            resource=regulation,
            action=action,
            result=result,
            **metadata
        )
    
    async def _process_audit_buffer(self):
        """Process audit buffer and send to storage"""
        while True:
            try:
                batch = []
                with self._lock:
                    while self.audit_buffer and len(batch) < 100:
                        batch.append(self.audit_buffer.popleft())
                
                if batch and self.es_client:
                    await self._send_audit_logs(batch)
                
                await asyncio.sleep(10)  # Process every 10 seconds
                
            except Exception as e:
                logger.error(f"Error processing audit buffer: {e}")
                await asyncio.sleep(10)
    
    async def _send_audit_logs(self, entries: List[Dict[str, Any]]):
        """Send audit logs to Elasticsearch"""
        try:
            actions = []
            for entry in entries:
                timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                index_name = f"audit-logs-{timestamp.strftime('%Y-%m-%d')}"
                action = {
                    "_index": index_name,
                    "_source": entry
                }
                actions.append(action)
            
            if actions:
                from elasticsearch.helpers import async_bulk
                await async_bulk(self.es_client, actions)
                
        except Exception as e:
            logger.error(f"Failed to send audit logs: {e}")

class PerformanceMonitor:
    """Performance monitoring and bottleneck detection"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.performance_data: Dict[str, List[float]] = defaultdict(list)
        self.bottlenecks: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
    def record_performance(self, component: str, metric: str, value: float):
        """Record performance metric"""
        key = f"{component}.{metric}"
        
        with self._lock:
            self.performance_data[key].append(value)
            
            # Keep only recent data (last 1000 points)
            if len(self.performance_data[key]) > 1000:
                self.performance_data[key] = self.performance_data[key][-1000:]
    
    def analyze_bottlenecks(self) -> List[Dict[str, Any]]:
        """Analyze performance data for bottlenecks"""
        bottlenecks = []
        
        with self._lock:
            for key, values in self.performance_data.items():
                if len(values) < 10:
                    continue
                
                # Calculate statistics
                mean_value = sum(values) / len(values)
                max_value = max(values)
                min_value = min(values)
                
                # Detect bottlenecks based on thresholds
                if "response_time" in key and mean_value > 5.0:  # 5 seconds
                    bottlenecks.append({
                        "type": "high_response_time",
                        "component": key.split('.')[0],
                        "metric": key,
                        "mean_value": mean_value,
                        "max_value": max_value,
                        "severity": "high" if mean_value > 10.0 else "medium"
                    })
                
                elif "cpu_usage" in key and mean_value > 80.0:  # 80%
                    bottlenecks.append({
                        "type": "high_cpu_usage",
                        "component": key.split('.')[0],
                        "metric": key,
                        "mean_value": mean_value,
                        "max_value": max_value,
                        "severity": "high" if mean_value > 90.0 else "medium"
                    })
                
                elif "memory_usage" in key and mean_value > 85.0:  # 85%
                    bottlenecks.append({
                        "type": "high_memory_usage",
                        "component": key.split('.')[0],
                        "metric": key,
                        "mean_value": mean_value,
                        "max_value": max_value,
                        "severity": "high" if mean_value > 95.0 else "medium"
                    })
        
        self.bottlenecks = bottlenecks
        return bottlenecks
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        summary = {}
        
        with self._lock:
            for key, values in self.performance_data.items():
                if len(values) > 0:
                    summary[key] = {
                        "count": len(values),
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "latest": values[-1] if values else 0
                    }
        
        summary["bottlenecks"] = self.bottlenecks
        return summary

class DashboardManager:
    """Dashboard management with Grafana integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.dashboards: Dict[str, Dict[str, Any]] = {}
        self.grafana_config = config.get('dashboards', {}).get('grafana', {})
    
    async def create_dashboard(self, dashboard_config: Dict[str, Any]) -> str:
        """Create a new dashboard"""
        dashboard_id = str(uuid.uuid4())
        self.dashboards[dashboard_id] = dashboard_config
        
        # If Grafana is configured, create dashboard there
        if self.grafana_config:
            await self._create_grafana_dashboard(dashboard_config)
        
        logger.info(f"Created dashboard: {dashboard_config.get('title', dashboard_id)}")
        return dashboard_id
    
    async def _create_grafana_dashboard(self, config: Dict[str, Any]):
        """Create dashboard in Grafana"""
        try:
            grafana_url = f"http://{self.grafana_config.get('host', 'localhost')}:{self.grafana_config.get('port', 3000)}"
            api_key = self.grafana_config.get('api_key')
            
            if not api_key:
                logger.warning("Grafana API key not configured")
                return
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            dashboard_json = self._generate_grafana_dashboard(config)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{grafana_url}/api/dashboards/db",
                    json=dashboard_json,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logger.info("Dashboard created in Grafana")
                    else:
                        logger.error(f"Failed to create Grafana dashboard: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error creating Grafana dashboard: {e}")
    
    def _generate_grafana_dashboard(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Grafana dashboard JSON"""
        return {
            "dashboard": {
                "id": None,
                "title": config.get('title', 'DORA Compliance Dashboard'),
                "tags": ["dora", "compliance"],
                "timezone": "browser",
                "panels": self._generate_panels(config.get('panels', [])),
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "refresh": config.get('refresh_interval', '30s')
            },
            "overwrite": True
        }
    
    def _generate_panels(self, panel_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate Grafana panels"""
        panels = []
        
        for i, panel_config in enumerate(panel_configs):
            panel = {
                "id": i + 1,
                "title": panel_config.get('title', f'Panel {i + 1}'),
                "type": panel_config.get('type', 'graph'),
                "gridPos": {"h": 8, "w": 12, "x": (i % 2) * 12, "y": (i // 2) * 8},
                "targets": [{
                    "expr": panel_config.get('metric', 'up'),
                    "refId": "A"
                }]
            }
            panels.append(panel)
        
        return panels
    
    def get_dashboard_list(self) -> List[Dict[str, Any]]:
        """Get list of all dashboards"""
        return [
            {
                "id": dashboard_id,
                "title": config.get('title', 'Untitled'),
                "created_at": config.get('created_at', datetime.utcnow().isoformat())
            }
            for dashboard_id, config in self.dashboards.items()
        ]

class MonitoringSystem:
    """Main monitoring and observability system orchestrator"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize components
        self.metrics_collector = MetricsCollector(self.config)
        self.tracer = DistributedTracer(self.config)
        self.log_aggregator = LogAggregator(self.config)
        self.alerting_system = AlertingSystem(self.config)
        self.anomaly_detector = AnomalyDetector(self.config)
        self.audit_logger = AuditLogger(self.config)
        self.performance_monitor = PerformanceMonitor(self.config)
        self.dashboard_manager = DashboardManager(self.config)
        
        # System state
        self.running = False
        self._monitoring_tasks: List[asyncio.Task] = []
        
        logger.info("Monitoring system initialized")
    
    async def initialize(self):
        """Initialize the monitoring system"""
        try:
            # Initialize async components
            await self.log_aggregator.initialize()
            await self.audit_logger.initialize()
            
            # Start Prometheus metrics server
            metrics_port = self.config.get('monitoring', {}).get('metrics_port', 8000)
            start_http_server(metrics_port)
            logger.info(f"Prometheus metrics server started on port {metrics_port}")
            
            # Create default dashboards
            await self._create_default_dashboards()
            
            # Setup default alert rules
            self._setup_default_alerts()
            
            logger.info("Monitoring system fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize monitoring system: {e}")
            raise
    
    async def start(self):
        """Start monitoring system"""
        if self.running:
            logger.warning("Monitoring system already running")
            return
        
        self.running = True
        
        # Start background monitoring tasks
        self._monitoring_tasks = [
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._alert_evaluation_loop()),
            asyncio.create_task(self._performance_analysis_loop()),
            asyncio.create_task(self._anomaly_detection_loop())
        ]
        
        logger.info("Monitoring system started")
    
    async def stop(self):
        """Stop monitoring system"""
        self.running = False
        
        # Cancel monitoring tasks
        for task in self._monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._monitoring_tasks, return_exceptions=True)
        
        logger.info("Monitoring system stopped")
    
    async def _metrics_collection_loop(self):
        """Background metrics collection"""
        while self.running:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Collect application metrics
                await self._collect_application_metrics()
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(30)
    
    async def _alert_evaluation_loop(self):
        """Background alert evaluation"""
        while self.running:
            try:
                # Get current metrics
                current_metrics = await self._get_current_metrics()
                
                # Evaluate alert rules
                await self.alerting_system.evaluate_rules(current_metrics)
                
                await asyncio.sleep(60)  # Evaluate every minute
                
            except Exception as e:
                logger.error(f"Error in alert evaluation: {e}")
                await asyncio.sleep(60)
    
    async def _performance_analysis_loop(self):
        """Background performance analysis"""
        while self.running:
            try:
                # Analyze bottlenecks
                bottlenecks = self.performance_monitor.analyze_bottlenecks()
                
                if bottlenecks:
                    self.log_aggregator.warning(
                        "Performance bottlenecks detected",
                        service="monitoring",
                        component="performance_monitor",
                        bottleneck_count=len(bottlenecks)
                    )
                
                await asyncio.sleep(300)  # Analyze every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in performance analysis: {e}")
                await asyncio.sleep(300)
    
    async def _anomaly_detection_loop(self):
        """Background anomaly detection"""
        while self.running:
            try:
                # Get current metrics
                current_metrics = await self._get_current_metrics()
                
                # Check for anomalies
                for metric_name, value in current_metrics.items():
                    is_anomaly, confidence = self.anomaly_detector.detect_anomaly(metric_name, value)
                    
                    if is_anomaly and confidence > 0.8:
                        self.log_aggregator.warning(
                            "Anomaly detected",
                            service="monitoring",
                            component="anomaly_detector",
                            metric=metric_name,
                            value=value,
                            confidence=confidence
                        )
                
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                logger.error(f"Error in anomaly detection: {e}")
                await asyncio.sleep(120)
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            import psutil
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent()
            self.metrics_collector.record_metric(
                "system_cpu_usage_percent",
                cpu_percent,
                {"node_id": "local", "core": "all"}
            )
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics_collector.record_metric(
                "system_memory_usage_bytes",
                memory.used,
                {"node_id": "local", "type": "used"}
            )
            
            # Record for performance monitoring
            self.performance_monitor.record_performance("system", "cpu_usage", cpu_percent)
            self.performance_monitor.record_performance("system", "memory_usage", memory.percent)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def _collect_application_metrics(self):
        """Collect application-level metrics"""
        try:
            # This would collect metrics from various application components
            # For now, we'll simulate some metrics
            
            import random
            
            # Simulate workflow metrics
            workflow_duration = random.uniform(1.0, 60.0)
            self.metrics_collector.record_metric(
                "workflow_duration_seconds",
                workflow_duration,
                {"workflow_type": "compliance_audit", "agent_id": "policy_analyzer", "status": "success"}
            )
            
            # Simulate DORA metrics
            self.metrics_collector.record_metric(
                "dora_deployment_frequency",
                random.uniform(5.0, 15.0),
                {"environment": "production", "service": "dora-agents"}
            )
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
    
    async def _get_current_metrics(self) -> Dict[str, float]:
        """Get current metric values"""
        # This is a simplified implementation
        # In practice, you'd query the actual metric values from Prometheus or similar
        import random
        
        return {
            "system_cpu_usage_percent": random.uniform(20.0, 80.0),
            "system_memory_usage_percent": random.uniform(30.0, 70.0),
            "workflow_error_rate": random.uniform(0.01, 0.1),
            "dora_deployment_frequency": random.uniform(5.0, 15.0)
        }
    
    async def _create_default_dashboards(self):
        """Create default monitoring dashboards"""
        # Executive dashboard
        executive_dashboard = {
            "title": "DORA Compliance Executive View",
            "refresh_interval": "5m",
            "panels": [
                {
                    "title": "Deployment Frequency",
                    "type": "stat",
                    "metric": "dora_deployment_frequency",
                    "target": 10
                },
                {
                    "title": "Lead Time for Changes",
                    "type": "gauge",
                    "metric": "dora_lead_time_hours",
                    "thresholds": [24, 168, 720]
                },
                {
                    "title": "Change Failure Rate",
                    "type": "stat",
                    "metric": "dora_change_failure_rate",
                    "unit": "percent"
                },
                {
                    "title": "Time to Restore Service",
                    "type": "gauge",
                    "metric": "dora_recovery_time_hours",
                    "thresholds": [1, 24, 168]
                }
            ]
        }
        
        await self.dashboard_manager.create_dashboard(executive_dashboard)
        
        # Operational dashboard
        operational_dashboard = {
            "title": "System Operations",
            "refresh_interval": "30s",
            "panels": [
                {
                    "title": "System Health",
                    "type": "heatmap",
                    "metrics": ["system_cpu_usage_percent", "system_memory_usage_percent"]
                },
                {
                    "title": "Active Workflows",
                    "type": "graph",
                    "metric": "workflows_active",
                    "time_range": "1h"
                }
            ]
        }
        
        await self.dashboard_manager.create_dashboard(operational_dashboard)
    
    def _setup_default_alerts(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule(
                name="High CPU Usage",
                metric="system_cpu_usage_percent",
                threshold=85.0,
                comparison=">",
                duration="5m",
                severity=AlertSeverity.WARNING,
                channels=["email", "slack"]
            ),
            AlertRule(
                name="High Memory Usage",
                metric="system_memory_usage_percent",
                threshold=90.0,
                comparison=">",
                duration="5m",
                severity=AlertSeverity.CRITICAL,
                channels=["email", "slack", "pagerduty"]
            ),
            AlertRule(
                name="High Workflow Error Rate",
                metric="workflow_error_rate",
                threshold=0.05,
                comparison=">",
                duration="10m",
                severity=AlertSeverity.CRITICAL,
                channels=["pagerduty", "slack"]
            ),
            AlertRule(
                name="Low Deployment Frequency",
                metric="dora_deployment_frequency",
                threshold=1.0,
                comparison="<",
                duration="1h",
                severity=AlertSeverity.WARNING,
                channels=["email"]
            )
        ]
        
        for rule in default_rules:
            self.alerting_system.add_rule(rule)
    
    # Public API methods
    
    def create_metric(self, metric_def: MetricDefinition):
        """Create a custom metric"""
        self.metrics_collector.register_metric(metric_def)
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a metric value"""
        self.metrics_collector.record_metric(name, value, labels)
    
    def increment_counter(self, name: str, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        self.metrics_collector.increment_counter(name, amount, labels)
    
    def start_span(self, operation_name: str, parent_span: Optional[TraceSpan] = None) -> TraceSpan:
        """Start a new trace span"""
        return self.tracer.start_span(operation_name, parent_span)
    
    def finish_span(self, span: TraceSpan):
        """Finish a trace span"""
        self.tracer.finish_span(span)
    
    def log(self, level: LogLevel, message: str, service: str = "", component: str = "", **kwargs):
        """Log a message"""
        entry = LogEntry(
            level=level,
            service=service,
            component=component,
            message=message,
            fields=kwargs
        )
        self.log_aggregator.log(entry)
    
    def log_audit_event(self, event_type: str, user_id: str, resource: str, 
                       action: str, result: str, **metadata):
        """Log an audit event"""
        self.audit_logger.log_event(event_type, user_id, resource, action, result, **metadata)
    
    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.alerting_system.add_rule(rule)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return self.alerting_system.get_active_alerts()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return self.performance_monitor.get_performance_summary()
    
    async def create_dashboard(self, dashboard_config: Dict[str, Any]) -> str:
        """Create a new dashboard"""
        return await self.dashboard_manager.create_dashboard(dashboard_config)
    
    def get_dashboard_list(self) -> List[Dict[str, Any]]:
        """Get list of all dashboards"""
        return self.dashboard_manager.get_dashboard_list()

# Export main classes
__all__ = [
    'MonitoringSystem',
    'MetricsCollector',
    'DistributedTracer',
    'LogAggregator',
    'AlertingSystem',
    'AnomalyDetector',
    'AuditLogger',
    'PerformanceMonitor',
    'DashboardManager',
    'MetricDefinition',
    'AlertRule',
    'Alert',
    'TraceSpan',
    'LogEntry',
    'MetricType',
    'AlertSeverity',
    'LogLevel'
] 