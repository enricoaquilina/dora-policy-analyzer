"""
DORA Compliance System - Source Package

This package contains all the core modules for the DORA compliance system:
- dora_penalties: Official DORA penalty calculation engine
- penalty_models: Advanced risk modeling and scenario analysis  
- financial_data: Financial data integration and ROI calculations
- cost_estimation_framework: Advanced cost estimation with templates and vendor quotes
- risk_calculator_agent: Main risk calculator agent
- gap_assessment_agent: Gap assessment and analysis
- rts_its_integration: Technical standards integration

Author: DORA Compliance System
Date: 2025-01-23
"""

# Import main components for easy access
from .risk_calculator_agent import calculate_financial_impact
from .dora_penalties import DORAfinePenalties, ViolationType, SeverityLevel
from .penalty_models import PenaltyCalculationEngine, RiskFactors, CompanySize
from .financial_data import FinancialProfile, FinancialDataManager, create_demo_financial_profile
from .cost_estimation_framework import (
    AdvancedCostEstimator, ImplementationType, ProjectComplexity, CostCategory,
    CostComponent, CostTemplate, VendorQuote, HistoricalCostRecord,
    create_demo_cost_estimator
)

# Version info
__version__ = "1.2.0"
__author__ = "DORA Compliance System"

# Package metadata
__all__ = [
    # Risk Calculator Agent
    "calculate_financial_impact",
    
    # DORA Penalties
    "DORAfinePenalties", 
    "ViolationType", 
    "SeverityLevel",
    
    # Penalty Models
    "PenaltyCalculationEngine", 
    "RiskFactors", 
    "CompanySize",
    
    # Financial Data
    "FinancialProfile", 
    "FinancialDataManager", 
    "create_demo_financial_profile",
    
    # Cost Estimation Framework
    "AdvancedCostEstimator",
    "ImplementationType",
    "ProjectComplexity", 
    "CostCategory",
    "CostComponent",
    "CostTemplate",
    "VendorQuote",
    "HistoricalCostRecord",
    "create_demo_cost_estimator"
] 