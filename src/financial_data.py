#!/usr/bin/env python3
"""
Financial Data Integration Module

Handles integration with financial data sources, revenue information,
and company profile data for DORA penalty calculations and business case generation.

Author: DORA Compliance System
Date: 2025-01-23
"""

import json
import csv
import logging
from typing import Dict, List, Optional, Union, Tuple
from decimal import Decimal
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import re

from .penalty_models import CompanySize, RiskFactors, create_default_risk_factors


class DataSource(Enum):
    """Available financial data sources"""
    MANUAL_INPUT = "manual_input"
    CSV_FILE = "csv_file"
    JSON_FILE = "json_file"
    API_ENDPOINT = "api_endpoint"
    DATABASE = "database"


class Currency(Enum):
    """Supported currencies for financial data"""
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"
    CHF = "CHF"


@dataclass
class FinancialProfile:
    """Company financial profile for penalty calculations"""
    
    # Basic company information
    company_name: str
    company_id: Optional[str] = None
    industry_sector: Optional[str] = None
    country_of_incorporation: str = "EU"
    
    # Financial metrics (in EUR)
    annual_revenue: Decimal = Decimal('0')
    total_assets: Optional[Decimal] = None
    market_capitalization: Optional[Decimal] = None
    operating_income: Optional[Decimal] = None
    
    # Additional context
    fiscal_year_end: Optional[str] = None
    reporting_currency: Currency = Currency.EUR
    revenue_growth_rate: Optional[float] = None
    
    # Risk profile indicators
    regulatory_capital_ratio: Optional[float] = None
    credit_rating: Optional[str] = None
    systemic_importance: bool = False
    
    # Metadata
    data_source: DataSource = DataSource.MANUAL_INPUT
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class CostEstimate:
    """Cost estimation for compliance implementations"""
    
    category: str
    description: str
    estimated_cost_eur: Decimal
    confidence_level: float = 0.7  # 0.0 to 1.0
    timeline_months: int = 12
    cost_type: str = "one_time"  # "one_time", "recurring", "mixed"
    
    # Cost breakdown
    internal_resources_pct: float = 0.5
    external_services_pct: float = 0.3
    technology_pct: float = 0.2
    
    # Risk factors
    cost_variance_pct: float = 0.2  # Expected variance (+/-)
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class FinancialDataManager:
    """Manager for financial data integration and processing"""
    
    # Exchange rates (simplified - in production would integrate with live API)
    EXCHANGE_RATES = {
        Currency.USD: Decimal('0.92'),  # USD to EUR
        Currency.GBP: Decimal('1.17'),  # GBP to EUR
        Currency.CHF: Decimal('1.08'),  # CHF to EUR
        Currency.EUR: Decimal('1.00')   # EUR to EUR
    }
    
    # Industry benchmarks for cost estimation (€ per employee)
    INDUSTRY_COST_BENCHMARKS = {
        "banking": {
            "base_compliance_cost": 25000,
            "technology_multiplier": 1.5,
            "complexity_multiplier": 2.0
        },
        "insurance": {
            "base_compliance_cost": 20000,
            "technology_multiplier": 1.3,
            "complexity_multiplier": 1.8
        },
        "investment_services": {
            "base_compliance_cost": 30000,
            "technology_multiplier": 1.8,
            "complexity_multiplier": 2.2
        },
        "payment_services": {
            "base_compliance_cost": 15000,
            "technology_multiplier": 1.4,
            "complexity_multiplier": 1.5
        },
        "crypto_services": {
            "base_compliance_cost": 35000,
            "technology_multiplier": 2.0,
            "complexity_multiplier": 2.5
        },
        "other": {
            "base_compliance_cost": 20000,
            "technology_multiplier": 1.2,
            "complexity_multiplier": 1.5
        }
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.profiles_cache = {}
    
    def create_financial_profile(
        self,
        company_name: str,
        annual_revenue: Union[Decimal, float, str],
        revenue_currency: Currency = Currency.EUR,
        **kwargs
    ) -> FinancialProfile:
        """
        Create a financial profile from basic inputs
        
        Args:
            company_name: Name of the company
            annual_revenue: Annual revenue amount
            revenue_currency: Currency of the revenue figure
            **kwargs: Additional profile parameters
            
        Returns:
            FinancialProfile object
        """
        
        # Convert revenue to Decimal and EUR
        revenue_decimal = self._to_decimal(annual_revenue)
        revenue_eur = self._convert_to_eur(revenue_decimal, revenue_currency)
        
        # Create profile
        profile = FinancialProfile(
            company_name=company_name,
            annual_revenue=revenue_eur,
            reporting_currency=revenue_currency,
            **kwargs
        )
        
        # Cache the profile
        self.profiles_cache[company_name] = profile
        
        return profile
    
    def load_financial_profile_from_json(self, file_path: str) -> FinancialProfile:
        """Load financial profile from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert revenue to Decimal
            if 'annual_revenue' in data:
                data['annual_revenue'] = Decimal(str(data['annual_revenue']))
            
            # Convert currency enum
            if 'reporting_currency' in data:
                data['reporting_currency'] = Currency(data['reporting_currency'])
            
            # Convert data source enum
            if 'data_source' in data:
                data['data_source'] = DataSource(data['data_source'])
            
            # Parse datetime
            if 'last_updated' in data and isinstance(data['last_updated'], str):
                data['last_updated'] = datetime.fromisoformat(data['last_updated'])
            
            profile = FinancialProfile(**data)
            self.profiles_cache[profile.company_name] = profile
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error loading financial profile from {file_path}: {e}")
            raise
    
    def save_financial_profile_to_json(self, profile: FinancialProfile, file_path: str):
        """Save financial profile to JSON file"""
        try:
            # Convert to dict and handle special types
            data = asdict(profile)
            
            # Convert Decimal to string
            if 'annual_revenue' in data:
                data['annual_revenue'] = str(data['annual_revenue'])
            
            # Convert enums to values
            if 'reporting_currency' in data:
                data['reporting_currency'] = data['reporting_currency'].value
            
            if 'data_source' in data:
                data['data_source'] = data['data_source'].value
            
            # Convert datetime to ISO string
            if 'last_updated' in data and data['last_updated']:
                data['last_updated'] = data['last_updated'].isoformat()
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error saving financial profile to {file_path}: {e}")
            raise
    
    def determine_company_size(self, annual_revenue: Decimal) -> CompanySize:
        """Determine company size category based on revenue"""
        revenue_millions = float(annual_revenue) / 1_000_000
        
        if revenue_millions < 50:
            return CompanySize.SMALL
        elif revenue_millions < 500:
            return CompanySize.MEDIUM
        elif revenue_millions < 5000:
            return CompanySize.LARGE
        else:
            return CompanySize.SYSTEMIC
    
    def estimate_employee_count(self, annual_revenue: Decimal, industry: str = "other") -> int:
        """Estimate employee count based on revenue and industry"""
        revenue_millions = float(annual_revenue) / 1_000_000
        
        # Industry-specific revenue per employee (in thousands)
        revenue_per_employee = {
            "banking": 500,
            "insurance": 400,
            "investment_services": 800,
            "payment_services": 300,
            "crypto_services": 1000,
            "other": 400
        }
        
        multiplier = revenue_per_employee.get(industry, 400)
        estimated_employees = int(revenue_millions * 1000 / multiplier)
        
        return max(estimated_employees, 10)  # Minimum 10 employees
    
    def estimate_compliance_cost(
        self,
        profile: FinancialProfile,
        gap_categories: List[str],
        complexity_factor: float = 1.0
    ) -> List[CostEstimate]:
        """
        Estimate compliance implementation costs based on company profile and gaps
        
        Args:
            profile: Company financial profile
            gap_categories: List of compliance gap categories
            complexity_factor: Adjustment factor for implementation complexity
            
        Returns:
            List of cost estimates by category
        """
        
        industry = profile.industry_sector or "other"
        employee_count = self.estimate_employee_count(profile.annual_revenue, industry)
        
        # Get industry benchmarks
        benchmarks = self.INDUSTRY_COST_BENCHMARKS.get(industry, 
                                                       self.INDUSTRY_COST_BENCHMARKS["other"])
        
        cost_estimates = []
        
        # Cost estimation by gap category
        category_costs = {
            "ICT Governance": {
                "base_cost": benchmarks["base_compliance_cost"] * 0.3,
                "timeline": 6,
                "description": "ICT governance framework implementation"
            },
            "Risk Management": {
                "base_cost": benchmarks["base_compliance_cost"] * 0.4,
                "timeline": 8,
                "description": "ICT risk management tools and processes"
            },
            "Incident Management": {
                "base_cost": benchmarks["base_compliance_cost"] * 0.25,
                "timeline": 4,
                "description": "Incident management system implementation"
            },
            "Testing & Resilience": {
                "base_cost": benchmarks["base_compliance_cost"] * 0.5,
                "timeline": 12,
                "description": "Digital operational resilience testing programme"
            },
            "Third-Party Risk": {
                "base_cost": benchmarks["base_compliance_cost"] * 0.35,
                "timeline": 6,
                "description": "Third-party risk management framework"
            },
            "Information Sharing": {
                "base_cost": benchmarks["base_compliance_cost"] * 0.15,
                "timeline": 3,
                "description": "Threat information sharing capabilities"
            }
        }
        
        for category in gap_categories:
            if category in category_costs:
                category_info = category_costs[category]
                
                # Calculate base cost per employee
                base_cost_per_employee = category_info["base_cost"]
                
                # Apply multipliers
                total_cost = (
                    base_cost_per_employee * 
                    employee_count * 
                    benchmarks["complexity_multiplier"] * 
                    complexity_factor
                )
                
                # Add technology costs for certain categories
                if category in ["Risk Management", "Testing & Resilience", "Incident Management"]:
                    total_cost *= benchmarks["technology_multiplier"]
                
                cost_estimate = CostEstimate(
                    category=category,
                    description=category_info["description"],
                    estimated_cost_eur=Decimal(str(int(total_cost))),
                    timeline_months=category_info["timeline"],
                    confidence_level=0.7,
                    cost_variance_pct=0.3,
                    internal_resources_pct=0.6,
                    external_services_pct=0.25,
                    technology_pct=0.15
                )
                
                cost_estimates.append(cost_estimate)
        
        return cost_estimates
    
    def calculate_roi_metrics(
        self,
        implementation_cost: Decimal,
        potential_penalty: Decimal,
        annual_operational_savings: Decimal = Decimal('0'),
        discount_rate: float = 0.08,
        time_horizon_years: int = 5
    ) -> Dict[str, Union[Decimal, float]]:
        """
        Calculate ROI metrics for compliance investment
        
        Args:
            implementation_cost: One-time implementation cost
            potential_penalty: Potential annual penalty avoided
            annual_operational_savings: Annual operational cost savings
            discount_rate: Discount rate for NPV calculation
            time_horizon_years: Analysis time horizon
            
        Returns:
            Dictionary containing ROI metrics
        """
        
        # Calculate annual benefits
        annual_benefits = potential_penalty + annual_operational_savings
        
        # Simple payback period
        payback_years = float(implementation_cost / annual_benefits) if annual_benefits > 0 else float('inf')
        
        # NPV calculation - convert discount_rate to Decimal for consistent arithmetic
        discount_rate_decimal = Decimal(str(discount_rate))
        npv = -implementation_cost  # Initial investment
        for year in range(1, time_horizon_years + 1):
            discounted_benefit = annual_benefits / ((Decimal('1') + discount_rate_decimal) ** year)
            npv += discounted_benefit
        
        # IRR calculation (simplified approximation)
        if annual_benefits > 0 and implementation_cost > 0:
            irr = float((annual_benefits / implementation_cost) - Decimal('1'))
        else:
            irr = -1.0
        
        # ROI calculation
        total_benefits = annual_benefits * time_horizon_years
        if implementation_cost > 0:
            roi = float((total_benefits - implementation_cost) / implementation_cost)
            benefit_cost_ratio = float(total_benefits / implementation_cost)
        else:
            roi = 0.0
            benefit_cost_ratio = 0.0
        
        return {
            "implementation_cost_eur": implementation_cost,
            "annual_benefits_eur": annual_benefits,
            "payback_period_years": payback_years,
            "net_present_value_eur": npv,
            "internal_rate_of_return": irr,
            "return_on_investment": roi,
            "total_savings_eur": total_benefits - implementation_cost,
            "benefit_cost_ratio": benefit_cost_ratio
        }
    
    def _to_decimal(self, value: Union[Decimal, float, str]) -> Decimal:
        """Convert various number types to Decimal"""
        if isinstance(value, Decimal):
            return value
        elif isinstance(value, (int, float)):
            return Decimal(str(value))
        elif isinstance(value, str):
            # Clean string (remove currency symbols, commas, etc.)
            cleaned = re.sub(r'[€$£,\s]', '', value)
            return Decimal(cleaned)
        else:
            raise ValueError(f"Cannot convert {type(value)} to Decimal")
    
    def _convert_to_eur(self, amount: Decimal, from_currency: Currency) -> Decimal:
        """Convert amount from specified currency to EUR"""
        if from_currency == Currency.EUR:
            return amount
        
        exchange_rate = self.EXCHANGE_RATES.get(from_currency, Decimal('1.0'))
        return amount * exchange_rate


def create_demo_financial_profile() -> FinancialProfile:
    """Create a demo financial profile for testing"""
    return FinancialProfile(
        company_name="Demo Financial Institution",
        company_id="DEMO-001",
        industry_sector="banking",
        country_of_incorporation="EU",
        annual_revenue=Decimal('500_000_000'),  # €500M
        total_assets=Decimal('5_000_000_000'),   # €5B
        operating_income=Decimal('75_000_000'),  # €75M
        fiscal_year_end="2024-12-31",
        reporting_currency=Currency.EUR,
        revenue_growth_rate=0.08,
        regulatory_capital_ratio=0.15,
        credit_rating="A+",
        systemic_importance=False,
        data_source=DataSource.MANUAL_INPUT
    )


if __name__ == "__main__":
    # Example usage
    manager = FinancialDataManager()
    
    # Create demo profile
    profile = create_demo_financial_profile()
    
    # Estimate costs
    gap_categories = ["Risk Management", "Testing & Resilience", "Incident Management"]
    cost_estimates = manager.estimate_compliance_cost(profile, gap_categories, complexity_factor=1.2)
    
    print("Financial Profile:")
    print(f"Company: {profile.company_name}")
    print(f"Revenue: €{profile.annual_revenue:,.2f}")
    print(f"Size: {manager.determine_company_size(profile.annual_revenue).value}")
    print()
    
    print("Cost Estimates:")
    total_cost = Decimal('0')
    for estimate in cost_estimates:
        print(f"{estimate.category}: €{estimate.estimated_cost_eur:,.2f} ({estimate.timeline_months} months)")
        total_cost += estimate.estimated_cost_eur
    
    print(f"Total Implementation Cost: €{total_cost:,.2f}")
    
    # Calculate ROI
    potential_penalty = Decimal('10_000_000')  # €10M potential penalty
    roi_metrics = manager.calculate_roi_metrics(total_cost, potential_penalty)
    
    print(f"\nROI Analysis:")
    print(f"Payback Period: {roi_metrics['payback_period_years']:.1f} years")
    print(f"NPV: €{roi_metrics['net_present_value_eur']:,.2f}")
    print(f"ROI: {roi_metrics['return_on_investment']:.1%}") 