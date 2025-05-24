#!/usr/bin/env python3
"""
Advanced Cost Estimation Framework

Comprehensive framework for estimating DORA implementation costs including
software development, hardware, licensing, personnel, training, and maintenance.
Provides templates, vendor quote integration, and historical cost analysis.

Author: DORA Compliance System
Date: 2025-01-23
"""

import json
import logging
import statistics
from typing import Dict, List, Optional, Union, Tuple, Any
from decimal import Decimal
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import re
import csv
from pathlib import Path

from .financial_data import FinancialProfile, Currency, CompanySize


class CostCategory(Enum):
    """Cost categories for DORA implementation"""
    SOFTWARE_DEVELOPMENT = "software_development"
    HARDWARE_INFRASTRUCTURE = "hardware_infrastructure"
    SOFTWARE_LICENSING = "software_licensing"
    PERSONNEL_COSTS = "personnel_costs"
    TRAINING_CERTIFICATION = "training_certification"
    MAINTENANCE_OPERATIONS = "maintenance_operations"
    CONSULTING_SERVICES = "consulting_services"
    REGULATORY_COMPLIANCE = "regulatory_compliance"


class ProjectComplexity(Enum):
    """Project complexity levels affecting cost estimation"""
    SIMPLE = "simple"         # Basic policy updates, documentation
    MODERATE = "moderate"     # System integrations, process improvements
    COMPLEX = "complex"       # Major system overhauls, new implementations
    ENTERPRISE = "enterprise" # Organization-wide transformations


class ImplementationType(Enum):
    """Types of DORA implementation scenarios"""
    GOVERNANCE_FRAMEWORK = "governance_framework"
    RISK_MANAGEMENT_SYSTEM = "risk_management_system"
    INCIDENT_MANAGEMENT = "incident_management"
    RESILIENCE_TESTING = "resilience_testing"
    THIRD_PARTY_MANAGEMENT = "third_party_management"
    INFORMATION_SHARING = "information_sharing"
    FULL_COMPLIANCE = "full_compliance"


@dataclass
class CostComponent:
    """Individual cost component with detailed breakdown"""
    
    category: CostCategory
    description: str
    base_cost: Decimal
    unit: str = "fixed"  # "fixed", "per_user", "per_month", "per_system"
    quantity: int = 1
    complexity_multiplier: float = 1.0
    timeline_months: int = 12
    
    # Cost adjustments
    regional_multiplier: float = 1.0
    size_multiplier: float = 1.0
    risk_buffer: float = 0.2  # 20% contingency
    
    # Additional metadata
    vendor_quote: Optional[Decimal] = None
    historical_average: Optional[Decimal] = None
    confidence_level: float = 0.7
    dependencies: List[str] = field(default_factory=list)
    
    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost with all multipliers"""
        adjusted_cost = (
            self.base_cost * 
            self.quantity * 
            Decimal(str(self.complexity_multiplier)) *
            Decimal(str(self.regional_multiplier)) *
            Decimal(str(self.size_multiplier)) *
            (1 + Decimal(str(self.risk_buffer)))
        )
        
        # Use vendor quote if available and reliable
        if self.vendor_quote and self.confidence_level > 0.8:
            return min(adjusted_cost, self.vendor_quote * Decimal('1.1'))  # Allow 10% buffer
        
        return adjusted_cost


@dataclass
class CostTemplate:
    """Template for specific implementation scenarios"""
    
    template_id: str
    name: str
    description: str
    implementation_type: ImplementationType
    typical_complexity: ProjectComplexity
    
    # Template components
    components: List[CostComponent] = field(default_factory=list)
    
    # Template metadata
    typical_timeline_months: int = 12
    success_rate: float = 0.85
    common_risks: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    
    @property
    def total_template_cost(self) -> Decimal:
        """Calculate total cost for this template"""
        return sum(component.total_cost for component in self.components)


@dataclass
class VendorQuote:
    """Vendor pricing information"""
    
    vendor_name: str
    product_service: str
    category: CostCategory
    quoted_price: Decimal
    quote_date: datetime
    
    # Optional fields with defaults
    currency: Currency = Currency.EUR
    validity_period_days: int = 30
    includes_support: bool = False
    includes_implementation: bool = False
    payment_terms: str = "Net 30"
    minimum_commitment: Optional[str] = None
    scalability_options: List[str] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if quote is still valid"""
        expiry_date = self.quote_date + timedelta(days=self.validity_period_days)
        return datetime.now() < expiry_date


