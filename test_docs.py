#!/usr/bin/env python
"""Test script to verify documentation can be built."""

import subprocess
import sys
import os
from pathlib import Path

def test_sphinx_build():
    """Test that Sphinx documentation builds without errors."""
    docs_dir = Path(__file__).parent / "docs"
    
    # Check if docs directory exists
    if not docs_dir.exists():
        print(f"❌ Documentation directory not found: {docs_dir}")
        return False
    
    # Install documentation requirements
    print("📦 Installing documentation requirements...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", 
            str(docs_dir / "requirements.txt")
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False
    
    # Try to build documentation
    print("🔨 Building documentation...")
    os.chdir(docs_dir)
    
    try:
        # Clean previous builds
        subprocess.run(["make", "clean"], capture_output=True)
        
        # Build HTML docs
        result = subprocess.run(
            ["make", "html"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Documentation built successfully!")
            print(f"📁 Output: {docs_dir}/build/html/index.html")
            return True
        else:
            print(f"❌ Documentation build failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error building documentation: {e}")
        return False

if __name__ == "__main__":
    success = test_sphinx_build()
    sys.exit(0 if success else 1)