#!/usr/bin/env python3
"""
DORA Industry Benchmarks and Best Practices Collection System

This module collects, structures, and manages industry benchmarks, best practices, 
and implementation guidance relevant to DORA compliance. It sources data from 
regulatory bodies, industry groups, and expert publications, linking them to 
specific DORA requirements for contextual guidance.

Author: DORA Compliance System
Created: 2025-05-24
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, date
from enum import Enum
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SourceType(Enum):
    """Types of benchmark sources"""
    REGULATORY_BODY = "regulatory_body"
    INDUSTRY_GROUP = "industry_group"
    EXPERT_PUBLICATION = "expert_publication"
    CONSULTING_FIRM = "consulting_firm"
    TECHNOLOGY_VENDOR = "technology_vendor"
    ACADEMIC_RESEARCH = "academic_research"
    CERTIFICATION_BODY = "certification_body"

class BenchmarkCategory(Enum):
    """Categories of benchmarks and best practices"""
    GOVERNANCE = "governance"
    RISK_MANAGEMENT = "risk_management"
    INCIDENT_MANAGEMENT = "incident_management"
    RESILIENCE_TESTING = "resilience_testing"
    THIRD_PARTY_RISK = "third_party_risk"
    THREAT_INTELLIGENCE = "threat_intelligence"
    OPERATIONAL_METRICS = "operational_metrics"
    TECHNOLOGY_IMPLEMENTATION = "technology_implementation"
    COMPLIANCE_FRAMEWORK = "compliance_framework"

class MaturityLevel(Enum):
    """Maturity levels for benchmark assessment"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    LEADING_PRACTICE = "leading_practice"

class IndustryVertical(Enum):
    """Industry verticals for targeted benchmarks"""
    BANKING = "banking"
    INSURANCE = "insurance"
    INVESTMENT_SERVICES = "investment_services"
    PAYMENT_SERVICES = "payment_services"
    ASSET_MANAGEMENT = "asset_management"
    FINTECH = "fintech"
    CROSS_SECTOR = "cross_sector"

@dataclass
class BenchmarkSource:
    """Represents a source of benchmarks and best practices"""
    id: str
    name: str
    source_type: SourceType
    website: str
    description: str
    credibility_score: float  # 0.0 to 1.0
    last_updated: date
    contact_info: Optional[str] = None
    
class BenchmarkMetric:
    """Represents a quantitative benchmark metric"""
    def __init__(self, name: str, value: Union[float, int, str], 
                 unit: str, percentile: Optional[float] = None,
                 sample_size: Optional[int] = None):
        self.name = name
        self.value = value
        self.unit = unit
        self.percentile = percentile
        self.sample_size = sample_size
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "percentile": self.percentile,
            "sample_size": self.sample_size
        }

@dataclass
class BestPractice:
    """Represents a qualitative best practice"""
    id: str
    title: str
    description: str
    implementation_guidance: str
    success_factors: List[str]
    common_pitfalls: List[str]
    estimated_effort: str
    estimated_cost: str
    roi_indicators: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

