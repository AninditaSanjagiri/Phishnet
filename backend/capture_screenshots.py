"""
capture_screenshots.py
=======================
Batch-capture screenshots from a list of URLs using Playwright.
Use this to build the image dataset for train_image_model.py.

Usage:
  python capture_screenshots.py --urls phish_urls.txt --output data/screenshots/phishing --limit 1000
  python capture_screenshots.py --urls legit_urls.txt --output data/screenshots/legitimate --limit 1000
"""
import argparse
import asyncio
import hashlib
from pathlib import Path


async def capture(url: str, output_dir: Path, timeout: int = 10000) -> bool:
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            )
            page = await browser.new_page(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0",
            )
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            await page.wait_for_timeout(1000)
            fname = hashlib.md5(url.encode()).hexdigest() + ".png"
            await page.screenshot(path=str(output_dir / fname), full_page=False)
            await browser.close()
            return True
    except Exception as exc:
        print(f"  ✗ {url[:60]} — {exc}")
        return False


async def main_async(urls: list[str], output_dir: Path, concurrency: int = 5):
    output_dir.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(concurrency)
    success = 0

    async def run_one(url: str):
        nonlocal success
        async with sem:
            ok = await capture(url, output_dir)
            if ok:
                success += 1
                print(f"  ✓ [{success}] {url[:60]}")

    await asyncio.gather(*[run_one(url) for url in urls])
    print(f"\nCaptured {success}/{len(urls)} screenshots → {output_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--urls", required=True, help="Text file with one URL per line")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=5)
    args = parser.parse_args()

    with open(args.urls) as f:
        urls = [line.strip() for line in f if line.strip()][:args.limit]

    print(f"Capturing {len(urls)} screenshots → {args.output}")
    asyncio.run(main_async(urls, Path(args.output), args.concurrency))


if __name__ == "__main__":
    main()
