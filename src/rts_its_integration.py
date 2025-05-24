#!/usr/bin/env python3
"""
RTS/ITS Integration Module for Policy Analyzer

This module integrates Regulatory Technical Standards (RTS) and Implementing 
Technical Standards (ITS) data with the Policy Analyzer to provide enhanced 
compliance analysis with technical standards context.

Features:
- Load RTS/ITS technical standards data
- Map policy content to relevant technical standards
- Enhance compliance analysis with regulatory context
- Provide specific implementation guidance

Author: DORA Compliance System
Date: 2025-01-23
"""

import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

# Add the dora-knowledge-base scripts to path
sys.path.append(str(Path(__file__).parent.parent.parent / "dora-knowledge-base" / "scripts"))

try:
    from rts_its_integrator import RTSITSIntegrator, RTSITSDocument, RequirementMapping
    RTS_ITS_AVAILABLE = True
except ImportError:
    RTS_ITS_AVAILABLE = False
    # Create dummy classes for typing
    class RTSITSDocument:
        def __init__(self):
            self.standard_id = ""
            self.standard_type = ""
            self.title = ""
            self.description = ""
            self.effective_date = None
            self.status = ""
            self.related_articles = []
            self.key_provisions = []
            self.implementation_requirements = []
            self.entity_scope = []
    
    class RequirementMapping:
        pass
    
    class RTSITSIntegrator:
        pass

logger = logging.getLogger(__name__)

@dataclass
class TechnicalStandardsEnhancement:
    """Enhanced analysis with technical standards context"""
    matched_standards: List[Dict[str, Any]]
    implementation_guidance: List[str]
    compliance_gaps: List[str]
    priority_recommendations: List[str]
    regulatory_references: List[str]

@dataclass
class EnhancedComplianceResult:
    """Enhanced compliance analysis result"""
    article_reference: str
    compliance_status: str
    confidence_score: float
    technical_standards: List[Dict[str, Any]]
    implementation_notes: List[str]
    gap_analysis: List[str]
    next_steps: List[str]

