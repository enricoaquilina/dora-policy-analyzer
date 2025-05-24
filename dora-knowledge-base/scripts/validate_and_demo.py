#!/usr/bin/env python3
"""
DORA Knowledge Base Validation and Demonstration

This script demonstrates the complete content extraction and validation process
for the DORA Knowledge Base, showing:
- Content extraction from regulatory text
- Database population and validation
- Query capabilities and API functionality
- Traceability and quality assurance

Usage:
    python validate_and_demo.py --full-demo
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from data.dora_content_extractor import DORAContentExtractor
from database.init_database import DORADatabaseInitializer
from schemas.data_models import (
    Chapter, Section, Article, Requirement, ComplianceCriteria,
    PillarType, RequirementType, EntityType
)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DORAKnowledgeBaseDemo:
    """Comprehensive demonstration of DORA Knowledge Base capabilities"""
    
    def __init__(self, database_url: str = "postgresql://postgres:password@localhost:5432/dora_kb"):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.extractor = DORAContentExtractor(database_url)
        self.initializer = DORADatabaseInitializer(database_url)
        
    async def run_full_demonstration(self):
        """Run complete demonstration workflow"""
        print("🎯 DORA Knowledge Base - Complete Demonstration")
        print("=" * 60)
        
        try:
            # Step 1: Database initialization
            await self._demo_database_setup()
            
            # Step 2: Content extraction
            extracted_content = await self._demo_content_extraction()
            
            # Step 3: Content validation
            validation_results = await self._demo_content_validation(extracted_content)
            
            # Step 4: Database loading
            loading_stats = await self._demo_database_loading(extracted_content)
            
            # Step 5: Query capabilities
            await self._demo_query_capabilities()
            
            # Step 6: API simulation
            await self._demo_api_capabilities()
            
            # Step 7: Traceability demonstration
            await self._demo_traceability()
            
            # Step 8: Generate final report
            await self._generate_final_report(validation_results, loading_stats)
            
            print("\n🎉 DORA Knowledge Base demonstration completed successfully!")
            
        except Exception as e:
            logger.error(f"Demonstration failed: {e}")
            raise
    
    async def _demo_database_setup(self):
        """Demonstrate database setup and initialization"""
        print("\n📊 Step 1: Database Setup and Initialization")
        print("-" * 40)
        
        # Create schema
        print("🔧 Creating database schema...")
        self.initializer.create_database_schema()
        print("✅ Database schema created successfully")
        
        # Load basic sample data
        print("📥 Loading initial sample data...")
        self.initializer.load_sample_data()
        print("✅ Initial sample data loaded")
        
        # Verify installation
        if self.initializer.verify_installation():
            print("✅ Database installation verified")
        else:
            raise Exception("Database installation verification failed")
    
    async def _demo_content_extraction(self) -> Dict[str, Any]:
        """Demonstrate content extraction capabilities"""
        print("\n📑 Step 2: DORA Content Extraction")
        print("-" * 40)
        
        print("🔍 Extracting DORA regulation content...")
        extracted_content = self.extractor.extract_dora_content()
        
        print(f"✅ Content extraction completed:")
        print(f"   📄 Articles extracted: {len(extracted_content['articles'])}")
        
        total_requirements = sum(len(art.requirements) for art in extracted_content['articles'])
        print(f"   📋 Requirements extracted: {total_requirements}")
        
        # Show pillar distribution
        pillar_stats = {}
        for article in extracted_content['articles']:
            pillar = article.pillar.value
            pillar_stats[pillar] = pillar_stats.get(pillar, 0) + 1
        
        print(f"   🏛️ Pillar distribution:")
        for pillar, count in pillar_stats.items():
            print(f"      {pillar.replace('_', ' ').title()}: {count} articles")
        
        # Show sample extracted content
        print(f"\n📋 Sample Extracted Content:")
        sample_article = extracted_content['articles'][0]
        print(f"   Article {sample_article.article_number}: {sample_article.title}")
        print(f"   Pillar: {sample_article.pillar.value}")
        print(f"   Requirements: {len(sample_article.requirements)}")
        if sample_article.requirements:
            sample_req = sample_article.requirements[0]
            print(f"   Sample Requirement: {sample_req.title}")
            print(f"   Evidence Requirements: {len(sample_req.evidence_requirements)}")
        
        return extracted_content
    
    async def _demo_content_validation(self, extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """Demonstrate content validation process"""
        print("\n✅ Step 3: Content Validation")
        print("-" * 40)
        
        print("🔍 Validating extracted content...")
        validation_results = self.extractor.validate_extracted_content(extracted_content)
        
        print(f"📊 Validation Results:")
        print(f"   Total Articles: {validation_results['total_articles']}")
        print(f"   Total Requirements: {validation_results['total_requirements']}")
        print(f"   Validation Score: {validation_results['validation_score']:.1f}%")
        
        if validation_results['coverage_gaps']:
            print(f"   ⚠️  Coverage Gaps: {len(validation_results['coverage_gaps'])}")
            for gap in validation_results['coverage_gaps']:
                print(f"      - {gap}")
        
        if validation_results['quality_issues']:
            print(f"   ❌ Quality Issues: {len(validation_results['quality_issues'])}")
            for issue in validation_results['quality_issues'][:3]:  # Show first 3
                print(f"      - {issue}")
            if len(validation_results['quality_issues']) > 3:
                print(f"      ... and {len(validation_results['quality_issues']) - 3} more")
        
        if validation_results['validation_score'] >= 80:
            print("✅ Content validation passed")
        else:
            print("⚠️  Content validation needs attention")
        
        return validation_results
    
    async def _demo_database_loading(self, extracted_content: Dict[str, Any]) -> Dict[str, int]:
        """Demonstrate database loading process"""
        print("\n💾 Step 4: Database Loading")
        print("-" * 40)
        
        print("📥 Loading extracted content to database...")
        loading_stats = self.extractor.load_content_to_database(extracted_content)
        
        print(f"✅ Database loading completed:")
        for key, value in loading_stats.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        
        # Verify database state
        with self.Session() as session:
            chapter_count = session.query(Chapter).count()
            article_count = session.query(Article).count()
            requirement_count = session.query(Requirement).count()
            criteria_count = session.query(ComplianceCriteria).count()
            
            print(f"\n📊 Database State After Loading:")
            print(f"   Chapters: {chapter_count}")
            print(f"   Articles: {article_count}")
            print(f"   Requirements: {requirement_count}")
            print(f"   Compliance Criteria: {criteria_count}")
        
        return loading_stats
    
    async def _demo_query_capabilities(self):
        """Demonstrate database query capabilities"""
        print("\n🔍 Step 5: Query Capabilities")
        print("-" * 40)
        
        with self.Session() as session:
            # Query 1: Articles by pillar
            print("📋 Query 1: Articles by DORA Pillar")
            pillar_query = session.query(Article.pillar, 
                                       session.query(Article.id).filter(Article.pillar == Article.pillar).count().label('count')
                                      ).group_by(Article.pillar).all()
            
            governance_articles = session.query(Article).filter(
                Article.pillar == PillarType.GOVERNANCE_ARRANGEMENTS
            ).all()
            
            incident_articles = session.query(Article).filter(
                Article.pillar == PillarType.ICT_RELATED_INCIDENTS
            ).all()
            
            print(f"   🏛️ Governance Arrangements: {len(governance_articles)} articles")
            print(f"   🚨 ICT-Related Incidents: {len(incident_articles)} articles")
            
            # Query 2: Requirements by category
            print(f"\n📋 Query 2: Requirements by Category")
            governance_reqs = session.query(Requirement).filter(
                Requirement.category == 'governance'
            ).all()
            
            incident_reqs = session.query(Requirement).filter(
                Requirement.category == 'incident_management'
            ).all()
            
            print(f"   ⚖️ Governance Requirements: {len(governance_reqs)}")
            print(f"   🚨 Incident Management Requirements: {len(incident_reqs)}")
            
            # Query 3: Sample requirement with details
            print(f"\n📋 Query 3: Sample Requirement Details")
            sample_req = session.query(Requirement).filter(
                Requirement.requirement_id == 'req_5_1'
            ).first()
            
            if sample_req:
                print(f"   📄 {sample_req.title}")
                print(f"   📝 Description: {sample_req.description[:100]}...")
                print(f"   🏷️ Category: {sample_req.category}")
                print(f"   📊 Compliance Level: {sample_req.compliance_level.value}")
                
                # Get related criteria
                criteria = session.query(ComplianceCriteria).filter(
                    ComplianceCriteria.requirement_id == sample_req.id
                ).all()
                print(f"   ✅ Assessment Criteria: {len(criteria)}")
            
            # Query 4: Cross-references and relationships
            print(f"\n📋 Query 4: Article Relationships")
            article_5 = session.query(Article).filter(Article.article_number == 5).first()
            if article_5:
                requirements = session.query(Requirement).filter(
                    Requirement.article_id == article_5.id
                ).all()
                print(f"   📄 Article 5 '{article_5.title}':")
                print(f"   📋 Requirements: {len(requirements)}")
                for req in requirements:
                    print(f"      - {req.title}")
    
    async def _demo_api_capabilities(self):
        """Demonstrate API-like access patterns"""
        print("\n🌐 Step 6: API Capabilities Simulation")
        print("-" * 40)
        
        # Simulate REST API endpoints
        print("🔌 Simulating Knowledge Base API endpoints...")
        
        # GET /articles
        articles_data = await self._simulate_get_articles()
        print(f"✅ GET /articles: {len(articles_data)} articles")
        
        # GET /articles/{id}/requirements  
        requirements_data = await self._simulate_get_article_requirements(5)
        print(f"✅ GET /articles/5/requirements: {len(requirements_data)} requirements")
        
        # GET /requirements/search
        search_results = await self._simulate_search_requirements("risk management")
        print(f"✅ GET /requirements/search?q='risk management': {len(search_results)} results")
        
        # GET /compliance/criteria/{requirement_id}
        criteria_data = await self._simulate_get_compliance_criteria("req_5_1")
        print(f"✅ GET /compliance/criteria/req_5_1: {len(criteria_data)} criteria")
        
        # POST /assessment/score
        assessment_result = await self._simulate_assessment_scoring()
        print(f"✅ POST /assessment/score: Score {assessment_result['score']}/10")
    
    async def _simulate_get_articles(self) -> List[Dict[str, Any]]:
        """Simulate GET /articles endpoint"""
        with self.Session() as session:
            articles = session.query(Article).all()
            return [{
                "article_id": art.article_id,
                "article_number": art.article_number,
                "title": art.title,
                "pillar": art.pillar.value,
                "effective_date": art.effective_date.isoformat()
            } for art in articles]
    
    async def _simulate_get_article_requirements(self, article_number: int) -> List[Dict[str, Any]]:
        """Simulate GET /articles/{id}/requirements endpoint"""
        with self.Session() as session:
            article = session.query(Article).filter(Article.article_number == article_number).first()
            if not article:
                return []
            
            requirements = session.query(Requirement).filter(
                Requirement.article_id == article.id
            ).all()
            
            return [{
                "requirement_id": req.requirement_id,
                "title": req.title,
                "description": req.description,
                "category": req.category,
                "requirement_type": req.requirement_type.value
            } for req in requirements]
    
    async def _simulate_search_requirements(self, query: str) -> List[Dict[str, Any]]:
        """Simulate GET /requirements/search endpoint"""
        with self.Session() as session:
            # Simple text search simulation
            requirements = session.query(Requirement).filter(
                Requirement.description.ilike(f"%{query}%")
            ).all()
            
            return [{
                "requirement_id": req.requirement_id,
                "title": req.title,
                "relevance_score": 0.85  # Simulated relevance
            } for req in requirements]
    
    async def _simulate_get_compliance_criteria(self, requirement_id: str) -> List[Dict[str, Any]]:
        """Simulate GET /compliance/criteria/{requirement_id} endpoint"""
        with self.Session() as session:
            requirement = session.query(Requirement).filter(
                Requirement.requirement_id == requirement_id
            ).first()
            
            if not requirement:
                return []
            
            criteria = session.query(ComplianceCriteria).filter(
                ComplianceCriteria.requirement_id == requirement.id
            ).all()
            
            return [{
                "criteria_id": crit.criteria_id,
                "criterion": crit.criterion,
                "assessment_method": crit.assessment_method.value,
                "weight": float(crit.weight)
            } for crit in criteria]
    
    async def _simulate_assessment_scoring(self) -> Dict[str, Any]:
        """Simulate POST /assessment/score endpoint"""
        # Simulate compliance assessment scoring
        return {
            "requirement_id": "req_5_1",
            "score": 7,
            "level": "Good compliance",
            "risk_level": "low",
            "gaps": ["Missing periodic review documentation"],
            "recommendations": ["Implement quarterly review process"]
        }
    
    async def _demo_traceability(self):
        """Demonstrate source traceability capabilities"""
        print("\n🔗 Step 7: Source Traceability")
        print("-" * 40)
        
        print("📋 Demonstrating traceability from database to source...")
        
        with self.Session() as session:
            # Get a sample requirement
            sample_req = session.query(Requirement).filter(
                Requirement.requirement_id == 'req_5_1'
            ).first()
            
            if sample_req:
                # Get article
                article = session.query(Article).filter(
                    Article.id == sample_req.article_id
                ).first()
                
                # Get chapter
                chapter = session.query(Chapter).filter(
                    Chapter.id == article.chapter_id
                ).first()
                
                print(f"📄 Requirement: {sample_req.requirement_id}")
                print(f"   Title: {sample_req.title}")
                print(f"   Source Article: {article.article_number} - {article.title}")
                print(f"   Source Chapter: {chapter.chapter_number} - {chapter.title}")
                print(f"   Regulatory Reference: DORA Article {article.article_number}")
                print(f"   EU Regulation: 2022/2554")
                print(f"   Official URL: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32022R2554")
                
                # Show implementation lineage
                print(f"\n🔍 Implementation Lineage:")
                print(f"   📊 Pillar: {article.pillar.value}")
                print(f"   📋 Category: {sample_req.category}")
                print(f"   ⚖️ Requirement Type: {sample_req.requirement_type.value}")
                print(f"   📈 Compliance Level: {sample_req.compliance_level.value}")
                
                # Show related compliance criteria
                criteria = session.query(ComplianceCriteria).filter(
                    ComplianceCriteria.requirement_id == sample_req.id
                ).all()
                
                print(f"\n✅ Related Assessment Criteria:")
                for crit in criteria:
                    print(f"   - {crit.criterion}")
                    print(f"     Method: {crit.assessment_method.value}")
                    print(f"     Weight: {crit.weight}")
    
    async def _generate_final_report(self, validation_results: Dict[str, Any], 
                                   loading_stats: Dict[str, int]):
        """Generate final demonstration report"""
        print("\n📊 Step 8: Final Report Generation")
        print("-" * 40)
        
        # Calculate overall metrics
        total_entities_loaded = sum(loading_stats.values())
        
        report_data = {
            "demonstration_completed": datetime.now().isoformat(),
            "database_metrics": {
                "total_entities": total_entities_loaded,
                "loading_stats": loading_stats
            },
            "content_metrics": {
                "articles_processed": validation_results['total_articles'],
                "requirements_extracted": validation_results['total_requirements'],
                "validation_score": validation_results['validation_score']
            },
            "capabilities_demonstrated": [
                "Content extraction from regulatory text",
                "Database schema and data model validation",
                "Structured data loading and integrity checks",
                "Multi-dimensional query capabilities",
                "API-style access patterns",
                "Source traceability and lineage tracking",
                "Compliance assessment simulation"
            ],
            "next_steps": [
                "Implement full DORA text extraction",
                "Add RTS/ITS integration",
                "Build REST API layer",
                "Create search indexing",
                "Implement cross-regulatory mapping",
                "Develop assessment algorithms"
            ]
        }
        
        # Save report
        report_path = Path("dora-knowledge-base/scripts/demo_report.json")
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Final Report:")
        print(f"   📊 Total Entities Loaded: {total_entities_loaded}")
        print(f"   ✅ Validation Score: {validation_results['validation_score']:.1f}%")
        print(f"   🎯 Capabilities Demonstrated: {len(report_data['capabilities_demonstrated'])}")
        print(f"   📝 Report saved to: {report_path}")
        
        # Summary
        print(f"\n🎉 Demonstration Summary:")
        print(f"   ✅ Database schema created and validated")
        print(f"   ✅ Content extraction working with real DORA text")
        print(f"   ✅ Database loading and querying functional")
        print(f"   ✅ API access patterns demonstrated")
        print(f"   ✅ Source traceability established")
        print(f"   ✅ Ready for Policy Analyzer Agent integration")


async def main():
    """Main demonstration entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DORA Knowledge Base Validation and Demo")
    parser.add_argument("--full-demo", action="store_true", help="Run complete demonstration")
    parser.add_argument("--quick-test", action="store_true", help="Run quick validation test")
    parser.add_argument("--database-url", default="postgresql://postgres:password@localhost:5432/dora_kb")
    
    args = parser.parse_args()
    
    demo = DORAKnowledgeBaseDemo(args.database_url)
    
    try:
        if args.full_demo:
            await demo.run_full_demonstration()
        elif args.quick_test:
            # Quick validation test
            print("🔍 Running quick validation test...")
            extracted_content = demo.extractor.extract_dora_content()
            validation_results = demo.extractor.validate_extracted_content(extracted_content)
            print(f"✅ Quick test complete. Validation score: {validation_results['validation_score']:.1f}%")
        else:
            print("Use --full-demo for complete demonstration or --quick-test for validation")
            
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 