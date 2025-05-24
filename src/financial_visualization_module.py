#!/usr/bin/env python3
"""
DORA Compliance Financial Impact Visualization Module

This module creates interactive visualizations and dashboards for DORA compliance
financial analysis, including penalty risks, implementation costs, ROI projections,
and comprehensive scenario comparisons with export capabilities.

Author: DORA Compliance System
Created: 2025-05-24
"""

import json
import logging
import os
import base64
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import math
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChartType(Enum):
    """Supported chart types"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    SCATTER = "scatter"
    WATERFALL = "waterfall"
    GAUGE = "gauge"
    TREE_MAP = "treemap"
    HEAT_MAP = "heatmap"

class VisualizationLevel(Enum):
    """Target audience visualization levels"""
    EXECUTIVE = "executive"     # High-level, strategic charts
    ANALYTICAL = "analytical"   # Detailed analysis charts
    TECHNICAL = "technical"     # Comprehensive technical charts

class ExportFormat(Enum):
    """Supported export formats"""
    HTML = "html"
    SVG = "svg"
    PNG = "png"
    PDF = "pdf"
    JSON = "json"

@dataclass
class ChartConfig:
    """Configuration for individual charts"""
    title: str
    chart_type: ChartType
    width: int = 800
    height: int = 400
    show_legend: bool = True
    show_grid: bool = True
    color_scheme: str = "corporate"
    animation: bool = True
    responsive: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['chart_type'] = self.chart_type.value
        return result

@dataclass
class DashboardConfig:
    """Configuration for dashboard layout"""
    title: str
    layout: str = "grid"  # "grid", "tabs", "accordion"
    columns: int = 2
    theme: str = "light"
    export_enabled: bool = True
    interactive: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ColorSchemes:
    """Predefined color schemes for visualizations"""
    
    CORPORATE = {
        "primary": "#2c3e50",
        "secondary": "#3498db", 
        "success": "#27ae60",
        "warning": "#f39c12",
        "danger": "#e74c3c",
        "info": "#17a2b8",
        "light": "#f8f9fa",
        "dark": "#343a40"
    }
    
    FINANCIAL = {
        "profit": "#27ae60",
        "loss": "#e74c3c", 
        "neutral": "#6c757d",
        "investment": "#3498db",
        "savings": "#28a745",
        "cost": "#dc3545",
        "penalty": "#ff6b6b",
        "roi": "#20c997"
    }
    
    RISK = {
        "critical": "#dc3545",
        "high": "#fd7e14",
        "medium": "#ffc107", 
        "low": "#28a745",
        "very_low": "#17a2b8"
    }

class ChartGenerator:
    """Generates individual chart visualizations"""
    
    def __init__(self, color_scheme: str = "corporate"):
        self.color_scheme = getattr(ColorSchemes, color_scheme.upper(), ColorSchemes.CORPORATE)
        
    def generate_penalty_risk_chart(self, penalty_data: Dict[str, Any], config: ChartConfig) -> Dict[str, Any]:
        """Generate penalty risk visualization"""
        
        max_penalty = penalty_data.get('maximum_penalty_risk', 0)
        expected_penalty = penalty_data.get('expected_annual_penalty', 0)
        
        chart_data = {
            "type": config.chart_type.value,
            "title": config.title,
            "data": {
                "labels": ["Maximum Penalty Risk", "Expected Annual Penalty", "Risk-Free Scenario"],
                "datasets": [{
                    "label": "Penalty Exposure (€)",
                    "data": [max_penalty, expected_penalty, 0],
                    "backgroundColor": [
                        ColorSchemes.FINANCIAL["penalty"],
                        ColorSchemes.FINANCIAL["cost"], 
                        ColorSchemes.FINANCIAL["profit"]
                    ],
                    "borderColor": "#ffffff",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": config.responsive,
                "plugins": {
                    "legend": {"display": config.show_legend},
                    "title": {"display": True, "text": config.title}
                },
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "grid": {"display": config.show_grid},
                        "ticks": {
                            "callback": "function(value) { return '€' + value.toLocaleString(); }"
                        }
                    }
                }
            },
            "config": config.to_dict()
        }
        
        return chart_data
    
    def generate_roi_timeline_chart(self, roi_data: Dict[str, Any], cash_flows: List[Dict[str, Any]], config: ChartConfig) -> Dict[str, Any]:
        """Generate ROI timeline visualization"""
        
        # Process cash flows for timeline
        years = []
        cumulative_cash_flows = []
        annual_cash_flows = []
        cumulative = 0
        
        # Group cash flows by year
        cash_flow_by_year = {}
        for cf in cash_flows:
            year = cf.get('year', 0)
            amount = cf.get('amount', 0)
            if year not in cash_flow_by_year:
                cash_flow_by_year[year] = 0
            cash_flow_by_year[year] += amount
        
        # Generate timeline data
        for year in sorted(cash_flow_by_year.keys()):
            years.append(f"Year {year}")
            annual_amount = cash_flow_by_year[year]
            annual_cash_flows.append(annual_amount)
            cumulative += annual_amount
            cumulative_cash_flows.append(cumulative)
        
        chart_data = {
            "type": "line",
            "title": config.title,
            "data": {
                "labels": years,
                "datasets": [
                    {
                        "label": "Annual Cash Flow (€)",
                        "data": annual_cash_flows,
                        "borderColor": ColorSchemes.FINANCIAL["investment"],
                        "backgroundColor": ColorSchemes.FINANCIAL["investment"] + "20",
                        "yAxisID": "y"
                    },
                    {
                        "label": "Cumulative Cash Flow (€)",
                        "data": cumulative_cash_flows,
                        "borderColor": ColorSchemes.FINANCIAL["profit"],
                        "backgroundColor": ColorSchemes.FINANCIAL["profit"] + "20",
                        "yAxisID": "y1"
                    }
                ]
            },
            "options": {
                "responsive": config.responsive,
                "interaction": {"intersect": False},
                "plugins": {
                    "legend": {"display": config.show_legend},
                    "title": {"display": True, "text": config.title}
                },
                "scales": {
                    "y": {
                        "type": "linear",
                        "display": True,
                        "position": "left",
                        "grid": {"display": config.show_grid},
                        "ticks": {
                            "callback": "function(value) { return '€' + value.toLocaleString(); }"
                        }
                    },
                    "y1": {
                        "type": "linear",
                        "display": True,
                        "position": "right",
                        "grid": {"drawOnChartArea": False},
                        "ticks": {
                            "callback": "function(value) { return '€' + value.toLocaleString(); }"
                        }
                    }
                }
            },
            "config": config.to_dict()
        }
        
        return chart_data
    
    def generate_cost_breakdown_chart(self, cost_data: Dict[str, Any], config: ChartConfig) -> Dict[str, Any]:
        """Generate implementation cost breakdown visualization"""
        
        cost_breakdown = cost_data.get('cost_breakdown', {})
        
        # Prepare data for pie/donut chart
        labels = []
        values = []
        colors = []
        
        color_map = {
            "software": ColorSchemes.FINANCIAL["investment"],
            "hardware": ColorSchemes.FINANCIAL["cost"],
            "personnel": ColorSchemes.FINANCIAL["neutral"],
            "training": "#9b59b6",
            "consulting": "#e67e22",
            "licensing": "#1abc9c",
            "maintenance": "#34495e",
            "other": "#95a5a6"
        }
        
        for category, amount in cost_breakdown.items():
            if amount > 0:
                labels.append(category.replace('_', ' ').title())
                values.append(float(amount))
                colors.append(color_map.get(category.lower(), "#95a5a6"))
        
        chart_data = {
            "type": config.chart_type.value,
            "title": config.title,
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": values,
                    "backgroundColor": colors,
                    "borderColor": "#ffffff",
                    "borderWidth": 2,
                    "hoverOffset": 4
                }]
            },
            "options": {
                "responsive": config.responsive,
                "plugins": {
                    "legend": {
                        "display": config.show_legend,
                        "position": "right"
                    },
                    "title": {"display": True, "text": config.title},
                    "tooltip": {
                        "callbacks": {
                            "label": "function(context) { return context.label + ': €' + context.parsed.toLocaleString(); }"
                        }
                    }
                }
            },
            "config": config.to_dict()
        }
        
        return chart_data
    
    def generate_sensitivity_analysis_chart(self, sensitivity_data: Dict[str, Any], config: ChartConfig) -> Dict[str, Any]:
        """Generate sensitivity analysis tornado chart"""
        
        tornado_data = sensitivity_data.get('tornado_chart_data', [])
        
        # Prepare data for horizontal bar chart
        labels = []
        negative_impacts = []
        positive_impacts = []
        
        for item in sorted(tornado_data, key=lambda x: x.get('impact_range', 0), reverse=True):
            variable = item.get('variable', '').replace('_', ' ').title()
            min_npv = item.get('min_npv', 0)
            max_npv = item.get('max_npv', 0)
            base_npv = sensitivity_data.get('base_case', {}).get('npv', 0)
            
            labels.append(variable)
            negative_impacts.append(min_npv - base_npv)
            positive_impacts.append(max_npv - base_npv)
        
        chart_data = {
            "type": "bar",
            "title": config.title,
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Negative Impact",
                        "data": negative_impacts,
                        "backgroundColor": ColorSchemes.FINANCIAL["loss"],
                        "borderColor": ColorSchemes.FINANCIAL["loss"],
                        "borderWidth": 1
                    },
                    {
                        "label": "Positive Impact", 
                        "data": positive_impacts,
                        "backgroundColor": ColorSchemes.FINANCIAL["profit"],
                        "borderColor": ColorSchemes.FINANCIAL["profit"],
                        "borderWidth": 1
                    }
                ]
            },
            "options": {
                "indexAxis": "y",
                "responsive": config.responsive,
                "plugins": {
                    "legend": {"display": config.show_legend},
                    "title": {"display": True, "text": config.title}
                },
                "scales": {
                    "x": {
                        "stacked": True,
                        "grid": {"display": config.show_grid},
                        "ticks": {
                            "callback": "function(value) { return '€' + value.toLocaleString(); }"
                        }
                    },
                    "y": {
                        "stacked": True
                    }
                }
            },
            "config": config.to_dict()
        }
        
        return chart_data
    
    def generate_scenario_comparison_chart(self, scenario_data: Dict[str, Any], config: ChartConfig) -> Dict[str, Any]:
        """Generate scenario comparison visualization"""
        
        scenarios = scenario_data.get('scenario_analysis', {})
        
        scenario_names = []
        benefits = []
        costs = []
        npvs = []
        
        for scenario_name, data in scenarios.items():
            scenario_names.append(scenario_name.replace('_', ' ').title())
            benefits.append(data.get('benefits', 0))
            costs.append(data.get('costs', 0))
            npvs.append(data.get('npv', 0))
        
        chart_data = {
            "type": "bar",
            "title": config.title,
            "data": {
                "labels": scenario_names,
                "datasets": [
                    {
                        "label": "Benefits (€)",
                        "data": benefits,
                        "backgroundColor": ColorSchemes.FINANCIAL["profit"],
                        "yAxisID": "y"
                    },
                    {
                        "label": "Costs (€)",
                        "data": costs,
                        "backgroundColor": ColorSchemes.FINANCIAL["cost"],
                        "yAxisID": "y"
                    },
                    {
                        "label": "NPV (€)",
                        "data": npvs,
                        "type": "line",
                        "borderColor": ColorSchemes.FINANCIAL["roi"],
                        "backgroundColor": ColorSchemes.FINANCIAL["roi"] + "20",
                        "yAxisID": "y1"
                    }
                ]
            },
            "options": {
                "responsive": config.responsive,
                "plugins": {
                    "legend": {"display": config.show_legend},
                    "title": {"display": True, "text": config.title}
                },
                "scales": {
                    "y": {
                        "type": "linear",
                        "display": True,
                        "position": "left",
                        "grid": {"display": config.show_grid},
                        "ticks": {
                            "callback": "function(value) { return '€' + value.toLocaleString(); }"
                        }
                    },
                    "y1": {
                        "type": "linear",
                        "display": True,
                        "position": "right",
                        "grid": {"drawOnChartArea": False},
                        "ticks": {
                            "callback": "function(value) { return '€' + value.toLocaleString(); }"
                        }
                    }
                }
            },
            "config": config.to_dict()
        }
        
        return chart_data
    
    def generate_risk_assessment_gauge(self, risk_data: Dict[str, Any], config: ChartConfig) -> Dict[str, Any]:
        """Generate risk assessment gauge chart"""
        
        probability_positive = risk_data.get('probability_positive_npv', 0) * 100
        
        chart_data = {
            "type": "doughnut",
            "title": config.title,
            "data": {
                "labels": ["Success Probability", "Risk"],
                "datasets": [{
                    "data": [probability_positive, 100 - probability_positive],
                    "backgroundColor": [
                        ColorSchemes.FINANCIAL["profit"],
                        ColorSchemes.FINANCIAL["loss"]
                    ],
                    "borderWidth": 0,
                    "cutout": "70%"
                }]
            },
            "options": {
                "responsive": config.responsive,
                "plugins": {
                    "legend": {"display": config.show_legend},
                    "title": {"display": True, "text": config.title},
                    "tooltip": {
                        "callbacks": {
                            "label": "function(context) { return context.label + ': ' + context.parsed + '%'; }"
                        }
                    }
                }
            },
            "config": config.to_dict()
        }
        
        return chart_data

class DashboardGenerator:
    """Generates comprehensive financial impact dashboards"""
    
    def __init__(self, visualization_level: VisualizationLevel = VisualizationLevel.ANALYTICAL):
        self.visualization_level = visualization_level
        self.chart_generator = ChartGenerator()
        
    def generate_executive_dashboard(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive-level dashboard"""
        
        config = DashboardConfig(
            title="DORA Compliance Financial Impact Dashboard",
            layout="grid",
            columns=2,
            theme="light"
        )
        
        # Generate key charts for executives
        charts = []
        
        # 1. Penalty Risk Overview
        penalty_config = ChartConfig(
            title="Regulatory Penalty Risk",
            chart_type=ChartType.BAR,
            width=600,
            height=300
        )
        penalty_chart = self.chart_generator.generate_penalty_risk_chart(
            financial_data.get('penalty_analysis', {}), penalty_config
        )
        charts.append(penalty_chart)
        
        # 2. ROI Summary
        roi_config = ChartConfig(
            title="Return on Investment Timeline",
            chart_type=ChartType.LINE,
            width=600,
            height=300
        )
        roi_chart = self.chart_generator.generate_roi_timeline_chart(
            financial_data.get('advanced_roi_analysis', {}),
            financial_data.get('cash_flow_analysis', {}).get('detailed_cash_flows', []),
            roi_config
        )
        charts.append(roi_chart)
        
        # 3. Investment Breakdown
        cost_config = ChartConfig(
            title="Implementation Investment Breakdown",
            chart_type=ChartType.PIE,
            width=600,
            height=300
        )
        cost_chart = self.chart_generator.generate_cost_breakdown_chart(
            financial_data.get('implementation_cost', {}), cost_config
        )
        charts.append(cost_chart)
        
        # 4. Risk Assessment
        risk_config = ChartConfig(
            title="Investment Success Probability",
            chart_type=ChartType.DONUT,
            width=600,
            height=300
        )
        risk_chart = self.chart_generator.generate_risk_assessment_gauge(
            financial_data.get('risk_metrics', {}), risk_config
        )
        charts.append(risk_chart)
        
        # Generate key metrics summary
        roi_data = financial_data.get('advanced_roi_analysis', {})
        penalty_data = financial_data.get('penalty_analysis', {})
        
        key_metrics = {
            "max_penalty_risk": f"€{penalty_data.get('maximum_penalty_risk', 0):,.0f}",
            "implementation_cost": f"€{financial_data.get('implementation_cost', {}).get('total_cost', 0):,.0f}",
            "roi_percentage": f"{roi_data.get('roi_percentage', 0):.0f}%",
            "npv": f"€{roi_data.get('npv', 0):,.0f}",
            "payback_period": f"{roi_data.get('payback_period_years', 0):.1f} years",
            "recommendation": financial_data.get('investment_recommendation', {}).get('recommendation', 'ANALYZE')
        }
        
        dashboard = {
            "config": config.to_dict(),
            "charts": charts,
            "key_metrics": key_metrics,
            "summary": {
                "total_charts": len(charts),
                "dashboard_type": "executive",
                "generation_timestamp": datetime.now().isoformat()
            }
        }
        
        return dashboard
    
    def generate_analytical_dashboard(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analytical-level dashboard with detailed analysis"""
        
        config = DashboardConfig(
            title="DORA Compliance Detailed Financial Analysis",
            layout="tabs",
            columns=2,
            theme="light"
        )
        
        charts = []
        
        # Include all executive charts plus detailed analysis
        executive_dashboard = self.generate_executive_dashboard(financial_data)
        charts.extend(executive_dashboard['charts'])
        
        # Add sensitivity analysis
        if 'sensitivity_analysis' in financial_data and financial_data['sensitivity_analysis']:
            sensitivity_config = ChartConfig(
                title="Sensitivity Analysis - Impact on NPV",
                chart_type=ChartType.BAR,
                width=800,
                height=400
            )
            sensitivity_chart = self.chart_generator.generate_sensitivity_analysis_chart(
                financial_data['sensitivity_analysis'], sensitivity_config
            )
            charts.append(sensitivity_chart)
            
            # Add scenario comparison
            scenario_config = ChartConfig(
                title="Scenario Analysis Comparison",
                chart_type=ChartType.BAR,
                width=800,
                height=400
            )
            scenario_chart = self.chart_generator.generate_scenario_comparison_chart(
                financial_data['sensitivity_analysis'], scenario_config
            )
            charts.append(scenario_chart)
        
        dashboard = {
            "config": config.to_dict(),
            "charts": charts,
            "key_metrics": executive_dashboard['key_metrics'],
            "detailed_analysis": {
                "cash_flow_summary": financial_data.get('cash_flow_analysis', {}).get('cash_flow_summary', {}),
                "risk_metrics": financial_data.get('risk_metrics', {}),
                "sensitivity_insights": self._generate_sensitivity_insights(financial_data.get('sensitivity_analysis', {}))
            },
            "summary": {
                "total_charts": len(charts),
                "dashboard_type": "analytical",
                "generation_timestamp": datetime.now().isoformat()
            }
        }
        
        return dashboard
    
    def _generate_sensitivity_insights(self, sensitivity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from sensitivity analysis"""
        
        if not sensitivity_data:
            return {}
            
        tornado_data = sensitivity_data.get('tornado_chart_data', [])
        
        insights = {
            "most_impactful_variable": "",
            "least_impactful_variable": "",
            "key_risks": [],
            "optimization_opportunities": []
        }
        
        if tornado_data:
            # Sort by impact range
            sorted_data = sorted(tornado_data, key=lambda x: x.get('impact_range', 0), reverse=True)
            
            if sorted_data:
                insights["most_impactful_variable"] = sorted_data[0].get('variable', '').replace('_', ' ').title()
                insights["least_impactful_variable"] = sorted_data[-1].get('variable', '').replace('_', ' ').title()
                
                # Identify key risks (high impact variables)
                for item in sorted_data[:3]:  # Top 3 most impactful
                    variable = item.get('variable', '').replace('_', ' ').title()
                    impact = item.get('impact_range', 0)
                    insights["key_risks"].append(f"{variable}: €{impact:,.0f} impact range")
                
                # Identify optimization opportunities
                for item in sorted_data:
                    if item.get('min_npv', 0) > item.get('max_npv', 0):  # Variables that could improve NPV
                        variable = item.get('variable', '').replace('_', ' ').title()
                        insights["optimization_opportunities"].append(f"Focus on {variable} optimization")
        
        return insights

class FinancialVisualizationModule:
    """Main module orchestrating financial impact visualizations"""
    
    def __init__(self, visualization_level: VisualizationLevel = VisualizationLevel.ANALYTICAL):
        self.visualization_level = visualization_level
        self.chart_generator = ChartGenerator()
        self.dashboard_generator = DashboardGenerator(visualization_level)
        
    def generate_comprehensive_visualizations(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete set of financial visualizations"""
        
        logger.info("Generating comprehensive financial visualizations...")
        
        # Generate appropriate dashboard based on visualization level
        if self.visualization_level == VisualizationLevel.EXECUTIVE:
            dashboard = self.dashboard_generator.generate_executive_dashboard(financial_data)
        else:
            dashboard = self.dashboard_generator.generate_analytical_dashboard(financial_data)
        
        # Generate individual chart exports
        chart_exports = {}
        for i, chart in enumerate(dashboard['charts']):
            chart_id = f"chart_{i+1}_{chart['title'].lower().replace(' ', '_')}"
            chart_exports[chart_id] = chart
        
        visualizations = {
            "dashboard": dashboard,
            "individual_charts": chart_exports,
            "export_options": {
                "formats": [fmt.value for fmt in ExportFormat],
                "sizes": ["small", "medium", "large", "custom"],
                "themes": ["light", "dark", "corporate"]
            },
            "metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "visualization_level": self.visualization_level.value,
                "total_charts": len(chart_exports),
                "data_sources": list(financial_data.keys())
            }
        }
        
        logger.info(f"Generated {len(chart_exports)} charts and 1 dashboard")
        return visualizations
    
    def export_to_html(self, visualizations: Dict[str, Any]) -> str:
        """Export visualizations to interactive HTML dashboard"""
        
        dashboard = visualizations['dashboard']
        charts = dashboard['charts']
        key_metrics = dashboard['key_metrics']
        
        # Generate HTML with Chart.js integration
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dashboard['config']['title']}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 30px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
        }}
        .recommendation {{
            background: #e8f6f3;
            border-left: 4px solid #27ae60;
            padding: 15px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        .recommendation.critical {{
            background: #fdf2f2;
            border-left-color: #e74c3c;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{dashboard['config']['title']}</h1>
        <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{key_metrics['max_penalty_risk']}</div>
            <div class="metric-label">Maximum Penalty Risk</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{key_metrics['implementation_cost']}</div>
            <div class="metric-label">Implementation Investment</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{key_metrics['roi_percentage']}</div>
            <div class="metric-label">Return on Investment</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{key_metrics['npv']}</div>
            <div class="metric-label">Net Present Value</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{key_metrics['payback_period']}</div>
            <div class="metric-label">Payback Period</div>
        </div>
    </div>
    
    <div class="recommendation {'critical' if 'NOT' in key_metrics['recommendation'] else ''}">
        <strong>Investment Recommendation:</strong> {key_metrics['recommendation']}
    </div>
    
    <div class="charts-grid">
"""
        
        # Generate individual chart containers
        for i, chart in enumerate(charts):
            chart_id = f"chart_{i}"
            html_content += f"""
        <div class="chart-container">
            <div class="chart-title">{chart['title']}</div>
            <canvas id="{chart_id}" width="{chart['config']['width']}" height="{chart['config']['height']}"></canvas>
        </div>
"""
        
        html_content += """
    </div>
    
    <script>
        // Chart.js configuration and rendering
"""
        
        # Generate JavaScript for each chart
        for i, chart in enumerate(charts):
            chart_id = f"chart_{i}"
            chart_json = json.dumps(chart, default=str)
            html_content += f"""
        const ctx{i} = document.getElementById('{chart_id}').getContext('2d');
        const chartConfig{i} = {chart_json};
        new Chart(ctx{i}, {{
            type: chartConfig{i}.type,
            data: chartConfig{i}.data,
            options: chartConfig{i}.options
        }});
"""
        
        html_content += """
    </script>
</body>
</html>
"""
        
        return html_content
    
    def save_visualizations(self, visualizations: Dict[str, Any], 
                          output_dir: str = "output/visualizations",
                          formats: List[ExportFormat] = None) -> Dict[str, str]:
        """Save visualizations in multiple formats"""
        
        if formats is None:
            formats = [ExportFormat.HTML, ExportFormat.JSON]
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        for format_type in formats:
            if format_type == ExportFormat.HTML:
                html_content = self.export_to_html(visualizations)
                filepath = os.path.join(output_dir, "financial_dashboard.html")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                saved_files['html'] = filepath
                
            elif format_type == ExportFormat.JSON:
                json_content = json.dumps(visualizations, indent=2, default=str)
                filepath = os.path.join(output_dir, "financial_visualizations.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(json_content)
                saved_files['json'] = filepath
        
        logger.info(f"Visualizations saved to {output_dir}")
        return saved_files

def demonstrate_financial_visualization():
    """Demonstrate the Financial Visualization Module capabilities"""
    
    print("📊 DORA Compliance Financial Visualization Module")
    print("=" * 55)
    
    # Sample financial data
    sample_data = {
        "penalty_analysis": {
            "maximum_penalty_risk": 10000000,
            "expected_annual_penalty": 3000000,
            "penalty_as_revenue_percentage": 2.0
        },
        "implementation_cost": {
            "total_cost": 399000,
            "cost_breakdown": {
                "software": 150000,
                "personnel": 120000,
                "consulting": 80000,
                "training": 30000,
                "hardware": 19000
            }
        },
        "advanced_roi_analysis": {
            "roi_percentage": 2431.3,
            "npv": 5480424,
            "irr": 64.9,
            "payback_period_years": 6.06,
            "profitability_index": 14.74
        },
        "risk_metrics": {
            "probability_positive_npv": 1.0,
            "worst_case_npv": 5655235,
            "best_case_npv": 9628937
        },
        "cash_flow_analysis": {
            "detailed_cash_flows": [
                {"year": 0, "amount": -279300, "category": "implementation_cost"},
                {"year": 1, "amount": 50000, "category": "savings"},
                {"year": 2, "amount": 10050000, "category": "penalty_avoidance"},
                {"year": 3, "amount": 50000, "category": "savings"},
                {"year": 4, "amount": 50000, "category": "savings"},
                {"year": 5, "amount": 50000, "category": "savings"}
            ]
        },
        "sensitivity_analysis": {
            "base_case": {"npv": 5480424},
            "tornado_chart_data": [
                {"variable": "benefits", "impact_range": 3000000, "min_npv": 3480424, "max_npv": 7480424},
                {"variable": "costs", "impact_range": 800000, "min_npv": 4880424, "max_npv": 6080424},
                {"variable": "discount_rate", "impact_range": 500000, "min_npv": 5180424, "max_npv": 5780424}
            ],
            "scenario_analysis": {
                "pessimistic": {"benefits": 7000000, "costs": 519000, "npv": 4920843},
                "most_likely": {"benefits": 10000000, "costs": 399000, "npv": 5480424},
                "optimistic": {"benefits": 13000000, "costs": 319000, "npv": 6633495}
            }
        },
        "investment_recommendation": {
            "recommendation": "STRONGLY RECOMMENDED"
        }
    }
    
    # Create visualization module
    viz_module = FinancialVisualizationModule(VisualizationLevel.ANALYTICAL)
    
    print("🎨 Generating Comprehensive Visualizations...")
    visualizations = viz_module.generate_comprehensive_visualizations(sample_data)
    
    print(f"✅ Visualization Generation Complete!")
    print(f"   • Dashboard Type: {visualizations['dashboard']['summary']['dashboard_type']}")
    print(f"   • Total Charts: {visualizations['metadata']['total_charts']}")
    print(f"   • Visualization Level: {visualizations['metadata']['visualization_level']}")
    
    # Display chart information
    print(f"\n📈 Generated Charts:")
    for chart_id, chart in visualizations['individual_charts'].items():
        print(f"   • {chart['title']} ({chart['type']})")
    
    # Display key metrics
    key_metrics = visualizations['dashboard']['key_metrics']
    print(f"\n💰 Key Financial Metrics:")
    print(f"   • Maximum Penalty Risk: {key_metrics['max_penalty_risk']}")
    print(f"   • Implementation Cost: {key_metrics['implementation_cost']}")
    print(f"   • ROI: {key_metrics['roi_percentage']}")
    print(f"   • NPV: {key_metrics['npv']}")
    print(f"   • Payback Period: {key_metrics['payback_period']}")
    print(f"   • Recommendation: {key_metrics['recommendation']}")
    
    # Test HTML export
    print(f"\n📄 Testing Export Capabilities...")
    try:
        html_content = viz_module.export_to_html(visualizations)
        print(f"   • HTML Dashboard: {len(html_content)} characters generated")
        print(f"   • Interactive Charts: Chart.js integration included")
        print(f"   • Responsive Design: Mobile-friendly layout")
        
        # Test save functionality
        saved_files = viz_module.save_visualizations(
            visualizations, 
            "demo_output",
            [ExportFormat.HTML, ExportFormat.JSON]
        )
        print(f"   • Files Saved: {list(saved_files.keys())}")
        
    except Exception as e:
        print(f"   • Export Error: {str(e)}")
    
    print(f"\n✅ Financial Visualization Module Demonstration Complete!")

if __name__ == "__main__":
    demonstrate_financial_visualization() 