"""
train_url_model.py
==================
Train the URL Random Forest classifier on real phishing datasets.

Datasets (download first):
  1. PhishTank: https://phishtank.org/developer_info.php  → verified_online.csv
  2. UCI Phishing: https://archive.ics.uci.edu/dataset/327  → phishing+websites.zip
  3. Kaggle Phishing URL: https://www.kaggle.com/datasets/taruntiwarihp/phishing-site-urls

Usage:
  python train_url_model.py --phishtank data/verified_online.csv \
                             --legit data/top-1m.csv \
                             --output models/url_rf_model.joblib

Or just run without args to use the synthetic fallback (for testing).
"""
import argparse
import sys
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from agents.url_agent import extract_features

MODEL_OUTPUT = Path("models/url_rf_model.joblib")


def load_phishtank(csv_path: str) -> list[tuple[str, int]]:
    """Load PhishTank verified_online.csv → list of (url, 1)"""
    import csv
    samples = []
    with open(csv_path, encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("url", "").strip()
            if url:
                samples.append((url, 1))
    print(f"  Loaded {len(samples)} phishing URLs from PhishTank")
    return samples


def load_legit_urls(csv_path: str, limit: int = 10000) -> list[tuple[str, int]]:
    """Load Tranco / Alexa top-1M CSV → list of (url, 0)"""
    import csv
    samples = []
    with open(csv_path, encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break
            domain = row[-1].strip() if row else ""
            if domain:
                samples.append((f"https://{domain}", 0))
    print(f"  Loaded {len(samples)} legitimate URLs")
    return samples


def featurize(samples: list[tuple[str, int]]) -> tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    for url, label in samples:
        try:
            feat, _ = extract_features(url)
            X.append(feat)
            y.append(label)
        except Exception:
            pass
    return np.array(X, dtype=np.float32), np.array(y)


def main():
    parser = argparse.ArgumentParser(description="Train PhishNet URL model")
    parser.add_argument("--phishtank", help="Path to PhishTank CSV")
    parser.add_argument("--legit", help="Path to Tranco/Alexa CSV")
    parser.add_argument("--output", default=str(MODEL_OUTPUT))
    args = parser.parse_args()

    samples = []

    if args.phishtank:
        samples.extend(load_phishtank(args.phishtank))
    if args.legit:
        samples.extend(load_legit_urls(args.legit))

    if not samples:
        print("No data provided — generating synthetic training data for demo.")
        from agents.url_agent import URLAgent
        agent = URLAgent()
        agent._train_synthetic_model()
        print("Done. Synthetic model saved.")
        return

    print(f"\nFeaturizing {len(samples)} URLs...")
    X, y = featurize(samples)
    print(f"Feature matrix: {X.shape}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\nTraining Random Forest...")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Legitimate", "Phishing"]))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, output_path)
    print(f"\n✅ Model saved to {output_path}")


if __name__ == "__main__":
    main()
