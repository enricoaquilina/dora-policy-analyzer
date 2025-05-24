#!/usr/bin/env python3
"""
DORA Compliance Executive Reporting System

This module generates comprehensive, executive-ready reports combining financial analysis,
business cases, visualizations, and strategic recommendations for DORA compliance
investments. It integrates with all Risk Calculator Agent components to produce
professional reports suitable for C-suite and board consumption.

Author: DORA Compliance System
Created: 2025-05-24
"""

import json
import logging
import os
import base64
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path

# Import our components
try:
    # Try relative imports first (for module usage)
    from .business_case_generator import BusinessCaseGenerator, BusinessCaseConfig, AudienceLevel
    from .financial_visualization_module import FinancialVisualizationModule, VisualizationLevel, ExportFormat
    from .risk_calculator_agent import calculate_financial_impact
except ImportError:
    # Fall back to direct imports (for standalone execution)
    from business_case_generator import BusinessCaseGenerator, BusinessCaseConfig, AudienceLevel
    from financial_visualization_module import FinancialVisualizationModule, VisualizationLevel, ExportFormat
    from risk_calculator_agent import calculate_financial_impact

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportType(Enum):
    """Types of executive reports"""
    BOARD_PRESENTATION = "board_presentation"
    CIO_BRIEFING = "cio_briefing"
    CFO_ANALYSIS = "cfo_analysis"
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_BUSINESS_CASE = "detailed_business_case"
    INVESTMENT_PROPOSAL = "investment_proposal"

class ReportFormat(Enum):
    """Output formats for reports"""
    HTML = "html"
    PDF = "pdf"
    POWERPOINT = "powerpoint"
    WORD = "word"
    JSON = "json"
    INTERACTIVE = "interactive"

