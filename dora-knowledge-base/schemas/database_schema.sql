-- DORA Knowledge Base Database Schema
-- PostgreSQL schema for comprehensive DORA compliance database

-- Create database and schema
CREATE DATABASE IF NOT EXISTS dora_kb;
USE dora_kb;

-- Enable extensions for enhanced functionality
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create enum types for standardized values
CREATE TYPE entity_type AS ENUM (
    'credit_institution',
    'payment_institution', 
    'electronic_money_institution',
    'investment_firm',
    'crypto_asset_service_provider',
    'central_securities_depository',
    'insurance_undertaking',
    'reinsurance_undertaking',
    'central_counterparty',
    'trade_repository'
);

CREATE TYPE tier_classification AS ENUM ('tier_1', 'tier_2', 'exempt');
CREATE TYPE requirement_type AS ENUM ('mandatory', 'optional', 'conditional', 'enhanced');
CREATE TYPE compliance_level AS ENUM ('level_1', 'level_2', 'level_3');
CREATE TYPE pillar_type AS ENUM (
    'governance_arrangements',
    'ict_related_incidents', 
    'digital_operational_resilience_testing',
    'ict_third_party_risk',
    'information_sharing'
);
CREATE TYPE assessment_method AS ENUM ('automated', 'manual', 'hybrid');
CREATE TYPE evidence_type AS ENUM (
    'policy_document',
    'procedure_document',
    'board_resolution',
    'audit_report',
    'test_results',
    'training_records',
    'incident_reports',
    'third_party_contracts'
);
CREATE TYPE risk_level AS ENUM ('minimal', 'low', 'medium', 'high', 'critical');

-- Chapters table
CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chapter_number INTEGER NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sections table  
CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    section_id VARCHAR(50) NOT NULL UNIQUE,
    chapter_id UUID NOT NULL REFERENCES chapters(id),
    section_number INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- DORA Articles table
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id VARCHAR(50) NOT NULL UNIQUE,
    article_number INTEGER NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    chapter_id UUID NOT NULL REFERENCES chapters(id),
    section_id UUID REFERENCES sections(id),
    effective_date DATE NOT NULL DEFAULT '2025-01-17',
    implementation_deadline DATE NOT NULL DEFAULT '2025-01-17',
    pillar pillar_type NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Article paragraphs table for structured content
CREATE TABLE article_paragraphs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paragraph_id VARCHAR(50) NOT NULL UNIQUE,
    article_id UUID NOT NULL REFERENCES articles(id),
    paragraph_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Article cross-references
CREATE TABLE article_cross_references (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_article_id UUID NOT NULL REFERENCES articles(id),
    target_article_id UUID NOT NULL REFERENCES articles(id),
    reference_type VARCHAR(100) DEFAULT 'general',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_article_id, target_article_id)
);

-- Entity type definitions and thresholds
CREATE TABLE entity_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type entity_type NOT NULL UNIQUE,
    tier tier_classification NOT NULL,
    threshold_description TEXT,
    threshold_amount DECIMAL(15,2),
    threshold_currency VARCHAR(3) DEFAULT 'EUR',
    enhanced_requirements BOOLEAN DEFAULT false,
    testing_frequency VARCHAR(50),
    simplified_requirements BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Article applicability by entity type
CREATE TABLE article_applicability (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES articles(id),
    entity_type entity_type NOT NULL,
    tier tier_classification,
    mandatory BOOLEAN DEFAULT true,
    exceptions TEXT,
    additional_conditions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(article_id, entity_type, tier)
);

-- Requirements table
CREATE TABLE requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requirement_id VARCHAR(50) NOT NULL UNIQUE,
    article_id UUID NOT NULL REFERENCES articles(id),
    paragraph_id UUID REFERENCES article_paragraphs(id),
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    pillar pillar_type NOT NULL,
    requirement_type requirement_type NOT NULL DEFAULT 'mandatory',
    compliance_level compliance_level NOT NULL DEFAULT 'level_2',
    implementation_guidance TEXT,
    common_gaps TEXT[],
    remediation_steps TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Evidence requirements for each requirement