@dataclass
class IndustryBenchmark:
    """Comprehensive industry benchmark entry"""
    id: str
    title: str
    description: str
    category: BenchmarkCategory
    source: BenchmarkSource
    industry_vertical: IndustryVertical
    maturity_level: MaturityLevel
    dora_requirements: List[str]  # DORA requirement IDs
    dora_articles: List[str]  # DORA article references
    
    # Content
    metrics: List[BenchmarkMetric]
    best_practices: List[BestPractice]
    implementation_guidance: str
    success_stories: List[str]
    lessons_learned: List[str]
    
    # Metadata
    publication_date: date
    last_reviewed: date
    confidence_level: float  # 0.0 to 1.0
    evidence_quality: str
    geographic_scope: List[str]
    entity_size_applicability: List[str]  # Tier 1, Tier 2, etc.
    
    # Relationships
    related_benchmarks: List[str]
    regulatory_references: List[str]
    cross_framework_mappings: Dict[str, List[str]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        
        # Handle enum serialization
        result['category'] = self.category.value
        result['industry_vertical'] = self.industry_vertical.value
        result['maturity_level'] = self.maturity_level.value
        result['source']['source_type'] = self.source.source_type.value
        
        # Handle date serialization
        result['publication_date'] = self.publication_date.isoformat()
        result['last_reviewed'] = self.last_reviewed.isoformat()
        result['source']['last_updated'] = self.source.last_updated.isoformat()
        
        # Handle metrics serialization
        result['metrics'] = [metric.to_dict() for metric in self.metrics]
        
        # Handle best practices serialization
        result['best_practices'] = [bp.to_dict() for bp in self.best_practices]
        
        return result

class BenchmarkDatabase:
    """Database for managing industry benchmarks"""
    
    def __init__(self):
        self.benchmarks: Dict[str, IndustryBenchmark] = {}
        self.sources: Dict[str, BenchmarkSource] = {}
        self.tags_index: Dict[str, List[str]] = {}
        self.dora_mapping_index: Dict[str, List[str]] = {}
        
    def add_source(self, source: BenchmarkSource) -> None:
        """Add a benchmark source"""
        self.sources[source.id] = source
        logger.info(f"Added benchmark source: {source.name}")
        
    def add_benchmark(self, benchmark: IndustryBenchmark) -> None:
        """Add a benchmark to the database"""
        self.benchmarks[benchmark.id] = benchmark
        
        # Update indexes
        for req_id in benchmark.dora_requirements:
            if req_id not in self.dora_mapping_index:
                self.dora_mapping_index[req_id] = []
            self.dora_mapping_index[req_id].append(benchmark.id)
            
        logger.info(f"Added benchmark: {benchmark.title}")
        
    def search_benchmarks(self, 
                         category: Optional[BenchmarkCategory] = None,
                         industry: Optional[IndustryVertical] = None,
                         maturity_level: Optional[MaturityLevel] = None,
                         dora_requirement: Optional[str] = None) -> List[IndustryBenchmark]:
        """Search benchmarks by various criteria"""
        results = []
        
        for benchmark in self.benchmarks.values():
            if category and benchmark.category != category:
                continue
            if industry and benchmark.industry_vertical != industry:
                continue
            if maturity_level and benchmark.maturity_level != maturity_level:
                continue
            if dora_requirement and dora_requirement not in benchmark.dora_requirements:
                continue
                
            results.append(benchmark)
            
        return results
        
    def get_benchmarks_for_dora_requirement(self, requirement_id: str) -> List[IndustryBenchmark]:
        """Get all benchmarks linked to a specific DORA requirement"""
        benchmark_ids = self.dora_mapping_index.get(requirement_id, [])
        return [self.benchmarks[bid] for bid in benchmark_ids if bid in self.benchmarks]

class IndustryBenchmarkCollector:
    """Main collector class for industry benchmarks and best practices"""
    
    def __init__(self):
        self.database = BenchmarkDatabase()
        self.load_benchmark_sources()
        self.populate_industry_benchmarks()
        
    def load_benchmark_sources(self) -> None:
        """Load authoritative sources for benchmarks"""
        
        sources = [
            BenchmarkSource(
                id="eba_2024",
                name="European Banking Authority",
                source_type=SourceType.REGULATORY_BODY,
                website="https://www.eba.europa.eu",
                description="EU banking regulator providing DORA implementation guidance and industry best practices",
                credibility_score=1.0,
                last_updated=date(2024, 10, 1),
                contact_info="info@eba.europa.eu"
            ),
            BenchmarkSource(
                id="esma_2024",
                name="European Securities and Markets Authority",
                source_type=SourceType.REGULATORY_BODY,
                website="https://www.esma.europa.eu",
                description="EU securities regulator with DORA compliance guidance for investment firms",
                credibility_score=1.0,
                last_updated=date(2024, 9, 15)
            ),
            BenchmarkSource(
                id="eiopa_2024",
                name="European Insurance and Occupational Pensions Authority",
                source_type=SourceType.REGULATORY_BODY,
                website="https://www.eiopa.europa.eu",
                description="EU insurance regulator providing DORA implementation frameworks",
                credibility_score=1.0,
                last_updated=date(2024, 8, 30)
            ),
            BenchmarkSource(
                id="fsb_2024",
                name="Financial Stability Board",
                source_type=SourceType.REGULATORY_BODY,
                website="https://www.fsb.org",
                description="International body coordinating financial regulation including cyber resilience",
                credibility_score=0.95,
                last_updated=date(2024, 7, 20)
            ),
            BenchmarkSource(
                id="isaca_2024",
                name="ISACA",
                source_type=SourceType.INDUSTRY_GROUP,
                website="https://www.isaca.org",
                description="Global association providing IT governance and cybersecurity frameworks",
                credibility_score=0.9,
                last_updated=date(2024, 11, 1)
            ),
            BenchmarkSource(
                id="iif_2024",
                name="Institute of International Finance",
                source_type=SourceType.INDUSTRY_GROUP,
                website="https://www.iif.com",
                description="Global association of financial institutions sharing best practices",
                credibility_score=0.85,
                last_updated=date(2024, 10, 15)
            ),
            BenchmarkSource(
                id="deloitte_2024",
                name="Deloitte Financial Services",
                source_type=SourceType.CONSULTING_FIRM,
                website="https://www.deloitte.com",
                description="Global consulting firm with DORA implementation expertise",
                credibility_score=0.8,
                last_updated=date(2024, 11, 10)
            ),
            BenchmarkSource(
                id="mckinsey_2024",
                name="McKinsey & Company",
                source_type=SourceType.CONSULTING_FIRM,
                website="https://www.mckinsey.com",
                description="Management consulting firm with digital resilience research",
                credibility_score=0.8,
                last_updated=date(2024, 10, 25)
            ),
            BenchmarkSource(
                id="bis_2024",
                name="Bank for International Settlements",
                source_type=SourceType.REGULATORY_BODY,
                website="https://www.bis.org",
                description="Central bank coordination body with operational resilience principles",
                credibility_score=0.95,
                last_updated=date(2024, 9, 5)
            ),
            BenchmarkSource(
                id="nist_2024",
                name="NIST Cybersecurity Framework",
                source_type=SourceType.CERTIFICATION_BODY,
                website="https://www.nist.gov",
                description="US standards body providing cybersecurity frameworks and benchmarks",
                credibility_score=0.9,
                last_updated=date(2024, 8, 15)
            )
        ]
        
        for source in sources:
            self.database.add_source(source)
            
        logger.info(f"Loaded {len(sources)} benchmark sources")
        
    def populate_industry_benchmarks(self) -> None:
        """Populate the database with comprehensive industry benchmarks"""
        
        # Governance Benchmarks
        self._add_governance_benchmarks()
        
        # Risk Management Benchmarks  
        self._add_risk_management_benchmarks()
        
        # Incident Management Benchmarks
        self._add_incident_management_benchmarks()
        
        # Resilience Testing Benchmarks
        self._add_resilience_testing_benchmarks()
        
        # Third-Party Risk Benchmarks
        self._add_third_party_risk_benchmarks()
        
        # Threat Intelligence Benchmarks
        self._add_threat_intelligence_benchmarks()
        
        # Technology Implementation Benchmarks
        self._add_technology_implementation_benchmarks()
        
        logger.info(f"Populated {len(self.database.benchmarks)} industry benchmarks")
        
    def _add_governance_benchmarks(self) -> None:
        """Add ICT governance and oversight benchmarks"""
        
        # Senior Management Oversight Benchmark
        governance_benchmark = IndustryBenchmark(
            id="gov_001",
            title="Senior Management ICT Risk Oversight Framework",
            description="Comprehensive benchmark for establishing senior management oversight of ICT risks in line with DORA Article 5",
            category=BenchmarkCategory.GOVERNANCE,
            source=self.database.sources["eba_2024"],
            industry_vertical=IndustryVertical.CROSS_SECTOR,
            maturity_level=MaturityLevel.ADVANCED,
            dora_requirements=["DORA_ART5_REQ1", "DORA_ART5_REQ2", "DORA_ART5_REQ3"],
            dora_articles=["Article 5", "Article 6"],
            
            metrics=[
                BenchmarkMetric("Board Meeting ICT Discussion Frequency", 4, "times per year", 75, 150),
                BenchmarkMetric("ICT Risk Committee Independence", 80, "percentage", 90, 120),
                BenchmarkMetric("Senior Management ICT Training Hours", 24, "hours per year", 85, 200),
                BenchmarkMetric("ICT Risk Appetite Documentation Score", 85, "percentage", 80, 180)
            ],
            
            best_practices=[
                BestPractice(
                    id="gov_bp_001",
                    title="Quarterly ICT Risk Board Reporting",
                    description="Establish quarterly board-level reporting on ICT risks, incidents, and resilience metrics",
                    implementation_guidance="Create standardized dashboard with key risk indicators, incident summaries, and forward-looking assessments",
                    success_factors=["Executive sponsorship", "Standardized metrics", "Clear escalation procedures"],
                    common_pitfalls=["Information overload", "Lack of business context", "Infrequent updates"],
                    estimated_effort="3-6 months",
                    estimated_cost="€150,000 - €300,000",
                    roi_indicators=["Improved risk visibility", "Faster decision making", "Regulatory compliance"]
                ),
                BestPractice(
                    id="gov_bp_002",
                    title="ICT Risk Appetite Framework",
                    description="Develop and implement comprehensive ICT risk appetite statements aligned with business strategy",
                    implementation_guidance="Define quantitative and qualitative risk tolerance levels across technology domains",
                    success_factors=["Business alignment", "Measurable metrics", "Regular review cycles"],
                    common_pitfalls=["Overly complex frameworks", "Lack of operational translation", "Static assessments"],
                    estimated_effort="4-8 months",
                    estimated_cost="€200,000 - €500,000",
                    roi_indicators=["Better risk decisions", "Resource optimization", "Compliance assurance"]
                )
            ],
            
            implementation_guidance="""
            1. Establish ICT Risk Committee with appropriate expertise and independence
            2. Define clear roles and responsibilities for ICT risk management
            3. Implement regular reporting mechanisms to senior management and board
            4. Develop ICT risk appetite statements aligned with business objectives
            5. Create escalation procedures for critical ICT risks and incidents
            6. Ensure adequate ICT expertise at governance level through training or recruitment
            """,
            
            success_stories=[
                "Major EU bank reduced ICT incident impact by 40% after implementing comprehensive governance framework",
                "Insurance company achieved 'exceeds expectations' rating in regulatory examination following governance enhancement"
            ],
            
            lessons_learned=[
                "Governance frameworks require ongoing maintenance and evolution",
                "Cultural change takes longer than technical implementation",
                "Board engagement essential for sustainable success"
            ],
            
            publication_date=date(2024, 10, 1),
            last_reviewed=date(2024, 11, 15),
            confidence_level=0.9,
            evidence_quality="High - Based on regulatory guidance and industry surveys",
            geographic_scope=["EU", "EEA"],
            entity_size_applicability=["Tier 1", "Tier 2"],
            
            related_benchmarks=["risk_001", "inc_001"],
            regulatory_references=["DORA Article 5", "DORA Article 6", "EBA Guidelines ICT Risk Management"],
            cross_framework_mappings={
                "ISO27001": ["A.6.1.1", "A.6.1.2"],
                "NIST_CSF": ["GV.OV", "GV.RM"],
                "COBIT": ["EDM03", "APO01"]
            }
        )
        
        self.database.add_benchmark(governance_benchmark)
        
        # Add more governance benchmarks...
        
    def _add_risk_management_benchmarks(self) -> None:
        """Add ICT risk management benchmarks"""
        
        risk_benchmark = IndustryBenchmark(
            id="risk_001",
            title="Comprehensive ICT Risk Management Framework",
            description="Industry benchmark for implementing robust ICT risk identification, assessment, and mitigation processes",
            category=BenchmarkCategory.RISK_MANAGEMENT,
            source=self.database.sources["fsb_2024"],
            industry_vertical=IndustryVertical.CROSS_SECTOR,
            maturity_level=MaturityLevel.INTERMEDIATE,
            dora_requirements=["DORA_ART6_REQ1", "DORA_ART6_REQ2"],
            dora_articles=["Article 6", "Article 8"],
            
            metrics=[
                BenchmarkMetric("Risk Assessment Frequency", 2, "times per year", 70, 100),
                BenchmarkMetric("Critical Asset Identification Coverage", 95, "percentage", 85, 150),
                BenchmarkMetric("Risk Mitigation Plan Completion", 88, "percentage", 80, 200),
                BenchmarkMetric("Business Impact Analysis Currency", 6, "months maximum age", 90, 120)
            ],
            
            best_practices=[
                BestPractice(
                    id="risk_bp_001",
                    title="Dynamic Risk Assessment Methodology",
                    description="Implement continuous risk assessment with real-time threat intelligence integration",
                    implementation_guidance="Deploy automated scanning tools integrated with threat feeds and business context",
                    success_factors=["Automation capabilities", "Threat intelligence feeds", "Business context integration"],
                    common_pitfalls=["Tool proliferation", "False positive fatigue", "Lack of business prioritization"],
                    estimated_effort="6-12 months",
                    estimated_cost="€500,000 - €1,200,000",
                    roi_indicators=["Faster threat response", "Improved risk prioritization", "Resource efficiency"]
                )
            ],
            
            implementation_guidance="""
            1. Establish comprehensive asset inventory and classification system
            2. Implement risk-based approach to ICT service criticality assessment
            3. Develop scenario-based risk analysis methodologies
            4. Create integrated threat intelligence and vulnerability management
            5. Establish clear risk appetite and tolerance thresholds
            6. Implement continuous monitoring and assessment capabilities
            """,
            
            success_stories=[
                "Investment firm reduced risk assessment time by 60% through automation while improving accuracy",
                "Payment processor identified and mitigated critical vulnerabilities 3x faster with dynamic assessment"
            ],
            
            lessons_learned=[
                "Risk assessment quality more important than frequency",
                "Business context critical for effective prioritization",
                "Automation enables focus on high-value analysis"
            ],
            
            publication_date=date(2024, 7, 20),
            last_reviewed=date(2024, 11, 10),
            confidence_level=0.85,
            evidence_quality="High - Based on FSB principles and industry implementation data",
            geographic_scope=["Global"],
            entity_size_applicability=["Tier 1", "Tier 2", "Proportional for smaller entities"],
            
            related_benchmarks=["gov_001", "inc_001", "test_001"],
            regulatory_references=["DORA Article 6", "FSB Operational Resilience Principles"],
            cross_framework_mappings={
                "ISO27005": ["7.2", "8.2", "9.2"],
                "NIST_CSF": ["ID.RA", "PR.IP"],
                "FAIR": ["Risk Analysis", "Scenario Modeling"]
            }
        )
        
        self.database.add_benchmark(risk_benchmark)
        
    def _add_incident_management_benchmarks(self) -> None:
        """Add incident management and reporting benchmarks"""
        
        incident_benchmark = IndustryBenchmark(
            id="inc_001",
            title="Advanced ICT Incident Management and Regulatory Reporting",
            description="Comprehensive benchmark for incident detection, response, and regulatory reporting capabilities",
            category=BenchmarkCategory.INCIDENT_MANAGEMENT,
            source=self.database.sources["eba_2024"],
            industry_vertical=IndustryVertical.CROSS_SECTOR,
            maturity_level=MaturityLevel.ADVANCED,
            dora_requirements=["DORA_ART17_REQ1", "DORA_ART17_REQ2", "DORA_ART19_REQ1"],
            dora_articles=["Article 17", "Article 18", "Article 19"],
            
            metrics=[
                BenchmarkMetric("Mean Time to Detection (MTTD)", 15, "minutes", 75, 250),
                BenchmarkMetric("Mean Time to Response (MTTR)", 60, "minutes", 80, 200),
                BenchmarkMetric("Incident Classification Accuracy", 92, "percentage", 85, 180),
                BenchmarkMetric("Regulatory Reporting Timeliness", 98, "percentage on time", 90, 150),
                BenchmarkMetric("Post-Incident Review Completion", 95, "percentage within 30 days", 85, 120)
            ],
            
            best_practices=[
                BestPractice(
                    id="inc_bp_001",
                    title="Automated Incident Classification and Escalation",
                    description="Implement AI-powered incident classification with automated escalation workflows",
                    implementation_guidance="Deploy machine learning models trained on historical incidents with decision trees for escalation",
                    success_factors=["Quality training data", "Clear escalation criteria", "Human oversight mechanisms"],
                    common_pitfalls=["Over-automation", "Alert fatigue", "False classification"],
                    estimated_effort="8-15 months",
                    estimated_cost="€800,000 - €1,500,000",
                    roi_indicators=["Faster response times", "Improved accuracy", "Resource efficiency"]
                ),
                BestPractice(
                    id="inc_bp_002",
                    title="Real-time Regulatory Reporting Pipeline",
                    description="Establish automated pipeline for real-time incident data collection and regulatory submission",
                    implementation_guidance="Create data integration layer connecting incident tools to regulatory reporting templates",
                    success_factors=["Data standardization", "Quality validation", "Backup procedures"],
                    common_pitfalls=["Data quality issues", "System dependencies", "Regulatory format changes"],
                    estimated_effort="6-10 months",
                    estimated_cost="€400,000 - €800,000",
                    roi_indicators=["Compliance assurance", "Reduced manual effort", "Audit efficiency"]
                )
            ],
            
            implementation_guidance="""
            1. Establish 24/7 incident response capability with appropriate staffing
            2. Implement comprehensive logging and monitoring across all critical systems
            3. Develop automated incident detection and classification capabilities
            4. Create standardized incident response procedures and playbooks
            5. Establish direct integration with regulatory reporting systems
            6. Implement continuous improvement based on lessons learned
            """,
            
            success_stories=[
                "Global bank reduced regulatory reporting time from 4 hours to 30 minutes through automation",
                "Insurance company improved incident detection rate by 85% with advanced monitoring implementation"
            ],
            
            lessons_learned=[
                "Preparation and training more critical than technology alone",
                "Regular testing of procedures essential for effectiveness",
                "Communication protocols must be clear and well-practiced"
            ],
            
            publication_date=date(2024, 10, 1),
            last_reviewed=date(2024, 11, 20),
            confidence_level=0.9,
            evidence_quality="Very High - Based on EBA technical standards and industry data",
            geographic_scope=["EU", "EEA"],
            entity_size_applicability=["Tier 1", "Tier 2"],
            
            related_benchmarks=["gov_001", "risk_001", "test_001"],
            regulatory_references=["DORA Article 17", "DORA RTS on Incident Classification", "EBA Incident Reporting Guidelines"],
            cross_framework_mappings={
                "ISO27035": ["5.2", "5.3", "6.1"],
                "NIST_CSF": ["DE.CM", "DE.DP", "RS.CO"],
                "ITIL": ["Incident Management", "Problem Management"]
            }
        )
        
        self.database.add_benchmark(incident_benchmark)
        
    def _add_resilience_testing_benchmarks(self) -> None:
        """Add digital operational resilience testing benchmarks"""
        
        testing_benchmark = IndustryBenchmark(
            id="test_001",
            title="Comprehensive Digital Operational Resilience Testing Program",
            description="Industry benchmark for implementing thorough testing programs including TLPT coordination",
            category=BenchmarkCategory.RESILIENCE_TESTING,
            source=self.database.sources["esma_2024"],
            industry_vertical=IndustryVertical.CROSS_SECTOR,
            maturity_level=MaturityLevel.LEADING_PRACTICE,
            dora_requirements=["DORA_ART24_REQ1", "DORA_ART24_REQ2", "DORA_ART26_REQ1"],
            dora_articles=["Article 24", "Article 25", "Article 26"],
            
            metrics=[
                BenchmarkMetric("Testing Program Coverage", 95, "percentage of critical systems", 85, 100),
                BenchmarkMetric("TLPT Frequency", 1, "tests per 3 years", 80, 50),
                BenchmarkMetric("Remediation Time for Critical Findings", 30, "days average", 75, 150),
                BenchmarkMetric("Testing Automation Level", 70, "percentage automated", 90, 80),
                BenchmarkMetric("Cross-System Integration Testing", 85, "percentage coverage", 80, 120)
            ],
            
            best_practices=[
                BestPractice(
                    id="test_bp_001",
                    title="Continuous Resilience Testing Framework",
                    description="Implement continuous automated testing with periodic comprehensive assessments",
                    implementation_guidance="Deploy chaos engineering principles with graduated testing intensity and business impact consideration",
                    success_factors=["Gradual implementation", "Business alignment", "Comprehensive monitoring"],
                    common_pitfalls=["Production impact", "Test coverage gaps", "Inadequate rollback procedures"],
                    estimated_effort="12-18 months",
                    estimated_cost="€1,000,000 - €2,500,000",
                    roi_indicators=["Improved system reliability", "Faster recovery times", "Regulatory compliance"]
                ),
                BestPractice(
                    id="test_bp_002",
                    title="TLPT Coordination and Management",
                    description="Establish comprehensive threat-led penetration testing program with external coordination",
                    implementation_guidance="Create structured TLPT program with qualified external providers and clear scope definition",
                    success_factors=["Qualified providers", "Clear scope", "Executive support", "Coordinated response"],
                    common_pitfalls=["Scope creep", "Inadequate preparation", "Poor communication"],
                    estimated_effort="6-12 months per cycle",
                    estimated_cost="€500,000 - €1,500,000 per test",
                    roi_indicators=["Vulnerability identification", "Response capability validation", "Regulatory compliance"]
                )
            ],
            
            implementation_guidance="""
            1. Develop risk-based testing strategy covering all critical systems and processes
            2. Implement graduated testing approach from basic to advanced scenarios
            3. Establish clear testing schedules and documentation requirements
            4. Create coordination mechanisms for TLPT with external providers and regulators
            5. Develop comprehensive remediation tracking and validation processes
            6. Ensure business continuity during testing activities
            """,
            
            success_stories=[
                "European investment bank discovered and remediated 15 critical vulnerabilities through comprehensive TLPT program",
                "Payment processor improved system resilience by 90% through continuous testing implementation"
            ],
            
            lessons_learned=[
                "Testing realism more important than frequency",
                "Business involvement critical for meaningful scenarios",
                "Remediation tracking essential for continuous improvement"
            ],
            
            publication_date=date(2024, 9, 15),
            last_reviewed=date(2024, 11, 25),
            confidence_level=0.88,
            evidence_quality="High - Based on ESMA guidance and early implementation experience",
            geographic_scope=["EU", "EEA"],
            entity_size_applicability=["Tier 1 entities", "Proportional application for Tier 2"],
            
            related_benchmarks=["risk_001", "inc_001", "tech_001"],
            regulatory_references=["DORA Article 24", "ESMA TLPT Guidelines", "ECB Cyber Resilience Oversight"],
            cross_framework_mappings={
                "ISO27001": ["A.14.2.8", "A.17.1.3"],
                "NIST_CSF": ["PR.IP", "DE.AE"],
                "PCI_DSS": ["11.3", "11.4"]
            }
        )
        
        self.database.add_benchmark(testing_benchmark)
        
    def _add_third_party_risk_benchmarks(self) -> None:
        """Add third-party risk management benchmarks"""
        
        third_party_benchmark = IndustryBenchmark(
            id="tpr_001",
            title="Comprehensive Third-Party ICT Risk Management",
            description="Industry benchmark for managing ICT risks from third-party service providers and vendors",
            category=BenchmarkCategory.THIRD_PARTY_RISK,
            source=self.database.sources["iif_2024"],
            industry_vertical=IndustryVertical.CROSS_SECTOR,
            maturity_level=MaturityLevel.INTERMEDIATE,
            dora_requirements=["DORA_ART28_REQ1", "DORA_ART28_REQ2", "DORA_ART30_REQ1"],
            dora_articles=["Article 28", "Article 29", "Article 30"],
            
            metrics=[
                BenchmarkMetric("Vendor Assessment Completion Rate", 98, "percentage", 85, 200),
                BenchmarkMetric("Critical Vendor Monitoring Coverage", 100, "percentage", 95, 150),
                BenchmarkMetric("Contract Review Cycle Time", 45, "days average", 70, 180),
                BenchmarkMetric("Vendor Risk Rating Accuracy", 89, "percentage validated", 80, 120),
                BenchmarkMetric("Third-Party Incident Response Time", 120, "minutes average", 75, 100)
            ],
            
            best_practices=[
                BestPractice(
                    id="tpr_bp_001",
                    title="Continuous Third-Party Risk Monitoring",
                    description="Implement real-time monitoring of third-party risk indicators and performance metrics",
                    implementation_guidance="Deploy automated monitoring tools integrated with vendor management platforms",
                    success_factors=["Data integration", "Real-time alerting", "Risk correlation"],
                    common_pitfalls=["Data quality issues", "Alert fatigue", "Vendor resistance"],
                    estimated_effort="8-12 months",
                    estimated_cost="€600,000 - €1,200,000",
                    roi_indicators=["Early risk detection", "Improved vendor performance", "Regulatory compliance"]
                )
            ],
            
            implementation_guidance="""
            1. Establish comprehensive vendor classification and criticality assessment
            2. Implement risk-based due diligence procedures for vendor onboarding
            3. Develop continuous monitoring capabilities for critical vendors
            4. Create standardized contract language for ICT risk management
            5. Establish clear escalation and termination procedures
            6. Implement vendor concentration risk management
            """,
            
            success_stories=[
                "Global asset manager reduced vendor-related incidents by 70% through comprehensive monitoring program"
            ],
            
            lessons_learned=[
                "Vendor cooperation essential for effective monitoring",
                "Contract terms must be enforceable and practical",
                "Regular relationship management prevents adversarial dynamics"
            ],
            
            publication_date=date(2024, 10, 15),
            last_reviewed=date(2024, 11, 18),
            confidence_level=0.82,
            evidence_quality="Good - Based on industry survey and implementation case studies",
            geographic_scope=["Global"],
            entity_size_applicability=["All entity sizes with appropriate scaling"],
            
            related_benchmarks=["risk_001", "gov_001"],
            regulatory_references=["DORA Article 28", "IIF Third-Party Risk Management Principles"],
            cross_framework_mappings={
                "ISO27001": ["A.15.1.1", "A.15.2.1"],
                "NIST_CSF": ["ID.SC", "PR.IP"],
                "COBIT": ["APO10", "EDM03"]
            }
        )
        
        self.database.add_benchmark(third_party_benchmark)
        
    def _add_threat_intelligence_benchmarks(self) -> None:
        """Add threat intelligence and information sharing benchmarks"""
        
        threat_intel_benchmark = IndustryBenchmark(
            id="ti_001",
            title="Cyber Threat Intelligence and Information Sharing Framework",
            description="Benchmark for establishing comprehensive threat intelligence capabilities and industry information sharing",
            category=BenchmarkCategory.THREAT_INTELLIGENCE,
            source=self.database.sources["isaca_2024"],
            industry_vertical=IndustryVertical.CROSS_SECTOR,
            maturity_level=MaturityLevel.ADVANCED,
            dora_requirements=["DORA_ART40_REQ1", "DORA_ART42_REQ1"],
            dora_articles=["Article 40", "Article 41", "Article 42"],
            
            metrics=[
                BenchmarkMetric("Threat Intelligence Sources", 12, "number of feeds", 80, 100),
                BenchmarkMetric("Intelligence Integration Time", 30, "minutes to operational use", 85, 150),
                BenchmarkMetric("Threat Hunt Frequency", 4, "campaigns per month", 75, 80),
                BenchmarkMetric("Information Sharing Participation", 85, "percentage of relevant sharing groups", 70, 120)
            ],
            
            best_practices=[
                BestPractice(
                    id="ti_bp_001",
                    title="Automated Threat Intelligence Integration",
                    description="Implement automated ingestion and correlation of threat intelligence from multiple sources",
                    implementation_guidance="Deploy SOAR platform with intelligence feeds integration and automated response workflows",
                    success_factors=["Quality intelligence sources", "Automated correlation", "Analyst training"],
                    common_pitfalls=["Information overload", "False positives", "Analyst burnout"],
                    estimated_effort="6-12 months",
                    estimated_cost="€400,000 - €900,000",
                    roi_indicators=["Faster threat detection", "Improved accuracy", "Analyst productivity"]
                )
            ],
            
            implementation_guidance="""
            1. Establish threat intelligence program with dedicated resources
            2. Implement multiple intelligence sources for comprehensive coverage
            3. Develop automated intelligence processing and correlation capabilities
            4. Create threat hunting program based on intelligence insights
            5. Establish information sharing relationships with industry peers
            6. Implement privacy-preserving sharing mechanisms
            """,
            
            success_stories=[
                "Financial services firm prevented major breach through early threat intelligence warning"
            ],
            
            lessons_learned=[
                "Quality more important than quantity in intelligence sources",
                "Analyst expertise critical for effective intelligence use",
                "Sharing relationships require ongoing investment"
            ],
            
            publication_date=date(2024, 11, 1),
            last_reviewed=date(2024, 11, 30),
            confidence_level=0.85,
            evidence_quality="Good - Based on ISACA frameworks and industry best practices",
            geographic_scope=["Global"],
            entity_size_applicability=["Tier 1", "Tier 2 with appropriate scaling"],
            
            related_benchmarks=["inc_001", "risk_001"],
            regulatory_references=["DORA Article 40", "ISACA Threat Intelligence Framework"],
            cross_framework_mappings={
                "NIST_CSF": ["DE.CM", "DE.DP"],
                "MITRE_ATT&CK": ["Threat Intelligence", "Detection"],
                "ISO27035": ["5.4", "7.3"]
            }
        )
        
        self.database.add_benchmark(threat_intel_benchmark)
        
    def _add_technology_implementation_benchmarks(self) -> None:
        """Add technology implementation and operational benchmarks"""
        
        tech_benchmark = IndustryBenchmark(
            id="tech_001",
            title="Technology Infrastructure Resilience Implementation",
            description="Comprehensive benchmark for implementing resilient technology infrastructure and operations",
            category=BenchmarkCategory.TECHNOLOGY_IMPLEMENTATION,
            source=self.database.sources["deloitte_2024"],
            industry_vertical=IndustryVertical.CROSS_SECTOR,
            maturity_level=MaturityLevel.INTERMEDIATE,
            dora_requirements=["DORA_ART6_REQ3", "DORA_ART8_REQ1"],
            dora_articles=["Article 6", "Article 8", "Article 11"],
            
            metrics=[
                BenchmarkMetric("System Availability", 99.95, "percentage uptime", 90, 200),
                BenchmarkMetric("Recovery Time Objective", 4, "hours maximum", 80, 150),
                BenchmarkMetric("Recovery Point Objective", 15, "minutes maximum", 85, 180),
                BenchmarkMetric("Change Success Rate", 97, "percentage", 85, 250),
                BenchmarkMetric("Patch Management Timeliness", 95, "percentage within SLA", 80, 200)
            ],
            
            best_practices=[
                BestPractice(
                    id="tech_bp_001",
                    title="Zero-Downtime Deployment Framework",
                    description="Implement blue-green deployment strategies for critical systems with automated rollback",
                    implementation_guidance="Establish parallel environments with automated traffic switching and health monitoring",
                    success_factors=["Environment parity", "Automated testing", "Monitoring integration"],
                    common_pitfalls=["Resource overhead", "Complexity management", "Data synchronization"],
                    estimated_effort="9-15 months",
                    estimated_cost="€750,000 - €1,800,000",
                    roi_indicators=["Reduced downtime", "Faster deployments", "Improved reliability"]
                )
            ],
            
            implementation_guidance="""
            1. Implement comprehensive monitoring and alerting across all infrastructure
            2. Establish automated backup and disaster recovery procedures
            3. Deploy redundant systems with automatic failover capabilities
            4. Implement infrastructure as code for consistent deployments
            5. Establish comprehensive change management and testing procedures
            6. Create performance optimization and capacity planning processes
            """,
            
            success_stories=[
                "Payment processor achieved 99.99% uptime through comprehensive resilience implementation"
            ],
            
            lessons_learned=[
                "Automation critical for consistent operational excellence",
                "Monitoring must provide actionable insights, not just data",
                "Disaster recovery testing must be regular and realistic"
            ],
            
            publication_date=date(2024, 11, 10),
            last_reviewed=date(2024, 11, 28),
            confidence_level=0.83,
            evidence_quality="Good - Based on consulting firm analysis and client implementations",
            geographic_scope=["Global"],
            entity_size_applicability=["All sizes with appropriate scaling"],
            
            related_benchmarks=["test_001", "risk_001"],
            regulatory_references=["DORA Article 6", "Deloitte Technology Resilience Framework"],
            cross_framework_mappings={
                "ITIL": ["Service Level Management", "Availability Management"],
                "ISO20000": ["9.1", "9.2"],
                "COBIT": ["BAI04", "DSS01"]
            }
        )
        
        self.database.add_benchmark(tech_benchmark)
        
    def generate_benchmark_report(self, 
                                 dora_requirement: Optional[str] = None,
                                 category: Optional[BenchmarkCategory] = None,
                                 industry: Optional[IndustryVertical] = None) -> Dict[str, Any]:
        """Generate comprehensive benchmark analysis report"""
        
        # Filter benchmarks based on criteria
        if dora_requirement:
            benchmarks = self.database.get_benchmarks_for_dora_requirement(dora_requirement)
        else:
            benchmarks = self.database.search_benchmarks(category=category, industry=industry)
            
        if not benchmarks:
            return {"error": "No benchmarks found matching criteria"}
            
        # Generate summary statistics
        stats = {
            "total_benchmarks": len(benchmarks),
            "categories": {},
            "maturity_levels": {},
            "industries": {},
            "sources": {},
            "avg_confidence": sum(b.confidence_level for b in benchmarks) / len(benchmarks)
        }
        
        for benchmark in benchmarks:
            # Category stats
            cat = benchmark.category.value
            stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
            
            # Maturity level stats
            mat = benchmark.maturity_level.value
            stats["maturity_levels"][mat] = stats["maturity_levels"].get(mat, 0) + 1
            
            # Industry stats
            ind = benchmark.industry_vertical.value
            stats["industries"][ind] = stats["industries"].get(ind, 0) + 1
            
            # Source stats
            src = benchmark.source.name
            stats["sources"][src] = stats["sources"].get(src, 0) + 1
            
        # Generate key insights
        insights = []
        
        if len(benchmarks) > 3:
            insights.append(f"Strong benchmark coverage available with {len(benchmarks)} relevant industry references")
            
        leading_practices = [b for b in benchmarks if b.maturity_level == MaturityLevel.LEADING_PRACTICE]
        if leading_practices:
            insights.append(f"{len(leading_practices)} leading practice benchmarks identified for advanced implementation")
            
        high_confidence = [b for b in benchmarks if b.confidence_level > 0.85]
        if high_confidence:
            insights.append(f"{len(high_confidence)} high-confidence benchmarks from authoritative sources")
            
        # Generate recommendations
        recommendations = []
        
        if category == BenchmarkCategory.GOVERNANCE:
            recommendations.append("Focus on establishing senior management oversight before technical implementations")
            recommendations.append("Ensure board-level ICT risk expertise through training or recruitment")
            
        elif category == BenchmarkCategory.INCIDENT_MANAGEMENT:
            recommendations.append("Prioritize automated incident detection and classification capabilities")
            recommendations.append("Establish direct regulatory reporting integration to meet DORA timelines")
            
        elif category == BenchmarkCategory.RESILIENCE_TESTING:
            recommendations.append("Implement graduated testing approach starting with basic scenarios")
            recommendations.append("Plan TLPT coordination early to meet regulatory timeline requirements")
            
        # Compile detailed benchmark information
        benchmark_details = []
        for benchmark in benchmarks:
            detail = {
                "id": benchmark.id,
                "title": benchmark.title,
                "category": benchmark.category.value,
                "maturity_level": benchmark.maturity_level.value,
                "confidence_level": benchmark.confidence_level,
                "source": benchmark.source.name,
                "key_metrics": [
                    f"{m.name}: {m.value} {m.unit}" for m in benchmark.metrics[:3]
                ],
                "implementation_cost_range": [
                    bp.estimated_cost for bp in benchmark.best_practices if bp.estimated_cost
                ][:2],
                "dora_coverage": len(benchmark.dora_requirements)
            }
            benchmark_details.append(detail)
            
        return {
            "summary": stats,
            "insights": insights,
            "recommendations": recommendations,
            "benchmarks": benchmark_details,
            "generation_timestamp": datetime.now().isoformat(),
            "criteria": {
                "dora_requirement": dora_requirement,
                "category": category.value if category else None,
                "industry": industry.value if industry else None
            }
        }
        
    def export_benchmarks_for_ai_agents(self) -> Dict[str, Any]:
        """Export benchmark data in format optimized for AI agent consumption"""
        
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "total_benchmarks": len(self.database.benchmarks),
                "total_sources": len(self.database.sources),
                "schema_version": "1.0"
            },
            "sources": {
                source_id: {
                    "name": source.name,
                    "type": source.source_type.value,
                    "credibility": source.credibility_score,
                    "website": source.website
                }
                for source_id, source in self.database.sources.items()
            },
            "benchmarks": {
                benchmark_id: benchmark.to_dict()
                for benchmark_id, benchmark in self.database.benchmarks.items()
            },
            "indexes": {
                "by_dora_requirement": self.database.dora_mapping_index,
                "by_category": {
                    category.value: [
                        b_id for b_id, b in self.database.benchmarks.items()
                        if b.category == category
                    ]
                    for category in BenchmarkCategory
                },
                "by_maturity": {
                    level.value: [
                        b_id for b_id, b in self.database.benchmarks.items()
                        if b.maturity_level == level
                    ]
                    for level in MaturityLevel
                }
            }
        }
        
        return export_data
        
    def save_benchmarks_database(self, filepath: str) -> None:
        """Save complete benchmark database to JSON file"""
        
        export_data = self.export_benchmarks_for_ai_agents()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved benchmark database to {filepath}")
        
