#!/bin/bash

# Build script for Pantheon Agents documentation

echo "Building Pantheon Agents documentation..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install documentation dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Clean previous builds
echo "Cleaning previous builds..."
make clean

# Build HTML documentation
echo "Building HTML documentation..."
make html

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Documentation built successfully!"
    echo "Open docs/build/html/index.html to view the documentation"
    
    # Optional: Start a local server
    read -p "Start local server to preview? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting server at http://localhost:8080"
        cd build/html && python -m http.server 8080
    fi
else
    echo "Documentation build failed!"
    exit 1
fi