#!/usr/bin/env python3
"""
Penalty Models and Calculation Utilities

Advanced penalty calculation models that extend the basic DORA penalty engine
with risk-adjusted calculations, scenario modeling, and integration with 
compliance gap analysis.

Author: DORA Compliance System
Date: 2025-01-23
"""

import math
import statistics
from typing import Dict, List, Optional, Union, Tuple
from decimal import Decimal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .dora_penalties import (
    DORAfinePenalties, ViolationType, SeverityLevel, 
    get_violation_descriptions
)


class RiskProfile(Enum):
    """Risk profile classifications for penalty modeling"""
    LOW_RISK = "low_risk"          # Strong compliance history, proactive measures
    MEDIUM_RISK = "medium_risk"    # Average compliance, reactive measures  
    HIGH_RISK = "high_risk"        # Poor compliance history, minimal measures
    CRITICAL_RISK = "critical_risk"  # Known violations, regulatory attention


class CompanySize(Enum):
    """Company size classifications affecting penalty calculations"""
    SMALL = "small"           # <€50M revenue
    MEDIUM = "medium"         # €50M-€500M revenue  
    LARGE = "large"           # €500M-€5B revenue
    SYSTEMIC = "systemic"     # >€5B revenue or systemically important


@dataclass
class RiskFactors:
    """Risk factors that influence penalty probability and severity"""
    
    # Compliance history factors (0.0 to 1.0 scale)
    compliance_history_score: float = 0.5      # Historical compliance performance
    incident_frequency: float = 0.3            # Frequency of past incidents
    regulatory_attention: float = 0.2          # Level of regulatory scrutiny
    
    # Operational factors
    system_complexity: float = 0.5             # Complexity of ICT systems
    third_party_dependencies: float = 0.4      # Level of third-party dependencies
    digital_transformation_pace: float = 0.3   # Speed of digital changes
    
    # Governance factors  
    board_oversight: float = 0.7               # Quality of board oversight
    risk_management_maturity: float = 0.5      # Maturity of risk management
    compliance_resources: float = 0.6          # Adequacy of compliance resources
    
    # External factors
    threat_landscape: float = 0.4              # Current threat environment
    regulatory_focus: float = 0.5              # Regulatory enforcement focus
    industry_peer_performance: float = 0.5     # Performance vs industry peers


@dataclass
class PenaltyScenario:
    """A specific penalty scenario with associated calculations"""
    
    scenario_name: str
    probability: float                          # Probability of occurrence (0.0-1.0)
    violations: List[Dict[str, any]]           # List of violation details
    annual_revenue: Decimal
    risk_factors: RiskFactors
    timeline_months: int = 12                  # Timeline for scenario realization
    
    # Calculated fields
    penalty_calculation: Optional[Dict] = field(default=None, init=False)
    expected_value: Optional[Decimal] = field(default=None, init=False)
    risk_adjusted_penalty: Optional[Decimal] = field(default=None, init=False)


