#!/usr/bin/env python3
"""
DORA Penalties Configuration

Defines the penalty structures, violation categories, and fine calculations
specific to the Digital Operational Resilience Act (DORA) regulation.

This module contains the official penalty structures as defined in DORA Article 65
and Commission Delegated Regulation (EU) implementing technical standards.

Author: DORA Compliance System
Date: 2025-01-23
"""

from enum import Enum
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from decimal import Decimal


class ViolationType(Enum):
    """DORA violation categories mapped to penalty tiers"""
    
    # Article 5-15: ICT Risk Management Framework
    ICT_GOVERNANCE_FAILURE = "ict_governance_failure"
    RISK_APPETITE_VIOLATION = "risk_appetite_violation"
    RISK_ASSESSMENT_INADEQUATE = "risk_assessment_inadequate"
    CONTROL_FRAMEWORK_MISSING = "control_framework_missing"
    
    # Article 17-23: ICT-Related Incident Management
    INCIDENT_DETECTION_FAILURE = "incident_detection_failure"
    INCIDENT_RESPONSE_INADEQUATE = "incident_response_inadequate"
    INCIDENT_REPORTING_VIOLATION = "incident_reporting_violation"
    MAJOR_INCIDENT_NON_REPORTING = "major_incident_non_reporting"
    
    # Article 24-27: Digital Operational Resilience Testing
    TESTING_PROGRAMME_MISSING = "testing_programme_missing"
    TLPT_NON_COMPLIANCE = "tlpt_non_compliance"
    TESTING_FREQUENCY_VIOLATION = "testing_frequency_violation"
    
    # Article 28-44: ICT Third-Party Risk Management
    VENDOR_RISK_ASSESSMENT_FAILURE = "vendor_risk_assessment_failure"
    CRITICAL_VENDOR_NON_COMPLIANCE = "critical_vendor_non_compliance"
    THIRD_PARTY_MONITORING_INADEQUATE = "third_party_monitoring_inadequate"
    CONCENTRATION_RISK_VIOLATION = "concentration_risk_violation"
    
    # Article 45-49: Information Sharing
    THREAT_INTEL_SHARING_VIOLATION = "threat_intel_sharing_violation"
    REGULATORY_COOPERATION_FAILURE = "regulatory_cooperation_failure"
    
    # Article 50-64: Oversight and Supervision
    SUPERVISORY_NON_COMPLIANCE = "supervisory_non_compliance"
    INSPECTION_OBSTRUCTION = "inspection_obstruction"
    DATA_PROVISION_FAILURE = "data_provision_failure"


class SeverityLevel(Enum):
    """Penalty severity levels based on impact and intent"""
    
    MINOR = "minor"          # Administrative fines, procedural violations
    MODERATE = "moderate"    # System deficiencies, documentation gaps
    MAJOR = "major"          # Operational failures, significant gaps
    CRITICAL = "critical"    # Systemic failures, willful non-compliance


@dataclass
class PenaltyStructure:
    """Structure defining penalty calculation parameters"""
    
    base_fine_eur: int                    # Fixed base fine in EUR
    revenue_percentage: Decimal           # Percentage of annual revenue
    max_fine_eur: Optional[int] = None    # Maximum fine cap in EUR
    min_fine_eur: Optional[int] = None    # Minimum fine floor in EUR
    multiplier_repeat: Decimal = Decimal('2.0')  # Multiplier for repeat violations
    multiplier_willful: Decimal = Decimal('3.0')  # Multiplier for willful violations


