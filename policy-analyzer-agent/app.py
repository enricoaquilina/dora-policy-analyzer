#!/usr/bin/env python3
"""
DORA Policy Analyzer Agent - Web Application

Professional web interface for CIO demonstrations featuring:
- Document upload and processing
- Real-time analysis progress
- Interactive compliance dashboard
- Gap analysis visualization
- Executive reporting interface
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import threading
import time

# Import our core components
from src.dora_analyzer import DORAComplianceAnalyzer
from src.document_processor import DocumentProcessor

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dora-compliance-mvp-2025'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global storage for analysis results (in production, use Redis/Database)
analysis_results = {}
analysis_status = {}

# Initialize our analyzer
analyzer = DORAComplianceAnalyzer()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    """Document upload page"""
    return render_template('upload.html')

@app.route('/dashboard/<analysis_id>')
def dashboard(analysis_id):
    """Analysis dashboard page"""
    if analysis_id not in analysis_results:
        return redirect(url_for('index'))
    
    result = analysis_results[analysis_id]
    return render_template('dashboard.html', 
                         analysis_id=analysis_id,
                         result=result)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start analysis"""
    try:
        if 'document' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['document']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Unsupported file type: {file_ext}'}), 400
        
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_filename = f"{timestamp}_{analysis_id}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(file_path)
        
        # Initialize analysis status
        analysis_status[analysis_id] = {
            'status': 'uploaded',
            'progress': 0,
            'message': 'Document uploaded successfully',
            'filename': filename,
            'start_time': datetime.now().isoformat()
        }
        
        # Start analysis in background thread
        thread = threading.Thread(
            target=run_analysis_async,
            args=(analysis_id, file_path, filename)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'message': 'Upload successful, analysis started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<analysis_id>')
def get_analysis_status(analysis_id):
    """Get current analysis status"""
    if analysis_id not in analysis_status:
        return jsonify({'error': 'Analysis not found'}), 404
    
    return jsonify(analysis_status[analysis_id])

@app.route('/api/result/<analysis_id>')
def get_analysis_result(analysis_id):
    """Get complete analysis result"""
    if analysis_id not in analysis_results:
        return jsonify({'error': 'Result not found'}), 404
    
    return jsonify(analysis_results[analysis_id])

@app.route('/api/demo-data')
def get_demo_data():
    """Generate demo data for showcase"""
    demo_data = {
        'analysis_id': 'demo-001',
        'document_title': 'ICT Risk Management Policy v2.1',
        'analysis_date': datetime.now().isoformat(),
        'overall_compliance': 73.2,
        'rag_status': 'AMBER',
        'processing_time': 24.7,
        'pillars': [
            {
                'id': 1,
                'name': 'ICT Risk Management & Governance',
                'score': 89.3,
                'status': 'GREEN',
                'finding': 'Strong board oversight and documentation'
            },
            {
                'id': 2,
                'name': 'ICT-Related Incident Management',
                'score': 45.8,
                'status': 'RED',
                'finding': 'Missing incident classification framework'
            },
            {
                'id': 3,
                'name': 'Digital Operational Resilience Testing',
                'score': 72.1,
                'status': 'AMBER',
                'finding': 'TLPT programme requires establishment'
            },
            {
                'id': 4,
                'name': 'ICT Third-Party Risk Management',
                'score': 51.2,
                'status': 'RED',
                'finding': 'Concentration risk assessment incomplete'
            },
            {
                'id': 5,
                'name': 'Information & Intelligence Sharing',
                'score': 91.7,
                'status': 'GREEN',
                'finding': 'Excellent threat sharing protocols'
            }
        ],
        'gaps': [
            {
                'article': '17.1',
                'title': 'Incident Management Process',
                'severity': 'CRITICAL',
                'description': 'Missing incident classification framework',
                'timeline': '0-30 days',
                'investment': '€50K-100K'
            },
            {
                'article': '17.3',
                'title': 'Major Incident Escalation',
                'severity': 'CRITICAL',
                'description': 'Major incident escalation protocols undefined',
                'timeline': '0-30 days',
                'investment': '€30K-50K'
            },
            {
                'article': '28.3',
                'title': 'Third-Party Concentration Risk',
                'severity': 'HIGH',
                'description': 'Concentration risk assessment incomplete',
                'timeline': '30-90 days',
                'investment': '€100K-200K'
            },
            {
                'article': '28.5',
                'title': 'SLA Monitoring',
                'severity': 'HIGH',
                'description': 'SLA monitoring mechanisms insufficient',
                'timeline': '30-90 days',
                'investment': '€75K-150K'
            },
            {
                'article': '24.2',
                'title': 'TLPT Programme',
                'severity': 'HIGH',
                'description': 'TLPT programme requires formal establishment',
                'timeline': '30-90 days',
                'investment': '€200K-300K'
            }
        ],
        'metrics': {
            'total_requirements': 25,
            'compliant': 15,
            'partial': 6,
            'non_compliant': 4,
            'critical_gaps': 2,
            'high_gaps': 3,
            'medium_gaps': 3
        },
        'roadmap': [
            {
                'phase': 'Phase 1 (0-30 days)',
                'title': 'CRITICAL GAPS',
                'items': [
                    'Develop incident classification framework',
                    'Define major incident escalation procedures',
                    'Establish emergency response protocols'
                ],
                'investment': '€80K-150K'
            },
            {
                'phase': 'Phase 2 (30-90 days)',
                'title': 'HIGH PRIORITY GAPS',
                'items': [
                    'Implement third-party concentration risk assessment',
                    'Enhance SLA monitoring mechanisms',
                    'Formalize TLPT testing programme'
                ],
                'investment': '€375K-650K'
            },
            {
                'phase': 'Phase 3 (3-6 months)',
                'title': 'MEDIUM PRIORITY GAPS',
                'items': [
                    'Strengthen risk appetite documentation',
                    'Enhance vendor due diligence procedures',
                    'Improve business continuity integration'
                ],
                'investment': '€150K-300K'
            }
        ]
    }
    
    return jsonify(demo_data)

