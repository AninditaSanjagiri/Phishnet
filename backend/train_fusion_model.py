"""
train_fusion_model.py
=====================
Train the 3-feature logistic regression fusion layer on agent predictions.
Input CSV must have columns: url_score, text_score, image_score, label

Usage:
  python train_fusion_model.py \
    --data   data/fusion_train.csv \
    --output models/fusion_lr.joblib
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


def load_csv(path: str):
    X, y = [], []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                us = row.get("url_score", "")
                ts = row.get("text_score", "")
                im = row.get("image_score", "")
                label = int(row["label"])

                # Skip rows missing all three scores
                if us == "" and ts == "" and im == "":
                    continue

                # Replace missing scores with neutral 0.5
                feats = [
                    float(us) if us != "" else 0.5,
                    float(ts) if ts != "" else 0.5,
                    float(im) if im != "" else 0.5,
                ]
                X.append(feats)
                y.append(label)
            except (ValueError, KeyError):
                pass
    return np.array(X, dtype=np.float32), np.array(y, dtype=int)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",   default="data/fusion_train.csv")
    parser.add_argument("--output", default="models/fusion_lr.joblib")
    args = parser.parse_args()

    print(f"Loading {args.data}…")
    X, y = load_csv(args.data)
    print(f"Loaded {len(X)} samples — {y.sum()} phishing, {(y==0).sum()} legit")

    if len(X) < 20:
        print("❌ Need at least 20 samples to train fusion model.")
        sys.exit(1)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Pipeline: standard scale + logistic regression (C=1 default)
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("lr",     LogisticRegression(C=1.0, max_iter=200, random_state=42)),
    ])

    # Cross-validation
    cv_scores = cross_val_score(pipe, X_train, y_train, cv=5, scoring="f1")
    print(f"\n5-fold CV F1: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # Final fit
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    print("\nTest Set Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Legit", "Phishing"]))

    # Print learned coefficients
    coef = pipe.named_steps["lr"].coef_[0]
    print(f"\nLearned fusion weights:")
    print(f"  URL score:   {coef[0]:.4f}")
    print(f"  Text score:  {coef[1]:.4f}")
    print(f"  Image score: {coef[2]:.4f}")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out_path)
    print(f"\n✅ Fusion model saved to {out_path}")


if __name__ == "__main__":
    main()
