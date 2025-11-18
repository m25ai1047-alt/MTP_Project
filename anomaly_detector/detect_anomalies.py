import joblib
from pathlib import Path
from typing import List, Dict

class AnomalyDetector:
    """Detects anomalies in log messages using Isolation Forest."""

    def __init__(self, model_path: str = 'isolation_forest.joblib',
                 vectorizer_path: str = 'tfidf_vectorizer.joblib'):
        """Load pre-trained model and vectorizer."""
        model_file = Path(model_path)
        vectorizer_file = Path(vectorizer_path)

        if not model_file.exists() or not vectorizer_file.exists():
            raise FileNotFoundError(
                f"Model or vectorizer not found. Please train the model first using train_model.py"
            )

        self.model = joblib.load(model_file)
        self.vectorizer = joblib.load(vectorizer_file)

    def predict(self, log_messages: List[str]) -> List[int]:
        """
        Detect anomalies in log messages.
        Returns: List of predictions (-1 for anomaly, 1 for normal)
        """
        if not log_messages:
            return []

        X_new = self.vectorizer.transform(log_messages)
        predictions = self.model.predict(X_new)
        return predictions.tolist()

    def detect_with_scores(self, log_messages: List[str]) -> List[Dict]:
        """
        Detect anomalies with anomaly scores.
        Returns: List of dicts with log, prediction, and score
        """
        if not log_messages:
            return []

        X_new = self.vectorizer.transform(log_messages)
        predictions = self.model.predict(X_new)
        scores = self.model.score_samples(X_new)

        results = []
        for log, pred, score in zip(log_messages, predictions, scores):
            results.append({
                'log': log,
                'is_anomaly': pred == -1,
                'anomaly_score': float(score)
            })

        return results

def main():
    """CLI for anomaly detection."""
    detector = AnomalyDetector()

    test_logs = [
        "INFO: User 'testuser' logged in successfully.",
        "ERROR: Database connection failed: timeout expired.",
        "INFO: Processing request /api/v1/users",
        "WARN: High memory usage detected: 95%",
        "FATAL: NullPointerException at com.example.UserService:123"
    ]

    results = detector.detect_with_scores(test_logs)

    print("\nAnomaly Detection Results:")
    print("-" * 80)
    for r in results:
        status = "ANOMALY" if r['is_anomaly'] else "NORMAL"
        print(f"[{status:8}] Score: {r['anomaly_score']:6.3f} | {r['log']}")

if __name__ == '__main__':
    main()