CREATE TABLE evidence_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    evidence_type evidence_type NOT NULL,
    description TEXT NOT NULL,
    mandatory BOOLEAN DEFAULT true,
    validation_rules TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Compliance criteria for assessment
CREATE TABLE compliance_criteria (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    criteria_id VARCHAR(50) NOT NULL UNIQUE,
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    criterion TEXT NOT NULL,
    assessment_method assessment_method NOT NULL,
    evidence_type evidence_type NOT NULL,
    weight DECIMAL(3,2) DEFAULT 1.0,
    automation_feasibility VARCHAR(20) DEFAULT 'medium',
    validation_rules TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scoring rubrics
CREATE TABLE scoring_rubrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    score_range VARCHAR(10) NOT NULL, -- e.g., "1-2", "3-4", etc.
    level_name VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    characteristics TEXT[],
    risk_level risk_level NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Maturity levels for criteria
CREATE TABLE maturity_levels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    criteria_id UUID NOT NULL REFERENCES compliance_criteria(id),
    level_name VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    score_range VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Regulatory mappings to other standards
CREATE TABLE regulatory_standards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    standard_name VARCHAR(100) NOT NULL UNIQUE,
    version VARCHAR(50),
    description TEXT,
    alignment_percentage INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE requirement_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    standard_id UUID NOT NULL REFERENCES regulatory_standards(id),
    standard_reference VARCHAR(100) NOT NULL,
    mapping_description TEXT,
    confidence_level VARCHAR(20) DEFAULT 'high',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(requirement_id, standard_id, standard_reference)
);

-- Requirement dependencies
CREATE TABLE requirement_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dependent_requirement_id UUID NOT NULL REFERENCES requirements(id),
    prerequisite_requirement_id UUID NOT NULL REFERENCES requirements(id),
    dependency_type VARCHAR(50) DEFAULT 'prerequisite',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(dependent_requirement_id, prerequisite_requirement_id)
);

-- Technical standards (RTS/ITS)
CREATE TABLE technical_standards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    standard_id VARCHAR(50) NOT NULL UNIQUE,
    standard_type VARCHAR(10) NOT NULL CHECK (standard_type IN ('RTS', 'ITS')),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    effective_date DATE,
    status VARCHAR(50) DEFAULT 'draft',
    document_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Link technical standards to requirements
CREATE TABLE requirement_technical_standards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    technical_standard_id UUID NOT NULL REFERENCES technical_standards(id),
    applicability_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(requirement_id, technical_standard_id)
);

-- Industry benchmarks and best practices
CREATE TABLE industry_benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    benchmark_id VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    entity_type entity_type,
    asset_size_category VARCHAR(50),
    maturity_level VARCHAR(50),
    implementation_cost_estimate DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    timeline_estimate INTEGER, -- in days
    source VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Link benchmarks to requirements  
CREATE TABLE requirement_benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    benchmark_id UUID NOT NULL REFERENCES industry_benchmarks(id),
    relevance_score DECIMAL(3,2) DEFAULT 1.0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(requirement_id, benchmark_id)
);

-- Implementation timeline phases
CREATE TABLE implementation_phases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phase_name VARCHAR(100) NOT NULL UNIQUE,
    effective_date DATE NOT NULL,
    description TEXT,
    entity_scope TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Requirements by implementation phase
CREATE TABLE requirement_phases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    phase_id UUID NOT NULL REFERENCES implementation_phases(id),
    mandatory BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(requirement_id, phase_id)
);

-- Cost estimation data
CREATE TABLE cost_components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_name VARCHAR(100) NOT NULL,
    component_type VARCHAR(50) NOT NULL, -- 'personnel', 'technology', 'consulting', 'training'
    base_cost DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    unit VARCHAR(50), -- 'per_month', 'per_user', 'one_time'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cost estimates by requirement
CREATE TABLE requirement_costs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requirement_id UUID NOT NULL REFERENCES requirements(id),
    cost_component_id UUID NOT NULL REFERENCES cost_components(id),
    entity_type entity_type,
    estimated_cost DECIMAL(15,2),
    effort_days INTEGER,
    confidence_level VARCHAR(20) DEFAULT 'medium',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(requirement_id, cost_component_id, entity_type)
);

