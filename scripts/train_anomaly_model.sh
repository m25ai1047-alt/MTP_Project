#!/bin/bash
# Train Anomaly Detection Model
# Usage: ./scripts/train_anomaly_model.sh <path_to_normal_logs.csv>

cd "$(dirname "$0")/.."
python3 anomaly_detector/train_model.py "$@"
