#!/usr/bin/env python3
"""
Test Executive Reporting System Integration

This script tests the executive reporting system and resolves any import issues.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_executive_reporting():
    """Test the executive reporting system"""
    
    print("🧪 Testing Executive Reporting System...")
    
    try:
        # Test imports
        from src.executive_reporting_system import ExecutiveReportingSystem, ReportType, AudienceLevel
        print("✅ Executive Reporting System imports successful")
        
        # Sample gap assessment data
        gap_data = {
            'critical_gaps': [
                {
                    'id': 'GAP-001',
                    'category': 'Digital Operational Resilience Testing',
                    'description': 'No comprehensive testing programme for critical systems'
                },
                {
                    'id': 'GAP-002',
                    'category': 'ICT Governance',
                    'description': 'Insufficient ICT governance framework and board oversight'
                }
            ],
            'high_priority_gaps': [
                {
                    'id': 'GAP-003',
                    'category': 'ICT Risk Management',
                    'description': 'Manual risk assessment processes lack automation'
                }
            ]
        }
        
        company_info = {
            'name': 'European Financial Services Ltd',
            'annual_revenue': 500000000,
            'country': 'Germany'
        }
        
        # Create reporting system
        reporting_system = ExecutiveReportingSystem()
        print("✅ Executive Reporting System initialized")
        
        # Generate single report test
        print("📊 Generating CIO Briefing report...")
        cio_report = reporting_system.generate_report(
            ReportType.CIO_BRIEFING,
            gap_data,
            AudienceLevel.CXO,
            company_info
        )
        
        print(f"✅ CIO Briefing Generated:")
        print(f"   • Report ID: {cio_report['metadata']['report_id']}")
        print(f"   • Title: {cio_report['metadata']['title']}")
        print(f"   • Audience: {cio_report['config']['audience_level']}")
        
        # Test export functionality
        print("📄 Testing HTML export...")
        html_export = reporting_system.export_report(cio_report)
        print(f"   • HTML Export: {len(html_export)} characters generated")
        
        # Test saving
        print("💾 Testing file save...")
        from pathlib import Path
        output_dir = "demo_output/executive_reports"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        saved_files = reporting_system.save_report(cio_report, output_dir)
        print(f"   • Files Saved: {list(saved_files.keys())}")
        for format_type, filepath in saved_files.items():
            print(f"     - {format_type}: {filepath}")
        
        # Show executive summary
        exec_summary = cio_report['executive_summary']
        print(f"\n🎯 Executive Summary:")
        print(f"   • Situation: {exec_summary['situation'][:80]}...")
        print(f"   • Recommendation: {exec_summary['recommendation']}")
        print(f"   • Urgency: {exec_summary['urgency'][:60]}...")
        
        print(f"\n✅ Executive Reporting System Test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Executive Reporting System Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_executive_reporting()
    if success:
        print("\n🎉 Executive Reporting System is working correctly!")
    else:
        print("\n💥 Executive Reporting System needs fixes!")
        sys.exit(1) 