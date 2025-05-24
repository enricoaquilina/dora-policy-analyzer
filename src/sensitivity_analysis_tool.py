#!/usr/bin/env python3
"""
DORA Compliance Sensitivity Analysis Tool

This module provides comprehensive sensitivity analysis capabilities for DORA compliance
financial models, including Monte Carlo simulation, scenario analysis, tornado charts,
and stress testing to account for uncertainty and variable inputs.

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
from scipy import stats, optimize
from scipy.stats import norm, lognorm, uniform, beta
import itertools
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VariableDistribution:
    """Statistical distribution for a variable"""
    name: str
    distribution_type: str  # "normal", "lognormal", "uniform", "beta", "triangular"
    parameters: Dict[str, float]  # e.g., {"mean": 1.0, "std": 0.15}
    bounds: Optional[Tuple[float, float]] = None  # Min/max bounds
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.bounds:
            result['bounds'] = list(self.bounds)
        return result

@dataclass
class SensitivityVariable:
    """Variable for sensitivity analysis"""
    name: str
    base_value: float
    range_percent: Tuple[float, float]  # e.g., (-0.3, 0.5) for -30% to +50%
    distribution: Optional[VariableDistribution] = None
    category: str = "financial"  # "financial", "operational", "regulatory"
    impact_type: str = "multiplicative"  # "multiplicative", "additive"
    description: str = ""  # Added description field
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['range_percent'] = list(self.range_percent)
        if self.distribution:
            result['distribution'] = self.distribution.to_dict()
        return result

@dataclass
class SensitivityScenario:
    """Scenario for sensitivity analysis"""
    name: str
    description: str
    variable_adjustments: Dict[str, float]  # Variable name -> adjustment factor
    probability: float = 1.0
    category: str = "stress"  # "optimistic", "pessimistic", "stress", "base"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SensitivityResults:
    """Results from sensitivity analysis"""
    analysis_type: str
    base_case_npv: float
    variable_impacts: Dict[str, Dict[str, float]]
    scenario_results: Dict[str, Dict[str, float]]
    statistical_summary: Dict[str, float]
    confidence_intervals: Dict[str, Dict[str, float]]
    risk_metrics: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class DistributionGenerator:
    """Generates random samples from various distributions"""
    
    @staticmethod
    def generate_samples(distribution: VariableDistribution, size: int = 10000) -> np.ndarray:
        """Generate random samples from specified distribution"""
        
        params = distribution.parameters
        
        if distribution.distribution_type == "normal":
            samples = np.random.normal(params["mean"], params["std"], size)
            
        elif distribution.distribution_type == "lognormal":
            samples = np.random.lognormal(params["mean"], params["sigma"], size)
            
        elif distribution.distribution_type == "uniform":
            samples = np.random.uniform(params["low"], params["high"], size)
            
        elif distribution.distribution_type == "beta":
            samples = np.random.beta(params["alpha"], params["beta"], size)
            # Scale to appropriate range if needed
            if "scale" in params:
                samples = samples * params["scale"]
            if "loc" in params:
                samples = samples + params["loc"]
                
        elif distribution.distribution_type == "triangular":
            samples = np.random.triangular(
                params["left"], params["mode"], params["right"], size
            )
            
        else:
            raise ValueError(f"Unsupported distribution type: {distribution.distribution_type}")
        
        # Apply bounds if specified
        if distribution.bounds:
            samples = np.clip(samples, distribution.bounds[0], distribution.bounds[1])
        
        return samples

class TornadoAnalyzer:
    """Performs tornado diagram analysis"""
    
    def __init__(self, base_model_function):
        """
        Initialize with a base model function that takes variable adjustments
        and returns the target metric (e.g., NPV)
        """
        self.base_model_function = base_model_function
        
    def analyze(self, variables: List[SensitivityVariable], 
                base_case_result: float) -> Dict[str, Any]:
        """Perform tornado analysis on all variables"""
        
        tornado_data = []
        
        for variable in variables:
            # Test low and high values
            low_adjustment = 1 + variable.range_percent[0]
            high_adjustment = 1 + variable.range_percent[1]
            
            # Calculate impact for low value
            low_result = self.base_model_function({variable.name: low_adjustment})
            low_impact = low_result - base_case_result
            
            # Calculate impact for high value
            high_result = self.base_model_function({variable.name: high_adjustment})
            high_impact = high_result - base_case_result
            
            # Calculate total impact range
            impact_range = abs(high_impact - low_impact)
            
            tornado_data.append({
                "variable": variable.name,
                "category": variable.category,
                "low_impact": low_impact,
                "high_impact": high_impact,
                "impact_range": impact_range,
                "low_value": variable.base_value * low_adjustment,
                "high_value": variable.base_value * high_adjustment,
                "sensitivity": impact_range / base_case_result if base_case_result != 0 else 0
            })
        
        # Sort by impact range (descending)
        tornado_data.sort(key=lambda x: x["impact_range"], reverse=True)
        
        return {
            "tornado_chart_data": tornado_data,
            "most_sensitive_variable": tornado_data[0]["variable"] if tornado_data else None,
            "total_sensitivity_range": sum(item["impact_range"] for item in tornado_data)
        }

class MonteCarloSimulator:
    """Performs Monte Carlo simulation analysis"""
    
    def __init__(self, base_model_function):
        self.base_model_function = base_model_function
        
    def simulate(self, variables: List[SensitivityVariable], 
                num_simulations: int = 10000,
                correlation_matrix: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Perform Monte Carlo simulation"""
        
        logger.info(f"Starting Monte Carlo simulation with {num_simulations} iterations...")
        
        # Generate samples for each variable
        variable_samples = {}
        
        for variable in variables:
            if variable.distribution:
                # Use specified distribution
                samples = DistributionGenerator.generate_samples(
                    variable.distribution, num_simulations
                )
            else:
                # Use uniform distribution within range
                low_val = 1 + variable.range_percent[0]
                high_val = 1 + variable.range_percent[1]
                samples = np.random.uniform(low_val, high_val, num_simulations)
            
            variable_samples[variable.name] = samples
        
        # Apply correlation if specified
        if correlation_matrix is not None:
            # Convert to correlated samples using Cholesky decomposition
            # This is a simplified approach - in practice might need more sophisticated methods
            variable_names = list(variable_samples.keys())
            uncorrelated_matrix = np.column_stack([variable_samples[name] for name in variable_names])
            
            # Apply correlation
            L = np.linalg.cholesky(correlation_matrix)
            correlated_matrix = uncorrelated_matrix @ L.T
            
            # Update variable samples
            for i, name in enumerate(variable_names):
                variable_samples[name] = correlated_matrix[:, i]
        
        # Run simulations
        results = []
        for i in range(num_simulations):
            # Create adjustment dict for this iteration
            adjustments = {name: samples[i] for name, samples in variable_samples.items()}
            
            # Run model
            result = self.base_model_function(adjustments)
            results.append(result)
            
            if (i + 1) % 1000 == 0:
                logger.info(f"Completed {i + 1}/{num_simulations} simulations")
        
        results = np.array(results)
        
        # Calculate statistics
        statistics_summary = {
            "mean": float(np.mean(results)),
            "median": float(np.median(results)),
            "std_dev": float(np.std(results)),
            "variance": float(np.var(results)),
            "minimum": float(np.min(results)),
            "maximum": float(np.max(results)),
            "skewness": float(stats.skew(results)),
            "kurtosis": float(stats.kurtosis(results))
        }
        
        # Calculate percentiles
        percentiles = {
            "p5": float(np.percentile(results, 5)),
            "p10": float(np.percentile(results, 10)),
            "p25": float(np.percentile(results, 25)),
            "p50": float(np.percentile(results, 50)),
            "p75": float(np.percentile(results, 75)),
            "p90": float(np.percentile(results, 90)),
            "p95": float(np.percentile(results, 95))
        }
        
        # Risk metrics
        negative_results = results[results < 0]
        risk_metrics = {
            "probability_negative": len(negative_results) / len(results),
            "expected_shortfall_5": float(np.mean(results[results <= percentiles["p5"]])),
            "value_at_risk_5": percentiles["p5"],
            "value_at_risk_1": float(np.percentile(results, 1)),
            "coefficient_of_variation": statistics_summary["std_dev"] / abs(statistics_summary["mean"]) if statistics_summary["mean"] != 0 else float('inf')
        }
        
        logger.info(f"Monte Carlo simulation completed: Mean NPV: {statistics_summary['mean']:,.0f}")
        
        return {
            "simulation_results": results.tolist(),
            "statistics": statistics_summary,
            "percentiles": percentiles,
            "risk_metrics": risk_metrics,
            "variable_samples": {name: samples.tolist() for name, samples in variable_samples.items()},
            "num_simulations": num_simulations
        }

