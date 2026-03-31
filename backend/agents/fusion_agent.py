"""
FusionAgent
Combines scores from URL, Text, and Image agents using
late fusion with a learned logistic regression layer.

If no trained fusion model exists, falls back to static weights:
  URL: 0.35 | Text: 0.40 | Image: 0.25

Verdict thresholds:
  >= 65  → phishing
  >= 40  → suspicious
  <  40  → safe
"""
import asyncio
import joblib
import numpy as np
from pathlib import Path
from typing import Optional

FUSION_MODEL_PATH = Path(__file__).parent.parent / "models" / "fusion_lr.joblib"

# Static fallback weights when no trained fusion model exists
STATIC_WEIGHTS = {"url": 0.35, "text": 0.40, "image": 0.25}

VERDICT_THRESHOLDS = {"phishing": 65.0, "suspicious": 40.0}


class FusionAgent:
    def __init__(self):
        self.lr_model = None
        self.weights = STATIC_WEIGHTS.copy()

    async def load(self):
        if FUSION_MODEL_PATH.exists():
            try:
                self.lr_model = joblib.load(FUSION_MODEL_PATH)
                print(f"    ✅ Fusion LR model loaded from {FUSION_MODEL_PATH}")
            except Exception as exc:
                print(f"    ⚠️  Could not load fusion model: {exc}. Using static weights.")
        else:
            print("    ℹ️  No fusion model found — using static weights.")

    def fuse(
        self,
        url_result: dict,
        text_result: dict,
        image_result: dict,
    ) -> dict:
        url_score: Optional[float] = url_result.get("score")
        text_score: Optional[float] = text_result.get("score")
        image_score: Optional[float] = image_result.get("score")

        available = {
            k: v for k, v in [("url", url_score), ("text", text_score), ("image", image_score)]
            if v is not None
        }

        if not available:
            return {
                "verdict": "suspicious",
                "phishing_probability": 50.0,
                "fusion_weights": {},
                "explanation": "All agents failed — defaulting to suspicious.",
            }

        if self.lr_model is not None and len(available) == 3:
            probability = self._lr_fuse(url_score, text_score, image_score)
            effective_weights = {"url": 0.0, "text": 0.0, "image": 0.0, "method": "logistic_regression"}
        else:
            probability, effective_weights = self._static_fuse(available)

        prob_pct = probability * 100.0
        verdict = self._verdict(prob_pct)

        return {
            "verdict": verdict,
            "phishing_probability": round(prob_pct, 2),
            "fusion_weights": effective_weights,
        }

    def _lr_fuse(
        self,
        url_score: float,
        text_score: float,
        image_score: float,
    ) -> float:
        feat = np.array([[url_score, text_score, image_score]])
        proba = self.lr_model.predict_proba(feat)[0]
        return float(proba[1])

    def _static_fuse(self, available: dict) -> tuple[float, dict]:
        """Weighted average with weight redistribution for missing agents."""
        total_weight = sum(STATIC_WEIGHTS[k] for k in available)
        if total_weight == 0:
            return 0.5, {}

        effective_weights = {
            k: round(STATIC_WEIGHTS[k] / total_weight, 4) for k in available
        }
        effective_weights["method"] = "static_weighted_average"

        probability = sum(
            float(effective_weights[k]) * float(v)
            for k, v in available.items()
            if k in effective_weights
        )
        effective_weights = {
            k: float(v) if isinstance(v, (int, float)) else v
            for k, v in effective_weights.items()
        }

        return float(probability), effective_weights

    @staticmethod
    def _verdict(prob_pct: float) -> str:
        if prob_pct >= VERDICT_THRESHOLDS["phishing"]:
            return "phishing"
        if prob_pct >= VERDICT_THRESHOLDS["suspicious"]:
            return "suspicious"
        return "safe"