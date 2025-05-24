"""
DORA Knowledge Base Data Models

This module contains the data models for the DORA Knowledge Base, including:
- Pydantic models for API serialization/validation
- SQLAlchemy ORM models for database operations
- Enum definitions for standardized values
- Relationship definitions and constraints

Based on the comprehensive DORA Requirements Database schema.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import (
    Column, String, Integer, Text, Boolean, Date, DateTime, 
    Numeric, ForeignKey, UniqueConstraint, Index, CheckConstraint,
    ARRAY, JSON as SQLJSON
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TSVECTOR, JSONB, ENUM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# SQLAlchemy Base
Base = declarative_base()

# Enum Definitions
class EntityType(str, Enum):
    """Financial entity types as defined in DORA"""
    CREDIT_INSTITUTION = "credit_institution"
    PAYMENT_INSTITUTION = "payment_institution"
    ELECTRONIC_MONEY_INSTITUTION = "electronic_money_institution"
    INVESTMENT_FIRM = "investment_firm"
    CRYPTO_ASSET_SERVICE_PROVIDER = "crypto_asset_service_provider"
    CENTRAL_SECURITIES_DEPOSITORY = "central_securities_depository"
    INSURANCE_UNDERTAKING = "insurance_undertaking"
    REINSURANCE_UNDERTAKING = "reinsurance_undertaking"
    CENTRAL_COUNTERPARTY = "central_counterparty"
    TRADE_REPOSITORY = "trade_repository"

class TierClassification(str, Enum):
    """Entity tier classification"""
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    EXEMPT = "exempt"

class RequirementType(str, Enum):
    """Requirement types"""
    MANDATORY = "mandatory"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"
    ENHANCED = "enhanced"

class ComplianceLevel(str, Enum):
    """Compliance levels"""
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"

class PillarType(str, Enum):
    """DORA five pillars"""
    GOVERNANCE_ARRANGEMENTS = "governance_arrangements"
    ICT_RELATED_INCIDENTS = "ict_related_incidents"
    DIGITAL_OPERATIONAL_RESILIENCE_TESTING = "digital_operational_resilience_testing"
    ICT_THIRD_PARTY_RISK = "ict_third_party_risk"
    INFORMATION_SHARING = "information_sharing"

class AssessmentMethod(str, Enum):
    """Assessment methods"""
    AUTOMATED = "automated"
    MANUAL = "manual"
    HYBRID = "hybrid"

class EvidenceType(str, Enum):
    """Types of evidence for compliance"""
    POLICY_DOCUMENT = "policy_document"
    PROCEDURE_DOCUMENT = "procedure_document"
    BOARD_RESOLUTION = "board_resolution"
    AUDIT_REPORT = "audit_report"
    TEST_RESULTS = "test_results"
    TRAINING_RECORDS = "training_records"
    INCIDENT_REPORTS = "incident_reports"
    THIRD_PARTY_CONTRACTS = "third_party_contracts"

class RiskLevel(str, Enum):
    """Risk level classifications"""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# SQLAlchemy ORM Models

class Chapter(Base):
    """DORA chapters"""
    __tablename__ = 'chapters'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    chapter_number = Column(Integer, nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sections = relationship("Section", back_populates="chapter")
    articles = relationship("Article", back_populates="chapter")

class Section(Base):
    """DORA sections within chapters"""
    __tablename__ = 'sections'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    section_id = Column(String(50), nullable=False, unique=True)
    chapter_id = Column(PGUUID(as_uuid=True), ForeignKey('chapters.id'), nullable=False)
    section_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    chapter = relationship("Chapter", back_populates="sections")
    articles = relationship("Article", back_populates="section")

class Article(Base):
    """DORA articles"""
    __tablename__ = 'articles'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    article_id = Column(String(50), nullable=False, unique=True)
    article_number = Column(Integer, nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    chapter_id = Column(PGUUID(as_uuid=True), ForeignKey('chapters.id'), nullable=False)
    section_id = Column(PGUUID(as_uuid=True), ForeignKey('sections.id'))
    effective_date = Column(Date, nullable=False, default=date(2025, 1, 17))
    implementation_deadline = Column(Date, nullable=False, default=date(2025, 1, 17))
    pillar = Column(ENUM(PillarType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    chapter = relationship("Chapter", back_populates="articles")
    section = relationship("Section", back_populates="articles")
    paragraphs = relationship("ArticleParagraph", back_populates="article")
    requirements = relationship("Requirement", back_populates="article")
    applicability = relationship("ArticleApplicability", back_populates="article")
    
    # Indexes
    __table_args__ = (
        Index('idx_articles_pillar', 'pillar'),
        Index('idx_articles_chapter', 'chapter_id'),
    )

class ArticleParagraph(Base):
    """Article paragraphs for structured content"""
    __tablename__ = 'article_paragraphs'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    paragraph_id = Column(String(50), nullable=False, unique=True)
    article_id = Column(PGUUID(as_uuid=True), ForeignKey('articles.id'), nullable=False)
    paragraph_number = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    article = relationship("Article", back_populates="paragraphs")
    requirements = relationship("Requirement", back_populates="paragraph")

class EntityDefinition(Base):
    """Entity type definitions and thresholds"""
    __tablename__ = 'entity_definitions'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_type = Column(ENUM(EntityType), nullable=False, unique=True)
    tier = Column(ENUM(TierClassification), nullable=False)
    threshold_description = Column(Text)
    threshold_amount = Column(Numeric(15, 2))
    threshold_currency = Column(String(3), default='EUR')
    enhanced_requirements = Column(Boolean, default=False)
    testing_frequency = Column(String(50))
    simplified_requirements = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ArticleApplicability(Base):
    """Article applicability by entity type"""
    __tablename__ = 'article_applicability'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    article_id = Column(PGUUID(as_uuid=True), ForeignKey('articles.id'), nullable=False)
    entity_type = Column(ENUM(EntityType), nullable=False)
    tier = Column(ENUM(TierClassification))
    mandatory = Column(Boolean, default=True)
    exceptions = Column(Text)
    additional_conditions = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article = relationship("Article", back_populates="applicability")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('article_id', 'entity_type', 'tier'),
    )

class Requirement(Base):
    """DORA requirements"""
    __tablename__ = 'requirements'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id = Column(String(50), nullable=False, unique=True)
    article_id = Column(PGUUID(as_uuid=True), ForeignKey('articles.id'), nullable=False)
    paragraph_id = Column(PGUUID(as_uuid=True), ForeignKey('article_paragraphs.id'))
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    pillar = Column(ENUM(PillarType), nullable=False)
    requirement_type = Column(ENUM(RequirementType), nullable=False, default=RequirementType.MANDATORY)
    compliance_level = Column(ENUM(ComplianceLevel), nullable=False, default=ComplianceLevel.LEVEL_2)
    implementation_guidance = Column(Text)
    common_gaps = Column(ARRAY(Text))
    remediation_steps = Column(ARRAY(Text))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    article = relationship("Article", back_populates="requirements")
    paragraph = relationship("ArticleParagraph", back_populates="requirements")
    evidence_requirements = relationship("EvidenceRequirement", back_populates="requirement")
    compliance_criteria = relationship("ComplianceCriteria", back_populates="requirement")
    scoring_rubrics = relationship("ScoringRubric", back_populates="requirement")
    mappings = relationship("RequirementMapping", back_populates="requirement")
    technical_standards = relationship("RequirementTechnicalStandard", back_populates="requirement")
    benchmarks = relationship("RequirementBenchmark", back_populates="requirement")
    phases = relationship("RequirementPhase", back_populates="requirement")
    costs = relationship("RequirementCost", back_populates="requirement")
    
    # Indexes
    __table_args__ = (
        Index('idx_requirements_article', 'article_id'),
        Index('idx_requirements_pillar', 'pillar'),
        Index('idx_requirements_category', 'category'),
    )

class EvidenceRequirement(Base):
    """Evidence requirements for each requirement"""
    __tablename__ = 'evidence_requirements'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id = Column(PGUUID(as_uuid=True), ForeignKey('requirements.id'), nullable=False)
    evidence_type = Column(ENUM(EvidenceType), nullable=False)
    description = Column(Text, nullable=False)
    mandatory = Column(Boolean, default=True)
    validation_rules = Column(ARRAY(Text))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    requirement = relationship("Requirement", back_populates="evidence_requirements")
    
    # Indexes
    __table_args__ = (
        Index('idx_evidence_requirements_requirement', 'requirement_id'),
    )

class ComplianceCriteria(Base):
    """Compliance criteria for assessment"""
    __tablename__ = 'compliance_criteria'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    criteria_id = Column(String(50), nullable=False, unique=True)
    requirement_id = Column(PGUUID(as_uuid=True), ForeignKey('requirements.id'), nullable=False)
    criterion = Column(Text, nullable=False)
    assessment_method = Column(ENUM(AssessmentMethod), nullable=False)
    evidence_type = Column(ENUM(EvidenceType), nullable=False)
    weight = Column(Numeric(3, 2), default=1.0)
    automation_feasibility = Column(String(20), default='medium')
    validation_rules = Column(ARRAY(Text))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    requirement = relationship("Requirement", back_populates="compliance_criteria")
    maturity_levels = relationship("MaturityLevel", back_populates="criteria")
    
    # Indexes
    __table_args__ = (
        Index('idx_compliance_criteria_requirement', 'requirement_id'),
    )

class ScoringRubric(Base):
    """Scoring rubrics for compliance assessment"""
    __tablename__ = 'scoring_rubrics'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id = Column(PGUUID(as_uuid=True), ForeignKey('requirements.id'), nullable=False)
    score_range = Column(String(10), nullable=False)  # e.g., "1-2", "3-4"
    level_name = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    characteristics = Column(ARRAY(Text))
    risk_level = Column(ENUM(RiskLevel), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    requirement = relationship("Requirement", back_populates="scoring_rubrics")

class MaturityLevel(Base):
    """Maturity levels for criteria"""
    __tablename__ = 'maturity_levels'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    criteria_id = Column(PGUUID(as_uuid=True), ForeignKey('compliance_criteria.id'), nullable=False)
    level_name = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    score_range = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    criteria = relationship("ComplianceCriteria", back_populates="maturity_levels")

class RegulatoryStandard(Base):
    """Regulatory standards for cross-mapping"""
    __tablename__ = 'regulatory_standards'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    standard_name = Column(String(100), nullable=False, unique=True)
    version = Column(String(50))
    description = Column(Text)
    alignment_percentage = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    mappings = relationship("RequirementMapping", back_populates="standard")

class RequirementMapping(Base):
    """Mappings between DORA requirements and other regulations"""
    __tablename__ = 'requirement_mappings'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id = Column(PGUUID(as_uuid=True), ForeignKey('requirements.id'), nullable=False)
    standard_id = Column(PGUUID(as_uuid=True), ForeignKey('regulatory_standards.id'), nullable=False)
    standard_reference = Column(String(100), nullable=False)
    mapping_description = Column(Text)
    confidence_level = Column(String(20), default='high')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    requirement = relationship("Requirement", back_populates="mappings")
    standard = relationship("RegulatoryStandard", back_populates="mappings")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('requirement_id', 'standard_id', 'standard_reference'),
        Index('idx_requirement_mappings_requirement', 'requirement_id'),
        Index('idx_requirement_mappings_standard', 'standard_id'),
    )

class TechnicalStandard(Base):
    """Technical standards (RTS/ITS)"""
    __tablename__ = 'technical_standards'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    standard_id = Column(String(50), nullable=False, unique=True)
    standard_type = Column(String(10), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    effective_date = Column(Date)
    status = Column(String(50), default='draft')
    document_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    requirements = relationship("RequirementTechnicalStandard", back_populates="technical_standard")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("standard_type IN ('RTS', 'ITS')"),
    )

class RequirementTechnicalStandard(Base):
    """Link requirements to technical standards"""
    __tablename__ = 'requirement_technical_standards'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id = Column(PGUUID(as_uuid=True), ForeignKey('requirements.id'), nullable=False)
    technical_standard_id = Column(PGUUID(as_uuid=True), ForeignKey('technical_standards.id'), nullable=False)
    applicability_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    requirement = relationship("Requirement", back_populates="technical_standards")
    technical_standard = relationship("TechnicalStandard", back_populates="requirements")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('requirement_id', 'technical_standard_id'),
    )

class IndustryBenchmark(Base):
    """Industry benchmarks and best practices"""
    __tablename__ = 'industry_benchmarks'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    benchmark_id = Column(String(50), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    entity_type = Column(ENUM(EntityType))
    asset_size_category = Column(String(50))
    maturity_level = Column(String(50))
    implementation_cost_estimate = Column(Numeric(15, 2))
    currency = Column(String(3), default='EUR')
    timeline_estimate = Column(Integer)  # in days
    source = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    requirements = relationship("RequirementBenchmark", back_populates="benchmark")

class RequirementBenchmark(Base):
    """Link benchmarks to requirements"""
    __tablename__ = 'requirement_benchmarks'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id = Column(PGUUID(as_uuid=True), ForeignKey('requirements.id'), nullable=False)
    benchmark_id = Column(PGUUID(as_uuid=True), ForeignKey('industry_benchmarks.id'), nullable=False)
    relevance_score = Column(Numeric(3, 2), default=1.0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    requirement = relationship("Requirement", back_populates="benchmarks")
    benchmark = relationship("IndustryBenchmark", back_populates="requirements")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('requirement_id', 'benchmark_id'),
    )

class ImplementationPhase(Base):
    """Implementation timeline phases"""
    __tablename__ = 'implementation_phases'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    phase_name = Column(String(100), nullable=False, unique=True)
    effective_date = Column(Date, nullable=False)
    description = Column(Text)
    entity_scope = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    requirements = relationship("RequirementPhase", back_populates="phase")

class RequirementPhase(Base):
    """Requirements by implementation phase"""
    __tablename__ = 'requirement_phases'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id = Column(PGUUID(as_uuid=True), ForeignKey('requirements.id'), nullable=False)
    phase_id = Column(PGUUID(as_uuid=True), ForeignKey('implementation_phases.id'), nullable=False)
    mandatory = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    requirement = relationship("Requirement", back_populates="phases")
    phase = relationship("ImplementationPhase", back_populates="requirements")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('requirement_id', 'phase_id'),
    )

class CostComponent(Base):
    """Cost estimation components"""
    __tablename__ = 'cost_components'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    component_name = Column(String(100), nullable=False)
    component_type = Column(String(50), nullable=False)  # 'personnel', 'technology', 'consulting', 'training'
    base_cost = Column(Numeric(15, 2))
    currency = Column(String(3), default='EUR')
    unit = Column(String(50))  # 'per_month', 'per_user', 'one_time'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    requirement_costs = relationship("RequirementCost", back_populates="cost_component")

class RequirementCost(Base):
    """Cost estimates by requirement"""
    __tablename__ = 'requirement_costs'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    requirement_id = Column(PGUUID(as_uuid=True), ForeignKey('requirements.id'), nullable=False)
    cost_component_id = Column(PGUUID(as_uuid=True), ForeignKey('cost_components.id'), nullable=False)
    entity_type = Column(ENUM(EntityType))
    estimated_cost = Column(Numeric(15, 2))
    effort_days = Column(Integer)
    confidence_level = Column(String(20), default='medium')
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    requirement = relationship("Requirement", back_populates="costs")
    cost_component = relationship("CostComponent", back_populates="requirement_costs")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('requirement_id', 'cost_component_id', 'entity_type'),
    )

class SearchIndex(Base):
    """Search and indexing support"""
    __tablename__ = 'search_index'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    object_type = Column(String(50), nullable=False)  # 'article', 'requirement', 'criteria'
    object_id = Column(PGUUID(as_uuid=True), nullable=False)
    content = Column(Text, nullable=False)
    search_vector = Column(TSVECTOR)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_search_index_type', 'object_type'),
        Index('idx_search_index_vector', 'search_vector', postgresql_using='gin'),
    )

class AuditLog(Base):
    """Audit trail for changes"""
    __tablename__ = 'audit_log'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    table_name = Column(String(100), nullable=False)
    record_id = Column(PGUUID(as_uuid=True), nullable=False)
    action = Column(String(20), nullable=False)  # 'INSERT', 'UPDATE', 'DELETE'
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    changed_by = Column(String(100))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    change_reason = Column(Text)
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_log_table_record', 'table_name', 'record_id'),
    )

# Pydantic Models for API Serialization

class BaseAPIModel(BaseModel):
    """Base model with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        arbitrary_types_allowed=True
    )