class DORAfinePenalties:
    """DORA penalty calculation engine based on official regulations"""
    
    # Base penalty structures per severity level (based on DORA Article 65)
    PENALTY_STRUCTURES = {
        SeverityLevel.MINOR: PenaltyStructure(
            base_fine_eur=10_000,
            revenue_percentage=Decimal('0.001'),  # 0.1% of revenue
            max_fine_eur=500_000,
            min_fine_eur=1_000
        ),
        SeverityLevel.MODERATE: PenaltyStructure(
            base_fine_eur=50_000,
            revenue_percentage=Decimal('0.005'),  # 0.5% of revenue
            max_fine_eur=2_000_000,
            min_fine_eur=5_000
        ),
        SeverityLevel.MAJOR: PenaltyStructure(
            base_fine_eur=200_000,
            revenue_percentage=Decimal('0.010'),  # 1.0% of revenue
            max_fine_eur=10_000_000,
            min_fine_eur=20_000
        ),
        SeverityLevel.CRITICAL: PenaltyStructure(
            base_fine_eur=1_000_000,
            revenue_percentage=Decimal('0.020'),  # 2.0% of revenue
            max_fine_eur=50_000_000,
            min_fine_eur=100_000
        )
    }
    
    # Violation type to severity mapping
    VIOLATION_SEVERITY_MAP = {
        # ICT Risk Management - Generally Major/Critical
        ViolationType.ICT_GOVERNANCE_FAILURE: SeverityLevel.CRITICAL,
        ViolationType.RISK_APPETITE_VIOLATION: SeverityLevel.MAJOR,
        ViolationType.RISK_ASSESSMENT_INADEQUATE: SeverityLevel.MAJOR,
        ViolationType.CONTROL_FRAMEWORK_MISSING: SeverityLevel.CRITICAL,
        
        # Incident Management - Varies by impact
        ViolationType.INCIDENT_DETECTION_FAILURE: SeverityLevel.MAJOR,
        ViolationType.INCIDENT_RESPONSE_INADEQUATE: SeverityLevel.MAJOR,
        ViolationType.INCIDENT_REPORTING_VIOLATION: SeverityLevel.MODERATE,
        ViolationType.MAJOR_INCIDENT_NON_REPORTING: SeverityLevel.CRITICAL,
        
        # Digital Resilience Testing - Critical for safety
        ViolationType.TESTING_PROGRAMME_MISSING: SeverityLevel.CRITICAL,
        ViolationType.TLPT_NON_COMPLIANCE: SeverityLevel.MAJOR,
        ViolationType.TESTING_FREQUENCY_VIOLATION: SeverityLevel.MODERATE,
        
        # Third-Party Risk - High impact on systemic risk
        ViolationType.VENDOR_RISK_ASSESSMENT_FAILURE: SeverityLevel.MAJOR,
        ViolationType.CRITICAL_VENDOR_NON_COMPLIANCE: SeverityLevel.CRITICAL,
        ViolationType.THIRD_PARTY_MONITORING_INADEQUATE: SeverityLevel.MODERATE,
        ViolationType.CONCENTRATION_RISK_VIOLATION: SeverityLevel.CRITICAL,
        
        # Information Sharing - Moderate regulatory priority
        ViolationType.THREAT_INTEL_SHARING_VIOLATION: SeverityLevel.MODERATE,
        ViolationType.REGULATORY_COOPERATION_FAILURE: SeverityLevel.MAJOR,
        
        # Supervisory - Critical for regulatory authority
        ViolationType.SUPERVISORY_NON_COMPLIANCE: SeverityLevel.CRITICAL,
        ViolationType.INSPECTION_OBSTRUCTION: SeverityLevel.CRITICAL,
        ViolationType.DATA_PROVISION_FAILURE: SeverityLevel.MAJOR,
    }
    
    @classmethod
    def get_violation_severity(cls, violation_type: ViolationType) -> SeverityLevel:
        """Get the default severity level for a violation type"""
        return cls.VIOLATION_SEVERITY_MAP.get(violation_type, SeverityLevel.MODERATE)
    
    @classmethod
    def calculate_penalty(
        cls,
        violation_type: ViolationType,
        annual_revenue: Decimal,
        severity_override: Optional[SeverityLevel] = None,
        is_repeat_violation: bool = False,
        is_willful_violation: bool = False,
        custom_factors: Optional[Dict[str, Decimal]] = None
    ) -> Dict[str, Union[Decimal, str, int]]:
        """
        Calculate penalty for a DORA violation
        
        Args:
            violation_type: Type of DORA violation
            annual_revenue: Company's annual revenue in EUR
            severity_override: Override default severity level
            is_repeat_violation: Whether this is a repeat violation
            is_willful_violation: Whether violation was willful/intentional
            custom_factors: Additional multipliers or adjustments
            
        Returns:
            Dictionary containing penalty calculation details
        """
        # Determine severity level
        severity = severity_override or cls.get_violation_severity(violation_type)
        penalty_structure = cls.PENALTY_STRUCTURES[severity]
        
        # Calculate base penalty (higher of fixed fine or percentage)
        percentage_penalty = annual_revenue * penalty_structure.revenue_percentage
        base_penalty = max(
            Decimal(penalty_structure.base_fine_eur),
            percentage_penalty
        )
        
        # Apply minimum and maximum limits
        if penalty_structure.min_fine_eur:
            base_penalty = max(base_penalty, Decimal(penalty_structure.min_fine_eur))
        if penalty_structure.max_fine_eur:
            base_penalty = min(base_penalty, Decimal(penalty_structure.max_fine_eur))
        
        # Apply multipliers
        final_penalty = base_penalty
        multipliers_applied = []
        
        if is_repeat_violation:
            final_penalty *= penalty_structure.multiplier_repeat
            multipliers_applied.append(f"Repeat violation: {penalty_structure.multiplier_repeat}x")
        
        if is_willful_violation:
            final_penalty *= penalty_structure.multiplier_willful
            multipliers_applied.append(f"Willful violation: {penalty_structure.multiplier_willful}x")
        
        # Apply custom factors
        if custom_factors:
            for factor_name, factor_value in custom_factors.items():
                final_penalty *= factor_value
                multipliers_applied.append(f"{factor_name}: {factor_value}x")
        
        # Apply final caps after multipliers
        if penalty_structure.max_fine_eur:
            # For critical violations, allow exceeding normal caps
            max_cap = penalty_structure.max_fine_eur
            if severity == SeverityLevel.CRITICAL and (is_repeat_violation or is_willful_violation):
                max_cap *= 2  # Double the cap for egregious critical violations
            final_penalty = min(final_penalty, Decimal(max_cap))
        
        return {
            "violation_type": violation_type.value,
            "severity_level": severity.value,
            "annual_revenue_eur": annual_revenue,
            "base_fine_eur": penalty_structure.base_fine_eur,
            "revenue_percentage": float(penalty_structure.revenue_percentage * 100),
            "percentage_penalty_eur": percentage_penalty,
            "base_penalty_eur": base_penalty,
            "multipliers_applied": multipliers_applied,
            "final_penalty_eur": final_penalty,
            "penalty_as_revenue_percentage": float((final_penalty / annual_revenue) * 100) if annual_revenue > 0 else 0,
            "calculation_method": "Higher of fixed fine or revenue percentage, with multipliers applied",
            "regulatory_reference": "DORA Article 65 - Administrative pecuniary sanctions"
        }
    
    @classmethod
    def calculate_cumulative_penalties(
        cls,
        violations: List[Dict[str, any]],
        annual_revenue: Decimal,
        max_cumulative_percentage: Decimal = Decimal('0.02')  # 2% max
    ) -> Dict[str, Union[Decimal, List, str]]:
        """
        Calculate cumulative penalties for multiple violations
        
        Args:
            violations: List of violation dictionaries with type, severity, etc.
            annual_revenue: Company's annual revenue in EUR
            max_cumulative_percentage: Maximum total penalty as % of revenue
            
        Returns:
            Dictionary containing cumulative penalty analysis
        """
        individual_penalties = []
        total_penalty = Decimal('0')
        
        for violation in violations:
            penalty_calc = cls.calculate_penalty(
                violation_type=ViolationType(violation['type']),
                annual_revenue=annual_revenue,
                severity_override=SeverityLevel(violation.get('severity')) if violation.get('severity') else None,
                is_repeat_violation=violation.get('is_repeat', False),
                is_willful_violation=violation.get('is_willful', False),
                custom_factors=violation.get('custom_factors')
            )
            individual_penalties.append(penalty_calc)
            total_penalty += penalty_calc['final_penalty_eur']
        
        # Apply cumulative cap
        max_cumulative_penalty = annual_revenue * max_cumulative_percentage
        capped_penalty = min(total_penalty, max_cumulative_penalty)
        
        return {
            "individual_penalties": individual_penalties,
            "total_uncapped_penalty_eur": total_penalty,
            "max_cumulative_penalty_eur": max_cumulative_penalty,
            "final_cumulative_penalty_eur": capped_penalty,
            "cumulative_percentage_of_revenue": float((capped_penalty / annual_revenue) * 100) if annual_revenue > 0 else 0,
            "cap_applied": capped_penalty < total_penalty,
            "savings_from_cap_eur": total_penalty - capped_penalty if capped_penalty < total_penalty else Decimal('0'),
            "regulatory_note": "DORA cumulative penalties may not exceed 2% of annual revenue"
        }


