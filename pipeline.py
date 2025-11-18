"""
End-to-end pipeline for anomaly detection and RCA.
This module integrates anomaly detection with root cause analysis.
"""

import sys
from pathlib import Path
from typing import List, Dict

# Add subdirectories to path
sys.path.insert(0, str(Path(__file__).parent / 'anomaly_detector'))
sys.path.insert(0, str(Path(__file__).parent / 'rca_agent'))

from anomaly_detector.detect_anomalies import AnomalyDetector
from rca_agent.rca_service import perform_root_cause_analysis

class LogAnalysisPipeline:
    """Complete pipeline for log analysis and RCA."""

    def __init__(self,
                 model_path: str = 'anomaly_detector/isolation_forest.joblib',
                 vectorizer_path: str = 'anomaly_detector/tfidf_vectorizer.joblib'):
        """Initialize pipeline with anomaly detector."""
        try:
            self.anomaly_detector = AnomalyDetector(model_path, vectorizer_path)
            self.detector_available = True
        except FileNotFoundError:
            print("Warning: Anomaly detection model not found. Only RCA will be available.")
            print("Train the model using: python anomaly_detector/train_model.py <training_data.csv>")
            self.detector_available = False

    def process_logs(self, log_messages: List[str], auto_analyze: bool = True) -> Dict:
        """
        Process logs through the complete pipeline.

        Args:
            log_messages: List of log messages to analyze
            auto_analyze: Automatically run RCA on detected anomalies

        Returns:
            Dict with anomaly detection and RCA results
        """
        results = {
            'total_logs': len(log_messages),
            'anomalies': [],
            'rca_analyses': []
        }

        if not log_messages:
            return results

        # Step 1: Detect anomalies
        if self.detector_available:
            anomaly_results = self.anomaly_detector.detect_with_scores(log_messages)

            for result in anomaly_results:
                if result['is_anomaly']:
                    results['anomalies'].append(result)

            print(f"Detected {len(results['anomalies'])} anomalies out of {len(log_messages)} logs")
        else:
            # If no detector, treat all ERROR/FATAL logs as anomalies
            for log in log_messages:
                if any(level in log for level in ['ERROR', 'FATAL', 'EXCEPTION']):
                    results['anomalies'].append({
                        'log': log,
                        'is_anomaly': True,
                        'anomaly_score': -1.0
                    })

        # Step 2: Run RCA on anomalies
        if auto_analyze and results['anomalies']:
            print(f"\nPerforming RCA on {len(results['anomalies'])} anomalies...")

            for anomaly in results['anomalies']:
                try:
                    rca_result = perform_root_cause_analysis(anomaly['log'])
                    results['rca_analyses'].append(rca_result)
                except Exception as e:
                    print(f"RCA failed for log: {anomaly['log'][:50]}... Error: {e}")

        return results

    def analyze_single_error(self, error_log: str) -> Dict:
        """Directly analyze a single error without anomaly detection."""
        return perform_root_cause_analysis(error_log)

def main():
    """CLI for the complete pipeline."""
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <log_file_or_message>")
        print("\nExamples:")
        print("  python pipeline.py 'ERROR: Database connection failed at UserService.java:42'")
        print("  python pipeline.py logs/application.log")
        sys.exit(1)

    input_arg = sys.argv[1]
    pipeline = LogAnalysisPipeline()

    # Check if input is a file
    input_path = Path(input_arg)
    if input_path.exists() and input_path.is_file():
        with open(input_path, 'r') as f:
            log_messages = [line.strip() for line in f if line.strip()]

        print(f"Processing {len(log_messages)} logs from {input_arg}")
        results = pipeline.process_logs(log_messages)

        print("\n" + "="*80)
        print(f"SUMMARY: Found {len(results['anomalies'])} anomalies")
        print("="*80)

        for i, analysis in enumerate(results['rca_analyses'], 1):
            print(f"\n--- Anomaly {i} ---")
            print(f"Error: {analysis['error_log'][:100]}...")
            print(f"\nAnalysis:\n{analysis['analysis']}")
            print("-"*80)
    else:
        # Treat as single error message
        print("Analyzing error log...")
        result = pipeline.analyze_single_error(input_arg)

        print("\n" + "="*80)
        print("ROOT CAUSE ANALYSIS")
        print("="*80)
        print(f"\nError: {result['error_log']}\n")
        print(f"Analysis:\n{result['analysis']}\n")

        if result['relevant_code']:
            print(f"Found {len(result['relevant_code'])} relevant code snippets")

if __name__ == "__main__":
    main()
