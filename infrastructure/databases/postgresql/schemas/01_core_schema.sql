-- DORA Compliance System - Core Database Schema
-- This schema contains the core tables for the DORA compliance system

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create custom types
CREATE TYPE user_role AS ENUM (
    'SUPER_ADMIN',
    'COMPLIANCE_MANAGER', 
    'AUDITOR',
    'ANALYST',
    'VIEWER'
);

CREATE TYPE organization_status AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'SUSPENDED',
    'PENDING_REVIEW'
);

CREATE TYPE policy_type AS ENUM (
    'ICT_RISK_MANAGEMENT',
    'INCIDENT_MANAGEMENT',
    'OPERATIONAL_RESILIENCE',
    'THIRD_PARTY_RISK',
    'TESTING_FRAMEWORK'
);

CREATE TYPE compliance_status AS ENUM (
    'COMPLIANT',
    'NON_COMPLIANT',
    'PARTIALLY_COMPLIANT',
    'UNDER_REVIEW',
    'NOT_ASSESSED'
);

CREATE TYPE risk_level AS ENUM (
    'VERY_LOW',
    'LOW',
    'MEDIUM',
    'HIGH',
    'VERY_HIGH',
    'CRITICAL'
);

CREATE TYPE report_status AS ENUM (
    'DRAFT',
    'IN_REVIEW',
    'APPROVED',
    'PUBLISHED',
    'ARCHIVED'
);

-- Organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    lei_code VARCHAR(20) UNIQUE, -- Legal Entity Identifier
    jurisdiction VARCHAR(100) NOT NULL,
    business_type VARCHAR(100),
    status organization_status DEFAULT 'ACTIVE',
    dora_classification VARCHAR(50), -- Significant/Other ICT third-party service provider
    parent_organization_id UUID REFERENCES organizations(id),
    
    -- Contact information
    primary_contact_name VARCHAR(255),
    primary_contact_email VARCHAR(255),
    primary_contact_phone VARCHAR(50),
    
    -- Address information
    headquarters_address TEXT,
    headquarters_country VARCHAR(100),
    headquarters_city VARCHAR(100),
    
    -- Compliance metadata
    dora_effective_date DATE,
    first_assessment_date DATE,
    last_assessment_date DATE,
    next_assessment_due DATE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1,
    
    CONSTRAINT organizations_name_check CHECK (length(name) >= 2),
    CONSTRAINT organizations_lei_check CHECK (lei_code IS NULL OR length(lei_code) = 20)
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role user_role NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    
    -- Account status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    must_change_password BOOLEAN DEFAULT TRUE,
    
    -- Security
    failed_login_attempts INTEGER DEFAULT 0,
    last_login_at TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Two-factor authentication
    totp_secret VARCHAR(255),
    totp_enabled BOOLEAN DEFAULT FALSE,
    backup_codes TEXT[], -- Encrypted backup codes
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,
    
    CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$'),
    CONSTRAINT users_username_check CHECK (length(username) >= 3)
);

-- User sessions table
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Session metadata
    login_method VARCHAR(50), -- password, sso, api_key
    is_active BOOLEAN DEFAULT TRUE,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Policy frameworks table
CREATE TABLE policy_frameworks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type policy_type NOT NULL,
    version VARCHAR(50),
    effective_date DATE,
    
    -- Framework metadata
    issuing_authority VARCHAR(255),
    legal_basis TEXT,
    scope_description TEXT,
    
    -- Status and lifecycle
    is_active BOOLEAN DEFAULT TRUE,
    superseded_by_id UUID REFERENCES policy_frameworks(id),
    
    -- Document references
    official_document_url TEXT,
    guidance_document_url TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Policy requirements table
CREATE TABLE policy_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    framework_id UUID NOT NULL REFERENCES policy_frameworks(id),
    requirement_number VARCHAR(50),
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    
    -- Requirement hierarchy
    parent_requirement_id UUID REFERENCES policy_requirements(id),
    level INTEGER DEFAULT 1, -- Depth in hierarchy
    order_index INTEGER, -- Ordering within same level
    
    -- Classification
    mandatory BOOLEAN DEFAULT TRUE,
    risk_category VARCHAR(100),
    applicable_entity_types TEXT[], -- Array of entity types this applies to
    
    -- Implementation details
    implementation_guidance TEXT,
    suggested_controls TEXT,
    evidence_requirements TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    
    CONSTRAINT policy_requirements_level_check CHECK (level > 0 AND level <= 10)
);

