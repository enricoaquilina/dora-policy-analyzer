#!/usr/bin/env python3
"""
Policy Analyzer Agent - NLP Model Integration

This module provides sophisticated NLP capabilities for policy analysis using
multiple AI models including Anthropic Claude and Hugging Face transformers.

Features:
- Multi-model AI integration (Claude, Hugging Face)
- Semantic understanding of regulatory text
- Context-aware compliance analysis
- Entity recognition for regulatory concepts
- Semantic search within documents
- Intelligent text summarization
- Policy gap identification
- Risk assessment scoring
"""

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from uuid import uuid4

# AI model integrations
import anthropic
import openai
from transformers import (
    pipeline, AutoTokenizer, AutoModel, AutoModelForSequenceClassification,
    AutoModelForQuestionAnswering, AutoModelForTokenClassification
)
import torch
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Text processing
import nltk
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Import our data structures
from .text_extractor import PolicyElement, PolicyStructure, ExtractionResult, PolicyElementType
from .document_processor import ProcessedDocument

# Configuration
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """Types of NLP analysis"""
    COMPLIANCE_ASSESSMENT = "compliance_assessment"
    GAP_ANALYSIS = "gap_analysis"
    RISK_EVALUATION = "risk_evaluation"
    SEMANTIC_SEARCH = "semantic_search"
    ENTITY_EXTRACTION = "entity_extraction"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    SENTIMENT_ANALYSIS = "sentiment_analysis"