class PenaltyCalculationEngine:
    """Advanced penalty calculation engine with risk modeling"""
    
    # Risk multipliers by company size
    SIZE_RISK_MULTIPLIERS = {
        CompanySize.SMALL: 0.7,      # Lower penalties but less resources
        CompanySize.MEDIUM: 1.0,     # Standard penalties
        CompanySize.LARGE: 1.3,      # Higher penalties, more scrutiny
        CompanySize.SYSTEMIC: 1.8    # Highest penalties, systemic importance
    }
    
    # Risk profile penalty multipliers  
    RISK_PROFILE_MULTIPLIERS = {
        RiskProfile.LOW_RISK: 0.6,
        RiskProfile.MEDIUM_RISK: 1.0,
        RiskProfile.HIGH_RISK: 1.5,
        RiskProfile.CRITICAL_RISK: 2.2
    }
    
    @classmethod
    def calculate_risk_adjusted_penalty(
        cls,
        violations: List[Dict[str, any]],
        annual_revenue: Decimal,
        risk_factors: RiskFactors,
        company_size: CompanySize,
        risk_profile: RiskProfile
    ) -> Dict[str, Union[Decimal, float, str, List]]:
        """
        Calculate risk-adjusted penalty considering company profile and risk factors
        
        Args:
            violations: List of violation scenarios
            annual_revenue: Company annual revenue
            risk_factors: Detailed risk factor assessment
            company_size: Company size classification
            risk_profile: Overall risk profile
            
        Returns:
            Comprehensive penalty analysis with risk adjustments
        """
        
        # Calculate base penalty using DORA engine
        base_calculation = DORAfinePenalties.calculate_cumulative_penalties(
            violations, annual_revenue
        )
        
        # Calculate risk multiplier based on factors
        risk_multiplier = cls._calculate_risk_multiplier(risk_factors)
        
        # Apply company size and risk profile adjustments
        size_multiplier = cls.SIZE_RISK_MULTIPLIERS[company_size]
        profile_multiplier = cls.RISK_PROFILE_MULTIPLIERS[risk_profile]
        
        # Calculate final adjustments
        total_multiplier = risk_multiplier * size_multiplier * profile_multiplier
        
        # Apply adjustments to base penalty
        adjusted_penalty = base_calculation['final_cumulative_penalty_eur'] * Decimal(str(total_multiplier))
        
        # Ensure we don't exceed the 2% revenue cap
        max_penalty = annual_revenue * Decimal('0.02')
        final_penalty = min(adjusted_penalty, max_penalty)
        
        return {
            "base_penalty_eur": base_calculation['final_cumulative_penalty_eur'],
            "risk_multiplier": risk_multiplier,
            "size_multiplier": size_multiplier,
            "profile_multiplier": profile_multiplier,
            "total_multiplier": total_multiplier,
            "adjusted_penalty_eur": adjusted_penalty,
            "final_penalty_eur": final_penalty,
            "penalty_as_revenue_percentage": float((final_penalty / annual_revenue) * 100),
            "cap_applied": final_penalty < adjusted_penalty,
            "risk_factors_summary": cls._summarize_risk_factors(risk_factors),
            "company_profile": {
                "size": company_size.value,
                "risk_profile": risk_profile.value
            },
            "base_calculation": base_calculation
        }
    
    @classmethod
    def _calculate_risk_multiplier(cls, risk_factors: RiskFactors) -> float:
        """Calculate composite risk multiplier from individual risk factors"""
        
        # Weight different risk categories
        compliance_weight = 0.4
        operational_weight = 0.3
        governance_weight = 0.2
        external_weight = 0.1
        
        # Calculate category scores (higher score = higher risk)
        compliance_risk = (
            (1 - risk_factors.compliance_history_score) * 0.5 +
            risk_factors.incident_frequency * 0.3 +
            risk_factors.regulatory_attention * 0.2
        )
        
        operational_risk = (
            risk_factors.system_complexity * 0.4 +
            risk_factors.third_party_dependencies * 0.3 +
            risk_factors.digital_transformation_pace * 0.3
        )
        
        governance_risk = (
            (1 - risk_factors.board_oversight) * 0.4 +
            (1 - risk_factors.risk_management_maturity) * 0.3 +
            (1 - risk_factors.compliance_resources) * 0.3
        )
        
        external_risk = (
            risk_factors.threat_landscape * 0.4 +
            risk_factors.regulatory_focus * 0.3 +
            (1 - risk_factors.industry_peer_performance) * 0.3
        )
        
        # Calculate weighted average
        composite_risk = (
            compliance_risk * compliance_weight +
            operational_risk * operational_weight +
            governance_risk * governance_weight +
            external_risk * external_weight
        )
        
        # Convert to multiplier (range approximately 0.5 to 2.0)
        risk_multiplier = 0.5 + (composite_risk * 1.5)
        
        return round(risk_multiplier, 3)
    
    @classmethod
    def _summarize_risk_factors(cls, risk_factors: RiskFactors) -> Dict[str, float]:
        """Summarize risk factors into categories"""
        return {
            "compliance_history": risk_factors.compliance_history_score,
            "operational_complexity": (
                risk_factors.system_complexity + 
                risk_factors.third_party_dependencies + 
                risk_factors.digital_transformation_pace
            ) / 3,
            "governance_strength": (
                risk_factors.board_oversight + 
                risk_factors.risk_management_maturity + 
                risk_factors.compliance_resources
            ) / 3,
            "external_environment": (
                risk_factors.threat_landscape + 
                risk_factors.regulatory_focus
            ) / 2
        }
    
    @classmethod
    def model_penalty_scenarios(
        cls,
        scenarios: List[PenaltyScenario]
    ) -> Dict[str, Union[Decimal, float, List]]:
        """
        Model multiple penalty scenarios and calculate expected values
        
        Args:
            scenarios: List of penalty scenarios with probabilities
            
        Returns:
            Scenario analysis with expected values and risk metrics
        """
        
        scenario_results = []
        total_expected_value = Decimal('0')
        weighted_penalties = []
        
        for scenario in scenarios:
            # Calculate penalty for this scenario
            penalty_calc = cls.calculate_risk_adjusted_penalty(
                violations=scenario.violations,
                annual_revenue=scenario.annual_revenue,
                risk_factors=scenario.risk_factors,
                company_size=cls._determine_company_size(scenario.annual_revenue),
                risk_profile=cls._determine_risk_profile(scenario.risk_factors)
            )
            
            # Calculate expected value
            expected_value = penalty_calc['final_penalty_eur'] * Decimal(str(scenario.probability))
            total_expected_value += expected_value
            
            # Store results
            scenario_result = {
                "scenario_name": scenario.scenario_name,
                "probability": scenario.probability,
                "penalty_eur": penalty_calc['final_penalty_eur'],
                "expected_value_eur": expected_value,
                "penalty_calculation": penalty_calc
            }
            scenario_results.append(scenario_result)
            weighted_penalties.append(float(penalty_calc['final_penalty_eur']) * scenario.probability)
        
        # Calculate risk metrics
        penalties = [float(s['penalty_eur']) for s in scenario_results]
        probabilities = [s['probability'] for s in scenario_results]
        
        return {
            "scenarios": scenario_results,
            "expected_total_penalty_eur": total_expected_value,
            "worst_case_penalty_eur": max(penalties) if penalties else 0,
            "best_case_penalty_eur": min(penalties) if penalties else 0,
            "penalty_variance": statistics.variance(weighted_penalties) if len(weighted_penalties) > 1 else 0,
            "penalty_std_deviation": statistics.stdev(weighted_penalties) if len(weighted_penalties) > 1 else 0,
            "value_at_risk_95": cls._calculate_value_at_risk(scenario_results, 0.95),
            "summary_statistics": {
                "num_scenarios": len(scenarios),
                "total_probability": sum(probabilities),
                "average_penalty": statistics.mean(penalties) if penalties else 0,
                "median_penalty": statistics.median(penalties) if penalties else 0
            }
        }
    
    @classmethod
    def _determine_company_size(cls, annual_revenue: Decimal) -> CompanySize:
        """Determine company size based on annual revenue"""
        revenue_millions = float(annual_revenue) / 1_000_000
        
        if revenue_millions < 50:
            return CompanySize.SMALL
        elif revenue_millions < 500:
            return CompanySize.MEDIUM
        elif revenue_millions < 5000:
            return CompanySize.LARGE
        else:
            return CompanySize.SYSTEMIC
    
    @classmethod
    def _determine_risk_profile(cls, risk_factors: RiskFactors) -> RiskProfile:
        """Determine risk profile based on risk factors"""
        risk_score = cls._calculate_risk_multiplier(risk_factors)
        
        if risk_score < 0.8:
            return RiskProfile.LOW_RISK
        elif risk_score < 1.2:
            return RiskProfile.MEDIUM_RISK
        elif risk_score < 1.6:
            return RiskProfile.HIGH_RISK
        else:
            return RiskProfile.CRITICAL_RISK
    
    @classmethod
    def _calculate_value_at_risk(cls, scenario_results: List[Dict], confidence_level: float) -> float:
        """Calculate Value at Risk at specified confidence level"""
        if not scenario_results:
            return 0.0
        
        # Sort scenarios by penalty amount
        sorted_scenarios = sorted(scenario_results, key=lambda x: x['penalty_eur'])
        
        # Calculate cumulative probabilities
        cumulative_prob = 0.0
        for scenario in sorted_scenarios:
            cumulative_prob += scenario['probability']
            if cumulative_prob >= confidence_level:
                return float(scenario['penalty_eur'])
        
        # If we don't reach the confidence level, return the highest penalty
        return float(sorted_scenarios[-1]['penalty_eur'])


