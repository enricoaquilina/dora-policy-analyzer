#!/usr/bin/env python3
"""
DORA Compliance System - Setup Script
Automated setup for the DORA compliance demo application
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} is not compatible. Please use Python 3.11+")
        return False

def setup_virtual_environment():
    """Set up virtual environment"""
    if Path("venv").exists():
        print("✅ Virtual environment already exists")
        return True
    
    return run_command("python -m venv venv", "Creating virtual environment")

def install_dependencies():
    """Install required dependencies"""
    # Determine the correct pip command based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # macOS/Linux
        pip_cmd = "venv/bin/pip"
    
    # Install basic dependencies first
    basic_deps = [
        "pip install --upgrade pip",
        f"{pip_cmd} install flask>=3.0.0",
        f"{pip_cmd} install flask-socketio>=5.3.6",
        f"{pip_cmd} install eventlet>=0.35.2",
        f"{pip_cmd} install python-dotenv>=1.0.0",
        f"{pip_cmd} install requests>=2.31.0"
    ]
    
    for cmd in basic_deps:
        if not run_command(cmd, f"Installing {cmd.split()[-1]}"):
            return False
    
    # Try to install from requirements.txt
    if Path("requirements.txt").exists():
        run_command(f"{pip_cmd} install -r requirements.txt", "Installing from requirements.txt")
    
    return True

def setup_environment():
    """Set up environment configuration"""
    if not Path(".env").exists() and Path(".env.example").exists():
        shutil.copy(".env.example", ".env")
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your API keys")
    else:
        print("✅ Environment file already exists")
    
    # Create uploads directory
    Path("uploads").mkdir(exist_ok=True)
    print("✅ Created uploads directory")

def main():
    """Main setup function"""
    print("🏦 DORA Compliance System - Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Set up virtual environment
    if not setup_virtual_environment():
        print("❌ Failed to create virtual environment")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        print("💡 Try the minimal setup from the README")
        sys.exit(1)
    
    # Set up environment
    setup_environment()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys (optional for demo)")
    print("2. Run the demo:")
    print("   python run_demo.py")
    print("   OR activate virtual environment first:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   python demo_app.py")
    print("3. Open http://localhost:5001 in your browser")

if __name__ == "__main__":
    main() 