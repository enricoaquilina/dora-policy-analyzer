#!/usr/bin/env python3
"""
DORA Compliance Scoring Engine

This module provides comprehensive scoring and assessment capabilities for DORA compliance,
including RAG status indicators, weighted criteria evaluation, gap analysis, and 
multi-level aggregation from requirements to domains.

Features:
- Multi-level scoring (criterion, requirement, article, pillar, overall)
- RAG (Red/Amber/Green) status determination
- Weighted scoring with configurable criteria
- Gap analysis and remediation prioritization
- Automated and manual assessment support
- Historical scoring and trend analysis
- Configurable scoring methodologies
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from uuid import uuid4

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import our data models
import sys
sys.path.append(str(Path(__file__).parent.parent))
from schemas.data_models import (
    Base, Requirement, ComplianceCriteria, ScoringRubric, ComplianceAssessment,
    AssessmentScore, GapAnalysis, PillarType, RequirementType, ComplianceLevel,
    AssessmentMethod, EvidenceType, RiskLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGStatus(Enum):
    """RAG (Red/Amber/Green) status levels"""
    RED = "red"           # Critical non-compliance (0-4.9)
    AMBER = "amber"       # Partial compliance (5.0-7.9) 
    GREEN = "green"       # Full compliance (8.0-10.0)
    NOT_ASSESSED = "not_assessed"

class ScoreWeightType(Enum):
    """Types of score weighting"""
    EQUAL = "equal"                    # All criteria weighted equally
    RISK_BASED = "risk_based"         # Weighted by risk level
    CRITICALITY = "criticality"       # Weighted by business criticality
    REGULATORY_PRIORITY = "regulatory_priority"  # Weighted by regulatory focus
    CUSTOM = "custom"                 # Custom weighting scheme

class AssessmentConfidence(Enum):
    """Confidence levels for assessments"""
    HIGH = "high"         # 90-100% confidence
    MEDIUM = "medium"     # 70-89% confidence  
    LOW = "low"           # 50-69% confidence
    VERY_LOW = "very_low" # <50% confidence

@dataclass
class ScoringCriteria:
    """Individual scoring criteria definition"""
    criteria_id: str
    name: str
    description: str
    weight: Decimal
    score_range: Tuple[int, int] = (0, 10)
    assessment_method: AssessmentMethod = AssessmentMethod.MANUAL
    evidence_types: List[EvidenceType] = field(default_factory=list)
    scoring_guidelines: Dict[str, str] = field(default_factory=dict)
    automation_feasible: bool = False

@dataclass
class ScoreResult:
    """Individual score result"""
    criteria_id: str
    score: Decimal
    max_score: Decimal
    rag_status: RAGStatus
    confidence: AssessmentConfidence
    evidence_provided: List[str] = field(default_factory=list)
    gaps_identified: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    assessor: Optional[str] = None
    assessment_date: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None

@dataclass
class AggregatedScore:
    """Aggregated score at various levels"""
    level: str  # requirement, article, pillar, overall
    entity_id: str
    entity_name: str
    score: Decimal
    max_score: Decimal
    percentage: Decimal
    rag_status: RAGStatus
    contributing_scores: List[ScoreResult] = field(default_factory=list)
    gap_count: int = 0
    critical_gaps: List[str] = field(default_factory=list)
    improvement_priority: int = 1  # 1=highest, 5=lowest

class DORAComplianceScoringEngine:
    """Main scoring engine for DORA compliance assessment"""
    
    def __init__(self, database_url: str = "postgresql://postgres:password@localhost:5432/dora_kb"):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Initialize scoring configurations
        self.scoring_methodologies = self._initialize_scoring_methodologies()
        self.rag_thresholds = self._initialize_rag_thresholds()
        self.pillar_weights = self._initialize_pillar_weights()
        
    def _initialize_scoring_methodologies(self) -> Dict[str, Any]:
        """Initialize different scoring methodologies"""
        return {
            "standard": {
                "name": "Standard DORA Scoring",
                "description": "Balanced scoring across all requirements",
                "weight_type": ScoreWeightType.EQUAL,
                "rag_thresholds": {"red": 4.9, "amber": 7.9, "green": 10.0},
                "evidence_multiplier": 1.0
            },
            "risk_based": {
                "name": "Risk-Based Scoring",
                "description": "Higher weight for high-risk requirements",
                "weight_type": ScoreWeightType.RISK_BASED,
                "rag_thresholds": {"red": 5.4, "amber": 8.2, "green": 10.0},
                "evidence_multiplier": 1.2
            },
            "regulatory_focus": {
                "name": "Regulatory Priority Scoring",
                "description": "Emphasis on regulatory examination priorities",
                "weight_type": ScoreWeightType.REGULATORY_PRIORITY,
                "rag_thresholds": {"red": 4.5, "amber": 7.5, "green": 10.0},
                "evidence_multiplier": 1.1
            },
            "operational": {
                "name": "Operational Excellence Scoring",
                "description": "Focus on operational resilience capabilities",
                "weight_type": ScoreWeightType.CRITICALITY,
                "rag_thresholds": {"red": 5.0, "amber": 8.0, "green": 10.0},
                "evidence_multiplier": 1.0
            }
        }
    
    def _initialize_rag_thresholds(self) -> Dict[str, Tuple[float, float]]:
        """Initialize RAG status thresholds"""
        return {
            "standard": (4.9, 7.9),
            "conservative": (5.9, 8.4),
            "aggressive": (3.9, 6.9),
            "regulatory": (5.4, 8.2)
        }
    
    def _initialize_pillar_weights(self) -> Dict[PillarType, Decimal]:
        """Initialize default pillar weights"""
        return {
            PillarType.GOVERNANCE_ARRANGEMENTS: Decimal("0.25"),
            PillarType.ICT_RELATED_INCIDENTS: Decimal("0.20"),
            PillarType.DIGITAL_OPERATIONAL_RESILIENCE_TESTING: Decimal("0.15"),
            PillarType.ICT_THIRD_PARTY_RISK: Decimal("0.25"),
            PillarType.INFORMATION_SHARING: Decimal("0.15")
        }
    
    def create_scoring_rubrics(self) -> Dict[str, List[ScoringCriteria]]:
        """Create comprehensive scoring rubrics for DORA requirements"""
        logger.info("Creating DORA scoring rubrics...")
        
        rubrics = {
            "governance": self._create_governance_rubric(),
            "incident_management": self._create_incident_rubric(),
            "testing": self._create_testing_rubric(),
            "third_party_risk": self._create_third_party_rubric(),
            "information_sharing": self._create_information_sharing_rubric()
        }
        
        total_criteria = sum(len(criteria_list) for criteria_list in rubrics.values())
        logger.info(f"Created {total_criteria} scoring criteria across {len(rubrics)} domains")
        
        return rubrics
    
    def _create_governance_rubric(self) -> List[ScoringCriteria]:
        """Create governance scoring criteria"""
        return [
            ScoringCriteria(
                criteria_id="gov_framework_01",
                name="ICT Risk Management Framework Existence",
                description="Comprehensive ICT risk management framework documented and approved",
                weight=Decimal("3.0"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.POLICY_DOCUMENT, EvidenceType.BOARD_RESOLUTION],
                scoring_guidelines={
                    "10": "Comprehensive framework with all DORA requirements, board approved",
                    "8-9": "Good framework covering most requirements, minor gaps",
                    "6-7": "Basic framework exists but significant gaps or lack of approval",
                    "4-5": "Framework exists but inadequate coverage or implementation",
                    "0-3": "No framework or fundamentally inadequate"
                },
                automation_feasible=False
            ),
            ScoringCriteria(
                criteria_id="gov_framework_02",
                name="Periodic Review and Updates",
                description="Framework subject to regular review and updates (at least annually)",
                weight=Decimal("2.0"),
                assessment_method=AssessmentMethod.HYBRID,
                evidence_types=[EvidenceType.PROCEDURE_DOCUMENT, EvidenceType.MEETING_MINUTES],
                scoring_guidelines={
                    "10": "Annual reviews documented with evidence of updates and improvements",
                    "8-9": "Regular reviews with some documented updates",
                    "6-7": "Reviews occur but limited documentation or follow-up",
                    "4-5": "Infrequent reviews or inadequate documentation",
                    "0-3": "No evidence of regular review process"
                },
                automation_feasible=True
            ),
            ScoringCriteria(
                criteria_id="gov_resources_01",
                name="Resource Allocation",
                description="Sufficient human and financial resources allocated to ICT risk management",
                weight=Decimal("2.5"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.ORGANIZATIONAL_CHART, EvidenceType.BUDGET_DOCUMENT],
                scoring_guidelines={
                    "10": "Dedicated team with clear responsibilities and adequate budget",
                    "8-9": "Mostly adequate resources with minor gaps",
                    "6-7": "Basic resource allocation but stretched capacity",
                    "4-5": "Inadequate resources affecting capability",
                    "0-3": "No dedicated resources or severe understaffing"
                },
                automation_feasible=False
            ),
            ScoringCriteria(
                criteria_id="gov_oversight_01",
                name="Management Body Oversight",
                description="Active management body involvement in ICT risk governance",
                weight=Decimal("2.5"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.BOARD_RESOLUTION, EvidenceType.MEETING_MINUTES],
                scoring_guidelines={
                    "10": "Regular board engagement with documented decisions and oversight",
                    "8-9": "Good board involvement with most key decisions documented",
                    "6-7": "Basic board oversight but limited engagement",
                    "4-5": "Minimal board involvement or poor documentation",
                    "0-3": "No evidence of meaningful board oversight"
                },
                automation_feasible=False
            )
        ]
    
    def _create_incident_rubric(self) -> List[ScoringCriteria]:
        """Create incident management scoring criteria"""
        return [
            ScoringCriteria(
                criteria_id="inc_process_01",
                name="Incident Management Process",
                description="Defined and implemented ICT incident management process",
                weight=Decimal("3.0"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.PROCEDURE_DOCUMENT, EvidenceType.INCIDENT_REPORTS],
                scoring_guidelines={
                    "10": "Comprehensive process covering all DORA requirements with evidence of use",
                    "8-9": "Good process with minor gaps and regular use",
                    "6-7": "Basic process but gaps in coverage or implementation",
                    "4-5": "Process exists but significant deficiencies",
                    "0-3": "No defined process or fundamentally inadequate"
                },
                automation_feasible=False
            ),
            ScoringCriteria(
                criteria_id="inc_classification_01",
                name="Incident Classification System",
                description="Systematic classification of incidents by priority and severity",
                weight=Decimal("2.0"),
                assessment_method=AssessmentMethod.HYBRID,
                evidence_types=[EvidenceType.PROCEDURE_DOCUMENT, EvidenceType.INCIDENT_REPORTS],
                scoring_guidelines={
                    "10": "Clear classification criteria with consistent application",
                    "8-9": "Good classification system with minor inconsistencies",
                    "6-7": "Basic classification but gaps or inconsistent application",
                    "4-5": "Classification exists but poorly defined or applied",
                    "0-3": "No systematic classification approach"
                },
                automation_feasible=True
            ),
            ScoringCriteria(
                criteria_id="inc_reporting_01",
                name="Incident Reporting Capability",
                description="Effective internal and external incident reporting mechanisms",
                weight=Decimal("2.5"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.INCIDENT_REPORTS, EvidenceType.REGULATORY_SUBMISSION],
                scoring_guidelines={
                    "10": "Comprehensive reporting with all required elements and timely submission",
                    "8-9": "Good reporting with minor gaps or delays",
                    "6-7": "Basic reporting but missing elements or timing issues",
                    "4-5": "Reporting exists but significant deficiencies",
                    "0-3": "No systematic reporting or major non-compliance"
                },
                automation_feasible=False
            ),
            ScoringCriteria(
                criteria_id="inc_response_01",
                name="Incident Response Effectiveness",
                description="Timely and effective response to ICT incidents",
                weight=Decimal("2.5"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.INCIDENT_REPORTS, EvidenceType.POST_INCIDENT_REVIEW],
                scoring_guidelines={
                    "10": "Consistently effective response with documented lessons learned",
                    "8-9": "Generally effective response with good documentation",
                    "6-7": "Response occurs but gaps in effectiveness or documentation",
                    "4-5": "Poor response times or effectiveness",
                    "0-3": "No effective incident response capability"
                },
                automation_feasible=False
            )
        ]
    
    def _create_testing_rubric(self) -> List[ScoringCriteria]:
        """Create testing scoring criteria"""
        return [
            ScoringCriteria(
                criteria_id="test_program_01",
                name="Testing Programme Comprehensiveness",
                description="Comprehensive digital operational resilience testing programme",
                weight=Decimal("3.0"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.TEST_RESULTS, EvidenceType.PROCEDURE_DOCUMENT],
                scoring_guidelines={
                    "10": "Comprehensive programme covering all systems and scenarios",
                    "8-9": "Good programme with minor coverage gaps",
                    "6-7": "Basic programme but significant gaps",
                    "4-5": "Limited testing programme",
                    "0-3": "No systematic testing programme"
                },
                automation_feasible=False
            ),
            ScoringCriteria(
                criteria_id="test_frequency_01",
                name="Testing Frequency and Regularity",
                description="Regular and appropriate frequency of resilience testing",
                weight=Decimal("2.0"),
                assessment_method=AssessmentMethod.AUTOMATED,
                evidence_types=[EvidenceType.TEST_RESULTS, EvidenceType.SCHEDULE_DOCUMENT],
                scoring_guidelines={
                    "10": "Testing performed at optimal frequency with documented schedule",
                    "8-9": "Regular testing with minor scheduling gaps",
                    "6-7": "Inconsistent testing frequency",
                    "4-5": "Infrequent testing",
                    "0-3": "No regular testing schedule"
                },
                automation_feasible=True
            ),
            ScoringCriteria(
                criteria_id="test_scenarios_01",
                name="Scenario Coverage and Realism",
                description="Testing scenarios cover realistic and severe disruption scenarios",
                weight=Decimal("2.5"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.TEST_RESULTS, EvidenceType.SCENARIO_DOCUMENT],
                scoring_guidelines={
                    "10": "Comprehensive scenarios including severe and complex disruptions",
                    "8-9": "Good scenario coverage with minor gaps",
                    "6-7": "Basic scenarios but limited complexity",
                    "4-5": "Simple scenarios only",
                    "0-3": "No realistic scenario testing"
                },
                automation_feasible=False
            ),
            ScoringCriteria(
                criteria_id="test_remediation_01",
                name="Remediation and Follow-up",
                description="Effective remediation of issues identified through testing",
                weight=Decimal("2.5"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.REMEDIATION_PLAN, EvidenceType.TEST_RESULTS],
                scoring_guidelines={
                    "10": "Systematic remediation with tracking and verification",
                    "8-9": "Good remediation with minor tracking gaps",
                    "6-7": "Basic remediation but limited tracking",
                    "4-5": "Poor remediation follow-up",
                    "0-3": "No systematic remediation process"
                },
                automation_feasible=False
            )
        ]
    
    def _create_third_party_rubric(self) -> List[ScoringCriteria]:
        """Create third-party risk scoring criteria"""
        return [
            ScoringCriteria(
                criteria_id="tpr_assessment_01",
                name="Third-party Risk Assessment",
                description="Comprehensive assessment of ICT third-party risks",
                weight=Decimal("3.0"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.THIRD_PARTY_CONTRACTS, EvidenceType.AUDIT_REPORT],
                scoring_guidelines={
                    "10": "Comprehensive risk assessment covering all critical aspects",
                    "8-9": "Good assessment with minor gaps",
                    "6-7": "Basic assessment but significant gaps",
                    "4-5": "Limited assessment coverage",
                    "0-3": "No systematic risk assessment"
                },
                automation_feasible=False
            ),
            ScoringCriteria(
                criteria_id="tpr_contracts_01",
                name="Contract Risk Management",
                description="Appropriate contractual provisions for ICT risk management",
                weight=Decimal("2.5"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.THIRD_PARTY_CONTRACTS, EvidenceType.CONTRACT_REVIEW],
                scoring_guidelines={
                    "10": "Comprehensive contractual provisions covering all DORA requirements",
                    "8-9": "Good contractual coverage with minor gaps",
                    "6-7": "Basic provisions but significant gaps",
                    "4-5": "Limited contractual protections",
                    "0-3": "No adequate contractual provisions"
                },
                automation_feasible=False
            ),
            ScoringCriteria(
                criteria_id="tpr_monitoring_01",
                name="Ongoing Monitoring",
                description="Continuous monitoring of third-party service provider performance",
                weight=Decimal("2.5"),
                assessment_method=AssessmentMethod.HYBRID,
                evidence_types=[EvidenceType.MONITORING_REPORTS, EvidenceType.AUDIT_REPORT],
                scoring_guidelines={
                    "10": "Comprehensive monitoring with regular reporting and follow-up",
                    "8-9": "Good monitoring with minor gaps",
                    "6-7": "Basic monitoring but limited coverage",
                    "4-5": "Minimal monitoring activity",
                    "0-3": "No systematic monitoring"
                },
                automation_feasible=True
            ),
            ScoringCriteria(
                criteria_id="tpr_concentration_01",
                name="Concentration Risk Management",
                description="Management of ICT concentration risks",
                weight=Decimal("2.0"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.RISK_REGISTER, EvidenceType.CONCENTRATION_ANALYSIS],
                scoring_guidelines={
                    "10": "Comprehensive concentration risk analysis and management",
                    "8-9": "Good concentration risk management",
                    "6-7": "Basic concentration risk awareness",
                    "4-5": "Limited concentration risk consideration",
                    "0-3": "No concentration risk management"
                },
                automation_feasible=False
            )
        ]
    
    def _create_information_sharing_rubric(self) -> List[ScoringCriteria]:
        """Create information sharing scoring criteria"""
        return [
            ScoringCriteria(
                criteria_id="info_arrangements_01",
                name="Information Sharing Arrangements",
                description="Participation in cyber threat information sharing arrangements",
                weight=Decimal("2.0"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.PARTICIPATION_AGREEMENT, EvidenceType.SHARING_LOGS],
                scoring_guidelines={
                    "10": "Active participation in multiple relevant arrangements",
                    "8-9": "Good participation with regular sharing",
                    "6-7": "Basic participation but limited activity",
                    "4-5": "Minimal participation",
                    "0-3": "No participation in sharing arrangements"
                },
                automation_feasible=False
            ),
            ScoringCriteria(
                criteria_id="info_quality_01",
                name="Information Quality and Relevance",
                description="Quality and relevance of shared and received threat information",
                weight=Decimal("2.0"),
                assessment_method=AssessmentMethod.MANUAL,
                evidence_types=[EvidenceType.THREAT_INTEL_REPORTS, EvidenceType.SHARING_LOGS],
                scoring_guidelines={
                    "10": "High-quality, relevant, and actionable information sharing",
                    "8-9": "Good quality information with minor relevance gaps",
                    "6-7": "Adequate information quality",
                    "4-5": "Poor quality or irrelevant information",
                    "0-3": "No meaningful information sharing"
                },
                automation_feasible=False
            ),
            ScoringCriteria(
                criteria_id="info_timeliness_01",
                name="Timeliness of Information Sharing",
                description="Prompt sharing and utilization of threat intelligence",
                weight=Decimal("1.5"),
                assessment_method=AssessmentMethod.HYBRID,
                evidence_types=[EvidenceType.SHARING_LOGS, EvidenceType.INCIDENT_TIMELINE],
                scoring_guidelines={
                    "10": "Real-time or near real-time information sharing",
                    "8-9": "Timely sharing with minor delays",
                    "6-7": "Acceptable timeliness but some delays",
                    "4-5": "Significant delays in sharing",
                    "0-3": "No timely information sharing"
                },
                automation_feasible=True
            )
        ]
    
    def calculate_rag_status(self, score: Decimal, max_score: Decimal, 
                           methodology: str = "standard") -> RAGStatus:
        """Calculate RAG status based on score and methodology"""
        if max_score == 0:
            return RAGStatus.NOT_ASSESSED
        
        percentage = (score / max_score) * 100
        thresholds = self.rag_thresholds.get(methodology, self.rag_thresholds["standard"])
        
        if percentage >= thresholds[1]:
            return RAGStatus.GREEN
        elif percentage >= thresholds[0]:
            return RAGStatus.AMBER
        else:
            return RAGStatus.RED
    
    def assess_requirement(self, requirement_id: str, criteria_scores: List[ScoreResult],
                          methodology: str = "standard") -> AggregatedScore:
        """Assess a single requirement based on criteria scores"""
        if not criteria_scores:
            return AggregatedScore(
                level="requirement",
                entity_id=requirement_id,
                entity_name=f"Requirement {requirement_id}",
                score=Decimal("0"),
                max_score=Decimal("10"),
                percentage=Decimal("0"),
                rag_status=RAGStatus.NOT_ASSESSED
            )
        
        # Calculate weighted score
        total_weighted_score = Decimal("0")
        total_weight = Decimal("0")
        
        for score_result in criteria_scores:
            # Find the criteria to get weight
            weight = Decimal("1.0")  # Default weight
            total_weighted_score += score_result.score * weight
            total_weight += weight
        
        final_score = total_weighted_score / total_weight if total_weight > 0 else Decimal("0")
        final_score = final_score.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        
        # Calculate RAG status
        rag_status = self.calculate_rag_status(final_score, Decimal("10"), methodology)
        
        # Identify gaps and critical issues
        gaps = []
        critical_gaps = []
        for score_result in criteria_scores:
            gaps.extend(score_result.gaps_identified)
            if score_result.rag_status == RAGStatus.RED:
                critical_gaps.extend(score_result.gaps_identified)
        
        return AggregatedScore(
            level="requirement",
            entity_id=requirement_id,
            entity_name=f"Requirement {requirement_id}",
            score=final_score,
            max_score=Decimal("10"),
            percentage=(final_score / Decimal("10")) * 100,
            rag_status=rag_status,
            contributing_scores=criteria_scores,
            gap_count=len(gaps),
            critical_gaps=critical_gaps,
            improvement_priority=self._calculate_improvement_priority(final_score, len(critical_gaps))
        )
    
    def assess_pillar(self, pillar: PillarType, requirement_scores: List[AggregatedScore],
                     methodology: str = "standard") -> AggregatedScore:
        """Assess a pillar based on requirement scores"""
        if not requirement_scores:
            return AggregatedScore(
                level="pillar",
                entity_id=pillar.value,
                entity_name=pillar.value.replace("_", " ").title(),
                score=Decimal("0"),
                max_score=Decimal("10"),
                percentage=Decimal("0"),
                rag_status=RAGStatus.NOT_ASSESSED
            )
        
        # Calculate average score (could be weighted by requirement importance)
        total_score = sum(score.score for score in requirement_scores)
        average_score = total_score / len(requirement_scores)
        average_score = average_score.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        
        # Calculate RAG status
        rag_status = self.calculate_rag_status(average_score, Decimal("10"), methodology)
        
        # Aggregate gaps
        all_gaps = []
        critical_gaps = []
        for req_score in requirement_scores:
            all_gaps.extend(req_score.critical_gaps)
            if req_score.rag_status == RAGStatus.RED:
                critical_gaps.extend(req_score.critical_gaps)
        
        return AggregatedScore(
            level="pillar",
            entity_id=pillar.value,
            entity_name=pillar.value.replace("_", " ").title(),
            score=average_score,
            max_score=Decimal("10"),
            percentage=(average_score / Decimal("10")) * 100,
            rag_status=rag_status,
            gap_count=len(all_gaps),
            critical_gaps=critical_gaps,
            improvement_priority=self._calculate_improvement_priority(average_score, len(critical_gaps))
        )
    
    def assess_overall_compliance(self, pillar_scores: List[AggregatedScore],
                                methodology: str = "standard") -> AggregatedScore:
        """Calculate overall compliance score based on pillar scores"""
        if not pillar_scores:
            return AggregatedScore(
                level="overall",
                entity_id="dora_overall",
                entity_name="DORA Overall Compliance",
                score=Decimal("0"),
                max_score=Decimal("10"),
                percentage=Decimal("0"),
                rag_status=RAGStatus.NOT_ASSESSED
            )
        
        # Calculate weighted average based on pillar weights
        total_weighted_score = Decimal("0")
        total_weight = Decimal("0")
        
        for pillar_score in pillar_scores:
            pillar_type = PillarType(pillar_score.entity_id)
            weight = self.pillar_weights.get(pillar_type, Decimal("0.2"))
            total_weighted_score += pillar_score.score * weight
            total_weight += weight
        
        overall_score = total_weighted_score / total_weight if total_weight > 0 else Decimal("0")
        overall_score = overall_score.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        
        # Calculate RAG status
        rag_status = self.calculate_rag_status(overall_score, Decimal("10"), methodology)
        
        # Aggregate critical gaps
        all_critical_gaps = []
        for pillar_score in pillar_scores:
            all_critical_gaps.extend(pillar_score.critical_gaps)
        
        return AggregatedScore(
            level="overall",
            entity_id="dora_overall",
            entity_name="DORA Overall Compliance",
            score=overall_score,
            max_score=Decimal("10"),
            percentage=(overall_score / Decimal("10")) * 100,
            rag_status=rag_status,
            gap_count=sum(ps.gap_count for ps in pillar_scores),
            critical_gaps=all_critical_gaps[:10],  # Top 10 critical gaps
            improvement_priority=self._calculate_improvement_priority(overall_score, len(all_critical_gaps))
        )
    
    def _calculate_improvement_priority(self, score: Decimal, critical_gap_count: int) -> int:
        """Calculate improvement priority (1=highest, 5=lowest)"""
        if score < Decimal("5.0") or critical_gap_count > 5:
            return 1  # Critical
        elif score < Decimal("7.0") or critical_gap_count > 2:
            return 2  # High
        elif score < Decimal("8.5") or critical_gap_count > 0:
            return 3  # Medium
        elif score < Decimal("9.5"):
            return 4  # Low
        else:
            return 5  # Minimal
    
    def generate_gap_analysis(self, assessment_scores: List[AggregatedScore]) -> Dict[str, Any]:
        """Generate comprehensive gap analysis"""
        logger.info("Generating gap analysis...")
        
        gap_analysis = {
            "overall_summary": {},
            "pillar_analysis": {},
            "critical_gaps": [],
            "improvement_recommendations": [],
            "priority_matrix": [],
            "trend_analysis": {}
        }
        
        # Overall summary
        overall_score = next((score for score in assessment_scores if score.level == "overall"), None)
        if overall_score:
            gap_analysis["overall_summary"] = {
                "score": float(overall_score.score),
                "percentage": float(overall_score.percentage),
                "rag_status": overall_score.rag_status.value,
                "total_gaps": overall_score.gap_count,
                "critical_gaps": len(overall_score.critical_gaps),
                "improvement_priority": overall_score.improvement_priority
            }
        
        # Pillar analysis
        pillar_scores = [score for score in assessment_scores if score.level == "pillar"]
        for pillar_score in pillar_scores:
            gap_analysis["pillar_analysis"][pillar_score.entity_id] = {
                "name": pillar_score.entity_name,
                "score": float(pillar_score.score),
                "rag_status": pillar_score.rag_status.value,
                "gap_count": pillar_score.gap_count,
                "critical_gaps": pillar_score.critical_gaps[:5],  # Top 5
                "priority": pillar_score.improvement_priority
            }
        
        # Critical gaps across all levels
        all_critical_gaps = []
        for score in assessment_scores:
            for gap in score.critical_gaps:
                all_critical_gaps.append({
                    "gap": gap,
                    "level": score.level,
                    "entity": score.entity_name,
                    "impact": self._assess_gap_impact(gap, score.rag_status)
                })
        
        # Sort by impact and take top 20
        gap_analysis["critical_gaps"] = sorted(
            all_critical_gaps, 
            key=lambda x: x["impact"], 
            reverse=True
        )[:20]
        
        # Generate improvement recommendations
        gap_analysis["improvement_recommendations"] = self._generate_improvement_recommendations(
            assessment_scores
        )
        
        # Priority matrix
        gap_analysis["priority_matrix"] = self._create_priority_matrix(pillar_scores)
        
        logger.info(f"Gap analysis completed. Found {len(gap_analysis['critical_gaps'])} critical gaps")
        return gap_analysis
    
    def _assess_gap_impact(self, gap: str, rag_status: RAGStatus) -> int:
        """Assess the impact of a gap (1-10 scale)"""
        base_impact = 5
        
        # Adjust for RAG status
        if rag_status == RAGStatus.RED:
            base_impact += 3
        elif rag_status == RAGStatus.AMBER:
            base_impact += 1
        
        # Adjust for gap keywords
        high_impact_keywords = ["critical", "missing", "no", "absent", "inadequate"]
        medium_impact_keywords = ["limited", "basic", "partial", "gaps"]
        
        gap_lower = gap.lower()
        if any(keyword in gap_lower for keyword in high_impact_keywords):
            base_impact += 2
        elif any(keyword in gap_lower for keyword in medium_impact_keywords):
            base_impact += 1
        
        return min(base_impact, 10)
    
    def _generate_improvement_recommendations(self, assessment_scores: List[AggregatedScore]) -> List[Dict[str, Any]]:
        """Generate prioritized improvement recommendations"""
        recommendations = []
        
        # Sort by priority and score
        sorted_scores = sorted(assessment_scores, key=lambda x: (x.improvement_priority, x.score))
        
        for score in sorted_scores[:10]:  # Top 10 recommendations
            if score.improvement_priority <= 3:  # Only for high priority items
                recommendations.append({
                    "entity": score.entity_name,
                    "level": score.level,
                    "current_score": float(score.score),
                    "rag_status": score.rag_status.value,
                    "priority": score.improvement_priority,
                    "recommendation": self._generate_specific_recommendation(score),
                    "estimated_effort": self._estimate_effort(score),
                    "expected_improvement": self._estimate_improvement(score)
                })
        
        return recommendations
    
    def _generate_specific_recommendation(self, score: AggregatedScore) -> str:
        """Generate specific recommendation based on score"""
        if score.rag_status == RAGStatus.RED:
            return f"Immediate attention required for {score.entity_name}. Address critical gaps in {', '.join(score.critical_gaps[:3])}"
        elif score.rag_status == RAGStatus.AMBER:
            return f"Strengthen {score.entity_name} by addressing {score.gap_count} identified gaps"
        else:
            return f"Optimize {score.entity_name} to achieve excellence level"
    
    def _estimate_effort(self, score: AggregatedScore) -> str:
        """Estimate implementation effort"""
        if score.score < Decimal("5.0"):
            return "High"
        elif score.score < Decimal("7.5"):
            return "Medium"
        else:
            return "Low"
    
    def _estimate_improvement(self, score: AggregatedScore) -> str:
        """Estimate potential improvement"""
        potential = Decimal("10") - score.score
        if potential > Decimal("4"):
            return "Significant"
        elif potential > Decimal("2"):
            return "Moderate"
        else:
            return "Minor"
    
    def _create_priority_matrix(self, pillar_scores: List[AggregatedScore]) -> List[Dict[str, Any]]:
        """Create effort vs impact priority matrix"""
        matrix = []
        
        for pillar_score in pillar_scores:
            impact = 10 - float(pillar_score.score)  # Higher impact for lower scores
            effort = self._estimate_effort_numeric(pillar_score)
            
            matrix.append({
                "pillar": pillar_score.entity_name,
                "impact": impact,
                "effort": effort,
                "priority_quadrant": self._determine_quadrant(impact, effort),
                "recommendation": self._quadrant_recommendation(impact, effort)
            })
        
        return sorted(matrix, key=lambda x: x["impact"], reverse=True)
    
    def _estimate_effort_numeric(self, score: AggregatedScore) -> float:
        """Estimate effort numerically (1-10 scale)"""
        if score.score < Decimal("5.0"):
            return 8.0  # High effort
        elif score.score < Decimal("7.5"):
            return 5.0  # Medium effort
        else:
            return 2.0  # Low effort
    
    def _determine_quadrant(self, impact: float, effort: float) -> str:
        """Determine priority matrix quadrant"""
        if impact >= 5 and effort <= 5:
            return "Quick Wins"
        elif impact >= 5 and effort > 5:
            return "Major Projects"
        elif impact < 5 and effort <= 5:
            return "Fill-ins"
        else:
            return "Thankless Tasks"
    
    def _quadrant_recommendation(self, impact: float, effort: float) -> str:
        """Provide recommendation based on quadrant"""
        quadrant = self._determine_quadrant(impact, effort)
        
        recommendations = {
            "Quick Wins": "Implement immediately - high impact, low effort",
            "Major Projects": "Plan carefully - high impact but requires significant resources",
            "Fill-ins": "Consider when resources are available - low impact, low effort",
            "Thankless Tasks": "Deprioritize - low impact, high effort"
        }
        
        return recommendations.get(quadrant, "Assess further")
    
    def save_assessment_to_database(self, assessment_scores: List[AggregatedScore], 
                                  gap_analysis: Dict[str, Any],
                                  assessment_id: str = None) -> str:
        """Save assessment results to database"""
        if not assessment_id:
            assessment_id = str(uuid4())
        
        logger.info(f"Saving assessment {assessment_id} to database...")
        
        with self.Session() as session:
            try:
                # Save main assessment
                assessment = ComplianceAssessment(
                    assessment_id=assessment_id,
                    assessment_date=datetime.now().date(),
                    methodology="standard",
                    overall_score=next((s.score for s in assessment_scores if s.level == "overall"), Decimal("0")),
                    rag_status=next((s.rag_status for s in assessment_scores if s.level == "overall"), RAGStatus.NOT_ASSESSED),
                    gap_analysis=gap_analysis,
                    recommendations=[rec["recommendation"] for rec in gap_analysis.get("improvement_recommendations", [])]
                )
                session.add(assessment)
                
                # Save individual scores
                for score in assessment_scores:
                    assessment_score = AssessmentScore(
                        assessment_id=assessment_id,
                        entity_type=score.level,
                        entity_id=score.entity_id,
                        score=score.score,
                        max_score=score.max_score,
                        rag_status=score.rag_status,
                        gap_count=score.gap_count,
                        improvement_priority=score.improvement_priority
                    )
                    session.add(assessment_score)
                
                session.commit()
                logger.info(f"Assessment {assessment_id} saved successfully")
                return assessment_id
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error saving assessment: {e}")
                raise
    
    def generate_scoring_report(self, assessment_scores: List[AggregatedScore],
                              gap_analysis: Dict[str, Any]) -> str:
        """Generate comprehensive scoring report"""
        report = f"""
