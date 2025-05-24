#!/usr/bin/env python3
"""
DORA Knowledge Base Database Initialization

This script initializes the DORA Knowledge Base database with:
- Database schema creation
- Initial sample data loading
- Regulatory standards setup
- Entity definitions
- Basic DORA structure

Usage:
    python init_database.py --create-schema --load-sample-data
"""

import asyncio
import logging
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import sys

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the parent directory to path to import our models
sys.path.append(str(Path(__file__).parent.parent))
from schemas.data_models import (
    Base, 
    Chapter, Section, Article, ArticleParagraph,
    EntityDefinition, ArticleApplicability,
    Requirement, EvidenceRequirement, ComplianceCriteria, ScoringRubric,
    RegulatoryStandard, RequirementMapping,
    TechnicalStandard, IndustryBenchmark,
    ImplementationPhase, CostComponent,
    EntityType, TierClassification, PillarType, RequirementType,
    ComplianceLevel, AssessmentMethod, EvidenceType, RiskLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql://postgres:password@localhost:5432/dora_kb"
ASYNC_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/dora_kb"

class DORADatabaseInitializer:
    """Initializes the DORA Knowledge Base database"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def create_database_schema(self):
        """Create all database tables and indexes"""
        logger.info("Creating database schema...")
        
        try:
            # Create all tables
            Base.metadata.create_all(self.engine)
            logger.info("Database schema created successfully")
            
            # Execute additional SQL for triggers and functions
            with self.engine.connect() as conn:
                # Enable extensions
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\""))
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"unaccent\""))
                conn.commit()
                
            logger.info("Database extensions enabled")
            
        except Exception as e:
            logger.error(f"Error creating database schema: {e}")
            raise
    
    def load_sample_data(self):
        """Load initial sample data for testing and demonstration"""
        logger.info("Loading sample data...")
        
        with self.Session() as session:
            try:
                # Load chapters
                chapters_data = self._get_chapters_data()
                for chapter_data in chapters_data:
                    chapter = Chapter(**chapter_data)
                    session.add(chapter)
                
                session.flush()  # Get IDs for foreign keys
                
                # Load sections
                sections_data = self._get_sections_data(session)
                for section_data in sections_data:
                    section = Section(**section_data)
                    session.add(section)
                
                session.flush()
                
                # Load articles
                articles_data = self._get_articles_data(session)
                for article_data in articles_data:
                    article = Article(**article_data)
                    session.add(article)
                
                session.flush()
                
                # Load entity definitions
                entity_definitions = self._get_entity_definitions()
                for entity_def in entity_definitions:
                    entity = EntityDefinition(**entity_def)
                    session.add(entity)
                
                # Load regulatory standards
                standards_data = self._get_regulatory_standards()
                for standard_data in standards_data:
                    standard = RegulatoryStandard(**standard_data)
                    session.add(standard)
                
                # Load implementation phases
                phases_data = self._get_implementation_phases()
                for phase_data in phases_data:
                    phase = ImplementationPhase(**phase_data)
                    session.add(phase)
                
                # Load cost components
                cost_components_data = self._get_cost_components()
                for cost_data in cost_components_data:
                    cost_component = CostComponent(**cost_data)
                    session.add(cost_component)
                
                session.flush()
                
                # Load sample requirements
                requirements_data = self._get_sample_requirements(session)
                for req_data in requirements_data:
                    requirement = Requirement(**req_data)
                    session.add(requirement)
                
                session.flush()
                
                # Load sample compliance criteria
                criteria_data = self._get_sample_compliance_criteria(session)
                for criteria in criteria_data:
                    compliance_criteria = ComplianceCriteria(**criteria)
                    session.add(compliance_criteria)
                
                # Load sample scoring rubrics
                rubrics_data = self._get_sample_scoring_rubrics(session)
                for rubric_data in rubrics_data:
                    rubric = ScoringRubric(**rubric_data)
                    session.add(rubric)
                
                session.commit()
                logger.info("Sample data loaded successfully")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error loading sample data: {e}")
                raise
    
    def _get_chapters_data(self):
        """Get DORA chapters data"""
        return [
            {
                "chapter_number": 1,
                "title": "General provisions",
                "description": "Subject matter, scope and definitions"
            },
            {
                "chapter_number": 2,
                "title": "ICT risk management",
                "description": "ICT risk management framework requirements"
            },
            {
                "chapter_number": 3,
                "title": "ICT-related incident management, classification and reporting",
                "description": "Requirements for managing and reporting ICT incidents"
            },
            {
                "chapter_number": 4,
                "title": "Digital operational resilience testing",
                "description": "Testing framework and TLPT requirements"
            },
            {
                "chapter_number": 5,
                "title": "Managing ICT third-party risk",
                "description": "Third-party risk management requirements"
            },
            {
                "chapter_number": 6,
                "title": "Information and intelligence sharing",
                "description": "Cyber threat information sharing arrangements"
            }
        ]
    
    def _get_sections_data(self, session):
        """Get DORA sections data"""
        chapters = {ch.chapter_number: ch.id for ch in session.query(Chapter).all()}
        
        return [
            {
                "section_id": "section_1_1",
                "chapter_id": chapters[1],
                "section_number": 1,
                "title": "Subject matter, scope and definitions",
                "description": "Fundamental definitions and scope"
            },
            {
                "section_id": "section_2_1", 
                "chapter_id": chapters[2],
                "section_number": 1,
                "title": "ICT risk management framework",
                "description": "Requirements for ICT risk management"
            },
            {
                "section_id": "section_3_1",
                "chapter_id": chapters[3], 
                "section_number": 1,
                "title": "ICT-related incident management",
                "description": "Incident management processes"
            }
        ]
    
    def _get_articles_data(self, session):
        """Get sample DORA articles data"""
        chapters = {ch.chapter_number: ch.id for ch in session.query(Chapter).all()}
        sections = {s.section_id: s.id for s in session.query(Section).all()}
        
        return [
            {
                "article_id": "art_1",
                "article_number": 1,
                "title": "Subject matter and scope",
                "chapter_id": chapters[1],
                "section_id": sections["section_1_1"],
                "pillar": PillarType.GOVERNANCE_ARRANGEMENTS,
                "effective_date": date(2025, 1, 17),
                "implementation_deadline": date(2025, 1, 17)
            },
            {
                "article_id": "art_5",
                "article_number": 5,
                "title": "ICT risk management framework",
                "chapter_id": chapters[2],
                "section_id": sections["section_2_1"],
                "pillar": PillarType.GOVERNANCE_ARRANGEMENTS,
                "effective_date": date(2025, 1, 17),
                "implementation_deadline": date(2025, 1, 17)
            },
            {
                "article_id": "art_17",
                "article_number": 17,
                "title": "ICT-related incident management process",
                "chapter_id": chapters[3],
                "section_id": sections["section_3_1"],
                "pillar": PillarType.ICT_RELATED_INCIDENTS,
                "effective_date": date(2025, 1, 17),
                "implementation_deadline": date(2025, 1, 17)
            }
        ]
    
    def _get_entity_definitions(self):
        """Get entity type definitions"""
        return [
            {
                "entity_type": EntityType.CREDIT_INSTITUTION,
                "tier": TierClassification.TIER_1,
                "threshold_description": "€5 billion total assets",
                "threshold_amount": Decimal("5000000000"),
                "enhanced_requirements": True,
                "testing_frequency": "annual"
            },
            {
                "entity_type": EntityType.PAYMENT_INSTITUTION,
                "tier": TierClassification.TIER_1,
                "threshold_description": "€1 billion payment volume",
                "threshold_amount": Decimal("1000000000"),
                "enhanced_requirements": True,
                "testing_frequency": "annual"
            },
            {
                "entity_type": EntityType.INVESTMENT_FIRM,
                "tier": TierClassification.TIER_2,
                "threshold_description": "Below €5 billion assets under management",
                "enhanced_requirements": False,
                "testing_frequency": "triennial",
                "simplified_requirements": True
            }
        ]
    
    def _get_regulatory_standards(self):
        """Get regulatory standards for cross-mapping"""
        return [
            {
                "standard_name": "ISO 27001:2022",
                "version": "2022",
                "description": "Information security management systems",
                "alignment_percentage": 85
            },
            {
                "standard_name": "NIST Cybersecurity Framework",
                "version": "1.1",
                "description": "Framework for improving critical infrastructure cybersecurity",
                "alignment_percentage": 90
            },
            {
                "standard_name": "Basel III",
                "version": "2017",
                "description": "International regulatory framework for banks",
                "alignment_percentage": 70
            },
            {
                "standard_name": "PCI DSS",
                "version": "4.0",
                "description": "Payment Card Industry Data Security Standard",
                "alignment_percentage": 60
            }
        ]
    
    def _get_implementation_phases(self):
        """Get implementation timeline phases"""
        return [
            {
                "phase_name": "Phase 1 - Immediate",
                "effective_date": date(2025, 1, 17),
                "description": "Basic governance and incident reporting",
                "entity_scope": "All entities"
            },
            {
                "phase_name": "Phase 2 - Enhanced",
                "effective_date": date(2025, 7, 17),
                "description": "TLPT and enhanced oversight",
                "entity_scope": "Tier 1 entities only"
            },
            {
                "phase_name": "Phase 3 - Optimization",
                "effective_date": date(2026, 1, 17),
                "description": "Continuous monitoring and automation",
                "entity_scope": "All entities"
            }
        ]
    
    def _get_cost_components(self):
        """Get cost estimation components"""
        return [
            {
                "component_name": "CISO Personnel",
                "component_type": "personnel",
                "base_cost": Decimal("120000"),
                "currency": "EUR",
                "unit": "per_year"
            },
            {
                "component_name": "SIEM Platform",
                "component_type": "technology",
                "base_cost": Decimal("50000"),
                "currency": "EUR", 
                "unit": "per_year"
            },
            {
                "component_name": "Compliance Consulting",
                "component_type": "consulting",
                "base_cost": Decimal("1500"),
                "currency": "EUR",
                "unit": "per_day"
            },
            {
                "component_name": "Staff Training",
                "component_type": "training",
                "base_cost": Decimal("2000"),
                "currency": "EUR",
                "unit": "per_user"
            }
        ]
    
    def _get_sample_requirements(self, session):
        """Get sample requirements data"""
        articles = {a.article_id: a.id for a in session.query(Article).all()}
        
        return [
            {
                "requirement_id": "req_5_1",
                "article_id": articles["art_5"],
                "title": "ICT risk management framework establishment",
                "description": "Financial entities shall maintain a comprehensive ICT risk management framework as part of their overall risk management system.",
                "category": "governance",
                "pillar": PillarType.GOVERNANCE_ARRANGEMENTS,
                "requirement_type": RequirementType.MANDATORY,
                "compliance_level": ComplianceLevel.LEVEL_2,
                "implementation_guidance": "Establish documented ICT risk management policies approved by the management body.",
                "common_gaps": ["Lack of board approval", "Insufficient documentation", "Missing periodic review"],
                "remediation_steps": ["Develop comprehensive policy", "Obtain board approval", "Implement review process"]
            },
            {
                "requirement_id": "req_17_1",
                "article_id": articles["art_17"],
                "title": "ICT incident management process",
                "description": "Financial entities shall have in place a comprehensive ICT-related incident management process.",
                "category": "incident_management",
                "pillar": PillarType.ICT_RELATED_INCIDENTS,
                "requirement_type": RequirementType.MANDATORY,
                "compliance_level": ComplianceLevel.LEVEL_2,
                "implementation_guidance": "Implement structured incident response procedures with clear roles and responsibilities.",
                "common_gaps": ["No formal process", "Unclear escalation", "Poor documentation"],
                "remediation_steps": ["Design incident process", "Define roles", "Implement tooling"]
            }
        ]
    
    def _get_sample_compliance_criteria(self, session):
        """Get sample compliance criteria"""
        requirements = {r.requirement_id: r.id for r in session.query(Requirement).all()}
        
        return [
            {
                "criteria_id": "crit_5_1_1",
                "requirement_id": requirements["req_5_1"],
                "criterion": "ICT risk management policy exists and is approved by management body",
                "assessment_method": AssessmentMethod.MANUAL,
                "evidence_type": EvidenceType.POLICY_DOCUMENT,
                "weight": Decimal("0.4"),
                "automation_feasibility": "low",
                "validation_rules": ["policy_document_exists", "board_approval_documented"]
            },
            {
                "criteria_id": "crit_17_1_1", 
                "requirement_id": requirements["req_17_1"],
                "criterion": "Incident management process is documented and implemented",
                "assessment_method": AssessmentMethod.HYBRID,
                "evidence_type": EvidenceType.PROCEDURE_DOCUMENT,
                "weight": Decimal("0.5"),
                "automation_feasibility": "medium",
                "validation_rules": ["process_documented", "roles_defined", "tools_implemented"]
            }
        ]
    
    def _get_sample_scoring_rubrics(self, session):
        """Get sample scoring rubrics"""
        requirements = {r.requirement_id: r.id for r in session.query(Requirement).all()}
        
        return [
            {
                "requirement_id": requirements["req_5_1"],
                "score_range": "1-2",
                "level_name": "Non-compliant",
                "description": "No ICT risk management framework in place",
                "characteristics": ["No policy exists", "No board awareness", "No risk assessment"],
                "risk_level": RiskLevel.CRITICAL
            },
            {
                "requirement_id": requirements["req_5_1"],
                "score_range": "3-4",
                "level_name": "Minimal compliance",
                "description": "Basic framework exists but significant gaps",
                "characteristics": ["Basic policy exists", "Limited board involvement", "Ad-hoc risk assessment"],
                "risk_level": RiskLevel.HIGH
            },
            {
                "requirement_id": requirements["req_5_1"],
                "score_range": "9-10",
                "level_name": "Excellent compliance",
                "description": "Comprehensive framework with continuous improvement",
                "characteristics": ["Best-practice policy", "Full board engagement", "Continuous risk monitoring"],
                "risk_level": RiskLevel.MINIMAL
            }
        ]
    
    def verify_installation(self):
        """Verify the database installation"""
        logger.info("Verifying database installation...")
        
        with self.Session() as session:
            try:
                # Check table counts
                chapter_count = session.query(Chapter).count()
                article_count = session.query(Article).count()
                requirement_count = session.query(Requirement).count()
                criteria_count = session.query(ComplianceCriteria).count()
                
                logger.info(f"Database verification results:")
                logger.info(f"  Chapters: {chapter_count}")
                logger.info(f"  Articles: {article_count}")
                logger.info(f"  Requirements: {requirement_count}")
                logger.info(f"  Compliance Criteria: {criteria_count}")
                
                if all([chapter_count > 0, article_count > 0, requirement_count > 0]):
                    logger.info("✅ Database installation verified successfully")
                    return True
                else:
                    logger.error("❌ Database installation verification failed")
                    return False
                    
            except Exception as e:
                logger.error(f"Error during verification: {e}")
                return False


def main():
    """Main function to initialize the database"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize DORA Knowledge Base database")
    parser.add_argument("--create-schema", action="store_true", help="Create database schema")
    parser.add_argument("--load-sample-data", action="store_true", help="Load sample data")
    parser.add_argument("--verify", action="store_true", help="Verify installation")
    parser.add_argument("--database-url", default=DATABASE_URL, help="Database URL")
    
    args = parser.parse_args()
    
    # Initialize the database initializer
    initializer = DORADatabaseInitializer(args.database_url)
    
    try:
        if args.create_schema:
            initializer.create_database_schema()
        
        if args.load_sample_data:
            initializer.load_sample_data()
        
        if args.verify or (args.create_schema and args.load_sample_data):
            initializer.verify_installation()
            
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 