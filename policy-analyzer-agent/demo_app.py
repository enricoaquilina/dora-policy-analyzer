#!/usr/bin/env python3
"""
DORA Policy Analyzer - Demo Web Application

Simplified demo version that provides full UI experience with realistic 
compliance analysis results and interactive dashboard features.

Features:
- Document upload with real-time progress
- DORA compliance analysis simulation  
- Interactive dashboard with charts
- Executive reporting and gap analysis
- Technical standards integration

Author: DORA Compliance System
Date: 2025-01-23
"""

import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import eventlet

# Add RTS/ITS integration
try:
    sys.path.append(str(Path(__file__).parent.parent))  # Add parent directory to path
    from src.rts_its_integration import enhance_policy_analysis, get_technical_standards_data, search_standards
    RTS_ITS_INTEGRATION_AVAILABLE = True
    print("✅ RTS/ITS integration module loaded successfully")
except ImportError as e:
    RTS_ITS_INTEGRATION_AVAILABLE = False
    print(f"⚠️  RTS/ITS integration not available: {e}")

# Add Gap Assessment Agent
try:
    from src.gap_assessment_agent import assess_compliance_gaps
    GAP_ASSESSMENT_AVAILABLE = True
    print("✅ Gap Assessment Agent loaded successfully")
except ImportError as e:
    GAP_ASSESSMENT_AVAILABLE = False
    print(f"⚠️  Gap Assessment Agent not available: {e}")

# Add Risk Calculator Agent
try:
    from src.risk_calculator_agent import calculate_financial_impact
    RISK_CALCULATOR_AVAILABLE = True
    print("✅ Risk Calculator Agent loaded successfully")
except ImportError as e:
    RISK_CALCULATOR_AVAILABLE = False
    print(f"⚠️  Risk Calculator Agent not available: {e}")

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dora-demo-secret-key-2025'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# SocketIO setup
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Ensure upload directory exists
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)

# In-memory storage for demo
analysis_results = {}
upload_progress = {}

def serialize_for_json(obj):
    """
    Recursively convert objects to JSON-serializable format.
    Handles enums, datetime objects, and other non-serializable types.
    """
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Handle dataclass objects and other objects with __dict__
        return serialize_for_json(obj.__dict__)
    else:
        return obj