# DORA Compliance Assessment Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
"""
        
        overall_score = next((score for score in assessment_scores if score.level == "overall"), None)
        if overall_score:
            report += f"""
- **Overall Compliance Score**: {overall_score.score}/10 ({overall_score.percentage:.1f}%)
- **RAG Status**: {overall_score.rag_status.value.upper()}
- **Total Gaps Identified**: {overall_score.gap_count}
- **Critical Gaps**: {len(overall_score.critical_gaps)}
- **Improvement Priority**: {overall_score.improvement_priority}/5
"""
        
        # Pillar breakdown
        report += f"\n## DORA Pillar Breakdown\n"
        pillar_scores = [score for score in assessment_scores if score.level == "pillar"]
        for pillar_score in sorted(pillar_scores, key=lambda x: x.score, reverse=True):
            status_emoji = {"green": "🟢", "amber": "🟡", "red": "🔴"}.get(pillar_score.rag_status.value, "⚪")
            report += f"- **{pillar_score.entity_name}**: {pillar_score.score}/10 {status_emoji} ({pillar_score.gap_count} gaps)\n"
        
        # Critical gaps
        if gap_analysis.get("critical_gaps"):
            report += f"\n## Critical Gaps Requiring Immediate Attention\n"
            for i, gap in enumerate(gap_analysis["critical_gaps"][:5], 1):
                report += f"{i}. **{gap['entity']}**: {gap['gap']} (Impact: {gap['impact']}/10)\n"
        
        # Improvement recommendations
        if gap_analysis.get("improvement_recommendations"):
            report += f"\n## Priority Improvement Recommendations\n"
            for i, rec in enumerate(gap_analysis["improvement_recommendations"][:5], 1):
                report += f"{i}. **{rec['entity']}** ({rec['rag_status'].upper()})\n"
                report += f"   - Current Score: {rec['current_score']}/10\n"
                report += f"   - Recommendation: {rec['recommendation']}\n"
                report += f"   - Estimated Effort: {rec['estimated_effort']}\n\n"
        
        # Priority matrix
        if gap_analysis.get("priority_matrix"):
            report += f"\n## Priority Matrix (Effort vs Impact)\n"
            for item in gap_analysis["priority_matrix"]:
                report += f"- **{item['pillar']}**: {item['priority_quadrant']} - {item['recommendation']}\n"
        
        report += f"\n## Next Steps\n"
        report += f"1. Address critical gaps identified in high-priority areas\n"
        report += f"2. Implement quick wins for immediate improvement\n"
        report += f"3. Plan major projects for significant compliance enhancement\n"
        report += f"4. Establish regular reassessment schedule\n"
        report += f"5. Monitor progress against improvement recommendations\n"
        
        return report


def main():
    """Main function for scoring engine demonstration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DORA Compliance Scoring Engine")
    parser.add_argument("--create-rubrics", action="store_true", help="Create scoring rubrics")
    parser.add_argument("--demo-scoring", action="store_true", help="Demonstrate scoring capabilities")
    parser.add_argument("--generate-report", action="store_true", help="Generate assessment report")
    parser.add_argument("--database-url", default="postgresql://postgres:password@localhost:5432/dora_kb")
    
    args = parser.parse_args()
    
    # Initialize scoring engine
    engine = DORAComplianceScoringEngine(args.database_url)
    
    try:
        if args.create_rubrics:
            # Create scoring rubrics
            rubrics = engine.create_scoring_rubrics()
            print(f"Created scoring rubrics for {len(rubrics)} domains")
            
            for domain, criteria_list in rubrics.items():
                print(f"\n{domain.title()}: {len(criteria_list)} criteria")
                for criteria in criteria_list[:2]:  # Show first 2
                    print(f"  - {criteria.name} (Weight: {criteria.weight})")
        
        if args.demo_scoring:
            # Demonstrate scoring with sample data
            print("Demonstrating scoring capabilities...")
            
            # Create sample score results
            sample_scores = [
                ScoreResult(
                    criteria_id="gov_framework_01",
                    score=Decimal("7.5"),
                    max_score=Decimal("10"),
                    rag_status=RAGStatus.AMBER,
                    confidence=AssessmentConfidence.HIGH,
                    gaps_identified=["Missing annual review documentation"]
                ),
                ScoreResult(
                    criteria_id="gov_resources_01",
                    score=Decimal("6.0"),
                    max_score=Decimal("10"),
                    rag_status=RAGStatus.AMBER,
                    confidence=AssessmentConfidence.MEDIUM,
                    gaps_identified=["Insufficient dedicated resources"]
                )
            ]
            
            # Assess requirement
            req_score = engine.assess_requirement("req_5_1", sample_scores)
            print(f"Requirement Score: {req_score.score}/10 ({req_score.rag_status.value})")
            
            # Create sample pillar assessment
            pillar_score = engine.assess_pillar(PillarType.GOVERNANCE_ARRANGEMENTS, [req_score])
            print(f"Pillar Score: {pillar_score.score}/10 ({pillar_score.rag_status.value})")
            
            # Overall assessment
            overall_score = engine.assess_overall_compliance([pillar_score])
            print(f"Overall Score: {overall_score.score}/10 ({overall_score.rag_status.value})")
            
            # Generate gap analysis
            gap_analysis = engine.generate_gap_analysis([req_score, pillar_score, overall_score])
            print(f"Gap Analysis: {len(gap_analysis['critical_gaps'])} critical gaps identified")
        
        if args.generate_report:
            # Generate sample report
            print("Generating assessment report...")
            
            # Create sample assessment scores
            sample_assessment = [
                AggregatedScore(
                    level="overall",
                    entity_id="dora_overall",
                    entity_name="DORA Overall Compliance",
                    score=Decimal("7.2"),
                    max_score=Decimal("10"),
                    percentage=Decimal("72.0"),
                    rag_status=RAGStatus.AMBER,
                    gap_count=15,
                    critical_gaps=["Missing framework approval", "Inadequate resources"]
                )
            ]
            
            gap_analysis = engine.generate_gap_analysis(sample_assessment)
            report = engine.generate_scoring_report(sample_assessment, gap_analysis)
            
            # Save report
            report_path = Path("dora-knowledge-base/reports/assessment_report.md")
            report_path.parent.mkdir(exist_ok=True)
            with open(report_path, 'w') as f:
                f.write(report)
            
            print(f"Assessment report saved to: {report_path}")
        
        logger.info("Scoring engine operations completed successfully")
        
    except Exception as e:
        logger.error(f"Scoring engine operations failed: {e}")
        raise


if __name__ == "__main__":
    main() 