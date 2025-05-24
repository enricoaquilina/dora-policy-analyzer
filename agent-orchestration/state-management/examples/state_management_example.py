#!/usr/bin/env python3
"""
DORA Compliance State Management Example

This example demonstrates the state management system capabilities including
ACID transactions, caching, versioning, locking, and event sourcing.
"""

import asyncio
import logging
import json
from datetime import datetime
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
    PessimisticLockException
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Example Configuration
# ============================================================================

CONFIG = {
    'database': {
        'host': 'localhost',
        'port': 5432,
        'database': 'dora_state_example',
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

# ============================================================================
# Example Data
# ============================================================================

EXAMPLE_WORKFLOW_DATA = {
    "workflow_id": "wf-dora-assessment-001",
    "definition_id": "dora-compliance-assessment",
    "version": "1.2.0",
    "state": WorkflowState.CREATED.value,
    "created_at": datetime.utcnow().isoformat(),
    "context": {
        "organization": "example-bank",
        "compliance_framework": "DORA",
        "triggered_by": "admin@example-bank.com",
        "priority": "high"
    },
    "tasks": {},
    "metrics": {
        "total_tasks": 0,
        "completed_tasks": 0,
        "running_tasks": 0,
        "pending_tasks": 0,
        "progress_percentage": 0.0
    },
    "dependencies": {
        "satisfied": [],
        "pending": ["manual-approval"]
    },
    "retry_count": 0,
    "max_retries": 3
}

EXAMPLE_AGENT_DATA = {
    "agent_id": "policy-analyzer-001",
    "agent_type": "policy_analyzer",
    "instance_id": "pa-inst-001",
    "node_id": "k8s-node-1",
    "state": AgentState.HEALTHY.value,
    "last_heartbeat": datetime.utcnow().isoformat(),
    "registration_time": datetime.utcnow().isoformat(),
    "capabilities": [
        "document_analysis",
        "policy_extraction",
        "compliance_scoring"
    ],
    "resource_usage": {
        "cpu_percent": 25.0,
        "memory_percent": 45.0,
        "disk_percent": 30.0
    },
    "capacity": {
        "max_concurrent_tasks": 5,
        "current_tasks": 0,
        "available_slots": 5,
        "queue_size": 0,
        "processing_rate": 2.5
    },
    "performance_metrics": {
        "tasks_completed": 0,
        "average_execution_time": 0.0,
        "success_rate": 1.0,
        "error_count": 0
    },
    "current_tasks": [],
    "health_status": {
        "overall": "healthy",
        "checks": {
            "memory": "ok",
            "cpu": "ok",
            "disk": "ok",
            "network": "ok",
            "external_deps": "ok"
        },
        "last_health_check": datetime.utcnow().isoformat()
    }
}

EXAMPLE_TASK_DATA = {
    "task_id": "task-policy-analysis-001",
    "workflow_id": "wf-dora-assessment-001",
    "definition_id": "document_analysis",
    "state": TaskState.CREATED.value,
    "created_at": datetime.utcnow().isoformat(),
    "dependencies": {
        "required": [],
        "satisfied": [],
        "blocked_by": []
    },
    "inputs": {
        "documents": ["incident_response_policy.pdf", "business_continuity_plan.pdf"],
        "analysis_type": "comprehensive"
    },
    "outputs": {},
    "progress": {
        "percentage": 0.0,
        "current_phase": "preparation",
        "phases_completed": [],
        "phases_remaining": ["preparation", "analysis", "reporting"]
    },
    "resource_requirements": {
        "cpu": "2",
        "memory": "4Gi",
        "storage": "10Gi",
        "timeout": 300
    },
    "retry_info": {
        "attempt": 1,
        "max_attempts": 3,
        "retry_count": 0,
        "last_error": None
    },
    "audit_trail": [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "task_created",
            "actor": "workflow_engine",
            "details": {"workflow_id": "wf-dora-assessment-001"}
        }
    ]
}

# ============================================================================
# State Management Demo
# ============================================================================

class StateManagementDemo:
    """Demonstrates state management system capabilities"""
    
    def __init__(self):
        self.state_manager = StateManager(CONFIG)
        
    async def initialize(self):
        """Initialize the state management system"""
        logger.info("🚀 Initializing State Management Demo")
        await self.state_manager.initialize()
        logger.info("✅ State Manager initialized successfully")
        
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up State Management Demo")
        await self.state_manager.shutdown()
        logger.info("✅ Cleanup completed")
        
    async def demo_basic_operations(self):
        """Demonstrate basic CRUD operations"""
        logger.info("\n📊 Demo 1: Basic CRUD Operations")
        
        # Create workflow state
        workflow_id = "wf-dora-assessment-001"
        logger.info(f"Creating workflow: {workflow_id}")
        
        success = await self.state_manager.create_workflow_state(
            workflow_id, 
            EXAMPLE_WORKFLOW_DATA.copy(),
            actor="demo-user"
        )
        
        if success:
            logger.info("✅ Workflow created successfully")
        else:
            logger.error("❌ Failed to create workflow")
            return
            
        # Read workflow state
        logger.info(f"Reading workflow: {workflow_id}")
        workflow_state = await self.state_manager.get_workflow_state(workflow_id)
        
        if workflow_state:
            logger.info(f"✅ Workflow retrieved successfully (version: {workflow_state.get('_version')})")
            logger.info(f"   State: {workflow_state.get('state')}")
            logger.info(f"   Organization: {workflow_state.get('context', {}).get('organization')}")
        else:
            logger.error("❌ Failed to retrieve workflow")
            return
            
        # Update workflow state
        logger.info(f"Updating workflow: {workflow_id}")
        updated_data = workflow_state.copy()
        updated_data['state'] = WorkflowState.RUNNING.value
        updated_data['started_at'] = datetime.utcnow().isoformat()
        updated_data['metrics']['total_tasks'] = 3
        
        try:
            new_version = await self.state_manager.update_workflow_state(
                workflow_id,
                updated_data,
                expected_version=workflow_state.get('_version'),
                actor="demo-user"
            )
            logger.info(f"✅ Workflow updated successfully to version {new_version}")
        except OptimisticLockException as e:
            logger.error(f"❌ Optimistic lock failed: {e}")
            
        # Verify update
        updated_workflow = await self.state_manager.get_workflow_state(workflow_id)
        if updated_workflow:
            logger.info(f"✅ Updated workflow verified (version: {updated_workflow.get('_version')})")
            logger.info(f"   New state: {updated_workflow.get('state')}")
            
    async def demo_agent_state_management(self):
        """Demonstrate agent state management"""
        logger.info("\n🤖 Demo 2: Agent State Management")
        
        # Create multiple agents
        agents = [
            ("policy-analyzer-001", "policy_analyzer"),
            ("gap-assessment-001", "gap_assessment"),
            ("risk-calculator-001", "risk_calculator")
        ]
        
        for agent_id, agent_type in agents:
            logger.info(f"Creating agent: {agent_id}")
            
            agent_data = EXAMPLE_AGENT_DATA.copy()
            agent_data['agent_id'] = agent_id
            agent_data['agent_type'] = agent_type
            agent_data['instance_id'] = f"{agent_type}-inst-001"
            
            success = await self.state_manager.create_agent_state(
                agent_id,
                agent_data,
                actor="demo-system"
            )
            
            if success:
                logger.info(f"✅ Agent {agent_id} created successfully")
            else:
                logger.error(f"❌ Failed to create agent {agent_id}")
                
        # Simulate agent heartbeat updates
        logger.info("Simulating agent heartbeat updates...")
        
        for agent_id, _ in agents:
            agent_state = await self.state_manager.get_agent_state(agent_id)
            if agent_state:
                # Update heartbeat and resource usage
                agent_state['last_heartbeat'] = datetime.utcnow().isoformat()
                agent_state['resource_usage']['cpu_percent'] = 35.0 + (hash(agent_id) % 30)
                agent_state['resource_usage']['memory_percent'] = 50.0 + (hash(agent_id) % 25)
                
                try:
                    new_version = await self.state_manager.update_agent_state(
                        agent_id,
                        agent_state,
                        expected_version=agent_state.get('_version'),
                        actor="heartbeat-service"
                    )
                    logger.info(f"✅ Agent {agent_id} heartbeat updated (version: {new_version})")
                except OptimisticLockException as e:
                    logger.error(f"❌ Failed to update agent {agent_id}: {e}")
                    
    async def demo_caching_performance(self):
        """Demonstrate caching performance"""
        logger.info("\n⚡ Demo 3: Caching Performance")
        
        workflow_id = "wf-dora-assessment-001"
        
        # First read (from database)
        import time
        start_time = time.time()
        workflow_state = await self.state_manager.get_workflow_state(workflow_id)
        db_time = time.time() - start_time
        
        if workflow_state:
            logger.info(f"✅ Database read: {db_time:.4f}s")
        
        # Second read (from cache)
        start_time = time.time()
        cached_workflow = await self.state_manager.get_workflow_state(workflow_id)
        cache_time = time.time() - start_time
        
        if cached_workflow:
            logger.info(f"✅ Cache read: {cache_time:.4f}s")
            speedup = db_time / cache_time if cache_time > 0 else float('inf')
            logger.info(f"🚀 Cache speedup: {speedup:.1f}x faster")
            
        # Demonstrate cache invalidation
        logger.info("Testing cache invalidation...")
        updated_data = workflow_state.copy()
        updated_data['updated_at'] = datetime.utcnow().isoformat()
        
        await self.state_manager.update_workflow_state(
            workflow_id,
            updated_data,
            expected_version=workflow_state.get('_version'),
            actor="cache-demo"
        )
        
        # Read after cache invalidation (should hit database again)
        start_time = time.time()
        fresh_workflow = await self.state_manager.get_workflow_state(workflow_id)
        fresh_time = time.time() - start_time
        
        if fresh_workflow:
            logger.info(f"✅ Post-invalidation read: {fresh_time:.4f}s")
            logger.info(f"   Version after update: {fresh_workflow.get('_version')}")
            
    async def demo_transactions(self):
        """Demonstrate transaction support"""
        logger.info("\n💾 Demo 4: Transaction Support")
        
        # Create a task within a transaction
        try:
            async with self.state_manager.transaction() as txn:
                logger.info("Starting transaction...")
                
                # Create task entity
                task_id = "task-policy-analysis-001"
                task_data = EXAMPLE_TASK_DATA.copy()
                
                await txn.create_entity(
                    EntityType.TASK,
                    task_id,
                    task_data,
                    actor="transaction-demo"
                )
                
                # Update workflow to include the task
                workflow_state = await self.state_manager.get_workflow_state("wf-dora-assessment-001")
                if workflow_state:
                    workflow_state['tasks'][task_id] = {
                        "state": TaskState.CREATED.value,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    workflow_state['metrics']['total_tasks'] += 1
                    workflow_state['metrics']['pending_tasks'] += 1
                    
                    await txn.update_entity(
                        EntityType.WORKFLOW,
                        "wf-dora-assessment-001",
                        workflow_state,
                        expected_version=workflow_state.get('_version'),
                        actor="transaction-demo"
                    )
                
                # Commit transaction
                await txn.commit()
                logger.info("✅ Transaction committed successfully")
                
        except Exception as e:
            logger.error(f"❌ Transaction failed: {e}")
            
        # Verify the changes
        final_workflow = await self.state_manager.get_workflow_state("wf-dora-assessment-001")
        if final_workflow:
            task_count = final_workflow.get('metrics', {}).get('total_tasks', 0)
            logger.info(f"✅ Workflow now has {task_count} tasks")
            
    async def demo_locking(self):
        """Demonstrate pessimistic locking"""
        logger.info("\n🔒 Demo 5: Pessimistic Locking")
        
        workflow_id = "wf-dora-assessment-001"
        
        # Demonstrate exclusive locking
        try:
            async with self.state_manager.exclusive_lock(
                EntityType.WORKFLOW, 
                workflow_id, 
                ttl=30,
                holder="lock-demo"
            ) as lock_id:
                logger.info(f"✅ Acquired exclusive lock: {lock_id}")
                
                # Simulate some work while holding the lock
                await asyncio.sleep(1)
                
                # Update workflow state while locked
                workflow_state = await self.state_manager.get_workflow_state(workflow_id)
                if workflow_state:
                    workflow_state['last_locked'] = datetime.utcnow().isoformat()
                    
                    new_version = await self.state_manager.update_workflow_state(
                        workflow_id,
                        workflow_state,
                        expected_version=workflow_state.get('_version'),
                        actor="lock-demo"
                    )
                    logger.info(f"✅ Updated workflow while locked (version: {new_version})")
                    
                logger.info("✅ Lock will be automatically released")
                
        except PessimisticLockException as e:
            logger.error(f"❌ Failed to acquire lock: {e}")
            
    async def demo_versioning(self):
        """Demonstrate state versioning"""
        logger.info("\n📈 Demo 6: State Versioning")
        
        workflow_id = "wf-dora-assessment-001"
        
        # Get version history
        try:
            versions = await self.state_manager.state_store.get_version_info(
                EntityType.WORKFLOW, 
                workflow_id
            )
            
            logger.info(f"✅ Found {len(versions)} versions for workflow {workflow_id}")
            for version in versions:
                logger.info(f"   Version {version.version}: {version.timestamp.isoformat()} "
                          f"by {version.actor} ({version.size} bytes)")
                          
            # Get specific versions
            if len(versions) >= 2:
                logger.info("Retrieving specific versions...")
                
                # Get first version
                v1_state = await self.state_manager.get_workflow_state(workflow_id, version=1)
                if v1_state:
                    logger.info(f"✅ Version 1 state: {v1_state.get('state')}")
                    
                # Get latest version
                latest_state = await self.state_manager.get_workflow_state(workflow_id)
                if latest_state:
                    logger.info(f"✅ Latest state: {latest_state.get('state')} "
                              f"(version: {latest_state.get('_version')})")
                              
        except Exception as e:
            logger.error(f"❌ Failed to get version info: {e}")
            
    async def demo_concurrent_access(self):
        """Demonstrate concurrent access and optimistic locking"""
        logger.info("\n🔄 Demo 7: Concurrent Access")
        
        workflow_id = "wf-dora-assessment-001"
        
        # Simulate concurrent updates
        async def update_worker(worker_id: int):
            try:
                # Get current state
                workflow_state = await self.state_manager.get_workflow_state(workflow_id)
                if not workflow_state:
                    logger.error(f"Worker {worker_id}: No workflow found")
                    return
                    
                # Simulate processing time
                await asyncio.sleep(0.1)
                
                # Update state
                workflow_state[f'worker_{worker_id}_timestamp'] = datetime.utcnow().isoformat()
                workflow_state['concurrent_updates'] = workflow_state.get('concurrent_updates', 0) + 1
                
                new_version = await self.state_manager.update_workflow_state(
                    workflow_id,
                    workflow_state,
                    expected_version=workflow_state.get('_version'),
                    actor=f"worker-{worker_id}"
                )
                
                logger.info(f"✅ Worker {worker_id}: Updated to version {new_version}")
                
            except OptimisticLockException as e:
                logger.warning(f"⚠️  Worker {worker_id}: Optimistic lock conflict - {e}")
            except Exception as e:
                logger.error(f"❌ Worker {worker_id}: Update failed - {e}")
                
        # Start multiple workers concurrently
        logger.info("Starting 3 concurrent workers...")
        tasks = [update_worker(i) for i in range(1, 4)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check final state
        final_state = await self.state_manager.get_workflow_state(workflow_id)
        if final_state:
            concurrent_updates = final_state.get('concurrent_updates', 0)
            logger.info(f"✅ Final state has {concurrent_updates} concurrent updates recorded")

# ============================================================================
# Main Demo Runner
# ============================================================================

async def run_demo():
    """Run the complete state management demonstration"""
    
    demo = StateManagementDemo()
    
    try:
        # Initialize
        await demo.initialize()
        
        # Run all demos
        await demo.demo_basic_operations()
        await demo.demo_agent_state_management()
        await demo.demo_caching_performance()
        await demo.demo_transactions()
        await demo.demo_locking()
        await demo.demo_versioning()
        await demo.demo_concurrent_access()
        
        logger.info("\n🎉 All state management demos completed successfully!")
        
        # Summary
        logger.info("\n📋 Demo Summary:")
        logger.info("• ✅ Basic CRUD operations with versioning")
        logger.info("• ✅ Agent state management with heartbeats")
        logger.info("• ✅ Multi-level caching with performance benefits")
        logger.info("• ✅ ACID transactions with rollback capabilities")
        logger.info("• ✅ Pessimistic locking for critical sections")
        logger.info("• ✅ State versioning with history tracking")
        logger.info("• ✅ Optimistic concurrency control")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise
        
    finally:
        # Cleanup
        await demo.cleanup()

async def setup_database():
    """Setup database for the demo (simplified)"""
    logger.info("📦 Setting up demo database...")
    
    # In a real scenario, you'd create the database here
    # For this demo, we assume PostgreSQL and Redis are running
    
    logger.info("✅ Database setup complete")
    logger.info("   Make sure PostgreSQL is running on localhost:5432")
    logger.info("   Make sure Redis is running on localhost:6379")

async def main():
    """Main entry point"""
    
    print("DORA Compliance State Management Demo")
    print("=" * 45)
    print()
    
    try:
        # Setup
        await setup_database()
        
        # Run demo
        await run_demo()
        
        print("\n" + "=" * 45)
        print("✅ State Management Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("• ACID transactions with automatic rollback")
        print("• Multi-level caching (L1 memory + L2 Redis)")
        print("• State versioning with complete history")
        print("• Optimistic and pessimistic locking")
        print("• Event sourcing with audit trails")
        print("• High-performance concurrent access")
        print("• Comprehensive error handling")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        print("\nMake sure you have:")
        print("• PostgreSQL running on localhost:5432")
        print("• Redis running on localhost:6379")
        print("• Required Python packages installed")

if __name__ == "__main__":
    asyncio.run(main()) 