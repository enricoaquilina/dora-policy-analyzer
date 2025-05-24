#!/usr/bin/env python3
"""
DORA Compliance Business Case Generator

This module generates comprehensive, executive-ready business cases for DORA compliance
investments. It creates professional documents with financial analysis, risk assessment,
implementation timelines, and strategic recommendations in multiple formats.

Author: DORA Compliance System
Created: 2025-05-24
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import html
import base64
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentFormat(Enum):
    """Supported output document formats"""
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"
    CSV = "csv"

class BusinessCaseSection(Enum):
    """Business case document sections"""
    EXECUTIVE_SUMMARY = "executive_summary"
    FINANCIAL_ANALYSIS = "financial_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    IMPLEMENTATION_PLAN = "implementation_plan"
    STRATEGIC_RATIONALE = "strategic_rationale"
    APPENDICES = "appendices"

class AudienceLevel(Enum):
    """Target audience sophistication levels"""
    BOARD = "board"              # Board of Directors - high level, strategic focus
    CXO = "cxo"                  # C-suite executives - strategic with some detail
    MANAGEMENT = "management"     # Senior management - operational focus
    TECHNICAL = "technical"      # Technical teams - detailed implementation

@dataclass
class BusinessCaseConfig:
    """Configuration for business case generation"""
    company_name: str = "Financial Institution"
    document_title: str = "DORA Compliance Investment Business Case"
    author: str = "Chief Information Officer"
    audience_level: AudienceLevel = AudienceLevel.CXO
    include_charts: bool = True
    include_appendices: bool = True
    confidentiality_level: str = "Confidential"
    currency: str = "EUR"
    date_format: str = "%B %d, %Y"
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['audience_level'] = self.audience_level.value
        return result

@dataclass
class ImplementationPhase:
    """Individual implementation phase details"""
    phase_number: int
    phase_name: str
    duration_months: int
    cost_eur: Decimal
    activities: List[str]
    deliverables: List[str]
    success_criteria: List[str]
    dependencies: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['cost_eur'] = float(self.cost_eur)
        return result

@dataclass
class RiskItem:
    """Individual risk assessment item"""
    risk_id: str
    risk_name: str
    description: str
    probability: str  # "High", "Medium", "Low"
    impact: str       # "High", "Medium", "Low"
    risk_level: str   # "Critical", "High", "Medium", "Low"
    mitigation_strategy: str
    owner: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class BusinessCaseTemplate:
    """Base template for business case generation"""
    
    def __init__(self, config: BusinessCaseConfig):
        self.config = config
        
    def generate_executive_summary(self, financial_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate executive summary section"""
        
        penalty_risk = financial_data.get('penalty_analysis', {}).get('maximum_penalty_risk', 0)
        implementation_cost = financial_data.get('implementation_cost', {}).get('total_cost', 0)
        roi_data = financial_data.get('advanced_roi_analysis', {})
        
        return {
            "title": "Executive Summary",
            "situation": f"The Digital Operational Resilience Act (DORA) establishes comprehensive cybersecurity and operational resilience requirements for EU financial institutions. Current assessment reveals compliance gaps that expose {self.config.company_name} to regulatory penalties up to €{penalty_risk:,.0f}.",
            
            "opportunity": f"Strategic investment in DORA compliance will eliminate regulatory risk, enhance operational resilience, and strengthen competitive positioning. The proposed program delivers measurable financial returns while ensuring regulatory compliance.",
            
            "proposal": f"We recommend immediate investment of €{implementation_cost:,.0f} in a comprehensive DORA compliance program. This initiative will achieve full regulatory compliance while generating substantial operational benefits.",
            
            "financial_highlights": f"The investment delivers exceptional returns with {roi_data.get('roi_percentage', 0):.0f}% ROI, €{roi_data.get('npv', 0):,.0f} NPV over 5 years, and payback in {roi_data.get('payback_period_years', 0):.1f} years.",
            
            "recommendation": financial_data.get('investment_recommendation', {}).get('recommendation', 'RECOMMENDED'),
            
            "urgency": "DORA enforcement begins January 2025. Immediate action is required to avoid regulatory penalties and maintain operational authorization."
        }
    
    def generate_financial_analysis(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed financial analysis section"""
        
        penalty_analysis = financial_data.get('penalty_analysis', {})
        cost_analysis = financial_data.get('implementation_cost', {})
        roi_analysis = financial_data.get('advanced_roi_analysis', {})
        risk_metrics = financial_data.get('risk_metrics', {})
        
        return {
            "title": "Financial Analysis",
            "penalty_risk_assessment": {
                "maximum_exposure": f"€{penalty_analysis.get('maximum_penalty_risk', 0):,.0f}",
                "expected_annual_penalty": f"€{penalty_analysis.get('expected_annual_penalty', 0):,.0f}",
                "revenue_percentage": f"{penalty_analysis.get('penalty_as_revenue_percentage', 0):.1f}%",
                "regulatory_basis": "DORA Article 65 - Administrative penalties up to 2% of annual revenue"
            },
            "investment_analysis": {
                "total_investment": f"€{cost_analysis.get('total_cost', 0):,.0f}",
                "implementation_period": f"{cost_analysis.get('timeline_months', 12)} months",
                "complexity_level": cost_analysis.get('complexity_assessment', 'Medium'),
                "implementation_type": cost_analysis.get('implementation_type', 'Comprehensive')
            },
            "return_metrics": {
                "net_present_value": f"€{roi_analysis.get('npv', 0):,.0f}",
                "internal_rate_return": f"{roi_analysis.get('irr', 0):.1f}%",
                "return_on_investment": f"{roi_analysis.get('roi_percentage', 0):.0f}%",
                "payback_period": f"{roi_analysis.get('payback_period_years', 0):.1f} years",
                "profitability_index": f"{roi_analysis.get('profitability_index', 0):.2f}"
            },
            "risk_assessment": {
                "probability_success": f"{risk_metrics.get('probability_positive_npv', 0):.0%}",
                "worst_case_npv": f"€{risk_metrics.get('worst_case_npv', 0):,.0f}",
                "best_case_npv": f"€{risk_metrics.get('best_case_npv', 0):,.0f}",
                "financial_assumptions": risk_metrics.get('financial_assumptions', {})
            }
        }
    
    def generate_risk_assessment(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive risk assessment"""
        
        risks = [
            RiskItem(
                risk_id="REG-001",
                risk_name="Regulatory Non-Compliance",
                description="Failure to achieve DORA compliance by January 2025 deadline",
                probability="High",
                impact="High", 
                risk_level="Critical",
                mitigation_strategy="Immediate implementation of comprehensive compliance program",
                owner="Chief Risk Officer"
            ),
            RiskItem(
                risk_id="FIN-001",
                risk_name="Financial Penalties",
                description="Regulatory fines up to 2% of annual revenue for non-compliance",
                probability="Medium",
                impact="High",
                risk_level="High",
                mitigation_strategy="Full DORA compliance implementation with regular monitoring",
                owner="Chief Financial Officer"
            ),
            RiskItem(
                risk_id="OPS-001",
                risk_name="Operational Disruption",
                description="ICT incidents causing business disruption and customer impact",
                probability="Medium",
                impact="Medium",
                risk_level="Medium",
                mitigation_strategy="Enhanced ICT risk management and incident response capabilities",
                owner="Chief Operations Officer"
            ),
            RiskItem(
                risk_id="REP-001",
                risk_name="Reputational Damage",
                description="Public disclosure of compliance failures damaging market confidence",
                probability="Low",
                impact="High",
                risk_level="Medium",
                mitigation_strategy="Proactive compliance communication and stakeholder engagement",
                owner="Chief Executive Officer"
            ),
            RiskItem(
                risk_id="IMPL-001",
                risk_name="Implementation Delays",
                description="Project delays increasing costs and compliance risks",
                probability="Medium",
                impact="Medium",
                risk_level="Medium",
                mitigation_strategy="Robust project management with contingency planning",
                owner="Chief Information Officer"
            )
        ]
        
        return {
            "title": "Risk Assessment",
            "regulatory_risks": [r.to_dict() for r in risks if r.risk_id.startswith("REG")],
            "financial_risks": [r.to_dict() for r in risks if r.risk_id.startswith("FIN")],
            "operational_risks": [r.to_dict() for r in risks if r.risk_id.startswith("OPS")],
            "reputational_risks": [r.to_dict() for r in risks if r.risk_id.startswith("REP")],
            "implementation_risks": [r.to_dict() for r in risks if r.risk_id.startswith("IMPL")],
            "risk_matrix": self._generate_risk_matrix(risks)
        }
    
    def generate_implementation_plan(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed implementation plan"""
        
        cost_data = financial_data.get('implementation_cost', {})
        total_cost = cost_data.get('total_cost', 500000)
        timeline_months = cost_data.get('timeline_months', 12)
        
        phases = [
            ImplementationPhase(
                phase_number=1,
                phase_name="Assessment and Foundation",
                duration_months=2,
                cost_eur=Decimal(str(total_cost * 0.20)),
                activities=[
                    "Comprehensive gap analysis and risk assessment",
                    "Stakeholder alignment and governance structure",
                    "Project team formation and training",
                    "Vendor selection and procurement",
                    "Detailed implementation planning"
                ],
                deliverables=[
                    "Complete DORA gap assessment report",
                    "Project charter and governance framework",
                    "Implementation roadmap and timeline",
                    "Vendor contracts and service agreements",
                    "Risk register and mitigation plans"
                ],
                success_criteria=[
                    "100% of critical gaps identified and documented",
                    "Project governance approved by board",
                    "All key vendors contracted",
                    "Implementation team fully staffed"
                ],
                dependencies=["Board approval", "Budget allocation", "Resource assignment"]
            ),
            ImplementationPhase(
                phase_number=2,
                phase_name="Core Implementation",
                duration_months=max(6, timeline_months - 4),
                cost_eur=Decimal(str(total_cost * 0.60)),
                activities=[
                    "ICT governance framework implementation",
                    "Risk management system deployment",
                    "Incident management process implementation",
                    "Third-party risk management enhancement",
                    "Staff training and capability building"
                ],
                deliverables=[
                    "Operational ICT governance framework",
                    "Integrated risk management platform",
                    "24/7 incident response capability",
                    "Third-party risk monitoring system",
                    "Trained and certified staff"
                ],
                success_criteria=[
                    "All systems operational and tested",
                    "Staff training completion rate >95%",
                    "Incident response time <30 minutes",
                    "Third-party assessments completed"
                ],
                dependencies=["Phase 1 completion", "System procurement", "Staff availability"]
            ),
            ImplementationPhase(
                phase_number=3,
                phase_name="Testing and Validation",
                duration_months=2,
                cost_eur=Decimal(str(total_cost * 0.15)),
                activities=[
                    "Comprehensive system testing",
                    "DORA compliance validation",
                    "Regulatory readiness assessment",
                    "Documentation finalization",
                    "Stakeholder sign-off"
                ],
                deliverables=[
                    "System test results and certification",
                    "DORA compliance validation report",
                    "Regulatory submission package",
                    "Complete documentation suite",
                    "Executive compliance certification"
                ],
                success_criteria=[
                    "100% test cases passed",
                    "Full DORA compliance validated",
                    "Regulatory approval received",
                    "Board certification obtained"
                ],
                dependencies=["Phase 2 completion", "External validation", "Regulatory review"]
            ),
            ImplementationPhase(
                phase_number=4,
                phase_name="Go-Live and Optimization",
                duration_months=max(2, timeline_months - 10),
                cost_eur=Decimal(str(total_cost * 0.05)),
                activities=[
                    "Production deployment",
                    "Performance monitoring",
                    "Process optimization",
                    "Continuous improvement",
                    "Knowledge transfer"
                ],
                deliverables=[
                    "Live production environment",
                    "Performance dashboards",
                    "Optimized processes",
                    "Improvement roadmap",
                    "Knowledge base"
                ],
                success_criteria=[
                    "Zero critical incidents in first 30 days",
                    "Performance targets achieved",
                    "User satisfaction >90%",
                    "Compliance monitoring operational"
                ],
                dependencies=["Phase 3 completion", "Regulatory approval", "Operational readiness"]
            )
        ]
        
        return {
            "title": "Implementation Plan",
            "overview": f"The DORA compliance implementation will be delivered in {len(phases)} phases over {timeline_months} months, ensuring systematic deployment with minimal business disruption.",
            "phases": [phase.to_dict() for phase in phases],
            "timeline": self._generate_timeline(phases),
            "resource_requirements": self._generate_resource_requirements(phases),
            "success_metrics": self._generate_success_metrics(),
            "governance_structure": self._generate_governance_structure()
        }
    
    def generate_strategic_rationale(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic rationale section"""
        
        return {
            "title": "Strategic Rationale",
            "regulatory_imperative": {
                "description": "DORA establishes mandatory operational resilience requirements for all EU financial institutions",
                "implications": [
                    "Legal obligation to comply by January 2025",
                    "Regulatory supervision and enforcement powers",
                    "Potential operational authorization impact",
                    "Cross-border regulatory coordination"
                ]
            },
            "business_benefits": {
                "operational_excellence": [
                    "Enhanced ICT risk management capabilities",
                    "Improved incident response and recovery",
                    "Stronger third-party risk oversight",
                    "Automated compliance monitoring"
                ],
                "competitive_advantage": [
                    "Market confidence through compliance leadership",
                    "Enhanced customer trust and retention",
                    "Regulatory relationship strengthening",
                    "Industry best practice adoption"
                ],
                "risk_mitigation": [
                    "Reduced operational risk exposure",
                    "Enhanced cyber resilience capabilities",
                    "Improved business continuity planning",
                    "Stronger vendor risk management"
                ]
            },
            "strategic_alignment": {
                "digital_transformation": "DORA compliance supports broader digital transformation initiatives",
                "risk_management": "Enhanced enterprise risk management capabilities across all business lines",
                "operational_efficiency": "Process automation and optimization delivering ongoing cost savings",
                "stakeholder_value": "Demonstrable commitment to operational excellence and regulatory compliance"
            }
        }
    
    def _generate_risk_matrix(self, risks: List[RiskItem]) -> Dict[str, Any]:
        """Generate risk assessment matrix"""
        
        matrix = {
            "high_probability_high_impact": [],
            "high_probability_medium_impact": [],
            "high_probability_low_impact": [],
            "medium_probability_high_impact": [],
            "medium_probability_medium_impact": [],
            "medium_probability_low_impact": [],
            "low_probability_high_impact": [],
            "low_probability_medium_impact": [],
            "low_probability_low_impact": []
        }
        
        for risk in risks:
            key = f"{risk.probability.lower()}_probability_{risk.impact.lower()}_impact"
            if key in matrix:
                matrix[key].append(risk.to_dict())
        
        return matrix
    
    def _generate_timeline(self, phases: List[ImplementationPhase]) -> Dict[str, Any]:
        """Generate implementation timeline"""
        
        start_date = datetime.now() + timedelta(days=30)  # Start in 30 days
        current_date = start_date
        
        timeline = []
        for phase in phases:
            end_date = current_date + timedelta(days=phase.duration_months * 30)
            timeline.append({
                "phase": phase.phase_name,
                "start_date": current_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "duration_months": phase.duration_months,
                "cost": float(phase.cost_eur)
            })
            current_date = end_date
        
        return {
            "project_start": start_date.strftime("%Y-%m-%d"),
            "project_end": current_date.strftime("%Y-%m-%d"),
            "total_duration_months": sum(p.duration_months for p in phases),
            "phases": timeline
        }
    
    def _generate_resource_requirements(self, phases: List[ImplementationPhase]) -> Dict[str, Any]:
        """Generate resource requirements"""
        
        return {
            "project_team": {
                "project_manager": "1 FTE - Senior project manager with regulatory experience",
                "compliance_specialist": "1 FTE - DORA subject matter expert",
                "technical_architect": "1 FTE - Senior system architect",
                "risk_analyst": "0.5 FTE - Operational risk specialist",
                "business_analyst": "0.5 FTE - Process improvement specialist"
            },
            "external_resources": {
                "regulatory_consultant": "0.25 FTE - DORA implementation specialist",
                "technical_consultant": "0.5 FTE - System integration expert",
                "training_provider": "As needed - Staff training and certification"
            },
            "technology_resources": {
                "governance_platform": "ICT governance and risk management platform",
                "monitoring_tools": "Operational resilience monitoring systems",
                "testing_environment": "Dedicated testing and validation environment",
                "reporting_tools": "Regulatory reporting and dashboard tools"
            }
        }
    
    def _generate_success_metrics(self) -> Dict[str, List[str]]:
        """Generate success metrics"""
        
        return {
            "compliance_metrics": [
                "100% DORA requirement coverage",
                "Zero regulatory findings or penalties",
                "Successful regulatory validation",
                "Positive supervisory feedback"
            ],
            "operational_metrics": [
                "Incident response time <30 minutes",
                "System availability >99.9%",
                "Recovery time objective <4 hours",
                "Zero critical security incidents"
            ],
            "financial_metrics": [
                "Project delivery within budget",
                "ROI achievement within 24 months",
                "Cost savings realization >€50K annually",
                "Penalty avoidance >€1M annually"
            ],
            "stakeholder_metrics": [
                "Board satisfaction >90%",
                "Staff training completion >95%",
                "Customer satisfaction maintained",
                "Regulatory relationship strength"
            ]
        }
    
    def _generate_governance_structure(self) -> Dict[str, Any]:
        """Generate governance structure"""
        
        return {
            "steering_committee": {
                "chair": "Chief Executive Officer",
                "members": [
                    "Chief Information Officer",
                    "Chief Risk Officer", 
                    "Chief Financial Officer",
                    "Chief Operations Officer",
                    "Head of Compliance"
                ],
                "frequency": "Monthly",
                "responsibilities": [
                    "Strategic oversight and direction",
                    "Resource allocation decisions",
                    "Risk escalation and resolution",
                    "Regulatory communication"
                ]
            },
            "project_management_office": {
                "head": "Project Manager",
                "responsibilities": [
                    "Day-to-day project execution",
                    "Progress monitoring and reporting",
                    "Risk and issue management",
                    "Stakeholder communication"
                ]
            },
            "working_groups": {
                "technical_implementation": "System deployment and configuration",
                "process_design": "Business process optimization",
                "training_rollout": "Staff education and certification",
                "regulatory_liaison": "Supervisor communication and validation"
            }
        }

class BusinessCaseGenerator:
    """Main business case generator orchestrating document creation"""
    
    def __init__(self, config: Optional[BusinessCaseConfig] = None):
        self.config = config or BusinessCaseConfig()
        self.template = BusinessCaseTemplate(self.config)
        
    def generate_comprehensive_business_case(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete business case document"""
        
        logger.info("Generating comprehensive business case...")
        
        # Generate all sections
        sections = {
            BusinessCaseSection.EXECUTIVE_SUMMARY.value: self.template.generate_executive_summary(financial_data),
            BusinessCaseSection.FINANCIAL_ANALYSIS.value: self.template.generate_financial_analysis(financial_data),
            BusinessCaseSection.RISK_ASSESSMENT.value: self.template.generate_risk_assessment(financial_data),
            BusinessCaseSection.IMPLEMENTATION_PLAN.value: self.template.generate_implementation_plan(financial_data),
            BusinessCaseSection.STRATEGIC_RATIONALE.value: self.template.generate_strategic_rationale(financial_data)
        }
        
        # Generate document metadata
        metadata = {
            "document_title": self.config.document_title,
            "company_name": self.config.company_name,
            "author": self.config.author,
            "creation_date": datetime.now().strftime(self.config.date_format),
            "audience_level": self.config.audience_level.value,
            "confidentiality": self.config.confidentiality_level,
            "version": "1.0",
            "currency": self.config.currency
        }
        
        business_case = {
            "metadata": metadata,
            "sections": sections,
            "appendices": self._generate_appendices(financial_data) if self.config.include_appendices else {}
        }
        
        logger.info("Business case generation completed successfully")
        return business_case
    
    def _generate_appendices(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate appendices with detailed supporting data"""
        
        return {
            "appendix_a_financial_details": {
                "title": "Detailed Financial Analysis",
                "cash_flow_projections": financial_data.get('cash_flow_analysis', {}),
                "sensitivity_analysis": financial_data.get('sensitivity_analysis', {}),
                "assumptions": financial_data.get('risk_metrics', {}).get('financial_assumptions', {})
            },
            "appendix_b_regulatory_references": {
                "title": "DORA Regulatory References",
                "key_articles": [
                    "Article 4: ICT risk management framework",
                    "Article 11: ICT-related incident management",
                    "Article 25: Digital operational resilience testing",
                    "Article 28: ICT third-party risk management",
                    "Article 65: Administrative penalties"
                ],
                "implementation_deadlines": {
                    "dora_application": "January 17, 2025",
                    "testing_requirements": "January 17, 2026",
                    "third_party_oversight": "January 17, 2025"
                }
            },
            "appendix_c_implementation_details": {
                "title": "Implementation Technical Details",
                "system_requirements": financial_data.get('implementation_cost', {}).get('cost_breakdown', {}),
                "vendor_information": financial_data.get('implementation_cost', {}).get('vendor_quotes', []),
                "timeline_details": "Detailed project timeline and milestones"
            }
        }
    
    def export_to_format(self, business_case: Dict[str, Any], format_type: DocumentFormat) -> str:
        """Export business case to specified format"""
        
        logger.info(f"Exporting business case to {format_type.value} format")
        
        if format_type == DocumentFormat.JSON:
            return json.dumps(business_case, indent=2, default=str)
        
        elif format_type == DocumentFormat.HTML:
            return self._export_to_html(business_case)
        
        elif format_type == DocumentFormat.MARKDOWN:
            return self._export_to_markdown(business_case)
        
        elif format_type == DocumentFormat.TEXT:
            return self._export_to_text(business_case)
        
        elif format_type == DocumentFormat.CSV:
            return self._export_to_csv(business_case)
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _export_to_html(self, business_case: Dict[str, Any]) -> str:
        """Export business case to HTML format"""
        
        metadata = business_case['metadata']
        sections = business_case['sections']
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata['document_title']}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; line-height: 1.6; color: #333; }}
        .header {{ border-bottom: 3px solid #2c3e50; padding-bottom: 20px; margin-bottom: 30px; }}
        .company {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .title {{ font-size: 28px; font-weight: bold; margin: 10px 0; color: #34495e; }}
        .metadata {{ font-size: 14px; color: #666; margin-top: 10px; }}
        .section {{ margin: 30px 0; page-break-inside: avoid; }}
        .section-title {{ font-size: 22px; font-weight: bold; color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }}
        .subsection {{ margin: 20px 0; }}
        .subsection-title {{ font-size: 18px; font-weight: bold; color: #34495e; margin-bottom: 10px; }}
        .highlight {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0; }}
        .financial-metric {{ background-color: #e8f6f3; padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .risk-high {{ color: #e74c3c; font-weight: bold; }}
        .risk-medium {{ color: #f39c12; font-weight: bold; }}
        .risk-low {{ color: #27ae60; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .confidential {{ text-align: center; color: #e74c3c; font-weight: bold; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company">{metadata['company_name']}</div>
        <div class="title">{metadata['document_title']}</div>
        <div class="metadata">
            Author: {metadata['author']} | Date: {metadata['creation_date']} | Version: {metadata['version']}
        </div>
        <div class="confidential">{metadata['confidentiality']}</div>
    </div>
"""
        
        # Executive Summary
        exec_summary = sections['executive_summary']
        html_content += f"""
    <div class="section">
        <div class="section-title">{exec_summary['title']}</div>
        <div class="highlight">
            <strong>Situation:</strong> {exec_summary['situation']}
        </div>
        <div class="highlight">
            <strong>Opportunity:</strong> {exec_summary['opportunity']}
        </div>
        <div class="highlight">
            <strong>Proposal:</strong> {exec_summary['proposal']}
        </div>
        <div class="financial-metric">
            <strong>Financial Highlights:</strong> {exec_summary['financial_highlights']}
        </div>
        <div class="highlight">
            <strong>Recommendation:</strong> {exec_summary['recommendation']}
        </div>
        <div class="highlight">
            <strong>Urgency:</strong> {exec_summary['urgency']}
        </div>
    </div>
"""
        
        # Financial Analysis
        financial = sections['financial_analysis']
        html_content += f"""
    <div class="section">
        <div class="section-title">{financial['title']}</div>
        <div class="subsection">
            <div class="subsection-title">Penalty Risk Assessment</div>
            <table>
                <tr><th>Metric</th><th>Value</th><th>Description</th></tr>
                <tr><td>Maximum Exposure</td><td>{financial['penalty_risk_assessment']['maximum_exposure']}</td><td>Maximum regulatory penalty under DORA</td></tr>
                <tr><td>Expected Annual Penalty</td><td>{financial['penalty_risk_assessment']['expected_annual_penalty']}</td><td>Risk-adjusted expected penalty</td></tr>
                <tr><td>Revenue Percentage</td><td>{financial['penalty_risk_assessment']['revenue_percentage']}</td><td>Penalty as percentage of annual revenue</td></tr>
            </table>
        </div>
        <div class="subsection">
            <div class="subsection-title">Investment Analysis</div>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Total Investment</td><td>{financial['investment_analysis']['total_investment']}</td></tr>
                <tr><td>Implementation Period</td><td>{financial['investment_analysis']['implementation_period']}</td></tr>
                <tr><td>Complexity Level</td><td>{financial['investment_analysis']['complexity_level']}</td></tr>
            </table>
        </div>
        <div class="subsection">
            <div class="subsection-title">Return Metrics</div>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Net Present Value</td><td>{financial['return_metrics']['net_present_value']}</td></tr>
                <tr><td>Internal Rate of Return</td><td>{financial['return_metrics']['internal_rate_return']}</td></tr>
                <tr><td>Return on Investment</td><td>{financial['return_metrics']['return_on_investment']}</td></tr>
                <tr><td>Payback Period</td><td>{financial['return_metrics']['payback_period']}</td></tr>
            </table>
        </div>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        return html_content
    
    def _export_to_markdown(self, business_case: Dict[str, Any]) -> str:
        """Export business case to Markdown format"""
        
        metadata = business_case['metadata']
        sections = business_case['sections']
        
        markdown_content = f"""# {metadata['document_title']}

**Company:** {metadata['company_name']}  
**Author:** {metadata['author']}  
**Date:** {metadata['creation_date']}  
**Version:** {metadata['version']}  
**Confidentiality:** {metadata['confidentiality']}

---

"""
        
        # Executive Summary
        exec_summary = sections['executive_summary']
        markdown_content += f"""## {exec_summary['title']}

### Situation
{exec_summary['situation']}

### Opportunity
{exec_summary['opportunity']}

### Proposal
{exec_summary['proposal']}

### Financial Highlights
{exec_summary['financial_highlights']}

### Recommendation
**{exec_summary['recommendation']}**

### Urgency
{exec_summary['urgency']}

---

"""
        
        # Financial Analysis
        financial = sections['financial_analysis']
        markdown_content += f"""## {financial['title']}

### Penalty Risk Assessment

| Metric | Value | Description |
|--------|-------|-------------|
| Maximum Exposure | {financial['penalty_risk_assessment']['maximum_exposure']} | Maximum regulatory penalty under DORA |
| Expected Annual Penalty | {financial['penalty_risk_assessment']['expected_annual_penalty']} | Risk-adjusted expected penalty |
| Revenue Percentage | {financial['penalty_risk_assessment']['revenue_percentage']} | Penalty as percentage of annual revenue |

### Investment Analysis

| Metric | Value |
|--------|-------|
| Total Investment | {financial['investment_analysis']['total_investment']} |
| Implementation Period | {financial['investment_analysis']['implementation_period']} |
| Complexity Level | {financial['investment_analysis']['complexity_level']} |

### Return Metrics

| Metric | Value |
|--------|-------|
| Net Present Value | {financial['return_metrics']['net_present_value']} |
| Internal Rate of Return | {financial['return_metrics']['internal_rate_return']} |
| Return on Investment | {financial['return_metrics']['return_on_investment']} |
| Payback Period | {financial['return_metrics']['payback_period']} |

---

"""
        
        return markdown_content
    
    def _export_to_text(self, business_case: Dict[str, Any]) -> str:
        """Export business case to plain text format"""
        
        metadata = business_case['metadata']
        sections = business_case['sections']
        
        text_content = f"""{metadata['document_title']}
{'=' * len(metadata['document_title'])}

Company: {metadata['company_name']}
Author: {metadata['author']}
Date: {metadata['creation_date']}
Version: {metadata['version']}
Confidentiality: {metadata['confidentiality']}

"""
        
        # Executive Summary
        exec_summary = sections['executive_summary']
        text_content += f"""{exec_summary['title']}
{'-' * len(exec_summary['title'])}

Situation:
{exec_summary['situation']}

Opportunity:
{exec_summary['opportunity']}

Proposal:
{exec_summary['proposal']}

Financial Highlights:
{exec_summary['financial_highlights']}

Recommendation:
{exec_summary['recommendation']}

Urgency:
{exec_summary['urgency']}

"""
        
        return text_content
    
    def _export_to_csv(self, business_case: Dict[str, Any]) -> str:
        """Export key metrics to CSV format"""
        
        financial = business_case['sections']['financial_analysis']
        
        csv_content = "Metric,Value,Category\n"
        
        # Penalty risk metrics
        penalty_data = financial['penalty_risk_assessment']
        csv_content += f"Maximum Exposure,{penalty_data['maximum_exposure']},Penalty Risk\n"
        csv_content += f"Expected Annual Penalty,{penalty_data['expected_annual_penalty']},Penalty Risk\n"
        csv_content += f"Revenue Percentage,{penalty_data['revenue_percentage']},Penalty Risk\n"
        
        # Investment metrics
        investment_data = financial['investment_analysis']
        csv_content += f"Total Investment,{investment_data['total_investment']},Investment\n"
        csv_content += f"Implementation Period,{investment_data['implementation_period']},Investment\n"
        
        # Return metrics
        return_data = financial['return_metrics']
        csv_content += f"Net Present Value,{return_data['net_present_value']},Returns\n"
        csv_content += f"Internal Rate of Return,{return_data['internal_rate_return']},Returns\n"
        csv_content += f"Return on Investment,{return_data['return_on_investment']},Returns\n"
        csv_content += f"Payback Period,{return_data['payback_period']},Returns\n"
        
        return csv_content
    
    def save_business_case(self, business_case: Dict[str, Any], 
                          output_dir: str = "output", 
                          formats: List[DocumentFormat] = None) -> Dict[str, str]:
        """Save business case in multiple formats"""
        
        if formats is None:
            formats = [DocumentFormat.HTML, DocumentFormat.MARKDOWN, DocumentFormat.JSON]
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        base_filename = "dora_business_case"
        
        for format_type in formats:
            content = self.export_to_format(business_case, format_type)
            filename = f"{base_filename}.{format_type.value}"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files[format_type.value] = filepath
            logger.info(f"Business case saved to {filepath}")
        
        return saved_files

def demonstrate_business_case_generator():
    """Demonstrate the Business Case Generator capabilities"""
    
    print("📋 DORA Compliance Business Case Generator")
    print("=" * 50)
    
    # Sample financial data (from ROI analysis)
    sample_financial_data = {
        "penalty_analysis": {
            "maximum_penalty_risk": 10000000,
            "expected_annual_penalty": 3000000,
            "penalty_as_revenue_percentage": 2.0
        },
        "implementation_cost": {
            "total_cost": 399000,
            "timeline_months": 7,
            "complexity_assessment": "moderate",
            "implementation_type": "governance_framework"
        },
        "advanced_roi_analysis": {
            "roi_percentage": 2431.3,
            "npv": 5480424,
            "irr": 64.9,
            "payback_period_years": 6.06,
            "profitability_index": 14.74
        },
        "risk_metrics": {
            "probability_positive_npv": 1.0,
            "worst_case_npv": 5655235,
            "best_case_npv": 9628937,
            "financial_assumptions": {
                "discount_rate": 0.08,
                "analysis_period_years": 5,
                "currency": "EUR"
            }
        },
        "investment_recommendation": {
            "recommendation": "STRONGLY RECOMMENDED",
            "reason": "Exceptional ROI with rapid payback"
        }
    }
    
    # Create configuration
    config = BusinessCaseConfig(
        company_name="European Financial Services Ltd",
        document_title="DORA Compliance Investment Business Case",
        author="Chief Information Officer",
        audience_level=AudienceLevel.CXO
    )
    
    # Generate business case
    generator = BusinessCaseGenerator(config)
    business_case = generator.generate_comprehensive_business_case(sample_financial_data)
    
    print(f"📊 Business Case Generated Successfully!")
    print(f"   • Company: {business_case['metadata']['company_name']}")
    print(f"   • Document: {business_case['metadata']['document_title']}")
    print(f"   • Author: {business_case['metadata']['author']}")
    print(f"   • Date: {business_case['metadata']['creation_date']}")
    
    print(f"\n📋 Document Sections:")
    for section_key in business_case['sections']:
        section_title = business_case['sections'][section_key].get('title', section_key.replace('_', ' ').title())
        print(f"   • {section_title}")
    
    # Generate executive summary preview
    exec_summary = business_case['sections']['executive_summary']
    print(f"\n🎯 Executive Summary Preview:")
    print(f"   • Situation: {exec_summary['situation'][:100]}...")
    print(f"   • Recommendation: {exec_summary['recommendation']}")
    
    # Display financial highlights
    financial = business_case['sections']['financial_analysis']
    print(f"\n💰 Financial Highlights:")
    print(f"   • Maximum Penalty Risk: {financial['penalty_risk_assessment']['maximum_exposure']}")
    print(f"   • Investment Required: {financial['investment_analysis']['total_investment']}")
    print(f"   • NPV: {financial['return_metrics']['net_present_value']}")
    print(f"   • ROI: {financial['return_metrics']['return_on_investment']}")
    
    # Export samples
    print(f"\n📄 Export Capabilities:")
    try:
        html_preview = generator.export_to_format(business_case, DocumentFormat.HTML)
        print(f"   • HTML: {len(html_preview)} characters generated")
        
        markdown_preview = generator.export_to_format(business_case, DocumentFormat.MARKDOWN)
        print(f"   • Markdown: {len(markdown_preview)} characters generated")
        
        json_preview = generator.export_to_format(business_case, DocumentFormat.JSON)
        print(f"   • JSON: {len(json_preview)} characters generated")
        
        csv_preview = generator.export_to_format(business_case, DocumentFormat.CSV)
        print(f"   • CSV: {len(csv_preview.split('\\n'))} rows generated")
        
    except Exception as e:
        print(f"   • Export Error: {str(e)}")
    
    print(f"\n✅ Business Case Generator Demonstration Complete!")

if __name__ == "__main__":
    demonstrate_business_case_generator() 