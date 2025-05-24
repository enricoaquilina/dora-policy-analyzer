#!/usr/bin/env python3
"""
DORA Compliance System - Architecture Diagrams Generator
Generates various architecture diagrams for the system
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS, EKS, Lambda
from diagrams.aws.database import RDS, Dynamodb, ElastiCache
from diagrams.aws.network import ELB, Route53, CloudFront
from diagrams.aws.storage import S3
from diagrams.aws.security import IAM, SecretsManager
from diagrams.aws.analytics import Kinesis
from diagrams.aws.ml import Sagemaker
from diagrams.onprem.database import PostgreSQL, MongoDB, Neo4J, InfluxDB
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.queue import Kafka
from diagrams.onprem.container import Docker
from diagrams.onprem.gitops import ArgoCD
from diagrams.onprem.monitoring import Prometheus, Grafana
from diagrams.onprem.logging import Fluentd
from diagrams.onprem.tracing import Jaeger
from diagrams.programming.framework import React, FastAPI
from diagrams.programming.language import Python, Go, NodeJS
from diagrams.generic.security import Security
from diagrams.generic.storage import Storage

def create_high_level_architecture():
    """Create high-level system architecture diagram"""
    with Diagram("DORA Compliance System - High Level Architecture", show=False, direction="TB"):
        # External systems
        with Cluster("External Systems"):
            regulatory = Storage("Regulatory\nAuthorities")
            third_parties = Storage("Third Party\nProviders")
            threat_intel = Storage("Threat\nIntelligence")
        
        # User interfaces
        with Cluster("User Interfaces"):
            web_app = React("Web Dashboard")
            mobile_app = React("Mobile App")
            api_clients = NodeJS("API Clients")
        
        # Gateway layer
        with Cluster("Gateway Layer"):
            load_balancer = ELB("Load Balancer")
            api_gateway = ELB("API Gateway")
            auth_service = IAM("Auth Service")
        
        # Core platform
        with Cluster("DORA Compliance Platform"):
            with Cluster("Orchestration Layer"):
                workflow_engine = Lambda("Workflow Engine")
                scheduler = Lambda("Scheduler")
                state_manager = Redis("State Manager")
            
            with Cluster("Agent Layer"):
                policy_agent = Python("Policy Analyzer")
                gap_agent = Python("Gap Assessment")
                risk_agent = Python("Risk Calculator")
                impl_agent = Python("Implementation\nPlanner")
                ict_agent = Python("ICT Risk Mgmt")
                incident_agent = Python("Incident Mgmt")
                testing_agent = Python("Resilience Testing")
                tpr_agent = Python("Third Party Risk")
                ti_agent = Python("Threat Intelligence")
            
            with Cluster("Data Layer"):
                graph_db = Neo4J("Graph Database")
                time_series = InfluxDB("Time Series DB")
                document_db = MongoDB("Document Store")
                relational_db = PostgreSQL("PostgreSQL")
                cache = Redis("Cache Layer")
            
            with Cluster("Integration"):
                message_queue = Kafka("Message Queue")
                event_bus = Kafka("Event Bus")
        
        # Infrastructure
        with Cluster("Infrastructure"):
            k8s = EKS("Kubernetes")
            monitoring = Prometheus("Monitoring")
            logging = Fluentd("Logging")
            secrets = SecretsManager("Secrets Vault")
        
        # Connections
        [web_app, mobile_app, api_clients] >> load_balancer >> api_gateway
        api_gateway >> auth_service
        api_gateway >> workflow_engine
        
        workflow_engine >> [scheduler, state_manager]
        workflow_engine >> message_queue
        
        message_queue >> [policy_agent, gap_agent, risk_agent, impl_agent, 
                         ict_agent, incident_agent, testing_agent, tpr_agent, ti_agent]
        
        [policy_agent, gap_agent, risk_agent, impl_agent, ict_agent, 
         incident_agent, testing_agent, tpr_agent, ti_agent] >> event_bus
        
        [policy_agent, gap_agent, risk_agent, impl_agent, ict_agent, 
         incident_agent, testing_agent, tpr_agent, ti_agent] >> [graph_db, time_series, document_db, relational_db, cache]
        
        [regulatory, third_parties, threat_intel] >> api_gateway

def create_agent_architecture():
    """Create detailed agent architecture diagram"""
    with Diagram("DORA Compliance - Agent Architecture", show=False, direction="LR"):
        # External interfaces
        with Cluster("External Interfaces"):
            api = FastAPI("REST API")
            mq_consumer = Kafka("Message Consumer")
            event_publisher = Kafka("Event Publisher")
        
        # Agent core
        with Cluster("Agent Core Components"):
            with Cluster("Processing Layer"):
                msg_handler = Python("Message Handler")
                business_logic = Python("Business Logic")
                ai_models = Sagemaker("AI/ML Models")
            
            with Cluster("State Management"):
                local_state = Redis("Local State")
                distributed_state = Redis("Distributed State")
            
            with Cluster("Data Access"):
                dao = Python("Data Access Layer")
                ext_clients = Python("External Clients")
        
        # Supporting services
        with Cluster("Supporting Services"):
            monitoring = Prometheus("Metrics")
            logging = Fluentd("Logging")
            tracing = Jaeger("Tracing")
            secrets = SecretsManager("Secrets")
        
        # Data stores
        with Cluster("Data Stores"):
            primary_db = PostgreSQL("Primary DB")
            cache = Redis("Cache")
            object_store = S3("Object Store")
        
        # Connections
        mq_consumer >> msg_handler >> business_logic
        business_logic >> ai_models
        business_logic >> [local_state, distributed_state]
        business_logic >> dao >> [primary_db, cache, object_store]
        business_logic >> ext_clients
        business_logic >> event_publisher
        
        api >> business_logic
        
        [msg_handler, business_logic, dao] >> [monitoring, logging, tracing]
        [business_logic, dao, ext_clients] >> secrets

def create_data_flow_diagram():
    """Create data flow diagram"""
    with Diagram("DORA Compliance - Data Flow", show=False, direction="LR"):
        # Input sources
        with Cluster("Input Sources"):
            policy_docs = Storage("Policy\nDocuments")
            risk_data = Storage("Risk Data")
            incident_reports = Storage("Incident\nReports")
            vendor_info = Storage("Vendor Info")
        
        # Processing pipeline
        with Cluster("Processing Pipeline"):
            with Cluster("Ingestion"):
                file_upload = Lambda("File Upload")
                api_ingest = FastAPI("API Ingestion")
                stream_ingest = Kinesis("Stream Ingestion")
            
            with Cluster("Processing"):
                validation = Python("Validation")
                transformation = Python("Transformation")
                enrichment = Python("Enrichment")
                analysis = Sagemaker("Analysis")
            
            with Cluster("Storage"):
                raw_storage = S3("Raw Data")
                processed_storage = S3("Processed Data")
                analytics_db = PostgreSQL("Analytics DB")
        
        # Output destinations
        with Cluster("Output Destinations"):
            dashboards = Grafana("Dashboards")
            reports = Storage("Reports")
            alerts = Lambda("Alerts")
            api_output = FastAPI("API Output")
        
        # Flow
        [policy_docs, risk_data, incident_reports, vendor_info] >> [file_upload, api_ingest, stream_ingest]
        [file_upload, api_ingest, stream_ingest] >> validation
        validation >> transformation >> enrichment >> analysis
        
        validation >> raw_storage
        analysis >> processed_storage
        analysis >> analytics_db
        
        [processed_storage, analytics_db] >> [dashboards, reports, alerts, api_output]

def create_security_architecture():
    """Create security architecture diagram"""
    with Diagram("DORA Compliance - Security Architecture", show=False, direction="TB"):
        # External layer
        with Cluster("External Security"):
            waf = Security("WAF")
            ddos = Security("DDoS Protection")
            cdn = CloudFront("CDN")
        
        # Identity layer
        with Cluster("Identity & Access"):
            idp = IAM("Identity Provider")
            mfa = Security("Multi-Factor Auth")
            sso = IAM("Single Sign-On")
            rbac = IAM("RBAC")
        
        # Network security
        with Cluster("Network Security"):
            vpc = Security("VPC")
            sg = Security("Security Groups")
            nacl = Security("NACLs")
            vpn = Security("VPN Gateway")
        
        # Application security
        with Cluster("Application Security"):
            api_security = Security("API Security")
            encryption = SecretsManager("Encryption")
            vault = SecretsManager("HashiCorp Vault")
            mtls = Security("Mutual TLS")
        
        # Data security
        with Cluster("Data Security"):
            data_encryption = Security("Data Encryption")
            key_mgmt = SecretsManager("Key Management")
            data_masking = Security("Data Masking")
            audit_logs = Storage("Audit Logs")
        
        # Monitoring
        with Cluster("Security Monitoring"):
            siem = Security("SIEM")
            threat_detection = Security("Threat Detection")
            compliance = Security("Compliance Scanner")
        
        # Flow
        waf >> Edge(label="Filter") >> api_security
        api_security >> Edge(label="Authenticate") >> idp
        idp >> Edge(label="Authorize") >> rbac
        rbac >> Edge(label="Encrypt") >> mtls
        mtls >> Edge(label="Access") >> data_encryption
        
        [api_security, mtls, data_encryption] >> audit_logs
        audit_logs >> siem
        siem >> threat_detection

def create_deployment_architecture():
    """Create deployment architecture diagram"""
    with Diagram("DORA Compliance - Deployment Architecture", show=False, direction="TB"):
        # Regions
        with Cluster("Primary Region"):
            with Cluster("Availability Zone 1"):
                master1 = EKS("Master Node 1")
                workers1 = ECS("Worker Nodes")
                data1 = RDS("Data Nodes")
            
            with Cluster("Availability Zone 2"):
                master2 = EKS("Master Node 2")
                workers2 = ECS("Worker Nodes")
                data2 = RDS("Data Nodes")
            
            with Cluster("Availability Zone 3"):
                master3 = EKS("Master Node 3")
                workers3 = ECS("Worker Nodes")
                data3 = RDS("Data Nodes")
        
        with Cluster("DR Region"):
            dr_cluster = EKS("DR Cluster")
            dr_data = RDS("DR Database")
            dr_storage = S3("DR Storage")
        
        # Shared services
        with Cluster("Shared Services"):
            registry = Docker("Container Registry")
            artifacts = S3("Artifact Storage")
            ci_cd = ArgoCD("CI/CD Pipeline")
            monitoring = Grafana("Monitoring")
        
        # Connections
        [master1, master2, master3] >> Edge(label="Sync") >> dr_cluster
        [data1, data2, data3] >> Edge(label="Replicate") >> dr_data
        ci_cd >> [master1, master2, master3, dr_cluster]
        registry >> [workers1, workers2, workers3]

if __name__ == "__main__":
    # Generate all diagrams
    create_high_level_architecture()
    create_agent_architecture()
    create_data_flow_diagram()
    create_security_architecture()
    create_deployment_architecture()
    
    print("Architecture diagrams generated successfully!")
    print("Files created:")
    print("- dora_compliance_system_-_high_level_architecture.png")
    print("- dora_compliance_-_agent_architecture.png")
    print("- dora_compliance_-_data_flow.png")
    print("- dora_compliance_-_security_architecture.png")
    print("- dora_compliance_-_deployment_architecture.png") 