-- Compliance assessments table
CREATE TABLE compliance_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    framework_id UUID NOT NULL REFERENCES policy_frameworks(id),
    
    -- Assessment metadata
    assessment_name VARCHAR(255) NOT NULL,
    assessment_type VARCHAR(100), -- initial, annual, ad_hoc, remediation
    assessment_period_start DATE,
    assessment_period_end DATE,
    
    -- Status and progress
    status compliance_status DEFAULT 'NOT_ASSESSED',
    overall_score DECIMAL(5,2), -- Percentage score
    risk_rating risk_level,
    
    -- Assessment team
    lead_assessor_id UUID REFERENCES users(id),
    assessment_team_ids UUID[], -- Array of user IDs
    
    -- Timeline
    initiated_date DATE,
    fieldwork_start_date DATE,
    fieldwork_end_date DATE,
    draft_report_date DATE,
    final_report_date DATE,
    
    -- Review and approval
    reviewed_by_id UUID REFERENCES users(id),
    approved_by_id UUID REFERENCES users(id),
    review_comments TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    version INTEGER DEFAULT 1,
    
    CONSTRAINT compliance_assessments_score_check CHECK (overall_score >= 0 AND overall_score <= 100),
    CONSTRAINT compliance_assessments_period_check CHECK (assessment_period_start <= assessment_period_end)
);

-- Requirement assessments table (junction table with assessment details)
CREATE TABLE requirement_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES compliance_assessments(id) ON DELETE CASCADE,
    requirement_id UUID NOT NULL REFERENCES policy_requirements(id),
    
    -- Assessment results
    compliance_status compliance_status DEFAULT 'NOT_ASSESSED',
    score DECIMAL(5,2), -- Individual requirement score
    
    -- Evidence and findings
    evidence_description TEXT,
    evidence_file_paths TEXT[], -- Array of file paths
    findings TEXT,
    recommendations TEXT,
    
    -- Risk assessment
    inherent_risk risk_level,
    residual_risk risk_level,
    risk_mitigation_plan TEXT,
    
    -- Remediation
    requires_remediation BOOLEAN DEFAULT FALSE,
    remediation_priority risk_level,
    remediation_due_date DATE,
    remediation_owner_id UUID REFERENCES users(id),
    remediation_status VARCHAR(50),
    remediation_notes TEXT,
    
    -- Testing details
    testing_method VARCHAR(100), -- document_review, interview, observation, testing
    testing_date DATE,
    tested_by_id UUID REFERENCES users(id),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assessed_by_id UUID REFERENCES users(id),
    
    CONSTRAINT requirement_assessments_score_check CHECK (score >= 0 AND score <= 100),
    UNIQUE(assessment_id, requirement_id)
);

-- Compliance reports table
CREATE TABLE compliance_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES compliance_assessments(id),
    
    -- Report metadata
    report_name VARCHAR(255) NOT NULL,
    report_type VARCHAR(100), -- assessment, remediation, monitoring, incident
    status report_status DEFAULT 'DRAFT',
    
    -- Report content
    executive_summary TEXT,
    methodology TEXT,
    scope_and_limitations TEXT,
    key_findings TEXT,
    recommendations TEXT,
    conclusion TEXT,
    
    -- Report structure
    table_of_contents JSONB,
    appendices JSONB,
    
    -- File management
    report_file_path TEXT,
    report_file_size BIGINT,
    report_file_hash VARCHAR(64), -- SHA-256 hash
    
    -- Distribution
    distribution_list UUID[], -- Array of user IDs
    external_distribution TEXT[], -- External email addresses
    confidentiality_level VARCHAR(50), -- public, internal, confidential, restricted
    
    -- Version control
    version VARCHAR(50) DEFAULT '1.0',
    previous_version_id UUID REFERENCES compliance_reports(id),
    change_summary TEXT,
    
    -- Approval workflow
    submitted_by_id UUID REFERENCES users(id),
    submitted_at TIMESTAMP WITH TIME ZONE,
    reviewed_by_id UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    approved_by_id UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    
    CONSTRAINT compliance_reports_file_size_check CHECK (report_file_size >= 0)
);