@dataclass
class HistoricalCostRecord:
    """Historical cost data for benchmarking"""
    
    project_name: str
    implementation_type: ImplementationType
    company_size: CompanySize
    actual_cost: Decimal
    planned_cost: Decimal
    
    # Project details
    completion_date: datetime
    timeline_months: int
    complexity: ProjectComplexity
    industry: str
    region: str = "EU"
    
    # Outcomes
    success_level: float = 1.0  # 0.0 to 1.0
    cost_variance: float = 0.0  # (actual - planned) / planned
    lessons_learned: List[str] = field(default_factory=list)
    
    @property
    def cost_per_month(self) -> Decimal:
        """Calculate cost per month"""
        return self.actual_cost / max(self.timeline_months, 1)


class AdvancedCostEstimator:
    """Advanced cost estimation engine with multiple methodologies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates: Dict[str, CostTemplate] = {}
        self.vendor_quotes: List[VendorQuote] = []
        self.historical_records: List[HistoricalCostRecord] = []
        
        # Load built-in templates and data
        self._initialize_default_templates()
        self._load_historical_data()
    
    def estimate_implementation_cost(
        self,
        implementation_type: ImplementationType,
        company_profile: FinancialProfile,
        complexity: ProjectComplexity = ProjectComplexity.MODERATE,
        custom_requirements: Optional[List[str]] = None,
        use_vendor_quotes: bool = True,
        timeline_months: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive cost estimate for DORA implementation
        
        Args:
            implementation_type: Type of implementation scenario
            company_profile: Company financial and operational profile
            complexity: Project complexity level
            custom_requirements: Additional custom requirements
            use_vendor_quotes: Whether to incorporate vendor quotes
            timeline_months: Custom timeline (uses template default if None)
            
        Returns:
            Comprehensive cost estimate with breakdown and analysis
        """
        
        try:
            # Get appropriate template
            template = self._get_best_template(implementation_type, complexity)
            
            # Determine company size and regional factors
            company_size = self._determine_company_size(company_profile.annual_revenue)
            regional_multiplier = self._get_regional_multiplier(company_profile.country_of_incorporation)
            
            # Calculate component costs
            estimated_components = []
            total_cost = Decimal('0')
            
            for component in template.components:
                # Apply company-specific adjustments
                adjusted_component = self._adjust_component_for_company(
                    component, company_size, company_profile, regional_multiplier
                )
                
                # Apply vendor quotes if available and requested
                if use_vendor_quotes:
                    self._apply_vendor_quotes(adjusted_component)
                
                estimated_components.append(adjusted_component)
                total_cost += adjusted_component.total_cost
            
            # Add custom requirements costs
            if custom_requirements:
                custom_costs = self._estimate_custom_requirements(
                    custom_requirements, company_size, complexity
                )
                estimated_components.extend(custom_costs)
                total_cost += sum(comp.total_cost for comp in custom_costs)
            
            # Get historical benchmarks
            historical_benchmark = self._get_historical_benchmark(
                implementation_type, company_size, complexity
            )
            
            # Calculate timeline
            estimated_timeline = timeline_months or template.typical_timeline_months
            adjusted_timeline = self._adjust_timeline_for_complexity(
                estimated_timeline, complexity, company_size
            )
            
            # Risk analysis
            risk_analysis = self._analyze_implementation_risks(
                template, company_profile, complexity
            )
            
            # Generate final estimate
            estimate = {
                "implementation_type": implementation_type.value,
                "complexity": complexity.value,
                "total_cost_eur": total_cost,
                "timeline_months": adjusted_timeline,
                "cost_per_month": total_cost / max(adjusted_timeline, 1),
                
                # Cost breakdown
                "cost_breakdown": {
                    category.value: sum(
                        comp.total_cost for comp in estimated_components 
                        if comp.category == category
                    )
                    for category in CostCategory
                },
                
                # Component details
                "detailed_components": [
                    {
                        "category": comp.category.value,
                        "description": comp.description,
                        "base_cost": comp.base_cost,
                        "total_cost": comp.total_cost,
                        "quantity": comp.quantity,
                        "unit": comp.unit,
                        "confidence": comp.confidence_level
                    }
                    for comp in estimated_components
                ],
                
                # Benchmarking
                "historical_benchmark": historical_benchmark,
                "template_used": template.template_id,
                
                # Risk and confidence
                "risk_analysis": risk_analysis,
                "overall_confidence": self._calculate_overall_confidence(estimated_components),
                
                # Recommendations
                "cost_optimization_opportunities": self._identify_cost_optimizations(estimated_components),
                "implementation_recommendations": self._generate_implementation_recommendations(
                    template, company_profile, risk_analysis
                )
            }
            
            self.logger.info(f"Cost estimate generated: {implementation_type.value} = €{total_cost:,.0f}")
            return estimate
            
        except Exception as e:
            self.logger.error(f"Error generating cost estimate: {e}")
            raise
    
    def _initialize_default_templates(self):
        """Initialize built-in cost estimation templates"""
        
        # ICT Governance Framework Template
        governance_components = [
            CostComponent(
                category=CostCategory.CONSULTING_SERVICES,
                description="Governance framework design and implementation",
                base_cost=Decimal('75000'),
                complexity_multiplier=1.2,
                timeline_months=6
            ),
            CostComponent(
                category=CostCategory.SOFTWARE_LICENSING,
                description="Governance, Risk & Compliance (GRC) platform license",
                base_cost=Decimal('50000'),
                unit="per_year",
                timeline_months=12
            ),
            CostComponent(
                category=CostCategory.PERSONNEL_COSTS,
                description="Internal governance team (0.5 FTE for 6 months)",
                base_cost=Decimal('45000'),
                quantity=1,
                timeline_months=6
            ),
            CostComponent(
                category=CostCategory.TRAINING_CERTIFICATION,
                description="Board and senior management DORA training",
                base_cost=Decimal('15000'),
                timeline_months=2
            )
        ]
        
        governance_template = CostTemplate(
            template_id="dora_governance_001",
            name="ICT Governance Framework Implementation",
            description="Establish comprehensive ICT governance framework aligned with DORA requirements",
            implementation_type=ImplementationType.GOVERNANCE_FRAMEWORK,
            typical_complexity=ProjectComplexity.MODERATE,
            components=governance_components,
            typical_timeline_months=6,
            common_risks=["Stakeholder resistance", "Resource constraints", "Regulatory interpretation"]
        )
        
        # Risk Management System Template
        risk_mgmt_components = [
            CostComponent(
                category=CostCategory.SOFTWARE_DEVELOPMENT,
                description="Risk management system development/customization",
                base_cost=Decimal('150000'),
                complexity_multiplier=1.5,
                timeline_months=8
            ),
            CostComponent(
                category=CostCategory.SOFTWARE_LICENSING,
                description="Risk management platform licenses",
                base_cost=Decimal('80000'),
                unit="per_year"
            ),
            CostComponent(
                category=CostCategory.HARDWARE_INFRASTRUCTURE,
                description="Infrastructure for risk management systems",
                base_cost=Decimal('40000'),
                timeline_months=1
            ),
            CostComponent(
                category=CostCategory.PERSONNEL_COSTS,
                description="Risk management specialists (2 FTE for 8 months)",
                base_cost=Decimal('120000'),
                quantity=2,
                timeline_months=8
            ),
            CostComponent(
                category=CostCategory.TRAINING_CERTIFICATION,
                description="Risk management team training and certification",
                base_cost=Decimal('25000'),
                timeline_months=3
            )
        ]
        
        risk_mgmt_template = CostTemplate(
            template_id="dora_risk_mgmt_001",
            name="ICT Risk Management System Implementation",
            description="Deploy comprehensive ICT risk management capabilities",
            implementation_type=ImplementationType.RISK_MANAGEMENT_SYSTEM,
            typical_complexity=ProjectComplexity.COMPLEX,
            components=risk_mgmt_components,
            typical_timeline_months=8,
            common_risks=["Integration complexity", "Data quality issues", "Process changes"]
        )
        
        # Add templates to registry
        self.templates[governance_template.template_id] = governance_template
        self.templates[risk_mgmt_template.template_id] = risk_mgmt_template
        
        # Initialize other templates
        self._add_resilience_testing_template()
        self._add_incident_management_template()
        self._add_third_party_management_template()
        self._add_full_compliance_template()
    
    def _add_resilience_testing_template(self):
        """Add resilience testing template"""
        testing_components = [
            CostComponent(
                category=CostCategory.SOFTWARE_LICENSING,
                description="Resilience testing tools and platforms",
                base_cost=Decimal('60000'),
                unit="per_year"
            ),
            CostComponent(
                category=CostCategory.CONSULTING_SERVICES,
                description="TLPT (Threat-Led Penetration Testing) services",
                base_cost=Decimal('100000'),
                timeline_months=3
            ),
            CostComponent(
                category=CostCategory.PERSONNEL_COSTS,
                description="Internal testing team (1.5 FTE for 12 months)",
                base_cost=Decimal('90000'),
                quantity=1,
                timeline_months=12
            ),
            CostComponent(
                category=CostCategory.HARDWARE_INFRASTRUCTURE,
                description="Testing environment infrastructure",
                base_cost=Decimal('30000'),
                timeline_months=1
            )
        ]
        
        testing_template = CostTemplate(
            template_id="dora_testing_001",
            name="Digital Operational Resilience Testing Programme",
            description="Implement comprehensive resilience testing including TLPT",
            implementation_type=ImplementationType.RESILIENCE_TESTING,
            typical_complexity=ProjectComplexity.COMPLEX,
            components=testing_components,
            typical_timeline_months=12
        )
        
        self.templates[testing_template.template_id] = testing_template
    
    def _add_incident_management_template(self):
        """Add incident management template"""
        incident_components = [
            CostComponent(
                category=CostCategory.SOFTWARE_LICENSING,
                description="Incident management platform license",
                base_cost=Decimal('35000'),
                unit="per_year"
            ),
            CostComponent(
                category=CostCategory.SOFTWARE_DEVELOPMENT,
                description="Custom incident workflow development",
                base_cost=Decimal('50000'),
                timeline_months=4
            ),
            CostComponent(
                category=CostCategory.PERSONNEL_COSTS,
                description="Incident response team (1 FTE for 12 months)",
                base_cost=Decimal('75000'),
                timeline_months=12
            ),
            CostComponent(
                category=CostCategory.TRAINING_CERTIFICATION,
                description="Incident response training programme",
                base_cost=Decimal('20000'),
                timeline_months=2
            )
        ]
        
        incident_template = CostTemplate(
            template_id="dora_incident_001",
            name="ICT Incident Management System",
            description="Deploy comprehensive incident management capabilities",
            implementation_type=ImplementationType.INCIDENT_MANAGEMENT,
            typical_complexity=ProjectComplexity.MODERATE,
            components=incident_components,
            typical_timeline_months=6
        )
        
        self.templates[incident_template.template_id] = incident_template
    
    def _add_third_party_management_template(self):
        """Add third-party management template"""
        third_party_components = [
            CostComponent(
                category=CostCategory.SOFTWARE_LICENSING,
                description="Vendor risk management platform",
                base_cost=Decimal('45000'),
                unit="per_year"
            ),
            CostComponent(
                category=CostCategory.CONSULTING_SERVICES,
                description="Third-party risk assessment services",
                base_cost=Decimal('60000'),
                timeline_months=4
            ),
            CostComponent(
                category=CostCategory.PERSONNEL_COSTS,
                description="Vendor management specialist (1 FTE for 12 months)",
                base_cost=Decimal('70000'),
                timeline_months=12
            ),
            CostComponent(
                category=CostCategory.REGULATORY_COMPLIANCE,
                description="Concentration risk analysis and reporting",
                base_cost=Decimal('25000'),
                timeline_months=6
            )
        ]
        
        third_party_template = CostTemplate(
            template_id="dora_third_party_001",
            name="ICT Third-Party Risk Management",
            description="Implement comprehensive third-party risk management",
            implementation_type=ImplementationType.THIRD_PARTY_MANAGEMENT,
            typical_complexity=ProjectComplexity.MODERATE,
            components=third_party_components,
            typical_timeline_months=8
        )
        
        self.templates[third_party_template.template_id] = third_party_template
    
    def _add_full_compliance_template(self):
        """Add full DORA compliance template"""
        full_compliance_components = [
            CostComponent(
                category=CostCategory.CONSULTING_SERVICES,
                description="Full DORA implementation programme management",
                base_cost=Decimal('200000'),
                complexity_multiplier=1.8,
                timeline_months=18
            ),
            CostComponent(
                category=CostCategory.SOFTWARE_LICENSING,
                description="Integrated compliance platform suite",
                base_cost=Decimal('150000'),
                unit="per_year"
            ),
            CostComponent(
                category=CostCategory.SOFTWARE_DEVELOPMENT,
                description="Custom integrations and development",
                base_cost=Decimal('300000'),
                complexity_multiplier=2.0,
                timeline_months=12
            ),
            CostComponent(
                category=CostCategory.HARDWARE_INFRASTRUCTURE,
                description="Infrastructure upgrades and new systems",
                base_cost=Decimal('100000'),
                timeline_months=6
            ),
            CostComponent(
                category=CostCategory.PERSONNEL_COSTS,
                description="Dedicated DORA implementation team (5 FTE for 18 months)",
                base_cost=Decimal('675000'),  # 5 FTE * €75K * 18 months
                quantity=5,
                timeline_months=18
            ),
            CostComponent(
                category=CostCategory.TRAINING_CERTIFICATION,
                description="Organization-wide DORA training programme",
                base_cost=Decimal('80000'),
                timeline_months=12
            ),
            CostComponent(
                category=CostCategory.MAINTENANCE_OPERATIONS,
                description="Ongoing compliance operations (first year)",
                base_cost=Decimal('120000'),
                unit="per_year"
            )
        ]
        
        full_compliance_template = CostTemplate(
            template_id="dora_full_compliance_001",
            name="Complete DORA Compliance Programme",
            description="Full-scale DORA compliance implementation across all pillars",
            implementation_type=ImplementationType.FULL_COMPLIANCE,
            typical_complexity=ProjectComplexity.ENTERPRISE,
            components=full_compliance_components,
            typical_timeline_months=18,
            common_risks=[
                "Programme complexity", "Resource coordination", "Regulatory changes",
                "Stakeholder alignment", "Technology integration challenges"
            ]
        )
        
        self.templates[full_compliance_template.template_id] = full_compliance_template
    
    def _load_historical_data(self):
        """Load historical cost data for benchmarking"""
        # Sample historical data - in production, this would be loaded from database
        sample_records = [
            HistoricalCostRecord(
                project_name="Bank ABC Governance Implementation",
                implementation_type=ImplementationType.GOVERNANCE_FRAMEWORK,
                company_size=CompanySize.LARGE,
                actual_cost=Decimal('240000'),
                planned_cost=Decimal('200000'),
                completion_date=datetime(2024, 6, 15),
                timeline_months=7,
                complexity=ProjectComplexity.MODERATE,
                industry="banking",
                cost_variance=0.2,
                success_level=0.9
            ),
            HistoricalCostRecord(
                project_name="InsureCorp Risk Management System",
                implementation_type=ImplementationType.RISK_MANAGEMENT_SYSTEM,
                company_size=CompanySize.MEDIUM,
                actual_cost=Decimal('450000'),
                planned_cost=Decimal('400000'),
                completion_date=datetime(2024, 8, 30),
                timeline_months=9,
                complexity=ProjectComplexity.COMPLEX,
                industry="insurance",
                cost_variance=0.125,
                success_level=0.85
            )
        ]
        
        self.historical_records.extend(sample_records)
    
    def _get_best_template(self, implementation_type: ImplementationType, complexity: ProjectComplexity) -> CostTemplate:
        """Find the best matching template for the implementation"""
        matching_templates = [
            template for template in self.templates.values()
            if template.implementation_type == implementation_type
        ]
        
        if not matching_templates:
            # Fallback to a generic template
            return self._create_generic_template(implementation_type, complexity)
        
        # Return the template that best matches the complexity
        return min(matching_templates, key=lambda t: abs(
            list(ProjectComplexity).index(t.typical_complexity) - 
            list(ProjectComplexity).index(complexity)
        ))
    
    def _create_generic_template(self, implementation_type: ImplementationType, complexity: ProjectComplexity) -> CostTemplate:
        """Create a generic template when no specific template exists"""
        base_cost_map = {
            ProjectComplexity.SIMPLE: Decimal('50000'),
            ProjectComplexity.MODERATE: Decimal('150000'),
            ProjectComplexity.COMPLEX: Decimal('400000'),
            ProjectComplexity.ENTERPRISE: Decimal('800000')
        }
        
        generic_components = [
            CostComponent(
                category=CostCategory.CONSULTING_SERVICES,
                description=f"Generic {implementation_type.value} implementation",
                base_cost=base_cost_map[complexity],
                complexity_multiplier=1.0,
                timeline_months=6 if complexity in [ProjectComplexity.SIMPLE, ProjectComplexity.MODERATE] else 12
            )
        ]
        
        return CostTemplate(
            template_id=f"generic_{implementation_type.value}",
            name=f"Generic {implementation_type.value.replace('_', ' ').title()}",
            description=f"Generic template for {implementation_type.value}",
            implementation_type=implementation_type,
            typical_complexity=complexity,
            components=generic_components
        )
    
    def _determine_company_size(self, annual_revenue: Decimal) -> CompanySize:
        """Determine company size from revenue"""
        revenue_millions = float(annual_revenue) / 1_000_000
        
        if revenue_millions < 50:
            return CompanySize.SMALL
        elif revenue_millions < 500:
            return CompanySize.MEDIUM
        elif revenue_millions < 5000:
            return CompanySize.LARGE
        else:
            return CompanySize.SYSTEMIC
    
    def _get_regional_multiplier(self, country: str) -> float:
        """Get cost multiplier based on geographic region"""
        region_multipliers = {
            "DE": 1.1, "FR": 1.05, "UK": 1.15, "CH": 1.3, "NO": 1.25,
            "ES": 0.9, "IT": 0.95, "PL": 0.7, "CZ": 0.65, "RO": 0.6,
            "EU": 1.0  # Default EU
        }
        return region_multipliers.get(country.upper(), 1.0)
    
    def _adjust_component_for_company(
        self, 
        component: CostComponent, 
        company_size: CompanySize, 
        profile: FinancialProfile,
        regional_multiplier: float
    ) -> CostComponent:
        """Adjust cost component for specific company characteristics"""
        adjusted_component = CostComponent(
            category=component.category,
            description=component.description,
            base_cost=component.base_cost,
            unit=component.unit,
            quantity=component.quantity,
            complexity_multiplier=component.complexity_multiplier,
            timeline_months=component.timeline_months,
            regional_multiplier=regional_multiplier,
            size_multiplier=self._get_size_multiplier(company_size),
            risk_buffer=component.risk_buffer,
            vendor_quote=component.vendor_quote,
            historical_average=component.historical_average,
            confidence_level=component.confidence_level,
            dependencies=component.dependencies.copy()
        )
        
        return adjusted_component
    
    def _get_size_multiplier(self, company_size: CompanySize) -> float:
        """Get cost multiplier based on company size"""
        size_multipliers = {
            CompanySize.SMALL: 0.7,
            CompanySize.MEDIUM: 1.0,
            CompanySize.LARGE: 1.4,
            CompanySize.SYSTEMIC: 2.0
        }
        return size_multipliers[company_size]
    
    def _apply_vendor_quotes(self, component: CostComponent):
        """Apply vendor quotes to component if available"""
        matching_quotes = [
            quote for quote in self.vendor_quotes
            if quote.category == component.category and quote.is_valid
        ]
        
        if matching_quotes:
            # Use the most recent valid quote
            best_quote = max(matching_quotes, key=lambda q: q.quote_date)
            component.vendor_quote = best_quote.quoted_price
            component.confidence_level = min(component.confidence_level + 0.1, 1.0)
    
    def _estimate_custom_requirements(
        self, 
        requirements: List[str], 
        company_size: CompanySize, 
        complexity: ProjectComplexity
    ) -> List[CostComponent]:
        """Estimate costs for custom requirements"""
        custom_components = []
        base_multiplier = self._get_size_multiplier(company_size)
        
        for req in requirements:
            # Simple heuristic-based estimation
            estimated_cost = Decimal('25000') * Decimal(str(base_multiplier))
            
            if any(keyword in req.lower() for keyword in ['integration', 'api', 'custom']):
                estimated_cost *= Decimal('1.5')
            
            if any(keyword in req.lower() for keyword in ['real-time', 'monitoring', 'dashboard']):
                estimated_cost *= Decimal('1.3')
            
            custom_component = CostComponent(
                category=CostCategory.SOFTWARE_DEVELOPMENT,
                description=f"Custom requirement: {req}",
                base_cost=estimated_cost,
                complexity_multiplier=1.0 if complexity == ProjectComplexity.SIMPLE else 1.5,
                confidence_level=0.5  # Lower confidence for custom estimates
            )
            
            custom_components.append(custom_component)
        
        return custom_components
    
    def _get_historical_benchmark(
        self, 
        implementation_type: ImplementationType, 
        company_size: CompanySize, 
        complexity: ProjectComplexity
    ) -> Dict[str, Any]:
        """Get historical benchmarking data"""
        matching_records = [
            record for record in self.historical_records
            if (record.implementation_type == implementation_type and 
                record.company_size == company_size)
        ]
        
        if not matching_records:
            return {"available": False, "message": "No historical data available"}
        
        costs = [float(record.actual_cost) for record in matching_records]
        timelines = [record.timeline_months for record in matching_records]
        variances = [record.cost_variance for record in matching_records]
        
        return {
            "available": True,
            "sample_size": len(matching_records),
            "average_cost": statistics.mean(costs),
            "median_cost": statistics.median(costs),
            "cost_range": {"min": min(costs), "max": max(costs)},
            "average_timeline": statistics.mean(timelines),
            "average_cost_variance": statistics.mean(variances),
            "success_rate": statistics.mean([r.success_level for r in matching_records])
        }
    
    def _adjust_timeline_for_complexity(self, base_timeline: int, complexity: ProjectComplexity, company_size: CompanySize) -> int:
        """Adjust timeline based on complexity and company size"""
        complexity_multipliers = {
            ProjectComplexity.SIMPLE: 0.8,
            ProjectComplexity.MODERATE: 1.0,
            ProjectComplexity.COMPLEX: 1.3,
            ProjectComplexity.ENTERPRISE: 1.6
        }
        
        size_adjustments = {
            CompanySize.SMALL: 0.9,
            CompanySize.MEDIUM: 1.0,
            CompanySize.LARGE: 1.2,
            CompanySize.SYSTEMIC: 1.4
        }
        
        adjusted_timeline = (
            base_timeline * 
            complexity_multipliers[complexity] * 
            size_adjustments[company_size]
        )
        
        return max(int(adjusted_timeline), 1)
    
    def _analyze_implementation_risks(
        self, 
        template: CostTemplate, 
        profile: FinancialProfile, 
        complexity: ProjectComplexity
    ) -> Dict[str, Any]:
        """Analyze implementation risks and impact on costs"""
        risk_factors = {
            "budget_overrun_probability": 0.3,
            "timeline_extension_probability": 0.25,
            "scope_creep_probability": 0.4,
            "technical_risks": [],
            "organizational_risks": [],
            "external_risks": []
        }
        
        # Adjust probabilities based on complexity
        if complexity == ProjectComplexity.ENTERPRISE:
            risk_factors["budget_overrun_probability"] += 0.2
            risk_factors["timeline_extension_probability"] += 0.15
            risk_factors["scope_creep_probability"] += 0.1
        
        # Add specific risks based on template
        risk_factors["technical_risks"] = template.common_risks
        
        return risk_factors
    
    def _calculate_overall_confidence(self, components: List[CostComponent]) -> float:
        """Calculate overall confidence in the estimate"""
        if not components:
            return 0.0
        
        total_cost = sum(comp.total_cost for comp in components)
        weighted_confidence = sum(
            comp.confidence_level * float(comp.total_cost) 
            for comp in components
        )
        
        return weighted_confidence / float(total_cost) if total_cost > 0 else 0.0
    
    def _identify_cost_optimizations(self, components: List[CostComponent]) -> List[str]:
        """Identify potential cost optimization opportunities"""
        optimizations = []
        
        # Analyze components for optimization opportunities
        total_cost = sum(comp.total_cost for comp in components)
        
        for component in components:
            cost_ratio = float(component.total_cost / total_cost)
            
            if cost_ratio > 0.3:  # Component represents >30% of total cost
                optimizations.append(
                    f"High-cost component '{component.description}' represents "
                    f"{cost_ratio:.1%} of total cost - consider alternatives or phased approach"
                )
            
            if component.confidence_level < 0.6:
                optimizations.append(
                    f"Low confidence in '{component.description}' estimate - "
                    f"seek additional quotes or detailed requirements"
                )
        
        # Add general optimization suggestions
        optimizations.extend([
            "Consider phased implementation to spread costs over time",
            "Evaluate build vs. buy decisions for software components",
            "Explore shared services or industry consortiums for cost sharing",
            "Review potential for leveraging existing infrastructure and tools"
        ])
        
        return optimizations[:5]  # Return top 5 recommendations
    
    def _generate_implementation_recommendations(
        self, 
        template: CostTemplate, 
        profile: FinancialProfile, 
        risk_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate implementation recommendations"""
        recommendations = []
        
        # Budget-based recommendations
        cost_to_revenue_ratio = float(template.total_template_cost / profile.annual_revenue)
        
        if cost_to_revenue_ratio > 0.01:  # >1% of revenue
            recommendations.append(
                "High cost relative to revenue - consider phased implementation approach"
            )
        
        # Risk-based recommendations
        if risk_analysis["budget_overrun_probability"] > 0.4:
            recommendations.append(
                "High budget overrun risk - recommend additional contingency and closer monitoring"
            )
        
        # Timeline recommendations
        if template.typical_timeline_months > 12:
            recommendations.append(
                "Long implementation timeline - establish clear milestones and governance checkpoints"
            )
        
        # General best practices
        recommendations.extend([
            "Establish dedicated project governance and steering committee",
            "Plan for regular regulatory guidance updates during implementation",
            "Include post-implementation review and optimization phase",
            "Ensure adequate change management and stakeholder communication"
        ])
        
        return recommendations
    
    def add_vendor_quote(self, quote: VendorQuote):
        """Add a vendor quote to the database"""
        self.vendor_quotes.append(quote)
        self.logger.info(f"Added vendor quote: {quote.vendor_name} - {quote.product_service}")
    
    def add_historical_record(self, record: HistoricalCostRecord):
        """Add a historical cost record"""
        self.historical_records.append(record)
        self.logger.info(f"Added historical record: {record.project_name}")
    
    def export_templates_to_json(self, file_path: str):
        """Export templates to JSON file"""
        templates_data = {
            template_id: {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "implementation_type": template.implementation_type.value,
                "typical_complexity": template.typical_complexity.value,
                "typical_timeline_months": template.typical_timeline_months,
                "components": [asdict(comp) for comp in template.components]
            }
            for template_id, template in self.templates.items()
        }
        
        with open(file_path, 'w') as f:
            json.dump(templates_data, f, indent=2, default=str)
        
        self.logger.info(f"Templates exported to {file_path}")


def create_demo_cost_estimator() -> AdvancedCostEstimator:
    """Create a demo cost estimator with sample data"""
    estimator = AdvancedCostEstimator()
    
    # Add sample vendor quotes
    sample_quotes = [
        VendorQuote(
            vendor_name="SecureGRC Corp",
            product_service="DORA Compliance Platform",
            category=CostCategory.SOFTWARE_LICENSING,
            quoted_price=Decimal('85000'),
            quote_date=datetime.now() - timedelta(days=5),
            includes_support=True,
            includes_implementation=False
        ),
        VendorQuote(
            vendor_name="RiskTech Solutions",
            product_service="Advanced Risk Management Suite",
            category=CostCategory.SOFTWARE_LICENSING,
            quoted_price=Decimal('120000'),
            quote_date=datetime.now() - timedelta(days=10),
            includes_support=True,
            includes_implementation=True
        )
    ]
    
    for quote in sample_quotes:
        estimator.add_vendor_quote(quote)
    
    return estimator


if __name__ == "__main__":
    # Example usage
    from .financial_data import create_demo_financial_profile
    
    estimator = create_demo_cost_estimator()
    profile = create_demo_financial_profile()
    
    # Generate cost estimate for full DORA compliance
    estimate = estimator.estimate_implementation_cost(
        implementation_type=ImplementationType.FULL_COMPLIANCE,
        company_profile=profile,
        complexity=ProjectComplexity.ENTERPRISE,
        custom_requirements=["Real-time monitoring dashboard", "API integrations"],
        use_vendor_quotes=True
    )
    
    print("=== DORA Implementation Cost Estimate ===")
    print(f"Total Cost: €{estimate['total_cost_eur']:,.0f}")
    print(f"Timeline: {estimate['timeline_months']} months")
    print(f"Monthly Cost: €{estimate['cost_per_month']:,.0f}")
    print(f"Overall Confidence: {estimate['overall_confidence']:.1%}")
    print()
    print("Cost Breakdown:")
    for category, cost in estimate['cost_breakdown'].items():
        if cost > 0:
            print(f"  {category.replace('_', ' ').title()}: €{cost:,.0f}") 