#!/usr/bin/env python3
"""
DORA Compliance Conflict Resolution System Demo

This demo showcases the comprehensive conflict resolution system including:
- Resource allocation conflicts and priority-based resolution
- Deadlock detection and resolution
- Agent competition resolution with capability matching
- Policy-driven conflict management
- Integration with state management and communication systems
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Import conflict resolution components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from conflict_resolver import (
    ConflictResolutionManager,
    ConflictInfo,
    ConflictType,
    ConflictPriority,
    ResourceType,
    ResourceRequest,
    ResolutionStrategy
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConflictResolutionDemo:
    """Demonstrates conflict resolution system capabilities"""
    
    def __init__(self):
        # Custom policy configuration for demo
        demo_policy = {
            "detection_interval": 2,  # Faster detection for demo
            "resolution_timeout": 15,
            "max_retries": 2,
            "resource_conflicts": {
                "cpu": {
                    "strategy": "priority_preemption",
                    "preemption_threshold": 0.7,
                    "grace_period": 5
                },
                "memory": {
                    "strategy": "fair_share",
                    "min_allocation": "1GB",
                    "max_allocation": "32GB"
                }
            },
            "agent_conflicts": {
                "strategy": "capability_matching",
                "load_balance_factor": 0.4,
                "capability_weight": 0.6,
                "prefer_local_agents": False
            }
        }
        
        self.conflict_manager = ConflictResolutionManager(demo_policy)
        
    async def initialize(self):
        """Initialize the conflict resolution system"""
        logger.info("🚀 Initializing Conflict Resolution Demo")
        await self.conflict_manager.start()
        logger.info("✅ Conflict Resolution System started successfully")
        
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up Conflict Resolution Demo")
        await self.conflict_manager.stop()
        logger.info("✅ Cleanup completed")
        
    async def demo_resource_conflicts(self):
        """Demonstrate resource allocation conflicts and resolution"""
        logger.info("\n💻 Demo 1: Resource Allocation Conflicts")
        
        # Register some agents with the agent detector
        agent_detector = self.conflict_manager.agent_detector
        await agent_detector.register_agent(
            "policy-analyzer-001", 
            {"document_analysis", "policy_scoring"}, 
            0.2
        )
        await agent_detector.register_agent(
            "gap-assessment-001", 
            {"gap_analysis", "compliance_checking"}, 
            0.6
        )
        await agent_detector.register_agent(
            "risk-calculator-001", 
            {"risk_modeling", "financial_analysis"}, 
            0.1
        )
        
        logger.info("✅ Registered 3 agents with different capabilities and loads")
        
        # Create competing resource requests
        resource_detector = self.conflict_manager.resource_detector
        
        # High priority request
        high_priority_request = ResourceRequest(
            requester_id="workflow-critical-001",
            resource_type=ResourceType.CPU,
            amount=60.0,  # 60 CPU cores
            priority=ConflictPriority.CRITICAL,
            timestamp=datetime.utcnow(),
            metadata={"workflow_type": "emergency_compliance_check"}
        )
        
        # Medium priority request
        medium_priority_request = ResourceRequest(
            requester_id="workflow-standard-002",
            resource_type=ResourceType.CPU,
            amount=50.0,  # 50 CPU cores
            priority=ConflictPriority.MEDIUM,
            timestamp=datetime.utcnow() - timedelta(minutes=5),  # Older request
            metadata={"workflow_type": "routine_assessment"}
        )
        
        # Low priority request
        low_priority_request = ResourceRequest(
            requester_id="workflow-background-003",
            resource_type=ResourceType.CPU,
            amount=30.0,  # 30 CPU cores
            priority=ConflictPriority.LOW,
            timestamp=datetime.utcnow() - timedelta(minutes=10),  # Oldest request
            metadata={"workflow_type": "data_cleanup"}
        )
        
        logger.info("Creating resource requests:")
        logger.info(f"  Critical: {high_priority_request.amount} CPU cores")
        logger.info(f"  Medium: {medium_priority_request.amount} CPU cores (older)")
        logger.info(f"  Low: {low_priority_request.amount} CPU cores (oldest)")
        logger.info(f"  Total demand: {high_priority_request.amount + medium_priority_request.amount + low_priority_request.amount} cores")
        logger.info(f"  Available: 100 cores")
        
        # Add requests to detector
        await resource_detector.add_resource_request(high_priority_request)
        await resource_detector.add_resource_request(medium_priority_request)
        await resource_detector.add_resource_request(low_priority_request)
        
        # Wait for conflict detection and resolution
        logger.info("⏳ Waiting for conflict detection and resolution...")
        await asyncio.sleep(5)
        
        # Check resolution metrics
        resolver = self.conflict_manager.resolver
        metrics = resolver.metrics
        
        if metrics.total_conflicts:
            logger.info(f"✅ Detected and resolved {sum(metrics.total_conflicts.values())} conflicts")
            for conflict_type, count in metrics.total_conflicts.items():
                logger.info(f"   {conflict_type}: {count} conflicts")
        
        # Simulate resolution completion
        await resource_detector.remove_resource_request("workflow-background-003")
        logger.info("✅ Background workflow preempted successfully")
        
    async def demo_deadlock_resolution(self):
        """Demonstrate deadlock detection and resolution"""
        logger.info("\n🔒 Demo 2: Deadlock Detection and Resolution")
        
        deadlock_detector = self.conflict_manager.deadlock_detector
        
        # Create a deadlock scenario
        # Workflow A holds Resource 1, wants Resource 2
        # Workflow B holds Resource 2, wants Resource 1
        
        logger.info("Setting up deadlock scenario:")
        logger.info("  Workflow A: holds resource-1, wants resource-2")
        logger.info("  Workflow B: holds resource-2, wants resource-1")
        
        # Workflow A gets resource-1
        deadlock_detector.grant_lock("workflow-A", "resource-1")
        
        # Workflow B gets resource-2
        deadlock_detector.grant_lock("workflow-B", "resource-2")
        
        # Now they request each other's resources (creating deadlock)
        deadlock_detector.add_lock_request("workflow-A", "resource-2")
        deadlock_detector.add_lock_request("workflow-B", "resource-1")
        
        logger.info("⏳ Waiting for deadlock detection...")
        
        # Manually trigger deadlock detection for demo
        conflicts = await deadlock_detector.detect_conflicts()
        
        if conflicts:
            deadlock_conflict = conflicts[0]
            logger.info(f"🚨 Deadlock detected: {' -> '.join(deadlock_conflict.deadlock_cycle)}")
            
            # Resolve the deadlock
            resolution = await self.conflict_manager.resolver.resolve_deadlock_conflict(deadlock_conflict)
            
            logger.info(f"✅ Deadlock resolved using {resolution.strategy.value}")
            logger.info(f"   Victim entity: {resolution.metadata.get('victim_entity')}")
            logger.info(f"   Success probability: {resolution.success_probability:.2%}")
            
            # Execute the resolution
            await self.conflict_manager._execute_resolution(resolution)
        else:
            logger.info("❌ No deadlock detected (unexpected)")
            
    async def demo_agent_competition(self):
        """Demonstrate agent competition resolution"""
        logger.info("\n🤖 Demo 3: Agent Competition Resolution")
        
        agent_detector = self.conflict_manager.agent_detector
        
        # Create a task that multiple agents can handle
        task_id = "task-policy-analysis-urgent"
        
        logger.info(f"Creating task assignment conflict for: {task_id}")
        
        # Multiple agents want to handle the same task
        agents = [
            ("policy-analyzer-001", 0.2),  # 20% load
            ("policy-analyzer-002", 0.8),  # 80% load  
            ("policy-analyzer-003", 0.1),  # 10% load
        ]
        
        for agent_id, load in agents:
            agent_detector.register_agent(
                agent_id,
                {"document_analysis", "policy_scoring", "compliance_checking"},
                load
            )
            agent_detector.add_task_candidate(task_id, agent_id)
            logger.info(f"   Agent {agent_id}: {load:.0%} load")
        
        # Trigger conflict detection
        conflicts = await agent_detector.detect_conflicts()
        
        if conflicts:
            competition_conflict = conflicts[0]
            logger.info(f"🎯 Agent competition detected: {len(competition_conflict.involved_entities)} candidates")
            
            # Resolve the competition
            resolution = await self.conflict_manager.resolver.resolve_agent_competition(competition_conflict)
            
            selected_agent = resolution.metadata.get('selected_agent')
            selection_score = resolution.metadata.get('selection_score', 0.0)
            
            logger.info(f"✅ Task assigned to: {selected_agent}")
            logger.info(f"   Selection score: {selection_score:.3f}")
            logger.info(f"   Strategy: {resolution.strategy.value}")
            
            # Show the resolution actions
            for action in resolution.actions:
                if action.action_type == "assign_task":
                    logger.info(f"   ✓ Assigned to {action.target_entity}")
                elif action.action_type == "reject_assignment":
                    logger.info(f"   ✗ Rejected {action.target_entity}")
                    
        else:
            logger.info("❌ No agent competition detected")
            
    async def demo_policy_management(self):
        """Demonstrate dynamic policy updates"""
        logger.info("\n⚙️ Demo 4: Dynamic Policy Management")
        
        policy_manager = self.conflict_manager.policy_manager
        
        # Show current policies
        current_cpu_strategy = policy_manager.get_policy("resource_conflicts.cpu.strategy")
        current_grace_period = policy_manager.get_policy("resource_conflicts.cpu.grace_period")
        
        logger.info(f"Current CPU conflict strategy: {current_cpu_strategy}")
        logger.info(f"Current grace period: {current_grace_period} seconds")
        
        # Update policies dynamically
        logger.info("Updating policies dynamically...")
        
        policy_manager.update_policy("resource_conflicts.cpu.grace_period", 15)
        policy_manager.update_policy("detection_interval", 1)
        
        # Verify updates
        updated_grace_period = policy_manager.get_policy("resource_conflicts.cpu.grace_period")
        updated_interval = policy_manager.get_policy("detection_interval")
        
        logger.info(f"✅ Updated grace period: {updated_grace_period} seconds")
        logger.info(f"✅ Updated detection interval: {updated_interval} seconds")
        
        # Show policy hierarchy
        logger.info("Policy hierarchy example:")
        base_priorities = policy_manager.get_policy("priority_settings.base_priorities", {})
        for level, priority in base_priorities.items():
            logger.info(f"   {level}: {priority}")
            
    async def demo_conflict_metrics(self):
        """Demonstrate conflict resolution metrics and monitoring"""
        logger.info("\n📊 Demo 5: Conflict Metrics and Monitoring")
        
        resolver = self.conflict_manager.resolver
        metrics = resolver.metrics
        
        # Generate some artificial metrics data for demo
        metrics.record_conflict("resource_allocation", 0.15, True)
        metrics.record_conflict("resource_allocation", 0.23, True)
        metrics.record_conflict("agent_competition", 0.08, True)
        metrics.record_conflict("deadlock", 1.2, True)
        metrics.record_conflict("resource_allocation", 0.45, False)
        
        logger.info("Conflict resolution metrics:")
        logger.info(f"✅ Total conflicts by type:")
        for conflict_type, count in metrics.total_conflicts.items():
            logger.info(f"   {conflict_type}: {count}")
        
        if metrics.resolution_times:
            avg_resolution_time = sum(metrics.resolution_times) / len(metrics.resolution_times)
            logger.info(f"📈 Average resolution time: {avg_resolution_time:.3f} seconds")
            logger.info(f"📈 Total resolutions: {len(metrics.resolution_times)}")
        
        logger.info(f"✅ Success rates by conflict type:")
        for conflict_type, successes in metrics.resolution_success_rate.items():
            if successes:
                success_rate = sum(successes) / len(successes)
                logger.info(f"   {conflict_type}: {success_rate:.2%}")
        
        # Show active resolutions
        active_count = len(resolver.active_resolutions)
        logger.info(f"🔄 Currently active resolutions: {active_count}")
        
    async def demo_stress_testing(self):
        """Demonstrate system behavior under high conflict load"""
        logger.info("\n⚡ Demo 6: Stress Testing with Multiple Conflicts")
        
        start_time = time.time()
        
        # Create multiple resource conflicts simultaneously
        resource_detector = self.conflict_manager.resource_detector
        
        conflict_count = 5
        logger.info(f"Creating {conflict_count} simultaneous resource conflicts...")
        
        for i in range(conflict_count):
            request = ResourceRequest(
                requester_id=f"stress-test-workflow-{i}",
                resource_type=ResourceType.MEMORY,
                amount=300.0,  # Each wants 300GB, total > 1000GB available
                priority=ConflictPriority.MEDIUM if i % 2 == 0 else ConflictPriority.HIGH,
                timestamp=datetime.utcnow() - timedelta(seconds=i),
                metadata={"stress_test": True, "batch": i}
            )
            await resource_detector.add_resource_request(request)
        
        # Create agent competition conflicts
        agent_detector = self.conflict_manager.agent_detector
        
        for i in range(3):
            task_id = f"stress-task-{i}"
            for j in range(4):  # 4 agents compete for each task
                agent_id = f"stress-agent-{j}"
                agent_detector.add_task_candidate(task_id, agent_id)
        
        logger.info("⏳ Waiting for conflict detection and resolution...")
        await asyncio.sleep(8)  # Wait for multiple resolution cycles
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Check final metrics
        metrics = self.conflict_manager.resolver.metrics
        total_conflicts = sum(metrics.total_conflicts.values())
        
        logger.info(f"✅ Stress test completed in {duration:.2f} seconds")
        logger.info(f"📊 Total conflicts handled: {total_conflicts}")
        
        if metrics.resolution_times:
            avg_time = sum(metrics.resolution_times) / len(metrics.resolution_times)
            max_time = max(metrics.resolution_times)
            logger.info(f"📈 Average resolution time: {avg_time:.3f}s")
            logger.info(f"📈 Maximum resolution time: {max_time:.3f}s")
        
        # Clean up stress test requests
        for i in range(conflict_count):
            await resource_detector.remove_resource_request(f"stress-test-workflow-{i}")
        
        logger.info("🧹 Cleaned up stress test resources")
        
    async def demo_integration_scenarios(self):
        """Demonstrate integration with other system components"""
        logger.info("\n🔗 Demo 7: Integration Scenarios")
        
        logger.info("Simulating integration scenarios:")
        
        # Scenario 1: Workflow engine requesting conflict resolution
        logger.info("1. Workflow Engine Integration:")
        logger.info("   → Workflow requests task assignment")
        logger.info("   → Conflict resolver determines best agent")
        logger.info("   → Resolution actions sent to communication layer")
        
        # Scenario 2: State manager triggering conflict detection
        logger.info("2. State Manager Integration:")
        logger.info("   → State change detected (resource allocation)")
        logger.info("   → Conflict detector notified")
        logger.info("   → Resolution updates state atomically")
        
        # Scenario 3: Communication system notifying agents
        logger.info("3. Communication System Integration:")
        logger.info("   → Resolution actions generated")
        logger.info("   → Messages sent to affected agents")
        logger.info("   → Acknowledgments tracked for confirmation")
        
        # Scenario 4: Monitoring system alerting
        logger.info("4. Monitoring System Integration:")
        logger.info("   → High conflict rate detected")
        logger.info("   → Alert sent to operations team")
        logger.info("   → Dashboard updated with conflict metrics")
        
        logger.info("✅ All integration scenarios would work with:")
        logger.info("   • State Management System (implemented)")
        logger.info("   • Communication Protocols (implemented)")
        logger.info("   • Workflow Engine (implemented)")
        logger.info("   • Monitoring Infrastructure (ready for integration)")


async def run_conflict_resolution_demo():
    """Run the complete conflict resolution demonstration"""
    demo = ConflictResolutionDemo()
    
    try:
        await demo.initialize()
        
        await demo.demo_resource_conflicts()
        await asyncio.sleep(2)  # Brief pause between demos
        
        await demo.demo_deadlock_resolution()
        await asyncio.sleep(2)
        
        await demo.demo_agent_competition()
        await asyncio.sleep(2)
        
        await demo.demo_policy_management()
        await asyncio.sleep(2)
        
        await demo.demo_conflict_metrics()
        await asyncio.sleep(2)
        
        await demo.demo_stress_testing()
        await asyncio.sleep(2)
        
        await demo.demo_integration_scenarios()
        
        logger.info("\n🎉 Conflict Resolution Demo completed successfully!")
        
        # Final system status
        logger.info("\n📋 Final System Status:")
        resolver = demo.conflict_manager.resolver
        metrics = resolver.metrics
        
        total_conflicts = sum(metrics.total_conflicts.values())
        logger.info(f"   Total conflicts processed: {total_conflicts}")
        
        active_resolutions = len(resolver.active_resolutions)
        logger.info(f"   Active resolutions: {active_resolutions}")
        
        if metrics.resolution_times:
            avg_time = sum(metrics.resolution_times) / len(metrics.resolution_times)
            logger.info(f"   Average resolution time: {avg_time:.3f}s")
        
        logger.info("   System status: ✅ Operational")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(run_conflict_resolution_demo()) 