-- Risk assessments table
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    -- Risk identification
    risk_title VARCHAR(255) NOT NULL,
    risk_description TEXT NOT NULL,
    risk_category VARCHAR(100), -- operational, cyber, third_party, etc.
    risk_source VARCHAR(100), -- internal, external, third_party
    
    -- Risk assessment
    likelihood risk_level,
    impact risk_level,
    inherent_risk_rating risk_level,
    
    -- Risk response
    risk_response_strategy VARCHAR(100), -- accept, mitigate, transfer, avoid
    mitigation_controls TEXT,
    residual_risk_rating risk_level,
    
    -- Risk ownership
    risk_owner_id UUID REFERENCES users(id),
    risk_manager_id UUID REFERENCES users(id),
    
    -- Monitoring
    monitoring_frequency VARCHAR(50), -- daily, weekly, monthly, quarterly, annually
    last_review_date DATE,
    next_review_date DATE,
    
    -- Status
    status VARCHAR(50) DEFAULT 'ACTIVE', -- active, closed, transferred
    closure_reason TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    version INTEGER DEFAULT 1
);

-- Audit logs table for compliance tracking
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Event identification
    event_type VARCHAR(100) NOT NULL, -- login, data_access, report_generation, etc.
    event_category VARCHAR(50), -- authentication, data, system, compliance
    
    -- User and session
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES user_sessions(id),
    
    -- Request details
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_url TEXT,
    
    -- Resource accessed
    resource_type VARCHAR(100), -- table, report, document, system
    resource_id UUID,
    resource_name VARCHAR(255),
    
    -- Event details
    action VARCHAR(100), -- CREATE, READ, UPDATE, DELETE, EXPORT, etc.
    event_description TEXT,
    additional_data JSONB,
    
    -- Result
    success BOOLEAN,
    error_message TEXT,
    response_code INTEGER,
    
    -- Timing
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER,
    
    -- Data sensitivity
    contains_pii BOOLEAN DEFAULT FALSE,
    data_classification VARCHAR(50), -- public, internal, confidential, restricted
    
    CONSTRAINT audit_logs_duration_check CHECK (duration_ms >= 0)
);

-- Create indexes for performance
CREATE INDEX idx_organizations_status ON organizations(status);
CREATE INDEX idx_organizations_jurisdiction ON organizations(jurisdiction);
CREATE INDEX idx_organizations_parent ON organizations(parent_organization_id);

CREATE INDEX idx_users_organization ON users(organization_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;

CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active) WHERE is_active = TRUE;

CREATE INDEX idx_policy_requirements_framework ON policy_requirements(framework_id);
CREATE INDEX idx_policy_requirements_parent ON policy_requirements(parent_requirement_id);
CREATE INDEX idx_policy_requirements_level ON policy_requirements(level);

CREATE INDEX idx_compliance_assessments_org ON compliance_assessments(organization_id);
CREATE INDEX idx_compliance_assessments_framework ON compliance_assessments(framework_id);
CREATE INDEX idx_compliance_assessments_status ON compliance_assessments(status);
CREATE INDEX idx_compliance_assessments_dates ON compliance_assessments(assessment_period_start, assessment_period_end);

CREATE INDEX idx_requirement_assessments_assessment ON requirement_assessments(assessment_id);
CREATE INDEX idx_requirement_assessments_requirement ON requirement_assessments(requirement_id);
CREATE INDEX idx_requirement_assessments_status ON requirement_assessments(compliance_status);
CREATE INDEX idx_requirement_assessments_remediation ON requirement_assessments(requires_remediation) WHERE requires_remediation = TRUE;

CREATE INDEX idx_compliance_reports_assessment ON compliance_reports(assessment_id);
CREATE INDEX idx_compliance_reports_status ON compliance_reports(status);
CREATE INDEX idx_compliance_reports_type ON compliance_reports(report_type);

CREATE INDEX idx_risk_assessments_org ON risk_assessments(organization_id);
CREATE INDEX idx_risk_assessments_owner ON risk_assessments(risk_owner_id);
CREATE INDEX idx_risk_assessments_status ON risk_assessments(status);
CREATE INDEX idx_risk_assessments_rating ON risk_assessments(inherent_risk_rating);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(event_timestamp);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_success ON audit_logs(success);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_policy_frameworks_updated_at BEFORE UPDATE ON policy_frameworks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_policy_requirements_updated_at BEFORE UPDATE ON policy_requirements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_compliance_assessments_updated_at BEFORE UPDATE ON compliance_assessments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_requirement_assessments_updated_at BEFORE UPDATE ON requirement_assessments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_compliance_reports_updated_at BEFORE UPDATE ON compliance_reports FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_risk_assessments_updated_at BEFORE UPDATE ON risk_assessments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row-level security policies
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE compliance_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE requirement_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE compliance_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Grant permissions to application role
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO dora_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO dora_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO dora_app; 