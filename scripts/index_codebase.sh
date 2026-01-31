#!/bin/bash
# Index Java Codebase
# Usage: ./scripts/index_codebase.sh

cd "$(dirname "$0")/.."
python3 code_indexer/bulk_indexer_enhanced.py