def get_demo_compliance_data() -> Dict[str, Any]:
    """Generate realistic DORA compliance analysis data for demonstration"""
    return {
        "document_metadata": {
            "filename": "ICT_Risk_Management_Policy_v2.1.pdf",
            "file_size": "2.4 MB",
            "pages": 47,
            "upload_time": datetime.now().isoformat(),
            "document_type": "Policy Document",
            "classification": "Internal Use"
        },
        "document_content": {
            "text_content": "ICT Risk Management Policy. This policy establishes the framework for identifying, assessing, and managing information and communication technology risks within our organization. The policy covers risk governance, incident management, business continuity planning, and third-party vendor management in accordance with regulatory requirements including DORA compliance.",
            "structure_analysis": {
                "sections": 12,
                "subsections": 34,
                "references": 8,
                "appendices": 3
            },
            "key_topics": [
                "Risk governance framework",
                "Incident response procedures", 
                "Business continuity planning",
                "Third-party risk management",
                "Operational resilience testing",
                "Information security controls"
            ]
        },
        "dora_compliance": {
            "overall_score": 73.2,
            "status": "AMBER",
            "critical_gaps": 2,
            "high_priority_gaps": 5,
            "medium_priority_gaps": 8,
            "ict_governance": {
                "score": 78.5,
                "status": "GREEN", 
                "articles": [
                    {
                        "article_number": "5",
                        "title": "ICT risk management framework",
                        "compliance_level": 85,
                        "status": "compliant",
                        "findings": ["Strong governance structure", "Clear accountability"]
                    },
                    {
                        "article_number": "6", 
                        "title": "ICT risk appetite and strategy",
                        "compliance_level": 72,
                        "status": "partial",
                        "findings": ["Risk appetite defined", "Strategy needs update"]
                    }
                ]
            },
            "ict_risk_management": {
                "score": 69.8,
                "status": "AMBER",
                "articles": [
                    {
                        "article_number": "8",
                        "title": "Risk identification and assessment", 
                        "compliance_level": 75,
                        "status": "partial",
                        "findings": ["Good process framework", "Missing automated tools"]
                    },
                    {
                        "article_number": "9",
                        "title": "Risk mitigation and controls",
                        "compliance_level": 64,
                        "status": "non_compliant", 
                        "findings": ["Basic controls in place", "Lacks continuous monitoring"]
                    }
                ]
            },
            "ict_incident_management": {
                "score": 71.4,
                "status": "AMBER",
                "articles": [
                    {
                        "article_number": "17",
                        "title": "ICT-related incident management process",
                        "compliance_level": 68,
                        "status": "partial",
                        "findings": ["Process documented", "Classification criteria unclear"]
                    },
                    {
                        "article_number": "19", 
                        "title": "Reporting of major incidents",
                        "compliance_level": 75,
                        "status": "partial",
                        "findings": ["Reporting process exists", "Timeline compliance gaps"]
                    }
                ]
            },
            "digital_operational_resilience_testing": {
                "score": 62.1,
                "status": "RED",
                "articles": [
                    {
                        "article_number": "24",
                        "title": "General requirements for testing",
                        "compliance_level": 58,
                        "status": "non_compliant",
                        "findings": ["Ad-hoc testing only", "No comprehensive programme"]
                    },
                    {
                        "article_number": "25",
                        "title": "Testing of ICT tools and systems", 
                        "compliance_level": 66,
                        "status": "partial",
                        "findings": ["Basic testing performed", "Lacks threat-led approach"]
                    }
                ]
            },
            "ict_third_party_risk": {
                "score": 81.3,
                "status": "GREEN",
                "articles": [
                    {
                        "article_number": "28",
                        "title": "General principles of ICT third-party risk management",
                        "compliance_level": 83,
                        "status": "compliant", 
                        "findings": ["Strong vendor management", "Clear contractual requirements"]
                    },
                    {
                        "article_number": "29",
                        "title": "Preliminary assessment of ICT concentrations",
                        "compliance_level": 79,
                        "status": "compliant",
                        "findings": ["Concentration analysis performed", "Regular reviews scheduled"]
                    }
                ]
            },
            "information_sharing": {
                "score": 45.2,
                "status": "RED", 
                "articles": [
                    {
                        "article_number": "45",
                        "title": "Cyber threat information sharing",
                        "compliance_level": 42,
                        "status": "non_compliant",
                        "findings": ["No formal sharing arrangements", "Limited threat intelligence"]
                    },
                    {
                        "article_number": "46",
                        "title": "Operational or security communication protocols",
                        "compliance_level": 48,
                        "status": "non_compliant", 
                        "findings": ["Basic protocols exist", "Not aligned with DORA requirements"]
                    }
                ]
            }
        },
        "gap_analysis": {
            "critical_gaps": [
                {
                    "id": "GAP-001",
                    "category": "Digital Operational Resilience Testing", 
                    "severity": "Critical",
                    "description": "No comprehensive digital operational resilience testing programme in place",
                    "dora_reference": "Article 24, 25",
                    "current_state": "Ad-hoc testing without systematic approach",
                    "required_state": "Comprehensive testing programme with TLPT for critical systems",
                    "effort_estimate": "6-9 months",
                    "investment_estimate": "€250,000 - €400,000"
                },
                {
                    "id": "GAP-002", 
                    "category": "Information Sharing",
                    "severity": "Critical",
                    "description": "No cyber threat information sharing arrangements with authorities or peers",
                    "dora_reference": "Article 45, 46",
                    "current_state": "Isolated threat intelligence capabilities",
                    "required_state": "Active participation in information sharing mechanisms",
                    "effort_estimate": "3-4 months",
                    "investment_estimate": "€80,000 - €120,000"
                }
            ],
            "high_priority_gaps": [
                {
                    "id": "GAP-003",
                    "category": "ICT Risk Management",
                    "severity": "High", 
                    "description": "Continuous monitoring and automated risk assessment tools missing",
                    "dora_reference": "Article 8, 9",
                    "current_state": "Manual risk assessments performed quarterly",
                    "required_state": "Continuous automated monitoring with real-time risk indicators",
                    "effort_estimate": "4-6 months",
                    "investment_estimate": "€180,000 - €280,000"
                }
            ]
        },
        "recommendations": {
            "immediate_actions": [
                "Establish DORA compliance project team with executive sponsorship",
                "Conduct detailed gap assessment with external DORA specialists", 
                "Develop comprehensive implementation roadmap with timelines",
                "Allocate budget for critical compliance gaps (minimum €500K)"
            ],
            "phase_1_priorities": [
                "Implement digital operational resilience testing programme",
                "Establish cyber threat information sharing capabilities",
                "Upgrade ICT risk management tools and processes"
            ],
            "phase_2_initiatives": [
                "Enhance incident management and reporting procedures",
                "Strengthen third-party risk management framework",
                "Implement continuous compliance monitoring"
            ]
        },
        "timeline": {
            "assessment_phase": "Q1 2025 (Immediate - 3 months)",
            "implementation_phase_1": "Q2-Q3 2025 (Critical gaps - 6 months)", 
            "implementation_phase_2": "Q4 2025-Q1 2026 (Remaining gaps - 6 months)",
            "continuous_improvement": "Q2 2026+ (Ongoing optimization)"
        },
        "investment_summary": {
            "total_estimated_cost": "€650,000 - €950,000",
            "phase_1_cost": "€400,000 - €600,000",
            "phase_2_cost": "€250,000 - €350,000", 
            "annual_operational_cost": "€120,000 - €180,000",
            "cost_breakdown": {
                "technology_solutions": "40%",
                "external_consultancy": "25%", 
                "internal_resources": "20%",
                "training_certification": "10%",
                "contingency": "5%"
            }
        }
    }

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    """Document upload page"""
    return render_template('upload.html')

