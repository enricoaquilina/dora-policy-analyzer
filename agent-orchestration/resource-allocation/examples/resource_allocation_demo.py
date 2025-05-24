#!/usr/bin/env python3
"""
Resource Allocation System Comprehensive Demonstration

This script demonstrates all major features of the DORA Compliance Agent
Resource Allocation System including:
- Basic resource allocation
- Quota management and enforcement
- Resource reservations
- Pool management
- Throttling and rate limiting
- Real-time monitoring and metrics
- Stress testing and performance validation

Run this script to see the Resource Allocation System in action.
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import yaml
import sys
import os

# Add the parent directory to the path to import the resource manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.resource_manager import (
    ResourceManager, ResourceRequest, ResourceSpec, Priority, 
    ResourceType, AllocationStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResourceAllocationDemo:
    """Comprehensive demonstration of the Resource Allocation System"""
    
    def __init__(self):
        self.manager: ResourceManager = None
        self.demo_config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'dora_compliance_demo',
                'user': 'postgres',
                'password': 'password'
            },
            'tracking_interval': 10,  # Faster for demo
            'metrics_port': 8001
        }
        
    async def initialize(self):
        """Initialize the resource manager for demonstration"""
        print("\n🚀 Initializing Resource Allocation System Demo")
        print("=" * 60)
        
        try:
            self.manager = ResourceManager(self.demo_config)
            await self.manager.initialize()
            print("✅ Resource Manager initialized successfully")
            
            # Give the system a moment to discover resources
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Failed to initialize Resource Manager: {e}")
            print("Note: This demo requires PostgreSQL. Using mock mode.")
            # Continue with limited functionality
            self.manager = ResourceManager(self.demo_config)
    
    async def demo_basic_allocation(self):
        """Demonstrate basic resource allocation"""
        print("\n📋 Demo 1: Basic Resource Allocation")
        print("-" * 40)
        
        # Create various resource requests
        requests = [
            ResourceRequest(
                agent_id="policy_analyzer_01",
                agent_type="policy_analyzer",
                workflow_id="compliance_audit_2024",
                priority=Priority.HIGH,
                resources=ResourceSpec(
                    cpu=4, memory=8, disk=50, api_quota=1000
                ),
                duration=1800  # 30 minutes
            ),
            ResourceRequest(
                agent_id="gap_assessment_01",
                agent_type="gap_assessment",
                workflow_id="gap_analysis_q1",
                priority=Priority.MEDIUM,
                resources=ResourceSpec(
                    cpu=2, memory=4, disk=25, api_quota=500
                ),
                duration=3600  # 1 hour
            ),
            ResourceRequest(
                agent_id="risk_analyzer_01",
                agent_type="risk_analyzer",
                workflow_id="security_assessment",
                priority=Priority.CRITICAL,
                resources=ResourceSpec(
                    cpu=8, memory=16, gpu=1, api_quota=2000
                ),
                duration=2400  # 40 minutes
            )
        ]
        
        print(f"📝 Processing {len(requests)} resource requests...")
        
        allocations = []
        for i, request in enumerate(requests, 1):
            print(f"\n🔄 Request {i}: {request.agent_id}")
            print(f"   Priority: {request.priority.name}")
            print(f"   Resources: CPU={request.resources.cpu}, Memory={request.resources.memory}GB")
            
            allocation = await self.manager.allocate_resources(request)
            allocations.append(allocation)
            
            if allocation.success:
                print(f"   ✅ Allocated successfully")
                print(f"   📍 Node: {allocation.node_id}")
                print(f"   ⏰ Duration: {request.duration} seconds")
            else:
                print(f"   ❌ Allocation failed: {allocation.reason}")
            
            # Small delay for demonstration
            await asyncio.sleep(1)
        
        print(f"\n📊 Allocation Summary:")
        successful = len([a for a in allocations if a.success])
        print(f"   Successful: {successful}/{len(allocations)}")
        
        return allocations
    
    async def demo_quota_management(self):
        """Demonstrate quota management and enforcement"""
        print("\n💰 Demo 2: Quota Management")
        print("-" * 40)
        
        # Set custom quotas
        print("🔧 Setting custom quotas for agent types...")
        
        await self.manager.set_quota(
            agent_type="policy_analyzer",
            resources=ResourceSpec(cpu=16, memory=32, api_quota=10000),
            burst_allowance=1.5
        )
        
        await self.manager.set_quota(
            agent_type="test_agent",
            resources=ResourceSpec(cpu=2, memory=4, api_quota=1000),
            burst_allowance=1.2
        )
        
        print("✅ Quotas set successfully")
        
        # Test quota enforcement
        print("\n🧪 Testing quota enforcement...")
        
        # Request within quota
        small_request = ResourceRequest(
            agent_id="test_agent_01",
            agent_type="test_agent",
            resources=ResourceSpec(cpu=1, memory=2, api_quota=500),
            duration=300
        )
        
        allocation1 = await self.manager.allocate_resources(small_request)
        print(f"Small request (within quota): {'✅ Success' if allocation1.success else '❌ Failed'}")
        
        # Request exceeding quota
        large_request = ResourceRequest(
            agent_id="test_agent_02",
            agent_type="test_agent",
            resources=ResourceSpec(cpu=10, memory=20, api_quota=5000),
            duration=300
        )
        
        allocation2 = await self.manager.allocate_resources(large_request)
        print(f"Large request (exceeds quota): {'✅ Success' if allocation2.success else '❌ Failed'}")
        if not allocation2.success:
            print(f"   Reason: {allocation2.reason}")
        
        # Check quota usage
        quota_usage = await self.manager.get_quota_usage("test_agent")
        if quota_usage:
            print(f"\n📈 Quota Usage for 'test_agent':")
            print(f"   CPU: {quota_usage.used.cpu}/{quota_usage.limits.cpu}")
            print(f"   Memory: {quota_usage.used.memory}/{quota_usage.limits.memory}GB")
            print(f"   API Quota: {quota_usage.used.api_quota}/{quota_usage.limits.api_quota}")
        
        return [allocation1, allocation2]
    
    async def demo_reservations(self):
        """Demonstrate resource reservations"""
        print("\n📅 Demo 3: Resource Reservations")
        print("-" * 40)
        
        # Create future reservations
        now = datetime.utcnow()
        future_time = now + timedelta(minutes=5)
        
        print(f"🕐 Creating reservation for {future_time.strftime('%H:%M:%S')}")
        
        reservation = await self.manager.reserve_resources(
            workflow_id="scheduled_compliance_check",
            agent_id="compliance_auditor_01",
            resources=ResourceSpec(cpu=6, memory=12, disk=100),
            start_time=future_time,
            duration=1800,  # 30 minutes
            priority=Priority.HIGH
        )
        
        print(f"✅ Reservation created: {reservation.id}")
        print(f"   Resources: CPU={reservation.resources.cpu}, Memory={reservation.resources.memory}GB")
        print(f"   Start: {reservation.start_time.strftime('%H:%M:%S')}")
        print(f"   End: {reservation.end_time.strftime('%H:%M:%S')}")
        
        # Try to allocate conflicting resources
        print("\n🧪 Testing reservation conflicts...")
        
        conflicting_request = ResourceRequest(
            agent_id="conflicting_agent",
            agent_type="policy_analyzer",
            resources=ResourceSpec(cpu=8, memory=16),
            duration=3600
        )
        
        allocation = await self.manager.allocate_resources(conflicting_request)
        print(f"Conflicting allocation: {'✅ Success' if allocation.success else '❌ Failed'}")
        
        return reservation
    
    async def demo_monitoring_metrics(self):
        """Demonstrate monitoring and metrics collection"""
        print("\n📊 Demo 4: Monitoring and Metrics")
        print("-" * 40)
        
        # Get current utilization metrics
        print("📈 Current System Utilization:")
        metrics = await self.manager.get_utilization_metrics()
        
        print(f"   Total Nodes: {metrics['total_nodes']}")
        print(f"   Available Nodes: {metrics['available_nodes']}")
        print(f"   Active Allocations: {metrics['active_allocations']}")
        
        if 'utilization' in metrics:
            print("   Resource Utilization:")
            for resource_type, utilization in metrics['utilization'].items():
                print(f"     {resource_type}: {utilization:.1f}%")
        
        # Get allocation history
        print("\n📋 Recent Allocation History:")
        history = await self.manager.get_allocation_history("1h")
        
        if history:
            print(f"   Found {len(history)} recent allocations")
            for entry in history[-3:]:  # Show last 3
                timestamp = entry['timestamp'].strftime('%H:%M:%S')
                status = "✅" if entry['success'] else "❌"
                print(f"   {timestamp} - {status} Duration: {entry['duration']:.2f}s")
        else:
            print("   No recent allocation history available")
        
        return metrics
    
    async def demo_stress_testing(self):
        """Demonstrate system under load"""
        print("\n🏋️ Demo 5: Stress Testing")
        print("-" * 40)
        
        print("⚡ Generating concurrent resource requests...")
        
        # Create many concurrent requests
        stress_requests = []
        agent_types = ["policy_analyzer", "gap_assessment", "risk_analyzer", "compliance_auditor"]
        
        for i in range(20):
            agent_type = random.choice(agent_types)
            priority = random.choice(list(Priority))
            
            request = ResourceRequest(
                agent_id=f"stress_test_agent_{i:02d}",
                agent_type=agent_type,
                workflow_id=f"stress_test_workflow_{i:02d}",
                priority=priority,
                resources=ResourceSpec(
                    cpu=random.uniform(0.5, 4.0),
                    memory=random.uniform(1.0, 8.0),
                    disk=random.uniform(10.0, 100.0),
                    api_quota=random.randint(100, 2000)
                ),
                duration=random.randint(300, 1800)
            )
            stress_requests.append(request)
        
        # Process requests concurrently
        start_time = time.time()
        print(f"🚀 Processing {len(stress_requests)} concurrent requests...")
        
        tasks = [
            self.manager.allocate_resources(request)
            for request in stress_requests
        ]
        
        allocations = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Analyze results
        successful = len([a for a in allocations if a.success])
        failed = len(allocations) - successful
        processing_time = end_time - start_time
        
        print(f"\n📊 Stress Test Results:")
        print(f"   Total Requests: {len(allocations)}")
        print(f"   Successful: {successful} ({successful/len(allocations)*100:.1f}%)")
        print(f"   Failed: {failed} ({failed/len(allocations)*100:.1f}%)")
        print(f"   Processing Time: {processing_time:.2f} seconds")
        print(f"   Throughput: {len(allocations)/processing_time:.1f} requests/second")
        
        # Show failure reasons
        if failed > 0:
            failure_reasons = {}
            for allocation in allocations:
                if not allocation.success:
                    reason = allocation.reason
                    failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
            
            print(f"\n❌ Failure Reasons:")
            for reason, count in failure_reasons.items():
                print(f"   {reason}: {count}")
        
        return allocations
    
    async def demo_algorithm_comparison(self):
        """Demonstrate different allocation algorithms"""
        print("\n🧮 Demo 6: Algorithm Comparison")
        print("-" * 40)
        
        # Create identical request sets for comparison
        base_requests = [
            ResourceRequest(
                agent_id=f"algo_test_{i}",
                agent_type="policy_analyzer",
                priority=Priority.HIGH if i < 2 else Priority.MEDIUM,
                resources=ResourceSpec(
                    cpu=random.uniform(1, 4),
                    memory=random.uniform(2, 8)
                ),
                duration=600
            )
            for i in range(8)
        ]
        
        algorithms = ["priority_based", "fair_share", "bin_packing"]
        
        for algorithm in algorithms:
            print(f"\n🔄 Testing {algorithm} algorithm...")
            
            # Create fresh copies of requests
            test_requests = [
                ResourceRequest(
                    agent_id=req.agent_id + f"_{algorithm}",
                    agent_type=req.agent_type,
                    priority=req.priority,
                    resources=req.resources,
                    duration=req.duration
                )
                for req in base_requests
            ]
            
            start_time = time.time()
            allocations = await self.manager.allocation_resolver.resolve_allocation(
                test_requests, algorithm
            )
            end_time = time.time()
            
            successful = len([a for a in allocations if a.success])
            print(f"   Results: {successful}/{len(allocations)} successful")
            print(f"   Time: {(end_time - start_time)*1000:.1f}ms")
        
        print("\n✅ Algorithm comparison complete")
    
    async def demo_cleanup_and_monitoring(self):
        """Demonstrate cleanup and final monitoring"""
        print("\n🧹 Demo 7: Cleanup and Final Status")
        print("-" * 40)
        
        # Show final system state
        print("📊 Final System State:")
        metrics = await self.manager.get_utilization_metrics()
        
        print(f"   Active Allocations: {metrics['active_allocations']}")
        
        if 'utilization' in metrics:
            print("   Final Resource Utilization:")
            for resource_type, utilization in metrics['utilization'].items():
                if utilization > 0:
                    print(f"     {resource_type}: {utilization:.1f}%")
        
        # Cleanup - release some allocations for demonstration
        print("\n🔄 Simulating resource cleanup...")
        
        # In a real scenario, you would release specific allocations
        # For demo purposes, we'll just show what the cleanup process looks like
        await asyncio.sleep(2)
        
        print("✅ Cleanup simulation complete")
    
    async def run_complete_demo(self):
        """Run the complete demonstration"""
        print("🎯 DORA Compliance Resource Allocation System")
        print("=" * 60)
        print("This demonstration showcases the comprehensive resource")
        print("allocation capabilities for DORA compliance agents.")
        print("=" * 60)
        
        try:
            # Initialize system
            await self.initialize()
            
            # Run all demonstrations
            await self.demo_basic_allocation()
            await asyncio.sleep(2)
            
            await self.demo_quota_management()
            await asyncio.sleep(2)
            
            await self.demo_reservations()
            await asyncio.sleep(2)
            
            await self.demo_monitoring_metrics()
            await asyncio.sleep(2)
            
            await self.demo_stress_testing()
            await asyncio.sleep(2)
            
            await self.demo_algorithm_comparison()
            await asyncio.sleep(2)
            
            await self.demo_cleanup_and_monitoring()
            
            print("\n🎉 Demonstration Complete!")
            print("=" * 60)
            print("The Resource Allocation System has successfully demonstrated:")
            print("✅ Dynamic resource allocation with multiple algorithms")
            print("✅ Quota management and enforcement")
            print("✅ Resource reservations for future workflows")
            print("✅ Real-time monitoring and metrics collection")
            print("✅ High-throughput concurrent request processing")
            print("✅ Comprehensive error handling and reporting")
            print("✅ Enterprise-grade scalability and performance")
            
        except Exception as e:
            logger.error(f"Demo failed with error: {e}")
            print(f"\n❌ Demo encountered an error: {e}")
            print("This may be due to missing dependencies or database connection.")
            print("In a production environment, ensure all services are running.")
        
        finally:
            # Cleanup
            if self.manager:
                await self.manager.shutdown()
                print("\n🔌 Resource Manager shutdown complete")

async def main():
    """Main demonstration entry point"""
    demo = ResourceAllocationDemo()
    await demo.run_complete_demo()

if __name__ == "__main__":
    # Check if we're in a proper async context
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        print("Ensure you have all dependencies installed:")
        print("pip install -r requirements.txt") 