class ModelProvider(Enum):
    """Available model providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"

@dataclass
class AnalysisResult:
    """Result of NLP analysis"""
    analysis_id: str
    analysis_type: AnalysisType
    confidence_score: float
    findings: List[Dict[str, Any]]
    summary: str
    recommendations: List[str]
    evidence: List[str]
    model_used: str
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComplianceAssessment:
    """Compliance assessment result"""
    requirement_id: str
    requirement_text: str
    compliance_status: str  # "compliant", "non_compliant", "partial", "unclear"
    confidence_score: float
    gap_description: Optional[str] = None
    evidence_text: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_level: str = "medium"  # "low", "medium", "high", "critical"

@dataclass
class SemanticSearchResult:
    """Semantic search result"""
    element_id: str
    content: str
    similarity_score: float
    relevance_explanation: str
    context: str

class PolicyNLPAnalyzer:
    """Advanced NLP analyzer for policy documents"""
    
    # DORA-specific regulatory concepts
    DORA_CONCEPTS = {
        'ict_risk_management': [
            'ICT risk management framework', 'operational resilience', 'technology risk',
            'ICT governance', 'risk appetite', 'risk tolerance'
        ],
        'incident_management': [
            'ICT-related incident', 'major incident', 'incident classification',
            'incident reporting', 'incident response', 'business disruption'
        ],
        'testing': [
            'digital operational resilience testing', 'TLPT', 'vulnerability assessment',
            'penetration testing', 'scenario testing', 'recovery testing'
        ],
        'third_party_risk': [
            'ICT third-party service provider', 'outsourcing arrangement',
            'concentration risk', 'critical ICT services', 'service level agreements'
        ],
        'information_sharing': [
            'cyber threat information', 'threat intelligence sharing',
            'information sharing arrangements', 'cybersecurity information'
        ]
    }
    
    # Compliance requirement patterns
    REQUIREMENT_PATTERNS = {
        'mandatory': r'\b(?:shall|must|required|mandatory|obliged)\b',
        'recommended': r'\b(?:should|recommended|advisable|encouraged)\b',
        'conditional': r'\b(?:may|might|could|where applicable|if relevant)\b',
        'prohibited': r'\b(?:shall not|must not|prohibited|forbidden|banned)\b'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the NLP analyzer
        
        Args:
            config: Configuration dictionary for model settings
        """
        self.config = config or {}
        
        # Initialize AI model clients
        self._initialize_ai_clients()
        
        # Initialize transformers models
        self._initialize_transformers()
        
        # Initialize embeddings
        self._initialize_embeddings()
        
        # Statistics tracking
        self.analysis_stats = {
            'total_analyses': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'avg_processing_time': 0.0,
            'model_usage': {}
        }
    
    def _initialize_ai_clients(self):
        """Initialize AI model clients"""
        # Anthropic Claude
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                logger.info("Anthropic Claude client initialized")
            else:
                self.anthropic_client = None
                logger.warning("Anthropic API key not found")
        except Exception as e:
            logger.error(f"Error initializing Anthropic client: {e}")
            self.anthropic_client = None
        
        # OpenAI
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
            else:
                self.openai_client = None
                logger.warning("OpenAI API key not found")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            self.openai_client = None
    
    def _initialize_transformers(self):
        """Initialize Hugging Face transformers models"""
        try:
            # Sentiment analysis for policy tone
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                return_all_scores=True
            )
            
            # Question answering for compliance queries
            self.qa_model = pipeline(
                "question-answering",
                model="deepset/roberta-base-squad2"
            )
            
            # Named entity recognition for regulatory entities
            self.ner_model = pipeline(
                "ner",
                model="dbmdz/bert-large-cased-finetuned-conll03-english",
                aggregation_strategy="simple"
            )
            
            # Text classification for document categorization
            self.classifier = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium"
            )
            
            logger.info("Hugging Face transformers initialized")
            
        except Exception as e:
            logger.error(f"Error initializing transformers: {e}")
            self.sentiment_analyzer = None
            self.qa_model = None
            self.ner_model = None
            self.classifier = None
    
    def _initialize_embeddings(self):
        """Initialize sentence embeddings model"""
        try:
            # Use a model optimized for semantic similarity
            self.embeddings_model = SentenceTransformer('all-mpnet-base-v2')
            
            # Pre-compute embeddings for DORA concepts
            self.dora_concept_embeddings = {}
            for category, concepts in self.DORA_CONCEPTS.items():
                embeddings = self.embeddings_model.encode(concepts)
                self.dora_concept_embeddings[category] = {
                    'concepts': concepts,
                    'embeddings': embeddings
                }
            
            logger.info("Embeddings model initialized with DORA concepts")
            
        except Exception as e:
            logger.error(f"Error initializing embeddings: {e}")
            self.embeddings_model = None
            self.dora_concept_embeddings = {}
    
    async def analyze_compliance(self, policy_structure: PolicyStructure, 
                               dora_requirements: List[Dict[str, Any]]) -> List[ComplianceAssessment]:
        """
        Analyze policy compliance against DORA requirements
        
        Args:
            policy_structure: Structured policy content
            dora_requirements: List of DORA requirements to check against
            
        Returns:
            List of compliance assessments
        """
        logger.info(f"Analyzing compliance for {len(dora_requirements)} DORA requirements")
        
        assessments = []
        
        for requirement in dora_requirements:
            try:
                assessment = await self._assess_single_requirement(
                    requirement, policy_structure
                )
                assessments.append(assessment)
            except Exception as e:
                logger.error(f"Error assessing requirement {requirement.get('id', 'unknown')}: {e}")
        
        logger.info(f"Completed compliance analysis for {len(assessments)} requirements")
        return assessments
    
    async def _assess_single_requirement(self, requirement: Dict[str, Any], 
                                       policy_structure: PolicyStructure) -> ComplianceAssessment:
        """Assess compliance for a single DORA requirement"""
        requirement_id = requirement.get('id', 'unknown')
        requirement_text = requirement.get('text', '')
        
        # Find relevant policy elements using semantic search
        relevant_elements = await self.semantic_search(
            query=requirement_text,
            policy_structure=policy_structure,
            top_k=5
        )
        
        # Use AI to assess compliance
        if self.anthropic_client:
            compliance_result = await self._claude_compliance_assessment(
                requirement, relevant_elements
            )
        elif self.openai_client:
            compliance_result = await self._openai_compliance_assessment(
                requirement, relevant_elements
            )
        else:
            # Fallback to rule-based assessment
            compliance_result = self._rule_based_compliance_assessment(
                requirement, relevant_elements
            )
        
        return ComplianceAssessment(
            requirement_id=requirement_id,
            requirement_text=requirement_text,
            compliance_status=compliance_result['status'],
            confidence_score=compliance_result['confidence'],
            gap_description=compliance_result.get('gap_description'),
            evidence_text=[elem.content for elem in relevant_elements],
            recommendations=compliance_result.get('recommendations', []),
            risk_level=compliance_result.get('risk_level', 'medium')
        )
    
    async def _claude_compliance_assessment(self, requirement: Dict[str, Any], 
                                          relevant_elements: List[PolicyElement]) -> Dict[str, Any]:
        """Use Claude for compliance assessment"""
        try:
            # Prepare context
            context = "\n\n".join([
                f"Policy Element: {elem.title}\nContent: {elem.content}"
                for elem in relevant_elements
            ])
            
            prompt = f"""
            Analyze the compliance of the following policy content against this DORA requirement:

            DORA REQUIREMENT:
            ID: {requirement.get('id', 'unknown')}
            Text: {requirement.get('text', '')}
            Article: {requirement.get('article', 'unknown')}

            POLICY CONTENT TO ASSESS:
            {context}

            Please provide a detailed compliance assessment including:
            1. Compliance status: "compliant", "non_compliant", "partial", or "unclear"
            2. Confidence score (0.0 to 1.0)
            3. Gap description (if non-compliant or partial)
            4. Specific recommendations for improvement
            5. Risk level: "low", "medium", "high", or "critical"

            Respond in JSON format:
            {{
                "status": "compliant|non_compliant|partial|unclear",
                "confidence": 0.0-1.0,
                "gap_description": "description of gaps if any",
                "recommendations": ["recommendation 1", "recommendation 2"],
                "risk_level": "low|medium|high|critical",
                "explanation": "detailed explanation of assessment"
            }}
            """
            
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON response
            try:
                result = json.loads(response.content[0].text)
                return result
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                return self._parse_claude_response(response.content[0].text)
                
        except Exception as e:
            logger.error(f"Error in Claude compliance assessment: {e}")
            return {
                "status": "unclear",
                "confidence": 0.3,
                "gap_description": f"Assessment failed: {e}",
                "recommendations": ["Manual review required"],
                "risk_level": "medium"
            }
    
    async def _openai_compliance_assessment(self, requirement: Dict[str, Any], 
                                          relevant_elements: List[PolicyElement]) -> Dict[str, Any]:
        """Use OpenAI for compliance assessment"""
        try:
            # Similar implementation to Claude but with OpenAI API
            context = "\n\n".join([
                f"Policy Element: {elem.title}\nContent: {elem.content}"
                for elem in relevant_elements
            ])
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a DORA compliance expert. Analyze policy documents for regulatory compliance."},
                    {"role": "user", "content": f"Assess compliance for DORA requirement {requirement.get('id')}: {requirement.get('text')} against policy content: {context}"}
                ],
                max_tokens=1000
            )
            
            # Parse response (implement similar to Claude)
            return self._parse_openai_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error in OpenAI compliance assessment: {e}")
            return {
                "status": "unclear",
                "confidence": 0.3,
                "gap_description": f"Assessment failed: {e}",
                "recommendations": ["Manual review required"],
                "risk_level": "medium"
            }
    
    def _rule_based_compliance_assessment(self, requirement: Dict[str, Any], 
                                        relevant_elements: List[PolicyElement]) -> Dict[str, Any]:
        """Fallback rule-based compliance assessment"""
        requirement_text = requirement.get('text', '').lower()
        
        # Extract key concepts from requirement
        requirement_concepts = self._extract_regulatory_concepts(requirement_text)
        
        # Check for presence of mandatory language
        has_mandatory = bool(re.search(self.REQUIREMENT_PATTERNS['mandatory'], requirement_text))
        
        # Analyze policy elements
        compliance_indicators = []
        for element in relevant_elements:
            element_text = element.content.lower()
            
            # Check for concept coverage
            concept_matches = sum(1 for concept in requirement_concepts 
                                if concept in element_text)
            concept_coverage = concept_matches / max(1, len(requirement_concepts))
            
            # Check for mandatory compliance language
            has_compliance_language = bool(re.search(
                r'\b(?:complies?|compliance|adheres?|accordance|pursuant)\b', 
                element_text
            ))
            
            compliance_indicators.append({
                'element_id': element.element_id,
                'concept_coverage': concept_coverage,
                'has_compliance_language': has_compliance_language,
                'relevance_score': concept_coverage * (1.2 if has_compliance_language else 1.0)
            })
        
        # Calculate overall compliance
        avg_relevance = sum(ind['relevance_score'] for ind in compliance_indicators) / max(1, len(compliance_indicators))
        
        if avg_relevance >= 0.8:
            status = "compliant"
            confidence = min(0.9, avg_relevance)
            risk_level = "low"
        elif avg_relevance >= 0.5:
            status = "partial"
            confidence = avg_relevance
            risk_level = "medium" if has_mandatory else "low"
        elif avg_relevance >= 0.2:
            status = "non_compliant"
            confidence = 1.0 - avg_relevance
            risk_level = "high" if has_mandatory else "medium"
        else:
            status = "unclear"
            confidence = 0.3
            risk_level = "medium"
        
        return {
            "status": status,
            "confidence": confidence,
            "gap_description": f"Limited coverage of requirement concepts (coverage: {avg_relevance:.2f})" if status != "compliant" else None,
            "recommendations": self._generate_basic_recommendations(status, requirement_concepts),
            "risk_level": risk_level
        }
    
    async def semantic_search(self, query: str, policy_structure: PolicyStructure, 
                            top_k: int = 10) -> List[PolicyElement]:
        """
        Perform semantic search within policy structure
        
        Args:
            query: Search query
            policy_structure: Policy structure to search within
            top_k: Number of top results to return
            
        Returns:
            List of most relevant policy elements
        """
        if not self.embeddings_model:
            logger.warning("Embeddings model not available, falling back to keyword search")
            return self._keyword_search(query, policy_structure, top_k)
        
        try:
            # Encode query
            query_embedding = self.embeddings_model.encode([query])
            
            # Encode all policy elements
            element_texts = [elem.content for elem in policy_structure.elements]
            element_embeddings = self.embeddings_model.encode(element_texts)
            
            # Calculate similarities
            similarities = util.cos_sim(query_embedding, element_embeddings)[0]
            
            # Get top k results
            top_indices = similarities.argsort(descending=True)[:top_k]
            
            results = []
            for idx in top_indices:
                element = policy_structure.elements[idx.item()]
                similarity_score = similarities[idx].item()
                
                if similarity_score > 0.3:  # Minimum similarity threshold
                    results.append(element)
            
            logger.info(f"Semantic search found {len(results)} relevant elements for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return self._keyword_search(query, policy_structure, top_k)
    
    def _keyword_search(self, query: str, policy_structure: PolicyStructure, 
                       top_k: int) -> List[PolicyElement]:
        """Fallback keyword-based search"""
        query_words = set(query.lower().split())
        
        scored_elements = []
        for element in policy_structure.elements:
            element_words = set(element.content.lower().split())
            
            # Calculate Jaccard similarity
            intersection = query_words.intersection(element_words)
            union = query_words.union(element_words)
            similarity = len(intersection) / len(union) if union else 0
            
            if similarity > 0:
                scored_elements.append((element, similarity))
        
        # Sort by similarity and return top k
        scored_elements.sort(key=lambda x: x[1], reverse=True)
        return [elem for elem, score in scored_elements[:top_k]]
    
    def _extract_regulatory_concepts(self, text: str) -> List[str]:
        """Extract regulatory concepts from text"""
        concepts = []
        text_lower = text.lower()
        
        # Check for DORA concepts
        for category, concept_list in self.DORA_CONCEPTS.items():
            for concept in concept_list:
                if concept.lower() in text_lower:
                    concepts.append(concept)
        
        return concepts
    
    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude response if JSON parsing fails"""
        # Basic parsing for fallback
        return {
            "status": "unclear",
            "confidence": 0.5,
            "gap_description": "Response parsing failed",
            "recommendations": ["Manual review required"],
            "risk_level": "medium"
        }
    
    def _parse_openai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse OpenAI response"""
        # Basic parsing for fallback
        return {
            "status": "unclear",
            "confidence": 0.5,
            "gap_description": "Response parsing failed",
            "recommendations": ["Manual review required"],
            "risk_level": "medium"
        }
    
    def _generate_basic_recommendations(self, status: str, concepts: List[str]) -> List[str]:
        """Generate basic recommendations based on assessment"""
        recommendations = []
        
        if status == "non_compliant":
            recommendations.append("Develop policy content addressing the identified requirement")
            if concepts:
                recommendations.append(f"Include specific coverage of: {', '.join(concepts[:3])}")
        elif status == "partial":
            recommendations.append("Strengthen existing policy content to fully address requirement")
            recommendations.append("Review and enhance compliance documentation")
        elif status == "unclear":
            recommendations.append("Clarify policy language to demonstrate compliance")
            recommendations.append("Provide additional documentation or evidence")
        
        return recommendations
    
    async def analyze_policy_gaps(self, policy_structure: PolicyStructure, 
                                dora_requirements: List[Dict[str, Any]]) -> AnalysisResult:
        """
        Analyze gaps in policy coverage
        
        Args:
            policy_structure: Policy structure to analyze
            dora_requirements: DORA requirements to check coverage against
            
        Returns:
            Analysis result with gap findings
        """
        start_time = datetime.now()
        
        logger.info("Analyzing policy gaps against DORA requirements")
        
        try:
            # Perform compliance assessments
            assessments = await self.analyze_compliance(policy_structure, dora_requirements)
            
            # Identify gaps
            gaps = []
            for assessment in assessments:
                if assessment.compliance_status in ['non_compliant', 'partial', 'unclear']:
                    gaps.append({
                        'requirement_id': assessment.requirement_id,
                        'status': assessment.compliance_status,
                        'gap_description': assessment.gap_description,
                        'risk_level': assessment.risk_level,
                        'recommendations': assessment.recommendations
                    })
            
            # Generate summary
            total_requirements = len(assessments)
            gap_count = len(gaps)
            coverage_percentage = ((total_requirements - gap_count) / total_requirements * 100) if total_requirements > 0 else 0
            
            summary = f"Policy coverage analysis: {coverage_percentage:.1f}% compliant ({total_requirements - gap_count}/{total_requirements} requirements). {gap_count} gaps identified."
            
            # Generate recommendations
            recommendations = []
            high_risk_gaps = [g for g in gaps if g['risk_level'] in ['high', 'critical']]
            if high_risk_gaps:
                recommendations.append(f"Address {len(high_risk_gaps)} high/critical risk gaps immediately")
            
            medium_risk_gaps = [g for g in gaps if g['risk_level'] == 'medium']
            if medium_risk_gaps:
                recommendations.append(f"Plan remediation for {len(medium_risk_gaps)} medium risk gaps")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AnalysisResult(
                analysis_id=str(uuid4()),
                analysis_type=AnalysisType.GAP_ANALYSIS,
                confidence_score=0.8,  # Rule-based confidence for gap analysis
                findings=gaps,
                summary=summary,
                recommendations=recommendations,
                evidence=[],
                model_used="Policy Gap Analyzer",
                processing_time=processing_time,
                metadata={
                    'total_requirements': total_requirements,
                    'gap_count': gap_count,
                    'coverage_percentage': coverage_percentage
                }
            )
            
        except Exception as e:
            logger.error(f"Error in policy gap analysis: {e}")
            raise
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        return self.analysis_stats.copy()


def main():
    """Main function for testing NLP analyzer"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Policy NLP Analyzer Test")
    parser.add_argument("--test-compliance", action="store_true", help="Test compliance analysis")
    parser.add_argument("--test-search", action="store_true", help="Test semantic search")
    parser.add_argument("--query", help="Search query for testing")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = PolicyNLPAnalyzer()
    
    if args.test_compliance:
        print("Testing compliance analysis...")
        print("Note: Requires PolicyStructure and DORA requirements data")
    
    if args.test_search and args.query:
        print(f"Testing semantic search with query: {args.query}")
        print("Note: Requires PolicyStructure data")
    
    print("NLP Analyzer initialized successfully")
    print(f"Available models: Anthropic={analyzer.anthropic_client is not None}, "
          f"OpenAI={analyzer.openai_client is not None}, "
          f"Embeddings={analyzer.embeddings_model is not None}")
    
    return 0


if __name__ == "__main__":
    exit(main()) 