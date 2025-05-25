#!/usr/bin/env python3
"""
DORA Compliance System - Demo Runner
Automatically runs the demo using the correct Python environment
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the demo application using the virtual environment"""
    
    # Check if virtual environment exists
    if os.name == 'nt':  # Windows
        venv_python = Path("venv/Scripts/python.exe")
    else:  # macOS/Linux
        venv_python = Path("venv/bin/python")
    
    if not venv_python.exists():
        print("❌ Virtual environment not found!")
        print("💡 Please run: python setup.py")
        sys.exit(1)
    
    # Check if demo_app.py exists
    if not Path("demo_app.py").exists():
        print("❌ demo_app.py not found!")
        print("💡 Make sure you're in the project root directory")
        sys.exit(1)
    
    print("🚀 Starting DORA Compliance Demo...")
    print("📍 URL: http://localhost:5001")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        # Run the demo using the virtual environment's Python
        subprocess.run([str(venv_python), "demo_app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running demo: {e}")
        print("💡 Try: python setup.py")
        sys.exit(1)

if __name__ == "__main__":
    main() 