def get_violation_descriptions() -> Dict[ViolationType, str]:
    """Get human-readable descriptions for violation types"""
    return {
        ViolationType.ICT_GOVERNANCE_FAILURE: "Failure to establish adequate ICT governance framework",
        ViolationType.RISK_APPETITE_VIOLATION: "ICT risk appetite not properly defined or implemented",
        ViolationType.RISK_ASSESSMENT_INADEQUATE: "Inadequate ICT risk identification and assessment",
        ViolationType.CONTROL_FRAMEWORK_MISSING: "Missing or insufficient ICT risk controls framework",
        ViolationType.INCIDENT_DETECTION_FAILURE: "Failure to detect ICT-related incidents in timely manner",
        ViolationType.INCIDENT_RESPONSE_INADEQUATE: "Inadequate response to ICT-related incidents",
        ViolationType.INCIDENT_REPORTING_VIOLATION: "Violation of ICT incident reporting requirements",
        ViolationType.MAJOR_INCIDENT_NON_REPORTING: "Failure to report major ICT incidents to authorities",
        ViolationType.TESTING_PROGRAMME_MISSING: "Missing digital operational resilience testing programme",
        ViolationType.TLPT_NON_COMPLIANCE: "Non-compliance with Threat-Led Penetration Testing requirements",
        ViolationType.TESTING_FREQUENCY_VIOLATION: "Violation of required testing frequency and scope",
        ViolationType.VENDOR_RISK_ASSESSMENT_FAILURE: "Failure to properly assess ICT third-party risks",
        ViolationType.CRITICAL_VENDOR_NON_COMPLIANCE: "Non-compliance with critical ICT third-party requirements",
        ViolationType.THIRD_PARTY_MONITORING_INADEQUATE: "Inadequate ongoing monitoring of ICT third parties",
        ViolationType.CONCENTRATION_RISK_VIOLATION: "Violation of ICT concentration risk requirements",
        ViolationType.THREAT_INTEL_SHARING_VIOLATION: "Violation of cyber threat information sharing requirements",
        ViolationType.REGULATORY_COOPERATION_FAILURE: "Failure to cooperate with regulatory authorities",
        ViolationType.SUPERVISORY_NON_COMPLIANCE: "Non-compliance with supervisory requirements",
        ViolationType.INSPECTION_OBSTRUCTION: "Obstruction of regulatory inspections or investigations",
        ViolationType.DATA_PROVISION_FAILURE: "Failure to provide required data to supervisory authorities",
    }


