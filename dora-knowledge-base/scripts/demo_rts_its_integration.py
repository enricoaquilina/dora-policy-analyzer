#!/usr/bin/env python3
"""
DORA RTS/ITS Integration Demonstration

This script demonstrates the RTS/ITS integration capabilities without requiring
database connectivity. It shows the technical standards structure, mappings,
and integration logic.

Author: DORA Compliance System
Date: 2025-01-23
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import asdict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from rts_its_integrator import RTSITSIntegrator, RTSITSDocument, RequirementMapping

class RTSITSDemo:
    """Demonstration class for RTS/ITS integration"""
    
    def __init__(self):
        """Initialize demo with mock integrator"""
        # Create integrator without database connection
        self.integrator = RTSITSIntegrator.__new__(RTSITSIntegrator)
        self.integrator.rts_its_documents = []
        self.integrator.requirement_mappings = []
        
        # Load the catalog
        self.integrator._load_rts_its_catalog()
        self.integrator._create_requirement_mappings()
    
    def demonstrate_rts_its_catalog(self):
        """Demonstrate the RTS/ITS document catalog"""
        print("🏛️  DORA RTS/ITS Technical Standards Catalog")
        print("=" * 60)
        
        rts_count = sum(1 for doc in self.integrator.rts_its_documents if doc.standard_type == "RTS")
        its_count = sum(1 for doc in self.integrator.rts_its_documents if doc.standard_type == "ITS")
        
        print(f"📊 Total Standards: {len(self.integrator.rts_its_documents)}")
        print(f"   • RTS Documents: {rts_count}")
        print(f"   • ITS Documents: {its_count}")
        print()
        
        # Group by type
        rts_docs = [doc for doc in self.integrator.rts_its_documents if doc.standard_type == "RTS"]
        its_docs = [doc for doc in self.integrator.rts_its_documents if doc.standard_type == "ITS"]
        
        print("📋 Regulatory Technical Standards (RTS):")
        print("-" * 40)
        for doc in rts_docs:
            print(f"   {doc.standard_id}: {doc.title}")
            print(f"      Status: {doc.status.title()} | Effective: {doc.effective_date}")
            print(f"      Articles: {', '.join(doc.related_articles)}")
            print()
        
        print("📋 Implementing Technical Standards (ITS):")
        print("-" * 40)
        for doc in its_docs:
            print(f"   {doc.standard_id}: {doc.title}")
            print(f"      Status: {doc.status.title()} | Effective: {doc.effective_date}")
            print(f"      Articles: {', '.join(doc.related_articles)}")
            print()
    
    def demonstrate_requirement_mappings(self):
        """Demonstrate requirement mappings"""
        print("🔗 Requirement to Technical Standards Mappings")
        print("=" * 60)
        
        print(f"📊 Total Mappings: {len(self.integrator.requirement_mappings)}")
        print()
        
        # Group mappings by confidence level
        high_confidence = [m for m in self.integrator.requirement_mappings if m.mapping_confidence == "high"]
        medium_confidence = [m for m in self.integrator.requirement_mappings if m.mapping_confidence == "medium"]
        
        print(f"🎯 High Confidence Mappings ({len(high_confidence)}):")
        print("-" * 40)
        for mapping in high_confidence:
            print(f"   {mapping.requirement_id} ➜ {mapping.technical_standard_id}")
            print(f"      📝 {mapping.applicability_notes}")
            print(f"      🔍 {mapping.mapping_rationale}")
            print()
        
        print(f"⚖️  Medium Confidence Mappings ({len(medium_confidence)}):")
        print("-" * 40)
        for mapping in medium_confidence:
            print(f"   {mapping.requirement_id} ➜ {mapping.technical_standard_id}")
            print(f"      📝 {mapping.applicability_notes}")
            print()
    
    def demonstrate_pillar_coverage(self):
        """Demonstrate coverage by DORA pillar"""
        print("🏛️  DORA Pillar Coverage Analysis")
        print("=" * 60)
        
        # Analyze coverage by related articles
        article_mappings = {}
        for doc in self.integrator.rts_its_documents:
            for article in doc.related_articles:
                if article not in article_mappings:
                    article_mappings[article] = []
                article_mappings[article].append(doc)
        
        # Map articles to pillars (simplified mapping)
        pillar_mapping = {
            "17": "ICT Incident Management",
            "18": "ICT Incident Management", 
            "19": "ICT Incident Management",
            "20": "ICT Incident Management",
            "21": "ICT Incident Management",
            "24": "Digital Operational Resilience Testing",
            "25": "Digital Operational Resilience Testing",
            "26": "Digital Operational Resilience Testing",
            "28": "ICT Third-Party Risk Management",
            "29": "ICT Third-Party Risk Management",
            "32": "Governance & Oversight",
            "33": "Governance & Oversight",
            "34": "Governance & Oversight",
            "35": "Governance & Oversight",
            "45": "Information Sharing",
            "46": "Information Sharing"
        }
        
        pillar_coverage = {}
        for article, docs in article_mappings.items():
            pillar = pillar_mapping.get(article, "Other")
            if pillar not in pillar_coverage:
                pillar_coverage[pillar] = []
            pillar_coverage[pillar].extend(docs)
        
        for pillar, docs in pillar_coverage.items():
            unique_docs = {doc.standard_id: doc for doc in docs}.values()
            print(f"🏛️  {pillar}:")
            print(f"   📊 Standards Coverage: {len(unique_docs)} technical standards")
            for doc in unique_docs:
                print(f"      • {doc.standard_id} ({doc.standard_type}): {doc.title[:60]}...")
            print()
    
    def demonstrate_implementation_requirements(self):
        """Demonstrate implementation requirements"""
        print("⚙️  Implementation Requirements Analysis")
        print("=" * 60)
        
        for doc in self.integrator.rts_its_documents:
            print(f"📋 {doc.standard_id}: {doc.title}")
            print(f"   🎯 Entity Scope: {', '.join(doc.entity_scope)}")
            print(f"   📝 Key Provisions:")
            for provision in doc.key_provisions:
                print(f"      • {provision}")
            print(f"   ⚙️  Implementation Requirements:")
            for req in doc.implementation_requirements:
                print(f"      • {req}")
            print()
    
    def generate_integration_summary(self) -> Dict[str, Any]:
        """Generate integration summary statistics"""
        rts_count = sum(1 for doc in self.integrator.rts_its_documents if doc.standard_type == "RTS")
        its_count = sum(1 for doc in self.integrator.rts_its_documents if doc.standard_type == "ITS")
        
        # Analyze status distribution
        status_dist = {}
        for doc in self.integrator.rts_its_documents:
            status_dist[doc.status] = status_dist.get(doc.status, 0) + 1
        
        # Analyze mapping confidence
        confidence_dist = {}
        for mapping in self.integrator.requirement_mappings:
            confidence_dist[mapping.mapping_confidence] = confidence_dist.get(mapping.mapping_confidence, 0) + 1
        
        # Coverage analysis
        covered_articles = set()
        for doc in self.integrator.rts_its_documents:
            covered_articles.update(doc.related_articles)
        
        return {
            "total_standards": len(self.integrator.rts_its_documents),
            "rts_count": rts_count,
            "its_count": its_count,
            "total_mappings": len(self.integrator.requirement_mappings),
            "status_distribution": status_dist,
            "confidence_distribution": confidence_dist,
            "articles_covered": len(covered_articles),
            "covered_articles": sorted(list(covered_articles)),
            "effective_date": "2025-01-17"
        }
    
    def export_integration_data(self, output_path: str = "rts_its_integration_data.json"):
        """Export integration data for analysis"""
        print(f"💾 Exporting Integration Data")
        print("=" * 60)
        
        # Convert dataclasses to dictionaries for JSON serialization
        documents_data = []
        for doc in self.integrator.rts_its_documents:
            doc_dict = asdict(doc)
            # Convert date objects to strings
            if doc_dict['effective_date']:
                doc_dict['effective_date'] = doc_dict['effective_date'].isoformat()
            documents_data.append(doc_dict)
        
        mappings_data = [asdict(mapping) for mapping in self.integrator.requirement_mappings]
        
        export_data = {
            "generated_at": datetime.now().isoformat(),
            "technical_standards": documents_data,
            "requirement_mappings": mappings_data,
            "summary": self.generate_integration_summary()
        }
        
        # Save to file
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Integration data exported to: {output_file}")
        print(f"📊 Exported {len(documents_data)} technical standards")
        print(f"🔗 Exported {len(mappings_data)} requirement mappings")
        print(f"📄 File size: {output_file.stat().st_size / 1024:.1f} KB")
        
        return str(output_file)
    
    def run_full_demonstration(self):
        """Run complete demonstration"""
        print("🚀 DORA RTS/ITS Integration System Demonstration")
        print("🎯 MVP Demo - Technical Standards Integration")
        print("=" * 80)
        print()
        
        # Run all demonstrations
        self.demonstrate_rts_its_catalog()
        print("\n" + "=" * 80 + "\n")
        
        self.demonstrate_requirement_mappings()
        print("\n" + "=" * 80 + "\n")
        
        self.demonstrate_pillar_coverage()
        print("\n" + "=" * 80 + "\n")
        
        self.demonstrate_implementation_requirements()
        print("\n" + "=" * 80 + "\n")
        
        # Generate summary
        summary = self.generate_integration_summary()
        print("📊 Integration Summary")
        print("=" * 60)
        print(f"   • Total Technical Standards: {summary['total_standards']}")
        print(f"   • RTS Documents: {summary['rts_count']}")
        print(f"   • ITS Documents: {summary['its_count']}")
        print(f"   • Requirement Mappings: {summary['total_mappings']}")
        print(f"   • DORA Articles Covered: {summary['articles_covered']}")
        print(f"   • Effective Date: {summary['effective_date']}")
        print()
        
        # Export data
        export_file = self.export_integration_data()
        print()
        
        print("✅ RTS/ITS Integration Demonstration Completed!")
        print(f"📁 Integration data available in: {export_file}")
        print()
        print("🎯 Next Steps:")
        print("   1. Review technical standards and mappings")
        print("   2. Validate requirement mappings with domain experts")
        print("   3. Integrate with Policy Analyzer Agent")
        print("   4. Test compliance assessment with RTS/ITS context")
        print("   5. Deploy to DORA knowledge base database")

def main():
    """Main demonstration function"""
    try:
        demo = RTSITSDemo()
        demo.run_full_demonstration()
        return 0
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 