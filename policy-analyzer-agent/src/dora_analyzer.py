#!/usr/bin/env python3
"""
Policy Analyzer Agent - DORA Compliance Analysis Engine

This module provides the core business logic for analyzing policy documents
against DORA requirements, integrating all components to deliver comprehensive
compliance assessments and actionable recommendations.

Features:
- Complete DORA compliance analysis workflow
- Integration with knowledge base and AI models
- Multi-pillar assessment and scoring
- Gap identification and prioritization
- Risk-based recommendations
- Executive-ready reporting
- Real-time analysis capabilities
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from uuid import uuid4

# Import our core components
from .document_processor import DocumentProcessor, ProcessedDocument
from .text_extractor import PolicyTextExtractor, PolicyStructure, ExtractionResult
from .nlp_analyzer import PolicyNLPAnalyzer, ComplianceAssessment, AnalysisResult

# Import knowledge base components
sys.path.append(str(Path(__file__).parent.parent.parent / "dora-knowledge-base"))
from data.dora_content_extractor import DORAContentExtractor
from assessment.scoring_engine import DORAComplianceScoringEngine, RAGStatus
from data.regulatory_mapper import DORARegulatoryMapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceLevel(Enum):
    """Overall compliance levels"""
    COMPLIANT = "compliant"
    LARGELY_COMPLIANT = "largely_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    UNABLE_TO_ASSESS = "unable_to_assess"

class RiskPriority(Enum):
    """Risk priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"

@dataclass
class DORARequirement:
    """DORA requirement structure"""
    requirement_id: str
    article: str
    pillar: str
    title: str
    description: str
    requirement_text: str
    mandatory_level: str  # "shall", "should", "may"
    implementation_guidance: str
    evidence_requirements: List[str]
    assessment_criteria: List[str]

@dataclass
class ComplianceGap:
    """Individual compliance gap"""
    gap_id: str
    requirement_id: str
    gap_type: str  # "missing", "insufficient", "unclear", "conflicting"
    severity: RiskPriority
    description: str
    evidence: List[str]
    impact_assessment: str
    recommendations: List[str]
    estimated_effort: str  # "low", "medium", "high"
    timeline_suggestion: str

@dataclass
class PillarAssessment:
    """Assessment for individual DORA pillar"""
    pillar_name: str
    overall_score: Decimal
    compliance_level: ComplianceLevel
    rag_status: RAGStatus
    requirements_assessed: int
    requirements_compliant: int
    gaps_identified: List[ComplianceGap]
    strengths: List[str]
    key_findings: List[str]
    priority_actions: List[str]

@dataclass
class DORAComplianceReport:
    """Complete DORA compliance analysis report"""
    report_id: str
    document_id: str
    document_title: str
    analysis_date: datetime
    overall_compliance_level: ComplianceLevel
    overall_score: Decimal
    overall_rag_status: RAGStatus
    
    # Pillar assessments
    pillar_assessments: Dict[str, PillarAssessment]
    
    # Overall findings
    total_requirements: int
    compliant_requirements: int
    compliance_percentage: Decimal
    total_gaps: int
    critical_gaps: int
    high_risk_gaps: int
    
    # Recommendations
    executive_summary: str
    key_strengths: List[str]
    critical_findings: List[str]
    immediate_actions: List[str]
    remediation_roadmap: List[str]
    
    # Processing metadata
    processing_time: float
    confidence_score: float
    models_used: List[str]
    
    # Supporting data
    detailed_assessments: List[ComplianceAssessment]
    cross_regulatory_insights: Optional[Dict[str, Any]] = None

