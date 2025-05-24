#!/usr/bin/env python3
"""
Enhanced DORA Compliance State Management Demo

This demo showcases the complete state management system including:
- Event sourcing and reconstruction
- Task, Resource, and System state management
- Recovery and rollback capabilities
- Multi-entity transaction support
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Import state management components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from state_manager import (
    StateManager,
    EntityType,
    WorkflowState,
    TaskState,
    AgentState,
    OptimisticLockException,
    PessimisticLockException,
    StateChangeEvent
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CONFIG = {
    'database': {
        'host': 'localhost',
        'port': 5432,
        'database': 'dora_state_enhanced',
        'user': 'postgres',
        'password': 'postgres',
        'min_connections': 2,
        'max_connections': 10
    },
    'redis': {
        'url': 'redis://localhost:6379'
    },
    'l1_cache_size': 1000
}

class EnhancedStateDemo:
    """Demonstrates enhanced state management capabilities"""
    
    def __init__(self):
        self.state_manager = StateManager(CONFIG)
        
    async def initialize(self):
        """Initialize the state management system"""
        logger.info("🚀 Initializing Enhanced State Management Demo")
        await self.state_manager.initialize()
        logger.info("✅ Enhanced State Manager initialized successfully")
        
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up Enhanced State Management Demo")
        await self.state_manager.shutdown()
        logger.info("✅ Cleanup completed")
        
    async def demo_comprehensive_workflow(self):
        """Demonstrate complete workflow with all entity types"""
        logger.info("\n🔄 Demo 1: Comprehensive Multi-Entity Workflow")
        
        # Create system state
        system_data = {
            "system_id": "dora-compliance-platform",
            "environment": "demo",
            "version": "1.0.0",
            "deployment_id": "deploy-demo-001",
            "overall_health": "healthy",
            "active_workflows": 0,
            "active_agents": 0,
            "configuration": {
                "max_concurrent_workflows": 50,
                "default_timeout": 300
            }
        }
        
        success = await self.state_manager.create_system_state(
            "dora-compliance-platform",
            system_data,
            actor="demo-system"
        )
        
        if success:
            logger.info("✅ System state created")
        
        # Create resource pool
        resource_data = {
            "resource_pool_id": "compute-pool-demo",
            "total_capacity": {
                "cpu_cores": 100,
                "memory_gb": 400,
                "storage_gb": 2000
            },
            "available_capacity": {
                "cpu_cores": 90,
                "memory_gb": 350,
                "storage_gb": 1800
            },
            "utilization_metrics": {
                "cpu_utilization": 10.0,
                "memory_utilization": 12.5,
                "storage_utilization": 10.0
            }
        }
        
        success = await self.state_manager.create_resource_state(
            "compute-pool-demo",
            resource_data,
            actor="demo-system"
        )
        
        if success:
            logger.info("✅ Resource state created")
        
        # Create workflow
        workflow_data = {
            "workflow_id": "wf-demo-001",
            "definition_id": "dora-assessment",
            "state": WorkflowState.CREATED.value,
            "created_at": datetime.utcnow().isoformat(),
            "context": {
                "organization": "demo-bank",
                "assessment_type": "comprehensive"
            },
            "metrics": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "progress_percentage": 0.0
            }
        }
        
        success = await self.state_manager.create_workflow_state(
            "wf-demo-001",
            workflow_data,
            actor="demo-user"
        )
        
        if success:
            logger.info("✅ Workflow state created")
        
        # Create agent
        agent_data = {
            "agent_id": "policy-analyzer-demo",
            "agent_type": "policy_analyzer",
            "state": AgentState.HEALTHY.value,
            "last_heartbeat": datetime.utcnow().isoformat(),
            "capabilities": ["document_analysis", "policy_scoring"],
            "capacity": {
                "max_concurrent_tasks": 3,
                "current_tasks": 0,
                "available_slots": 3
            }
        }
        
        success = await self.state_manager.create_agent_state(
            "policy-analyzer-demo",
            agent_data,
            actor="demo-system"
        )
        
        if success:
            logger.info("✅ Agent state created")
        
        # Create task
        task_data = {
            "task_id": "task-demo-001",
            "workflow_id": "wf-demo-001",
            "state": TaskState.CREATED.value,
            "created_at": datetime.utcnow().isoformat(),
            "inputs": {
                "documents": ["policy.pdf"],
                "analysis_type": "basic"
            },
            "progress": {
                "percentage": 0.0,
                "current_phase": "preparation"
            }
        }
        
        success = await self.state_manager.create_task_state(
            "task-demo-001",
            task_data,
            actor="demo-workflow"
        )
        
        if success:
            logger.info("✅ Task state created")
            
    async def demo_event_sourcing(self):
        """Demonstrate event sourcing capabilities"""
        logger.info("\n📝 Demo 2: Event Sourcing and State Reconstruction")
        
        # Get events for workflow
        events = await self.state_manager.get_entity_events(
            EntityType.WORKFLOW,
            "wf-demo-001"
        )
        
        logger.info(f"✅ Found {len(events)} events for workflow")
        for event in events:
            logger.info(f"   Event: {event.event_type} at {event.timestamp} by {event.actor}")
        
        # Update workflow multiple times to create more events
        workflow_state = await self.state_manager.get_workflow_state("wf-demo-001")
        if workflow_state:
            # Update 1: Start workflow
            workflow_state['state'] = WorkflowState.RUNNING.value
            workflow_state['started_at'] = datetime.utcnow().isoformat()
            
            await self.state_manager.update_workflow_state(
                "wf-demo-001",
                workflow_state,
                expected_version=workflow_state.get('_version'),
                actor="demo-engine"
            )
            
            # Update 2: Progress update
            workflow_state = await self.state_manager.get_workflow_state("wf-demo-001")
            workflow_state['metrics']['total_tasks'] = 1
            workflow_state['metrics']['progress_percentage'] = 25.0
            
            await self.state_manager.update_workflow_state(
                "wf-demo-001",
                workflow_state,
                expected_version=workflow_state.get('_version'),
                actor="demo-engine"
            )
            
            logger.info("✅ Created additional workflow updates")
        
        # Get updated events
        events = await self.state_manager.get_entity_events(
            EntityType.WORKFLOW,
            "wf-demo-001"
        )
        
        logger.info(f"✅ Now have {len(events)} events for workflow")
        
        # Demonstrate state reconstruction
        reconstructed_state = await self.state_manager.reconstruct_state_from_events(
            EntityType.WORKFLOW,
            "wf-demo-001",
            up_to_version=2  # Reconstruct to version 2
        )
        
        if reconstructed_state:
            logger.info(f"✅ Reconstructed state to version 2: {reconstructed_state.get('state')}")
            
    async def demo_advanced_transactions(self):
        """Demonstrate advanced transaction scenarios"""
        logger.info("\n💾 Demo 3: Advanced Multi-Entity Transactions")
        
        try:
            async with self.state_manager.transaction() as txn:
                logger.info("Starting complex multi-entity transaction...")
                
                # Update task to running
                task_state = await self.state_manager.get_task_state("task-demo-001")
                if task_state:
                    task_state['state'] = TaskState.RUNNING.value
                    task_state['started_at'] = datetime.utcnow().isoformat()
                    task_state['assigned_agent'] = "policy-analyzer-demo"
                    
                    await txn.update_entity(
                        EntityType.TASK,
                        "task-demo-001",
                        task_state,
                        expected_version=task_state.get('_version'),
                        actor="demo-scheduler"
                    )
                
                # Update agent to show task assignment
                agent_state = await self.state_manager.get_agent_state("policy-analyzer-demo")
                if agent_state:
                    agent_state['capacity']['current_tasks'] = 1
                    agent_state['capacity']['available_slots'] = 2
                    agent_state['current_tasks'] = ["task-demo-001"]
                    
                    await txn.update_entity(
                        EntityType.AGENT,
                        "policy-analyzer-demo",
                        agent_state,
                        expected_version=agent_state.get('_version'),
                        actor="demo-scheduler"
                    )
                
                # Update resource allocation
                resource_state = await self.state_manager.get_resource_state("compute-pool-demo")
                if resource_state:
                    resource_state['available_capacity']['cpu_cores'] -= 2
                    resource_state['available_capacity']['memory_gb'] -= 4
                    resource_state['utilization_metrics']['cpu_utilization'] = 12.0
                    
                    await txn.update_entity(
                        EntityType.RESOURCE,
                        "compute-pool-demo",
                        resource_state,
                        expected_version=resource_state.get('_version'),
                        actor="demo-scheduler"
                    )
                
                # Update system state
                system_state = await self.state_manager.get_system_state("dora-compliance-platform")
                if system_state:
                    system_state['active_workflows'] = 1
                    system_state['active_agents'] = 1
                    
                    await txn.update_entity(
                        EntityType.SYSTEM,
                        "dora-compliance-platform",
                        system_state,
                        expected_version=system_state.get('_version'),
                        actor="demo-scheduler"
                    )
                
                # Commit all changes atomically
                await txn.commit()
                logger.info("✅ Complex transaction committed successfully")
                
        except Exception as e:
            logger.error(f"❌ Transaction failed: {e}")
            
    async def demo_rollback_capabilities(self):
        """Demonstrate rollback and recovery capabilities"""
        logger.info("\n⏮️ Demo 4: Rollback and Recovery")
        
        # Get current workflow state
        current_workflow = await self.state_manager.get_workflow_state("wf-demo-001")
        if current_workflow:
            current_version = current_workflow.get('_version')
            logger.info(f"Current workflow version: {current_version}")
            logger.info(f"Current workflow state: {current_workflow.get('state')}")
        
        # Make some changes we'll want to rollback
        workflow_state = current_workflow.copy()
        workflow_state['state'] = WorkflowState.FAILED.value
        workflow_state['error_info'] = {
            "error_type": "validation_failed",
            "message": "Simulated failure for demo"
        }
        workflow_state['failed_at'] = datetime.utcnow().isoformat()
        
        new_version = await self.state_manager.update_workflow_state(
            "wf-demo-001",
            workflow_state,
            expected_version=current_version,
            actor="demo-failure"
        )
        
        logger.info(f"✅ Updated workflow to failed state (version {new_version})")
        
        # Wait a moment to simulate time passing
        await asyncio.sleep(1)
        
        # Now demonstrate rollback to previous version
        rollback_success = await self.state_manager.rollback_entity_to_version(
            EntityType.WORKFLOW,
            "wf-demo-001",
            target_version=current_version,
            actor="demo-recovery"
        )
        
        if rollback_success:
            logger.info("✅ Successfully rolled back workflow to previous version")
            
            # Verify rollback
            rolled_back_workflow = await self.state_manager.get_workflow_state("wf-demo-001")
            if rolled_back_workflow:
                logger.info(f"   Rolled back state: {rolled_back_workflow.get('state')}")
                logger.info(f"   New version: {rolled_back_workflow.get('_version')}")
        
        # Demonstrate time-based rollback
        target_time = datetime.utcnow() - timedelta(minutes=1)
        time_rollback_success = await self.state_manager.rollback_entity_to_time(
            EntityType.WORKFLOW,
            "wf-demo-001",
            target_time=target_time,
            actor="demo-time-recovery"
        )
        
        if time_rollback_success:
            logger.info("✅ Successfully performed time-based rollback")
            
    async def demo_performance_monitoring(self):
        """Demonstrate performance and monitoring capabilities"""
        logger.info("\n⚡ Demo 5: Performance and Monitoring")
        
        # Simulate high-frequency operations
        start_time = datetime.utcnow()
        
        for i in range(10):
            # Create temporary task
            temp_task_data = {
                "task_id": f"temp-task-{i}",
                "workflow_id": "wf-demo-001",
                "state": TaskState.CREATED.value,
                "created_at": datetime.utcnow().isoformat(),
                "batch_id": "performance-test"
            }
            
            await self.state_manager.create_task_state(
                f"temp-task-{i}",
                temp_task_data,
                actor="performance-test"
            )
            
            # Immediately read it back (should hit cache)
            retrieved_task = await self.state_manager.get_task_state(f"temp-task-{i}")
            if retrieved_task:
                # Update it
                retrieved_task['state'] = TaskState.COMPLETED.value
                retrieved_task['completed_at'] = datetime.utcnow().isoformat()
                
                await self.state_manager.update_task_state(
                    f"temp-task-{i}",
                    retrieved_task,
                    expected_version=retrieved_task.get('_version'),
                    actor="performance-test"
                )
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Completed 30 operations (create/read/update) in {duration:.3f} seconds")
        logger.info(f"   Average: {(duration/30)*1000:.1f}ms per operation")
        
        # List all tasks to demonstrate filtering
        all_tasks = await self.state_manager.list_tasks(limit=20)
        logger.info(f"✅ Retrieved {len(all_tasks)} tasks from database")
        
        performance_test_tasks = [t for t in all_tasks if t.get('batch_id') == 'performance-test']
        logger.info(f"   {len(performance_test_tasks)} were performance test tasks")
        
    async def demo_health_and_diagnostics(self):
        """Demonstrate health checking and diagnostics"""
        logger.info("\n🏥 Demo 6: Health and Diagnostics")
        
        # Get entity counts by type
        workflows = await self.state_manager.state_store.list_entities(EntityType.WORKFLOW)
        agents = await self.state_manager.state_store.list_entities(EntityType.AGENT)
        tasks = await self.state_manager.state_store.list_entities(EntityType.TASK)
        resources = await self.state_manager.state_store.list_entities(EntityType.RESOURCE)
        systems = await self.state_manager.state_store.list_entities(EntityType.SYSTEM)
        
        logger.info(f"✅ Entity counts:")
        logger.info(f"   Workflows: {len(workflows)}")
        logger.info(f"   Agents: {len(agents)}")
        logger.info(f"   Tasks: {len(tasks)}")
        logger.info(f"   Resources: {len(resources)}")
        logger.info(f"   Systems: {len(systems)}")
        
        # Get version information for workflow
        workflow_versions = await self.state_manager.state_store.get_version_info(
            EntityType.WORKFLOW,
            "wf-demo-001"
        )
        
        logger.info(f"✅ Workflow version history ({len(workflow_versions)} versions):")
        for version in workflow_versions:
            logger.info(f"   Version {version.version}: {version.timestamp} "
                       f"by {version.actor} ({version.size} bytes)")
        
        # Get recent events across all entities
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        workflow_events = await self.state_manager.get_entity_events_by_time(
            EntityType.WORKFLOW,
            "wf-demo-001",
            from_time=recent_time
        )
        
        logger.info(f"✅ Recent workflow events ({len(workflow_events)} events):")
        for event in workflow_events[-5:]:  # Show last 5
            logger.info(f"   {event.event_type} at {event.timestamp} by {event.actor}")


async def run_enhanced_demo():
    """Run the complete enhanced state management demonstration"""
    demo = EnhancedStateDemo()
    
    try:
        await demo.initialize()
        
        await demo.demo_comprehensive_workflow()
        await demo.demo_event_sourcing()
        await demo.demo_advanced_transactions()
        await demo.demo_rollback_capabilities()
        await demo.demo_performance_monitoring()
        await demo.demo_health_and_diagnostics()
        
        logger.info("\n🎉 Enhanced State Management Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(run_enhanced_demo()) 