-- Search and indexing support
CREATE TABLE search_index (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    object_type VARCHAR(50) NOT NULL, -- 'article', 'requirement', 'criteria'
    object_id UUID NOT NULL,
    content TEXT NOT NULL,
    search_vector tsvector,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit trail for changes
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    change_reason TEXT
);

-- Create indexes for performance
CREATE INDEX idx_articles_pillar ON articles(pillar);
CREATE INDEX idx_articles_chapter ON articles(chapter_id);
CREATE INDEX idx_requirements_article ON requirements(article_id);
CREATE INDEX idx_requirements_pillar ON requirements(pillar);
CREATE INDEX idx_requirements_category ON requirements(category);
CREATE INDEX idx_compliance_criteria_requirement ON compliance_criteria(requirement_id);
CREATE INDEX idx_evidence_requirements_requirement ON evidence_requirements(requirement_id);
CREATE INDEX idx_requirement_mappings_requirement ON requirement_mappings(requirement_id);
CREATE INDEX idx_requirement_mappings_standard ON requirement_mappings(standard_id);
CREATE INDEX idx_search_index_type ON search_index(object_type);
CREATE INDEX idx_search_index_vector ON search_index USING gin(search_vector);
CREATE INDEX idx_audit_log_table_record ON audit_log(table_name, record_id);

-- Create search index trigger function
CREATE OR REPLACE FUNCTION update_search_index()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- Update search index based on table
        IF TG_TABLE_NAME = 'articles' THEN
            INSERT INTO search_index (object_type, object_id, content, search_vector)
            VALUES ('article', NEW.id, NEW.title || ' ' || COALESCE(NEW.description, ''), 
                   to_tsvector('english', NEW.title || ' ' || COALESCE(NEW.description, '')))
            ON CONFLICT (object_type, object_id) DO UPDATE SET
                content = EXCLUDED.content,
                search_vector = EXCLUDED.search_vector,
                updated_at = NOW();
                
        ELSIF TG_TABLE_NAME = 'requirements' THEN
            INSERT INTO search_index (object_type, object_id, content, search_vector)
            VALUES ('requirement', NEW.id, NEW.title || ' ' || NEW.description || ' ' || COALESCE(NEW.implementation_guidance, ''),
                   to_tsvector('english', NEW.title || ' ' || NEW.description || ' ' || COALESCE(NEW.implementation_guidance, '')))
            ON CONFLICT (object_type, object_id) DO UPDATE SET
                content = EXCLUDED.content,
                search_vector = EXCLUDED.search_vector,
                updated_at = NOW();
        END IF;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for search indexing
CREATE TRIGGER articles_search_trigger
    AFTER INSERT OR UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_search_index();

CREATE TRIGGER requirements_search_trigger  
    AFTER INSERT OR UPDATE ON requirements
    FOR EACH ROW EXECUTE FUNCTION update_search_index();

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, record_id, action, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to key tables
CREATE TRIGGER articles_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON articles
    FOR EACH ROW EXECUTE FUNCTION audit_trigger();

CREATE TRIGGER requirements_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON requirements  
    FOR EACH ROW EXECUTE FUNCTION audit_trigger();

CREATE TRIGGER compliance_criteria_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON compliance_criteria
    FOR EACH ROW EXECUTE FUNCTION audit_trigger();

-- Comments for documentation
COMMENT ON DATABASE dora_kb IS 'DORA Compliance Knowledge Base - Comprehensive regulatory requirements database';
COMMENT ON TABLE articles IS 'DORA regulation articles with hierarchical structure';
COMMENT ON TABLE requirements IS 'Structured compliance requirements extracted from DORA articles';
COMMENT ON TABLE compliance_criteria IS 'Assessment criteria for evaluating requirement compliance';
COMMENT ON TABLE scoring_rubrics IS 'Scoring guidelines for compliance assessment (1-10 scale)';
COMMENT ON TABLE regulatory_standards IS 'External regulatory standards for cross-mapping';
COMMENT ON TABLE requirement_mappings IS 'Mappings between DORA requirements and other regulations';
COMMENT ON TABLE industry_benchmarks IS 'Industry best practices and implementation benchmarks'; 