class ScenarioAnalyzer:
    """Performs scenario analysis"""
    
    def __init__(self, base_model_function):
        self.base_model_function = base_model_function
        
    def analyze(self, scenarios: List[SensitivityScenario], 
                base_case_result: float) -> Dict[str, Any]:
        """Analyze multiple scenarios"""
        
        scenario_results = {}
        
        for scenario in scenarios:
            # Run model with scenario adjustments
            result = self.base_model_function(scenario.variable_adjustments)
            
            scenario_results[scenario.name] = {
                "result": result,
                "difference_from_base": result - base_case_result,
                "percentage_change": ((result - base_case_result) / base_case_result * 100) if base_case_result != 0 else 0,
                "probability": scenario.probability,
                "category": scenario.category,
                "description": scenario.description,
                "variable_adjustments": scenario.variable_adjustments
            }
        
        # Calculate expected value across scenarios
        expected_value = sum(
            data["result"] * data["probability"] 
            for data in scenario_results.values()
        )
        
        return {
            "scenarios": scenario_results,
            "expected_value": expected_value,
            "best_case": max(scenario_results.values(), key=lambda x: x["result"]),
            "worst_case": min(scenario_results.values(), key=lambda x: x["result"]),
            "scenario_spread": max(s["result"] for s in scenario_results.values()) - min(s["result"] for s in scenario_results.values())
        }