class ChapterModel(BaseAPIModel):
    """Chapter API model"""
    id: UUID
    chapter_number: int
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class SectionModel(BaseAPIModel):
    """Section API model"""
    id: UUID
    section_id: str
    chapter_id: UUID
    section_number: int
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ArticleModel(BaseAPIModel):
    """Article API model"""
    id: UUID
    article_id: str
    article_number: int
    title: str
    chapter_id: UUID
    section_id: Optional[UUID] = None
    effective_date: date
    implementation_deadline: date
    pillar: PillarType
    created_at: datetime
    updated_at: datetime

class RequirementModel(BaseAPIModel):
    """Requirement API model"""
    id: UUID
    requirement_id: str
    article_id: UUID
    paragraph_id: Optional[UUID] = None
    title: str
    description: str
    category: str
    pillar: PillarType
    requirement_type: RequirementType
    compliance_level: ComplianceLevel
    implementation_guidance: Optional[str] = None
    common_gaps: Optional[List[str]] = None
    remediation_steps: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

class ComplianceCriteriaModel(BaseAPIModel):
    """Compliance criteria API model"""
    id: UUID
    criteria_id: str
    requirement_id: UUID
    criterion: str
    assessment_method: AssessmentMethod
    evidence_type: EvidenceType
    weight: Decimal
    automation_feasibility: str
    validation_rules: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

