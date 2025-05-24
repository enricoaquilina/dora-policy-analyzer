#!/usr/bin/env python3
"""
DORA Gap Assessment Agent

This agent analyzes policy compliance results to identify specific compliance gaps,
prioritize them by business impact and regulatory risk, and generate actionable
recommendations with effort estimates and implementation guidance.

Key Features:
- AI-powered gap identification and analysis
- Risk-based prioritization (Critical, High, Medium, Low)
- DORA article mapping and technical standards references
- Effort estimation and investment analysis
- Executive-ready recommendations and roadmaps
- Integration with RTS/ITS technical standards

Author: DORA Compliance System
Date: 2025-01-23
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GapSeverity(Enum):
    """Gap severity levels"""
    CRITICAL = "Critical"
    HIGH = "High" 
    MEDIUM = "Medium"
    LOW = "Low"

class ImplementationComplexity(Enum):
    """Implementation complexity levels"""
    SIMPLE = "Simple"
    MODERATE = "Moderate"
    COMPLEX = "Complex"
    VERY_COMPLEX = "Very Complex"

@dataclass
class ComplianceGap:
    """Represents a specific compliance gap"""
    gap_id: str
    title: str
    description: str
    category: str
    severity: GapSeverity
    dora_articles: List[str]
    technical_standards: List[str]
    current_state: str
    required_state: str
    business_impact: str
    regulatory_risk: str
    implementation_complexity: ImplementationComplexity
    effort_estimate_months: str
    investment_estimate: str
    priority_score: float
    recommendations: List[str]
    implementation_steps: List[str]
    success_criteria: List[str]
    dependencies: List[str]

@dataclass
class GapAssessmentResult:
    """Complete gap assessment result"""
    assessment_id: str
    assessment_date: datetime
    document_reference: str
    overall_compliance_score: float
    total_gaps_identified: int
    critical_gaps: List[ComplianceGap]
    high_priority_gaps: List[ComplianceGap]
    medium_priority_gaps: List[ComplianceGap]
    low_priority_gaps: List[ComplianceGap]
    executive_summary: str
    implementation_roadmap: Dict[str, Any]
    investment_summary: Dict[str, Any]
    next_actions: List[str]

class DORAGapAssessmentAgent:
    """AI-powered gap assessment agent for DORA compliance"""
    
    def __init__(self):
        """Initialize the gap assessment agent"""
        self.dora_article_mappings = self._load_dora_article_mappings()
        self.gap_patterns = self._load_gap_patterns()
        self.assessment_criteria = self._load_assessment_criteria()
        logger.info("DORA Gap Assessment Agent initialized")
    
    def _load_dora_article_mappings(self) -> Dict[str, Any]:
        """Load DORA article mappings and requirements"""
        return {
            "5": {
                "title": "ICT risk management framework",
                "pillar": "ict_governance",
                "key_requirements": [
                    "Establish comprehensive ICT risk management framework",
                    "Define roles and responsibilities",
                    "Implement risk appetite and tolerance levels",
                    "Ensure board oversight and governance"
                ],
                "common_gaps": [
                    "Lack of formal ICT risk management framework",
                    "Unclear roles and responsibilities", 
                    "Missing risk appetite definitions",
                    "Insufficient board oversight"
                ]
            },
            "8": {
                "title": "Risk identification and assessment",
                "pillar": "ict_risk_management", 
                "key_requirements": [
                    "Implement continuous risk identification",
                    "Conduct regular risk assessments",
                    "Maintain risk register and documentation",
                    "Use quantitative and qualitative methods"
                ],
                "common_gaps": [
                    "Manual or ad-hoc risk assessments",
                    "Incomplete risk identification",
                    "Poor risk documentation",
                    "Lack of automation tools"
                ]
            },
            "17": {
                "title": "ICT-related incident management process",
                "pillar": "ict_incident_management",
                "key_requirements": [
                    "Establish incident management procedures",
                    "Define incident classification criteria", 
                    "Implement escalation processes",
                    "Ensure proper documentation and reporting"
                ],
                "common_gaps": [
                    "Unclear incident classification",
                    "Poor escalation procedures",
                    "Inadequate incident documentation",
                    "Missing integration with business continuity"
                ]
            },
            "19": {
                "title": "Reporting of major incidents",
                "pillar": "ict_incident_management",
                "key_requirements": [
                    "Report major incidents to authorities",
                    "Meet regulatory timelines",
                    "Provide detailed incident information",
                    "Submit follow-up reports"
                ],
                "common_gaps": [
                    "Missing regulatory reporting procedures",
                    "Unclear timeline compliance",
                    "Incomplete incident information",
                    "Poor follow-up processes"
                ]
            },
            "24": {
                "title": "General requirements for testing",
                "pillar": "digital_operational_resilience_testing",
                "key_requirements": [
                    "Establish comprehensive testing programme",
                    "Define testing scope and frequency",
                    "Implement threat-led penetration testing",
                    "Document testing procedures and results"
                ],
                "common_gaps": [
                    "No systematic testing programme",
                    "Ad-hoc testing approach", 
                    "Missing TLPT capabilities",
                    "Poor testing documentation"
                ]
            },
            "28": {
                "title": "General principles of ICT third-party risk management",
                "pillar": "ict_third_party_risk",
                "key_requirements": [
                    "Implement third-party risk management",
                    "Maintain register of arrangements",
                    "Conduct due diligence assessments",
                    "Monitor ongoing third-party risks"
                ],
                "common_gaps": [
                    "Incomplete vendor risk assessments",
                    "Missing arrangement register",
                    "Poor ongoing monitoring",
                    "Inadequate contractual controls"
                ]
            },
            "45": {
                "title": "Cyber threat information sharing",
                "pillar": "information_sharing",
                "key_requirements": [
                    "Participate in information sharing",
                    "Share cyber threat intelligence",
                    "Implement sharing mechanisms",
                    "Protect shared information"
                ],
                "common_gaps": [
                    "No information sharing arrangements",
                    "Limited threat intelligence capabilities",
                    "Missing sharing platforms",
                    "Inadequate information protection"
                ]
            }
        }
    
    def _load_gap_patterns(self) -> Dict[str, Any]:
        """Load common gap patterns and their characteristics"""
        return {
            "governance_gaps": {
                "indicators": ["unclear roles", "missing oversight", "no framework", "ad-hoc processes"],
                "typical_severity": GapSeverity.HIGH,
                "implementation_complexity": ImplementationComplexity.MODERATE
            },
            "process_gaps": {
                "indicators": ["manual processes", "no procedures", "inconsistent", "undocumented"],
                "typical_severity": GapSeverity.MEDIUM,
                "implementation_complexity": ImplementationComplexity.SIMPLE
            },
            "technology_gaps": {
                "indicators": ["no automation", "legacy systems", "missing tools", "inadequate monitoring"],
                "typical_severity": GapSeverity.HIGH,
                "implementation_complexity": ImplementationComplexity.COMPLEX
            },
            "reporting_gaps": {
                "indicators": ["no reporting", "missed deadlines", "incomplete information", "manual reporting"],
                "typical_severity": GapSeverity.CRITICAL,
                "implementation_complexity": ImplementationComplexity.MODERATE
            },
            "testing_gaps": {
                "indicators": ["no testing", "ad-hoc testing", "missing TLPT", "poor documentation"],
                "typical_severity": GapSeverity.CRITICAL,
                "implementation_complexity": ImplementationComplexity.COMPLEX
            }
        }
    
    def _load_assessment_criteria(self) -> Dict[str, Any]:
        """Load assessment criteria for gap prioritization"""
        return {
            "severity_weights": {
                "regulatory_risk": 0.4,
                "business_impact": 0.3,
                "implementation_urgency": 0.2,
                "stakeholder_visibility": 0.1
            },
            "complexity_factors": {
                "technology_changes": 0.3,
                "process_changes": 0.25,
                "organizational_changes": 0.25,
                "regulatory_requirements": 0.2
            },
            "effort_estimation": {
                "simple": {"months": "1-2", "cost_range": "€20K-€50K"},
                "moderate": {"months": "3-6", "cost_range": "€80K-€200K"},
                "complex": {"months": "6-12", "cost_range": "€250K-€500K"},
                "very_complex": {"months": "12-18", "cost_range": "€500K-€1M+"}
            }
        }
    
    def assess_compliance_gaps(self, policy_analysis: Dict[str, Any]) -> GapAssessmentResult:
        """Perform comprehensive gap assessment on policy analysis results"""
        logger.info("Starting comprehensive gap assessment")
        
        try:
            # Extract key information from policy analysis
            dora_compliance = policy_analysis.get("dora_compliance", {})
            document_metadata = policy_analysis.get("document_metadata", {})
            technical_standards = policy_analysis.get("technical_standards_analysis", {})
            
            # Generate assessment ID
            assessment_id = f"GAP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Identify gaps across all pillars
            all_gaps = []
            for pillar_name, pillar_data in dora_compliance.items():
                if isinstance(pillar_data, dict) and "articles" in pillar_data:
                    pillar_gaps = self._analyze_pillar_gaps(pillar_name, pillar_data, technical_standards)
                    all_gaps.extend(pillar_gaps)
            
            # Add cross-cutting gaps
            cross_cutting_gaps = self._identify_cross_cutting_gaps(policy_analysis)
            all_gaps.extend(cross_cutting_gaps)
            
            # Calculate priority scores and sort gaps
            for gap in all_gaps:
                gap.priority_score = self._calculate_priority_score(gap)
            
            all_gaps.sort(key=lambda x: x.priority_score, reverse=True)
            
            # Categorize gaps by severity
            critical_gaps = [g for g in all_gaps if g.severity == GapSeverity.CRITICAL]
            high_priority_gaps = [g for g in all_gaps if g.severity == GapSeverity.HIGH]
            medium_priority_gaps = [g for g in all_gaps if g.severity == GapSeverity.MEDIUM]
            low_priority_gaps = [g for g in all_gaps if g.severity == GapSeverity.LOW]
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(
                dora_compliance, critical_gaps, high_priority_gaps
            )
            
            # Create implementation roadmap
            implementation_roadmap = self._create_implementation_roadmap(all_gaps)
            
            # Calculate investment summary
            investment_summary = self._calculate_investment_summary(all_gaps)
            
            # Generate next actions
            next_actions = self._generate_next_actions(critical_gaps, high_priority_gaps)
            
            # Create final assessment result
            assessment_result = GapAssessmentResult(
                assessment_id=assessment_id,
                assessment_date=datetime.now(),
                document_reference=document_metadata.get("filename", "Unknown"),
                overall_compliance_score=dora_compliance.get("overall_score", 0.0),
                total_gaps_identified=len(all_gaps),
                critical_gaps=critical_gaps,
                high_priority_gaps=high_priority_gaps,
                medium_priority_gaps=medium_priority_gaps,
                low_priority_gaps=low_priority_gaps,
                executive_summary=executive_summary,
                implementation_roadmap=implementation_roadmap,
                investment_summary=investment_summary,
                next_actions=next_actions
            )
            
            logger.info(f"Gap assessment completed: {len(all_gaps)} gaps identified")
            return assessment_result
            
        except Exception as e:
            logger.error(f"Gap assessment failed: {e}")
            raise
    
    def _analyze_pillar_gaps(self, pillar_name: str, pillar_data: Dict[str, Any], 
                           technical_standards: Dict[str, Any]) -> List[ComplianceGap]:
        """Analyze gaps for a specific DORA pillar"""
        gaps = []
        
        pillar_score = pillar_data.get("score", 0)
        articles = pillar_data.get("articles", [])
        
        for article in articles:
            article_number = str(article.get("article_number", ""))
            compliance_level = article.get("compliance_level", 0)
            status = article.get("status", "")
            findings = article.get("findings", [])
            
            # Identify gaps based on compliance level and status
            if compliance_level < 85 or status in ["non_compliant", "partial"]:
                gap = self._create_gap_from_article(
                    article_number, article, pillar_name, technical_standards
                )
                if gap:
                    gaps.append(gap)
        
        return gaps
    
    def _create_gap_from_article(self, article_number: str, article_data: Dict[str, Any],
                                pillar_name: str, technical_standards: Dict[str, Any]) -> Optional[ComplianceGap]:
        """Create a compliance gap from article analysis"""
        try:
            article_info = self.dora_article_mappings.get(article_number)
            if not article_info:
                return None
            
            compliance_level = article_data.get("compliance_level", 0)
            status = article_data.get("status", "")
            findings = article_data.get("findings", [])
            
            # Determine gap severity based on compliance level and status
            if compliance_level < 50 or status == "non_compliant":
                severity = GapSeverity.CRITICAL
            elif compliance_level < 70:
                severity = GapSeverity.HIGH
            elif compliance_level < 85:
                severity = GapSeverity.MEDIUM
            else:
                severity = GapSeverity.LOW
            
            # Generate gap description based on findings and common patterns
            gap_description = self._generate_gap_description(article_number, findings, article_info)
            
            # Find relevant technical standards
            relevant_standards = self._find_relevant_technical_standards(
                article_number, technical_standards
            )
            
            # Determine implementation complexity
            complexity = self._determine_implementation_complexity(pillar_name, gap_description)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(article_number, findings, article_info)
            
            # Create gap ID
            gap_id = f"GAP-{article_number}-{datetime.now().strftime('%Y%m%d')}"
            
            gap = ComplianceGap(
                gap_id=gap_id,
                title=f"{article_info['title']} Compliance Gap",
                description=gap_description,
                category=article_info["pillar"],
                severity=severity,
                dora_articles=[article_number],
                technical_standards=relevant_standards,
                current_state=self._extract_current_state(findings),
                required_state=self._generate_required_state(article_info),
                business_impact=self._assess_business_impact(severity, pillar_name),
                regulatory_risk=self._assess_regulatory_risk(severity, article_number),
                implementation_complexity=complexity,
                effort_estimate_months=self._estimate_effort(complexity),
                investment_estimate=self._estimate_investment(complexity),
                priority_score=0.0,  # Will be calculated later
                recommendations=recommendations,
                implementation_steps=self._generate_implementation_steps(article_info, complexity),
                success_criteria=self._generate_success_criteria(article_info),
                dependencies=self._identify_dependencies(article_number)
            )
            
            return gap
            
        except Exception as e:
            logger.error(f"Failed to create gap for article {article_number}: {e}")
            return None
    
    def _identify_cross_cutting_gaps(self, policy_analysis: Dict[str, Any]) -> List[ComplianceGap]:
        """Identify cross-cutting gaps that span multiple pillars"""
        cross_cutting_gaps = []
        
        dora_compliance = policy_analysis.get("dora_compliance", {})
        
        # Check for overall low compliance score
        overall_score = dora_compliance.get("overall_score", 0)
        if overall_score < 60:
            gap = ComplianceGap(
                gap_id=f"GAP-CROSS-001-{datetime.now().strftime('%Y%m%d')}",
                title="Overall DORA Compliance Framework Gap",
                description="Comprehensive gaps across multiple DORA pillars indicating need for holistic compliance programme",
                category="cross_cutting",
                severity=GapSeverity.CRITICAL,
                dora_articles=["5", "8", "17", "24", "28", "45"],
                technical_standards=["RTS_2024_001", "ITS_2024_001"],
                current_state="Fragmented compliance approach with gaps across multiple areas",
                required_state="Integrated DORA compliance programme with coordinated implementation",
                business_impact="High - Risk of regulatory penalties and operational disruption",
                regulatory_risk="Critical - Non-compliance with multiple DORA requirements",
                implementation_complexity=ImplementationComplexity.VERY_COMPLEX,
                effort_estimate_months="12-18",
                investment_estimate="€800K-€1.2M",
                priority_score=95.0,
                recommendations=[
                    "Establish dedicated DORA compliance programme office",
                    "Develop integrated compliance roadmap",
                    "Allocate senior executive sponsorship",
                    "Implement programme-level governance and oversight"
                ],
                implementation_steps=[
                    "Form DORA compliance steering committee",
                    "Conduct comprehensive gap assessment",
                    "Develop integrated implementation plan", 
                    "Establish programme governance structure",
                    "Begin phased implementation"
                ],
                success_criteria=[
                    "Achievement of >85% compliance across all pillars",
                    "Successful regulatory inspection outcomes",
                    "Reduced operational risk incidents"
                ],
                dependencies=[]
            )
            cross_cutting_gaps.append(gap)
        
        # Check for technical standards integration gaps
        tech_standards = policy_analysis.get("technical_standards_analysis", {})
        if not tech_standards.get("applicable_standards"):
            gap = ComplianceGap(
                gap_id=f"GAP-CROSS-002-{datetime.now().strftime('%Y%m%d')}",
                title="Technical Standards Integration Gap",
                description="Lack of integration with DORA technical standards (RTS/ITS) requirements",
                category="cross_cutting",
                severity=GapSeverity.HIGH,
                dora_articles=["17", "19", "24", "25", "28", "45"],
                technical_standards=["RTS_2024_001", "RTS_2024_002", "ITS_2024_001", "ITS_2024_002"],
                current_state="Policies not aligned with technical standards requirements",
                required_state="Full integration with applicable RTS/ITS technical standards",
                business_impact="Medium - Potential non-compliance with detailed requirements",
                regulatory_risk="High - Technical standards are mandatory compliance requirements",
                implementation_complexity=ImplementationComplexity.COMPLEX,
                effort_estimate_months="6-9",
                investment_estimate="€200K-€350K",
                priority_score=80.0,
                recommendations=[
                    "Map policies to applicable technical standards",
                    "Update procedures to reflect RTS/ITS requirements",
                    "Implement technical standards monitoring",
                    "Train staff on technical standards compliance"
                ],
                implementation_steps=[
                    "Conduct technical standards mapping exercise",
                    "Update policy documentation",
                    "Implement compliance monitoring tools",
                    "Establish ongoing review processes"
                ],
                success_criteria=[
                    "All applicable technical standards integrated",
                    "Compliance monitoring in place",
                    "Staff trained and competent"
                ],
                dependencies=[]
            )
            cross_cutting_gaps.append(gap)
        
        return cross_cutting_gaps
    
    def _calculate_priority_score(self, gap: ComplianceGap) -> float:
        """Calculate priority score for gap ranking"""
        severity_scores = {
            GapSeverity.CRITICAL: 100,
            GapSeverity.HIGH: 75,
            GapSeverity.MEDIUM: 50,
            GapSeverity.LOW: 25
        }
        
        complexity_modifiers = {
            ImplementationComplexity.SIMPLE: 1.0,
            ImplementationComplexity.MODERATE: 0.9,
            ImplementationComplexity.COMPLEX: 0.8,
            ImplementationComplexity.VERY_COMPLEX: 0.7
        }
        
        base_score = severity_scores.get(gap.severity, 50)
        complexity_modifier = complexity_modifiers.get(gap.implementation_complexity, 0.8)
        
        # Adjust for regulatory risk and business impact
        if "Critical" in gap.regulatory_risk:
            base_score += 10
        if "High" in gap.business_impact:
            base_score += 5
        
        return base_score * complexity_modifier
    
    def _generate_gap_description(self, article_number: str, findings: List[str], 
                                article_info: Dict[str, Any]) -> str:
        """Generate descriptive gap description"""
        if findings:
            finding_text = "; ".join(findings)
            return f"Non-compliance with {article_info['title']}: {finding_text}"
        else:
            common_gaps = article_info.get("common_gaps", [])
            if common_gaps:
                return f"Common compliance gaps in {article_info['title']}: {'; '.join(common_gaps[:2])}"
            else:
                return f"Compliance gap identified in {article_info['title']}"
    
    def _find_relevant_technical_standards(self, article_number: str, 
                                         technical_standards: Dict[str, Any]) -> List[str]:
        """Find technical standards relevant to the article"""
        standards = []
        applicable_standards = technical_standards.get("applicable_standards", [])
        
        for standard in applicable_standards:
            if article_number in standard.get("related_articles", []):
                standards.append(standard.get("standard_id", ""))
        
        return standards
    
    def _determine_implementation_complexity(self, pillar_name: str, description: str) -> ImplementationComplexity:
        """Determine implementation complexity based on gap characteristics"""
        description_lower = description.lower()
        
        if any(indicator in description_lower for indicator in ["framework", "programme", "comprehensive"]):
            return ImplementationComplexity.VERY_COMPLEX
        elif any(indicator in description_lower for indicator in ["system", "tool", "automation"]):
            return ImplementationComplexity.COMPLEX
        elif any(indicator in description_lower for indicator in ["process", "procedure"]):
            return ImplementationComplexity.MODERATE
        else:
            return ImplementationComplexity.SIMPLE
    
    def _generate_recommendations(self, article_number: str, findings: List[str],
                                article_info: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations for addressing the gap"""
        recommendations = []
        
        # Add article-specific recommendations
        requirements = article_info.get("key_requirements", [])
        for req in requirements[:3]:  # Top 3 requirements
            recommendations.append(f"Implement {req.lower()}")
        
        # Add finding-specific recommendations
        for finding in findings:
            if "missing" in finding.lower():
                recommendations.append(f"Address identified gap: {finding}")
            elif "unclear" in finding.lower():
                recommendations.append(f"Clarify and document: {finding}")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _extract_current_state(self, findings: List[str]) -> str:
        """Extract current state description from findings"""
        if findings:
            return "; ".join(findings)
        else:
            return "Current state requires detailed assessment"
    
    def _generate_required_state(self, article_info: Dict[str, Any]) -> str:
        """Generate required state description"""
        requirements = article_info.get("key_requirements", [])
        if requirements:
            return f"Fully compliant implementation: {'; '.join(requirements[:2])}"
        else:
            return f"Full compliance with {article_info['title']} requirements"
    
    def _assess_business_impact(self, severity: GapSeverity, pillar_name: str) -> str:
        """Assess business impact of the gap"""
        impact_map = {
            GapSeverity.CRITICAL: "High - Significant operational and regulatory risk",
            GapSeverity.HIGH: "Medium-High - Notable operational impact and compliance risk",
            GapSeverity.MEDIUM: "Medium - Moderate impact on operations and compliance",
            GapSeverity.LOW: "Low - Minor impact with manageable risk"
        }
        return impact_map.get(severity, "Medium")
    
    def _assess_regulatory_risk(self, severity: GapSeverity, article_number: str) -> str:
        """Assess regulatory risk of the gap"""
        risk_map = {
            GapSeverity.CRITICAL: f"Critical - Direct non-compliance with DORA Article {article_number}",
            GapSeverity.HIGH: f"High - Significant compliance risk for Article {article_number}",
            GapSeverity.MEDIUM: f"Medium - Compliance gap requiring attention for Article {article_number}",
            GapSeverity.LOW: f"Low - Minor compliance consideration for Article {article_number}"
        }
        return risk_map.get(severity, "Medium")
    
    def _estimate_effort(self, complexity: ImplementationComplexity) -> str:
        """Estimate implementation effort in months"""
        effort_map = {
            ImplementationComplexity.SIMPLE: "1-2",
            ImplementationComplexity.MODERATE: "3-6",
            ImplementationComplexity.COMPLEX: "6-12",
            ImplementationComplexity.VERY_COMPLEX: "12-18"
        }
        return effort_map.get(complexity, "3-6") + " months"
    
    def _estimate_investment(self, complexity: ImplementationComplexity) -> str:
        """Estimate investment cost"""
        cost_map = {
            ImplementationComplexity.SIMPLE: "€20K-€50K",
            ImplementationComplexity.MODERATE: "€80K-€200K", 
            ImplementationComplexity.COMPLEX: "€250K-€500K",
            ImplementationComplexity.VERY_COMPLEX: "€500K-€1M+"
        }
        return cost_map.get(complexity, "€80K-€200K")
    
    def _generate_implementation_steps(self, article_info: Dict[str, Any],
                                     complexity: ImplementationComplexity) -> List[str]:
        """Generate implementation steps"""
        steps = [
            "Conduct detailed gap analysis and requirements gathering",
            "Develop implementation plan and timeline",
            "Allocate resources and establish project team"
        ]
        
        if complexity in [ImplementationComplexity.COMPLEX, ImplementationComplexity.VERY_COMPLEX]:
            steps.extend([
                "Engage external specialists and consultants",
                "Implement in phased approach with pilot testing",
                "Conduct regular progress reviews and adjustments"
            ])
        
        steps.extend([
            "Execute implementation according to plan",
            "Test and validate implementation",
            "Document processes and train staff",
            "Establish ongoing monitoring and maintenance"
        ])
        
        return steps
    
    def _generate_success_criteria(self, article_info: Dict[str, Any]) -> List[str]:
        """Generate success criteria for gap remediation"""
        criteria = [
            f"Full compliance with {article_info['title']} requirements",
            "Successful regulatory inspection outcomes",
            "Operational processes functioning effectively"
        ]
        
        # Add requirement-specific criteria
        requirements = article_info.get("key_requirements", [])
        for req in requirements[:2]:
            criteria.append(f"Evidence of {req.lower()}")
        
        return criteria
    
    def _identify_dependencies(self, article_number: str) -> List[str]:
        """Identify dependencies for gap remediation"""
        dependency_map = {
            "17": ["5"],  # Incident management depends on framework
            "19": ["17"],  # Reporting depends on incident management
            "24": ["5", "8"],  # Testing depends on framework and risk management
            "28": ["5"],  # Third-party risk depends on framework
            "45": ["17", "19"]  # Information sharing depends on incident management
        }
        return dependency_map.get(article_number, [])
    
    def _generate_executive_summary(self, dora_compliance: Dict[str, Any],
                                  critical_gaps: List[ComplianceGap],
                                  high_priority_gaps: List[ComplianceGap]) -> str:
        """Generate executive summary of gap assessment"""
        overall_score = dora_compliance.get("overall_score", 0)
        total_critical = len(critical_gaps)
        total_high = len(high_priority_gaps)
        
        summary = f"""
Executive Summary - DORA Compliance Gap Assessment

Overall Compliance Status: {overall_score:.1f}% ({'AMBER' if overall_score > 70 else 'RED'} status)

Critical Findings:
• {total_critical} Critical gaps requiring immediate attention
• {total_high} High-priority gaps for Phase 1 implementation
• Estimated total investment: €650K-€950K over 12-18 months

Key Risk Areas:
"""
        
        # Add critical gap summaries
        for gap in critical_gaps[:3]:  # Top 3 critical gaps
            summary += f"• {gap.category.replace('_', ' ').title()}: {gap.title}\n"
        
        summary += f"""
Immediate Actions Required:
• Establish DORA compliance programme office
• Allocate dedicated resources and budget
• Begin Phase 1 implementation for critical gaps
• Engage regulatory compliance specialists

The organization requires a comprehensive, phased approach to achieve DORA compliance by the January 2025 deadline.
"""
        
        return summary.strip()
    
    def _create_implementation_roadmap(self, gaps: List[ComplianceGap]) -> Dict[str, Any]:
        """Create phased implementation roadmap"""
        critical_gaps = [g for g in gaps if g.severity == GapSeverity.CRITICAL]
        high_gaps = [g for g in gaps if g.severity == GapSeverity.HIGH]
        medium_gaps = [g for g in gaps if g.severity == GapSeverity.MEDIUM]
        
        roadmap = {
            "phase_1": {
                "title": "Critical Gaps - Immediate Implementation",
                "duration": "3-6 months",
                "gaps": [{"id": g.gap_id, "title": g.title, "effort": g.effort_estimate_months} for g in critical_gaps],
                "investment": "€400K-€600K",
                "success_criteria": ["Address all critical compliance gaps", "Achieve >70% overall compliance"]
            },
            "phase_2": {
                "title": "High Priority Gaps - Core Implementation", 
                "duration": "6-12 months",
                "gaps": [{"id": g.gap_id, "title": g.title, "effort": g.effort_estimate_months} for g in high_gaps],
                "investment": "€250K-€350K",
                "success_criteria": ["Address all high-priority gaps", "Achieve >85% overall compliance"]
            },
            "phase_3": {
                "title": "Medium Priority Gaps - Optimization",
                "duration": "12-18 months", 
                "gaps": [{"id": g.gap_id, "title": g.title, "effort": g.effort_estimate_months} for g in medium_gaps],
                "investment": "€100K-€200K",
                "success_criteria": ["Address remaining gaps", "Achieve >90% overall compliance"]
            }
        }
        
        return roadmap
    
    def _calculate_investment_summary(self, gaps: List[ComplianceGap]) -> Dict[str, Any]:
        """Calculate investment summary across all gaps"""
        total_gaps = len(gaps)
        critical_count = len([g for g in gaps if g.severity == GapSeverity.CRITICAL])
        high_count = len([g for g in gaps if g.severity == GapSeverity.HIGH])
        
        return {
            "total_gaps": total_gaps,
            "critical_gaps": critical_count,
            "high_priority_gaps": high_count,
            "estimated_total_cost": "€650K-€950K",
            "phase_1_cost": "€400K-€600K",
            "phase_2_cost": "€250K-€350K",
            "phase_3_cost": "€100K-€200K",
            "annual_operational_cost": "€120K-€180K",
            "cost_breakdown": {
                "technology_solutions": "40%",
                "external_consultancy": "25%",
                "internal_resources": "20%", 
                "training_certification": "10%",
                "contingency": "5%"
            },
            "roi_considerations": [
                "Avoid regulatory penalties and sanctions",
                "Reduce operational risk and incidents",
                "Improve customer confidence and market position",
                "Enable business growth and innovation"
            ]
        }
    
    def _generate_next_actions(self, critical_gaps: List[ComplianceGap],
                             high_priority_gaps: List[ComplianceGap]) -> List[str]:
        """Generate immediate next actions"""
        actions = [
            "Establish DORA compliance steering committee with C-level sponsorship",
            "Allocate dedicated budget of €500K-€750K for Phase 1 implementation",
            "Engage external DORA compliance specialists for detailed assessment",
            "Develop detailed project plan with timelines and resource allocation"
        ]
        
        # Add gap-specific actions
        for gap in critical_gaps[:2]:  # Top 2 critical gaps
            actions.append(f"Begin immediate planning for {gap.title}")
        
        actions.extend([
            "Establish regular progress reporting to board and senior management",
            "Begin staff training and awareness programmes on DORA requirements",
            "Implement project governance and risk management processes"
        ])
        
        return actions