def create_default_risk_factors(
    compliance_maturity: str = "medium",
    operational_complexity: str = "medium",
    regulatory_scrutiny: str = "medium"
) -> RiskFactors:
    """
    Create default risk factors based on high-level assessments
    
    Args:
        compliance_maturity: "low", "medium", "high"
        operational_complexity: "low", "medium", "high"  
        regulatory_scrutiny: "low", "medium", "high"
        
    Returns:
        RiskFactors object with appropriate defaults
    """
    
    # Map text descriptions to numerical values
    level_map = {"low": 0.3, "medium": 0.5, "high": 0.7}
    
    compliance_score = level_map.get(compliance_maturity, 0.5)
    complexity_score = level_map.get(operational_complexity, 0.5)
    scrutiny_score = level_map.get(regulatory_scrutiny, 0.5)
    
    return RiskFactors(
        compliance_history_score=compliance_score,
        incident_frequency=1.0 - compliance_score,  # Inverse relationship
        regulatory_attention=scrutiny_score,
        system_complexity=complexity_score,
        third_party_dependencies=complexity_score,
        digital_transformation_pace=complexity_score * 0.8,
        board_oversight=compliance_score,
        risk_management_maturity=compliance_score,
        compliance_resources=compliance_score,
        threat_landscape=0.5,  # External factor, moderate default
        regulatory_focus=scrutiny_score,
        industry_peer_performance=compliance_score
    )


if __name__ == "__main__":
    # Example usage
    revenue = Decimal('500_000_000')  # €500M annual revenue
    
    # Create risk factors
    risk_factors = create_default_risk_factors(
        compliance_maturity="medium",
        operational_complexity="high",
        regulatory_scrutiny="high"
    )
    
    # Define violations
    violations = [
        {"type": "testing_programme_missing", "severity": "critical"},
        {"type": "incident_reporting_violation", "severity": "moderate"},
    ]
    
    # Calculate risk-adjusted penalty
    result = PenaltyCalculationEngine.calculate_risk_adjusted_penalty(
        violations=violations,
        annual_revenue=revenue,
        risk_factors=risk_factors,
        company_size=CompanySize.LARGE,
        risk_profile=RiskProfile.HIGH_RISK
    )
    
    print("Risk-Adjusted Penalty Calculation:")
    print(f"Base Penalty: €{result['base_penalty_eur']:,.2f}")
    print(f"Risk Multiplier: {result['risk_multiplier']:.2f}")
    print(f"Final Penalty: €{result['final_penalty_eur']:,.2f}")
    print(f"As % of Revenue: {result['penalty_as_revenue_percentage']:.3f}%") 