class RTSITSPolicyIntegrator:
    """Integration layer between Policy Analyzer and RTS/ITS data"""
    
    def __init__(self):
        """Initialize the integrator"""
        self.rts_its_integrator = None
        self.technical_standards = []
        self.requirement_mappings = []
        self.loaded = False
        
        # Load RTS/ITS data if available
        self._load_rts_its_data()
    
    def _load_rts_its_data(self):
        """Load RTS/ITS technical standards data"""
        if not RTS_ITS_AVAILABLE:
            logger.warning("RTS/ITS integrator not available - running without technical standards")
            return
        
        try:
            # Create integrator instance (without database connection)
            self.rts_its_integrator = RTSITSIntegrator.__new__(RTSITSIntegrator)
            self.rts_its_integrator.rts_its_documents = []
            self.rts_its_integrator.requirement_mappings = []
            
            # Load the catalog
            self.rts_its_integrator._load_rts_its_catalog()
            self.rts_its_integrator._create_requirement_mappings()
            
            # Store in accessible format
            self.technical_standards = self.rts_its_integrator.rts_its_documents
            self.requirement_mappings = self.rts_its_integrator.requirement_mappings
            
            self.loaded = True
            logger.info(f"Loaded {len(self.technical_standards)} technical standards and {len(self.requirement_mappings)} mappings")
            
        except Exception as e:
            logger.error(f"Failed to load RTS/ITS data: {e}")
            self.loaded = False
    
    def enhance_compliance_analysis(self, policy_analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance policy analysis with technical standards context"""
        if not self.loaded:
            logger.warning("RTS/ITS data not loaded - returning original analysis")
            return policy_analysis_result
        
        try:
            enhanced_result = policy_analysis_result.copy()
            
            # Add technical standards section
            enhanced_result["technical_standards_analysis"] = self._analyze_technical_standards_context(policy_analysis_result)
            
            # Enhance DORA compliance analysis
            if "dora_compliance" in policy_analysis_result:
                enhanced_result["dora_compliance"] = self._enhance_dora_compliance(policy_analysis_result["dora_compliance"])
            
            # Add implementation guidance
            enhanced_result["implementation_guidance"] = self._generate_implementation_guidance(policy_analysis_result)
            
            # Add regulatory context
            enhanced_result["regulatory_context"] = self._provide_regulatory_context(policy_analysis_result)
            
            logger.info("Successfully enhanced policy analysis with technical standards context")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Failed to enhance compliance analysis: {e}")
            return policy_analysis_result
    
    def _analyze_technical_standards_context(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical standards context for the policy"""
        context = {
            "applicable_standards": [],
            "coverage_analysis": {},
            "implementation_requirements": [],
            "effective_dates": []
        }
        
        # Extract policy content for matching
        policy_content = analysis.get("document_content", {}).get("text_content", "")
        dora_compliance = analysis.get("dora_compliance", {})
        
        # Find applicable technical standards
        applicable_standards = self._match_technical_standards(policy_content, dora_compliance)
        
        for standard in applicable_standards:
            standard_dict = {
                "standard_id": standard.standard_id,
                "standard_type": standard.standard_type,
                "title": standard.title,
                "description": standard.description,
                "effective_date": standard.effective_date.isoformat() if standard.effective_date else None,
                "status": standard.status,
                "related_articles": standard.related_articles,
                "key_provisions": standard.key_provisions,
                "implementation_requirements": standard.implementation_requirements,
                "entity_scope": standard.entity_scope
            }
            context["applicable_standards"].append(standard_dict)
            
            # Add implementation requirements
            context["implementation_requirements"].extend(standard.implementation_requirements)
            
            # Track effective dates
            if standard.effective_date:
                context["effective_dates"].append({
                    "standard_id": standard.standard_id,
                    "effective_date": standard.effective_date.isoformat(),
                    "status": standard.status
                })
        
        # Analyze coverage by pillar
        context["coverage_analysis"] = self._analyze_pillar_coverage(applicable_standards)
        
        return context
    
    def _match_technical_standards(self, policy_content: str, dora_compliance: Dict[str, Any]) -> List[RTSITSDocument]:
        """Match technical standards to policy content"""
        matched_standards = []
        
        # Extract mentioned articles from DORA compliance analysis
        mentioned_articles = set()
        if isinstance(dora_compliance, dict):
            for pillar_data in dora_compliance.values():
                if isinstance(pillar_data, dict) and "articles" in pillar_data:
                    for article in pillar_data["articles"]:
                        if isinstance(article, dict) and "article_number" in article:
                            mentioned_articles.add(str(article["article_number"]))
        
        # Match standards based on related articles
        for standard in self.technical_standards:
            # Check if any related article is mentioned in the compliance analysis
            if any(article in mentioned_articles for article in standard.related_articles):
                matched_standards.append(standard)
                continue
            
            # Check for keyword matches in policy content
            policy_lower = policy_content.lower()
            title_words = standard.title.lower().split()
            
            # Look for key terms
            key_terms = [
                "incident", "reporting", "risk management", "testing", 
                "penetration", "information sharing", "third-party",
                "operational resilience", "cyber", "ict"
            ]
            
            if any(term in policy_lower for term in key_terms if term in standard.title.lower()):
                matched_standards.append(standard)
        
        return matched_standards
    
    def _enhance_dora_compliance(self, dora_compliance: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance DORA compliance analysis with technical standards context"""
        enhanced_compliance = dora_compliance.copy()
        
        # Add technical standards context to each pillar
        for pillar_name, pillar_data in enhanced_compliance.items():
            if isinstance(pillar_data, dict):
                pillar_data["technical_standards"] = self._get_pillar_technical_standards(pillar_name)
                pillar_data["implementation_guidance"] = self._get_pillar_implementation_guidance(pillar_name)
        
        return enhanced_compliance
    
    def _get_pillar_technical_standards(self, pillar_name: str) -> List[Dict[str, Any]]:
        """Get technical standards relevant to a specific DORA pillar"""
        # Map pillar names to relevant articles
        pillar_articles = {
            "ict_governance": ["5", "6", "15", "16"],
            "ict_risk_management": ["8", "9", "10", "11"],
            "ict_incident_management": ["17", "18", "19", "20", "21"],
            "digital_operational_resilience_testing": ["24", "25", "26"],
            "ict_third_party_risk": ["28", "29", "30"],
            "information_sharing": ["45", "46"]
        }
        
        relevant_articles = pillar_articles.get(pillar_name.lower(), [])
        relevant_standards = []
        
        for standard in self.technical_standards:
            if any(article in standard.related_articles for article in relevant_articles):
                relevant_standards.append({
                    "standard_id": standard.standard_id,
                    "title": standard.title,
                    "standard_type": standard.standard_type,
                    "related_articles": standard.related_articles
                })
        
        return relevant_standards
    
    def _get_pillar_implementation_guidance(self, pillar_name: str) -> List[str]:
        """Get implementation guidance for a specific DORA pillar"""
        guidance = []
        
        pillar_standards = self._get_pillar_technical_standards(pillar_name)
        for standard_info in pillar_standards:
            # Find the full standard object
            full_standard = next(
                (s for s in self.technical_standards if s.standard_id == standard_info["standard_id"]), 
                None
            )
            
            if full_standard:
                guidance.extend(full_standard.implementation_requirements)
        
        return list(set(guidance))  # Remove duplicates
    
    def _analyze_pillar_coverage(self, standards: List[RTSITSDocument]) -> Dict[str, Any]:
        """Analyze coverage of DORA pillars by technical standards"""
        coverage = {
            "ict_incident_management": {"standards": 0, "coverage": "none"},
            "ict_third_party_risk": {"standards": 0, "coverage": "none"},
            "digital_operational_resilience_testing": {"standards": 0, "coverage": "none"},
            "governance_oversight": {"standards": 0, "coverage": "none"},
            "information_sharing": {"standards": 0, "coverage": "none"}
        }
        
        # Article to pillar mapping
        article_pillar_map = {
            "17": "ict_incident_management", "18": "ict_incident_management", 
            "19": "ict_incident_management", "20": "ict_incident_management", "21": "ict_incident_management",
            "24": "digital_operational_resilience_testing", "25": "digital_operational_resilience_testing", 
            "26": "digital_operational_resilience_testing",
            "28": "ict_third_party_risk", "29": "ict_third_party_risk",
            "32": "governance_oversight", "33": "governance_oversight", 
            "34": "governance_oversight", "35": "governance_oversight",
            "45": "information_sharing", "46": "information_sharing"
        }
        
        # Count standards per pillar
        for standard in standards:
            for article in standard.related_articles:
                pillar = article_pillar_map.get(article)
                if pillar:
                    coverage[pillar]["standards"] += 1
        
        # Determine coverage level
        for pillar in coverage:
            count = coverage[pillar]["standards"]
            if count == 0:
                coverage[pillar]["coverage"] = "none"
            elif count <= 2:
                coverage[pillar]["coverage"] = "partial"
            else:
                coverage[pillar]["coverage"] = "comprehensive"
        
        return coverage
    
    def _generate_implementation_guidance(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate implementation guidance based on matched technical standards"""
        guidance = []
        
        # Get technical standards analysis
        tech_standards = analysis.get("technical_standards_analysis", {})
        applicable_standards = tech_standards.get("applicable_standards", [])
        
        for standard in applicable_standards:
            # Add standard-specific guidance
            guidance.append(f"Implement {standard['title']} requirements:")
            
            # Add implementation requirements
            for req in standard.get("implementation_requirements", []):
                guidance.append(f"  • {req}")
            
            # Add effective date considerations
            if standard.get("effective_date"):
                effective_date = datetime.fromisoformat(standard["effective_date"]).strftime("%B %d, %Y")
                guidance.append(f"  • Ensure compliance by effective date: {effective_date}")
        
        if not guidance:
            guidance.append("No specific technical standards implementation requirements identified")
        
        return guidance
    
    def _provide_regulatory_context(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Provide regulatory context and references"""
        context = {
            "regulatory_framework": "DORA (Digital Operational Resilience Act)",
            "effective_date": "January 17, 2025",
            "scope": "Financial entities and ICT third-party service providers",
            "key_deadlines": [],
            "regulatory_authorities": [
                "European Banking Authority (EBA)",
                "European Securities and Markets Authority (ESMA)", 
                "European Insurance and Occupational Pensions Authority (EIOPA)"
            ],
            "compliance_obligations": []
        }
        
        # Add technical standards specific deadlines
        tech_standards = analysis.get("technical_standards_analysis", {})
        for date_info in tech_standards.get("effective_dates", []):
            context["key_deadlines"].append({
                "standard": date_info["standard_id"],
                "date": date_info["effective_date"],
                "status": date_info["status"]
            })
        
        # Add compliance obligations based on applicable standards
        applicable_standards = tech_standards.get("applicable_standards", [])
        for standard in applicable_standards:
            for provision in standard.get("key_provisions", []):
                context["compliance_obligations"].append({
                    "standard": standard["standard_id"],
                    "obligation": provision,
                    "scope": standard.get("entity_scope", [])
                })
        
        return context
    
    def get_technical_standards_summary(self) -> Dict[str, Any]:
        """Get summary of all technical standards"""
        if not self.loaded:
            return {"error": "Technical standards data not available"}
        
        summary = {
            "total_standards": len(self.technical_standards),
            "rts_count": sum(1 for s in self.technical_standards if s.standard_type == "RTS"),
            "its_count": sum(1 for s in self.technical_standards if s.standard_type == "ITS"),
            "standards_by_pillar": {},
            "effective_dates": [],
            "status_distribution": {}
        }
        
        # Count by status
        for standard in self.technical_standards:
            status = standard.status
            summary["status_distribution"][status] = summary["status_distribution"].get(status, 0) + 1
            
            # Add effective dates
            if standard.effective_date:
                summary["effective_dates"].append({
                    "standard_id": standard.standard_id,
                    "effective_date": standard.effective_date.isoformat(),
                    "status": status
                })
        
        return summary
    
    def search_technical_standards(self, query: str) -> List[Dict[str, Any]]:
        """Search technical standards by query"""
        if not self.loaded:
            return []
        
        query_lower = query.lower()
        results = []
        
        for standard in self.technical_standards:
            # Search in title, description, and key provisions
            searchable_text = f"{standard.title} {standard.description} {' '.join(standard.key_provisions)}".lower()
            
            if query_lower in searchable_text:
                results.append({
                    "standard_id": standard.standard_id,
                    "title": standard.title,
                    "standard_type": standard.standard_type,
                    "description": standard.description,
                    "related_articles": standard.related_articles,
                    "relevance_score": self._calculate_relevance(query_lower, searchable_text)
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results
    
    def _calculate_relevance(self, query: str, text: str) -> float:
        """Calculate relevance score for search results"""
        # Simple relevance scoring based on term frequency
        words = query.split()
        score = 0.0
        
        for word in words:
            if word in text:
                score += text.count(word) / len(text.split())
        
        return score

# Create global instance
rts_its_integrator = RTSITSPolicyIntegrator()

def enhance_policy_analysis(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to enhance policy analysis with RTS/ITS context"""
    return rts_its_integrator.enhance_compliance_analysis(analysis_result)

def get_technical_standards_data() -> Dict[str, Any]:
    """Get technical standards data for web interface"""
    return rts_its_integrator.get_technical_standards_summary()

def search_standards(query: str) -> List[Dict[str, Any]]:
    """Search technical standards"""
    return rts_its_integrator.search_technical_standards(query) 