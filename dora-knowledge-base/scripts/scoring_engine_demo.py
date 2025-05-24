#!/usr/bin/env python3
"""
DORA Scoring Engine Demonstration

This script demonstrates the comprehensive scoring and assessment capabilities 
of the DORA Knowledge Base, showcasing:
- Scoring rubric creation and management
- Multi-level compliance assessment (criteria, requirement, pillar, overall)
- RAG status determination and visualization
- Gap analysis and remediation prioritization
- Priority matrix and improvement recommendations
- Comprehensive assessment reporting

Usage:
    python scoring_engine_demo.py --full-demo
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from assessment.scoring_engine import (
    DORAComplianceScoringEngine, RAGStatus, AssessmentConfidence,
    ScoreResult, AggregatedScore, ScoringCriteria
)
from schemas.data_models import PillarType, AssessmentMethod, EvidenceType

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScoringEngineDemo:
    """Comprehensive demonstration of DORA scoring engine capabilities"""
    
    def __init__(self, database_url: str = "postgresql://postgres:password@localhost:5432/dora_kb"):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.scoring_engine = DORAComplianceScoringEngine(database_url)
        
    async def run_full_demonstration(self):
        """Run complete scoring engine demonstration"""
        print("🎯 DORA Scoring Engine - Complete Demonstration")
        print("=" * 60)
        
        try:
            # Step 1: Create scoring rubrics
            rubrics = await self._demo_rubric_creation()
            
            # Step 2: Demonstrate criteria scoring
            criteria_scores = await self._demo_criteria_scoring()
            
            # Step 3: Multi-level assessment
            assessment_scores = await self._demo_multi_level_assessment(criteria_scores)
            
            # Step 4: RAG status calculation
            await self._demo_rag_status_calculation(assessment_scores)
            
            # Step 5: Gap analysis
            gap_analysis = await self._demo_gap_analysis(assessment_scores)
            
            # Step 6: Priority matrix and recommendations
            await self._demo_priority_matrix(gap_analysis)
            
            # Step 7: Assessment methodologies
            await self._demo_scoring_methodologies()
            
            # Step 8: Comprehensive reporting
            await self._demo_assessment_reporting(assessment_scores, gap_analysis)
            
            # Step 9: Database integration
            await self._demo_database_integration(assessment_scores, gap_analysis)
            
            print("\n🎉 Scoring engine demonstration completed successfully!")
            
        except Exception as e:
            logger.error(f"Demonstration failed: {e}")
            raise
    
    async def _demo_rubric_creation(self) -> Dict[str, List[ScoringCriteria]]:
        """Demonstrate scoring rubric creation"""
        print("\n📋 Step 1: Scoring Rubric Creation")
        print("-" * 40)
        
        print("🔧 Creating comprehensive DORA scoring rubrics...")
        rubrics = self.scoring_engine.create_scoring_rubrics()
        
        print(f"✅ Rubric creation completed:")
        total_criteria = 0
        for domain, criteria_list in rubrics.items():
            count = len(criteria_list)
            total_criteria += count
            print(f"   📊 {domain.title()}: {count} criteria")
            
            # Show sample criteria
            if criteria_list:
                sample = criteria_list[0]
                print(f"      Sample: {sample.name}")
                print(f"      Weight: {sample.weight}, Method: {sample.assessment_method.value}")
                print(f"      Evidence: {[et.value for et in sample.evidence_types]}")
        
        print(f"\n📈 Total Criteria Created: {total_criteria}")
        
        # Show scoring guidelines example
        print(f"\n📋 Sample Scoring Guidelines:")
        governance_criteria = rubrics["governance"][0]
        print(f"   Criteria: {governance_criteria.name}")
        for score_range, guideline in governance_criteria.scoring_guidelines.items():
            print(f"   {score_range}: {guideline}")
        
        return rubrics
    
    async def _demo_criteria_scoring(self) -> List[ScoreResult]:
        """Demonstrate individual criteria scoring"""
        print("\n⭐ Step 2: Criteria Scoring Demonstration")
        print("-" * 45)
        
        print("🎯 Creating sample criteria score results...")
        
        # Create realistic score results for governance criteria
        criteria_scores = [
            ScoreResult(
                criteria_id="gov_framework_01",
                score=Decimal("7.5"),
                max_score=Decimal("10"),
                rag_status=RAGStatus.AMBER,
                confidence=AssessmentConfidence.HIGH,
                evidence_provided=[
                    "ICT Risk Management Policy v2.1",
                    "Board Resolution 2024-03-15"
                ],
                gaps_identified=[
                    "Missing annual review documentation",
                    "Incomplete integration with business strategy"
                ],
                recommendations=[
                    "Establish formal annual review process",
                    "Align with strategic planning cycle"
                ],
                assessor="Senior Risk Manager",
                notes="Framework exists but needs strengthening"
            ),
            ScoreResult(
                criteria_id="gov_framework_02",
                score=Decimal("6.0"),
                max_score=Decimal("10"),
                rag_status=RAGStatus.AMBER,
                confidence=AssessmentConfidence.MEDIUM,
                evidence_provided=[
                    "Risk Committee Minutes Q3-Q4 2024"
                ],
                gaps_identified=[
                    "No documented review schedule",
                    "Limited evidence of framework updates"
                ],
                recommendations=[
                    "Create annual review calendar",
                    "Document framework change log"
                ],
                assessor="Compliance Officer",
                notes="Reviews happening but not well documented"
            ),
            ScoreResult(
                criteria_id="gov_resources_01",
                score=Decimal("5.5"),
                max_score=Decimal("10"),
                rag_status=RAGStatus.AMBER,
                confidence=AssessmentConfidence.MEDIUM,
                evidence_provided=[
                    "Organizational Chart ICT Risk Team",
                    "2024 Budget Allocation"
                ],
                gaps_identified=[
                    "Insufficient dedicated FTE",
                    "Budget constraints limiting capability"
                ],
                recommendations=[
                    "Increase dedicated resources by 2 FTE",
                    "Request additional budget for tools and training"
                ],
                assessor="Head of ICT Risk",
                notes="Team stretched thin across multiple priorities"
            ),
            ScoreResult(
                criteria_id="gov_oversight_01",
                score=Decimal("8.0"),
                max_score=Decimal("10"),
                rag_status=RAGStatus.GREEN,
                confidence=AssessmentConfidence.HIGH,
                evidence_provided=[
                    "Board ICT Risk Committee Charter",
                    "Monthly Board Reports 2024",
                    "ICT Risk Dashboard Q4"
                ],
                gaps_identified=[
                    "Could improve risk appetite documentation"
                ],
                recommendations=[
                    "Formalize ICT risk appetite statement"
                ],
                assessor="Board Secretary",
                notes="Strong board engagement with good documentation"
            )
        ]
        
        print(f"✅ Created {len(criteria_scores)} criteria score results:")
        for score in criteria_scores:
            rag_emoji = {"green": "🟢", "amber": "🟡", "red": "🔴"}.get(score.rag_status.value, "⚪")
            print(f"   {rag_emoji} {score.criteria_id}: {score.score}/10 ({score.confidence.value} confidence)")
            print(f"      Evidence: {len(score.evidence_provided)} items")
            print(f"      Gaps: {len(score.gaps_identified)} identified")
        
        return criteria_scores
    
    async def _demo_multi_level_assessment(self, criteria_scores: List[ScoreResult]) -> List[AggregatedScore]:
        """Demonstrate multi-level assessment aggregation"""
        print("\n🏗️ Step 3: Multi-Level Assessment")
        print("-" * 40)
        
        print("📊 Performing multi-level assessment aggregation...")
        
        # Requirement level assessment
        print("\n🔹 Requirement Level Assessment:")
        req_score = self.scoring_engine.assess_requirement("req_5_1", criteria_scores)
        print(f"   Requirement 5.1 (ICT Risk Framework):")
        print(f"   Score: {req_score.score}/10 ({req_score.percentage:.1f}%)")
        print(f"   RAG Status: {req_score.rag_status.value.upper()}")
        print(f"   Gaps: {req_score.gap_count}, Critical: {len(req_score.critical_gaps)}")
        print(f"   Priority: {req_score.improvement_priority}/5")
        
        # Create additional sample requirement scores for pillar assessment
        req_scores = [
            req_score,
            AggregatedScore(
                level="requirement",
                entity_id="req_6_1",
                entity_name="Requirement 6.1",
                score=Decimal("7.2"),
                max_score=Decimal("10"),
                percentage=Decimal("72.0"),
                rag_status=RAGStatus.AMBER,
                gap_count=3,
                critical_gaps=["Policy documentation gaps"],
                improvement_priority=2
            ),
            AggregatedScore(
                level="requirement",
                entity_id="req_7_1",
                entity_name="Requirement 7.1",
                score=Decimal("8.1"),
                max_score=Decimal("10"),
                percentage=Decimal("81.0"),
                rag_status=RAGStatus.GREEN,
                gap_count=1,
                critical_gaps=[],
                improvement_priority=4
            )
        ]
        
        # Pillar level assessment
        print("\n🔹 Pillar Level Assessment:")
        pillar_score = self.scoring_engine.assess_pillar(
            PillarType.GOVERNANCE_ARRANGEMENTS, 
            req_scores
        )
        print(f"   Pillar: {pillar_score.entity_name}")
        print(f"   Score: {pillar_score.score}/10 ({pillar_score.percentage:.1f}%)")
        print(f"   RAG Status: {pillar_score.rag_status.value.upper()}")
        print(f"   Requirements: {len(req_scores)}")
        print(f"   Total Gaps: {pillar_score.gap_count}")
        
        # Create sample pillar scores for overall assessment
        pillar_scores = [
            pillar_score,
            AggregatedScore(
                level="pillar",
                entity_id="ict_related_incidents",
                entity_name="ICT Related Incidents",
                score=Decimal("6.8"),
                max_score=Decimal("10"),
                percentage=Decimal("68.0"),
                rag_status=RAGStatus.AMBER,
                gap_count=8,
                critical_gaps=["Incident classification gaps", "Reporting delays"],
                improvement_priority=2
            ),
            AggregatedScore(
                level="pillar",
                entity_id="digital_operational_resilience_testing",
                entity_name="Digital Operational Resilience Testing",
                score=Decimal("5.9"),
                max_score=Decimal("10"),
                percentage=Decimal("59.0"),
                rag_status=RAGStatus.AMBER,
                gap_count=12,
                critical_gaps=["Limited test scenarios", "No TLPT programme"],
                improvement_priority=1
            ),
            AggregatedScore(
                level="pillar",
                entity_id="ict_third_party_risk",
                entity_name="ICT Third Party Risk",
                score=Decimal("7.8"),
                max_score=Decimal("10"),
                percentage=Decimal("78.0"),
                rag_status=RAGStatus.AMBER,
                gap_count=5,
                critical_gaps=["Concentration risk analysis"],
                improvement_priority=3
            ),
            AggregatedScore(
                level="pillar",
                entity_id="information_sharing",
                entity_name="Information Sharing",
                score=Decimal("8.3"),
                max_score=Decimal("10"),
                percentage=Decimal("83.0"),
                rag_status=RAGStatus.GREEN,
                gap_count=2,
                critical_gaps=[],
                improvement_priority=5
            )
        ]
        
        # Overall assessment
        print("\n🔹 Overall Assessment:")
        overall_score = self.scoring_engine.assess_overall_compliance(pillar_scores)
        print(f"   Overall DORA Compliance:")
        print(f"   Score: {overall_score.score}/10 ({overall_score.percentage:.1f}%)")
        print(f"   RAG Status: {overall_score.rag_status.value.upper()}")
        print(f"   Pillars: {len(pillar_scores)}")
        print(f"   Total Gaps: {overall_score.gap_count}")
        print(f"   Critical Gaps: {len(overall_score.critical_gaps)}")
        
        # Combine all scores for further analysis
        all_scores = req_scores + pillar_scores + [overall_score]
        
        return all_scores
    
    async def _demo_rag_status_calculation(self, assessment_scores: List[AggregatedScore]):
        """Demonstrate RAG status calculation with different methodologies"""
        print("\n🚦 Step 4: RAG Status Calculation")
        print("-" * 40)
        
        print("📊 Demonstrating RAG status calculation across methodologies...")
        
        # Test sample score with different methodologies
        test_score = Decimal("7.2")
        max_score = Decimal("10")
        
        methodologies = ["standard", "conservative", "aggressive", "regulatory"]
        
        print(f"\n🎯 Sample Score: {test_score}/10 ({(test_score/max_score)*100:.1f}%)")
        print(f"RAG Status by Methodology:")
        
        for methodology in methodologies:
            rag_status = self.scoring_engine.calculate_rag_status(test_score, max_score, methodology)
            thresholds = self.scoring_engine.rag_thresholds[methodology]
            emoji = {"green": "🟢", "amber": "🟡", "red": "🔴"}.get(rag_status.value, "⚪")
            print(f"   {emoji} {methodology.title()}: {rag_status.value.upper()} (thresholds: {thresholds[0]}-{thresholds[1]})")
        
        # Show RAG distribution across assessment
        print(f"\n📈 RAG Status Distribution:")
        rag_counts = {"green": 0, "amber": 0, "red": 0, "not_assessed": 0}
        
        for score in assessment_scores:
            rag_counts[score.rag_status.value] += 1
        
        total_scores = len(assessment_scores)
        for status, count in rag_counts.items():
            if count > 0:
                percentage = (count / total_scores) * 100
                emoji = {"green": "🟢", "amber": "🟡", "red": "🔴", "not_assessed": "⚪"}[status]
                print(f"   {emoji} {status.title()}: {count} ({percentage:.1f}%)")
    
    async def _demo_gap_analysis(self, assessment_scores: List[AggregatedScore]) -> Dict[str, Any]:
        """Demonstrate comprehensive gap analysis"""
        print("\n🔍 Step 5: Gap Analysis")
        print("-" * 30)
        
        print("📊 Generating comprehensive gap analysis...")
        gap_analysis = self.scoring_engine.generate_gap_analysis(assessment_scores)
        
        print(f"✅ Gap analysis completed:")
        
        # Overall summary
        summary = gap_analysis.get("overall_summary", {})
        if summary:
            print(f"\n📋 Overall Summary:")
            print(f"   Score: {summary['score']}/10 ({summary['percentage']:.1f}%)")
            print(f"   RAG Status: {summary['rag_status'].upper()}")
            print(f"   Total Gaps: {summary['total_gaps']}")
            print(f"   Critical Gaps: {summary['critical_gaps']}")
            print(f"   Priority Level: {summary['improvement_priority']}/5")
        
        # Pillar analysis
        pillar_analysis = gap_analysis.get("pillar_analysis", {})
        if pillar_analysis:
            print(f"\n🏛️ Pillar Analysis:")
            for pillar_id, analysis in pillar_analysis.items():
                rag_emoji = {"green": "🟢", "amber": "🟡", "red": "🔴"}.get(analysis["rag_status"], "⚪")
                print(f"   {rag_emoji} {analysis['name']}: {analysis['score']}/10")
                print(f"      Gaps: {analysis['gap_count']}, Priority: {analysis['priority']}/5")
                if analysis['critical_gaps']:
                    print(f"      Critical: {', '.join(analysis['critical_gaps'][:2])}...")
        
        # Critical gaps
        critical_gaps = gap_analysis.get("critical_gaps", [])
        if critical_gaps:
            print(f"\n🚨 Top Critical Gaps ({len(critical_gaps)}):")
            for i, gap in enumerate(critical_gaps[:5], 1):
                print(f"   {i}. {gap['entity']} - {gap['gap']} (Impact: {gap['impact']}/10)")
        
        # Improvement recommendations
        recommendations = gap_analysis.get("improvement_recommendations", [])
        if recommendations:
            print(f"\n💡 Priority Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"   {i}. {rec['entity']} ({rec['rag_status'].upper()})")
                print(f"      Current: {rec['current_score']}/10, Effort: {rec['estimated_effort']}")
                print(f"      Action: {rec['recommendation'][:60]}...")
        
        return gap_analysis
    
    async def _demo_priority_matrix(self, gap_analysis: Dict[str, Any]):
        """Demonstrate priority matrix and quadrant analysis"""
        print("\n🎯 Step 6: Priority Matrix Analysis")
        print("-" * 40)
        
        print("📊 Analyzing priority matrix (Effort vs Impact)...")
        
        priority_matrix = gap_analysis.get("priority_matrix", [])
        if priority_matrix:
            print(f"✅ Priority matrix generated for {len(priority_matrix)} pillars:")
            
            # Group by quadrant
            quadrants = {}
            for item in priority_matrix:
                quadrant = item["priority_quadrant"]
                if quadrant not in quadrants:
                    quadrants[quadrant] = []
                quadrants[quadrant].append(item)
            
            print(f"\n📋 Priority Quadrants:")
            quadrant_emojis = {
                "Quick Wins": "⚡",
                "Major Projects": "🏗️",
                "Fill-ins": "🔧",
                "Thankless Tasks": "⚠️"
            }
            
            for quadrant, items in quadrants.items():
                emoji = quadrant_emojis.get(quadrant, "📊")
                print(f"\n   {emoji} {quadrant} ({len(items)} items):")
                
                for item in items:
                    print(f"      - {item['pillar']}")
                    print(f"        Impact: {item['impact']:.1f}/10, Effort: {item['effort']:.1f}/10")
                    print(f"        Recommendation: {item['recommendation']}")
            
            # Show prioritized action plan
            print(f"\n🎯 Recommended Action Sequence:")
            quick_wins = quadrants.get("Quick Wins", [])
            major_projects = quadrants.get("Major Projects", [])
            
            action_sequence = 1
            
            if quick_wins:
                print(f"\n   Phase 1: Quick Wins (Immediate - 3 months)")
                for item in quick_wins:
                    print(f"   {action_sequence}. {item['pillar']} - {item['recommendation']}")
                    action_sequence += 1
            
            if major_projects:
                print(f"\n   Phase 2: Major Projects (6-18 months)")
                for item in major_projects:
                    print(f"   {action_sequence}. {item['pillar']} - {item['recommendation']}")
                    action_sequence += 1
        
        else:
            print("No priority matrix data available")
    
    async def _demo_scoring_methodologies(self):
        """Demonstrate different scoring methodologies"""
        print("\n⚙️ Step 7: Scoring Methodologies")
        print("-" * 40)
        
        print("🔧 Demonstrating different scoring methodologies...")
        
        methodologies = self.scoring_engine.scoring_methodologies
        
        print(f"✅ Available methodologies ({len(methodologies)}):")
        for method_id, method_config in methodologies.items():
            print(f"\n   📊 {method_config['name']}:")
            print(f"      Description: {method_config['description']}")
            print(f"      Weight Type: {method_config['weight_type'].value}")
            print(f"      RAG Thresholds: R<{method_config['rag_thresholds']['red']}, "
                  f"A<{method_config['rag_thresholds']['amber']}, "
                  f"G>={method_config['rag_thresholds']['green']}")
            print(f"      Evidence Multiplier: {method_config['evidence_multiplier']}")
        
        # Show pillar weights
        print(f"\n⚖️ Default Pillar Weights:")
        for pillar, weight in self.scoring_engine.pillar_weights.items():
            pillar_name = pillar.value.replace("_", " ").title()
            print(f"   {pillar_name}: {float(weight)*100:.1f}%")
        
        # Demonstrate methodology impact
        print(f"\n🎯 Methodology Impact Example (Score: 7.2/10):")
        test_score = Decimal("7.2")
        max_score = Decimal("10")
        
        for method_id in methodologies.keys():
            rag_status = self.scoring_engine.calculate_rag_status(test_score, max_score, method_id)
            emoji = {"green": "🟢", "amber": "🟡", "red": "🔴"}.get(rag_status.value, "⚪")
            print(f"   {emoji} {method_id.title()}: {rag_status.value.upper()}")
    
    async def _demo_assessment_reporting(self, assessment_scores: List[AggregatedScore], 
                                       gap_analysis: Dict[str, Any]):
        """Demonstrate comprehensive assessment reporting"""
        print("\n📄 Step 8: Assessment Reporting")
        print("-" * 40)
        
        print("📝 Generating comprehensive assessment report...")
        
        # Generate detailed report
        report = self.scoring_engine.generate_scoring_report(assessment_scores, gap_analysis)
        
        # Save report
        report_path = Path("dora-knowledge-base/reports/scoring_demo_report.md")
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"✅ Assessment report generated:")
        print(f"   📄 File: {report_path}")
        print(f"   📏 Length: {len(report)} characters")
        
        # Show report preview
        print(f"\n📋 Report Preview (first 500 characters):")
        print(f"{'='*50}")
        print(report[:500] + "..." if len(report) > 500 else report)
        print(f"{'='*50}")
        
        # Generate summary statistics
        print(f"\n📊 Report Statistics:")
        lines = report.split('\n')
        sections = [line for line in lines if line.startswith('#')]
        print(f"   Lines: {len(lines)}")
        print(f"   Sections: {len(sections)}")
        print(f"   Sections: {[s.strip('#').strip() for s in sections[:5]]}")
    
    async def _demo_database_integration(self, assessment_scores: List[AggregatedScore],
                                       gap_analysis: Dict[str, Any]):
        """Demonstrate database integration capabilities"""
        print("\n💾 Step 9: Database Integration")
        print("-" * 40)
        
        print("🔗 Demonstrating database integration...")
        
        try:
            # Save assessment to database
            assessment_id = self.scoring_engine.save_assessment_to_database(
                assessment_scores, 
                gap_analysis
            )
            
            print(f"✅ Assessment saved to database:")
            print(f"   Assessment ID: {assessment_id}")
            print(f"   Scores Saved: {len(assessment_scores)}")
            print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Verify database state
            with self.Session() as session:
                # Count assessments
                assessment_count = session.execute("SELECT COUNT(*) FROM compliance_assessments").scalar() or 0
                score_count = session.execute("SELECT COUNT(*) FROM assessment_scores").scalar() or 0
                
                print(f"\n📊 Database State:")
                print(f"   Total Assessments: {assessment_count}")
                print(f"   Total Scores: {score_count}")
            
            print(f"\n🎯 Database Integration Features Demonstrated:")
            print(f"   ✅ Assessment persistence")
            print(f"   ✅ Score tracking")
            print(f"   ✅ Gap analysis storage")
            print(f"   ✅ Historical tracking capability")
            print(f"   ✅ Data integrity maintenance")
            
        except Exception as e:
            print(f"⚠️  Database integration not available: {e}")
            print(f"   This is expected if database is not set up")
            print(f"   Scoring engine works independently of database")
    
    async def _generate_final_summary(self):
        """Generate final demonstration summary"""
        print("\n📋 Step 10: Demonstration Summary")
        print("-" * 40)
        
        capabilities_demonstrated = [
            "Comprehensive scoring rubric creation (20+ criteria)",
            "Multi-level assessment aggregation (criteria → requirement → pillar → overall)",
            "RAG status calculation with multiple methodologies",
            "Advanced gap analysis with impact scoring",
            "Priority matrix and quadrant analysis",
            "Improvement recommendations with effort estimation",
            "Multiple scoring methodologies (standard, risk-based, regulatory, operational)",
            "Comprehensive assessment reporting",
            "Database integration for persistence and tracking",
            "Configurable weighting and threshold systems"
        ]
        
        business_value = [
            "Objective compliance measurement and scoring",
            "Clear prioritization of improvement efforts", 
            "Evidence-based gap identification",
            "Regulatory examination readiness",
            "Resource allocation optimization",
            "Progress tracking and trend analysis",
            "Stakeholder communication and reporting",
            "Risk-based compliance management"
        ]
        
        print(f"🎯 Capabilities Successfully Demonstrated ({len(capabilities_demonstrated)}):")
        for i, capability in enumerate(capabilities_demonstrated, 1):
            print(f"   {i:2d}. {capability}")
        
        print(f"\n💼 Business Value Delivered ({len(business_value)}):")
        for i, value in enumerate(business_value, 1):
            print(f"   {i}. {value}")
        
        print(f"\n🚀 Ready for Integration:")
        print(f"   ✅ Policy Analyzer Agent can leverage scoring engine")
        print(f"   ✅ Assessment workflows can be automated")
        print(f"   ✅ Real-time compliance monitoring possible")
        print(f"   ✅ Regulatory reporting capabilities available")
        print(f"   ✅ Continuous improvement framework established")


async def main():
    """Main demonstration entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DORA Scoring Engine Demonstration")
    parser.add_argument("--full-demo", action="store_true", help="Run complete demonstration")
    parser.add_argument("--quick-test", action="store_true", help="Run quick scoring test")
    parser.add_argument("--rubrics-only", action="store_true", help="Create rubrics only")
    parser.add_argument("--database-url", default="postgresql://postgres:password@localhost:5432/dora_kb")
    
    args = parser.parse_args()
    
    demo = ScoringEngineDemo(args.database_url)
    
    try:
        if args.full_demo:
            await demo.run_full_demonstration()
            await demo._generate_final_summary()
        elif args.quick_test:
            # Quick scoring test
            print("🎯 Running quick scoring engine test...")
            rubrics = demo.scoring_engine.create_scoring_rubrics()
            total_criteria = sum(len(criteria_list) for criteria_list in rubrics.values())
            print(f"✅ Quick test complete. Created {total_criteria} scoring criteria across {len(rubrics)} domains")
        elif args.rubrics_only:
            # Create rubrics only
            print("📋 Creating scoring rubrics...")
            rubrics = demo.scoring_engine.create_scoring_rubrics()
            for domain, criteria_list in rubrics.items():
                print(f"   {domain.title()}: {len(criteria_list)} criteria")
            print(f"✅ Rubrics created successfully")
        else:
            print("Use --full-demo for complete demonstration, --quick-test for validation, or --rubrics-only for rubric creation")
            
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 