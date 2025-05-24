#!/usr/bin/env python3
"""
DORA Compliance Workflow Engine Example

This example demonstrates how to use the workflow engine to orchestrate
a complete DORA compliance assessment using multiple AI agents.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List

# Import workflow engine components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from workflow_engine.core import (
    WorkflowEngine,
    WorkflowDefinition,
    TaskDefinition,
    DORAAgent,
    TaskExecution,
    TaskResult,
    RetryPolicy,
    ResourceRequirements
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Mock DORA Compliance Agents
# ============================================================================

class PolicyAnalyzerAgent(DORAAgent):
    """Mock Policy Analyzer Agent for DORA compliance documents"""
    
    @property
    def agent_id(self) -> str:
        return "policy-analyzer-001"
    
    @property
    def agent_type(self) -> str:
        return "policy_analyzer"
    
    async def execute_task(self, task: TaskExecution) -> TaskResult:
        """Execute policy analysis task"""
        logger.info(f"PolicyAnalyzer executing task: {task.id}")
        
        # Simulate document analysis
        await asyncio.sleep(2)  # Simulate processing time
        
        # Mock analysis results
        compliance_score = 0.75
        gaps_found = [
            "Incident reporting procedures need update",
            "Third-party risk assessment incomplete",
            "Business continuity plan requires validation"
        ]
        
        return TaskResult(
            task_id=task.id,
            success=True,
            outputs={
                "compliance_score": compliance_score,
                "analysis_results": {
                    "documents_analyzed": 15,
                    "policies_reviewed": 8,
                    "gaps_identified": len(gaps_found),
                    "gaps_detail": gaps_found
                },
                "recommendations": [
                    "Update incident response procedures",
                    "Implement automated third-party monitoring",
                    "Schedule quarterly BCP testing"
                ]
            },
            metrics={
                "processing_time_seconds": 2.0,
                "documents_per_second": 7.5,
                "accuracy_score": 0.92
            }
        )
    
    async def get_capabilities(self) -> List[str]:
        return [
            "document_analysis",
            "policy_extraction", 
            "compliance_scoring",
            "gap_identification",
            "regulatory_mapping"
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "last_check": datetime.utcnow().isoformat(),
            "capabilities": await self.get_capabilities(),
            "load": 0.3
        }
    
    async def get_resource_requirements(self, task: TaskDefinition) -> ResourceRequirements:
        return ResourceRequirements(
            cpu="2",
            memory="4Gi",
            gpu=False,
            storage="10Gi"
        )

class GapAssessmentAgent(DORAAgent):
    """Mock Gap Assessment Agent for compliance gap analysis"""
    
    @property
    def agent_id(self) -> str:
        return "gap-assessment-001"
    
    @property
    def agent_type(self) -> str:
        return "gap_assessment"
    
    async def execute_task(self, task: TaskExecution) -> TaskResult:
        """Execute gap assessment task"""
        logger.info(f"GapAssessment executing task: {task.id}")
        
        # Get input from previous task
        analysis_results = task.inputs.get("analysis_results", {})
        compliance_score = task.inputs.get("compliance_score", 0.0)
        
        # Simulate gap analysis
        await asyncio.sleep(1.5)
        
        # Mock gap assessment results
        critical_gaps = [
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
        ]
        
        return TaskResult(
            task_id=task.id,
            success=True,
            outputs={
                "gaps_identified": critical_gaps,
                "risk_assessment": {
                    "total_gaps": len(critical_gaps),
                    "critical_gaps": sum(1 for g in critical_gaps if g["severity"] == "high"),
                    "medium_gaps": sum(1 for g in critical_gaps if g["severity"] == "medium"),
                    "low_gaps": sum(1 for g in critical_gaps if g["severity"] == "low"),
                    "overall_risk_level": "medium-high"
                },
                "compliance_status": {
                    "current_score": compliance_score,
                    "target_score": 0.95,
                    "gap_percentage": (0.95 - compliance_score) * 100
                }
            },
            metrics={
                "assessment_time_seconds": 1.5,
                "gaps_per_category": 2,
                "confidence_score": 0.88
            }
        )
    
    async def get_capabilities(self) -> List[str]:
        return [
            "gap_analysis",
            "risk_assessment",
            "compliance_mapping",
            "remediation_planning"
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "last_check": datetime.utcnow().isoformat(),
            "capabilities": await self.get_capabilities(),
            "load": 0.2
        }
    
    async def get_resource_requirements(self, task: TaskDefinition) -> ResourceRequirements:
        return ResourceRequirements(
            cpu="1",
            memory="2Gi",
            gpu=False
        )

class RiskCalculatorAgent(DORAAgent):
    """Mock Risk Calculator Agent for financial impact assessment"""
    
    @property
    def agent_id(self) -> str:
        return "risk-calculator-001"
    
    @property
    def agent_type(self) -> str:
        return "risk_calculator"
    
    async def execute_task(self, task: TaskExecution) -> TaskResult:
        """Execute risk calculation task"""
        logger.info(f"RiskCalculator executing task: {task.id}")
        
        # Get input from previous tasks
        gaps_data = task.inputs.get("gaps_identified", [])
        
        # Simulate financial risk calculation
        await asyncio.sleep(1.0)
        
        # Mock financial impact calculation
        base_penalty = 10000000  # 10M EUR base penalty for DORA non-compliance
        risk_multiplier = len(gaps_data) * 0.2
        potential_penalty = base_penalty * (1 + risk_multiplier)
        
        operational_costs = {
            "incident_response": 500000,
            "business_continuity": 750000,
            "regulatory_reporting": 200000,
            "third_party_monitoring": 300000
        }
        
        total_operational_risk = sum(operational_costs.values())
        
        return TaskResult(
            task_id=task.id,
            success=True,
            outputs={
                "risk_metrics": {
                    "potential_regulatory_penalty": potential_penalty,
                    "operational_risk_cost": total_operational_risk,
                    "total_financial_exposure": potential_penalty + total_operational_risk,
                    "risk_probability": 0.15,  # 15% chance of regulatory action
                    "expected_loss": (potential_penalty + total_operational_risk) * 0.15
                },
                "financial_impact": potential_penalty + total_operational_risk,
                "cost_breakdown": {
                    "regulatory_penalties": potential_penalty,
                    "operational_costs": operational_costs,
                    "reputational_impact": 2000000  # Estimated reputational cost
                },
                "risk_timeline": {
                    "immediate_costs": operational_costs["incident_response"],
                    "short_term_costs": operational_costs["business_continuity"],
                    "long_term_costs": potential_penalty
                }
            },
            metrics={
                "calculation_time_seconds": 1.0,
                "accuracy_confidence": 0.85,
                "model_version": "DORA-risk-v1.2"
            }
        )
    
    async def get_capabilities(self) -> List[str]:
        return [
            "financial_risk_calculation",
            "penalty_assessment",
            "operational_cost_analysis",
            "risk_modeling"
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "last_check": datetime.utcnow().isoformat(),
            "capabilities": await self.get_capabilities(),
            "load": 0.1
        }
    
    async def get_resource_requirements(self, task: TaskDefinition) -> ResourceRequirements:
        return ResourceRequirements(
            cpu="1",
            memory="1Gi",
            gpu=False
        )

class ReportGeneratorAgent(DORAAgent):
    """Mock Report Generator Agent for compliance reporting"""
    
    @property
    def agent_id(self) -> str:
        return "report-generator-001"
    
    @property
    def agent_type(self) -> str:
        return "report_generator"
    
    async def execute_task(self, task: TaskExecution) -> TaskResult:
        """Execute report generation task"""
        logger.info(f"ReportGenerator executing task: {task.id}")
        
        # Get aggregated results from all previous tasks
        all_results = task.inputs.get("all_results", {})
        
        # Simulate report generation
        await asyncio.sleep(0.5)
        
        # Generate comprehensive compliance report
        report_content = {
            "executive_summary": {
                "assessment_date": datetime.utcnow().isoformat(),
                "overall_compliance_score": all_results.get("compliance_score", 0.75),
                "total_gaps_identified": len(all_results.get("gaps_identified", [])),
                "financial_exposure": all_results.get("financial_impact", 0),
                "recommendation": "Immediate action required on critical gaps"
            },
            "detailed_findings": all_results,
            "regulatory_mapping": {
                "DORA_Article_5": "ICT Risk Management - Partially Compliant",
                "DORA_Article_11": "Testing - Non-Compliant", 
                "DORA_Article_17": "Reporting - Compliant"
            },
            "action_plan": {
                "priority_1": "Implement automated incident detection",
                "priority_2": "Increase BCP testing frequency",
                "priority_3": "Update third-party risk assessments"
            }
        }
        
        return TaskResult(
            task_id=task.id,
            success=True,
            outputs={
                "compliance_report": report_content,
                "executive_summary": report_content["executive_summary"],
                "report_format": "json",
                "report_size_kb": 245,
                "distribution_list": [
                    "chief_risk_officer@company.com",
                    "compliance_team@company.com", 
                    "board_secretary@company.com"
                ]
            },
            metrics={
                "generation_time_seconds": 0.5,
                "report_completeness": 0.95,
                "template_version": "DORA-report-v2.1"
            }
        )
    
    async def get_capabilities(self) -> List[str]:
        return [
            "report_generation",
            "executive_summaries",
            "regulatory_mapping",
            "action_planning"
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "last_check": datetime.utcnow().isoformat(),
            "capabilities": await self.get_capabilities(),
            "load": 0.05
        }
    
    async def get_resource_requirements(self, task: TaskDefinition) -> ResourceRequirements:
        return ResourceRequirements(
            cpu="0.5",
            memory="1Gi",
            gpu=False
        )

# ============================================================================
# Workflow Definition
# ============================================================================

def create_dora_compliance_workflow() -> WorkflowDefinition:
    """Create a complete DORA compliance assessment workflow"""
    
    # Define tasks with dependencies
    tasks = [
        TaskDefinition(
            id="document_analysis",
            name="Analyze Policy Documents",
            agent_type="policy_analyzer",
            timeout=900,
            priority="high",
            resource_requirements=ResourceRequirements(cpu="2", memory="4Gi"),
            inputs={
                "documents": [
                    "incident_response_policy.pdf",
                    "business_continuity_plan.pdf", 
                    "third_party_risk_framework.pdf",
                    "ict_governance_policy.pdf"
                ],
                "analysis_type": "comprehensive"
            },
            outputs=["compliance_score", "analysis_results"]
        ),
        
        TaskDefinition(
            id="gap_identification",
            name="Identify Compliance Gaps",
            agent_type="gap_assessment", 
            dependencies=["document_analysis"],
            timeout=600,
            priority="high",
            resource_requirements=ResourceRequirements(cpu="1", memory="2Gi"),
            inputs={},  # Will be populated from document_analysis outputs
            outputs=["gaps_identified", "risk_assessment"]
        ),
        
        TaskDefinition(
            id="risk_calculation",
            name="Calculate Financial Risk",
            agent_type="risk_calculator",
            dependencies=["gap_identification"],
            timeout=300,
            priority="medium",
            resource_requirements=ResourceRequirements(cpu="1", memory="1Gi"),
            inputs={},  # Will be populated from gap_identification outputs
            outputs=["risk_metrics", "financial_impact"]
        ),
        
        TaskDefinition(
            id="report_generation",
            name="Generate Compliance Report",
            agent_type="report_generator",
            dependencies=["document_analysis", "gap_identification", "risk_calculation"],
            timeout=300,
            priority="low",
            resource_requirements=ResourceRequirements(cpu="0.5", memory="1Gi"),
            inputs={},  # Will be aggregated from all previous tasks
            outputs=["compliance_report", "executive_summary"]
        )
    ]
    
    # Create workflow definition
    workflow = WorkflowDefinition(
        id="dora-compliance-assessment",
        name="DORA Compliance Assessment",
        description="Complete DORA regulatory compliance assessment workflow",
        version="1.0.0",
        tasks=tasks,
        timeout=3600,  # 1 hour total timeout
        retry_policy=RetryPolicy(max_attempts=3, backoff_strategy="exponential"),
        triggers=["manual", "scheduled"],
        config={
            "parallel_execution": True,
            "audit_enabled": True,
            "notification_enabled": True
        }
    )
    
    return workflow

# ============================================================================
# Example Execution
# ============================================================================

async def run_dora_compliance_example():
    """Run the complete DORA compliance workflow example"""
    
    logger.info("Starting DORA Compliance Workflow Engine Example")
    
    # Configuration for the workflow engine
    config = {
        'state_config': {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'user': 'postgres',
                'password': 'password',
                'name': 'dora_workflows'
            },
            'cache': {
                'url': 'redis://localhost:6379'
            }
        },
        'event_config': {
            'kafka': {
                'brokers': ['localhost:9092']
            }
        },
        'agent_config': {},
        'task_config': {},
        'resource_config': {}
    }
    
    try:
        # Initialize workflow engine
        logger.info("Initializing Workflow Engine...")
        engine = WorkflowEngine(config)
        
        # Start the engine (note: this requires actual infrastructure)
        # await engine.start()
        
        # Register mock agents
        logger.info("Registering DORA compliance agents...")
        policy_agent = PolicyAnalyzerAgent()
        gap_agent = GapAssessmentAgent()
        risk_agent = RiskCalculatorAgent()
        report_agent = ReportGeneratorAgent()
        
        await engine.agent_coordinator.register_agent(policy_agent)
        await engine.agent_coordinator.register_agent(gap_agent)
        await engine.agent_coordinator.register_agent(risk_agent)
        await engine.agent_coordinator.register_agent(report_agent)
        
        # Create workflow definition
        logger.info("Creating DORA compliance workflow...")
        workflow_def = create_dora_compliance_workflow()
        
        # Create workflow execution
        logger.info("Creating workflow execution...")
        workflow_id = await engine.create_workflow(
            workflow_def,
            context={
                "organization": "Example Financial Institution",
                "assessment_type": "quarterly_review",
                "initiated_by": "compliance_officer@company.com",
                "target_completion": "2024-01-31"
            }
        )
        
        logger.info(f"Created workflow with ID: {workflow_id}")
        
        # Start workflow execution
        logger.info("Starting workflow execution...")
        success = await engine.start_workflow(workflow_id)
        
        if success:
            logger.info("Workflow started successfully")
            
            # Monitor workflow progress
            while True:
                status = await engine.get_workflow_status(workflow_id)
                if not status:
                    logger.error("Failed to get workflow status")
                    break
                
                logger.info(f"Workflow Progress: {status['progress']['percentage']:.1f}%")
                logger.info(f"Workflow State: {status['state']}")
                
                # Print task statuses
                for task_id, task_info in status['tasks'].items():
                    logger.info(f"  Task {task_id}: {task_info['state']}")
                
                # Check if workflow is complete
                if status['state'] in ['completed', 'failed', 'cancelled']:
                    break
                
                await asyncio.sleep(2)
            
            # Print final results
            final_status = await engine.get_workflow_status(workflow_id)
            if final_status and final_status['state'] == 'completed':
                logger.info("🎉 DORA Compliance Assessment Completed Successfully!")
                logger.info(f"Final Progress: {final_status['progress']['percentage']:.1f}%")
                logger.info(f"Completed Tasks: {final_status['progress']['completed_tasks']}")
                logger.info(f"Total Duration: {final_status['end_time']} - {final_status['start_time']}")
            else:
                logger.error(f"Workflow failed or was cancelled: {final_status['state']}")
        
        else:
            logger.error("Failed to start workflow")
        
        # Cleanup
        # await engine.stop()
        
    except Exception as e:
        logger.error(f"Error in workflow execution: {e}")
        raise

async def simulate_workflow_execution():
    """Simulate workflow execution without requiring full infrastructure"""
    
    logger.info("🚀 Simulating DORA Compliance Workflow Execution")
    
    # Create agents
    agents = {
        "policy_analyzer": PolicyAnalyzerAgent(),
        "gap_assessment": GapAssessmentAgent(), 
        "risk_calculator": RiskCalculatorAgent(),
        "report_generator": ReportGeneratorAgent()
    }
    
    # Create workflow
    workflow = create_dora_compliance_workflow()
    
    logger.info(f"📋 Workflow: {workflow.name}")
    logger.info(f"📝 Description: {workflow.description}")
    logger.info(f"🔢 Version: {workflow.version}")
    logger.info(f"📊 Total Tasks: {len(workflow.tasks)}")
    
    # Execute tasks in dependency order
    task_results = {}
    
    for task in workflow.tasks:
        logger.info(f"\n🔄 Executing Task: {task.name}")
        logger.info(f"   Agent Type: {task.agent_type}")
        logger.info(f"   Dependencies: {task.dependencies}")
        
        # Check dependencies
        if task.dependencies:
            logger.info(f"   ✅ Dependencies satisfied: {task.dependencies}")
        
        # Get agent
        agent = agents.get(task.agent_type)
        if not agent:
            logger.error(f"   ❌ Agent not found: {task.agent_type}")
            continue
        
        # Create task execution
        task_execution = TaskExecution(
            id=f"sim-{task.id}",
            workflow_id="simulation",
            task_definition=task,
            inputs=task.inputs.copy()
        )
        
        # Add outputs from previous tasks
        for dep_id in task.dependencies:
            if dep_id in task_results:
                task_execution.inputs.update(task_results[dep_id].outputs)
        
        # Execute task
        start_time = datetime.utcnow()
        result = await agent.execute_task(task_execution)
        end_time = datetime.utcnow()
        
        # Store results
        task_results[task.id] = result
        
        # Log results
        duration = (end_time - start_time).total_seconds()
        logger.info(f"   ✅ Task completed in {duration:.2f} seconds")
        logger.info(f"   📈 Success: {result.success}")
        
        if result.outputs:
            logger.info(f"   📤 Outputs: {list(result.outputs.keys())}")
        
        if result.metrics:
            logger.info(f"   📊 Metrics: {result.metrics}")
    
    # Print final summary
    logger.info(f"\n🎉 DORA Compliance Assessment Simulation Complete!")
    logger.info(f"📈 Tasks Executed: {len(task_results)}")
    logger.info(f"✅ Success Rate: {sum(1 for r in task_results.values() if r.success) / len(task_results) * 100:.1f}%")
    
    # Extract key findings
    if "document_analysis" in task_results:
        score = task_results["document_analysis"].outputs.get("compliance_score", 0)
        logger.info(f"📊 Overall Compliance Score: {score:.1%}")
    
    if "gap_identification" in task_results:
        gaps = task_results["gap_identification"].outputs.get("gaps_identified", [])
        logger.info(f"⚠️  Critical Gaps Found: {len(gaps)}")
    
    if "risk_calculation" in task_results:
        financial_impact = task_results["risk_calculation"].outputs.get("financial_impact", 0)
        logger.info(f"💰 Financial Exposure: €{financial_impact:,.0f}")
    
    if "report_generation" in task_results:
        report = task_results["report_generation"].outputs.get("compliance_report", {})
        if report:
            logger.info(f"📄 Report Generated: {report.get('report_format', 'unknown')} format")

# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Main entry point for the example"""
    
    print("DORA Compliance Agent Orchestration Platform")
    print("=" * 50)
    print()
    
    try:
        # Run simulation (doesn't require infrastructure)
        await simulate_workflow_execution()
        
        print("\n" + "=" * 50)
        print("✅ Example completed successfully!")
        print("\nTo run with full infrastructure:")
        print("1. Set up PostgreSQL, Redis, and Kafka")
        print("2. Update configuration in run_dora_compliance_example()")
        print("3. Call run_dora_compliance_example() instead of simulate_workflow_execution()")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 