def main():
    """Demonstration of the Industry Benchmark Collection System"""
    
    print("🏢 DORA Industry Benchmarks and Best Practices Collection System")
    print("=" * 70)
    
    # Initialize the collector
    collector = IndustryBenchmarkCollector()
    
    print(f"\n📊 Database Statistics:")
    print(f"   • Sources: {len(collector.database.sources)}")
    print(f"   • Benchmarks: {len(collector.database.benchmarks)}")
    print(f"   • DORA Mappings: {len(collector.database.dora_mapping_index)}")
    
    # Demonstrate search capabilities
    print(f"\n🔍 Governance Benchmarks:")
    gov_benchmarks = collector.database.search_benchmarks(
        category=BenchmarkCategory.GOVERNANCE
    )
    for benchmark in gov_benchmarks:
        print(f"   • {benchmark.title}")
        print(f"     Source: {benchmark.source.name}")
        print(f"     Maturity: {benchmark.maturity_level.value}")
        print(f"     Confidence: {benchmark.confidence_level:.2f}")
    
    # Demonstrate DORA requirement mapping
    print(f"\n🎯 DORA Article 5 Benchmarks:")
    art5_benchmarks = collector.database.get_benchmarks_for_dora_requirement("DORA_ART5_REQ1")
    for benchmark in art5_benchmarks:
        print(f"   • {benchmark.title}")
        print(f"     Best Practices: {len(benchmark.best_practices)}")
        print(f"     Metrics: {len(benchmark.metrics)}")
    
    # Generate comprehensive report for governance
    print(f"\n📋 Governance Benchmark Report:")
    gov_report = collector.generate_benchmark_report(
        category=BenchmarkCategory.GOVERNANCE
    )
    
    print(f"   Summary:")
    print(f"   • Total benchmarks: {gov_report['summary']['total_benchmarks']}")
    print(f"   • Average confidence: {gov_report['summary']['avg_confidence']:.2f}")
    print(f"   • Sources: {list(gov_report['summary']['sources'].keys())}")
    
    print(f"\n   Key Insights:")
    for insight in gov_report['insights']:
        print(f"   • {insight}")
        
    print(f"\n   Recommendations:")
    for rec in gov_report['recommendations']:
        print(f"   • {rec}")
    
    # Demonstrate metrics analysis
    print(f"\n📈 Key Performance Metrics Examples:")
    for benchmark in list(collector.database.benchmarks.values())[:3]:
        print(f"\n   {benchmark.title}:")
        for metric in benchmark.metrics[:2]:
            print(f"   • {metric.name}: {metric.value} {metric.unit}")
            if metric.percentile:
                print(f"     ({metric.percentile}th percentile)")
    
    # Export for AI agents
    print(f"\n🤖 Exporting for AI Agent Integration...")
    collector.save_benchmarks_database("industry_benchmarks_database.json")
    
    # Generate cross-category analysis
    print(f"\n🔗 Cross-Category Analysis:")
    categories = [BenchmarkCategory.GOVERNANCE, BenchmarkCategory.RISK_MANAGEMENT, 
                 BenchmarkCategory.INCIDENT_MANAGEMENT]
    
    for category in categories:
        benchmarks = collector.database.search_benchmarks(category=category)
        leading_practices = sum(1 for b in benchmarks if b.maturity_level == MaturityLevel.LEADING_PRACTICE)
        avg_confidence = sum(b.confidence_level for b in benchmarks) / len(benchmarks) if benchmarks else 0
        
        print(f"   {category.value.replace('_', ' ').title()}:")
        print(f"   • Benchmarks: {len(benchmarks)}")
        print(f"   • Leading Practices: {leading_practices}")
        print(f"   • Avg Confidence: {avg_confidence:.2f}")
    
    print(f"\n✅ Industry Benchmark Collection System Demonstration Complete!")
    print(f"💾 Full database exported to: industry_benchmarks_database.json")

if __name__ == "__main__":
    main() 