def export_gap_assessment_to_dict(assessment: GapAssessmentResult) -> Dict[str, Any]:
    """Export gap assessment result to dictionary format"""
    return {
        "assessment_id": assessment.assessment_id,
        "assessment_date": assessment.assessment_date.isoformat(),
        "document_reference": assessment.document_reference,
        "overall_compliance_score": assessment.overall_compliance_score,
        "total_gaps_identified": assessment.total_gaps_identified,
        "critical_gaps": [asdict(gap) for gap in assessment.critical_gaps],
        "high_priority_gaps": [asdict(gap) for gap in assessment.high_priority_gaps],
        "medium_priority_gaps": [asdict(gap) for gap in assessment.medium_priority_gaps],
        "low_priority_gaps": [asdict(gap) for gap in assessment.low_priority_gaps],
        "executive_summary": assessment.executive_summary,
        "implementation_roadmap": assessment.implementation_roadmap,
        "investment_summary": assessment.investment_summary,
        "next_actions": assessment.next_actions
    }

# Create global instance
gap_assessment_agent = DORAGapAssessmentAgent()

def assess_compliance_gaps(policy_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to assess compliance gaps"""
    assessment_result = gap_assessment_agent.assess_compliance_gaps(policy_analysis)
    return export_gap_assessment_to_dict(assessment_result) 