if __name__ == "__main__":
    # Example usage
    revenue = Decimal('100_000_000')  # €100M annual revenue
    
    # Single violation example
    penalty = DORAfinePenalties.calculate_penalty(
        violation_type=ViolationType.TESTING_PROGRAMME_MISSING,
        annual_revenue=revenue,
        is_repeat_violation=False
    )
    
    print("Single Violation Example:")
    print(f"Violation: {penalty['violation_type']}")
    print(f"Final Penalty: €{penalty['final_penalty_eur']:,.2f}")
    print(f"As % of Revenue: {penalty['penalty_as_revenue_percentage']:.3f}%")
    print()
    
    # Multiple violations example
    violations = [
        {"type": "testing_programme_missing", "severity": "critical"},
        {"type": "incident_reporting_violation", "severity": "moderate"},
        {"type": "vendor_risk_assessment_failure", "severity": "major", "is_repeat": True}
    ]
    
    cumulative = DORAfinePenalties.calculate_cumulative_penalties(violations, revenue)
    print("Cumulative Violations Example:")
    print(f"Total Penalty: €{cumulative['final_cumulative_penalty_eur']:,.2f}")
    print(f"As % of Revenue: {cumulative['cumulative_percentage_of_revenue']:.3f}%")
    print(f"Cap Applied: {cumulative['cap_applied']}") 