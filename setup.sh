#!/bin/bash

# Setup script for RCA Analysis System

set -e

echo "=========================================="
echo "  RCA Analysis System Setup"
echo "=========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
echo "  - Anomaly detector dependencies..."
pip install -q -r anomaly_detector/requirements.txt

echo "  - Code indexer dependencies..."
pip install -q -r code_indexer/requirements.txt

echo "  - RCA agent dependencies..."
pip install -q -r rca_agent/requirements.txt

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p code_indexer/chroma_db_storage
mkdir -p logs
mkdir -p sample_data

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your LLM_API_KEY"
fi

# Train sample model if training data exists
if [ -f sample_data/normal_logs.csv ]; then
    echo ""
    echo "Training sample anomaly detection model..."
    cd anomaly_detector
    python train_model.py ../sample_data/normal_logs.csv 2>/dev/null || echo "Training skipped (optional)"
    cd ..
fi

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Edit .env and add your LLM_API_KEY"
echo ""
echo "  3. Test the system:"
echo "     python pipeline.py 'ERROR: Test error message'"
echo ""
echo "  4. See QUICKSTART.md for more examples"
echo ""
