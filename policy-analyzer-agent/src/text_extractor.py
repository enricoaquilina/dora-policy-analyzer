#!/usr/bin/env python3
"""
Policy Analyzer Agent - Advanced Text Extraction and Structuring

This module provides sophisticated text extraction and structuring capabilities
specifically designed for policy documents, regulatory texts, and compliance documents.

Features:
- Intelligent policy structure recognition
- Regulatory clause extraction and categorization
- Hierarchical content organization
- Policy statement identification
- Control objective extraction
- Compliance requirement parsing
- Cross-reference resolution
- Semantic section analysis
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from uuid import uuid4

# NLP and text processing
import nltk
import spacy
from nltk.tokenize import sent_tokenize, word_tokenize, line_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.tree import Tree

# ML and embeddings
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import our document processor
from .document_processor import ProcessedDocument, DocumentSection, DocumentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolicyElementType(Enum):
    """Types of policy elements"""
    POLICY_STATEMENT = "policy_statement"
    CONTROL_OBJECTIVE = "control_objective"
    REQUIREMENT = "requirement"
    PROCEDURE = "procedure"
    RESPONSIBILITY = "responsibility"
    EXCEPTION = "exception"
    DEFINITION = "definition"
    SCOPE = "scope"
    APPENDIX = "appendix"
    REFERENCE = "reference"
    REVIEW_CYCLE = "review_cycle"
    APPROVAL = "approval"
    ENFORCEMENT = "enforcement"

class StructureLevel(Enum):
    """Document structure hierarchy levels"""
    DOCUMENT = "document"
    CHAPTER = "chapter"
    SECTION = "section"
    SUBSECTION = "subsection"
    PARAGRAPH = "paragraph"
    CLAUSE = "clause"
    SUBCLAUSE = "subclause"
    ITEM = "item"

@dataclass
class PolicyElement:
    """Individual policy element"""
    element_id: str
    element_type: PolicyElementType
    title: str
    content: str
    level: StructureLevel
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    section_number: Optional[str] = None
    page_reference: Optional[int] = None
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    cross_references: List[str] = field(default_factory=list)
    compliance_tags: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    
@dataclass
class PolicyStructure:
    """Hierarchical policy document structure"""
    document_id: str
    title: str
    elements: List[PolicyElement]
    hierarchy: Dict[str, List[str]]  # parent_id -> [child_ids]
    element_index: Dict[str, PolicyElement]  # element_id -> element
    cross_reference_map: Dict[str, List[str]]  # element_id -> [referenced_element_ids]
    compliance_mapping: Dict[str, List[str]]  # compliance_tag -> [element_ids]
    extraction_stats: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExtractionResult:
    """Complete text extraction result"""
    document_id: str
    original_sections: List[DocumentSection]
    policy_structure: PolicyStructure
    extracted_text: str
    structured_content: str
    processing_quality: float
    extraction_method: str
    processing_time: float

class PolicyTextExtractor:
    """Advanced text extractor for policy documents"""
    
    # Policy-specific patterns
    POLICY_PATTERNS = {
        'policy_statement': [
            r'(?i)\b(?:policy|policies)\b.*?(?:states?|requires?|mandates?)',
            r'(?i)\bit is (?:the )?(?:policy|requirement) (?:of|that)',
            r'(?i)\bthis (?:policy|document) (?:establishes?|defines?|requires?)',
        ],
        'control_objective': [
            r'(?i)\b(?:control|controls?) (?:objective|purpose|goal)',
            r'(?i)\bto ensure (?:that|the)',
            r'(?i)\bthe (?:purpose|objective|goal) (?:of|is)',
        ],
        'requirement': [
            r'(?i)\b(?:must|shall|should|required?|mandatory)\b',
            r'(?i)\bis required to\b',
            r'(?i)\bat a minimum\b',
        ],
        'procedure': [
            r'(?i)\b(?:procedure|process|steps?|methodology)\b',
            r'(?i)\bthe following (?:steps?|procedures?|process)',
            r'(?i)\bin accordance with\b',
        ],
        'responsibility': [
            r'(?i)\b(?:responsible|responsibility|accountable|owns?)\b',
            r'(?i)\broles? and responsibilities\b',
            r'(?i)\bis responsible for\b',
        ],
        'definition': [
            r'(?i)\b(?:means?|defined? as|definition)\b',
            r'(?i)\bfor (?:the )?purposes? of this\b',
            r'(?i)\brefers? to\b',
        ]
    }
    
    # Section recognition patterns
    SECTION_PATTERNS = {
        'numbered': r'^(\d+(?:\.\d+)*)\s+(.+)$',
        'alphabetic': r'^([A-Z](?:\.[A-Z])*)\s+(.+)$',
        'roman': r'^([IVX]+(?:\.[IVX]+)*)\s+(.+)$',
        'bulleted': r'^\s*[•\-\*]\s+(.+)$',
        'titled': r'^([A-Z][A-Z\s]{5,})$',
    }
    
    # Compliance-related keywords
    COMPLIANCE_KEYWORDS = {
        'dora': ['operational resilience', 'ict risk', 'digital operational', 'third party risk', 'incident management'],
        'gdpr': ['personal data', 'data protection', 'privacy', 'data subject', 'processing'],
        'iso27001': ['information security', 'isms', 'security controls', 'risk management'],
        'sox': ['financial reporting', 'internal controls', 'disclosure controls'],
        'basel': ['operational risk', 'capital requirements', 'risk management'],
        'general': ['compliance', 'regulatory', 'audit', 'monitoring', 'reporting']
    }
    
    def __init__(self, language: str = 'en'):
        """
        Initialize the policy text extractor
        
        Args:
            language: Language for text processing
        """
        self.language = language
        
        # Initialize NLP components
        self._initialize_nlp()
        
        # Initialize embeddings model
        self._initialize_embeddings()
        
        # Statistics tracking
        self.extraction_stats = {
            'documents_processed': 0,
            'elements_extracted': 0,
            'cross_references_found': 0,
            'avg_processing_time': 0.0
        }
    
    def _initialize_nlp(self):
        """Initialize NLP libraries and models"""
        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('maxent_ne_chunker', quiet=True)
            nltk.download('words', quiet=True)
            
            # Load spaCy model
            try:
                self.nlp = spacy.load('en_core_web_sm')
            except OSError:
                logger.warning("spaCy English model not found. Installing...")
                try:
                    import subprocess
                    subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'], 
                                 check=True, capture_output=True)
                    self.nlp = spacy.load('en_core_web_sm')
                except Exception:
                    logger.error("Could not install spaCy model. Using basic processing.")
                    self.nlp = None
                    
            # Initialize stopwords
            self.stop_words = set(stopwords.words('english'))
            
        except Exception as e:
            logger.error(f"Error initializing NLP: {e}")
            self.nlp = None
            self.stop_words = set()
    
    def _initialize_embeddings(self):
        """Initialize sentence embeddings model"""
        try:
            # Use a lightweight but effective model for MVP
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence embeddings model")
        except Exception as e:
            logger.warning(f"Could not load embeddings model: {e}")
            self.embeddings_model = None
    
    def extract_and_structure(self, processed_doc: ProcessedDocument) -> ExtractionResult:
        """
        Main method to extract and structure text from processed document
        
        Args:
            processed_doc: ProcessedDocument from document processor
            
        Returns:
            ExtractionResult with structured policy content
        """
        start_time = datetime.now()
        
        logger.info(f"Extracting and structuring text for document: {processed_doc.document_id}")
        
        try:
            # Extract policy elements from document sections
            policy_elements = self._extract_policy_elements(processed_doc.structured_content)
            
            # Build hierarchical structure
            hierarchy = self._build_hierarchy(policy_elements)
            
            # Create element index for fast lookup
            element_index = {elem.element_id: elem for elem in policy_elements}
            
            # Resolve cross-references
            cross_reference_map = self._resolve_cross_references(policy_elements, processed_doc.raw_text)
            
            # Create compliance mapping
            compliance_mapping = self._create_compliance_mapping(policy_elements)
            
            # Generate structured content
            structured_content = self._generate_structured_content(policy_elements, hierarchy)
            
            # Calculate processing quality
            quality_score = self._calculate_extraction_quality(
                processed_doc, policy_elements, cross_reference_map
            )
            
            # Create policy structure
            policy_structure = PolicyStructure(
                document_id=processed_doc.document_id,
                title=processed_doc.metadata.title or processed_doc.metadata.filename,
                elements=policy_elements,
                hierarchy=hierarchy,
                element_index=element_index,
                cross_reference_map=cross_reference_map,
                compliance_mapping=compliance_mapping,
                extraction_stats={
                    'total_elements': len(policy_elements),
                    'element_types': self._count_element_types(policy_elements),
                    'hierarchy_depth': self._calculate_hierarchy_depth(hierarchy),
                    'cross_references': len(cross_reference_map),
                    'compliance_tags': len(compliance_mapping)
                }
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create extraction result
            result = ExtractionResult(
                document_id=processed_doc.document_id,
                original_sections=processed_doc.structured_content,
                policy_structure=policy_structure,
                extracted_text=processed_doc.raw_text,
                structured_content=structured_content,
                processing_quality=quality_score,
                extraction_method="Advanced Policy Extraction",
                processing_time=processing_time
            )
            
            # Update statistics
            self.extraction_stats['documents_processed'] += 1
            self.extraction_stats['elements_extracted'] += len(policy_elements)
            self.extraction_stats['cross_references_found'] += len(cross_reference_map)
            self.extraction_stats['avg_processing_time'] = (
                (self.extraction_stats['avg_processing_time'] * (self.extraction_stats['documents_processed'] - 1) + processing_time) /
                self.extraction_stats['documents_processed']
            )
            
            logger.info(f"Text extraction completed in {processing_time:.2f}s. "
                       f"Extracted {len(policy_elements)} elements with quality {quality_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in text extraction: {e}")
            raise
    
    def _extract_policy_elements(self, sections: List[DocumentSection]) -> List[PolicyElement]:
        """Extract policy elements from document sections"""
        elements = []
        element_counter = 0
        
        for section in sections:
            # Analyze section content
            section_elements = self._analyze_section_content(section, element_counter)
            elements.extend(section_elements)
            element_counter += len(section_elements)
        
        return elements
    
    def _analyze_section_content(self, section: DocumentSection, start_counter: int) -> List[PolicyElement]:
        """Analyze individual section content to extract policy elements"""
        elements = []
        
        # Split section into sentences for detailed analysis
        sentences = sent_tokenize(section.content)
        
        # Group sentences into logical elements
        element_groups = self._group_sentences_into_elements(sentences)
        
        for i, (element_type, group_sentences) in enumerate(element_groups):
            element_id = f"elem_{start_counter + i + 1}"
            
            # Combine sentences for element content
            content = ' '.join(group_sentences)
            
            # Extract key information
            keywords = self._extract_keywords(content)
            entities = self._extract_entities(content)
            compliance_tags = self._identify_compliance_tags(content)
            
            # Determine structure level
            structure_level = self._determine_structure_level(section, content)
            
            # Calculate confidence score
            confidence = self._calculate_element_confidence(element_type, content)
            
            element = PolicyElement(
                element_id=element_id,
                element_type=element_type,
                title=self._generate_element_title(element_type, content),
                content=content,
                level=structure_level,
                section_number=self._extract_section_number(section.title),
                page_reference=section.page_number,
                keywords=keywords,
                entities=entities,
                compliance_tags=compliance_tags,
                confidence_score=confidence
            )
            
            elements.append(element)
        
        return elements
    
    def _group_sentences_into_elements(self, sentences: List[str]) -> List[Tuple[PolicyElementType, List[str]]]:
        """Group sentences into logical policy elements"""
        groups = []
        current_type = None
        current_sentences = []
        
        for sentence in sentences:
            # Determine sentence type
            sentence_type = self._classify_sentence_type(sentence)
            
            if sentence_type != current_type and current_sentences:
                # Save previous group
                groups.append((current_type, current_sentences))
                current_sentences = []
            
            current_type = sentence_type
            current_sentences.append(sentence)
        
        # Add final group
        if current_sentences:
            groups.append((current_type, current_sentences))
        
        return groups
    
    def _classify_sentence_type(self, sentence: str) -> PolicyElementType:
        """Classify sentence into policy element type"""
        sentence_lower = sentence.lower()
        
        # Check each pattern type
        for element_type, patterns in self.POLICY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, sentence_lower):
                    return PolicyElementType(element_type)
        
        # Default classification based on content analysis
        if any(word in sentence_lower for word in ['must', 'shall', 'required', 'mandatory']):
            return PolicyElementType.REQUIREMENT
        elif any(word in sentence_lower for word in ['procedure', 'process', 'steps']):
            return PolicyElementType.PROCEDURE
        elif any(word in sentence_lower for word in ['responsible', 'responsibility', 'role']):
            return PolicyElementType.RESPONSIBILITY
        elif any(word in sentence_lower for word in ['means', 'defined as', 'definition']):
            return PolicyElementType.DEFINITION
        else:
            return PolicyElementType.POLICY_STATEMENT
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        if not self.nlp:
            # Fallback: simple keyword extraction
            words = word_tokenize(text.lower())
            keywords = [word for word in words if word.isalpha() and word not in self.stop_words]
            return list(set(keywords))[:10]  # Top 10 unique keywords
        
        # Use spaCy for advanced keyword extraction
        doc = self.nlp(text)
        keywords = []
        
        # Extract important nouns and noun phrases
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and token.text.lower() not in self.stop_words:
                keywords.append(token.lemma_.lower())
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) > 1:  # Multi-word phrases
                keywords.append(chunk.text.lower())
        
        return list(set(keywords))[:15]  # Top 15 unique keywords
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text"""
        entities = []
        
        if self.nlp:
            # Use spaCy NER
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PERSON', 'GPE', 'LAW', 'PRODUCT']:
                    entities.append(f"{ent.text} ({ent.label_})")
        else:
            # Fallback: NLTK NER
            try:
                tokens = word_tokenize(text)
                pos_tags = pos_tag(tokens)
                named_entities = ne_chunk(pos_tags, binary=False)
                
                for subtree in named_entities:
                    if isinstance(subtree, Tree):
                        entity_name = ' '.join([token for token, pos in subtree.leaves()])
                        entities.append(f"{entity_name} ({subtree.label()})")
            except Exception:
                pass
        
        return entities
    
    def _identify_compliance_tags(self, text: str) -> List[str]:
        """Identify compliance framework tags in text"""
        tags = []
        text_lower = text.lower()
        
        for framework, keywords in self.COMPLIANCE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    tags.append(framework)
                    break  # Only add framework once
        
        return tags
    
    def _determine_structure_level(self, section: DocumentSection, content: str) -> StructureLevel:
        """Determine the structural level of the element"""
        # Use section level as base
        section_level = section.level
        
        # Adjust based on content length and type
        if len(content.split()) < 20:
            return StructureLevel.CLAUSE
        elif len(content.split()) < 50:
            return StructureLevel.SUBCLAUSE
        elif section_level == 1:
            return StructureLevel.SECTION
        elif section_level == 2:
            return StructureLevel.SUBSECTION
        else:
            return StructureLevel.PARAGRAPH
    
    def _calculate_element_confidence(self, element_type: PolicyElementType, content: str) -> float:
        """Calculate confidence score for element classification"""
        base_confidence = 0.5
        
        # Pattern matching confidence
        patterns = self.POLICY_PATTERNS.get(element_type.value, [])
        pattern_matches = sum(1 for pattern in patterns if re.search(pattern, content.lower()))
        pattern_confidence = min(0.4, pattern_matches * 0.15)
        
        # Content length confidence
        length_confidence = min(0.2, len(content.split()) / 100)
        
        # Keyword presence confidence
        relevant_keywords = 0
        for keywords in self.COMPLIANCE_KEYWORDS.values():
            relevant_keywords += sum(1 for keyword in keywords if keyword in content.lower())
        keyword_confidence = min(0.3, relevant_keywords * 0.1)
        
        total_confidence = base_confidence + pattern_confidence + length_confidence + keyword_confidence
        return min(1.0, total_confidence)
    
    def _generate_element_title(self, element_type: PolicyElementType, content: str) -> str:
        """Generate a descriptive title for the element"""
        # Extract first meaningful sentence or phrase
        sentences = sent_tokenize(content)
        if sentences:
            first_sentence = sentences[0]
            # Truncate if too long
            if len(first_sentence) > 100:
                words = first_sentence.split()
                title = ' '.join(words[:15]) + "..."
            else:
                title = first_sentence
        else:
            title = f"{element_type.value.replace('_', ' ').title()}"
        
        return title.strip()
    
    def _extract_section_number(self, section_title: str) -> Optional[str]:
        """Extract section number from title"""
        # Try different numbering patterns
        for pattern_name, pattern in self.SECTION_PATTERNS.items():
            if pattern_name in ['numbered', 'alphabetic', 'roman']:
                match = re.match(pattern, section_title.strip())
                if match:
                    return match.group(1)
        return None
    
    def _build_hierarchy(self, elements: List[PolicyElement]) -> Dict[str, List[str]]:
        """Build hierarchical structure of elements"""
        hierarchy = {}
        
        # Group elements by structure level
        level_groups = {}
        for element in elements:
            level = element.level
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(element)
        
        # Build parent-child relationships
        sorted_levels = sorted(level_groups.keys(), key=lambda x: x.value)
        
        for i, level in enumerate(sorted_levels):
            if i == 0:
                # Top level elements have no parent
                for element in level_groups[level]:
                    hierarchy[element.element_id] = []
            else:
                # Find parents for current level elements
                parent_level = sorted_levels[i-1]
                parent_elements = level_groups[parent_level]
                current_elements = level_groups[level]
                
                for element in current_elements:
                    # Find closest parent (could be based on position, section, etc.)
                    parent = self._find_parent_element(element, parent_elements)
                    if parent:
                        element.parent_id = parent.element_id
                        if parent.element_id not in hierarchy:
                            hierarchy[parent.element_id] = []
                        hierarchy[parent.element_id].append(element.element_id)
                        parent.children_ids.append(element.element_id)
        
        return hierarchy
    
    def _find_parent_element(self, element: PolicyElement, parent_candidates: List[PolicyElement]) -> Optional[PolicyElement]:
        """Find the most appropriate parent for an element"""
        if not parent_candidates:
            return None
        
        # Simple heuristic: choose the last parent candidate with the same or related section
        for parent in reversed(parent_candidates):
            if (element.section_number and parent.section_number and 
                element.section_number.startswith(parent.section_number)):
                return parent
        
        # Fallback: choose the last parent candidate
        return parent_candidates[-1]
    
    def _resolve_cross_references(self, elements: List[PolicyElement], full_text: str) -> Dict[str, List[str]]:
        """Resolve cross-references between elements"""
        cross_refs = {}
        
        # Common cross-reference patterns
        ref_patterns = [
            r'(?i)see section (\d+(?:\.\d+)*)',
            r'(?i)refer to (?:section |paragraph |clause )?(\d+(?:\.\d+)*)',
            r'(?i)as (?:defined|specified|described) in (?:section |paragraph )?(\d+(?:\.\d+)*)',
            r'(?i)accordance with (?:section |paragraph )?(\d+(?:\.\d+)*)',
            r'(?i)pursuant to (?:section |paragraph )?(\d+(?:\.\d+)*)',
        ]
        
        for element in elements:
            element_refs = []
            
            # Find references in element content
            for pattern in ref_patterns:
                matches = re.finditer(pattern, element.content)
                for match in matches:
                    ref_section = match.group(1)
                    # Find element with matching section number
                    for target_element in elements:
                        if target_element.section_number == ref_section:
                            element_refs.append(target_element.element_id)
                            break
            
            if element_refs:
                cross_refs[element.element_id] = element_refs
                element.cross_references = element_refs
        
        return cross_refs
    
    def _create_compliance_mapping(self, elements: List[PolicyElement]) -> Dict[str, List[str]]:
        """Create mapping from compliance tags to elements"""
        mapping = {}
        
        for element in elements:
            for tag in element.compliance_tags:
                if tag not in mapping:
                    mapping[tag] = []
                mapping[tag].append(element.element_id)
        
        return mapping
    
    def _generate_structured_content(self, elements: List[PolicyElement], hierarchy: Dict[str, List[str]]) -> str:
        """Generate structured content representation"""
        content_lines = []
        
        # Find root elements (no parent)
        root_elements = [elem for elem in elements if not elem.parent_id]
        
        # Generate hierarchical content
        for root_element in root_elements:
            self._add_element_to_content(root_element, elements, hierarchy, content_lines, 0)
        
        return '\n'.join(content_lines)
    
    def _add_element_to_content(self, element: PolicyElement, all_elements: List[PolicyElement], 
                               hierarchy: Dict[str, List[str]], content_lines: List[str], indent_level: int):
        """Recursively add element and children to structured content"""
        indent = "  " * indent_level
        
        # Add element header
        content_lines.append(f"{indent}[{element.element_type.value.upper()}] {element.title}")
        
        # Add element content (truncated for overview)
        content_preview = element.content[:200] + "..." if len(element.content) > 200 else element.content
        content_lines.append(f"{indent}Content: {content_preview}")
        
        # Add metadata
        if element.compliance_tags:
            content_lines.append(f"{indent}Compliance: {', '.join(element.compliance_tags)}")
        
        content_lines.append("")  # Blank line
        
        # Add children
        child_ids = hierarchy.get(element.element_id, [])
        for child_id in child_ids:
            child_element = next((elem for elem in all_elements if elem.element_id == child_id), None)
            if child_element:
                self._add_element_to_content(child_element, all_elements, hierarchy, content_lines, indent_level + 1)
    
    def _count_element_types(self, elements: List[PolicyElement]) -> Dict[str, int]:
        """Count elements by type"""
        counts = {}
        for element in elements:
            element_type = element.element_type.value
            counts[element_type] = counts.get(element_type, 0) + 1
        return counts
    
    def _calculate_hierarchy_depth(self, hierarchy: Dict[str, List[str]]) -> int:
        """Calculate maximum hierarchy depth"""
        def get_depth(element_id: str, current_depth: int = 0) -> int:
            children = hierarchy.get(element_id, [])
            if not children:
                return current_depth
            return max(get_depth(child_id, current_depth + 1) for child_id in children)
        
        root_elements = [elem_id for elem_id in hierarchy.keys() 
                        if elem_id not in set().union(*hierarchy.values())]
        
        if not root_elements:
            return 0
        
        return max(get_depth(root_id) for root_id in root_elements)
    
    def _calculate_extraction_quality(self, processed_doc: ProcessedDocument, 
                                    elements: List[PolicyElement], 
                                    cross_refs: Dict[str, List[str]]) -> float:
        """Calculate extraction quality score"""
        quality_score = 0.0
        
        # Element extraction quality (40%)
        element_ratio = len(elements) / max(1, len(processed_doc.structured_content))
        element_quality = min(1.0, element_ratio / 2)  # Target ~2 elements per section
        quality_score += element_quality * 0.4
        
        # Content coverage quality (30%)
        total_element_content = sum(len(elem.content) for elem in elements)
        coverage_ratio = total_element_content / max(1, len(processed_doc.raw_text))
        coverage_quality = min(1.0, coverage_ratio)
        quality_score += coverage_quality * 0.3
        
        # Structure quality (20%)
        avg_confidence = sum(elem.confidence_score for elem in elements) / max(1, len(elements))
        quality_score += avg_confidence * 0.2
        
        # Cross-reference quality (10%)
        ref_ratio = len(cross_refs) / max(1, len(elements))
        ref_quality = min(1.0, ref_ratio * 5)  # Reward good cross-referencing
        quality_score += ref_quality * 0.1
        
        return min(1.0, quality_score)
    
    def get_extraction_statistics(self) -> Dict[str, Any]:
        """Get extraction statistics"""
        return self.extraction_stats.copy()


def main():
    """Main function for testing text extractor"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Policy Text Extractor Test")
    parser.add_argument("document_path", help="Path to processed document JSON")
    parser.add_argument("--output", help="Output file for extraction result")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Load processed document
    try:
        with open(args.document_path, 'r') as f:
            doc_data = json.load(f)
        
        # Reconstruct ProcessedDocument (simplified for testing)
        # In practice, this would be passed directly from DocumentProcessor
        print("Note: This test requires integration with DocumentProcessor")
        print("Run document_processor.py first to generate processed document")
        
    except Exception as e:
        print(f"Error loading document: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 