@app.route('/dashboard')
def dashboard():
    """Compliance dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Save file
        filename = f"{analysis_id}_{file.filename}"
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(filepath)
        
        # Initialize progress tracking
        upload_progress[analysis_id] = {
            'stage': 'uploaded',
            'progress': 10,
            'message': 'File uploaded successfully',
            'filename': file.filename,
            'start_time': datetime.now()
        }
        
        # Start background analysis simulation
        socketio.start_background_task(target=simulate_analysis, analysis_id=analysis_id, filename=file.filename)
        
        return jsonify({
            'analysis_id': analysis_id,
            'filename': file.filename,
            'status': 'uploaded'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def simulate_analysis(analysis_id: str, filename: str):
    """Simulate document analysis with progress updates"""
    try:
        stages = [
            {'stage': 'processing', 'progress': 15, 'message': 'Processing document structure...', 'delay': 2},
            {'stage': 'extracting', 'progress': 30, 'message': 'Extracting text content...', 'delay': 3},
            {'stage': 'analyzing', 'progress': 45, 'message': 'Analyzing DORA compliance...', 'delay': 4},
            {'stage': 'mapping', 'progress': 60, 'message': 'Mapping to technical standards...', 'delay': 3},
            {'stage': 'assessing', 'progress': 75, 'message': 'Performing gap assessment...', 'delay': 4},
            {'stage': 'generating', 'progress': 90, 'message': 'Generating recommendations...', 'delay': 2},
            {'stage': 'complete', 'progress': 100, 'message': 'Analysis complete!', 'delay': 1}
        ]
        
        for stage_info in stages:
            eventlet.sleep(stage_info['delay'])
            
            upload_progress[analysis_id].update({
                'stage': stage_info['stage'],
                'progress': stage_info['progress'],
                'message': stage_info['message']
            })
            
            socketio.emit('analysis_progress', {
                'analysis_id': analysis_id,
                **upload_progress[analysis_id]
            })
        
        # Generate results
        demo_results = get_demo_compliance_data()
        demo_results['document_metadata']['filename'] = filename
        
        # Enhance with RTS/ITS data if available
        if RTS_ITS_INTEGRATION_AVAILABLE:
            try:
                demo_results = enhance_policy_analysis(demo_results)
                print("✅ Analysis enhanced with technical standards")
            except Exception as e:
                print(f"⚠️  Could not enhance with technical standards: {e}")
        
        # Perform gap assessment if available
        if GAP_ASSESSMENT_AVAILABLE:
            try:
                gap_assessment = assess_compliance_gaps(demo_results)
                demo_results['gap_assessment'] = gap_assessment
                print("✅ Gap assessment completed")
            except Exception as e:
                print(f"⚠️  Could not perform gap assessment: {e}")
        
        # Perform financial risk calculation if available
        if RISK_CALCULATOR_AVAILABLE and GAP_ASSESSMENT_AVAILABLE:
            try:
                financial_impact = calculate_financial_impact(demo_results.get('gap_assessment', {}))
                demo_results['financial_impact'] = financial_impact
                print("✅ Financial impact analysis completed")
            except Exception as e:
                print(f"⚠️  Could not perform financial risk calculation: {e}")
        
        # Serialize the results to handle enums and other non-JSON objects
        demo_results = serialize_for_json(demo_results)
        analysis_results[analysis_id] = demo_results
        
        socketio.emit('analysis_complete', {
            'analysis_id': analysis_id,
            'status': 'complete'
        })
        
    except Exception as e:
        socketio.emit('analysis_error', {
            'analysis_id': analysis_id,
            'error': str(e)
        })

@app.route('/api/status/<analysis_id>')
def get_analysis_status(analysis_id: str):
    """Get analysis progress status"""
    if analysis_id in upload_progress:
        return jsonify(upload_progress[analysis_id])
    else:
        return jsonify({'error': 'Analysis not found'}), 404

@app.route('/api/result/<analysis_id>')
def get_analysis_result(analysis_id: str):
    """Get analysis results"""
    if analysis_id in analysis_results:
        # Results are already serialized when stored, but ensure proper response
        return jsonify(analysis_results[analysis_id])
    else:
        return jsonify({'error': 'Results not found'}), 404

@app.route('/api/demo-data')
def get_demo_data():
    """Get demo compliance data for dashboard"""
    try:
        demo_data = get_demo_compliance_data()
        
        # Enhance with RTS/ITS data if available
        if RTS_ITS_INTEGRATION_AVAILABLE:
            try:
                demo_data = enhance_policy_analysis(demo_data)
            except Exception as e:
                print(f"Could not enhance demo data: {e}")
        
        # Add gap assessment if available
        if GAP_ASSESSMENT_AVAILABLE:
            try:
                gap_assessment = assess_compliance_gaps(demo_data)
                demo_data['gap_assessment'] = gap_assessment
            except Exception as e:
                print(f"Could not perform gap assessment on demo data: {e}")
        
        # Add financial impact if available
        if RISK_CALCULATOR_AVAILABLE and GAP_ASSESSMENT_AVAILABLE:
            try:
                financial_impact = calculate_financial_impact(demo_data.get('gap_assessment', {}))
                demo_data['financial_impact'] = financial_impact
            except Exception as e:
                print(f"Could not perform financial risk calculation on demo data: {e}")
        
        # Serialize enums and other non-JSON objects before returning
        serialized_data = serialize_for_json(demo_data)
        return jsonify(serialized_data)
        
    except Exception as e:
        print(f"Error in get_demo_data: {e}")
        return jsonify({'error': f'Demo data generation failed: {str(e)}'}), 500

@app.route('/api/technical-standards')
def get_technical_standards():
    """Get technical standards summary"""
    if RTS_ITS_INTEGRATION_AVAILABLE:
        try:
            return jsonify(get_technical_standards_data())
        except Exception as e:
            return jsonify({'error': f'Technical standards not available: {e}'}), 500
    else:
        return jsonify({'error': 'RTS/ITS integration not available'}), 503

@app.route('/api/technical-standards/search')
def search_technical_standards():
    """Search technical standards"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    if RTS_ITS_INTEGRATION_AVAILABLE:
        try:
            results = search_standards(query)
            return jsonify({'query': query, 'results': results})
        except Exception as e:
            return jsonify({'error': f'Search failed: {e}'}), 500
    else:
        return jsonify({'error': 'RTS/ITS integration not available'}), 503