class StressTester:
    """Performs stress testing analysis"""
    
    def __init__(self, base_model_function):
        self.base_model_function = base_model_function
        
    def stress_test(self, variables: List[SensitivityVariable],
                   stress_levels: List[float] = [-0.5, -0.3, -0.1, 0.1, 0.3, 0.5]) -> Dict[str, Any]:
        """Perform stress testing on individual variables and combinations"""
        
        stress_results = {}
        
        # Individual variable stress tests
        for variable in variables:
            variable_stress = {}
            
            for stress_level in stress_levels:
                adjustment = {variable.name: 1 + stress_level}
                result = self.base_model_function(adjustment)
                variable_stress[f"{stress_level*100:.0f}%"] = result
            
            stress_results[variable.name] = variable_stress
        
        # Combined stress test (worst case for all variables)
        worst_case_adjustments = {}
        for variable in variables:
            # Use worst case direction for each variable
            worst_stress = min(stress_levels) if variable.range_percent[0] < 0 else max(stress_levels)
            worst_case_adjustments[variable.name] = 1 + worst_stress
        
        worst_case_result = self.base_model_function(worst_case_adjustments)
        
        # Best case scenario
        best_case_adjustments = {}
        for variable in variables:
            best_stress = max(stress_levels) if variable.range_percent[1] > 0 else min(stress_levels)
            best_case_adjustments[variable.name] = 1 + best_stress
        
        best_case_result = self.base_model_function(best_case_adjustments)
        
        return {
            "individual_stress_tests": stress_results,
            "combined_worst_case": {
                "result": worst_case_result,
                "adjustments": worst_case_adjustments
            },
            "combined_best_case": {
                "result": best_case_result,
                "adjustments": best_case_adjustments
            },
            "stress_range": best_case_result - worst_case_result
        }