class DORAComplianceAnalyzer:
    """Main DORA compliance analysis engine"""
    
    # DORA pillar mappings
    DORA_PILLARS = {
        "governance_arrangements": "Pillar 1: ICT Risk Management and Governance Arrangements",
        "ict_related_incidents": "Pillar 2: ICT-Related Incident Management",
        "digital_operational_resilience_testing": "Pillar 3: Digital Operational Resilience Testing",
        "ict_third_party_risk": "Pillar 4: ICT Third-Party Risk Management",
        "information_sharing": "Pillar 5: Information and Intelligence Sharing"
    }
    
    # Compliance level thresholds
    COMPLIANCE_THRESHOLDS = {
        ComplianceLevel.COMPLIANT: 0.90,
        ComplianceLevel.LARGELY_COMPLIANT: 0.75,
        ComplianceLevel.PARTIALLY_COMPLIANT: 0.50,
        ComplianceLevel.NON_COMPLIANT: 0.25
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the DORA compliance analyzer
        
        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        
        # Initialize core components
        self.document_processor = DocumentProcessor()
        self.text_extractor = PolicyTextExtractor()
        self.nlp_analyzer = PolicyNLPAnalyzer()
        self.scoring_engine = DORAComplianceScoringEngine()
        self.regulatory_mapper = DORARegulatoryMapper()
        
        # Initialize DORA knowledge base
        self.dora_extractor = DORAContentExtractor()
        self._load_dora_requirements()
        
        # Analysis statistics
        self.analysis_stats = {
            'documents_analyzed': 0,
            'total_processing_time': 0.0,
            'avg_processing_time': 0.0,
            'compliance_distribution': {}
        }
    
    def _load_dora_requirements(self):
        """Load DORA requirements from knowledge base"""
        try:
            # Extract DORA requirements using our knowledge base
            self.dora_requirements = self.dora_extractor.extract_requirements()
            logger.info(f"Loaded {len(self.dora_requirements)} DORA requirements")
        except Exception as e:
            logger.warning(f"Could not load DORA requirements from knowledge base: {e}")
            # Fallback to essential requirements
            self.dora_requirements = self._get_essential_dora_requirements()
    
    def _get_essential_dora_requirements(self) -> List[DORARequirement]:
        """Get essential DORA requirements as fallback"""
        return [
            DORARequirement(
                requirement_id="req_5_1",
                article="Article 5",
                pillar="governance_arrangements", 
                title="ICT Risk Management Framework",
                description="Maintain ICT risk management framework",
                requirement_text="Financial entities shall maintain a sound, comprehensive and well-documented ICT risk management framework",
                mandatory_level="shall",
                implementation_guidance="Establish board-approved framework with regular reviews",
                evidence_requirements=["ICT risk management policy", "Board approval", "Regular reviews"],
                assessment_criteria=["Framework comprehensiveness", "Documentation quality", "Board oversight"]
            ),
            DORARequirement(
                requirement_id="req_17_1",
                article="Article 17",
                pillar="ict_related_incidents",
                title="Incident Management Process",
                description="Establish ICT-related incident management process",
                requirement_text="Financial entities shall define, establish and implement an ICT-related incident management process",
                mandatory_level="shall",
                implementation_guidance="Define clear processes for incident detection, response, and recovery",
                evidence_requirements=["Incident management procedure", "Incident classification", "Response procedures"],
                assessment_criteria=["Process comprehensiveness", "Response capability", "Recovery procedures"]
            ),
            DORARequirement(
                requirement_id="req_24_1", 
                article="Article 24",
                pillar="digital_operational_resilience_testing",
                title="Testing Programme",
                description="Establish digital operational resilience testing programme",
                requirement_text="Financial entities shall establish a comprehensive digital operational resilience testing programme",
                mandatory_level="shall",
                implementation_guidance="Regular testing of ICT systems and operational procedures",
                evidence_requirements=["Testing programme", "Test results", "Remediation plans"],
                assessment_criteria=["Testing comprehensiveness", "Regular execution", "Follow-up actions"]
            ),
            DORARequirement(
                requirement_id="req_28_1",
                article="Article 28", 
                pillar="ict_third_party_risk",
                title="Third-Party Risk Assessment",
                description="Assess ICT third-party service provider risks",
                requirement_text="Financial entities shall assess and address ICT concentration risk and ICT third-party dependencies",
                mandatory_level="shall",
                implementation_guidance="Comprehensive risk assessment of all ICT service providers",
                evidence_requirements=["Third-party risk assessments", "Concentration analysis", "Mitigation measures"],
                assessment_criteria=["Risk assessment quality", "Concentration identification", "Mitigation effectiveness"]
            )
        ]
    
    async def analyze_document(self, file_path: Union[str, Path]) -> DORAComplianceReport:
        """
        Perform complete DORA compliance analysis on a policy document
        
        Args:
            file_path: Path to the policy document
            
        Returns:
            Complete DORA compliance report
        """
        start_time = datetime.now()
        
        logger.info(f"Starting DORA compliance analysis for: {Path(file_path).name}")
        
        try:
            # Step 1: Process document
            processed_doc = self.document_processor.process_document(file_path)
            logger.info(f"Document processed: {processed_doc.quality_score:.2f} quality score")
            
            # Step 2: Extract and structure policy content
            extraction_result = self.text_extractor.extract_and_structure(processed_doc)
            policy_structure = extraction_result.policy_structure
            logger.info(f"Text extraction completed: {len(policy_structure.elements)} policy elements")
            
            # Step 3: Analyze compliance against DORA requirements
            detailed_assessments = await self.nlp_analyzer.analyze_compliance(
                policy_structure, 
                [self._requirement_to_dict(req) for req in self.dora_requirements]
            )
            logger.info(f"Compliance analysis completed: {len(detailed_assessments)} assessments")
            
            # Step 4: Generate pillar assessments
            pillar_assessments = self._generate_pillar_assessments(detailed_assessments)
            
            # Step 5: Calculate overall compliance
            overall_assessment = self._calculate_overall_compliance(pillar_assessments, detailed_assessments)
            
            # Step 6: Identify gaps and generate recommendations
            gaps = self._identify_compliance_gaps(detailed_assessments)
            recommendations = self._generate_recommendations(gaps, pillar_assessments)
            
            # Step 7: Generate cross-regulatory insights (if available)
            cross_regulatory_insights = await self._generate_cross_regulatory_insights(policy_structure)
            
            # Step 8: Create comprehensive report
            processing_time = (datetime.now() - start_time).total_seconds()
            
            report = DORAComplianceReport(
                report_id=str(uuid4()),
                document_id=processed_doc.document_id,
                document_title=processed_doc.metadata.filename,
                analysis_date=datetime.now(),
                overall_compliance_level=overall_assessment['compliance_level'],
                overall_score=overall_assessment['score'],
                overall_rag_status=overall_assessment['rag_status'],
                pillar_assessments=pillar_assessments,
                total_requirements=len(detailed_assessments),
                compliant_requirements=len([a for a in detailed_assessments if a.compliance_status == 'compliant']),
                compliance_percentage=overall_assessment['compliance_percentage'],
                total_gaps=len(gaps),
                critical_gaps=len([g for g in gaps if g.severity == RiskPriority.CRITICAL]),
                high_risk_gaps=len([g for g in gaps if g.severity == RiskPriority.HIGH]),
                executive_summary=recommendations['executive_summary'],
                key_strengths=recommendations['strengths'],
                critical_findings=recommendations['critical_findings'],
                immediate_actions=recommendations['immediate_actions'],
                remediation_roadmap=recommendations['roadmap'],
                processing_time=processing_time,
                confidence_score=self._calculate_analysis_confidence(detailed_assessments),
                models_used=self._get_models_used(),
                detailed_assessments=detailed_assessments,
                cross_regulatory_insights=cross_regulatory_insights
            )
            
            # Update statistics
            self._update_analysis_stats(report)
            
            logger.info(f"DORA compliance analysis completed in {processing_time:.2f}s. "
                       f"Overall compliance: {report.compliance_percentage:.1f}%")
            
            return report
            
        except Exception as e:
            logger.error(f"Error in DORA compliance analysis: {e}")
            raise
    
    def _requirement_to_dict(self, req: DORARequirement) -> Dict[str, Any]:
        """Convert DORARequirement to dictionary for NLP analyzer"""
        return {
            'id': req.requirement_id,
            'text': req.requirement_text,
            'article': req.article,
            'pillar': req.pillar,
            'mandatory_level': req.mandatory_level,
            'title': req.title,
            'description': req.description
        }
    
    def _generate_pillar_assessments(self, detailed_assessments: List[ComplianceAssessment]) -> Dict[str, PillarAssessment]:
        """Generate assessments for each DORA pillar"""
        pillar_assessments = {}
        
        # Group assessments by pillar
        pillar_groups = {}
        for assessment in detailed_assessments:
            # Find requirement to get pillar
            req = next((r for r in self.dora_requirements if r.requirement_id == assessment.requirement_id), None)
            if req:
                pillar = req.pillar
                if pillar not in pillar_groups:
                    pillar_groups[pillar] = []
                pillar_groups[pillar].append(assessment)
        
        # Generate assessment for each pillar
        for pillar, assessments in pillar_groups.items():
            pillar_assessment = self._assess_pillar(pillar, assessments)
            pillar_assessments[pillar] = pillar_assessment
        
        return pillar_assessments
    
    def _assess_pillar(self, pillar: str, assessments: List[ComplianceAssessment]) -> PillarAssessment:
        """Assess individual pillar"""
        # Calculate pillar score
        total_assessments = len(assessments)
        compliant_count = len([a for a in assessments if a.compliance_status == 'compliant'])
        largely_compliant_count = len([a for a in assessments if a.compliance_status == 'partial'])
        
        # Weighted scoring
        score = Decimal('0')
        if total_assessments > 0:
            compliant_weight = Decimal('1.0')
            partial_weight = Decimal('0.6')
            score = (compliant_count * compliant_weight + largely_compliant_count * partial_weight) / total_assessments
        
        # Determine compliance level
        compliance_level = self._score_to_compliance_level(float(score))
        
        # Determine RAG status
        rag_status = self._score_to_rag_status(float(score))
        
        # Identify gaps
        gaps = []
        for assessment in assessments:
            if assessment.compliance_status != 'compliant':
                gap = ComplianceGap(
                    gap_id=f"gap_{assessment.requirement_id}",
                    requirement_id=assessment.requirement_id,
                    gap_type=assessment.compliance_status,
                    severity=self._determine_gap_severity(assessment),
                    description=assessment.gap_description or "Compliance gap identified",
                    evidence=assessment.evidence_text,
                    impact_assessment=self._assess_gap_impact(assessment),
                    recommendations=assessment.recommendations,
                    estimated_effort=self._estimate_remediation_effort(assessment),
                    timeline_suggestion=self._suggest_timeline(assessment)
                )
                gaps.append(gap)
        
        # Generate pillar-specific insights
        strengths = self._identify_pillar_strengths(assessments)
        key_findings = self._generate_pillar_findings(assessments, gaps)
        priority_actions = self._prioritize_pillar_actions(gaps)
        
        return PillarAssessment(
            pillar_name=self.DORA_PILLARS.get(pillar, pillar),
            overall_score=score,
            compliance_level=compliance_level,
            rag_status=rag_status,
            requirements_assessed=total_assessments,
            requirements_compliant=compliant_count,
            gaps_identified=gaps,
            strengths=strengths,
            key_findings=key_findings,
            priority_actions=priority_actions
        )
    
    def _calculate_overall_compliance(self, pillar_assessments: Dict[str, PillarAssessment], 
                                    detailed_assessments: List[ComplianceAssessment]) -> Dict[str, Any]:
        """Calculate overall compliance metrics"""
        if not pillar_assessments:
            return {
                'compliance_level': ComplianceLevel.UNABLE_TO_ASSESS,
                'score': Decimal('0'),
                'rag_status': RAGStatus.NOT_ASSESSED,
                'compliance_percentage': Decimal('0')
            }
        
        # Calculate weighted average score across pillars
        total_score = sum(assessment.overall_score for assessment in pillar_assessments.values())
        avg_score = total_score / len(pillar_assessments)
        
        # Calculate compliance percentage
        total_requirements = len(detailed_assessments)
        compliant_requirements = len([a for a in detailed_assessments if a.compliance_status == 'compliant'])
        compliance_percentage = Decimal(compliant_requirements) / Decimal(total_requirements) * 100 if total_requirements > 0 else Decimal('0')
        
        # Determine overall compliance level
        compliance_level = self._score_to_compliance_level(float(avg_score))
        
        # Determine RAG status
        rag_status = self._score_to_rag_status(float(avg_score))
        
        return {
            'compliance_level': compliance_level,
            'score': avg_score,
            'rag_status': rag_status,
            'compliance_percentage': compliance_percentage
        }
    
    def _identify_compliance_gaps(self, detailed_assessments: List[ComplianceAssessment]) -> List[ComplianceGap]:
        """Identify all compliance gaps"""
        gaps = []
        
        for assessment in detailed_assessments:
            if assessment.compliance_status != 'compliant':
                gap = ComplianceGap(
                    gap_id=f"gap_{assessment.requirement_id}",
                    requirement_id=assessment.requirement_id,
                    gap_type=assessment.compliance_status,
                    severity=self._determine_gap_severity(assessment),
                    description=assessment.gap_description or "Compliance gap identified",
                    evidence=assessment.evidence_text,
                    impact_assessment=self._assess_gap_impact(assessment),
                    recommendations=assessment.recommendations,
                    estimated_effort=self._estimate_remediation_effort(assessment),
                    timeline_suggestion=self._suggest_timeline(assessment)
                )
                gaps.append(gap)
        
        # Sort gaps by severity
        severity_order = [RiskPriority.CRITICAL, RiskPriority.HIGH, RiskPriority.MEDIUM, RiskPriority.LOW]
        gaps.sort(key=lambda g: severity_order.index(g.severity))
        
        return gaps
    
    def _generate_recommendations(self, gaps: List[ComplianceGap], 
                                pillar_assessments: Dict[str, PillarAssessment]) -> Dict[str, Any]:
        """Generate comprehensive recommendations"""
        # Executive summary
        total_gaps = len(gaps)
        critical_gaps = len([g for g in gaps if g.severity == RiskPriority.CRITICAL])
        high_gaps = len([g for g in gaps if g.severity == RiskPriority.HIGH])
        
        if critical_gaps > 0:
            executive_summary = f"Critical compliance gaps identified ({critical_gaps} critical, {high_gaps} high priority). Immediate action required to address regulatory exposure."
        elif high_gaps > 0:
            executive_summary = f"Significant compliance gaps identified ({high_gaps} high priority). Targeted improvements needed to meet DORA requirements."
        elif total_gaps > 0:
            executive_summary = f"Good overall compliance with minor gaps ({total_gaps} identified). Focus on continuous improvement and documentation enhancement."
        else:
            executive_summary = "Strong compliance posture with all assessed requirements met. Maintain current controls and monitor regulatory developments."
        
        # Identify strengths
        strengths = []
        for pillar, assessment in pillar_assessments.items():
            if assessment.compliance_level in [ComplianceLevel.COMPLIANT, ComplianceLevel.LARGELY_COMPLIANT]:
                strengths.extend(assessment.strengths)
        
        # Critical findings
        critical_findings = []
        for gap in gaps:
            if gap.severity in [RiskPriority.CRITICAL, RiskPriority.HIGH]:
                critical_findings.append(f"{gap.requirement_id}: {gap.description}")
        
        # Immediate actions
        immediate_actions = []
        for gap in gaps[:5]:  # Top 5 priority gaps
            if gap.recommendations:
                immediate_actions.extend(gap.recommendations[:2])  # Top 2 recommendations per gap
        
        # Remediation roadmap
        roadmap = self._create_remediation_roadmap(gaps)
        
        return {
            'executive_summary': executive_summary,
            'strengths': strengths[:10],  # Top 10 strengths
            'critical_findings': critical_findings[:10],  # Top 10 critical findings
            'immediate_actions': immediate_actions[:10],  # Top 10 immediate actions
            'roadmap': roadmap
        }
    
    async def _generate_cross_regulatory_insights(self, policy_structure: PolicyStructure) -> Optional[Dict[str, Any]]:
        """Generate cross-regulatory compliance insights"""
        try:
            # Use regulatory mapper to identify cross-regulatory opportunities
            mappings = self.regulatory_mapper.create_regulatory_mappings()
            gap_analysis = self.regulatory_mapper.analyze_regulatory_gaps(mappings)
            
            return {
                'frameworks_mapped': len(mappings),
                'efficiency_opportunities': len(gap_analysis.get('compliance_efficiency_opportunities', [])),
                'high_overlap_areas': len(gap_analysis.get('high_overlap_areas', [])),
                'insights': "Cross-regulatory analysis completed. See detailed mapping report for efficiency opportunities."
            }
        except Exception as e:
            logger.warning(f"Could not generate cross-regulatory insights: {e}")
            return None
    
    def _score_to_compliance_level(self, score: float) -> ComplianceLevel:
        """Convert score to compliance level"""
        if score >= self.COMPLIANCE_THRESHOLDS[ComplianceLevel.COMPLIANT]:
            return ComplianceLevel.COMPLIANT
        elif score >= self.COMPLIANCE_THRESHOLDS[ComplianceLevel.LARGELY_COMPLIANT]:
            return ComplianceLevel.LARGELY_COMPLIANT
        elif score >= self.COMPLIANCE_THRESHOLDS[ComplianceLevel.PARTIALLY_COMPLIANT]:
            return ComplianceLevel.PARTIALLY_COMPLIANT
        elif score >= self.COMPLIANCE_THRESHOLDS[ComplianceLevel.NON_COMPLIANT]:
            return ComplianceLevel.NON_COMPLIANT
        else:
            return ComplianceLevel.UNABLE_TO_ASSESS
    
    def _score_to_rag_status(self, score: float) -> RAGStatus:
        """Convert score to RAG status"""
        if score >= 0.8:
            return RAGStatus.GREEN
        elif score >= 0.6:
            return RAGStatus.AMBER
        else:
            return RAGStatus.RED
    
    def _determine_gap_severity(self, assessment: ComplianceAssessment) -> RiskPriority:
        """Determine gap severity based on assessment"""
        risk_level = assessment.risk_level.lower()
        
        if risk_level == 'critical':
            return RiskPriority.CRITICAL
        elif risk_level == 'high':
            return RiskPriority.HIGH
        elif risk_level == 'medium':
            return RiskPriority.MEDIUM
        elif risk_level == 'low':
            return RiskPriority.LOW
        else:
            return RiskPriority.MINIMAL
    
    def _assess_gap_impact(self, assessment: ComplianceAssessment) -> str:
        """Assess the impact of a compliance gap"""
        if assessment.risk_level == 'critical':
            return "Severe regulatory exposure with potential for enforcement action"
        elif assessment.risk_level == 'high':
            return "Significant compliance risk requiring prompt attention"
        elif assessment.risk_level == 'medium':
            return "Moderate compliance risk that should be addressed in planned cycle"
        else:
            return "Low compliance risk for future consideration"
    
    def _estimate_remediation_effort(self, assessment: ComplianceAssessment) -> str:
        """Estimate effort required for remediation"""
        if assessment.confidence_score >= 0.8:
            return "Low - Clear remediation path identified"
        elif assessment.confidence_score >= 0.6:
            return "Medium - Some analysis required"
        else:
            return "High - Significant analysis and development needed"
    
    def _suggest_timeline(self, assessment: ComplianceAssessment) -> str:
        """Suggest remediation timeline"""
        if assessment.risk_level == 'critical':
            return "Immediate (0-30 days)"
        elif assessment.risk_level == 'high':
            return "Short-term (30-90 days)"
        elif assessment.risk_level == 'medium':
            return "Medium-term (3-6 months)"
        else:
            return "Long-term (6-12 months)"
    
    def _identify_pillar_strengths(self, assessments: List[ComplianceAssessment]) -> List[str]:
        """Identify strengths within a pillar"""
        strengths = []
        
        compliant_assessments = [a for a in assessments if a.compliance_status == 'compliant']
        for assessment in compliant_assessments[:3]:  # Top 3 compliant areas
            req = next((r for r in self.dora_requirements if r.requirement_id == assessment.requirement_id), None)
            if req:
                strengths.append(f"Strong {req.title.lower()} with comprehensive documentation")
        
        return strengths
    
    def _generate_pillar_findings(self, assessments: List[ComplianceAssessment], gaps: List[ComplianceGap]) -> List[str]:
        """Generate key findings for a pillar"""
        findings = []
        
        total_assessments = len(assessments)
        gap_count = len(gaps)
        compliance_rate = ((total_assessments - gap_count) / total_assessments * 100) if total_assessments > 0 else 0
        
        findings.append(f"Compliance rate: {compliance_rate:.1f}% ({total_assessments - gap_count}/{total_assessments} requirements)")
        
        if gaps:
            critical_gaps = [g for g in gaps if g.severity == RiskPriority.CRITICAL]
            if critical_gaps:
                findings.append(f"Critical attention needed: {len(critical_gaps)} critical gaps identified")
        
        return findings
    
    def _prioritize_pillar_actions(self, gaps: List[ComplianceGap]) -> List[str]:
        """Prioritize actions for a pillar"""
        actions = []
        
        # Focus on critical and high priority gaps
        priority_gaps = [g for g in gaps if g.severity in [RiskPriority.CRITICAL, RiskPriority.HIGH]]
        
        for gap in priority_gaps[:3]:  # Top 3 priority actions
            if gap.recommendations:
                actions.append(f"{gap.requirement_id}: {gap.recommendations[0]}")
        
        return actions
    
    def _create_remediation_roadmap(self, gaps: List[ComplianceGap]) -> List[str]:
        """Create structured remediation roadmap"""
        roadmap = []
        
        # Phase 1: Critical gaps (0-30 days)
        critical_gaps = [g for g in gaps if g.severity == RiskPriority.CRITICAL]
        if critical_gaps:
            roadmap.append(f"Phase 1 (0-30 days): Address {len(critical_gaps)} critical gaps")
            for gap in critical_gaps[:3]:
                roadmap.append(f"  - {gap.requirement_id}: {gap.description}")
        
        # Phase 2: High priority gaps (30-90 days)
        high_gaps = [g for g in gaps if g.severity == RiskPriority.HIGH]
        if high_gaps:
            roadmap.append(f"Phase 2 (30-90 days): Address {len(high_gaps)} high priority gaps")
        
        # Phase 3: Medium priority gaps (3-6 months)
        medium_gaps = [g for g in gaps if g.severity == RiskPriority.MEDIUM]
        if medium_gaps:
            roadmap.append(f"Phase 3 (3-6 months): Address {len(medium_gaps)} medium priority gaps")
        
        return roadmap
    
    def _calculate_analysis_confidence(self, detailed_assessments: List[ComplianceAssessment]) -> float:
        """Calculate overall confidence in the analysis"""
        if not detailed_assessments:
            return 0.0
        
        avg_confidence = sum(a.confidence_score for a in detailed_assessments) / len(detailed_assessments)
        return avg_confidence
    
    def _get_models_used(self) -> List[str]:
        """Get list of models used in analysis"""
        models = ["DORA Knowledge Base", "Policy Text Extractor"]
        
        if self.nlp_analyzer.anthropic_client:
            models.append("Anthropic Claude")
        if self.nlp_analyzer.openai_client:
            models.append("OpenAI GPT-4")
        if self.nlp_analyzer.embeddings_model:
            models.append("Sentence Transformers")
        
        return models
    
    def _update_analysis_stats(self, report: DORAComplianceReport):
        """Update analysis statistics"""
        self.analysis_stats['documents_analyzed'] += 1
        self.analysis_stats['total_processing_time'] += report.processing_time
        self.analysis_stats['avg_processing_time'] = (
            self.analysis_stats['total_processing_time'] / 
            self.analysis_stats['documents_analyzed']
        )
        
        # Track compliance distribution
        compliance_level = report.overall_compliance_level.value
        self.analysis_stats['compliance_distribution'][compliance_level] = (
            self.analysis_stats['compliance_distribution'].get(compliance_level, 0) + 1
        )
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        return self.analysis_stats.copy()


def main():
    """Main function for testing DORA analyzer"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DORA Compliance Analyzer Test")
    parser.add_argument("document_path", nargs="?", help="Path to policy document to analyze")
    parser.add_argument("--test-requirements", action="store_true", help="Test DORA requirements loading")
    parser.add_argument("--output", help="Output file for analysis report")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = DORAComplianceAnalyzer()
    
    if args.test_requirements:
        print(f"Loaded {len(analyzer.dora_requirements)} DORA requirements")
        for req in analyzer.dora_requirements[:3]:
            print(f"  {req.requirement_id}: {req.title}")
        return 0
    
    if args.document_path:
        try:
            # Run analysis
            import asyncio
            report = asyncio.run(analyzer.analyze_document(args.document_path))
            
            print(f"Analysis completed for: {report.document_title}")
            print(f"Overall compliance: {report.compliance_percentage:.1f}%")
            print(f"Processing time: {report.processing_time:.2f}s")
            print(f"Total gaps: {report.total_gaps} (Critical: {report.critical_gaps})")
            
            if args.output:
                # Save detailed report (implementation needed)
                print(f"Report would be saved to: {args.output}")
            
        except Exception as e:
            print(f"Analysis failed: {e}")
            return 1
    else:
        print("DORA Compliance Analyzer initialized successfully")
        print(f"Requirements loaded: {len(analyzer.dora_requirements)}")
    
    return 0


if __name__ == "__main__":
    exit(main()) 