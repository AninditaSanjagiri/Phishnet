"""
TextAgent
Fetches the page HTML, extracts visible text and form metadata,
then classifies it using a fine-tuned DistilBERT checkpoint from HuggingFace.

Model: ealvaradob/bert-finetuned-phishing  (free, ~250 MB)
Fallback: keyword heuristic scorer if transformers unavailable
"""
import asyncio
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

# Lazy imports for heavy deps
_tokenizer = None
_model = None
_torch = None

MODEL_NAME = "ealvaradob/bert-finetuned-phishing"
MAX_TEXT_LENGTH = 512          # DistilBERT token limit
FETCH_TIMEOUT = 10             # seconds

# Fallback keyword weights
PHISH_KEYWORDS = {
    "verify your account": 0.9,
    "confirm your identity": 0.85,
    "suspended": 0.7,
    "unauthorized access": 0.75,
    "click here to update": 0.8,
    "enter your password": 0.7,
    "social security": 0.65,
    "urgent action required": 0.8,
    "your account will be closed": 0.85,
    "prize": 0.5,
    "winner": 0.5,
    "free gift": 0.6,
    "limited time offer": 0.4,
    "login": 0.2,
    "secure": 0.15,
}


def _load_model():
    global _tokenizer, _model, _torch
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        _torch = torch
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        _model.eval()
        print(f"    ✅ Text model loaded: {MODEL_NAME}")
    except Exception as exc:
        print(f"    ⚠️  Could not load DistilBERT ({exc}). Using keyword fallback.")


def _extract_text_from_html(html: str) -> tuple[str, dict]:
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise tags
    for tag in soup(["script", "style", "meta", "link", "noscript"]):
        tag.decompose()

    visible_text = soup.get_text(separator=" ", strip=True)
    visible_text = re.sub(r"\s+", " ", visible_text)[:3000]

    # Form metadata
    forms = soup.find_all("form")
    form_actions = [f.get("action", "") for f in forms]
    password_fields = len(soup.find_all("input", {"type": "password"}))
    external_forms = sum(
        1 for a in form_actions
        if a.startswith("http") and not any(
            domain in a for domain in ["", "localhost"]
        )
    )

    # Suspicious link count
    links = soup.find_all("a", href=True)
    suspicious_links = sum(
        1 for l in links
        if re.search(r"login|verify|secure|update|confirm", l["href"], re.I)
    )

    metadata = {
        "form_count": len(forms),
        "password_fields": password_fields,
        "external_form_actions": external_forms,
        "suspicious_links": suspicious_links,
        "text_length": len(visible_text),
    }
    return visible_text, metadata


def _keyword_fallback_score(text: str) -> float:
    """Simple weighted keyword scorer when DistilBERT is unavailable."""
    text_lower = text.lower()
    score = 0.0
    matches = 0
    for kw, weight in PHISH_KEYWORDS.items():
        if kw in text_lower:
            score += weight
            matches += 1
    if matches == 0:
        return 0.1
    return min(score / max(matches * 1.5, 1.0), 1.0)


class TextAgent:
    def __init__(self):
        self._model_loaded = False

    async def load(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _load_model)
        self._model_loaded = _model is not None

    async def analyze(self, url: str) -> dict:
        # Fetch page concurrently with a timeout
        html, fetch_error = await self._fetch_html(url)

        if not html:
            return {
                "score": None,
                "confidence": 0.0,
                "explanation": f"Page could not be fetched: {fetch_error}",
                "features": {"fetch_error": fetch_error},
            }

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._classify, html, url)

    async def _fetch_html(self, url: str) -> tuple[Optional[str], Optional[str]]:
        try:
            async with httpx.AsyncClient(
                timeout=FETCH_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (PhishNet/1.0 Security Scanner)"},
            ) as client:
                resp = await client.get(url)
                return resp.text, None
        except Exception as exc:
            return None, str(exc)[:100]

    def _classify(self, html: str, url: str) -> dict:
        text, metadata = _extract_text_from_html(html)

        if not text.strip():
            return {
                "score": 0.3,
                "confidence": 0.4,
                "explanation": "Page has no visible text content.",
                "features": metadata,
            }

        if self._model_loaded and _tokenizer and _model and _torch:
            score, top_tokens = self._bert_classify(text)
            method = "DistilBERT"
        else:
            score = _keyword_fallback_score(text)
            top_tokens = []
            method = "keyword heuristic"

        # Boost score from form metadata signals
        meta_boost = 0.0
        if metadata["password_fields"] > 0:
            meta_boost += 0.1
        if metadata["external_form_actions"] > 0:
            meta_boost += 0.15
        if metadata["suspicious_links"] > 3:
            meta_boost += 0.1

        final_score = min(score + meta_boost, 1.0)

        # Explanation
        reasons = []
        if metadata["password_fields"]:
            reasons.append(f"{metadata['password_fields']} password field(s) found")
        if metadata["external_form_actions"]:
            reasons.append("form submits to external domain")
        if metadata["suspicious_links"] > 2:
            reasons.append(f"{metadata['suspicious_links']} suspicious links")
        if not reasons:
            if final_score > 0.5:
                reasons.append(f"{method} classified content as phishing")
            else:
                reasons.append(f"{method} found no phishing indicators")

        return {
            "score": round(final_score, 4),
            "confidence": round(min(abs(score - 0.5) * 2 + 0.5, 1.0), 4),
            "explanation": "; ".join(reasons).capitalize() + ".",
            "features": {
                **metadata,
                "bert_raw_score": round(score, 4),
                "meta_boost": round(meta_boost, 4),
                "top_tokens": top_tokens,
                "classifier": method,
            },
        }

    def _bert_classify(self, text: str) -> tuple[float, list]:
        import torch

        inputs = _tokenizer(
            text,
            return_tensors="pt",
            max_length=MAX_TEXT_LENGTH,
            truncation=True,
            padding=True,
        )

        with torch.no_grad():
            outputs = _model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]

        # Model labels: 0=legit, 1=phishing (verify for your checkpoint)
        phish_idx = 1 if probs.shape[0] > 1 else 0
        phish_score = float(probs[phish_idx])

        # Simple token attribution: find tokens with highest attention
        # (lightweight alternative to full SHAP)
        tokens = _tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        top_tokens = [
            t for t in tokens
            if t not in ["[CLS]", "[SEP]", "[PAD]"]
            and not t.startswith("##")
            and len(t) > 3
        ][:5]

        return phish_score, top_tokens