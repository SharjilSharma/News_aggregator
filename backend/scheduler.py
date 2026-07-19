"""
Pipeline orchestrator + APScheduler wrapper.

Flow (each run):
  1. Async-fetch all configured sources
  2. Filter already-known URLs (DB lookup)
  3. Title-similarity deduplication
  4. Enrich with full-text where applicable
  5. Categorise + extractive-summarize (fast, no API)
  6. AI-summarize via Gemini (batch, rate-limited) -- adds ai_title + ai_summary
  7. Save to DB
  8. Second pass: KeyBERT keywords

Refreshes every REFRESH_INTERVAL_MINUTES (default: 2 hours).
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List

from apscheduler.schedulers.background import BackgroundScheduler

from .feeds_config import REFRESH_INTERVAL_MINUTES, EXTRACT_FULL_TEXT_SOURCES
from .database import insert_article, filter_known_urls, get_recent_titles, get_connection
from .fetcher import fetch_all_feeds, extract_content
from .deduplicator import deduplicate
from .categorizer import categorize, extract_keywords
from .summarizer import summarize, batch_ai_summarize

# Windows: use SelectorEventLoop to avoid ProactorEventLoop aiohttp issues
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

scheduler = BackgroundScheduler(daemon=True)

# Pipeline running flag (polled by /api/news/refresh/status)
_pipeline_running = False


def is_pipeline_running() -> bool:
    return _pipeline_running


def run_pipeline(domain: str = "ai") -> int:
    """Full fetch -> deduplicate -> AI-summarize -> store. Returns new article count."""
    global _pipeline_running
    if _pipeline_running:
        print("  [WARN] Pipeline already running -- skipping.")
        return 0

    _pipeline_running = True
    try:
        return _run_pipeline_inner(domain=domain)
    finally:
        _pipeline_running = False


def _run_pipeline_inner(domain: str = "ai") -> int:
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Pipeline starting for domain='{domain}' ...")

    # 1. Async fetch
    raw_articles: List[Dict] = asyncio.run(fetch_all_feeds(domain=domain))
    print(f"  Fetched {len(raw_articles)} raw articles from all sources")

    # 2. URL dedup
    new_articles = filter_known_urls(raw_articles)
    print(f"  {len(new_articles)} articles after URL dedup")
    if not new_articles:
        print("  Nothing new -- pipeline done.\n")
        return 0

    # 3. Title-similarity dedup
    existing_titles = get_recent_titles(limit=500)
    unique_articles = deduplicate(new_articles, existing_titles)
    print(f"  {len(unique_articles)} articles after title dedup")
    if not unique_articles:
        print("  All filtered by similarity -- pipeline done.\n")
        return 0

    # 4. Full-text enrichment
    for article in unique_articles:
        if (
            article.get("source") in EXTRACT_FULL_TEXT_SOURCES
            and len(article.get("raw_text", "")) < 300
        ):
            article["raw_text"] = extract_content(
                article["url"], article.get("raw_text", "")
            )

    # 5. Categorise + extractive summarize
    for article in unique_articles:
        text = article.get("raw_text") or article.get("title", "")
        article["category"] = categorize(article)
        result = summarize(text)
        article["summary"] = result["summary"]
        article["bullets"] = result["bullets"]
        article["keywords"] = []

    # 6. AI summarize (Gemini) -- batch, rate-limited
    print(f"  Starting AI summarization for {len(unique_articles)} articles ...")
    batch_ai_summarize(unique_articles)  # mutates in-place: adds ai_title, ai_summary, summarized_at

    # 7. Save to DB
    saved = 0
    for article in unique_articles:
        if insert_article(article):
            saved += 1
    print(f"  Saved {saved} articles")

    # 8. Second pass: keywords (KeyBERT)
    for article in unique_articles:
        text = article.get("raw_text") or article.get("title", "")
        kws  = extract_keywords(text)
        if kws:
            try:
                conn = get_connection()
                with conn:
                    conn.execute(
                        "UPDATE articles SET keywords=? WHERE url=?",
                        (json.dumps(kws), article["url"]),
                    )
                conn.close()
            except Exception:
                pass

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Pipeline complete -- {saved} new articles\n")
    return saved


def start_scheduler() -> None:
    """Start APScheduler with interval job + immediate warm-up job."""
    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        minutes=REFRESH_INTERVAL_MINUTES,
        id="recurring_fetch",
        replace_existing=True,
        max_instances=1,
    )
    # Run once at startup after a 15-second delay (lets server bind first)
    scheduler.add_job(
        run_pipeline,
        trigger="date",
        run_date=datetime.now() + timedelta(seconds=15),
        id="initial_fetch",
        replace_existing=True,
    )
    scheduler.start()
    print(
        f"Scheduler started -- refreshing every {REFRESH_INTERVAL_MINUTES} min "
        f"(first fetch in ~15 s)"
    )
