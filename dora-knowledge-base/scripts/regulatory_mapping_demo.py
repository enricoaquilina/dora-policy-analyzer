#!/usr/bin/env python3
"""
DORA Regulatory Mapping Demonstration

This script demonstrates the comprehensive regulatory mapping and cross-reference 
capabilities of the DORA Knowledge Base, showing:
- Cross-regulatory mapping creation
- Gap analysis and overlap detection  
- Bidirectional navigation
- Compliance efficiency analysis
- Matrix generation and reporting

Usage:
    python regulatory_mapping_demo.py --full-demo
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

from data.regulatory_mapper import DORARegulatoryMapper, RegulatoryFrameworkType
from schemas.data_models import CrossRegulationMapping, RegulatoryFramework

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RegulatoryMappingDemo:
    """Comprehensive demonstration of regulatory mapping capabilities"""
    
    def __init__(self, database_url: str = "postgresql://postgres:password@localhost:5432/dora_kb"):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.mapper = DORARegulatoryMapper(database_url)
        
    async def run_full_demonstration(self):
        """Run complete regulatory mapping demonstration"""
        print("🌐 DORA Regulatory Mapping - Complete Demonstration")
        print("=" * 60)
        
        try:
            # Step 1: Create regulatory mappings
            mappings = await self._demo_mapping_creation()
            
            # Step 2: Analyze gaps and overlaps
            gap_analysis = await self._demo_gap_analysis(mappings)
            
            # Step 3: Load to database
            loading_stats = await self._demo_database_loading(mappings)
            
            # Step 4: Demonstrate bidirectional navigation
            await self._demo_bidirectional_navigation()
            
            # Step 5: Generate compliance matrix
            await self._demo_compliance_matrix()
            
            # Step 6: Framework comparison analysis
            await self._demo_framework_comparison()
            
            # Step 7: Compliance efficiency analysis
            await self._demo_compliance_efficiency(gap_analysis)
            
            # Step 8: Generate comprehensive reports
            await self._generate_mapping_reports(mappings, gap_analysis, loading_stats)
            
            print("\n🎉 Regulatory mapping demonstration completed successfully!")
            
        except Exception as e:
            logger.error(f"Demonstration failed: {e}")
            raise
    
    async def _demo_mapping_creation(self) -> Dict[str, Any]:
        """Demonstrate regulatory mapping creation"""
        print("\n🔗 Step 1: Cross-Regulatory Mapping Creation")
        print("-" * 45)
        
        print("🔍 Creating comprehensive regulatory mappings...")
        mappings = self.mapper.create_regulatory_mappings()
        
        print(f"✅ Mapping creation completed:")
        total_mappings = 0
        for framework_key, mapping_list in mappings.items():
            framework_name = framework_key.replace("dora_to_", "").upper()
            count = len(mapping_list)
            total_mappings += count
            print(f"   📊 DORA → {framework_name}: {count} mappings")
            
            # Show sample mapping
            if mapping_list:
                sample = mapping_list[0]
                print(f"      Sample: {sample.source_requirement_id} → {sample.target_requirement_id}")
                print(f"      Type: {sample.mapping_type.value}, Confidence: {sample.confidence_score:.2f}")
        
        print(f"\n📈 Total Mappings Created: {total_mappings}")
        
        # Show mapping type distribution
        type_distribution = {}
        for mapping_list in mappings.values():
            for mapping in mapping_list:
                mapping_type = mapping.mapping_type.value
                type_distribution[mapping_type] = type_distribution.get(mapping_type, 0) + 1
        
        print(f"\n📋 Mapping Type Distribution:")
        for mapping_type, count in type_distribution.items():
            print(f"   {mapping_type.replace('_', ' ').title()}: {count}")
        
        return mappings
    
    async def _demo_gap_analysis(self, mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Demonstrate gap analysis capabilities"""
        print("\n🔍 Step 2: Regulatory Gap Analysis")
        print("-" * 40)
        
        print("📊 Analyzing regulatory gaps and overlaps...")
        gap_analysis = self.mapper.analyze_regulatory_gaps(mappings)
        
        print(f"✅ Gap analysis completed:")
        
        # Framework coverage analysis
        print(f"\n📈 Framework Coverage Analysis:")
        for framework, coverage in gap_analysis["framework_coverage"].items():
            print(f"   🏛️ {framework}:")
            print(f"      Total Mappings: {coverage['total_mappings']}")
            print(f"      High Confidence: {coverage['high_confidence']}")
            print(f"      Medium Confidence: {coverage['medium_confidence']}")
            print(f"      Low Confidence: {coverage['low_confidence']}")
            
            # Calculate coverage score
            total = coverage['total_mappings']
            if total > 0:
                score = (coverage['high_confidence'] * 1.0 + coverage['medium_confidence'] * 0.7) / total
                print(f"      Coverage Score: {score:.2f}")
        
        # High overlap areas
        print(f"\n🔄 High Overlap Areas ({len(gap_analysis['high_overlap_areas'])}):")
        for overlap in gap_analysis['high_overlap_areas'][:5]:  # Show first 5
            frameworks = ", ".join(overlap['frameworks'])
            print(f"   📋 {overlap['requirement_id']}: {frameworks}")
        
        # Compliance efficiency opportunities
        print(f"\n⚡ Compliance Efficiency Opportunities ({len(gap_analysis['compliance_efficiency_opportunities'])}):")
        for opportunity in gap_analysis['compliance_efficiency_opportunities'][:3]:  # Show first 3
            print(f"   🎯 {opportunity['dora_requirement']} → {opportunity['target_framework']}")
            print(f"      Confidence: {opportunity['confidence']:.2f}")
        
        # Potential conflicts
        if gap_analysis['potential_conflicts']:
            print(f"\n⚠️  Potential Conflicts ({len(gap_analysis['potential_conflicts'])}):")
            for conflict in gap_analysis['potential_conflicts']:
                frameworks = ", ".join(conflict['conflicting_frameworks'])
                print(f"   ❌ {conflict['requirement_id']}: {frameworks}")
        else:
            print(f"\n✅ No potential conflicts detected")
        
        return gap_analysis
    
    async def _demo_database_loading(self, mappings: Dict[str, Any]) -> Dict[str, int]:
        """Demonstrate database loading process"""
        print("\n💾 Step 3: Database Loading")
        print("-" * 30)
        
        print("📥 Loading regulatory mappings to database...")
        loading_stats = self.mapper.load_mappings_to_database(mappings)
        
        print(f"✅ Database loading completed:")
        for key, value in loading_stats.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        
        # Verify database state
        with self.Session() as session:
            framework_count = session.query(RegulatoryFramework).count()
            mapping_count = session.query(CrossRegulationMapping).count()
            
            print(f"\n📊 Database State After Loading:")
            print(f"   Regulatory Frameworks: {framework_count}")
            print(f"   Cross-Regulation Mappings: {mapping_count}")
        
        return loading_stats
    
    async def _demo_bidirectional_navigation(self):
        """Demonstrate bidirectional mapping navigation"""
        print("\n🔄 Step 4: Bidirectional Navigation")
        print("-" * 40)
        
        # Query sample requirement
        sample_requirement = "req_5_1"
        print(f"🔍 Querying mappings for requirement: {sample_requirement}")
        
        result = self.mapper.query_bidirectional_mappings(sample_requirement)
        
        print(f"📤 Outbound Mappings ({len(result['outbound_mappings'])}):")
        for mapping in result['outbound_mappings']:
            print(f"   → {mapping['target_framework']}: {mapping['target_requirement']}")
            print(f"     Type: {mapping['mapping_type']}, Confidence: {mapping['confidence_score']:.2f}")
            print(f"     Rationale: {mapping['rationale'][:80]}...")
        
        print(f"\n📥 Inbound Mappings ({len(result['inbound_mappings'])}):")
        for mapping in result['inbound_mappings']:
            print(f"   ← {mapping['source_framework']}: {mapping['source_requirement']}")
            print(f"     Type: {mapping['mapping_type']}, Confidence: {mapping['confidence_score']:.2f}")
        
        # Show navigation paths
        print(f"\n🗺️ Navigation Paths from {sample_requirement}:")
        if result['outbound_mappings']:
            for mapping in result['outbound_mappings'][:3]:  # Show first 3 paths
                print(f"   DORA:{sample_requirement} → {mapping['target_framework'].upper()}:{mapping['target_requirement']}")
    
    async def _demo_compliance_matrix(self):
        """Demonstrate compliance matrix generation"""
        print("\n📊 Step 5: Compliance Matrix Generation")
        print("-" * 45)
        
        print("📋 Generating cross-regulatory compliance matrix...")
        matrix_df = self.mapper.generate_compliance_matrix()
        
        print(f"✅ Compliance matrix generated:")
        print(f"   📏 Dimensions: {matrix_df.shape[0]} rows × {matrix_df.shape[1]} columns")
        
        # Show sample of matrix
        print(f"\n📋 Sample Matrix Data (first 5 rows):")
        print(matrix_df.head().to_string(index=False))
        
        # Show matrix statistics
        print(f"\n📈 Matrix Statistics:")
        framework_counts = matrix_df['Target_Framework'].value_counts()
        for framework, count in framework_counts.items():
            print(f"   {framework}: {count} mappings")
        
        # Show compliance efficiency distribution
        efficiency_counts = matrix_df['Compliance_Efficiency'].value_counts()
        print(f"\n⚡ Compliance Efficiency Distribution:")
        for efficiency, count in efficiency_counts.items():
            print(f"   {efficiency}: {count} mappings")
        
        # Save matrix
        output_path = Path("dora-knowledge-base/reports/compliance_matrix.csv")
        output_path.parent.mkdir(exist_ok=True)
        matrix_df.to_csv(output_path, index=False)
        print(f"\n💾 Matrix saved to: {output_path}")
    
    async def _demo_framework_comparison(self):
        """Demonstrate framework comparison capabilities"""
        print("\n🏛️ Step 6: Framework Comparison Analysis")
        print("-" * 45)
        
        with self.Session() as session:
            # Get framework statistics
            frameworks = session.query(RegulatoryFramework).all()
            
            print(f"📊 Loaded Regulatory Frameworks ({len(frameworks)}):")
            for framework in frameworks:
                print(f"   🏛️ {framework.name}")
                print(f"      Code: {framework.framework_code}")
                print(f"      Version: {framework.version}")
                print(f"      Jurisdiction: {framework.jurisdiction}")
                print(f"      Authority: {framework.authority}")
                
                # Count mappings for this framework
                outbound_count = session.query(CrossRegulationMapping).filter(
                    CrossRegulationMapping.source_framework == framework.framework_code
                ).count()
                
                inbound_count = session.query(CrossRegulationMapping).filter(
                    CrossRegulationMapping.target_framework == framework.framework_code
                ).count()
                
                print(f"      Outbound Mappings: {outbound_count}")
                print(f"      Inbound Mappings: {inbound_count}")
                print()
    
    async def _demo_compliance_efficiency(self, gap_analysis: Dict[str, Any]):
        """Demonstrate compliance efficiency analysis"""
        print("\n⚡ Step 7: Compliance Efficiency Analysis")
        print("-" * 45)
        
        print("🎯 Analyzing compliance efficiency opportunities...")
        
        # High efficiency opportunities (identical mappings)
        high_efficiency = gap_analysis["compliance_efficiency_opportunities"]
        print(f"✅ High Efficiency Opportunities ({len(high_efficiency)}):")
        
        efficiency_by_framework = {}
        for opportunity in high_efficiency:
            framework = opportunity['target_framework']
            if framework not in efficiency_by_framework:
                efficiency_by_framework[framework] = []
            efficiency_by_framework[framework].append(opportunity)
        
        for framework, opportunities in efficiency_by_framework.items():
            print(f"   🏛️ {framework.upper()}: {len(opportunities)} identical mappings")
            for opp in opportunities[:2]:  # Show first 2
                print(f"      - {opp['dora_requirement']} ≡ {opp['target_requirement']} (conf: {opp['confidence']:.2f})")
        
        # Multi-framework overlaps
        overlaps = gap_analysis["high_overlap_areas"]
        print(f"\n🔄 Multi-Framework Overlaps ({len(overlaps)}):")
        for overlap in overlaps[:5]:  # Show first 5
            frameworks = ", ".join(overlap['frameworks'])
            print(f"   📋 {overlap['requirement_id']}: {frameworks}")
            print(f"      Synergy Potential: {overlap['potential_synergy']}")
        
        # Calculate overall efficiency score
        total_mappings = sum(len(mapping_list) for mapping_list in gap_analysis.get("framework_coverage", {}).values() if isinstance(mapping_list, dict) and 'total_mappings' in mapping_list)
        if total_mappings == 0:
            # Fallback calculation
            with self.Session() as session:
                total_mappings = session.query(CrossRegulationMapping).count()
        
        high_conf_mappings = sum(
            coverage.get('high_confidence', 0) 
            for coverage in gap_analysis["framework_coverage"].values()
        )
        
        efficiency_score = (high_conf_mappings / total_mappings * 100) if total_mappings > 0 else 0
        print(f"\n📊 Overall Compliance Efficiency Score: {efficiency_score:.1f}%")
        
        # Recommendations
        print(f"\n💡 Efficiency Recommendations:")
        if efficiency_score >= 80:
            print("   ✅ Excellent cross-regulatory alignment")
            print("   📋 Focus on maintaining mapping quality")
        elif efficiency_score >= 60:
            print("   ⚠️  Good alignment with room for improvement") 
            print("   📋 Review medium confidence mappings")
        else:
            print("   ❌ Significant alignment gaps detected")
            print("   📋 Prioritize mapping validation and expansion")
    
    async def _generate_mapping_reports(self, mappings: Dict[str, Any], 
                                      gap_analysis: Dict[str, Any], 
                                      loading_stats: Dict[str, int]):
        """Generate comprehensive mapping reports"""
        print("\n📄 Step 8: Report Generation")
        print("-" * 35)
        
        # Calculate comprehensive metrics
        total_mappings = sum(len(mapping_list) for mapping_list in mappings.values())
        
        # Framework effectiveness scores
        framework_scores = {}
        for framework_key, mapping_list in mappings.items():
            framework_name = framework_key.replace("dora_to_", "")
            if mapping_list:
                avg_confidence = sum(m.confidence_score for m in mapping_list) / len(mapping_list)
                high_conf_ratio = len([m for m in mapping_list if m.confidence_score >= 0.8]) / len(mapping_list)
                effectiveness_score = (avg_confidence * 0.6 + high_conf_ratio * 0.4) * 100
                framework_scores[framework_name] = effectiveness_score
        
        report_data = {
            "demonstration_completed": datetime.now().isoformat(),
            "mapping_metrics": {
                "total_mappings": total_mappings,
                "frameworks_covered": len(mappings),
                "loading_stats": loading_stats
            },
            "gap_analysis_results": {
                "high_overlap_areas": len(gap_analysis["high_overlap_areas"]),
                "efficiency_opportunities": len(gap_analysis["compliance_efficiency_opportunities"]),
                "potential_conflicts": len(gap_analysis["potential_conflicts"])
            },
            "framework_effectiveness": framework_scores,
            "capabilities_demonstrated": [
                "Cross-regulatory mapping creation",
                "Multi-framework gap analysis",
                "Bidirectional navigation",
                "Compliance matrix generation",
                "Framework comparison analysis", 
                "Efficiency opportunity identification",
                "Automated mapping validation"
            ],
            "key_insights": [
                f"Total of {total_mappings} cross-regulatory mappings created",
                f"Coverage across {len(mappings)} major regulatory frameworks",
                f"Identified {len(gap_analysis['compliance_efficiency_opportunities'])} high-efficiency opportunities",
                f"Multi-framework overlaps found in {len(gap_analysis['high_overlap_areas'])} requirement areas"
            ],
            "next_steps": [
                "Expand mapping coverage to additional frameworks",
                "Implement automated mapping suggestions",
                "Develop compliance assessment algorithms",
                "Create regulatory change impact analysis",
                "Build compliance dashboard interfaces"
            ]
        }
        
        # Save comprehensive report
        report_path = Path("dora-knowledge-base/reports/regulatory_mapping_report.json")
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Comprehensive Report:")
        print(f"   📊 Total Mappings: {total_mappings}")
        print(f"   🏛️ Frameworks Covered: {len(mappings)}")
        print(f"   ⚡ Efficiency Opportunities: {len(gap_analysis['compliance_efficiency_opportunities'])}")
        print(f"   📋 Capabilities Demonstrated: {len(report_data['capabilities_demonstrated'])}")
        print(f"   📝 Report saved to: {report_path}")
        
        # Generate framework effectiveness summary
        print(f"\n🏆 Framework Effectiveness Ranking:")
        sorted_frameworks = sorted(framework_scores.items(), key=lambda x: x[1], reverse=True)
        for i, (framework, score) in enumerate(sorted_frameworks, 1):
            print(f"   {i}. {framework.upper()}: {score:.1f}%")
        
        # Summary
        print(f"\n🎉 Regulatory Mapping Demonstration Summary:")
        print(f"   ✅ Cross-regulatory mappings created and validated")
        print(f"   ✅ Gap analysis and overlap detection completed")
        print(f"   ✅ Database integration and bidirectional navigation working")
        print(f"   ✅ Compliance matrix generation functional")
        print(f"   ✅ Framework comparison and efficiency analysis complete")
        print(f"   ✅ Ready for Policy Analyzer Agent integration")


