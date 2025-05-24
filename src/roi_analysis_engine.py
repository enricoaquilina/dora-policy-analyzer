#!/usr/bin/env python3
"""
DORA Compliance ROI Analysis Engine

This module provides comprehensive Return on Investment (ROI) analysis algorithms
for DORA compliance investments, including NPV, IRR, payback period calculations,
and advanced sensitivity analysis capabilities.

Author: DORA Compliance System
Created: 2025-05-24
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
import statistics
import math
from scipy import optimize
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FinancialAssumptions:
    """Core financial assumptions for ROI analysis"""
    discount_rate: float = 0.08  # 8% WACC assumption
    risk_free_rate: float = 0.03  # 3% government bond rate
    inflation_rate: float = 0.025  # 2.5% inflation
    tax_rate: float = 0.25  # 25% corporate tax rate
    analysis_period_years: int = 5  # 5-year analysis period
    currency: str = "EUR"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CashFlowItem:
    """Individual cash flow item"""
    year: int
    amount: Decimal
    category: str  # "penalty_avoidance", "cost_savings", "implementation_cost", "maintenance_cost"
    description: str
    confidence_level: float = 1.0  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['amount'] = float(self.amount)
        return result

@dataclass
class ROIResults:
    """Comprehensive ROI analysis results"""
    # Basic metrics
    total_benefits: Decimal
    total_costs: Decimal
    net_benefit: Decimal
    roi_percentage: float
    payback_period_years: float
    
    # Advanced metrics
    npv: Decimal
    irr: float
    modified_irr: float  # MIRR
    profitability_index: float
    equivalent_annual_annuity: Decimal
    
    # Risk metrics
    breakeven_discount_rate: float
    worst_case_npv: Decimal
    best_case_npv: Decimal
    probability_of_positive_npv: float
    
    # Supporting data
    cash_flows: List[CashFlowItem]
    assumptions: FinancialAssumptions
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Convert Decimal fields to float
        for field in ['total_benefits', 'total_costs', 'net_benefit', 'npv', 
                      'equivalent_annual_annuity', 'worst_case_npv', 'best_case_npv']:
            if hasattr(self, field):
                result[field] = float(getattr(self, field))
        
        # Convert cash flows
        result['cash_flows'] = [cf.to_dict() for cf in self.cash_flows]
        result['assumptions'] = self.assumptions.to_dict()
        
        return result

class NPVCalculator:
    """Net Present Value calculation engine"""
    
    @staticmethod
    def calculate_npv(cash_flows: List[Decimal], discount_rate: float) -> Decimal:
        """Calculate Net Present Value"""
        npv = Decimal(0)
        for year, cash_flow in enumerate(cash_flows):
            pv = cash_flow / Decimal((1 + discount_rate) ** year)
            npv += pv
        return npv.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_npv_with_terminal_value(cash_flows: List[Decimal], 
                                        discount_rate: float,
                                        terminal_growth_rate: float = 0.02) -> Decimal:
        """Calculate NPV with terminal value assumption"""
        if len(cash_flows) < 2:
            return NPVCalculator.calculate_npv(cash_flows, discount_rate)
            
        # Calculate NPV of projected cash flows
        base_npv = NPVCalculator.calculate_npv(cash_flows[:-1], discount_rate)
        
        # Calculate terminal value
        final_cash_flow = cash_flows[-1]
        terminal_value = final_cash_flow * Decimal(1 + terminal_growth_rate) / Decimal(discount_rate - terminal_growth_rate)
        
        # Present value of terminal value
        years = len(cash_flows) - 1
        pv_terminal = terminal_value / Decimal((1 + discount_rate) ** years)
        
        return (base_npv + pv_terminal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class IRRCalculator:
    """Internal Rate of Return calculation engine"""
    
    @staticmethod
    def calculate_irr(cash_flows: List[Decimal], 
                     initial_guess: float = 0.1,
                     max_iterations: int = 1000,
                     tolerance: float = 1e-6) -> Optional[float]:
        """Calculate Internal Rate of Return using Newton-Raphson method"""
        try:
            # Convert Decimal to float for optimization
            cf_float = [float(cf) for cf in cash_flows]
            
            def npv_function(rate):
                return sum(cf / (1 + rate) ** i for i, cf in enumerate(cf_float))
            
            def npv_derivative(rate):
                return sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cf_float))
            
            # Newton-Raphson method
            rate = initial_guess
            for iteration in range(max_iterations):
                npv = npv_function(rate)
                if abs(npv) < tolerance:
                    return rate
                
                derivative = npv_derivative(rate)
                if abs(derivative) < tolerance:
                    break
                    
                rate = rate - npv / derivative
                
                # Bounds checking
                if rate < -0.99:
                    rate = -0.99
                elif rate > 10.0:
                    rate = 10.0
            
            # Final verification
            if abs(npv_function(rate)) < tolerance:
                return rate
            else:
                return None
                
        except (ZeroDivisionError, OverflowError, ValueError):
            return None
    
    @staticmethod
    def calculate_mirr(cash_flows: List[Decimal], 
                      finance_rate: float,
                      reinvestment_rate: float) -> Optional[float]:
        """Calculate Modified Internal Rate of Return"""
        try:
            cf_float = [float(cf) for cf in cash_flows]
            
            # Separate positive and negative cash flows
            negative_cfs = [cf if cf < 0 else 0 for cf in cf_float]
            positive_cfs = [cf if cf > 0 else 0 for cf in cf_float]
            
            # Present value of negative cash flows (financing costs)
            pv_negative = sum(cf / (1 + finance_rate) ** i for i, cf in enumerate(negative_cfs))
            
            # Future value of positive cash flows (reinvestment returns)
            n = len(cash_flows) - 1
            fv_positive = sum(cf * (1 + reinvestment_rate) ** (n - i) for i, cf in enumerate(positive_cfs))
            
            if pv_negative == 0 or fv_positive <= 0:
                return None
                
            # MIRR calculation
            mirr = (fv_positive / abs(pv_negative)) ** (1 / n) - 1
            return mirr
            
        except (ZeroDivisionError, ValueError, OverflowError):
            return None

class PaybackCalculator:
    """Payback period calculation engine"""
    
    @staticmethod
    def calculate_simple_payback(cash_flows: List[Decimal]) -> Optional[float]:
        """Calculate simple payback period (undiscounted)"""
        cumulative = Decimal(0)
        for year, cash_flow in enumerate(cash_flows):
            cumulative += cash_flow
            if cumulative >= 0:
                if year == 0:
                    return 0.0
                # Interpolate within the year
                previous_cumulative = cumulative - cash_flow
                fraction = float(-previous_cumulative / cash_flow)
                return year - 1 + fraction
        return None  # Never pays back
    
    @staticmethod
    def calculate_discounted_payback(cash_flows: List[Decimal], 
                                   discount_rate: float) -> Optional[float]:
        """Calculate discounted payback period"""
        cumulative_pv = Decimal(0)
        for year, cash_flow in enumerate(cash_flows):
            pv = cash_flow / Decimal((1 + discount_rate) ** year)
            cumulative_pv += pv
            if cumulative_pv >= 0:
                if year == 0:
                    return 0.0
                # Interpolate within the year
                previous_cumulative = cumulative_pv - pv
                fraction = float(-previous_cumulative / pv)
                return year - 1 + fraction
        return None  # Never pays back

class SensitivityAnalyzer:
    """Advanced sensitivity analysis engine"""
    
    def __init__(self, base_assumptions: FinancialAssumptions):
        self.base_assumptions = base_assumptions
        
    def run_sensitivity_analysis(self, 
                                base_benefits: Decimal,
                                base_costs: Decimal,
                                variable_ranges: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
        """Run comprehensive sensitivity analysis"""
        
        results = {
            "base_case": {
                "benefits": float(base_benefits),
                "costs": float(base_costs),
                "npv": float(base_benefits - base_costs)
            },
            "sensitivity_table": {},
            "tornado_chart_data": [],
            "scenario_analysis": {}
        }
        
        # Single-variable sensitivity analysis
        for variable, (min_change, max_change) in variable_ranges.items():
            sensitivity_results = []
            
            for change_pct in np.linspace(min_change, max_change, 11):
                if variable == "benefits":
                    adjusted_benefits = base_benefits * Decimal(1 + change_pct)
                    adjusted_costs = base_costs
                elif variable == "costs":
                    adjusted_benefits = base_benefits
                    adjusted_costs = base_costs * Decimal(1 + change_pct)
                elif variable == "discount_rate":
                    # For discount rate, we need to recalculate NPV
                    adjusted_discount_rate = self.base_assumptions.discount_rate * (1 + change_pct)
                    cash_flows = self._generate_cash_flows(base_benefits, base_costs)
                    npv = NPVCalculator.calculate_npv(cash_flows, adjusted_discount_rate)
                    sensitivity_results.append({
                        "change_percent": change_pct * 100,
                        "npv": float(npv)
                    })
                    continue
                
                npv = adjusted_benefits - adjusted_costs
                sensitivity_results.append({
                    "change_percent": change_pct * 100,
                    "npv": float(npv)
                })
            
            results["sensitivity_table"][variable] = sensitivity_results
            
            # Calculate tornado chart impact
            min_npv = min(r["npv"] for r in sensitivity_results)
            max_npv = max(r["npv"] for r in sensitivity_results)
            impact_range = max_npv - min_npv
            
            results["tornado_chart_data"].append({
                "variable": variable,
                "impact_range": impact_range,
                "min_npv": min_npv,
                "max_npv": max_npv
            })
        
        # Sort tornado chart data by impact
        results["tornado_chart_data"].sort(key=lambda x: x["impact_range"], reverse=True)
        
        # Scenario analysis
        scenarios = {
            "pessimistic": {"benefits": -0.3, "costs": 0.3, "discount_rate": 0.2},
            "optimistic": {"benefits": 0.3, "costs": -0.2, "discount_rate": -0.2},
            "most_likely": {"benefits": 0.0, "costs": 0.0, "discount_rate": 0.0}
        }
        
        for scenario_name, changes in scenarios.items():
            scenario_benefits = base_benefits * Decimal(1 + changes["benefits"])
            scenario_costs = base_costs * Decimal(1 + changes["costs"])
            scenario_discount_rate = self.base_assumptions.discount_rate * (1 + changes["discount_rate"])
            
            cash_flows = self._generate_cash_flows(scenario_benefits, scenario_costs)
            npv = NPVCalculator.calculate_npv(cash_flows, scenario_discount_rate)
            
            results["scenario_analysis"][scenario_name] = {
                "benefits": float(scenario_benefits),
                "costs": float(scenario_costs),
                "discount_rate": scenario_discount_rate,
                "npv": float(npv)
            }
        
        return results
    
    def monte_carlo_simulation(self, 
                             base_benefits: Decimal,
                             base_costs: Decimal,
                             num_simulations: int = 10000) -> Dict[str, Any]:
        """Run Monte Carlo simulation for risk analysis"""
        
        npv_results = []
        
        for _ in range(num_simulations):
            # Random variations (assuming normal distribution)
            benefit_multiplier = np.random.normal(1.0, 0.15)  # 15% standard deviation
            cost_multiplier = np.random.normal(1.0, 0.20)     # 20% standard deviation
            discount_rate_adjustment = np.random.normal(0.0, 0.01)  # 1% standard deviation
            
            # Apply variations
            sim_benefits = base_benefits * Decimal(max(0.1, benefit_multiplier))
            sim_costs = base_costs * Decimal(max(0.1, cost_multiplier))
            sim_discount_rate = max(0.01, self.base_assumptions.discount_rate + discount_rate_adjustment)
            
            # Calculate NPV for this simulation
            cash_flows = self._generate_cash_flows(sim_benefits, sim_costs)
            npv = NPVCalculator.calculate_npv(cash_flows, sim_discount_rate)
            npv_results.append(float(npv))
        
        # Statistical analysis
        npv_array = np.array(npv_results)
        
        return {
            "num_simulations": num_simulations,
            "mean_npv": float(np.mean(npv_array)),
            "std_dev_npv": float(np.std(npv_array)),
            "min_npv": float(np.min(npv_array)),
            "max_npv": float(np.max(npv_array)),
            "percentiles": {
                "5th": float(np.percentile(npv_array, 5)),
                "25th": float(np.percentile(npv_array, 25)),
                "50th": float(np.percentile(npv_array, 50)),
                "75th": float(np.percentile(npv_array, 75)),
                "95th": float(np.percentile(npv_array, 95))
            },
            "probability_positive": float(np.sum(npv_array > 0) / len(npv_array)),
            "value_at_risk_5pct": float(np.percentile(npv_array, 5)),
            "expected_shortfall_5pct": float(np.mean(npv_array[npv_array <= np.percentile(npv_array, 5)]))
        }
    
    def _generate_cash_flows(self, total_benefits: Decimal, total_costs: Decimal) -> List[Decimal]:
        """Generate annual cash flows for analysis"""
        years = self.base_assumptions.analysis_period_years
        
        # Typical pattern: high costs upfront, benefits spread over time
        cash_flows = []
        
        # Year 0: Initial implementation costs (80% of total)
        initial_cost = total_costs * Decimal(0.8)
        initial_benefit = Decimal(0)  # No benefits in year 0
        cash_flows.append(initial_benefit - initial_cost)
        
        # Years 1-5: Remaining costs and benefits
        remaining_costs = total_costs * Decimal(0.2)
        annual_remaining_cost = remaining_costs / Decimal(years)
        annual_benefit = total_benefits / Decimal(years)
        
        for year in range(1, years + 1):
            yearly_cash_flow = annual_benefit - annual_remaining_cost
            cash_flows.append(yearly_cash_flow)
        
        return cash_flows

class ROIAnalysisEngine:
    """Main ROI Analysis Engine orchestrating all calculations"""
    
    def __init__(self, assumptions: Optional[FinancialAssumptions] = None):
        self.assumptions = assumptions or FinancialAssumptions()
        self.npv_calculator = NPVCalculator()
        self.irr_calculator = IRRCalculator()
        self.payback_calculator = PaybackCalculator()
        self.sensitivity_analyzer = SensitivityAnalyzer(self.assumptions)
        
    def comprehensive_roi_analysis(self,
                                 penalty_risk: Decimal,
                                 implementation_cost: Decimal,
                                 annual_operational_savings: Decimal = Decimal(0),
                                 include_sensitivity: bool = True) -> ROIResults:
        """Run comprehensive ROI analysis"""
        
        logger.info(f"Starting ROI analysis: Penalty Risk: €{penalty_risk:,.2f}, Implementation Cost: €{implementation_cost:,.2f}")
        
        # Calculate total benefits (penalty avoidance + operational savings)
        total_benefits = penalty_risk + (annual_operational_savings * Decimal(self.assumptions.analysis_period_years))
        
        # Generate cash flow projections
        cash_flows = self._generate_detailed_cash_flows(
            penalty_risk, implementation_cost, annual_operational_savings
        )
        
        # Convert to Decimal list for calculations
        cf_amounts = [cf.amount for cf in cash_flows]
        
        # Basic ROI calculations
        net_benefit = total_benefits - implementation_cost
        roi_percentage = float((net_benefit / implementation_cost) * 100) if implementation_cost > 0 else 0
        
        # NPV calculations
        npv = self.npv_calculator.calculate_npv(cf_amounts, self.assumptions.discount_rate)
        
        # IRR calculations
        irr = self.irr_calculator.calculate_irr(cf_amounts)
        mirr = self.irr_calculator.calculate_mirr(
            cf_amounts, 
            self.assumptions.discount_rate, 
            self.assumptions.discount_rate
        )
        
        # Payback calculations
        payback_simple = self.payback_calculator.calculate_simple_payback(cf_amounts)
        payback_discounted = self.payback_calculator.calculate_discounted_payback(
            cf_amounts, self.assumptions.discount_rate
        )
        
        # Advanced metrics
        profitability_index = float((npv + implementation_cost) / implementation_cost) if implementation_cost > 0 else 0
        
        # Equivalent Annual Annuity
        if npv != 0:
            annuity_factor = (self.assumptions.discount_rate * (1 + self.assumptions.discount_rate) ** self.assumptions.analysis_period_years) / \
                           ((1 + self.assumptions.discount_rate) ** self.assumptions.analysis_period_years - 1)
            eaa = npv * Decimal(annuity_factor)
        else:
            eaa = Decimal(0)
        
        # Risk metrics
        breakeven_rate = self._calculate_breakeven_rate(cf_amounts)
        
        # Sensitivity analysis
        sensitivity_data = None
        if include_sensitivity:
            variable_ranges = {
                "benefits": (-0.5, 0.5),    # -50% to +50%
                "costs": (-0.3, 0.7),       # -30% to +70%
                "discount_rate": (-0.3, 0.5) # -30% to +50%
            }
            sensitivity_data = self.sensitivity_analyzer.run_sensitivity_analysis(
                total_benefits, implementation_cost, variable_ranges
            )
        
        # Monte Carlo for risk assessment
        monte_carlo_results = self.sensitivity_analyzer.monte_carlo_simulation(
            total_benefits, implementation_cost, 1000
        )
        
        # Create results object
        results = ROIResults(
            total_benefits=total_benefits,
            total_costs=implementation_cost,
            net_benefit=net_benefit,
            roi_percentage=roi_percentage,
            payback_period_years=payback_discounted or payback_simple or 0,
            npv=npv,
            irr=irr or 0,
            modified_irr=mirr or 0,
            profitability_index=profitability_index,
            equivalent_annual_annuity=eaa,
            breakeven_discount_rate=breakeven_rate or 0,
            worst_case_npv=Decimal(monte_carlo_results["percentiles"]["5th"]),
            best_case_npv=Decimal(monte_carlo_results["percentiles"]["95th"]),
            probability_of_positive_npv=monte_carlo_results["probability_positive"],
            cash_flows=cash_flows,
            assumptions=self.assumptions,
            sensitivity_analysis=sensitivity_data
        )
        
        logger.info(f"ROI analysis completed: NPV: €{npv:,.2f}, IRR: {(irr or 0)*100:.1f}%, Payback: {results.payback_period_years:.2f} years")
        
        return results
    
    def _generate_detailed_cash_flows(self,
                                    penalty_risk: Decimal,
                                    implementation_cost: Decimal,
                                    annual_operational_savings: Decimal) -> List[CashFlowItem]:
        """Generate detailed cash flow projections"""
        
        cash_flows = []
        
        # Year 0: Implementation costs
        upfront_cost = implementation_cost * Decimal(0.7)  # 70% upfront
        cash_flows.append(CashFlowItem(
            year=0,
            amount=-upfront_cost,
            category="implementation_cost",
            description="Initial implementation and setup costs",
            confidence_level=0.9
        ))
        
        # Years 1-5: Remaining costs, benefits, and savings
        annual_remaining_cost = (implementation_cost * Decimal(0.3)) / Decimal(self.assumptions.analysis_period_years)
        annual_maintenance_cost = implementation_cost * Decimal(0.05)  # 5% annual maintenance
        
        # Penalty avoidance modeled as avoided cost in year 2 (when violations would typically occur)
        penalty_avoidance_year = 2
        
        for year in range(1, self.assumptions.analysis_period_years + 1):
            # Implementation costs
            if annual_remaining_cost > 0:
                cash_flows.append(CashFlowItem(
                    year=year,
                    amount=-annual_remaining_cost,
                    category="implementation_cost",
                    description=f"Year {year} implementation costs",
                    confidence_level=0.8
                ))
            
            # Maintenance costs
            cash_flows.append(CashFlowItem(
                year=year,
                amount=-annual_maintenance_cost,
                category="maintenance_cost",
                description=f"Year {year} maintenance and operational costs",
                confidence_level=0.9
            ))
            
            # Operational savings
            if annual_operational_savings > 0:
                cash_flows.append(CashFlowItem(
                    year=year,
                    amount=annual_operational_savings,
                    category="cost_savings",
                    description=f"Year {year} operational efficiency savings",
                    confidence_level=0.7
                ))
            
            # Penalty avoidance (modeled as a one-time avoided cost)
            if year == penalty_avoidance_year:
                cash_flows.append(CashFlowItem(
                    year=year,
                    amount=penalty_risk,
                    category="penalty_avoidance",
                    description="Avoided DORA penalty risk",
                    confidence_level=0.8
                ))
        
        return cash_flows
    
    def _calculate_breakeven_rate(self, cash_flows: List[Decimal]) -> Optional[float]:
        """Calculate the discount rate at which NPV = 0"""
        try:
            # Use binary search to find breakeven rate
            low_rate, high_rate = 0.001, 1.0  # 0.1% to 100%
            tolerance = 1e-6
            max_iterations = 100
            
            for _ in range(max_iterations):
                mid_rate = (low_rate + high_rate) / 2
                npv = self.npv_calculator.calculate_npv(cash_flows, mid_rate)
                
                if abs(float(npv)) < tolerance:
                    return mid_rate
                elif npv > 0:
                    low_rate = mid_rate
                else:
                    high_rate = mid_rate
                    
                if high_rate - low_rate < tolerance:
                    break
            
            return (low_rate + high_rate) / 2
            
        except Exception:
            return None
    
    def generate_roi_summary(self, results: ROIResults) -> Dict[str, Any]:
        """Generate executive summary of ROI analysis"""
        
        # Investment recommendation logic
        if results.roi_percentage > 300 and results.payback_period_years < 2:
            recommendation = "STRONGLY RECOMMENDED"
            recommendation_reason = "Exceptional ROI with rapid payback"
        elif results.roi_percentage > 100 and results.payback_period_years < 3:
            recommendation = "RECOMMENDED"
            recommendation_reason = "Strong ROI with reasonable payback period"
        elif results.roi_percentage > 50 and results.payback_period_years < 5:
            recommendation = "CONDITIONALLY RECOMMENDED"
            recommendation_reason = "Positive ROI within analysis period"
        elif results.roi_percentage > 0:
            recommendation = "MARGINAL"
            recommendation_reason = "Positive but limited ROI"
        else:
            recommendation = "NOT RECOMMENDED"
            recommendation_reason = "Negative ROI"
        
        # Risk assessment
        if results.probability_of_positive_npv > 0.9:
            risk_level = "LOW"
        elif results.probability_of_positive_npv > 0.7:
            risk_level = "MODERATE"
        else:
            risk_level = "HIGH"
        
        summary = {
            "executive_summary": {
                "investment_recommendation": recommendation,
                "recommendation_reason": recommendation_reason,
                "key_metrics": {
                    "roi_percentage": f"{results.roi_percentage:.1f}%",
                    "payback_period": f"{results.payback_period_years:.2f} years",
                    "npv": f"€{results.npv:,.0f}",
                    "irr": f"{results.irr*100:.1f}%" if results.irr else "N/A"
                }
            },
            "financial_highlights": {
                "total_investment": f"€{results.total_costs:,.0f}",
                "total_benefits": f"€{results.total_benefits:,.0f}",
                "net_benefit": f"€{results.net_benefit:,.0f}",
                "profitability_index": f"{results.profitability_index:.2f}"
            },
            "risk_assessment": {
                "risk_level": risk_level,
                "probability_success": f"{results.probability_of_positive_npv:.1%}",
                "worst_case_npv": f"€{results.worst_case_npv:,.0f}",
                "best_case_npv": f"€{results.best_case_npv:,.0f}"
            },
            "implementation_insights": {
                "critical_success_factors": [
                    "Timely project execution to realize benefits",
                    "Effective change management and training",
                    "Regular monitoring of compliance metrics",
                    "Maintaining system effectiveness over time"
                ],
                "key_risks": [
                    "Implementation delays increasing costs",
                    "Lower than expected penalty avoidance",
                    "Technology changes requiring additional investment",
                    "Regulatory changes affecting requirements"
                ]
            }
        }
        
        return summary

def demonstrate_roi_analysis():
    """Demonstrate the ROI Analysis Engine capabilities"""
    
    print("🔢 DORA Compliance ROI Analysis Engine")
    print("=" * 50)
    
    # Create engine with default assumptions
    engine = ROIAnalysisEngine()
    
    print(f"📊 Financial Assumptions:")
    print(f"   • Discount Rate: {engine.assumptions.discount_rate:.1%}")
    print(f"   • Analysis Period: {engine.assumptions.analysis_period_years} years")
    print(f"   • Risk-Free Rate: {engine.assumptions.risk_free_rate:.1%}")
    print(f"   • Inflation Rate: {engine.assumptions.inflation_rate:.1%}")
    
    # Example analysis
    penalty_risk = Decimal("10000000")  # €10M penalty risk
    implementation_cost = Decimal("396900")  # €396,900 implementation cost
    annual_savings = Decimal("50000")  # €50K annual operational savings
    
    print(f"\n💰 Investment Scenario:")
    print(f"   • Penalty Risk Avoided: €{penalty_risk:,.0f}")
    print(f"   • Implementation Cost: €{implementation_cost:,.0f}")
    print(f"   • Annual Operational Savings: €{annual_savings:,.0f}")
    
    # Run analysis
    results = engine.comprehensive_roi_analysis(
        penalty_risk=penalty_risk,
        implementation_cost=implementation_cost,
        annual_operational_savings=annual_savings
    )
    
    print(f"\n📈 ROI Analysis Results:")
    print(f"   • ROI: {results.roi_percentage:.1f}%")
    print(f"   • NPV: €{results.npv:,.0f}")
    print(f"   • IRR: {results.irr*100:.1f}%" if results.irr else "   • IRR: N/A")
    print(f"   • Payback Period: {results.payback_period_years:.2f} years")
    print(f"   • Profitability Index: {results.profitability_index:.2f}")
    
    print(f"\n⚠️  Risk Metrics:")
    print(f"   • Probability of Positive NPV: {results.probability_of_positive_npv:.1%}")
    print(f"   • Worst Case NPV (5th percentile): €{results.worst_case_npv:,.0f}")
    print(f"   • Best Case NPV (95th percentile): €{results.best_case_npv:,.0f}")
    
    # Generate executive summary
    summary = engine.generate_roi_summary(results)
    
    print(f"\n🎯 Executive Summary:")
    print(f"   • Recommendation: {summary['executive_summary']['investment_recommendation']}")
    print(f"   • Reason: {summary['executive_summary']['recommendation_reason']}")
    print(f"   • Risk Level: {summary['risk_assessment']['risk_level']}")
    
    print(f"\n💡 Key Insights:")
    for factor in summary['implementation_insights']['critical_success_factors'][:3]:
        print(f"   • {factor}")
    
    print(f"\n📊 Cash Flow Summary:")
    for cf in results.cash_flows[:5]:  # Show first 5 cash flows
        amount_str = f"€{cf.amount:,.0f}" if cf.amount >= 0 else f"-€{abs(cf.amount):,.0f}"
        print(f"   • Year {cf.year}: {amount_str} ({cf.category})")
    
    print(f"\n✅ ROI Analysis Engine Demonstration Complete!")

if __name__ == "__main__":
    demonstrate_roi_analysis() 