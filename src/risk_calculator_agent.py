#!/usr/bin/env python3
"""
Risk Calculator Agent

Main agent for calculating DORA compliance financial risks, implementation costs,
ROI analysis, and generating executive-ready business cases. Integrates with
Gap Assessment Agent to provide comprehensive financial justification.

Author: DORA Compliance System
Date: 2025-01-23
"""

import json
import logging
from typing import Dict, List, Optional, Union, Any
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import asdict

# Import penalty calculation components
from .dora_penalties import DORAfinePenalties, ViolationType, SeverityLevel, get_violation_descriptions
from .penalty_models import (
    PenaltyCalculationEngine, RiskFactors, RiskProfile, CompanySize,
    PenaltyScenario, create_default_risk_factors
)
from .financial_data import (
    FinancialDataManager, FinancialProfile, CostEstimate, 
    Currency, DataSource, create_demo_financial_profile
)
from .cost_estimation_framework import (
    AdvancedCostEstimator, ImplementationType, ProjectComplexity, CostCategory,
    create_demo_cost_estimator
)
from .roi_analysis_engine import ROIAnalysisEngine, FinancialAssumptions


class RiskCalculatorAgent:
    """
    Main Risk Calculator Agent for DORA compliance financial analysis
    
    Provides comprehensive financial risk assessment including:
    - DORA penalty calculations (up to 2% of annual revenue)
    - Implementation cost estimation 
    - ROI analysis and payback calculations
    - Business case generation for CIO presentations
    - Scenario modeling and sensitivity analysis
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.financial_manager = FinancialDataManager()
        self.penalty_engine = PenaltyCalculationEngine()
        self.roi_engine = ROIAnalysisEngine()
        
        # Cache for calculated results
        self.calculation_cache = {}
        
        self.logger.info("Risk Calculator Agent initialized")
    
    def calculate_comprehensive_risk_analysis(
        self,
        gap_assessment_data: Dict[str, Any],
        company_profile: Optional[FinancialProfile] = None,
        risk_factors: Optional[RiskFactors] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive risk analysis combining gap assessment with financial impact
        
        Args:
            gap_assessment_data: Results from Gap Assessment Agent
            company_profile: Company financial profile (will create demo if None)
            risk_factors: Risk factors assessment (will create defaults if None)
            
        Returns:
            Comprehensive financial risk analysis
        """
        
        try:
            # Use demo profile if none provided
            if company_profile is None:
                company_profile = create_demo_financial_profile()
                self.logger.info("Using demo financial profile for analysis")
            
            # Create default risk factors if none provided
            if risk_factors is None:
                # Infer risk factors from gap assessment
                compliance_maturity = self._infer_compliance_maturity(gap_assessment_data)
                operational_complexity = self._infer_operational_complexity(gap_assessment_data)
                regulatory_scrutiny = "high"  # DORA is high scrutiny
                
                risk_factors = create_default_risk_factors(
                    compliance_maturity=compliance_maturity,
                    operational_complexity=operational_complexity,
                    regulatory_scrutiny=regulatory_scrutiny
                )
                self.logger.info(f"Created default risk factors: {compliance_maturity} compliance, {operational_complexity} complexity")
            
            # Extract violations from gap assessment
            violations = self._extract_violations_from_gaps(gap_assessment_data)
            
            # Calculate penalties
            penalty_analysis = self._calculate_penalty_analysis(
                violations, company_profile.annual_revenue, risk_factors
            )
            
            # Estimate implementation costs
            cost_analysis = self._calculate_implementation_costs(
                gap_assessment_data, company_profile
            )
            
            # Calculate ROI metrics
            roi_analysis = self._calculate_roi_analysis(
                cost_analysis['total_cost'], penalty_analysis['expected_annual_penalty']
            )
            
            # Generate business case
            business_case = self._generate_business_case(
                company_profile, penalty_analysis, cost_analysis, roi_analysis, gap_assessment_data
            )
            
            # Compile comprehensive analysis
            comprehensive_analysis = {
                "analysis_id": f"risk_calc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "company_profile": {
                    "name": company_profile.company_name,
                    "annual_revenue_eur": company_profile.annual_revenue,
                    "industry": company_profile.industry_sector,
                    "size_category": self.financial_manager.determine_company_size(company_profile.annual_revenue).value
                },
                "penalty_analysis": penalty_analysis,
                "cost_analysis": cost_analysis,
                "roi_analysis": roi_analysis,
                "business_case": business_case,
                "scenarios": self._generate_scenarios(company_profile, violations, risk_factors),
                "executive_summary": self._generate_executive_summary(
                    penalty_analysis, cost_analysis, roi_analysis
                )
            }
            
            # Cache results
            cache_key = f"{company_profile.company_name}_{datetime.now().strftime('%Y%m%d')}"
            self.calculation_cache[cache_key] = comprehensive_analysis
            
            self.logger.info(f"Comprehensive risk analysis completed for {company_profile.company_name}")
            return comprehensive_analysis
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive risk analysis: {e}")
            raise
    
    def _extract_violations_from_gaps(self, gap_assessment_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract DORA violations from gap assessment data"""
        violations = []
        
        # Map gap categories to violation types
        gap_to_violation_map = {
            "ICT Governance": "ict_governance_failure",
            "ICT Risk Management": "risk_assessment_inadequate", 
            "ICT-Related Incident Management": "incident_response_inadequate",
            "Digital Operational Resilience Testing": "testing_programme_missing",
            "ICT Third-Party Risk Management": "vendor_risk_assessment_failure",
            "Information Sharing": "threat_intel_sharing_violation"
        }
        
        # Extract from critical and high priority gaps
        if 'critical_gaps' in gap_assessment_data:
            for gap in gap_assessment_data['critical_gaps']:
                violation_type = gap_to_violation_map.get(gap.get('category', ''))
                if violation_type:
                    violations.append({
                        "type": violation_type,
                        "severity": "critical",
                        "is_repeat": False,
                        "is_willful": False
                    })
        
        if 'high_priority_gaps' in gap_assessment_data:
            for gap in gap_assessment_data['high_priority_gaps']:
                violation_type = gap_to_violation_map.get(gap.get('category', ''))
                if violation_type:
                    violations.append({
                        "type": violation_type,
                        "severity": "major",
                        "is_repeat": False,
                        "is_willful": False
                    })
        
        # If no gaps found, create some demo violations
        if not violations:
            violations = [
                {"type": "testing_programme_missing", "severity": "critical"},
                {"type": "incident_response_inadequate", "severity": "major"},
                {"type": "threat_intel_sharing_violation", "severity": "moderate"}
            ]
        
        return violations
    
    def _calculate_penalty_analysis(
        self,
        violations: List[Dict[str, Any]],
        annual_revenue: Decimal,
        risk_factors: RiskFactors
    ) -> Dict[str, Any]:
        """Calculate comprehensive penalty analysis"""
        
        # Determine company size and risk profile
        company_size = self.financial_manager.determine_company_size(annual_revenue)
        risk_profile = self.penalty_engine._determine_risk_profile(risk_factors)
        
        # Calculate risk-adjusted penalties
        penalty_calc = self.penalty_engine.calculate_risk_adjusted_penalty(
            violations=violations,
            annual_revenue=annual_revenue,
            risk_factors=risk_factors,
            company_size=company_size,
            risk_profile=risk_profile
        )
        
        # Calculate expected annual penalty (assume 30% probability of enforcement)
        enforcement_probability = 0.3
        expected_annual_penalty = penalty_calc['final_penalty_eur'] * Decimal(str(enforcement_probability))
        
        return {
            "maximum_penalty_eur": penalty_calc['final_penalty_eur'],
            "expected_annual_penalty": expected_annual_penalty,
            "penalty_as_revenue_percentage": penalty_calc['penalty_as_revenue_percentage'],
            "enforcement_probability": enforcement_probability,
            "risk_profile": risk_profile.value,
            "company_size": company_size.value,
            "violations_analyzed": len(violations),
            "risk_multiplier": penalty_calc['risk_multiplier'],
            "detailed_calculation": penalty_calc
        }
    
    def _calculate_implementation_costs(
        self,
        gap_assessment_data: Dict[str, Any],
        company_profile: FinancialProfile
    ) -> Dict[str, Any]:
        """Calculate implementation costs for addressing gaps"""
        
        # Extract gap categories
        gap_categories = set()
        
        if 'critical_gaps' in gap_assessment_data:
            for gap in gap_assessment_data['critical_gaps']:
                gap_categories.add(gap.get('category', 'Other'))
        
        if 'high_priority_gaps' in gap_assessment_data:
            for gap in gap_assessment_data['high_priority_gaps']:
                gap_categories.add(gap.get('category', 'Other'))
        
        # Default categories if none found
        if not gap_categories:
            gap_categories = ["Risk Management", "Testing & Resilience", "Incident Management"]
        
        # Estimate costs
        cost_estimates = self.financial_manager.estimate_compliance_cost(
            profile=company_profile,
            gap_categories=list(gap_categories),
            complexity_factor=1.2  # DORA complexity adjustment
        )
        
        # Calculate totals
        total_cost = sum(estimate.estimated_cost_eur for estimate in cost_estimates)
        total_timeline = max(estimate.timeline_months for estimate in cost_estimates) if cost_estimates else 12
        
        # Ensure minimum cost to avoid division by zero
        if total_cost == 0:
            self.logger.warning("Implementation cost calculated as zero, using minimum baseline")
            total_cost = Decimal('100000')  # €100K minimum baseline
        
        # Calculate annual operational cost (5% of implementation cost)
        annual_operational_cost = total_cost * Decimal('0.05')
        
        return {
            "total_cost": total_cost,
            "annual_operational_cost": annual_operational_cost,
            "implementation_timeline_months": total_timeline,
            "cost_by_category": [
                {
                    "category": est.category,
                    "cost_eur": est.estimated_cost_eur,
                    "timeline_months": est.timeline_months,
                    "description": est.description
                }
                for est in cost_estimates
            ],
            "cost_breakdown": {
                "internal_resources": total_cost * Decimal('0.6'),
                "external_services": total_cost * Decimal('0.25'),
                "technology": total_cost * Decimal('0.15')
            }
        }
    
    def _calculate_roi_analysis(
        self,
        implementation_cost: Decimal,
        expected_annual_penalty: Decimal
    ) -> Dict[str, Any]:
        """Calculate ROI analysis"""
        
        # Assume 10% annual operational savings from improved processes
        annual_operational_savings = implementation_cost * Decimal('0.1')
        
        roi_metrics = self.financial_manager.calculate_roi_metrics(
            implementation_cost=implementation_cost,
            potential_penalty=expected_annual_penalty,
            annual_operational_savings=annual_operational_savings,
            discount_rate=0.08,
            time_horizon_years=5
        )
        
        return {
            "payback_period_years": roi_metrics['payback_period_years'],
            "net_present_value_eur": roi_metrics['net_present_value_eur'],
            "return_on_investment": roi_metrics['return_on_investment'],
            "internal_rate_of_return": roi_metrics['internal_rate_of_return'],
            "benefit_cost_ratio": roi_metrics['benefit_cost_ratio'],
            "total_savings_eur": roi_metrics['total_savings_eur'],
            "annual_benefits_eur": roi_metrics['annual_benefits_eur'],
            "investment_recommendation": self._generate_investment_recommendation(roi_metrics)
        }
    
    def _generate_investment_recommendation(self, roi_metrics: Dict) -> str:
        """Generate investment recommendation based on ROI metrics"""
        
        payback = roi_metrics['payback_period_years']
        roi = roi_metrics['return_on_investment']
        npv = roi_metrics['net_present_value_eur']
        
        if payback < 2 and roi > 1.0 and npv > 0:
            return "STRONGLY RECOMMENDED - Excellent ROI with rapid payback"
        elif payback < 3 and roi > 0.5 and npv > 0:
            return "RECOMMENDED - Good ROI with reasonable payback period"
        elif payback < 5 and npv > 0:
            return "ACCEPTABLE - Positive NPV justifies investment"
        else:
            return "REQUIRED - Regulatory compliance mandatory despite poor ROI"
    
    def _generate_scenarios(
        self,
        company_profile: FinancialProfile,
        violations: List[Dict[str, Any]],
        risk_factors: RiskFactors
    ) -> Dict[str, Any]:
        """Generate scenario analysis"""
        
        scenarios = []
        
        # Best case scenario - minimal violations
        best_case_violations = violations[:1] if violations else []
        scenarios.append(PenaltyScenario(
            scenario_name="Best Case - Minimal Violations",
            probability=0.4,
            violations=best_case_violations,
            annual_revenue=company_profile.annual_revenue,
            risk_factors=risk_factors,
            timeline_months=12
        ))
        
        # Base case scenario - current violations
        scenarios.append(PenaltyScenario(
            scenario_name="Base Case - Current Assessment",
            probability=0.4,
            violations=violations,
            annual_revenue=company_profile.annual_revenue,
            risk_factors=risk_factors,
            timeline_months=12
        ))
        
        # Worst case scenario - additional violations
        worst_case_violations = violations + [
            {"type": "supervisory_non_compliance", "severity": "critical", "is_willful": True}
        ]
        scenarios.append(PenaltyScenario(
            scenario_name="Worst Case - Willful Non-Compliance",
            probability=0.2,
            violations=worst_case_violations,
            annual_revenue=company_profile.annual_revenue,
            risk_factors=risk_factors,
            timeline_months=12
        ))
        
        # Model scenarios
        scenario_analysis = self.penalty_engine.model_penalty_scenarios(scenarios)
        
        return {
            "scenarios": scenario_analysis['scenarios'],
            "expected_penalty_eur": scenario_analysis['expected_total_penalty_eur'],
            "worst_case_penalty_eur": scenario_analysis['worst_case_penalty_eur'],
            "value_at_risk_95": scenario_analysis['value_at_risk_95'],
            "penalty_variance": scenario_analysis['penalty_variance']
        }
    
    def _generate_business_case(
        self,
        company_profile: FinancialProfile,
        penalty_analysis: Dict[str, Any],
        cost_analysis: Dict[str, Any],
        roi_analysis: Dict[str, Any],
        gap_assessment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive business case"""
        
        return {
            "executive_summary": {
                "investment_required": cost_analysis['total_cost'],
                "maximum_penalty_avoided": penalty_analysis['maximum_penalty_eur'],
                "payback_period": roi_analysis['payback_period_years'],
                "net_benefit": roi_analysis['total_savings_eur'],
                "recommendation": roi_analysis['investment_recommendation']
            },
            "financial_justification": {
                "penalty_risk": f"Up to €{penalty_analysis['maximum_penalty_eur']:,.0f} ({penalty_analysis['penalty_as_revenue_percentage']:.1f}% of revenue)",
                "implementation_cost": f"€{cost_analysis['total_cost']:,.0f} over {cost_analysis['implementation_timeline_months']} months",
                "annual_savings": f"€{roi_analysis['annual_benefits_eur']:,.0f} per year",
                "roi_percentage": f"{roi_analysis['return_on_investment']:.1%} over 5 years"
            },
            "key_risks": [
                "Regulatory penalties up to 2% of annual revenue",
                "Reputational damage from non-compliance",
                "Operational disruption from incidents",
                "Competitive disadvantage vs compliant peers"
            ],
            "implementation_phases": self._generate_implementation_phases(cost_analysis),
            "success_metrics": [
                "Zero regulatory penalties or sanctions",
                "100% compliance with DORA requirements", 
                "Reduced operational risk incidents",
                "Improved regulatory relationships"
            ]
        }
    
    def _generate_implementation_phases(self, cost_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate implementation phases for business case"""
        
        phases = [
            {
                "phase": "1. Assessment and Planning",
                "duration_months": 2,
                "cost_percentage": 0.15,
                "activities": ["Detailed gap analysis", "Implementation planning", "Resource allocation"]
            },
            {
                "phase": "2. Core Implementation", 
                "duration_months": 8,
                "cost_percentage": 0.70,
                "activities": ["System deployment", "Process implementation", "Staff training"]
            },
            {
                "phase": "3. Testing and Validation",
                "duration_months": 2,
                "cost_percentage": 0.15,
                "activities": ["Compliance testing", "Validation activities", "Documentation finalization"]
            }
        ]
        
        total_cost = cost_analysis['total_cost']
        for phase in phases:
            phase['estimated_cost'] = total_cost * Decimal(str(phase['cost_percentage']))
        
        return phases
    
    def _generate_executive_summary(
        self,
        penalty_analysis: Dict[str, Any],
        cost_analysis: Dict[str, Any], 
        roi_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate executive summary for CIO presentation"""
        
        return {
            "situation": f"DORA compliance gaps expose the organization to penalties up to €{penalty_analysis['maximum_penalty_eur']:,.0f} ({penalty_analysis['penalty_as_revenue_percentage']:.1f}% of annual revenue).",
            
            "proposal": f"Invest €{cost_analysis['total_cost']:,.0f} over {cost_analysis['implementation_timeline_months']} months to achieve full DORA compliance and eliminate penalty risk.",
            
            "benefits": f"Avoid expected annual penalties of €{penalty_analysis['expected_annual_penalty']:,.0f}, achieve payback in {roi_analysis['payback_period_years']:.1f} years, and generate €{roi_analysis['total_savings_eur']:,.0f} net benefit over 5 years.",
            
            "recommendation": roi_analysis['investment_recommendation'],
            
            "urgency": "DORA applies from January 2025. Immediate action required to avoid regulatory penalties and maintain operational license."
        }
    
    def _infer_compliance_maturity(self, gap_assessment_data: Dict[str, Any]) -> str:
        """Infer compliance maturity from gap assessment"""
        critical_gaps = len(gap_assessment_data.get('critical_gaps', []))
        high_gaps = len(gap_assessment_data.get('high_priority_gaps', []))
        
        if critical_gaps >= 3 or high_gaps >= 5:
            return "low"
        elif critical_gaps >= 1 or high_gaps >= 2:
            return "medium"
        else:
            return "high"
    
    def _infer_operational_complexity(self, gap_assessment_data: Dict[str, Any]) -> str:
        """Infer operational complexity from gap assessment"""
        # Check for complex categories
        complex_categories = ["Digital Operational Resilience Testing", "ICT Third-Party Risk Management"]
        
        gaps = gap_assessment_data.get('critical_gaps', []) + gap_assessment_data.get('high_priority_gaps', [])
        complex_gaps = [gap for gap in gaps if gap.get('category', '') in complex_categories]
        
        if len(complex_gaps) >= 2:
            return "high"
        elif len(complex_gaps) >= 1:
            return "medium"
        else:
            return "low"


def calculate_financial_impact(gap_assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate comprehensive financial impact of DORA compliance gaps
    Integrates penalty calculations, advanced cost estimation, and ROI analysis
    
    Args:
        gap_assessment_data: Gap assessment results from Gap Assessment Agent
        
    Returns:
        Complete financial analysis with penalty risk, implementation costs, and ROI
    """
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize all engines including the new ROI Analysis Engine
        from .roi_analysis_engine import ROIAnalysisEngine
        
        penalty_engine = PenaltyCalculationEngine()
        cost_estimator = create_demo_cost_estimator()
        financial_manager = FinancialDataManager()
        roi_engine = ROIAnalysisEngine()  # New advanced ROI engine
        
        # Create demo financial profile (in production, this would come from actual data)
        company_profile = create_demo_financial_profile()
        
        # Extract company information from gap assessment if available
        if 'company_info' in gap_assessment_data:
            company_info = gap_assessment_data['company_info']
            # Update profile with actual company data
            if 'annual_revenue' in company_info:
                company_profile.annual_revenue = Decimal(str(company_info['annual_revenue']))
            if 'country' in company_info:
                company_profile.country_of_incorporation = company_info['country']
        
        # 1. PENALTY RISK ANALYSIS
        # Identify critical gaps and their potential penalties
        critical_gaps = gap_assessment_data.get('critical_gaps', [])
        high_priority_gaps = gap_assessment_data.get('high_priority_gaps', [])
        all_gaps = critical_gaps + high_priority_gaps
        
        # Calculate penalty scenarios based on identified gaps
        penalty_scenarios = []
        total_violation_risk = Decimal('0')
        
        for gap in all_gaps:
            # Map gap to violation type
            violation_type = _map_gap_to_violation_type(gap)
            severity = SeverityLevel.MAJOR if gap in critical_gaps else SeverityLevel.MODERATE
            
            # Calculate penalty for this specific gap using DORA engine
            penalty_result = DORAfinePenalties.calculate_penalty(
                violation_type=violation_type,
                annual_revenue=company_profile.annual_revenue,
                severity_override=severity
            )
            
            penalty_scenarios.append({
                'gap_id': gap.get('id', 'unknown'),
                'violation_type': violation_type.value,
                'severity': severity.value,
                'penalty_amount': penalty_result['final_penalty_eur'],
                'probability': 0.7 if gap in critical_gaps else 0.4,
                'expected_penalty': penalty_result['final_penalty_eur'] * Decimal(str(0.7 if gap in critical_gaps else 0.4))
            })
            
            total_violation_risk += penalty_result['final_penalty_eur'] * Decimal(str(0.7 if gap in critical_gaps else 0.4))
        
        # Calculate maximum penalty exposure using cumulative calculation
        max_violations = [{'type': violation_type.value, 'severity': 'critical'} for violation_type in [
            ViolationType.TESTING_PROGRAMME_MISSING, ViolationType.ICT_GOVERNANCE_FAILURE
        ]]
        
        max_penalty_result = DORAfinePenalties.calculate_cumulative_penalties(
            max_violations, company_profile.annual_revenue
        )
        
        # 2. ADVANCED COST ESTIMATION
        # Determine implementation type based on gaps
        implementation_type = _determine_implementation_type(gap_assessment_data)
        complexity = _assess_implementation_complexity(gap_assessment_data)
        
        # Generate comprehensive cost estimate using advanced framework
        cost_estimate = cost_estimator.estimate_implementation_cost(
            implementation_type=implementation_type,
            company_profile=company_profile,
            complexity=complexity,
            custom_requirements=_extract_custom_requirements(gap_assessment_data),
            use_vendor_quotes=True,
            timeline_months=None  # Use template defaults
        )
        
        # 3. ADVANCED ROI ANALYSIS USING NEW ENGINE
        implementation_cost = cost_estimate['total_cost_eur']
        max_penalty_risk = max_penalty_result.get('cumulative_penalty_eur', max_penalty_result.get('final_penalty_eur', Decimal('10000000')))
        
        # Estimate annual operational savings (5% of implementation cost)
        annual_operational_savings = implementation_cost * Decimal('0.05')
        
        # Run comprehensive ROI analysis using the new engine
        roi_results = roi_engine.comprehensive_roi_analysis(
            penalty_risk=max_penalty_risk,
            implementation_cost=implementation_cost,
            annual_operational_savings=annual_operational_savings,
            include_sensitivity=True
        )
        
        # Generate executive summary from ROI engine
        roi_summary = roi_engine.generate_roi_summary(roi_results)
        
        # 4. ENHANCED FINANCIAL IMPACT RESPONSE
        return {
            "penalty_analysis": {
                "maximum_penalty_risk": float(max_penalty_risk),
                "expected_annual_penalty": float(total_violation_risk),
                "penalty_scenarios": penalty_scenarios,
                "penalty_as_revenue_percentage": float((max_penalty_risk / company_profile.annual_revenue) * 100),
                "cumulative_penalty_details": max_penalty_result
            },
            "implementation_cost": {
                "total_cost": float(implementation_cost),
                "timeline_months": cost_estimate['timeline_months'],
                "complexity_assessment": complexity.value,
                "implementation_type": implementation_type.value,
                "cost_breakdown": cost_estimate.get('cost_breakdown', {}),
                "vendor_quotes": cost_estimate.get('vendor_quotes', [])
            },
            "advanced_roi_analysis": {
                "roi_percentage": roi_results.roi_percentage,
                "npv": float(roi_results.npv),
                "irr": roi_results.irr * 100 if roi_results.irr else None,
                "modified_irr": roi_results.modified_irr * 100 if roi_results.modified_irr else None,
                "payback_period_years": roi_results.payback_period_years,
                "profitability_index": roi_results.profitability_index,
                "equivalent_annual_annuity": float(roi_results.equivalent_annual_annuity),
                "breakeven_discount_rate": roi_results.breakeven_discount_rate * 100
            },
            "risk_metrics": {
                "probability_positive_npv": roi_results.probability_of_positive_npv,
                "worst_case_npv": float(roi_results.worst_case_npv),
                "best_case_npv": float(roi_results.best_case_npv),
                "financial_assumptions": roi_results.assumptions.to_dict()
            },
            "cash_flow_analysis": {
                "detailed_cash_flows": [cf.to_dict() for cf in roi_results.cash_flows],
                "cash_flow_summary": {
                    "year_0_outflow": float(roi_results.cash_flows[0].amount) if roi_results.cash_flows else 0,
                    "annual_net_benefits": float(sum(cf.amount for cf in roi_results.cash_flows[1:]) / len(roi_results.cash_flows[1:])) if len(roi_results.cash_flows) > 1 else 0,
                    "total_benefits": float(roi_results.total_benefits),
                    "net_benefit": float(roi_results.net_benefit)
                }
            },
            "sensitivity_analysis": roi_results.sensitivity_analysis,
            "investment_recommendation": {
                "recommendation": roi_summary["executive_summary"]["investment_recommendation"],
                "reason": roi_summary["executive_summary"]["recommendation_reason"],
                "risk_level": roi_summary["risk_assessment"]["risk_level"],
                "probability_success": roi_summary["risk_assessment"]["probability_success"],
                "key_metrics": roi_summary["executive_summary"]["key_metrics"]
            },
            "business_case": {
                "executive_summary": {
                    "situation": f"DORA compliance gaps expose the organization to penalties up to €{max_penalty_risk:,.0f} ({float((max_penalty_risk / company_profile.annual_revenue) * 100):.1f}% of annual revenue).",
                    "proposal": f"Invest €{implementation_cost:,.0f} over {cost_estimate['timeline_months']} months to achieve full DORA compliance and eliminate penalty risk.",
                    "benefits": f"Achieve payback in {roi_results.payback_period_years:.1f} years with NPV of €{roi_results.npv:,.0f} over 5 years.",
                    "recommendation": roi_summary["executive_summary"]["investment_recommendation"],
                    "urgency": "DORA applies from January 2025. Immediate action required to avoid regulatory penalties."
                },
                "financial_highlights": roi_summary["financial_highlights"],
                "implementation_insights": roi_summary["implementation_insights"]
            },
            "meta": {
                "calculation_timestamp": datetime.now().isoformat(),
                "roi_engine_version": "1.0",
                "analysis_methodology": "Advanced DCF with Monte Carlo simulation",
                "confidence_level": "High - Based on regulatory guidelines and industry benchmarks"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in financial impact calculation: {str(e)}")
        # Return basic fallback calculation
        return {
            "error": f"Financial impact calculation failed: {str(e)}",
            "fallback_analysis": {
                "estimated_penalty_risk": 10000000,  # €10M fallback
                "estimated_implementation_cost": 500000,  # €500K fallback
                "simple_roi": 1900,  # 1900% fallback
                "recommendation": "DETAILED ANALYSIS REQUIRED"
            }
        }


def _map_gap_to_violation_type(gap: Dict[str, Any]) -> ViolationType:
    """Map a compliance gap to DORA violation type"""
    
    gap_description = gap.get('description', '').lower()
    gap_id = gap.get('id', '').lower()
    dora_reference = gap.get('dora_reference', '').lower()
    
    # Map based on DORA article references and gap descriptions
    if any(keyword in gap_description for keyword in ['governance', 'board', 'oversight', 'strategy']):
        return ViolationType.ICT_GOVERNANCE_FAILURE
    
    elif any(keyword in gap_description for keyword in ['risk management', 'risk assessment', 'risk framework']):
        return ViolationType.RISK_ASSESSMENT_INADEQUATE
    
    elif any(keyword in gap_description for keyword in ['incident', 'response', 'notification', 'reporting']):
        return ViolationType.INCIDENT_REPORTING_VIOLATION
    
    elif any(keyword in gap_description for keyword in ['testing', 'resilience', 'tlpt', 'penetration']):
        return ViolationType.TESTING_PROGRAMME_MISSING
    
    elif any(keyword in gap_description for keyword in ['third party', 'vendor', 'outsourcing', 'concentration']):
        return ViolationType.VENDOR_RISK_ASSESSMENT_FAILURE
    
    elif any(keyword in gap_description for keyword in ['information sharing', 'threat intelligence', 'cyber threat']):
        return ViolationType.THREAT_INTEL_SHARING_VIOLATION
    
    elif any(keyword in gap_description for keyword in ['operational', 'disruption', 'business continuity']):
        return ViolationType.INCIDENT_RESPONSE_INADEQUATE
    
    elif any(keyword in gap_description for keyword in ['data protection', 'privacy', 'confidentiality']):
        return ViolationType.DATA_PROVISION_FAILURE
    
    elif any(keyword in gap_description for keyword in ['systemic', 'system-wide', 'critical infrastructure']):
        return ViolationType.CRITICAL_VENDOR_NON_COMPLIANCE
    
    # Default for unclassified gaps
    return ViolationType.RISK_ASSESSMENT_INADEQUATE


def _determine_implementation_type(gap_assessment_data: Dict[str, Any]) -> ImplementationType:
    """Determine the appropriate implementation type based on gap assessment results"""
    
    critical_gaps = gap_assessment_data.get('critical_gaps', [])
    high_priority_gaps = gap_assessment_data.get('high_priority_gaps', [])
    medium_priority_gaps = gap_assessment_data.get('medium_priority_gaps', [])
    
    all_gaps = critical_gaps + high_priority_gaps + medium_priority_gaps
    total_gaps = len(all_gaps)
    critical_count = len(critical_gaps)
    
    # Analyze gap patterns to determine implementation scope
    governance_gaps = sum(1 for gap in all_gaps if 'governance' in gap.get('description', '').lower())
    risk_mgmt_gaps = sum(1 for gap in all_gaps if 'risk' in gap.get('description', '').lower())
    incident_gaps = sum(1 for gap in all_gaps if 'incident' in gap.get('description', '').lower())
    testing_gaps = sum(1 for gap in all_gaps if 'testing' in gap.get('description', '').lower())
    third_party_gaps = sum(1 for gap in all_gaps if 'third party' in gap.get('description', '').lower())
    
    # Decision logic based on gap distribution and severity
    if total_gaps >= 15 or critical_count >= 5:
        return ImplementationType.FULL_COMPLIANCE
    
    elif governance_gaps >= 3:
        return ImplementationType.GOVERNANCE_FRAMEWORK
    
    elif risk_mgmt_gaps >= 3:
        return ImplementationType.RISK_MANAGEMENT_SYSTEM
    
    elif testing_gaps >= 2:
        return ImplementationType.RESILIENCE_TESTING
    
    elif incident_gaps >= 2:
        return ImplementationType.INCIDENT_MANAGEMENT
    
    elif third_party_gaps >= 2:
        return ImplementationType.THIRD_PARTY_MANAGEMENT
    
    # Default for smaller scope implementations
    return ImplementationType.GOVERNANCE_FRAMEWORK


def _assess_implementation_complexity(gap_assessment_data: Dict[str, Any]) -> ProjectComplexity:
    """Assess implementation complexity based on gap characteristics"""
    
    critical_gaps = gap_assessment_data.get('critical_gaps', [])
    high_priority_gaps = gap_assessment_data.get('high_priority_gaps', [])
    
    # Complexity factors
    total_gaps = len(critical_gaps) + len(high_priority_gaps)
    critical_count = len(critical_gaps)
    
    # Check for complex integration requirements
    integration_complexity = 0
    system_changes = 0
    
    for gap in critical_gaps + high_priority_gaps:
        description = gap.get('description', '').lower()
        
        if any(keyword in description for keyword in ['integration', 'system', 'platform', 'infrastructure']):
            system_changes += 1
        
        if any(keyword in description for keyword in ['multiple', 'enterprise', 'organization-wide', 'comprehensive']):
            integration_complexity += 1
    
    # Determine complexity level
    complexity_score = (critical_count * 3) + (total_gaps * 1) + (system_changes * 2) + (integration_complexity * 2)
    
    if complexity_score >= 25:
        return ProjectComplexity.ENTERPRISE
    elif complexity_score >= 15:
        return ProjectComplexity.COMPLEX
    elif complexity_score >= 8:
        return ProjectComplexity.MODERATE
    else:
        return ProjectComplexity.SIMPLE


def _extract_custom_requirements(gap_assessment_data: Dict[str, Any]) -> List[str]:
    """Extract custom requirements from gap assessment data"""
    
    custom_requirements = []
    
    # Extract from gap descriptions
    all_gaps = (gap_assessment_data.get('critical_gaps', []) + 
                gap_assessment_data.get('high_priority_gaps', []))
    
    for gap in all_gaps:
        description = gap.get('description', '')
        
        # Look for specific technology or integration mentions
        if 'api' in description.lower() or 'integration' in description.lower():
            custom_requirements.append("API integration and system connectivity")
        
        if 'dashboard' in description.lower() or 'monitoring' in description.lower():
            custom_requirements.append("Real-time monitoring dashboard")
        
        if 'automation' in description.lower() or 'automated' in description.lower():
            custom_requirements.append("Process automation capabilities")
        
        if 'reporting' in description.lower() and 'regulatory' in description.lower():
            custom_requirements.append("Regulatory reporting automation")
        
        if 'third party' in description.lower() and 'assessment' in description.lower():
            custom_requirements.append("Third-party risk assessment platform")
    
    # Remove duplicates
    return list(set(custom_requirements))


def _determine_company_size_category(annual_revenue: Decimal) -> CompanySize:
    """Determine company size category from annual revenue"""
    
    revenue_millions = float(annual_revenue) / 1_000_000
    
    if revenue_millions < 50:
        return CompanySize.SMALL
    elif revenue_millions < 500:
        return CompanySize.MEDIUM
    elif revenue_millions < 5000:
        return CompanySize.LARGE
    else:
        return CompanySize.SYSTEMIC


if __name__ == "__main__":
    # Example usage with demo data
    demo_gap_data = {
        "critical_gaps": [
            {
                "id": "GAP-001",
                "category": "Digital Operational Resilience Testing",
                "severity": "Critical",
                "description": "No comprehensive testing programme"
            }
        ],
        "high_priority_gaps": [
            {
                "id": "GAP-002", 
                "category": "ICT Risk Management",
                "severity": "High",
                "description": "Manual risk assessment processes"
            }
        ]
    }
    
    # Calculate financial impact
    agent = RiskCalculatorAgent()
    result = agent.calculate_comprehensive_risk_analysis(demo_gap_data)
    
    print("=== DORA Risk Calculator Analysis ===")
    print(f"Maximum Penalty Risk: €{result['penalty_analysis']['maximum_penalty_eur']:,.0f}")
    print(f"Implementation Cost: €{result['cost_analysis']['total_cost']:,.0f}")
    print(f"Payback Period: {result['roi_analysis']['payback_period_years']:.1f} years")
    print(f"ROI: {result['roi_analysis']['return_on_investment']:.1%}")
    print(f"Recommendation: {result['roi_analysis']['investment_recommendation']}")
    print()
    print("Executive Summary:")
    print(f"• {result['executive_summary']['situation']}")
    print(f"• {result['executive_summary']['proposal']}")
    print(f"• {result['executive_summary']['benefits']}")
    print(f"• {result['executive_summary']['recommendation']}") 