@app.route('/api/gap-assessment/<analysis_id>')
def get_gap_assessment(analysis_id: str):
    """Get gap assessment results for a specific analysis"""
    if analysis_id in analysis_results:
        result = analysis_results[analysis_id]
        gap_assessment = result.get('gap_assessment')
        if gap_assessment:
            # Data is already serialized, return directly
            return jsonify(gap_assessment)
        else:
            return jsonify({'error': 'Gap assessment not available for this analysis'}), 404
    else:
        return jsonify({'error': 'Analysis not found'}), 404

@app.route('/api/gap-assessment/demo')
def get_demo_gap_assessment():
    """Get demo gap assessment data"""
    if GAP_ASSESSMENT_AVAILABLE:
        try:
            demo_data = get_demo_compliance_data()
            # Enhance with RTS/ITS if available
            if RTS_ITS_INTEGRATION_AVAILABLE:
                demo_data = enhance_policy_analysis(demo_data)
            
            gap_assessment = assess_compliance_gaps(demo_data)
            # Serialize enums and other non-JSON objects before returning
            serialized_assessment = serialize_for_json(gap_assessment)
            return jsonify(serialized_assessment)
        except Exception as e:
            return jsonify({'error': f'Gap assessment failed: {e}'}), 500
    else:
        return jsonify({'error': 'Gap assessment not available'}), 503

@app.route('/api/financial-impact/<analysis_id>')
def get_financial_impact(analysis_id: str):
    """Get financial impact analysis for a specific analysis"""
    if analysis_id in analysis_results:
        result = analysis_results[analysis_id]
        financial_impact = result.get('financial_impact')
        if financial_impact:
            # Data is already serialized, return directly
            return jsonify(financial_impact)
        else:
            return jsonify({'error': 'Financial impact analysis not available for this analysis'}), 404
    else:
        return jsonify({'error': 'Analysis not found'}), 404