class ScoringRubricModel(BaseAPIModel):
    """Scoring rubric API model"""
    id: UUID
    requirement_id: UUID
    score_range: str
    level_name: str
    description: str
    characteristics: Optional[List[str]] = None
    risk_level: RiskLevel
    created_at: datetime

class RequirementMappingModel(BaseAPIModel):
    """Requirement mapping API model"""
    id: UUID
    requirement_id: UUID
    standard_id: UUID
    standard_reference: str
    mapping_description: Optional[str] = None
    confidence_level: str
    created_at: datetime

class IndustryBenchmarkModel(BaseAPIModel):
    """Industry benchmark API model"""
    id: UUID
    benchmark_id: str
    title: str
    description: Optional[str] = None
    entity_type: Optional[EntityType] = None
    asset_size_category: Optional[str] = None
    maturity_level: Optional[str] = None
    implementation_cost_estimate: Optional[Decimal] = None
    currency: str
    timeline_estimate: Optional[int] = None
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Complex response models for API endpoints

class ArticleDetailModel(ArticleModel):
    """Detailed article with relationships"""
    chapter: Optional[ChapterModel] = None
    section: Optional[SectionModel] = None
    requirements: List[RequirementModel] = []

class RequirementDetailModel(RequirementModel):
    """Detailed requirement with all related data"""
    article: Optional[ArticleModel] = None
    evidence_requirements: List[Dict[str, Any]] = []
    compliance_criteria: List[ComplianceCriteriaModel] = []
    scoring_rubrics: List[ScoringRubricModel] = []
    mappings: List[RequirementMappingModel] = []