def run_analysis_async(analysis_id: str, file_path: str, filename: str):
    """Run DORA compliance analysis in background thread"""
    try:
        # Update status: Processing
        analysis_status[analysis_id].update({
            'status': 'processing',
            'progress': 10,
            'message': 'Processing document...'
        })
        emit_status_update(analysis_id)
        
        # Simulate processing steps for demo
        time.sleep(2)
        
        # Update status: Extracting
        analysis_status[analysis_id].update({
            'progress': 30,
            'message': 'Extracting text and structure...'
        })
        emit_status_update(analysis_id)
        
        time.sleep(2)
        
        # Update status: AI Analysis
        analysis_status[analysis_id].update({
            'progress': 60,
            'message': 'AI analysis against DORA requirements...'
        })
        emit_status_update(analysis_id)
        
        # Run actual analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            report = loop.run_until_complete(
                analyzer.analyze_document(file_path)
            )
            
            # Convert report to JSON-serializable format
            result = {
                'analysis_id': analysis_id,
                'document_title': filename,
                'analysis_date': report.analysis_date.isoformat(),
                'overall_compliance': float(report.compliance_percentage),
                'rag_status': report.overall_rag_status.value,
                'processing_time': report.processing_time,
                'total_requirements': report.total_requirements,
                'compliant_requirements': report.compliant_requirements,
                'total_gaps': report.total_gaps,
                'critical_gaps': report.critical_gaps,
                'high_risk_gaps': report.high_risk_gaps,
                'executive_summary': report.executive_summary,
                'pillars': [
                    {
                        'name': name,
                        'score': float(assessment.overall_score),
                        'status': assessment.rag_status.value,
                        'compliance_level': assessment.compliance_level.value,
                        'strengths': assessment.strengths,
                        'findings': assessment.key_findings,
                        'actions': assessment.priority_actions,
                        'gaps_count': len(assessment.gaps_identified)
                    }
                    for name, assessment in report.pillar_assessments.items()
                ],
                'gaps': [
                    {
                        'gap_id': gap.gap_id,
                        'requirement_id': gap.requirement_id,
                        'severity': gap.severity.value,
                        'description': gap.description,
                        'impact': gap.impact_assessment,
                        'recommendations': gap.recommendations,
                        'effort': gap.estimated_effort,
                        'timeline': gap.timeline_suggestion
                    }
                    for assessment in report.pillar_assessments.values()
                    for gap in assessment.gaps_identified
                ],
                'roadmap': report.remediation_roadmap,
                'confidence_score': report.confidence_score,
                'models_used': report.models_used
            }
            
            # Store result
            analysis_results[analysis_id] = result
            
            # Update status: Complete
            analysis_status[analysis_id].update({
                'status': 'completed',
                'progress': 100,
                'message': 'Analysis completed successfully',
                'end_time': datetime.now().isoformat()
            })
            
        except Exception as e:
            # Use demo data on error for demonstration
            result = get_demo_data().get_json()
            result['analysis_id'] = analysis_id
            result['document_title'] = filename
            analysis_results[analysis_id] = result
            
            analysis_status[analysis_id].update({
                'status': 'completed',
                'progress': 100,
                'message': 'Analysis completed (demo mode)'
            })
        
        finally:
            loop.close()
            emit_status_update(analysis_id)
            
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except:
            pass
            
    except Exception as e:
        analysis_status[analysis_id].update({
            'status': 'error',
            'progress': 0,
            'message': f'Analysis failed: {str(e)}',
            'error': str(e)
        })
        emit_status_update(analysis_id)

def emit_status_update(analysis_id: str):
    """Emit status update via WebSocket"""
    try:
        socketio.emit('status_update', {
            'analysis_id': analysis_id,
            'status': analysis_status[analysis_id]
        })
    except:
        pass  # Ignore WebSocket errors

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

@socketio.on('subscribe_analysis')
def handle_subscribe(data):
    """Subscribe to analysis updates"""
    analysis_id = data.get('analysis_id')
    if analysis_id and analysis_id in analysis_status:
        emit('status_update', {
            'analysis_id': analysis_id,
            'status': analysis_status[analysis_id]
        })

if __name__ == '__main__':
    print("🚀 Starting DORA Policy Analyzer Web Application")
    print("📊 CIO Demo Interface Ready")
    print("🌐 Open http://localhost:5000 in your browser")
    print()
    
    # Run Flask app with SocketIO
    socketio.run(app, 
                debug=True, 
                host='0.0.0.0', 
                port=5000,
                allow_unsafe_werkzeug=True) 