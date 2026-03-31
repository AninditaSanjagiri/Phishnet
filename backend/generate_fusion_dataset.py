"""
generate_fusion_dataset.py
==========================
Run all three agents on a labeled URL list and output a CSV of
(url_score, text_score, image_score, label) for fusion model training.

Usage:
  python generate_fusion_dataset.py \
    --urls  data/val_urls.txt \     ← format: "url,label" where label=0/1
    --output data/fusion_train.csv
"""
import argparse
import asyncio
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.url_agent import URLAgent
from agents.text_agent import TextAgent
from agents.image_agent import ImageAgent


async def main(urls_file: str, output_path: str, limit: int):
    print("Loading agents…")
    url_agent   = URLAgent()
    text_agent  = TextAgent()
    image_agent = ImageAgent()

    await url_agent.load()
    await text_agent.load()
    await image_agent.load()

    # Read URLs file: each line "url,label" or just "url" (phishing assumed 1)
    samples = []
    with open(urls_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",", 1)
            url = parts[0].strip()
            label = int(parts[1].strip()) if len(parts) > 1 else 1
            samples.append((url, label))

    samples = samples[:limit]
    print(f"Processing {len(samples)} URLs…\n")

    rows = []
    for i, (url, label) in enumerate(samples):
        print(f"[{i+1}/{len(samples)}] {url[:60]}")
        try:
            url_r, text_r, img_r = await asyncio.gather(
                url_agent.analyze(url),
                text_agent.analyze(url),
                image_agent.analyze(url),
            )
            rows.append({
                "url":         url,
                "url_score":   url_r.get("score", ""),
                "text_score":  text_r.get("score", ""),
                "image_score": img_r.get("score", ""),
                "label":       label,
            })
        except Exception as exc:
            print(f"  ✗ Error: {exc}")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "url_score", "text_score", "image_score", "label"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Saved {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--urls",   required=True)
    parser.add_argument("--output", default="data/fusion_train.csv")
    parser.add_argument("--limit",  type=int, default=2000)
    args = parser.parse_args()
    asyncio.run(main(args.urls, args.output, args.limit))