class ComplianceAssessmentModel(BaseAPIModel):
    """Compliance assessment result"""
    requirement_id: str
    title: str
    score: int = Field(ge=1, le=10)
    level_name: str
    risk_level: RiskLevel
    evidence_provided: Dict[str, Any]
    gaps_identified: List[str] = []
    recommendations: List[str] = []
    assessed_at: datetime

class KnowledgeBaseStats(BaseAPIModel):
    """Knowledge base statistics"""
    total_articles: int
    total_requirements: int
    total_criteria: int
    pillars_covered: List[PillarType]
    entity_types_supported: List[EntityType]
    last_updated: datetime

# Create table models mapping for easier access
TABLE_MODELS = {
    'chapters': Chapter,
    'sections': Section,
    'articles': Article,
    'requirements': Requirement,
    'compliance_criteria': ComplianceCriteria,
    'scoring_rubrics': ScoringRubric,
    'regulatory_standards': RegulatoryStandard,
    'requirement_mappings': RequirementMapping,
    'technical_standards': TechnicalStandard,
    'industry_benchmarks': IndustryBenchmark,
    'implementation_phases': ImplementationPhase,
    'cost_components': CostComponent,
    'search_index': SearchIndex,
    'audit_log': AuditLog,
}

# API model mapping
API_MODELS = {
    'chapter': ChapterModel,
    'section': SectionModel, 
    'article': ArticleModel,
    'requirement': RequirementModel,
    'compliance_criteria': ComplianceCriteriaModel,
    'scoring_rubric': ScoringRubricModel,
    'requirement_mapping': RequirementMappingModel,
    'industry_benchmark': IndustryBenchmarkModel,
} 