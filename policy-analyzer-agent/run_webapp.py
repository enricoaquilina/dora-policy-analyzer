#!/usr/bin/env python3
"""
DORA Policy Analyzer - Web Application Launcher

Simple launcher script for the CIO demonstration web interface.
Ensures proper environment setup and configuration.
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if basic requirements are installed"""
    try:
        import flask
        import flask_socketio
        print("✅ Flask and SocketIO installed")
    except ImportError as e:
        print(f"❌ Missing required packages: {e}")
        print("\n📦 Installing requirements...")
        os.system("pip install Flask Flask-SocketIO eventlet")
        print("✅ Basic web requirements installed")

def setup_environment():
    """Setup environment variables and configuration"""
    # Set default environment variables
    if not os.getenv('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'
    
    if not os.getenv('FLASK_DEBUG'):
        os.environ['FLASK_DEBUG'] = '1'
    
    # Check for AI API keys
    ai_keys = {
        'ANTHROPIC_API_KEY': 'Anthropic Claude',
        'OPENAI_API_KEY': 'OpenAI GPT',
        'GOOGLE_API_KEY': 'Google Gemini'
    }
    
    available_keys = []
    for key, name in ai_keys.items():
        if os.getenv(key):
            available_keys.append(name)
    
    if available_keys:
        print(f"✅ AI models available: {', '.join(available_keys)}")
    else:
        print("⚠️  No AI API keys detected - demo mode will be used")
        print("💡 Set environment variables for AI analysis:")
        for key, name in ai_keys.items():
            print(f"   export {key}='your-api-key-here'")

def main():
    """Main launcher function"""
    print("🚀 DORA Policy Analyzer - Web Application")
    print("=" * 50)
    
    # Change to app directory
    app_dir = Path(__file__).parent
    os.chdir(app_dir)
    
    # Check requirements
    check_requirements()
    
    # Setup environment
    setup_environment()
    
    print("\n🌐 Starting web application...")
    print("📊 CIO Demo Interface: http://localhost:5000")
    print("📋 Upload Interface: http://localhost:5000/upload")
    print("\n⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Import and run the Flask app
        from app import app, socketio
        socketio.run(app, 
                    debug=True, 
                    host='0.0.0.0', 
                    port=5000,
                    allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n\n👋 Web application stopped")
    except Exception as e:
        print(f"\n❌ Error starting web application: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure you're in the policy-analyzer-agent directory")
        print("2. Install requirements: pip install -r requirements.txt")
        print("3. Check app.py exists and is properly configured")

if __name__ == "__main__":
    main() 