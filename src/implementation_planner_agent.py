#!/usr/bin/env python3
"""
DORA Compliance Implementation Planner Agent

This module generates detailed project roadmaps with timelines, resource allocation,
dependency mapping, and milestone tracking. It converts gap assessments into
structured project plans with Gantt chart visualizations and integrates with
project management methodologies.

Author: DORA Compliance System
Created: 2025-05-24
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import uuid
import itertools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskStatus(Enum):
    """Task status values"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    DEFERRED = "deferred"

class ResourceType(Enum):
    """Types of project resources"""
    INTERNAL_FTE = "internal_fte"
    EXTERNAL_CONSULTANT = "external_consultant"
    TECHNOLOGY = "technology"
    TRAINING = "training"
    BUDGET = "budget"

class ProjectMethodology(Enum):
    """Project management methodologies"""
    WATERFALL = "waterfall"
    AGILE = "agile"
    HYBRID = "hybrid"
    PRINCE2 = "prince2"

class RiskLevel(Enum):
    """Project risk levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ProjectResource:
    """Represents a project resource"""
    id: str
    name: str
    resource_type: ResourceType
    cost_per_unit: Decimal
    availability_percent: float = 100.0
    skills: List[str] = None
    location: str = ""
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['resource_type'] = self.resource_type.value
        result['cost_per_unit'] = float(self.cost_per_unit)
        return result

@dataclass
class ProjectTask:
    """Represents a project task in the implementation plan"""
    id: str
    name: str
    description: str
    duration_days: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    dependencies: List[str] = None
    assigned_resources: List[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.NOT_STARTED
    completion_percent: float = 0.0
    estimated_effort_hours: float = 0.0
    gap_reference: Optional[str] = None
    dora_requirement: Optional[str] = None
    deliverables: List[str] = None
    success_criteria: List[str] = None
    risks: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.assigned_resources is None:
            self.assigned_resources = []
        if self.deliverables is None:
            self.deliverables = []
        if self.success_criteria is None:
            self.success_criteria = []
        if self.risks is None:
            self.risks = []
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['priority'] = self.priority.value
        result['status'] = self.status.value
        if self.start_date:
            result['start_date'] = self.start_date.isoformat()
        if self.end_date:
            result['end_date'] = self.end_date.isoformat()
        return result

@dataclass
class ProjectMilestone:
    """Represents a project milestone"""
    id: str
    name: str
    description: str
    target_date: date
    dependencies: List[str] = None
    deliverables: List[str] = None
    success_criteria: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.deliverables is None:
            self.deliverables = []
        if self.success_criteria is None:
            self.success_criteria = []
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['target_date'] = self.target_date.isoformat()
        return result

@dataclass
class ProjectPhase:
    """Represents a project phase"""
    id: str
    name: str
    description: str
    start_date: date
    end_date: date
    tasks: List[str] = None
    milestones: List[str] = None
    success_criteria: List[str] = None
    
    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []
        if self.milestones is None:
            self.milestones = []
        if self.success_criteria is None:
            self.success_criteria = []
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['start_date'] = self.start_date.isoformat()
        result['end_date'] = self.end_date.isoformat()
        return result

@dataclass
class ImplementationPlan:
    """Complete implementation plan"""
    id: str
    name: str
    description: str
    project_start_date: date
    project_end_date: date
    methodology: ProjectMethodology
    total_budget: Decimal
    tasks: List[ProjectTask]
    phases: List[ProjectPhase]
    milestones: List[ProjectMilestone]
    resources: List[ProjectResource]
    risk_assessment: Dict[str, Any]
    success_metrics: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['project_start_date'] = self.project_start_date.isoformat()
        result['project_end_date'] = self.project_end_date.isoformat()
        result['methodology'] = self.methodology.value
        result['total_budget'] = float(self.total_budget)
        result['tasks'] = [task.to_dict() for task in self.tasks]
        result['phases'] = [phase.to_dict() for phase in self.phases]
        result['milestones'] = [milestone.to_dict() for milestone in self.milestones]
        result['resources'] = [resource.to_dict() for resource in self.resources]
        return result

class TaskDependencyAnalyzer:
    """Analyzes and optimizes task dependencies"""
    
    def __init__(self):
        self.tasks = {}
        
    def analyze_dependencies(self, tasks: List[ProjectTask]) -> Dict[str, Any]:
        """Analyze task dependencies and identify critical path"""
        
        self.tasks = {task.id: task for task in tasks}
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(tasks)
        
        # Find critical path
        critical_path = self._find_critical_path(dependency_graph)
        
        # Identify potential conflicts
        conflicts = self._identify_dependency_conflicts(dependency_graph)
        
        # Calculate project duration
        project_duration = self._calculate_project_duration(critical_path)
        
        return {
            "dependency_graph": dependency_graph,
            "critical_path": critical_path,
            "critical_path_duration": project_duration,
            "dependency_conflicts": conflicts,
            "task_levels": self._calculate_task_levels(dependency_graph),
            "parallel_opportunities": self._find_parallel_opportunities(dependency_graph)
        }
    
    def _build_dependency_graph(self, tasks: List[ProjectTask]) -> Dict[str, List[str]]:
        """Build a graph of task dependencies"""
        graph = {}
        
        for task in tasks:
            graph[task.id] = task.dependencies.copy()
        
        return graph
    
    def _find_critical_path(self, dependency_graph: Dict[str, List[str]]) -> List[str]:
        """Find the critical path through the project"""
        
        # Simple critical path calculation based on longest path
        # In a real implementation, this would use more sophisticated algorithms
        
        def get_task_duration(task_id: str) -> int:
            return self.tasks[task_id].duration_days if task_id in self.tasks else 0
        
        def calculate_path_duration(path: List[str]) -> int:
            return sum(get_task_duration(task_id) for task_id in path)
        
        # Find all possible paths
        all_paths = self._find_all_paths(dependency_graph)
        
        # Return the longest path
        if all_paths:
            return max(all_paths, key=calculate_path_duration)
        else:
            return []
    
    def _find_all_paths(self, dependency_graph: Dict[str, List[str]]) -> List[List[str]]:
        """Find all possible paths through the dependency graph"""
        
        # Simplified path finding - in practice would use more sophisticated algorithms
        paths = []
        
        # Find leaf nodes (tasks with no dependencies)
        leaf_nodes = [task_id for task_id, deps in dependency_graph.items() if not deps]
        
        for leaf in leaf_nodes:
            path = self._trace_path_backwards(leaf, dependency_graph)
            if path:
                paths.append(path)
        
        return paths
    
    def _trace_path_backwards(self, task_id: str, dependency_graph: Dict[str, List[str]]) -> List[str]:
        """Trace a path backwards from a task to its dependencies"""
        
        path = [task_id]
        current_deps = dependency_graph.get(task_id, [])
        
        # Simple linear trace - real implementation would handle multiple dependencies
        if current_deps:
            # Take the first dependency for simplicity
            next_task = current_deps[0]
            sub_path = self._trace_path_backwards(next_task, dependency_graph)
            path = sub_path + path
        
        return path
    
    def _identify_dependency_conflicts(self, dependency_graph: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Identify potential dependency conflicts"""
        
        conflicts = []
        
        # Check for circular dependencies (simplified)
        for task_id in dependency_graph:
            if self._has_circular_dependency(task_id, dependency_graph, set()):
                conflicts.append({
                    "type": "circular_dependency",
                    "task_id": task_id,
                    "description": f"Task {task_id} may have circular dependencies"
                })
        
        return conflicts
    
    def _has_circular_dependency(self, task_id: str, graph: Dict[str, List[str]], visited: set) -> bool:
        """Check if a task has circular dependencies"""
        
        if task_id in visited:
            return True
        
        visited.add(task_id)
        
        for dep in graph.get(task_id, []):
            if self._has_circular_dependency(dep, graph, visited.copy()):
                return True
        
        return False
    
    def _calculate_task_levels(self, dependency_graph: Dict[str, List[str]]) -> Dict[str, int]:
        """Calculate the level of each task in the dependency hierarchy"""
        
        levels = {}
        
        def calculate_level(task_id: str) -> int:
            if task_id in levels:
                return levels[task_id]
            
            deps = dependency_graph.get(task_id, [])
            if not deps:
                levels[task_id] = 0
                return 0
            
            max_dep_level = max(calculate_level(dep) for dep in deps)
            levels[task_id] = max_dep_level + 1
            return levels[task_id]
        
        for task_id in dependency_graph:
            calculate_level(task_id)
        
        return levels
    
    def _calculate_project_duration(self, critical_path: List[str]) -> int:
        """Calculate total project duration based on critical path"""
        
        return sum(
            self.tasks[task_id].duration_days 
            for task_id in critical_path 
            if task_id in self.tasks
        )
    
    def _find_parallel_opportunities(self, dependency_graph: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Find opportunities for parallel task execution"""
        
        levels = self._calculate_task_levels(dependency_graph)
        
        # Group tasks by level
        level_groups = {}
        for task_id, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(task_id)
        
        opportunities = []
        for level, tasks in level_groups.items():
            if len(tasks) > 1:
                opportunities.append({
                    "level": level,
                    "parallel_tasks": tasks,
                    "potential_time_savings": f"Tasks at level {level} can be executed in parallel"
                })
        
        return opportunities

class ResourceOptimizer:
    """Optimizes resource allocation across project tasks"""
    
    def __init__(self):
        self.resources = {}
        self.tasks = {}
        
    def optimize_resource_allocation(self, 
                                   tasks: List[ProjectTask], 
                                   resources: List[ProjectResource]) -> Dict[str, Any]:
        """Optimize resource allocation across tasks"""
        
        self.tasks = {task.id: task for task in tasks}
        self.resources = {resource.id: resource for resource in resources}
        
        # Calculate resource requirements
        resource_requirements = self._calculate_resource_requirements(tasks)
        
        # Identify resource conflicts
        conflicts = self._identify_resource_conflicts(tasks, resources)
        
        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations(conflicts, resource_requirements)
        
        # Calculate resource utilization
        utilization = self._calculate_resource_utilization(tasks, resources)
        
        return {
            "resource_requirements": resource_requirements,
            "resource_conflicts": conflicts,
            "optimization_recommendations": recommendations,
            "resource_utilization": utilization,
            "resource_summary": self._generate_resource_summary(resources, utilization)
        }
    
    def _calculate_resource_requirements(self, tasks: List[ProjectTask]) -> Dict[str, Any]:
        """Calculate total resource requirements for the project"""
        
        requirements = {
            "total_effort_hours": sum(task.estimated_effort_hours for task in tasks),
            "by_resource_type": {},
            "by_skill": {},
            "peak_periods": {}
        }
        
        # Calculate by resource type (simplified)
        for task in tasks:
            # Estimate resource type requirements based on task characteristics
            if "governance" in task.name.lower():
                resource_type = "governance_specialist"
            elif "technical" in task.name.lower() or "system" in task.name.lower():
                resource_type = "technical_specialist"
            elif "training" in task.name.lower():
                resource_type = "training_specialist"
            else:
                resource_type = "project_manager"
            
            if resource_type not in requirements["by_resource_type"]:
                requirements["by_resource_type"][resource_type] = 0
            requirements["by_resource_type"][resource_type] += task.estimated_effort_hours
        
        return requirements
    
    def _identify_resource_conflicts(self, 
                                   tasks: List[ProjectTask], 
                                   resources: List[ProjectResource]) -> List[Dict[str, Any]]:
        """Identify potential resource allocation conflicts"""
        
        conflicts = []
        
        # Check for over-allocation (simplified)
        resource_allocation = {}
        
        for task in tasks:
            for resource_id in task.assigned_resources:
                if resource_id not in resource_allocation:
                    resource_allocation[resource_id] = 0
                resource_allocation[resource_id] += task.estimated_effort_hours
        
        # Check against resource capacity
        for resource in resources:
            allocated_hours = resource_allocation.get(resource.id, 0)
            # Assume 40 hours/week * 52 weeks * availability
            available_hours = 40 * 52 * (resource.availability_percent / 100)
            
            if allocated_hours > available_hours:
                conflicts.append({
                    "type": "over_allocation",
                    "resource_id": resource.id,
                    "resource_name": resource.name,
                    "allocated_hours": allocated_hours,
                    "available_hours": available_hours,
                    "over_allocation": allocated_hours - available_hours
                })
        
        return conflicts
    
    def _generate_optimization_recommendations(self, 
                                             conflicts: List[Dict[str, Any]], 
                                             requirements: Dict[str, Any]) -> List[str]:
        """Generate resource optimization recommendations"""
        
        recommendations = []
        
        if conflicts:
            recommendations.append("Consider hiring additional resources or extending timeline to resolve over-allocations")
            
            over_allocated_resources = [c for c in conflicts if c["type"] == "over_allocation"]
            if over_allocated_resources:
                recommendations.append(f"Critical: {len(over_allocated_resources)} resources are over-allocated")
        
        total_hours = requirements["total_effort_hours"]
        if total_hours > 10000:  # Large project
            recommendations.append("Consider breaking the project into smaller phases")
            recommendations.append("Implement resource sharing across teams")
        
        recommendations.append("Regular resource utilization reviews recommended")
        recommendations.append("Consider external consultants for specialized skills")
        
        return recommendations
    
    def _calculate_resource_utilization(self, 
                                      tasks: List[ProjectTask], 
                                      resources: List[ProjectResource]) -> Dict[str, float]:
        """Calculate resource utilization percentages"""
        
        utilization = {}
        
        # Calculate allocation for each resource
        for resource in resources:
            allocated_hours = sum(
                task.estimated_effort_hours 
                for task in tasks 
                if resource.id in task.assigned_resources
            )
            
            # Assume 40 hours/week * 52 weeks * availability
            available_hours = 40 * 52 * (resource.availability_percent / 100)
            
            utilization[resource.id] = (allocated_hours / available_hours * 100) if available_hours > 0 else 0
        
        return utilization
    
    def _generate_resource_summary(self, 
                                 resources: List[ProjectResource], 
                                 utilization: Dict[str, float]) -> Dict[str, Any]:
        """Generate resource summary statistics"""
        
        summary = {
            "total_resources": len(resources),
            "resource_types": {},
            "average_utilization": sum(utilization.values()) / len(utilization) if utilization else 0,
            "over_utilized_resources": sum(1 for u in utilization.values() if u > 100),
            "under_utilized_resources": sum(1 for u in utilization.values() if u < 50)
        }
        
        # Count by resource type
        for resource in resources:
            resource_type = resource.resource_type.value
            if resource_type not in summary["resource_types"]:
                summary["resource_types"][resource_type] = 0
            summary["resource_types"][resource_type] += 1
        
        return summary

class GanttChartGenerator:
    """Generates Gantt chart data for project visualization"""
    
    def generate_gantt_data(self, 
                           tasks: List[ProjectTask], 
                           phases: List[ProjectPhase]) -> Dict[str, Any]:
        """Generate Gantt chart data structure"""
        
        # Calculate date ranges
        start_dates = [task.start_date for task in tasks if task.start_date]
        end_dates = [task.end_date for task in tasks if task.end_date]
        
        if start_dates and end_dates:
            project_start = min(start_dates)
            project_end = max(end_dates)
        else:
            project_start = date.today()
            project_end = project_start + timedelta(days=365)
        
        # Generate task data for Gantt chart
        gantt_tasks = []
        for task in tasks:
            task_start = task.start_date or project_start
            task_end = task.end_date or (task_start + timedelta(days=task.duration_days))
            
            gantt_tasks.append({
                "id": task.id,
                "name": task.name,
                "start": task_start.isoformat(),
                "end": task_end.isoformat(),
                "duration": task.duration_days,
                "progress": task.completion_percent,
                "dependencies": task.dependencies,
                "priority": task.priority.value,
                "status": task.status.value,
                "assigned_resources": task.assigned_resources
            })
        
        # Generate phase data
        gantt_phases = []
        for phase in phases:
            gantt_phases.append({
                "id": phase.id,
                "name": phase.name,
                "start": phase.start_date.isoformat(),
                "end": phase.end_date.isoformat(),
                "tasks": phase.tasks
            })
        
        return {
            "project_timeline": {
                "start": project_start.isoformat(),
                "end": project_end.isoformat(),
                "duration_days": (project_end - project_start).days
            },
            "tasks": gantt_tasks,
            "phases": gantt_phases,
            "chart_config": {
                "time_scale": "days",
                "show_dependencies": True,
                "show_progress": True,
                "show_critical_path": True
            }
        }

class ImplementationPlannerAgent:
    """Main Implementation Planner Agent for DORA compliance projects"""
    
    def __init__(self, methodology: ProjectMethodology = ProjectMethodology.HYBRID):
        self.methodology = methodology
        self.dependency_analyzer = TaskDependencyAnalyzer()
        self.resource_optimizer = ResourceOptimizer()
        self.gantt_generator = GanttChartGenerator()
        
        logger.info(f"Implementation Planner Agent initialized with {methodology.value} methodology")
    
    def generate_implementation_plan(self, 
                                   gap_assessment_data: Dict[str, Any],
                                   financial_analysis_data: Dict[str, Any],
                                   project_constraints: Dict[str, Any] = None) -> ImplementationPlan:
        """Generate comprehensive implementation plan from gap assessment and financial analysis"""
        
        logger.info("Generating implementation plan from gap assessment and financial analysis...")
        
        if project_constraints is None:
            project_constraints = self._create_default_constraints()
        
        # Extract gaps and financial data
        critical_gaps = gap_assessment_data.get('critical_gaps', [])
        high_priority_gaps = gap_assessment_data.get('high_priority_gaps', [])
        medium_priority_gaps = gap_assessment_data.get('medium_priority_gaps', [])
        
        implementation_cost = financial_analysis_data.get('implementation_cost', {}).get('total_cost', 500000)
        timeline_months = financial_analysis_data.get('implementation_cost', {}).get('timeline_months', 12)
        
        # Generate project components
        tasks = self._generate_project_tasks(critical_gaps, high_priority_gaps, medium_priority_gaps)
        resources = self._generate_project_resources(implementation_cost)
        phases = self._generate_project_phases(tasks, timeline_months)
        milestones = self._generate_project_milestones(phases)
        
        # Calculate dates and dependencies
        project_start = project_constraints.get('start_date', date.today() + timedelta(days=30))
        tasks_with_dates = self._assign_task_dates(tasks, project_start)
        
        # Optimize dependencies and resources
        dependency_analysis = self.dependency_analyzer.analyze_dependencies(tasks_with_dates)
        resource_analysis = self.resource_optimizer.optimize_resource_allocation(tasks_with_dates, resources)
        
        # Calculate project end date
        project_end = project_start + timedelta(days=dependency_analysis['critical_path_duration'])
        
        # Generate risk assessment
        risk_assessment = self._generate_risk_assessment(dependency_analysis, resource_analysis)
        
        # Create implementation plan
        plan = ImplementationPlan(
            id=f"dora_impl_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="DORA Compliance Implementation Plan",
            description="Comprehensive implementation plan for achieving DORA regulatory compliance",
            project_start_date=project_start,
            project_end_date=project_end,
            methodology=self.methodology,
            total_budget=Decimal(str(implementation_cost)),
            tasks=tasks_with_dates,
            phases=phases,
            milestones=milestones,
            resources=resources,
            risk_assessment=risk_assessment,
            success_metrics=self._generate_success_metrics()
        )
        
        logger.info(f"Implementation plan generated: {len(tasks_with_dates)} tasks, {len(phases)} phases, {(project_end - project_start).days} days duration")
        
        return plan
    
    def _generate_project_tasks(self, 
                               critical_gaps: List[Dict[str, Any]], 
                               high_priority_gaps: List[Dict[str, Any]], 
                               medium_priority_gaps: List[Dict[str, Any]]) -> List[ProjectTask]:
        """Generate project tasks from gap assessment data"""
        
        tasks = []
        task_counter = 1
        
        # Foundation tasks (always needed)
        foundation_tasks = [
            ("Project Initiation and Governance Setup", "Establish project governance structure and stakeholder alignment", 10, 80, TaskPriority.CRITICAL),
            ("DORA Requirements Analysis", "Detailed analysis of all DORA regulatory requirements", 15, 120, TaskPriority.CRITICAL),
            ("Current State Assessment", "Comprehensive assessment of current ICT and risk management capabilities", 20, 160, TaskPriority.HIGH),
            ("Gap Analysis Documentation", "Document all identified gaps and prioritize remediation activities", 10, 80, TaskPriority.HIGH)
        ]
        
        for name, desc, duration, effort, priority in foundation_tasks:
            task = ProjectTask(
                id=f"TASK_{task_counter:03d}",
                name=name,
                description=desc,
                duration_days=duration,
                estimated_effort_hours=effort,
                priority=priority,
                deliverables=[f"{name} Report", "Stakeholder Sign-off"],
                success_criteria=["Deliverable approved by steering committee"],
                gap_reference="FOUNDATION"
            )
            tasks.append(task)
            task_counter += 1
        
        # Generate tasks for critical gaps
        for gap in critical_gaps:
            task_name = f"Address Critical Gap: {gap.get('category', 'Unknown')}"
            task_desc = gap.get('description', 'Address critical compliance gap')
            
            task = ProjectTask(
                id=f"TASK_{task_counter:03d}",
                name=task_name,
                description=task_desc,
                duration_days=self._estimate_task_duration(gap, 'critical'),
                estimated_effort_hours=self._estimate_task_effort(gap, 'critical'),
                priority=TaskPriority.CRITICAL,
                gap_reference=gap.get('id'),
                dora_requirement=gap.get('dora_reference'),
                deliverables=self._generate_task_deliverables(gap),
                success_criteria=self._generate_success_criteria(gap),
                risks=self._generate_task_risks(gap)
            )
            tasks.append(task)
            task_counter += 1
        
        # Generate tasks for high priority gaps
        for gap in high_priority_gaps:
            task_name = f"Address High Priority Gap: {gap.get('category', 'Unknown')}"
            task_desc = gap.get('description', 'Address high priority compliance gap')
            
            task = ProjectTask(
                id=f"TASK_{task_counter:03d}",
                name=task_name,
                description=task_desc,
                duration_days=self._estimate_task_duration(gap, 'high'),
                estimated_effort_hours=self._estimate_task_effort(gap, 'high'),
                priority=TaskPriority.HIGH,
                gap_reference=gap.get('id'),
                dora_requirement=gap.get('dora_reference'),
                deliverables=self._generate_task_deliverables(gap),
                success_criteria=self._generate_success_criteria(gap),
                risks=self._generate_task_risks(gap)
            )
            tasks.append(task)
            task_counter += 1
        
        # Generate tasks for medium priority gaps (if manageable number)
        if len(medium_priority_gaps) <= 5:  # Only include if manageable
            for gap in medium_priority_gaps:
                task_name = f"Address Medium Priority Gap: {gap.get('category', 'Unknown')}"
                task_desc = gap.get('description', 'Address medium priority compliance gap')
                
                task = ProjectTask(
                    id=f"TASK_{task_counter:03d}",
                    name=task_name,
                    description=task_desc,
                    duration_days=self._estimate_task_duration(gap, 'medium'),
                    estimated_effort_hours=self._estimate_task_effort(gap, 'medium'),
                    priority=TaskPriority.MEDIUM,
                    gap_reference=gap.get('id'),
                    dora_requirement=gap.get('dora_reference'),
                    deliverables=self._generate_task_deliverables(gap),
                    success_criteria=self._generate_success_criteria(gap),
                    risks=self._generate_task_risks(gap)
                )
                tasks.append(task)
                task_counter += 1
        
        # Final tasks
        final_tasks = [
            ("Testing and Validation", "Comprehensive testing of all implemented solutions", 20, 160, TaskPriority.HIGH),
            ("Regulatory Compliance Validation", "Validate compliance with all DORA requirements", 15, 120, TaskPriority.CRITICAL),
            ("Documentation and Knowledge Transfer", "Complete documentation and knowledge transfer to operational teams", 10, 80, TaskPriority.MEDIUM),
            ("Project Closure", "Project closure activities and lessons learned", 5, 40, TaskPriority.LOW)
        ]
        
        for name, desc, duration, effort, priority in final_tasks:
            task = ProjectTask(
                id=f"TASK_{task_counter:03d}",
                name=name,
                description=desc,
                duration_days=duration,
                estimated_effort_hours=effort,
                priority=priority,
                deliverables=[f"{name} Report"],
                success_criteria=["All deliverables completed and approved"],
                gap_reference="CLOSURE"
            )
            tasks.append(task)
            task_counter += 1
        
        # Assign dependencies
        self._assign_task_dependencies(tasks)
        
        return tasks
    
    def _estimate_task_duration(self, gap: Dict[str, Any], priority: str) -> int:
        """Estimate task duration based on gap characteristics"""
        
        base_duration = {
            'critical': 25,
            'high': 15,
            'medium': 10
        }.get(priority, 10)
        
        # Adjust based on gap category
        category = gap.get('category', '').lower()
        if 'governance' in category:
            return base_duration + 10  # Governance takes longer
        elif 'testing' in category:
            return base_duration + 15  # Testing takes much longer
        elif 'third party' in category:
            return base_duration + 5   # Third party coordination
        
        return base_duration
    
    def _estimate_task_effort(self, gap: Dict[str, Any], priority: str) -> float:
        """Estimate task effort in hours"""
        
        base_effort = {
            'critical': 200,
            'high': 120,
            'medium': 80
        }.get(priority, 80)
        
        # Adjust based on gap category
        category = gap.get('category', '').lower()
        if 'governance' in category:
            return base_effort * 1.5  # Governance requires more effort
        elif 'testing' in category:
            return base_effort * 2.0  # Testing requires significant effort
        elif 'incident' in category:
            return base_effort * 1.3  # Incident management is complex
        
        return base_effort
    
    def _generate_task_deliverables(self, gap: Dict[str, Any]) -> List[str]:
        """Generate deliverables for a gap-related task"""
        
        category = gap.get('category', '').lower()
        base_deliverables = ["Implementation Plan", "Testing Results", "Documentation"]
        
        if 'governance' in category:
            return base_deliverables + ["Governance Framework", "Policy Documents"]
        elif 'risk' in category:
            return base_deliverables + ["Risk Assessment", "Risk Register"]
        elif 'incident' in category:
            return base_deliverables + ["Incident Response Procedures", "Escalation Matrix"]
        elif 'testing' in category:
            return base_deliverables + ["Test Plan", "Test Results", "Validation Report"]
        
        return base_deliverables
    
    def _generate_success_criteria(self, gap: Dict[str, Any]) -> List[str]:
        """Generate success criteria for a gap-related task"""
        
        return [
            "Gap fully addressed according to DORA requirements",
            "Implementation tested and validated",
            "Documentation completed and approved",
            "Stakeholder sign-off obtained"
        ]
    
    def _generate_task_risks(self, gap: Dict[str, Any]) -> List[str]:
        """Generate risks for a gap-related task"""
        
        category = gap.get('category', '').lower()
        base_risks = ["Resource availability", "Technical complexity", "Timeline constraints"]
        
        if 'third party' in category:
            return base_risks + ["Vendor dependencies", "Contract negotiations"]
        elif 'testing' in category:
            return base_risks + ["Test environment setup", "Coordination with business"]
        elif 'governance' in category:
            return base_risks + ["Stakeholder alignment", "Change management"]
        
        return base_risks
    
    def _assign_task_dependencies(self, tasks: List[ProjectTask]) -> None:
        """Assign logical dependencies between tasks"""
        
        # Simple dependency assignment based on task types and priorities
        foundation_tasks = [t for t in tasks if t.gap_reference == "FOUNDATION"]
        gap_tasks = [t for t in tasks if t.gap_reference not in ["FOUNDATION", "CLOSURE"]]
        closure_tasks = [t for t in tasks if t.gap_reference == "CLOSURE"]
        
        # Foundation tasks depend on each other sequentially
        for i in range(1, len(foundation_tasks)):
            foundation_tasks[i].dependencies.append(foundation_tasks[i-1].id)
        
        # Gap tasks depend on foundation completion
        if foundation_tasks:
            foundation_completion = foundation_tasks[-1].id
            for task in gap_tasks:
                task.dependencies.append(foundation_completion)
        
        # Closure tasks depend on gap tasks
        if gap_tasks:
            for closure_task in closure_tasks:
                # Add dependencies on critical and high priority gap tasks
                for gap_task in gap_tasks:
                    if gap_task.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]:
                        closure_task.dependencies.append(gap_task.id)
    
    def _generate_project_resources(self, implementation_cost: float) -> List[ProjectResource]:
        """Generate project resources based on implementation cost"""
        
        resources = []
        
        # Project Manager
        resources.append(ProjectResource(
            id="PM_001",
            name="Senior Project Manager",
            resource_type=ResourceType.INTERNAL_FTE,
            cost_per_unit=Decimal("120000"),  # Annual salary
            availability_percent=100.0,
            skills=["Project Management", "DORA", "Financial Services"],
            location="Headquarters"
        ))
        
        # DORA Specialist
        resources.append(ProjectResource(
            id="DORA_001",
            name="DORA Compliance Specialist",
            resource_type=ResourceType.EXTERNAL_CONSULTANT,
            cost_per_unit=Decimal("1500"),  # Daily rate
            availability_percent=80.0,
            skills=["DORA", "Regulatory Compliance", "Risk Management"],
            location="Remote/On-site"
        ))
        
        # Technical Architect
        resources.append(ProjectResource(
            id="TECH_001",
            name="Senior Technical Architect",
            resource_type=ResourceType.INTERNAL_FTE,
            cost_per_unit=Decimal("140000"),  # Annual salary
            availability_percent=75.0,
            skills=["System Architecture", "ICT", "Security"],
            location="Headquarters"
        ))
        
        # Risk Analyst
        resources.append(ProjectResource(
            id="RISK_001",
            name="Risk Management Analyst",
            resource_type=ResourceType.INTERNAL_FTE,
            cost_per_unit=Decimal("90000"),   # Annual salary
            availability_percent=60.0,
            skills=["Risk Management", "Compliance", "Analysis"],
            location="Headquarters"
        ))
        
        # Business Analyst
        resources.append(ProjectResource(
            id="BA_001",
            name="Senior Business Analyst",
            resource_type=ResourceType.INTERNAL_FTE,
            cost_per_unit=Decimal("100000"),  # Annual salary
            availability_percent=50.0,
            skills=["Business Analysis", "Process Improvement", "Documentation"],
            location="Headquarters"
        ))
        
        # Training Specialist (if budget allows)
        if implementation_cost > 300000:
            resources.append(ProjectResource(
                id="TRAIN_001",
                name="Training Specialist",
                resource_type=ResourceType.EXTERNAL_CONSULTANT,
                cost_per_unit=Decimal("1200"),  # Daily rate
                availability_percent=40.0,
                skills=["Training", "Change Management", "DORA"],
                location="Remote/On-site"
            ))
        
        return resources
    
    def _generate_project_phases(self, tasks: List[ProjectTask], timeline_months: int) -> List[ProjectPhase]:
        """Generate project phases based on tasks"""
        
        total_days = timeline_months * 30
        
        phases = []
        
        # Phase 1: Foundation and Analysis
        phase1_start = date.today() + timedelta(days=30)
        phase1_duration = max(30, total_days // 4)
        phase1_end = phase1_start + timedelta(days=phase1_duration)
        
        phase1_tasks = [t.id for t in tasks if t.gap_reference == "FOUNDATION"]
        
        phases.append(ProjectPhase(
            id="PHASE_001",
            name="Foundation and Analysis",
            description="Project setup, governance establishment, and detailed gap analysis",
            start_date=phase1_start,
            end_date=phase1_end,
            tasks=phase1_tasks,
            success_criteria=[
                "Project governance established",
                "Complete gap analysis completed",
                "Implementation plan approved"
            ]
        ))
        
        # Phase 2: Core Implementation
        phase2_start = phase1_end + timedelta(days=1)
        phase2_duration = max(60, total_days // 2)
        phase2_end = phase2_start + timedelta(days=phase2_duration)
        
        phase2_tasks = [t.id for t in tasks if t.gap_reference not in ["FOUNDATION", "CLOSURE"] and t.priority == TaskPriority.CRITICAL]
        
        phases.append(ProjectPhase(
            id="PHASE_002",
            name="Core Implementation",
            description="Implementation of critical compliance requirements",
            start_date=phase2_start,
            end_date=phase2_end,
            tasks=phase2_tasks,
            success_criteria=[
                "All critical gaps addressed",
                "Core systems implemented",
                "Initial testing completed"
            ]
        ))
        
        # Phase 3: Extended Implementation
        phase3_start = phase2_end + timedelta(days=1)
        phase3_duration = max(30, total_days // 5)
        phase3_end = phase3_start + timedelta(days=phase3_duration)
        
        phase3_tasks = [t.id for t in tasks if t.gap_reference not in ["FOUNDATION", "CLOSURE"] and t.priority in [TaskPriority.HIGH, TaskPriority.MEDIUM]]
        
        phases.append(ProjectPhase(
            id="PHASE_003",
            name="Extended Implementation",
            description="Implementation of remaining compliance requirements",
            start_date=phase3_start,
            end_date=phase3_end,
            tasks=phase3_tasks,
            success_criteria=[
                "All high and medium priority gaps addressed",
                "System integration completed",
                "User training delivered"
            ]
        ))
        
        # Phase 4: Validation and Closure
        phase4_start = phase3_end + timedelta(days=1)
        phase4_duration = max(20, total_days - phase1_duration - phase2_duration - phase3_duration)
        phase4_end = phase4_start + timedelta(days=phase4_duration)
        
        phase4_tasks = [t.id for t in tasks if t.gap_reference == "CLOSURE"]
        
        phases.append(ProjectPhase(
            id="PHASE_004",
            name="Validation and Closure",
            description="Final testing, validation, and project closure",
            start_date=phase4_start,
            end_date=phase4_end,
            tasks=phase4_tasks,
            success_criteria=[
                "All DORA requirements validated",
                "Regulatory approval obtained",
                "Project successfully closed"
            ]
        ))
        
        return phases
    
    def _generate_project_milestones(self, phases: List[ProjectPhase]) -> List[ProjectMilestone]:
        """Generate project milestones based on phases"""
        
        milestones = []
        
        for i, phase in enumerate(phases):
            milestone = ProjectMilestone(
                id=f"MILESTONE_{i+1:03d}",
                name=f"{phase.name} Complete",
                description=f"Completion of {phase.name} phase deliverables",
                target_date=phase.end_date,
                dependencies=phase.tasks,
                success_criteria=phase.success_criteria
            )
            milestones.append(milestone)
        
        # Add final project milestone
        if phases:
            final_milestone = ProjectMilestone(
                id="MILESTONE_FINAL",
                name="DORA Compliance Achieved",
                description="Full DORA regulatory compliance achieved and validated",
                target_date=phases[-1].end_date,
                dependencies=[m.id for m in milestones],
                success_criteria=[
                    "100% DORA compliance achieved",
                    "Regulatory validation completed",
                    "All stakeholders satisfied"
                ]
            )
            milestones.append(final_milestone)
        
        return milestones
    
    def _assign_task_dates(self, tasks: List[ProjectTask], project_start: date) -> List[ProjectTask]:
        """Assign start and end dates to tasks based on dependencies"""
        
        # Simple scheduling algorithm - in practice would use more sophisticated methods
        scheduled_tasks = {}
        current_date = project_start
        
        # Sort tasks by priority and dependencies
        tasks_to_schedule = tasks.copy()
        scheduled_task_ids = set()
        
        while tasks_to_schedule:
            # Find tasks with no unscheduled dependencies
            ready_tasks = []
            for task in tasks_to_schedule:
                if all(dep_id in scheduled_task_ids for dep_id in task.dependencies):
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Break circular dependencies by scheduling the first remaining task
                ready_tasks = [tasks_to_schedule[0]]
            
            # Schedule ready tasks
            for task in ready_tasks:
                # Calculate start date based on dependencies
                if task.dependencies:
                    dep_end_dates = [
                        scheduled_tasks[dep_id].end_date 
                        for dep_id in task.dependencies 
                        if dep_id in scheduled_tasks
                    ]
                    if dep_end_dates:
                        task_start = max(dep_end_dates) + timedelta(days=1)
                    else:
                        task_start = current_date
                else:
                    task_start = current_date
                
                task.start_date = task_start
                task.end_date = task_start + timedelta(days=task.duration_days - 1)
                
                scheduled_tasks[task.id] = task
                scheduled_task_ids.add(task.id)
                tasks_to_schedule.remove(task)
        
        return list(scheduled_tasks.values())
    
    def _generate_risk_assessment(self, 
                                dependency_analysis: Dict[str, Any], 
                                resource_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive risk assessment"""
        
        risks = []
        
        # Dependency risks
        if dependency_analysis['dependency_conflicts']:
            risks.append({
                "category": "Dependencies",
                "risk": "Circular or conflicting task dependencies",
                "impact": "High",
                "probability": "Medium",
                "mitigation": "Review and resolve dependency conflicts before project start"
            })
        
        # Resource risks
        if resource_analysis['resource_conflicts']:
            risks.append({
                "category": "Resources",
                "risk": "Resource over-allocation or conflicts",
                "impact": "High", 
                "probability": "High",
                "mitigation": "Hire additional resources or extend timeline"
            })
        
        # Timeline risks
        critical_path_duration = dependency_analysis['critical_path_duration']
        if critical_path_duration > 365:  # More than 1 year
            risks.append({
                "category": "Timeline",
                "risk": "Extended project duration may impact regulatory deadlines",
                "impact": "Critical",
                "probability": "Medium",
                "mitigation": "Consider parallel execution and additional resources"
            })
        
        # Regulatory risks
        risks.append({
            "category": "Regulatory",
            "risk": "DORA requirements may change during implementation",
            "impact": "Medium",
            "probability": "Low",
            "mitigation": "Regular regulatory monitoring and agile adaptation"
        })
        
        return {
            "overall_risk_level": self._calculate_overall_risk_level(risks),
            "risk_items": risks,
            "risk_mitigation_plan": self._generate_risk_mitigation_plan(risks),
            "risk_monitoring_plan": [
                "Weekly risk review meetings",
                "Monthly risk register updates",
                "Quarterly risk assessment reviews"
            ]
        }
    
    def _calculate_overall_risk_level(self, risks: List[Dict[str, Any]]) -> str:
        """Calculate overall project risk level"""
        
        critical_risks = sum(1 for risk in risks if risk['impact'] == 'Critical')
        high_risks = sum(1 for risk in risks if risk['impact'] == 'High')
        
        if critical_risks > 0:
            return "Critical"
        elif high_risks > 2:
            return "High"
        elif high_risks > 0:
            return "Medium"
        else:
            return "Low"
    
    def _generate_risk_mitigation_plan(self, risks: List[Dict[str, Any]]) -> List[str]:
        """Generate risk mitigation plan"""
        
        mitigation_plan = []
        
        for risk in risks:
            mitigation_plan.append(f"{risk['category']}: {risk['mitigation']}")
        
        # Add general mitigation strategies
        mitigation_plan.extend([
            "Establish clear escalation procedures",
            "Maintain regular stakeholder communication",
            "Implement change control processes",
            "Monitor progress against milestones weekly"
        ])
        
        return mitigation_plan
    
    def _generate_success_metrics(self) -> List[str]:
        """Generate project success metrics"""
        
        return [
            "100% of critical gaps addressed",
            "All DORA requirements implemented",
            "Project delivered on time and within budget",
            "Regulatory validation achieved",
            "Stakeholder satisfaction >90%",
            "Zero critical post-implementation issues",
            "Knowledge transfer completed",
            "Operational readiness achieved"
        ]
    
    def _create_default_constraints(self) -> Dict[str, Any]:
        """Create default project constraints"""
        
        return {
            "start_date": date.today() + timedelta(days=30),
            "max_duration_months": 18,
            "budget_limit": 2000000,  # €2M
            "resource_constraints": {
                "max_internal_fte": 5,
                "max_external_consultants": 3
            },
            "delivery_constraints": [
                "DORA enforcement deadline",
                "Regulatory examination schedule",
                "Business impact minimization"
            ]
        }
    
    def export_gantt_chart_data(self, plan: ImplementationPlan) -> Dict[str, Any]:
        """Export Gantt chart data for visualization"""
        
        return self.gantt_generator.generate_gantt_data(plan.tasks, plan.phases)
    
    def export_project_plan(self, plan: ImplementationPlan, format_type: str = "json") -> str:
        """Export implementation plan in various formats"""
        
        if format_type.lower() == "json":
            return json.dumps(plan.to_dict(), indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

def demonstrate_implementation_planner():
    """Demonstrate the Implementation Planner Agent capabilities"""
    
    print("📋 DORA Compliance Implementation Planner Agent")
    print("=" * 55)
    
    # Sample gap assessment data
    gap_data = {
        'critical_gaps': [
            {
                'id': 'GAP-001',
                'category': 'ICT Governance',
                'description': 'Insufficient ICT governance framework and board oversight'
            },
            {
                'id': 'GAP-002',
                'category': 'Digital Operational Resilience Testing',
                'description': 'No comprehensive testing programme for critical systems'
            }
        ],
        'high_priority_gaps': [
            {
                'id': 'GAP-003',
                'category': 'ICT Risk Management',
                'description': 'Manual risk assessment processes lack automation'
            },
            {
                'id': 'GAP-004',
                'category': 'ICT-Related Incident Management',
                'description': 'Incident response procedures need enhancement'
            }
        ],
        'medium_priority_gaps': [
            {
                'id': 'GAP-005',
                'category': 'ICT Third-Party Risk Management',
                'description': 'Third-party risk assessment framework requires improvement'
            }
        ]
    }
    
    # Sample financial analysis data
    financial_data = {
        'implementation_cost': {
            'total_cost': 750000,
            'timeline_months': 9
        },
        'penalty_analysis': {
            'maximum_penalty_risk': 10000000
        }
    }
    
    # Create planner agent
    planner = ImplementationPlannerAgent(ProjectMethodology.HYBRID)
    
    print(f"🎯 Generating Implementation Plan...")
    print(f"   • Methodology: {planner.methodology.value}")
    print(f"   • Critical Gaps: {len(gap_data['critical_gaps'])}")
    print(f"   • High Priority Gaps: {len(gap_data['high_priority_gaps'])}")
    print(f"   • Budget: €{financial_data['implementation_cost']['total_cost']:,.0f}")
    print(f"   • Timeline: {financial_data['implementation_cost']['timeline_months']} months")
    
    # Generate implementation plan
    plan = planner.generate_implementation_plan(gap_data, financial_data)
    
    print(f"\n✅ Implementation Plan Generated!")
    print(f"   • Plan ID: {plan.id}")
    print(f"   • Project Duration: {(plan.project_end_date - plan.project_start_date).days} days")
    print(f"   • Total Tasks: {len(plan.tasks)}")
    print(f"   • Project Phases: {len(plan.phases)}")
    print(f"   • Milestones: {len(plan.milestones)}")
    print(f"   • Resources: {len(plan.resources)}")
    
    # Display phases
    print(f"\n📅 Project Phases:")
    for phase in plan.phases:
        duration = (phase.end_date - phase.start_date).days
        print(f"   • {phase.name}: {duration} days ({len(phase.tasks)} tasks)")
    
    # Display critical path tasks
    print(f"\n🛤️  Sample Tasks:")
    critical_tasks = [t for t in plan.tasks if t.priority == TaskPriority.CRITICAL][:5]
    for task in critical_tasks:
        print(f"   • {task.name}")
        print(f"     Duration: {task.duration_days} days | Effort: {task.estimated_effort_hours} hours")
        print(f"     Priority: {task.priority.value} | Dependencies: {len(task.dependencies)}")
    
    # Display resource summary
    print(f"\n👥 Resource Summary:")
    resource_summary = {}
    for resource in plan.resources:
        resource_type = resource.resource_type.value
        resource_summary[resource_type] = resource_summary.get(resource_type, 0) + 1
    
    for resource_type, count in resource_summary.items():
        print(f"   • {resource_type.replace('_', ' ').title()}: {count}")
    
    # Display risk assessment
    print(f"\n⚠️  Risk Assessment:")
    print(f"   • Overall Risk Level: {plan.risk_assessment['overall_risk_level']}")
    print(f"   • Risk Items: {len(plan.risk_assessment['risk_items'])}")
    for risk in plan.risk_assessment['risk_items'][:3]:
        print(f"   • {risk['category']}: {risk['risk']} ({risk['impact']} impact)")
    
    # Generate Gantt chart data
    print(f"\n📊 Generating Gantt Chart Data...")
    gantt_data = planner.export_gantt_chart_data(plan)
    print(f"   • Timeline: {gantt_data['project_timeline']['duration_days']} days")
    print(f"   • Chart Tasks: {len(gantt_data['tasks'])}")
    print(f"   • Chart Phases: {len(gantt_data['phases'])}")
    
    # Display success metrics
    print(f"\n🎯 Success Metrics ({len(plan.success_metrics)} total):")
    for metric in plan.success_metrics[:4]:
        print(f"   • {metric}")
    
    print(f"\n✅ Implementation Planner Agent Demonstration Complete!")

if __name__ == "__main__":
    demonstrate_implementation_planner() 