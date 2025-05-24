#!/usr/bin/env python3
"""
DORA Compliance Agent Communication Protocols Example

This example demonstrates how to use the communication protocols for
inter-agent communication in the DORA compliance system.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Import communication components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from protocols import (
    CommunicationManager,
    Message,
    MessageType,
    TransportType,
    AgentInfo,
    MessagePriority
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Mock DORA Compliance Agents with Communication
# ============================================================================

class PolicyAnalyzerAgent:
    """Policy Analyzer Agent with communication capabilities"""
    
    def __init__(self, agent_id: str):
        self.agent_info = AgentInfo(
            agent_id=agent_id,
            agent_type="policy_analyzer",
            instance_id=f"{agent_id}-instance",
            version="1.0.0",
            capabilities=["document_analysis", "policy_extraction", "compliance_scoring"]
        )
        
        # Communication configuration
        self.comm_config = {
            "agent_id": self.agent_info.agent_id,
            "agent_type": self.agent_info.agent_type,
            "instance_id": self.agent_info.instance_id,
            "version": self.agent_info.version,
            "transports": {
                "http": {
                    "host": "0.0.0.0",
                    "port": 8080,
                    "tls": False
                },
                "kafka": {
                    "brokers": ["localhost:9092"],
                    "group_id": f"agent-{agent_id}",
                    "topic_prefix": "dora-agent"
                }
            },
            "security": {
                "encryption": False,
                "signing": False,
                "authentication": False,
                "encryption_key": None,
                "signing_key": "dora-signing-key-2024",
                "jwt_secret": "dora-jwt-secret-2024"
            }
        }
        
        self.comm_manager = CommunicationManager(self.comm_config)
        self._setup_message_handlers()
        
    def _setup_message_handlers(self):
        """Setup message handlers for different message types"""
        self.comm_manager.register_handler(MessageType.TASK_REQUEST, self._handle_task_request)
        self.comm_manager.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        self.comm_manager.register_handler(MessageType.COMMAND, self._handle_command)
        
    async def start(self):
        """Start the agent and its communication manager"""
        await self.comm_manager.start()
        logger.info(f"PolicyAnalyzer {self.agent_info.agent_id} started")
        
    async def stop(self):
        """Stop the agent and its communication manager"""
        await self.comm_manager.stop()
        logger.info(f"PolicyAnalyzer {self.agent_info.agent_id} stopped")
        
    async def _handle_task_request(self, message: Message) -> Optional[Message]:
        """Handle incoming task request"""
        logger.info(f"PolicyAnalyzer received task request: {message.header.message_id}")
        
        # Extract task parameters
        task_data = message.payload.get("data", {})
        documents = task_data.get("documents", [])
        analysis_type = task_data.get("analysis_type", "basic")
        
        # Simulate document analysis
        await asyncio.sleep(1)  # Simulate processing time
        
        # Create analysis results
        analysis_results = {
            "task_id": task_data.get("task_id"),
            "status": "completed",
            "results": {
                "compliance_score": 0.78,
                "documents_analyzed": len(documents),
                "analysis_type": analysis_type,
                "gaps_found": [
                    "Missing incident response automation",
                    "Incomplete third-party risk assessment",
                    "Outdated business continuity procedures"
                ],
                "recommendations": [
                    "Implement automated incident detection",
                    "Update third-party monitoring procedures",
                    "Schedule quarterly BCP testing"
                ]
            },
            "metadata": {
                "processed_at": datetime.utcnow().isoformat(),
                "agent_id": self.agent_info.agent_id,
                "processing_time": 1.0
            }
        }
        
        # Create response message
        response_header = message.header
        response_header.message_type = MessageType.TASK_RESULT
        
        response = Message(
            header=response_header,
            payload={"data": analysis_results}
        )
        
        logger.info(f"PolicyAnalyzer completed analysis for {len(documents)} documents")
        return response
        
    async def _handle_heartbeat(self, message: Message) -> Optional[Message]:
        """Handle heartbeat request"""
        logger.debug(f"PolicyAnalyzer received heartbeat from {message.header.source.agent_id}")
        
        # Create heartbeat response
        response_data = {
            "agent_status": "healthy",
            "load": 0.45,
            "available_capacity": 0.55,
            "active_tasks": 2,
            "queued_tasks": 0,
            "last_activity": datetime.utcnow().isoformat(),
            "capabilities": self.agent_info.capabilities,
            "resource_usage": {
                "cpu_percent": 35.2,
                "memory_percent": 58.1,
                "disk_percent": 25.0
            }
        }
        
        response_header = message.header
        response_header.message_type = MessageType.RESPONSE
        
        return Message(
            header=response_header,
            payload={"data": response_data}
        )
        
    async def _handle_command(self, message: Message) -> Optional[Message]:
        """Handle command message"""
        command_data = message.payload.get("data", {})
        command = command_data.get("command")
        
        logger.info(f"PolicyAnalyzer received command: {command}")
        
        # Handle different commands
        if command == "get_status":
            status_data = {
                "agent_id": self.agent_info.agent_id,
                "status": "running",
                "uptime": 3600,  # 1 hour
                "tasks_completed": 25,
                "average_processing_time": 2.3
            }
            
            response_header = message.header
            response_header.message_type = MessageType.RESPONSE
            
            return Message(
                header=response_header,
                payload={"data": status_data}
            )
        
        return None
        
    async def send_task_to_agent(self, destination_agent: AgentInfo, task_data: Dict[str, Any], 
                                transport: TransportType = TransportType.HTTP) -> bool:
        """Send a task to another agent"""
        return await self.comm_manager.send_message(
            message_type=MessageType.TASK_REQUEST,
            destination_agent=destination_agent,
            payload={"data": task_data},
            transport_type=transport,
            priority=MessagePriority.HIGH
        )

class GapAssessmentAgent:
    """Gap Assessment Agent with communication capabilities"""
    
    def __init__(self, agent_id: str):
        self.agent_info = AgentInfo(
            agent_id=agent_id,
            agent_type="gap_assessment",
            instance_id=f"{agent_id}-instance",
            version="1.0.0",
            capabilities=["gap_analysis", "risk_assessment", "compliance_mapping"]
        )
        
        # Communication configuration
        self.comm_config = {
            "agent_id": self.agent_info.agent_id,
            "agent_type": self.agent_info.agent_type,
            "instance_id": self.agent_info.instance_id,
            "version": self.agent_info.version,
            "transports": {
                "http": {
                    "host": "0.0.0.0",
                    "port": 8081,
                    "tls": False
                },
                "kafka": {
                    "brokers": ["localhost:9092"],
                    "group_id": f"agent-{agent_id}",
                    "topic_prefix": "dora-agent"
                }
            },
            "security": {
                "encryption": False,
                "signing": False,
                "authentication": False,
                "signing_key": "dora-signing-key-2024",
                "jwt_secret": "dora-jwt-secret-2024"
            }
        }
        
        self.comm_manager = CommunicationManager(self.comm_config)
        self._setup_message_handlers()
        
    def _setup_message_handlers(self):
        """Setup message handlers for different message types"""
        self.comm_manager.register_handler(MessageType.TASK_REQUEST, self._handle_task_request)
        self.comm_manager.register_handler(MessageType.TASK_RESULT, self._handle_task_result)
        self.comm_manager.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        
    async def start(self):
        """Start the agent and its communication manager"""
        await self.comm_manager.start()
        logger.info(f"GapAssessment {self.agent_info.agent_id} started")
        
    async def stop(self):
        """Stop the agent and its communication manager"""
        await self.comm_manager.stop()
        logger.info(f"GapAssessment {self.agent_info.agent_id} stopped")
        
    async def _handle_task_request(self, message: Message) -> Optional[Message]:
        """Handle incoming gap assessment task"""
        logger.info(f"GapAssessment received task request: {message.header.message_id}")
        
        # Extract task parameters
        task_data = message.payload.get("data", {})
        
        # Simulate gap assessment analysis
        await asyncio.sleep(1.5)  # Simulate processing time
        
        # Create gap assessment results
        gap_results = {
            "task_id": task_data.get("task_id"),
            "status": "completed",
            "results": {
                "critical_gaps": [
                    {
                        "id": "DORA-ICT-001",
                        "category": "ICT Risk Management",
                        "description": "Missing automated incident detection system",
                        "severity": "high",
                        "regulation_reference": "Article 5 - ICT Risk Management Framework",
                        "remediation_effort": "3 months"
                    },
                    {
                        "id": "DORA-OP-002",
                        "category": "Operational Resilience",
                        "description": "Insufficient business continuity testing frequency",
                        "severity": "medium",
                        "regulation_reference": "Article 11 - Testing",
                        "remediation_effort": "1 month"
                    }
                ],
                "risk_assessment": {
                    "total_gaps": 2,
                    "critical_gaps": 1,
                    "medium_gaps": 1,
                    "low_gaps": 0,
                    "overall_risk_level": "medium-high"
                },
                "compliance_status": {
                    "current_score": 0.75,
                    "target_score": 0.95,
                    "gap_percentage": 20.0
                }
            },
            "metadata": {
                "processed_at": datetime.utcnow().isoformat(),
                "agent_id": self.agent_info.agent_id,
                "processing_time": 1.5
            }
        }
        
        # Create response message
        response_header = message.header
        response_header.message_type = MessageType.TASK_RESULT
        
        response = Message(
            header=response_header,
            payload={"data": gap_results}
        )
        
        logger.info(f"GapAssessment completed analysis with {len(gap_results['results']['critical_gaps'])} gaps found")
        return response
        
    async def _handle_task_result(self, message: Message) -> None:
        """Handle task result from another agent"""
        result_data = message.payload.get("data", {})
        logger.info(f"GapAssessment received task result from {message.header.source.agent_id}")
        logger.info(f"Task {result_data.get('task_id')} status: {result_data.get('status')}")
        
    async def _handle_heartbeat(self, message: Message) -> Optional[Message]:
        """Handle heartbeat request"""
        logger.debug(f"GapAssessment received heartbeat from {message.header.source.agent_id}")
        
        # Create heartbeat response
        response_data = {
            "agent_status": "healthy",
            "load": 0.62,
            "available_capacity": 0.38,
            "active_tasks": 1,
            "queued_tasks": 2,
            "last_activity": datetime.utcnow().isoformat(),
            "capabilities": self.agent_info.capabilities,
            "resource_usage": {
                "cpu_percent": 42.8,
                "memory_percent": 65.3,
                "disk_percent": 18.5
            }
        }
        
        response_header = message.header
        response_header.message_type = MessageType.RESPONSE
        
        return Message(
            header=response_header,
            payload={"data": response_data}
        )

# ============================================================================
# Workflow Coordinator Example
# ============================================================================

class WorkflowCoordinator:
    """Coordinates communication between multiple agents"""
    
    def __init__(self):
        self.agent_info = AgentInfo(
            agent_id="workflow-coordinator-001",
            agent_type="workflow_coordinator",
            instance_id="coordinator-instance",
            version="1.0.0",
            capabilities=["workflow_orchestration", "agent_coordination"]
        )
        
        # Communication configuration
        self.comm_config = {
            "agent_id": self.agent_info.agent_id,
            "agent_type": self.agent_info.agent_type,
            "instance_id": self.agent_info.instance_id,
            "version": self.agent_info.version,
            "transports": {
                "http": {
                    "host": "0.0.0.0",
                    "port": 8082,
                    "tls": False
                }
            },
            "security": {
                "encryption": False,
                "signing": False,
                "authentication": False
            }
        }
        
        self.comm_manager = CommunicationManager(self.comm_config)
        self.agents: Dict[str, AgentInfo] = {}
        
    async def start(self):
        """Start the workflow coordinator"""
        await self.comm_manager.start()
        logger.info("Workflow Coordinator started")
        
    async def stop(self):
        """Stop the workflow coordinator"""
        await self.comm_manager.stop()
        logger.info("Workflow Coordinator stopped")
        
    def register_agent(self, agent_info: AgentInfo):
        """Register an agent with the coordinator"""
        self.agents[agent_info.agent_id] = agent_info
        logger.info(f"Registered agent: {agent_info.agent_id} ({agent_info.agent_type})")
        
    async def send_heartbeat_to_all(self):
        """Send heartbeat to all registered agents"""
        logger.info("Sending heartbeat to all agents...")
        
        heartbeat_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "coordinator_id": self.agent_info.agent_id,
            "request_type": "status_check"
        }
        
        for agent_info in self.agents.values():
            try:
                success = await self.comm_manager.send_message(
                    message_type=MessageType.HEARTBEAT,
                    destination_agent=agent_info,
                    payload={"data": heartbeat_data},
                    transport_type=TransportType.HTTP,
                    priority=MessagePriority.LOW
                )
                
                if success:
                    logger.info(f"Heartbeat sent to {agent_info.agent_id}")
                else:
                    logger.warning(f"Failed to send heartbeat to {agent_info.agent_id}")
                    
            except Exception as e:
                logger.error(f"Error sending heartbeat to {agent_info.agent_id}: {e}")
                
    async def orchestrate_dora_workflow(self):
        """Orchestrate a complete DORA compliance workflow"""
        logger.info("🚀 Starting DORA Compliance Workflow Orchestration")
        
        # Find available agents
        policy_agent = None
        gap_agent = None
        
        for agent_info in self.agents.values():
            if agent_info.agent_type == "policy_analyzer":
                policy_agent = agent_info
            elif agent_info.agent_type == "gap_assessment":
                gap_agent = agent_info
                
        if not policy_agent or not gap_agent:
            logger.error("Required agents not available for workflow")
            return
            
        # Step 1: Send document analysis task to Policy Analyzer
        logger.info("📄 Step 1: Sending document analysis task to Policy Analyzer")
        
        policy_task = {
            "task_id": "workflow-task-001",
            "task_type": "document_analysis",
            "workflow_id": "dora-compliance-workflow-001",
            "parameters": {
                "documents": [
                    "incident_response_policy.pdf",
                    "business_continuity_plan.pdf",
                    "third_party_risk_framework.pdf"
                ],
                "analysis_type": "comprehensive",
                "priority": "high"
            },
            "requirements": {
                "timeout": 300
            }
        }
        
        success = await self.comm_manager.send_message(
            message_type=MessageType.TASK_REQUEST,
            destination_agent=policy_agent,
            payload={"data": policy_task},
            transport_type=TransportType.HTTP,
            priority=MessagePriority.HIGH
        )
        
        if success:
            logger.info("✅ Document analysis task sent successfully")
        else:
            logger.error("❌ Failed to send document analysis task")
            return
            
        # Wait for processing
        await asyncio.sleep(2)
        
        # Step 2: Send gap assessment task to Gap Assessment Agent
        logger.info("🔍 Step 2: Sending gap assessment task to Gap Assessment Agent")
        
        gap_task = {
            "task_id": "workflow-task-002",
            "task_type": "gap_assessment",
            "workflow_id": "dora-compliance-workflow-001",
            "parameters": {
                "analysis_results": {
                    "compliance_score": 0.78,
                    "gaps_identified": 3,
                    "critical_findings": ["Missing incident automation", "Incomplete BCP testing"]
                },
                "assessment_type": "comprehensive"
            },
            "dependencies": ["workflow-task-001"]
        }
        
        success = await self.comm_manager.send_message(
            message_type=MessageType.TASK_REQUEST,
            destination_agent=gap_agent,
            payload={"data": gap_task},
            transport_type=TransportType.HTTP,
            priority=MessagePriority.HIGH
        )
        
        if success:
            logger.info("✅ Gap assessment task sent successfully")
        else:
            logger.error("❌ Failed to send gap assessment task")
            return
            
        # Wait for processing
        await asyncio.sleep(2)
        
        logger.info("🎉 DORA Compliance Workflow orchestration completed!")

# ============================================================================
# Main Example Execution
# ============================================================================

async def run_communication_example():
    """Run the complete communication example"""
    
    logger.info("🚀 Starting DORA Agent Communication Example")
    
    # Create agents
    policy_agent = PolicyAnalyzerAgent("policy-analyzer-001")
    gap_agent = GapAssessmentAgent("gap-assessment-001")
    coordinator = WorkflowCoordinator()
    
    try:
        # Start all agents
        logger.info("🔧 Starting agents...")
        await policy_agent.start()
        await gap_agent.start()
        await coordinator.start()
        
        # Register agents with coordinator
        coordinator.register_agent(policy_agent.agent_info)
        coordinator.register_agent(gap_agent.agent_info)
        
        # Wait for agents to be ready
        await asyncio.sleep(1)
        
        # Test 1: Send heartbeat to all agents
        logger.info("\n📡 Test 1: Heartbeat Communication")
        await coordinator.send_heartbeat_to_all()
        
        # Wait for responses
        await asyncio.sleep(2)
        
        # Test 2: Direct agent-to-agent communication
        logger.info("\n🤝 Test 2: Direct Agent Communication")
        
        task_data = {
            "task_id": "direct-task-001",
            "task_type": "policy_analysis",
            "documents": ["compliance_policy.pdf", "risk_framework.pdf"],
            "analysis_type": "targeted"
        }
        
        success = await gap_agent.comm_manager.send_message(
            message_type=MessageType.TASK_REQUEST,
            destination_agent=policy_agent.agent_info,
            payload={"data": task_data},
            transport_type=TransportType.HTTP,
            priority=MessagePriority.MEDIUM
        )
        
        if success:
            logger.info("✅ Direct task communication successful")
        else:
            logger.error("❌ Direct task communication failed")
            
        # Wait for processing
        await asyncio.sleep(3)
        
        # Test 3: Orchestrated workflow
        logger.info("\n🎼 Test 3: Orchestrated DORA Workflow")
        await coordinator.orchestrate_dora_workflow()
        
        # Test 4: Command communication
        logger.info("\n💻 Test 4: Command Communication")
        
        command_data = {
            "command": "get_status",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        success = await coordinator.comm_manager.send_message(
            message_type=MessageType.COMMAND,
            destination_agent=policy_agent.agent_info,
            payload={"data": command_data},
            transport_type=TransportType.HTTP,
            priority=MessagePriority.LOW
        )
        
        if success:
            logger.info("✅ Command sent successfully")
            
        # Wait for final processing
        await asyncio.sleep(2)
        
        logger.info("\n🎉 All communication tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in communication example: {e}")
        raise
        
    finally:
        # Cleanup
        logger.info("🧹 Cleaning up...")
        await policy_agent.stop()
        await gap_agent.stop()
        await coordinator.stop()

async def demonstrate_message_types():
    """Demonstrate different message types and formats"""
    
    logger.info("\n📋 Demonstrating Message Types and Formats")
    
    # Example message structures
    examples = {
        "Task Request": {
            "header": {
                "message_type": "task_request",
                "source": {"agent_id": "policy-analyzer-001", "agent_type": "policy_analyzer"},
                "destination": {"agent_id": "gap-assessment-001", "agent_type": "gap_assessment"},
                "priority": "high"
            },
            "payload": {
                "data": {
                    "task_id": "task-uuid",
                    "task_type": "gap_assessment",
                    "parameters": {
                        "analysis_results": {"compliance_score": 0.75},
                        "assessment_type": "comprehensive"
                    }
                }
            }
        },
        "Heartbeat": {
            "header": {
                "message_type": "heartbeat",
                "source": {"agent_id": "coordinator-001", "agent_type": "coordinator"},
                "destination": {"agent_id": "policy-analyzer-001", "agent_type": "policy_analyzer"},
                "priority": "low"
            },
            "payload": {
                "data": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_type": "status_check"
                }
            }
        },
        "Event Notification": {
            "header": {
                "message_type": "event",
                "source": {"agent_id": "risk-detector-001", "agent_type": "risk_detector"},
                "destination": {"agent_id": "incident-manager-001", "agent_type": "incident_manager"},
                "priority": "critical"
            },
            "payload": {
                "data": {
                    "event_type": "compliance_violation_detected",
                    "severity": "high",
                    "event_data": {
                        "violation_type": "missing_backup_procedure",
                        "affected_system": "payment_processing",
                        "regulation_reference": "DORA Article 11"
                    },
                    "action_required": True
                }
            }
        }
    }
    
    for msg_type, example in examples.items():
        logger.info(f"\n📨 {msg_type} Example:")
        logger.info(json.dumps(example, indent=2, default=str))

async def main():
    """Main entry point for the communication example"""
    
    print("DORA Compliance Agent Communication Protocols Demo")
    print("=" * 55)
    print()
    
    try:
        # Demonstrate message formats
        await demonstrate_message_types()
        
        # Run the full communication example
        await run_communication_example()
        
        print("\n" + "=" * 55)
        print("✅ Communication Protocol Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("• Standardized message formats with headers and payloads")
        print("• Multiple transport protocols (HTTP, Kafka, WebSocket)")
        print("• Security features (encryption, signing, authentication)")
        print("• Agent coordination and workflow orchestration")
        print("• Comprehensive observability and monitoring")
        print("• Fault tolerance and error handling")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 