"""
URLAgent
Extracts handcrafted heuristic features from a URL and classifies
it using a trained Random Forest model.

Features (16 total):
  - URL length
  - Number of dots in domain
  - Number of subdomains
  - Has IP address as host
  - Has HTTPS
  - Presence of suspicious keywords (login, secure, update, verify…)
  - URL entropy (Shannon)
  - Number of special characters (@, -, _, ~)
  - Path depth
  - Query string length
  - Levenshtein distance to nearest top-brand domain
  - TLD suspicion score
  - Has port number
  - Domain length
  - Subdomain length
  - Number of digits in domain
"""
import asyncio
import math
import re
import os
import joblib
import numpy as np
from pathlib import Path
from urllib.parse import urlparse
from Levenshtein import distance as lev_distance
import tldextract

MODEL_PATH = Path(__file__).parent.parent / "models" / "url_rf_model.joblib"

# Top 30 most-phished brands — Levenshtein bait detection
TOP_BRANDS = [
    "paypal", "microsoft", "apple", "google", "amazon", "facebook",
    "netflix", "instagram", "twitter", "linkedin", "dropbox", "yahoo",
    "chase", "wellsfargo", "bankofamerica", "citibank", "ebay", "steam",
    "roblox", "discord", "whatsapp", "telegram", "outlook", "office365",
    "adobe", "docusign", "fedex", "dhl", "ups", "irs",
]

SUSPICIOUS_KEYWORDS = [
    "login", "signin", "secure", "verify", "update", "confirm", "account",
    "banking", "password", "credential", "webscr", "ebayisapi", "wallet",
    "paypal", "ssn", "free", "lucky", "winner", "prize", "urgent",
]

SUSPICIOUS_TLDS = {
    ".tk": 0.9, ".ml": 0.85, ".ga": 0.85, ".cf": 0.8, ".gq": 0.8,
    ".xyz": 0.6, ".top": 0.6, ".club": 0.55, ".work": 0.5, ".site": 0.5,
    ".online": 0.45, ".info": 0.4,
}


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((f / n) * math.log2(f / n) for f in freq.values())


def min_brand_distance(domain: str) -> float:
    """Normalised Levenshtein distance to nearest top brand (0=match, 1=far)."""
    if not domain:
        return 1.0
    d = min(lev_distance(domain.lower(), brand) for brand in TOP_BRANDS)
    return min(d / max(len(domain), 1), 1.0)


def extract_features(url: str) -> tuple[np.ndarray, dict]:
    parsed = urlparse(url)
    ext = tldextract.extract(url)

    domain = ext.domain or ""
    subdomain = ext.subdomain or ""
    suffix = "." + ext.suffix if ext.suffix else ""
    host = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""

    # IP address host
    is_ip = bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host))

    # Suspicious keyword count
    full_url_lower = url.lower()
    keyword_hits = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in full_url_lower)

    # Brand mimicry
    brand_dist = min_brand_distance(domain)

    # TLD suspicion
    tld_score = SUSPICIOUS_TLDS.get(suffix.lower(), 0.0)

    features = {
        "url_length": len(url),
        "dot_count": url.count("."),
        "subdomain_count": len(subdomain.split(".")) if subdomain else 0,
        "is_ip": int(is_ip),
        "is_https": int(parsed.scheme == "https"),
        "keyword_count": keyword_hits,
        "url_entropy": round(shannon_entropy(url), 4),
        "special_char_count": sum(url.count(c) for c in "@-_~%"),
        "path_depth": len([p for p in path.split("/") if p]),
        "query_length": len(query),
        "brand_lev_distance": round(brand_dist, 4),
        "tld_suspicion": tld_score,
        "has_port": int(bool(parsed.port)),
        "domain_length": len(domain),
        "subdomain_length": len(subdomain),
        "digit_count": sum(1 for c in domain if c.isdigit()),
    }

    return np.array(list(features.values()), dtype=np.float32), features


class URLAgent:
    def __init__(self):
        self.model = None

    async def load(self):
        """Load trained RF model, or train a tiny synthetic one if not found."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_or_create_model)

    def _load_or_create_model(self):
        if MODEL_PATH.exists():
            self.model = joblib.load(MODEL_PATH)
            print(f"    ✅ URL RF model loaded from {MODEL_PATH}")
        else:
            print("    ⚠️  No trained RF model found — creating synthetic baseline.")
            self._train_synthetic_model()

    def _train_synthetic_model(self):
        """
        Train a minimal Random Forest on synthetically generated feature vectors.
        Replace this with real PhishTank + UCI data for production accuracy.
        """
        from sklearn.ensemble import RandomForestClassifier

        rng = np.random.default_rng(42)

        # Synthetic phishing features: long URLs, low HTTPS, high entropy, etc.
        phish_X = rng.uniform(
            [80, 4, 2, 0, 0, 2, 4.0, 3, 2, 20, 0.0, 0.5, 0, 8, 4, 2],
            [300, 10, 5, 1, 1, 8, 5.5, 10, 6, 100, 0.3, 1.0, 1, 30, 20, 8],
            size=(500, 16),
        )
        # Synthetic legit features: shorter, HTTPS, low entropy
        legit_X = rng.uniform(
            [10, 1, 0, 0, 1, 0, 2.5, 0, 0, 0, 0.5, 0.0, 0, 4, 0, 0],
            [80, 3, 1, 0, 1, 1, 3.8, 2, 3, 30, 1.0, 0.0, 0, 15, 5, 2],
            size=(500, 16),
        )

        X = np.vstack([phish_X, legit_X]).astype(np.float32)
        y = np.array([1] * 500 + [0] * 500)

        self.model = RandomForestClassifier(
            n_estimators=100, max_depth=8, random_state=42, n_jobs=-1
        )
        self.model.fit(X, y)

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, MODEL_PATH)
        print(f"    ✅ Synthetic RF model saved to {MODEL_PATH}")

    async def analyze(self, url: str) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._analyze_sync, url)

    def _analyze_sync(self, url: str) -> dict:
        feat_array, feat_dict = extract_features(url)
        proba = self.model.predict_proba([feat_array])[0]
        phish_score = float(proba[1])

        # Identify top contributing features
        importances = self.model.feature_importances_
        feat_names = list(feat_dict.keys())
        top_idx = np.argsort(importances)[::-1][:3]
        top_features = {feat_names[i]: float(round(feat_array[i], 3)) for i in top_idx}

        # Build human-readable explanation
        reasons = []
        if feat_dict["is_ip"]:
            reasons.append("uses IP address as host")
        if feat_dict["keyword_count"] >= 3:
            reasons.append(f"{feat_dict['keyword_count']} suspicious keywords found")
        if feat_dict["brand_lev_distance"] < 0.25:
            reasons.append("domain mimics a known brand")
        if feat_dict["tld_suspicion"] > 0.5:
            reasons.append("uses a high-risk TLD")
        if feat_dict["url_entropy"] > 4.5:
            reasons.append("high URL entropy (obfuscation likely)")
        if not reasons:
            if phish_score > 0.5:
                reasons.append("multiple weak signals combined")
            else:
                reasons.append("URL structure looks normal")

        
        def safe_convert(val):
            if isinstance(val, (np.floating,)):
                return float(val)
            if isinstance(val, (np.integer,)):
                return int(val)
            return val

        features_clean = {
            k: safe_convert(v)
            for k, v in {**feat_dict, "top_importances": top_features}.items()
        }

        return {
            "score": float(round(phish_score, 4)),
            "confidence": float(round(max(proba), 4)),
            "explanation": "; ".join(reasons).capitalize() + ".",
            "features": features_clean,
        }
        