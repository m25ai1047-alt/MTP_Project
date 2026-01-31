#!/bin/bash
# Run Root Cause Analysis
# Usage: ./scripts/run_rca.sh "ERROR: Your error message here"

cd "$(dirname "$0")/.."
python3 rca_agent/cli.py "$@"
