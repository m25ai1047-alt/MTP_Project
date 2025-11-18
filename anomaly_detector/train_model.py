import sys
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import IsolationForest
import joblib

def train_and_save_model(
    normal_logs_path: str,
    model_path: str = 'isolation_forest.joblib',
    vectorizer_path: str = 'tfidf_vectorizer.joblib',
    contamination: float = 0.1
):
    """
    Train Isolation Forest model on normal log data.

    Args:
        normal_logs_path: CSV file with 'log_message' column containing normal logs
        model_path: Path to save trained model
        vectorizer_path: Path to save fitted vectorizer
        contamination: Expected proportion of anomalies (default 0.1 = 10%)
    """
    logs_file = Path(normal_logs_path)
    if not logs_file.exists():
        raise FileNotFoundError(f"Training data not found: {normal_logs_path}")

    print(f"Loading training data from {normal_logs_path}")
    df = pd.read_csv(normal_logs_path)

    if 'log_message' not in df.columns:
        raise ValueError("CSV must contain a 'log_message' column")

    print(f"Training on {len(df)} log entries")

    # Vectorize using TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=5000,
        min_df=2,
        max_df=0.95,
        ngram_range=(1, 2)
    )
    X_train = vectorizer.fit_transform(df['log_message'])
    print(f"Vectorized to {X_train.shape[1]} features")

    # Train model
    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
        max_samples='auto'
    )
    model.fit(X_train)
    print("Model training complete")

    # Save artifacts
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)
    print(f"Saved model to {model_path}")
    print(f"Saved vectorizer to {vectorizer_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python train_model.py <path_to_normal_logs.csv> [contamination]")
        print("\nExample:")
        print("  python train_model.py data/normal_logs.csv 0.1")
        sys.exit(1)

    logs_path = sys.argv[1]
    contamination = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1

    train_and_save_model(logs_path, contamination=contamination)

if __name__ == '__main__':
    main()