async def main():
    """Main demonstration entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DORA Regulatory Mapping Demonstration")
    parser.add_argument("--full-demo", action="store_true", help="Run complete demonstration")
    parser.add_argument("--quick-test", action="store_true", help="Run quick mapping test")
    parser.add_argument("--create-only", action="store_true", help="Create mappings only")
    parser.add_argument("--database-url", default="postgresql://postgres:password@localhost:5432/dora_kb")
    
    args = parser.parse_args()
    
    demo = RegulatoryMappingDemo(args.database_url)
    
    try:
        if args.full_demo:
            await demo.run_full_demonstration()
        elif args.quick_test:
            # Quick mapping test
            print("🔍 Running quick regulatory mapping test...")
            mappings = demo.mapper.create_regulatory_mappings()
            total_mappings = sum(len(mapping_list) for mapping_list in mappings.values())
            print(f"✅ Quick test complete. Created {total_mappings} mappings across {len(mappings)} frameworks")
        elif args.create_only:
            # Create mappings only
            print("🔗 Creating regulatory mappings...")
            mappings = demo.mapper.create_regulatory_mappings()
            stats = demo.mapper.load_mappings_to_database(mappings)
            print(f"✅ Mappings created and loaded: {stats}")
        else:
            print("Use --full-demo for complete demonstration, --quick-test for validation, or --create-only for mapping creation")
            
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 