@app.route('/api/financial-impact/demo')
def get_demo_financial_impact():
    """Get demo financial impact analysis"""
    if RISK_CALCULATOR_AVAILABLE and GAP_ASSESSMENT_AVAILABLE:
        try:
            demo_data = get_demo_compliance_data()
            # Enhance with RTS/ITS if available
            if RTS_ITS_INTEGRATION_AVAILABLE:
                demo_data = enhance_policy_analysis(demo_data)
            
            gap_assessment = assess_compliance_gaps(demo_data)
            financial_impact = calculate_financial_impact(gap_assessment)
            # Serialize enums and other non-JSON objects before returning
            serialized_impact = serialize_for_json(financial_impact)
            return jsonify(serialized_impact)
        except Exception as e:
            return jsonify({'error': f'Financial impact analysis failed: {e}'}), 500
    else:
        return jsonify({'error': 'Financial impact analysis not available'}), 503

@app.route('/api/business-case/<analysis_id>')
def get_business_case(analysis_id: str):
    """Get executive business case for a specific analysis"""
    if analysis_id in analysis_results:
        result = analysis_results[analysis_id]
        financial_impact = result.get('financial_impact')
        if financial_impact and 'business_case' in financial_impact:
            # Data is already serialized, return directly
            return jsonify(financial_impact['business_case'])
        else:
            return jsonify({'error': 'Business case not available for this analysis'}), 404
    else:
        return jsonify({'error': 'Analysis not found'}), 404

@app.route('/api/business-case/demo')
def get_demo_business_case():
    """Get demo executive business case"""
    if RISK_CALCULATOR_AVAILABLE and GAP_ASSESSMENT_AVAILABLE:
        try:
            demo_data = get_demo_compliance_data()
            if RTS_ITS_INTEGRATION_AVAILABLE:
                demo_data = enhance_policy_analysis(demo_data)
            
            gap_assessment = assess_compliance_gaps(demo_data)
            financial_impact = calculate_financial_impact(gap_assessment)
            
            business_case_data = {
                'business_case': financial_impact.get('business_case', {}),
                'executive_summary': financial_impact.get('executive_summary', {}),
                'roi_analysis': financial_impact.get('roi_analysis', {}),
                'penalty_analysis': financial_impact.get('penalty_analysis', {})
            }
            
            # Serialize enums and other non-JSON objects before returning
            serialized_case = serialize_for_json(business_case_data)
            return jsonify(serialized_case)
        except Exception as e:
            return jsonify({'error': f'Business case generation failed: {e}'}), 500
    else:
        return jsonify({'error': 'Business case generation not available'}), 503

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'rts_its_integration': RTS_ITS_INTEGRATION_AVAILABLE,
            'gap_assessment': GAP_ASSESSMENT_AVAILABLE,
            'risk_calculator': RISK_CALCULATOR_AVAILABLE,
            'financial_impact': RISK_CALCULATOR_AVAILABLE and GAP_ASSESSMENT_AVAILABLE,
            'business_case_generation': RISK_CALCULATOR_AVAILABLE and GAP_ASSESSMENT_AVAILABLE,
            'demo_mode': True,
            'upload_enabled': True
        }
    })

@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'status': 'Connected to DORA Policy Analyzer'})

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('base.html'), 500

if __name__ == '__main__':
    print("🚀 Starting DORA Policy Analyzer Web Application (Demo Mode)")
    print("📊 CIO Demo Interface Ready")
    print("🌐 Open http://localhost:5001 in your browser")
    print()
    print("✨ Demo Features:")
    print("   • Professional web interface")
    print("   • Real-time document upload and analysis")
    print("   • Interactive compliance dashboard")
    print("   • Executive reporting with RAG status")
    print("   • Gap analysis and remediation roadmaps")
    if RTS_ITS_INTEGRATION_AVAILABLE:
        print("   • Technical standards integration (RTS/ITS)")
    if GAP_ASSESSMENT_AVAILABLE:
        print("   • AI-powered gap assessment and prioritization")
    if RISK_CALCULATOR_AVAILABLE:
        print("   • Financial risk calculation and penalty modeling")
        print("   • ROI analysis and payback calculations")
        print("   • Executive business case generation")
        if GAP_ASSESSMENT_AVAILABLE:
            print("   • Integrated financial impact analysis (Gap → Financial)")
    print()
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Run Flask app with SocketIO
    socketio.run(app, 
                debug=True, 
                host='0.0.0.0', 
                port=5001,
                allow_unsafe_werkzeug=True) 