class SensitivityAnalysisTool:
    """Main sensitivity analysis tool integrating all analysis types"""
    
    def __init__(self, base_penalty_risk: float = 10000000,
                 base_implementation_cost: float = 500000,
                 base_annual_savings: float = 50000,
                 discount_rate: float = 0.08,
                 time_horizon: int = 5):
        
        self.base_penalty_risk = base_penalty_risk
        self.base_implementation_cost = base_implementation_cost
        self.base_annual_savings = base_annual_savings
        self.discount_rate = discount_rate
        self.time_horizon = time_horizon
        
        # Initialize analyzers
        self.tornado_analyzer = TornadoAnalyzer(self._financial_model)
        self.monte_carlo_simulator = MonteCarloSimulator(self._financial_model)
        self.scenario_analyzer = ScenarioAnalyzer(self._financial_model)
        self.stress_tester = StressTester(self._financial_model)
        
        # Define default variables
        self.default_variables = self._create_default_variables()
        self.default_scenarios = self._create_default_scenarios()
        
    def _financial_model(self, variable_adjustments: Dict[str, float]) -> float:
        """
        Core financial model that calculates NPV based on variable adjustments
        
        Args:
            variable_adjustments: Dict of variable_name -> adjustment_factor
        """
        
        # Apply adjustments to base values
        penalty_risk = self.base_penalty_risk * variable_adjustments.get("penalty_risk", 1.0)
        implementation_cost = self.base_implementation_cost * variable_adjustments.get("implementation_cost", 1.0)
        annual_savings = self.base_annual_savings * variable_adjustments.get("annual_savings", 1.0)
        discount_rate = self.discount_rate * variable_adjustments.get("discount_rate", 1.0)
        
        # Calculate cash flows
        cash_flows = [-implementation_cost * 0.8]  # Year 0: 80% of implementation cost
        
        remaining_cost_annual = (implementation_cost * 0.2) / self.time_horizon
        
        for year in range(1, self.time_horizon + 1):
            if year == 2:
                # Penalty avoidance in year 2
                annual_cf = penalty_risk + annual_savings - remaining_cost_annual
            else:
                annual_cf = annual_savings - remaining_cost_annual
            
            cash_flows.append(annual_cf)
        
        # Calculate NPV
        npv = 0
        for t, cf in enumerate(cash_flows):
            npv += cf / (1 + discount_rate) ** t
        
        return npv
    
    def _create_default_variables(self) -> List[SensitivityVariable]:
        """Create default sensitivity variables for DORA compliance analysis"""
        
        return [
            SensitivityVariable(
                name="penalty_risk",
                base_value=self.base_penalty_risk,
                range_percent=(-0.5, 1.0),  # -50% to +100%
                distribution=VariableDistribution(
                    name="penalty_risk_dist",
                    distribution_type="lognormal",
                    parameters={"mean": 0.0, "sigma": 0.3},
                    description="Log-normal distribution for penalty risk uncertainty"
                ),
                category="regulatory",
                description="Regulatory penalty risk exposure"
            ),
            SensitivityVariable(
                name="implementation_cost",
                base_value=self.base_implementation_cost,
                range_percent=(-0.2, 0.7),  # -20% to +70%
                distribution=VariableDistribution(
                    name="implementation_cost_dist",
                    distribution_type="normal",
                    parameters={"mean": 1.0, "std": 0.2},
                    bounds=(0.5, 2.0),
                    description="Normal distribution for implementation cost uncertainty"
                ),
                category="financial",
                description="Implementation cost variability"
            ),
            SensitivityVariable(
                name="annual_savings",
                base_value=self.base_annual_savings,
                range_percent=(-0.6, 0.8),  # -60% to +80%
                distribution=VariableDistribution(
                    name="annual_savings_dist",
                    distribution_type="beta",
                    parameters={"alpha": 2, "beta": 3, "scale": 1.4, "loc": 0.4},
                    description="Beta distribution for savings realization uncertainty"
                ),
                category="operational",
                description="Annual operational savings variability"
            ),
            SensitivityVariable(
                name="discount_rate",
                base_value=self.discount_rate,
                range_percent=(-0.3, 0.5),  # -30% to +50%
                distribution=VariableDistribution(
                    name="discount_rate_dist",
                    distribution_type="normal",
                    parameters={"mean": 1.0, "std": 0.1},
                    bounds=(0.5, 1.5),
                    description="Normal distribution for discount rate uncertainty"
                ),
                category="financial",
                description="Discount rate (WACC) variability"
            )
        ]
    
    def _create_default_scenarios(self) -> List[SensitivityScenario]:
        """Create default scenarios for analysis"""
        
        return [
            SensitivityScenario(
                name="optimistic",
                description="Best case scenario with favorable conditions",
                variable_adjustments={
                    "penalty_risk": 1.2,  # 20% higher penalty risk (more justification)
                    "implementation_cost": 0.8,  # 20% lower costs
                    "annual_savings": 1.5,  # 50% higher savings
                    "discount_rate": 0.9  # 10% lower discount rate
                },
                probability=0.2,
                category="optimistic"
            ),
            SensitivityScenario(
                name="pessimistic",
                description="Worst case scenario with adverse conditions",
                variable_adjustments={
                    "penalty_risk": 0.6,  # 40% lower penalty risk
                    "implementation_cost": 1.6,  # 60% higher costs
                    "annual_savings": 0.4,  # 60% lower savings
                    "discount_rate": 1.3  # 30% higher discount rate
                },
                probability=0.2,
                category="pessimistic"
            ),
            SensitivityScenario(
                name="base_case",
                description="Most likely scenario based on current estimates",
                variable_adjustments={
                    "penalty_risk": 1.0,
                    "implementation_cost": 1.0,
                    "annual_savings": 1.0,
                    "discount_rate": 1.0
                },
                probability=0.6,
                category="base"
            ),
            SensitivityScenario(
                name="regulatory_stress",
                description="Heightened regulatory scrutiny scenario",
                variable_adjustments={
                    "penalty_risk": 1.8,  # 80% higher penalty risk
                    "implementation_cost": 1.3,  # 30% higher implementation costs
                    "annual_savings": 0.8,  # 20% lower savings due to urgency
                    "discount_rate": 1.1  # 10% higher discount rate due to risk
                },
                probability=0.15,
                category="stress"
            ),
            SensitivityScenario(
                name="economic_downturn",
                description="Economic recession impacting costs and funding",
                variable_adjustments={
                    "penalty_risk": 1.0,  # Same penalty risk
                    "implementation_cost": 1.4,  # 40% higher costs
                    "annual_savings": 0.6,  # 40% lower savings
                    "discount_rate": 1.4  # 40% higher discount rate
                },
                probability=0.1,
                category="stress"
            )
        ]
    
    def run_comprehensive_analysis(self, 
                                 variables: Optional[List[SensitivityVariable]] = None,
                                 scenarios: Optional[List[SensitivityScenario]] = None,
                                 num_monte_carlo: int = 10000) -> Dict[str, Any]:
        """Run comprehensive sensitivity analysis including all methods"""
        
        if variables is None:
            variables = self.default_variables
        
        if scenarios is None:
            scenarios = self.default_scenarios
        
        logger.info("Starting comprehensive sensitivity analysis...")
        
        # Calculate base case
        base_case_npv = self._financial_model({})
        
        # 1. Tornado Analysis
        logger.info("Running tornado analysis...")
        tornado_results = self.tornado_analyzer.analyze(variables, base_case_npv)
        
        # 2. Monte Carlo Simulation
        logger.info("Running Monte Carlo simulation...")
        monte_carlo_results = self.monte_carlo_simulator.simulate(variables, num_monte_carlo)
        
        # 3. Scenario Analysis
        logger.info("Running scenario analysis...")
        scenario_results = self.scenario_analyzer.analyze(scenarios, base_case_npv)
        
        # 4. Stress Testing
        logger.info("Running stress tests...")
        stress_results = self.stress_tester.stress_test(variables)
        
        # Compile comprehensive results
        comprehensive_results = {
            "analysis_metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "base_case_npv": base_case_npv,
                "num_variables": len(variables),
                "num_scenarios": len(scenarios),
                "monte_carlo_iterations": num_monte_carlo
            },
            "base_assumptions": {
                "penalty_risk": self.base_penalty_risk,
                "implementation_cost": self.base_implementation_cost,
                "annual_savings": self.base_annual_savings,
                "discount_rate": self.discount_rate,
                "time_horizon": self.time_horizon
            },
            "tornado_analysis": tornado_results,
            "monte_carlo_simulation": monte_carlo_results,
            "scenario_analysis": scenario_results,
            "stress_testing": stress_results,
            "variables_analyzed": [var.to_dict() for var in variables],
            "scenarios_analyzed": [scenario.to_dict() for scenario in scenarios]
        }
        
        # Generate insights
        insights = self._generate_insights(comprehensive_results)
        comprehensive_results["insights"] = insights
        
        logger.info("Comprehensive sensitivity analysis completed")
        return comprehensive_results
    
    def _generate_insights(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable insights from sensitivity analysis results"""
        
        tornado_data = results["tornado_analysis"]["tornado_chart_data"]
        mc_stats = results["monte_carlo_simulation"]["statistics"]
        mc_risk = results["monte_carlo_simulation"]["risk_metrics"]
        scenarios = results["scenario_analysis"]["scenarios"]
        
        insights = {
            "key_risk_drivers": [],
            "decision_recommendations": [],
            "risk_assessment": {},
            "scenario_implications": []
        }
        
        # Identify key risk drivers from tornado analysis
        if tornado_data:
            top_3_drivers = tornado_data[:3]
            for driver in top_3_drivers:
                insights["key_risk_drivers"].append({
                    "variable": driver["variable"],
                    "impact_range": driver["impact_range"],
                    "sensitivity": f"{driver['sensitivity']*100:.1f}%",
                    "recommendation": f"Focus on {driver['variable']} management as it has {driver['sensitivity']*100:.1f}% impact on NPV"
                })
        
        # Risk assessment from Monte Carlo
        prob_negative = mc_risk["probability_negative"]
        if prob_negative < 0.05:
            risk_level = "LOW"
            risk_description = "Very low probability of negative returns"
        elif prob_negative < 0.2:
            risk_level = "MODERATE"
            risk_description = "Acceptable risk level with good upside potential"
        else:
            risk_level = "HIGH"
            risk_description = "Significant risk of negative returns requires mitigation"
        
        insights["risk_assessment"] = {
            "risk_level": risk_level,
            "description": risk_description,
            "probability_negative": f"{prob_negative:.1%}",
            "value_at_risk_5": f"€{mc_risk['value_at_risk_5']:,.0f}",
            "coefficient_of_variation": f"{mc_risk['coefficient_of_variation']:.2f}"
        }
        
        # Decision recommendations
        if mc_stats["mean"] > 0 and prob_negative < 0.2:
            insights["decision_recommendations"].append("STRONGLY RECOMMEND: Positive expected NPV with acceptable risk")
        elif mc_stats["mean"] > 0:
            insights["decision_recommendations"].append("RECOMMEND WITH CAUTION: Positive expected NPV but higher risk")
        else:
            insights["decision_recommendations"].append("NOT RECOMMENDED: Negative expected NPV")
        
        # Add variable-specific recommendations
        if tornado_data:
            most_sensitive = tornado_data[0]
            if most_sensitive["variable"] == "implementation_cost":
                insights["decision_recommendations"].append("Focus on cost control and vendor management")
            elif most_sensitive["variable"] == "penalty_risk":
                insights["decision_recommendations"].append("Validate penalty risk estimates with regulatory experts")
            elif most_sensitive["variable"] == "annual_savings":
                insights["decision_recommendations"].append("Develop robust business case for operational savings")
        
        # Scenario implications
        best_scenario = max(scenarios.values(), key=lambda x: x["result"])
        worst_scenario = min(scenarios.values(), key=lambda x: x["result"])
        
        insights["scenario_implications"] = [
            f"Best case ({list(scenarios.keys())[list(scenarios.values()).index(best_scenario)]}): €{best_scenario['result']:,.0f} NPV",
            f"Worst case ({list(scenarios.keys())[list(scenarios.values()).index(worst_scenario)]}): €{worst_scenario['result']:,.0f} NPV",
            f"Scenario spread: €{best_scenario['result'] - worst_scenario['result']:,.0f}"
        ]
        
        return insights

def demonstrate_sensitivity_analysis():
    """Demonstrate the Sensitivity Analysis Tool capabilities"""
    
    print("📊 DORA Compliance Sensitivity Analysis Tool")
    print("=" * 50)
    
    # Create tool with sample parameters
    tool = SensitivityAnalysisTool(
        base_penalty_risk=10_000_000,  # €10M penalty risk
        base_implementation_cost=500_000,  # €500K implementation cost
        base_annual_savings=75_000,  # €75K annual savings
        discount_rate=0.08,  # 8% discount rate
        time_horizon=5  # 5-year analysis
    )
    
    print(f"🎯 Base Case Assumptions:")
    print(f"   • Penalty Risk: €{tool.base_penalty_risk:,.0f}")
    print(f"   • Implementation Cost: €{tool.base_implementation_cost:,.0f}")
    print(f"   • Annual Savings: €{tool.base_annual_savings:,.0f}")
    print(f"   • Discount Rate: {tool.discount_rate:.1%}")
    print(f"   • Time Horizon: {tool.time_horizon} years")
    
    # Calculate base case NPV
    base_npv = tool._financial_model({})
    print(f"   • Base Case NPV: €{base_npv:,.0f}")
    
    print(f"\n🔬 Running Comprehensive Sensitivity Analysis...")
    
    # Run comprehensive analysis
    results = tool.run_comprehensive_analysis(num_monte_carlo=5000)  # Reduced for demo
    
    print(f"✅ Analysis Complete!")
    
    # Display tornado analysis results
    print(f"\n🌪️  Tornado Analysis (Top 3 Variables):")
    tornado_data = results["tornado_analysis"]["tornado_chart_data"][:3]
    for i, item in enumerate(tornado_data, 1):
        print(f"   {i}. {item['variable'].replace('_', ' ').title()}")
        print(f"      • Impact Range: €{item['impact_range']:,.0f}")
        print(f"      • Sensitivity: {item['sensitivity']*100:.1f}%")
    
    # Display Monte Carlo results
    mc_stats = results["monte_carlo_simulation"]["statistics"]
    mc_risk = results["monte_carlo_simulation"]["risk_metrics"]
    print(f"\n🎲 Monte Carlo Simulation Results:")
    print(f"   • Mean NPV: €{mc_stats['mean']:,.0f}")
    print(f"   • Standard Deviation: €{mc_stats['std_dev']:,.0f}")
    print(f"   • 5th Percentile: €{mc_stats['median']:,.0f}")
    print(f"   • 95th Percentile: €{results['monte_carlo_simulation']['percentiles']['p95']:,.0f}")
    print(f"   • Probability of Loss: {mc_risk['probability_negative']:.1%}")
    print(f"   • Value at Risk (5%): €{mc_risk['value_at_risk_5']:,.0f}")
    
    # Display scenario analysis
    scenarios = results["scenario_analysis"]["scenarios"]
    print(f"\n📋 Scenario Analysis:")
    for name, data in scenarios.items():
        print(f"   • {name.replace('_', ' ').title()}: €{data['result']:,.0f} NPV ({data['percentage_change']:+.1f}% vs base)")
    
    # Display key insights
    insights = results["insights"]
    print(f"\n💡 Key Insights:")
    print(f"   Risk Assessment: {insights['risk_assessment']['risk_level']} - {insights['risk_assessment']['description']}")
    
    print(f"\n🎯 Top Risk Drivers:")
    for driver in insights["key_risk_drivers"]:
        print(f"   • {driver['variable'].replace('_', ' ').title()}: {driver['sensitivity']} sensitivity")
    
    print(f"\n📈 Recommendations:")
    for rec in insights["decision_recommendations"]:
        print(f"   • {rec}")
    
    print(f"\n✅ Sensitivity Analysis Tool Demonstration Complete!")

if __name__ == "__main__":
    demonstrate_sensitivity_analysis() 