class ApprovalStatus(Enum):
    """Report approval workflow status"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"

@dataclass
class ReportConfig:
    """Configuration for executive report generation"""
    report_type: ReportType
    audience_level: AudienceLevel = AudienceLevel.CXO
    include_charts: bool = True
    include_appendices: bool = True
    include_executive_summary: bool = True
    include_financial_details: bool = True
    include_implementation_plan: bool = True
    include_risk_assessment: bool = True
    branding_template: str = "corporate"
    confidentiality_level: str = "Confidential"
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['report_type'] = self.report_type.value
        result['audience_level'] = self.audience_level.value
        return result

@dataclass
class ReportMetadata:
    """Metadata for report tracking and versioning"""
    report_id: str
    title: str
    author: str
    company: str
    creation_date: datetime
    last_modified: datetime
    version: str
    approval_status: ApprovalStatus
    approver: Optional[str] = None
    approval_date: Optional[datetime] = None
    distribution_list: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['creation_date'] = self.creation_date.isoformat()
        result['last_modified'] = self.last_modified.isoformat()
        result['approval_status'] = self.approval_status.value
        if self.approval_date:
            result['approval_date'] = self.approval_date.isoformat()
        return result

class ReportTemplate:
    """Base template for executive reports"""
    
    def __init__(self, config: ReportConfig):
        self.config = config
        
    def generate_board_presentation_template(self) -> Dict[str, Any]:
        """Generate board presentation template structure"""
        return {
            "slide_structure": [
                {"slide": 1, "title": "Executive Summary", "content_type": "summary", "duration": "2 minutes"},
                {"slide": 2, "title": "DORA Compliance Imperative", "content_type": "regulatory_overview", "duration": "3 minutes"},
                {"slide": 3, "title": "Financial Impact Analysis", "content_type": "financial_summary", "duration": "4 minutes"},
                {"slide": 4, "title": "Investment Recommendation", "content_type": "recommendation", "duration": "2 minutes"},
                {"slide": 5, "title": "Implementation Overview", "content_type": "implementation_summary", "duration": "2 minutes"},
                {"slide": 6, "title": "Risk Assessment", "content_type": "risk_matrix", "duration": "2 minutes"},
                {"slide": 7, "title": "Next Steps & Timeline", "content_type": "action_plan", "duration": "3 minutes"},
                {"slide": 8, "title": "Questions & Discussion", "content_type": "discussion", "duration": "10 minutes"}
            ],
            "total_duration": "28 minutes",
            "presentation_style": "executive",
            "visual_emphasis": "high_level_metrics",
            "detail_level": "strategic"
        }
    
    def generate_cio_briefing_template(self) -> Dict[str, Any]:
        """Generate CIO briefing template structure"""
        return {
            "sections": [
                {"section": "Executive Summary", "pages": 1, "focus": "strategic_overview"},
                {"section": "Technical Architecture Impact", "pages": 2, "focus": "system_implications"},
                {"section": "Implementation Roadmap", "pages": 3, "focus": "detailed_planning"},
                {"section": "Resource Requirements", "pages": 2, "focus": "technical_resources"},
                {"section": "Risk Mitigation Strategy", "pages": 2, "focus": "technical_risks"},
                {"section": "Budget Justification", "pages": 2, "focus": "financial_analysis"},
                {"section": "Success Metrics", "pages": 1, "focus": "kpi_definition"},
                {"section": "Appendices", "pages": 5, "focus": "supporting_documentation"}
            ],
            "total_pages": 18,
            "document_style": "technical_executive",
            "detail_level": "comprehensive"
        }
    
    def generate_cfo_analysis_template(self) -> Dict[str, Any]:
        """Generate CFO analysis template structure"""
        return {
            "sections": [
                {"section": "Financial Executive Summary", "pages": 1, "focus": "financial_highlights"},
                {"section": "Investment Analysis", "pages": 3, "focus": "cost_benefit_analysis"},
                {"section": "Risk Financial Impact", "pages": 2, "focus": "penalty_exposure"},
                {"section": "ROI Projections", "pages": 3, "focus": "return_analysis"},
                {"section": "Cash Flow Analysis", "pages": 2, "focus": "cash_flow_projections"},
                {"section": "Sensitivity Analysis", "pages": 2, "focus": "scenario_modeling"},
                {"section": "Budget Planning", "pages": 2, "focus": "budget_allocation"},
                {"section": "Financial Controls", "pages": 1, "focus": "governance_controls"}
            ],
            "total_pages": 16,
            "document_style": "financial_analytical",
            "detail_level": "detailed_financial"
        }

class ExecutiveReportGenerator:
    """Main class for generating executive reports"""
    
    def __init__(self, config: ReportConfig):
        self.config = config
        self.template = ReportTemplate(config)
        self.business_case_generator = BusinessCaseGenerator(
            BusinessCaseConfig(
                audience_level=config.audience_level,
                include_appendices=config.include_appendices
            )
        )
        self.visualization_module = FinancialVisualizationModule(
            VisualizationLevel.EXECUTIVE if config.audience_level == AudienceLevel.BOARD 
            else VisualizationLevel.ANALYTICAL
        )
        
    def generate_comprehensive_report(self, gap_assessment_data: Dict[str, Any], 
                                    company_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive executive report"""
        
        logger.info(f"Generating {self.config.report_type.value} report...")
        
        # 1. Generate financial impact analysis
        financial_analysis = calculate_financial_impact(gap_assessment_data)
        
        # 2. Generate business case
        business_case = self.business_case_generator.generate_comprehensive_business_case(financial_analysis)
        
        # 3. Generate visualizations
        visualizations = self.visualization_module.generate_comprehensive_visualizations(financial_analysis)
        
        # 4. Generate report content based on type
        if self.config.report_type == ReportType.BOARD_PRESENTATION:
            report_content = self._generate_board_presentation(financial_analysis, business_case, visualizations)
        elif self.config.report_type == ReportType.CIO_BRIEFING:
            report_content = self._generate_cio_briefing(financial_analysis, business_case, visualizations)
        elif self.config.report_type == ReportType.CFO_ANALYSIS:
            report_content = self._generate_cfo_analysis(financial_analysis, business_case, visualizations)
        else:
            report_content = self._generate_standard_report(financial_analysis, business_case, visualizations)
        
        # 5. Generate report metadata
        metadata = ReportMetadata(
            report_id=f"DORA-{self.config.report_type.value}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            title=f"DORA Compliance {self.config.report_type.value.replace('_', ' ').title()}",
            author="Chief Information Officer",
            company=company_info.get('name', 'Financial Institution') if company_info else 'Financial Institution',
            creation_date=datetime.now(),
            last_modified=datetime.now(),
            version=self.config.version,
            approval_status=ApprovalStatus.DRAFT
        )
        
        # 6. Assemble final report
        executive_report = {
            "metadata": metadata.to_dict(),
            "config": self.config.to_dict(),
            "content": report_content,
            "financial_analysis": financial_analysis,
            "business_case": business_case,
            "visualizations": visualizations,
            "executive_summary": self._generate_executive_summary(financial_analysis),
            "recommendations": self._generate_recommendations(financial_analysis),
            "appendices": self._generate_report_appendices(financial_analysis, business_case)
        }
        
        logger.info(f"Report generation completed: {metadata.report_id}")
        return executive_report
    
    def _generate_board_presentation(self, financial_analysis: Dict[str, Any], 
                                   business_case: Dict[str, Any], 
                                   visualizations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate board presentation content"""
        
        template = self.template.generate_board_presentation_template()
        
        # Extract key metrics for board presentation
        penalty_risk = financial_analysis.get('penalty_analysis', {}).get('maximum_penalty_risk', 0)
        implementation_cost = financial_analysis.get('implementation_cost', {}).get('total_cost', 0)
        roi_data = financial_analysis.get('advanced_roi_analysis', {})
        
        slides = []
        
        # Slide 1: Executive Summary
        slides.append({
            "slide_number": 1,
            "title": "DORA Compliance Investment Proposal",
            "content": {
                "situation": f"Regulatory exposure up to €{penalty_risk:,.0f}",
                "solution": f"€{implementation_cost:,.0f} compliance investment",
                "outcome": f"{roi_data.get('roi_percentage', 0):.0f}% ROI with {roi_data.get('payback_period_years', 0):.1f} year payback",
                "recommendation": financial_analysis.get('investment_recommendation', {}).get('recommendation', 'RECOMMENDED')
            },
            "speaker_notes": "Board decision required for DORA compliance investment to avoid regulatory penalties and ensure operational authorization."
        })
        
        # Slide 2: DORA Compliance Imperative
        slides.append({
            "slide_number": 2,
            "title": "DORA Regulatory Imperative",
            "content": {
                "regulation_overview": "Digital Operational Resilience Act (DORA) mandates comprehensive cybersecurity and operational resilience requirements",
                "compliance_deadline": "January 17, 2025",
                "penalty_structure": "Up to 2% of annual revenue for non-compliance",
                "business_impact": "Operational authorization at risk without compliance"
            },
            "speaker_notes": "DORA is not optional - it's a legal requirement with severe financial and operational consequences."
        })
        
        # Continue with remaining slides...
        
        return {
            "template": template,
            "slides": slides,
            "presentation_summary": {
                "total_slides": len(template['slide_structure']),
                "estimated_duration": template['total_duration'],
                "key_message": "Immediate DORA compliance investment required to avoid regulatory penalties and ensure business continuity",
                "call_to_action": "Approve €{:,.0f} investment for DORA compliance implementation".format(implementation_cost)
            }
        }
    
    def _generate_cio_briefing(self, financial_analysis: Dict[str, Any], 
                             business_case: Dict[str, Any], 
                             visualizations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate CIO briefing content"""
        
        template = self.template.generate_cio_briefing_template()
        
        return {
            "template": template,
            "technical_overview": {
                "system_architecture_impact": "Comprehensive updates required across ICT infrastructure",
                "integration_requirements": "API integrations with monitoring, risk management, and reporting systems",
                "resource_allocation": "Dedicated team of 6 FTE for 7-month implementation",
                "technology_stack": "Risk management platform, monitoring tools, reporting systems"
            },
            "implementation_roadmap": business_case['sections']['implementation_plan'],
            "technical_risks": self._extract_technical_risks(financial_analysis),
            "success_metrics": self._define_technical_success_metrics()
        }
    
    def _generate_cfo_analysis(self, financial_analysis: Dict[str, Any], 
                             business_case: Dict[str, Any], 
                             visualizations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate CFO financial analysis content"""
        
        template = self.template.generate_cfo_analysis_template()
        
        return {
            "template": template,
            "financial_highlights": {
                "investment_required": financial_analysis.get('implementation_cost', {}).get('total_cost', 0),
                "penalty_exposure": financial_analysis.get('penalty_analysis', {}).get('maximum_penalty_risk', 0),
                "net_present_value": financial_analysis.get('advanced_roi_analysis', {}).get('npv', 0),
                "internal_rate_return": financial_analysis.get('advanced_roi_analysis', {}).get('irr', 0),
                "payback_period": financial_analysis.get('advanced_roi_analysis', {}).get('payback_period_years', 0)
            },
            "budget_breakdown": financial_analysis.get('implementation_cost', {}).get('cost_breakdown', {}),
            "cash_flow_projections": financial_analysis.get('cash_flow_analysis', {}),
            "sensitivity_analysis": financial_analysis.get('sensitivity_analysis', {}),
            "financial_controls": self._define_financial_controls(),
            "budget_monitoring": self._define_budget_monitoring_framework()
        }
    
    def _generate_standard_report(self, financial_analysis: Dict[str, Any], 
                                business_case: Dict[str, Any], 
                                visualizations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate standard executive report content"""
        
        return {
            "executive_overview": business_case['sections']['executive_summary'],
            "financial_analysis": business_case['sections']['financial_analysis'],
            "implementation_plan": business_case['sections']['implementation_plan'],
            "risk_assessment": business_case['sections']['risk_assessment'],
            "strategic_rationale": business_case['sections']['strategic_rationale'],
            "visualizations_summary": {
                "charts_included": len(visualizations['individual_charts']),
                "dashboard_type": visualizations['dashboard']['summary']['dashboard_type'],
                "key_metrics": visualizations['dashboard']['key_metrics']
            }
        }
    
    def _generate_executive_summary(self, financial_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate executive summary for all report types"""
        
        penalty_risk = financial_analysis.get('penalty_analysis', {}).get('maximum_penalty_risk', 0)
        implementation_cost = financial_analysis.get('implementation_cost', {}).get('total_cost', 0)
        roi_data = financial_analysis.get('advanced_roi_analysis', {})
        
        return {
            "situation": f"DORA compliance gaps expose the organization to regulatory penalties up to €{penalty_risk:,.0f} ({financial_analysis.get('penalty_analysis', {}).get('penalty_as_revenue_percentage', 0):.1f}% of annual revenue).",
            
            "opportunity": f"Strategic investment of €{implementation_cost:,.0f} will eliminate regulatory risk while delivering {roi_data.get('roi_percentage', 0):.0f}% ROI over 5 years.",
            
            "recommendation": financial_analysis.get('investment_recommendation', {}).get('recommendation', 'RECOMMENDED'),
            
            "urgency": "DORA enforcement begins January 2025. Immediate action required to maintain operational authorization and avoid penalties.",
            
            "next_steps": f"Secure board approval for €{implementation_cost:,.0f} investment and initiate {financial_analysis.get('implementation_cost', {}).get('timeline_months', 12)}-month implementation program."
        }
    
    def _generate_recommendations(self, financial_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Primary recommendation
        recommendations.append({
            "priority": "Immediate",
            "action": "Approve DORA compliance investment",
            "rationale": f"Avoid €{financial_analysis.get('penalty_analysis', {}).get('maximum_penalty_risk', 0):,.0f} penalty risk",
            "timeline": "Board decision required within 30 days",
            "owner": "Chief Executive Officer"
        })
        
        # Implementation recommendation
        recommendations.append({
            "priority": "High",
            "action": "Establish project governance",
            "rationale": "Ensure successful implementation and stakeholder alignment",
            "timeline": "Within 2 weeks of approval",
            "owner": "Chief Information Officer"
        })
        
        # Resource recommendation
        recommendations.append({
            "priority": "High",
            "action": "Secure implementation resources",
            "rationale": "Dedicated team required for timely delivery",
            "timeline": "Within 4 weeks of approval",
            "owner": "Chief Human Resources Officer"
        })
        
        return recommendations
    
    def _generate_report_appendices(self, financial_analysis: Dict[str, Any], 
                                  business_case: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive appendices"""
        
        return {
            "appendix_a_financial_details": {
                "title": "Detailed Financial Analysis",
                "content": financial_analysis.get('cash_flow_analysis', {}),
                "sensitivity_analysis": financial_analysis.get('sensitivity_analysis', {})
            },
            "appendix_b_implementation_details": {
                "title": "Implementation Plan Details",
                "content": business_case['sections']['implementation_plan']
            },
            "appendix_c_regulatory_references": {
                "title": "DORA Regulatory References",
                "key_articles": [
                    "Article 4: ICT risk management framework",
                    "Article 11: ICT-related incident management", 
                    "Article 25: Digital operational resilience testing",
                    "Article 28: ICT third-party risk management",
                    "Article 65: Administrative penalties"
                ]
            },
            "appendix_d_assumptions": {
                "title": "Financial Model Assumptions",
                "content": financial_analysis.get('risk_metrics', {}).get('financial_assumptions', {})
            }
        }
    
    def _extract_technical_risks(self, financial_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract technical risks for CIO briefing"""
        
        return [
            {
                "risk": "System Integration Complexity",
                "description": "Multiple system integrations required for compliance monitoring",
                "mitigation": "Phased implementation approach with dedicated integration team",
                "impact": "Medium"
            },
            {
                "risk": "Resource Availability",
                "description": "Competition for skilled technical resources",
                "mitigation": "Early resource allocation and external consultant engagement",
                "impact": "High"
            },
            {
                "risk": "Timeline Constraints",
                "description": "DORA deadline creates implementation pressure",
                "mitigation": "Parallel workstreams and agile delivery methodology",
                "impact": "High"
            }
        ]
    
    def _define_technical_success_metrics(self) -> Dict[str, List[str]]:
        """Define technical success metrics for CIO briefing"""
        
        return {
            "compliance_metrics": [
                "100% DORA requirement coverage achieved",
                "Zero critical compliance gaps remaining",
                "Successful regulatory validation completed"
            ],
            "operational_metrics": [
                "System availability >99.9%",
                "Incident response time <30 minutes",
                "Recovery time objective <4 hours"
            ],
            "project_metrics": [
                "On-time delivery within 7 months",
                "Budget variance <5%",
                "Stakeholder satisfaction >90%"
            ]
        }
    
    def _define_financial_controls(self) -> Dict[str, Any]:
        """Define financial controls for CFO analysis"""
        
        return {
            "budget_controls": {
                "approval_thresholds": "€10K CIO, €50K CFO, €100K+ Board",
                "change_control": "Formal change request process for budget modifications",
                "reporting_frequency": "Monthly budget vs actual reporting"
            },
            "vendor_management": {
                "procurement_process": "Competitive bidding for major vendors",
                "contract_terms": "Fixed-price contracts with penalty clauses",
                "performance_monitoring": "Monthly vendor performance reviews"
            },
            "cost_allocation": {
                "charge_back_model": "Costs allocated to business units based on usage",
                "capital_vs_opex": "Clear categorization for accounting treatment",
                "depreciation_schedule": "3-year depreciation for technology assets"
            }
        }
    
    def _define_budget_monitoring_framework(self) -> Dict[str, Any]:
        """Define budget monitoring framework"""
        
        return {
            "monitoring_frequency": {
                "daily": "Expenditure tracking and approval workflow",
                "weekly": "Budget consumption analysis and forecasting",
                "monthly": "Formal budget review and variance analysis",
                "quarterly": "Board reporting and forecast updates"
            },
            "key_performance_indicators": [
                "Budget consumption rate vs timeline",
                "Cost per milestone delivery",
                "Vendor cost performance vs contract",
                "ROI tracking vs projections"
            ],
            "variance_thresholds": {
                "green": "<5% variance from budget",
                "amber": "5-10% variance requiring explanation",
                "red": ">10% variance requiring corrective action"
            }
        }

class ExecutiveReportingSystem:
    """Main system orchestrating executive report generation"""
    
    def __init__(self):
        self.reports_generated = []
        
    def generate_report(self, report_type: ReportType, 
                       gap_assessment_data: Dict[str, Any],
                       audience_level: AudienceLevel = AudienceLevel.CXO,
                       company_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate executive report of specified type"""
        
        config = ReportConfig(
            report_type=report_type,
            audience_level=audience_level,
            include_charts=True,
            include_appendices=True
        )
        
        generator = ExecutiveReportGenerator(config)
        report = generator.generate_comprehensive_report(gap_assessment_data, company_info)
        
        # Track generated report
        self.reports_generated.append({
            "report_id": report['metadata']['report_id'],
            "report_type": report_type.value,
            "generation_time": datetime.now().isoformat(),
            "audience_level": audience_level.value
        })
        
        return report
    
    def generate_multiple_reports(self, gap_assessment_data: Dict[str, Any],
                                company_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate multiple report types for different audiences"""
        
        reports = {}
        
        # Generate board presentation
        reports['board_presentation'] = self.generate_report(
            ReportType.BOARD_PRESENTATION, 
            gap_assessment_data, 
            AudienceLevel.BOARD,
            company_info
        )
        
        # Generate CIO briefing
        reports['cio_briefing'] = self.generate_report(
            ReportType.CIO_BRIEFING,
            gap_assessment_data,
            AudienceLevel.CXO,
            company_info
        )
        
        # Generate CFO analysis
        reports['cfo_analysis'] = self.generate_report(
            ReportType.CFO_ANALYSIS,
            gap_assessment_data,
            AudienceLevel.CXO,
            company_info
        )
        
        return {
            "reports": reports,
            "generation_summary": {
                "total_reports": len(reports),
                "generation_timestamp": datetime.now().isoformat(),
                "report_types": list(reports.keys())
            }
        }
    
    def export_report(self, report: Dict[str, Any], 
                     export_format: ReportFormat = ReportFormat.HTML) -> str:
        """Export report to specified format"""
        
        if export_format == ReportFormat.HTML:
            return self._export_to_html(report)
        elif export_format == ReportFormat.JSON:
            return json.dumps(report, indent=2, default=str)
        else:
            raise ValueError(f"Export format {export_format.value} not yet implemented")
    
    def _export_to_html(self, report: Dict[str, Any]) -> str:
        """Export report to HTML format"""
        
        metadata = report['metadata']
        executive_summary = report['executive_summary']
        recommendations = report['recommendations']
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata['title']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 40px;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }}
        .company {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .title {{
            font-size: 32px;
            font-weight: bold;
            color: #34495e;
            margin-bottom: 20px;
        }}
        .metadata {{
            font-size: 14px;
            color: #666;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .section {{
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section-title {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 20px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .executive-item {{
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            border-radius: 0 5px 5px 0;
        }}
        .executive-label {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .recommendation {{
            background: #e8f6f3;
            border-left: 4px solid #27ae60;
            padding: 20px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
        }}
        .recommendation.high {{
            background: #fff3cd;
            border-left-color: #ffc107;
        }}
        .recommendation.immediate {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #dee2e6;
        }}
        .metric-value {{
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
        }}
        .confidential {{
            text-align: center;
            color: #dc3545;
            font-weight: bold;
            margin: 20px 0;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company">{metadata['company']}</div>
        <div class="title">{metadata['title']}</div>
        <div class="confidential">CONFIDENTIAL</div>
        <div class="metadata">
            <div><strong>Report ID:</strong> {metadata['report_id']}</div>
            <div><strong>Author:</strong> {metadata['author']}</div>
            <div><strong>Date:</strong> {datetime.fromisoformat(metadata['creation_date']).strftime('%B %d, %Y')}</div>
            <div><strong>Version:</strong> {metadata['version']}</div>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">Executive Summary</div>
        <div class="executive-item">
            <div class="executive-label">Situation</div>
            <div>{executive_summary['situation']}</div>
        </div>
        <div class="executive-item">
            <div class="executive-label">Opportunity</div>
            <div>{executive_summary['opportunity']}</div>
        </div>
        <div class="executive-item">
            <div class="executive-label">Recommendation</div>
            <div><strong>{executive_summary['recommendation']}</strong></div>
        </div>
        <div class="executive-item">
            <div class="executive-label">Urgency</div>
            <div>{executive_summary['urgency']}</div>
        </div>
        <div class="executive-item">
            <div class="executive-label">Next Steps</div>
            <div>{executive_summary['next_steps']}</div>
        </div>
    </div>
"""
        
        # Add key metrics if available
        if 'visualizations' in report and 'key_metrics' in report['visualizations']['dashboard']:
            key_metrics = report['visualizations']['dashboard']['key_metrics']
            html_content += f"""
    <div class="section">
        <div class="section-title">Key Financial Metrics</div>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{key_metrics['max_penalty_risk']}</div>
                <div class="metric-label">Maximum Penalty Risk</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{key_metrics['implementation_cost']}</div>
                <div class="metric-label">Implementation Investment</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{key_metrics['roi_percentage']}</div>
                <div class="metric-label">Return on Investment</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{key_metrics['npv']}</div>
                <div class="metric-label">Net Present Value</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{key_metrics['payback_period']}</div>
                <div class="metric-label">Payback Period</div>
            </div>
        </div>
    </div>
"""
        
        # Add recommendations
        html_content += f"""
    <div class="section">
        <div class="section-title">Recommendations</div>
"""
        
        for rec in recommendations:
            priority_class = rec['priority'].lower()
            html_content += f"""
        <div class="recommendation {priority_class}">
            <strong>{rec['priority']} Priority:</strong> {rec['action']}<br>
            <strong>Rationale:</strong> {rec['rationale']}<br>
            <strong>Timeline:</strong> {rec['timeline']}<br>
            <strong>Owner:</strong> {rec['owner']}
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        return html_content
    
    def save_report(self, report: Dict[str, Any], 
                   output_dir: str = "output/reports",
                   formats: List[ReportFormat] = None) -> Dict[str, str]:
        """Save report in multiple formats"""
        
        if formats is None:
            formats = [ReportFormat.HTML, ReportFormat.JSON]
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        report_id = report['metadata']['report_id']
        
        for format_type in formats:
            if format_type == ReportFormat.HTML:
                content = self.export_report(report, ReportFormat.HTML)
                filepath = os.path.join(output_dir, f"{report_id}.html")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                saved_files['html'] = filepath
                
            elif format_type == ReportFormat.JSON:
                content = self.export_report(report, ReportFormat.JSON)
                filepath = os.path.join(output_dir, f"{report_id}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                saved_files['json'] = filepath
        
        logger.info(f"Report saved: {report_id}")
        return saved_files

def demonstrate_executive_reporting():
    """Demonstrate the Executive Reporting System capabilities"""
    
    print("📊 DORA Compliance Executive Reporting System")
    print("=" * 50)
    
    # Sample gap assessment data
    gap_data = {
        'critical_gaps': [
            {
                'id': 'GAP-001',
                'category': 'Digital Operational Resilience Testing',
                'description': 'No comprehensive testing programme for critical systems'
            },
            {
                'id': 'GAP-002',
                'category': 'ICT Governance',
                'description': 'Insufficient ICT governance framework and board oversight'
            }
        ],
        'high_priority_gaps': [
            {
                'id': 'GAP-003',
                'category': 'ICT Risk Management',
                'description': 'Manual risk assessment processes lack automation'
            }
        ]
    }
    
    company_info = {
        'name': 'European Financial Services Ltd',
        'annual_revenue': 500000000,
        'country': 'Germany'
    }
    
    # Create reporting system
    reporting_system = ExecutiveReportingSystem()
    
    print("📋 Generating Executive Reports...")
    
    # Generate multiple reports
    try:
        reports = reporting_system.generate_multiple_reports(gap_data, company_info)
        
        print(f"✅ Report Generation Complete!")
        print(f"   • Total Reports: {reports['generation_summary']['total_reports']}")
        print(f"   • Report Types: {', '.join(reports['generation_summary']['report_types'])}")
        
        # Display report details
        for report_type, report in reports['reports'].items():
            print(f"\n📄 {report_type.replace('_', ' ').title()}:")
            print(f"   • Report ID: {report['metadata']['report_id']}")
            print(f"   • Audience: {report['config']['audience_level']}")
            
            if 'visualizations' in report:
                charts_count = len(report['visualizations']['individual_charts'])
                print(f"   • Charts Included: {charts_count}")
            
            # Show executive summary
            exec_summary = report['executive_summary']
            print(f"   • Recommendation: {exec_summary['recommendation']}")
        
        # Test export functionality
        print(f"\n📤 Testing Export Capabilities...")
        
        # Export board presentation to HTML
        board_report = reports['reports']['board_presentation']
        html_export = reporting_system.export_report(board_report, ReportFormat.HTML)
        print(f"   • HTML Export: {len(html_export)} characters generated")
        
        # Save reports
        saved_files = reporting_system.save_report(
            board_report,
            "demo_reports",
            [ReportFormat.HTML, ReportFormat.JSON]
        )
        print(f"   • Files Saved: {list(saved_files.keys())}")
        
        # Display key metrics
        if 'visualizations' in board_report:
            key_metrics = board_report['visualizations']['dashboard']['key_metrics']
            print(f"\n💰 Key Financial Highlights:")
            print(f"   • Maximum Penalty Risk: {key_metrics['max_penalty_risk']}")
            print(f"   • Implementation Cost: {key_metrics['implementation_cost']}")
            print(f"   • ROI: {key_metrics['roi_percentage']}")
            print(f"   • NPV: {key_metrics['npv']}")
            print(f"   • Recommendation: {key_metrics['recommendation']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n✅ Executive Reporting System Demonstration Complete!")

if __name__ == "__main__":
    demonstrate_executive_reporting() 