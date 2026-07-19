"""
Async fetcher: RSS, Reddit JSON, GitHub Trending, HuggingFace Models API.

TIMESTAMP FIX (v2):
  - All published_at values stored as UTC ISO strings ending in 'Z'.
  - Articles without published_at get utcnow() as the display timestamp.
  - DB orders by COALESCE(published_at, fetched_at) so relative times are correct.
"""

import asyncio
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List, Optional

import aiohttp
import feedparser
import trafilatura
from bs4 import BeautifulSoup

from .feeds_config import DOMAIN_FEEDS, EXTRACT_FULL_TEXT_SOURCES
from .database import update_feed_status

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
TIMEOUT = aiohttp.ClientTimeout(total=30)


# -- Helpers ------------------------------------------------------------------

def _url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _utc_now_iso() -> str:
    """Current UTC time as ISO string with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parsed_time_to_iso(t) -> str:
    """
    Convert feedparser's time.struct_time (always UTC) to ISO 8601 with Z.
    Falls back to current UTC if conversion fails.
    """
    if not t:
        return _utc_now_iso()
    try:
        return datetime(*t[:6], tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return _utc_now_iso()


# -- Parsers ------------------------------------------------------------------

def _parse_rss(text: str, source_name: str) -> List[Dict]:
    articles = []
    try:
        feed = feedparser.parse(text)
        for entry in feed.entries[:25]:
            title = entry.get("title", "").strip()
            url   = entry.get("link",  "").strip()
            if not title or not url:
                continue

            # Timestamp fix: always store a proper UTC ISO string
            pub = _parsed_time_to_iso(getattr(entry, "published_parsed", None))

            raw = entry.get("summary", "") or entry.get("description", "") or ""
            raw = re.sub(r"<[^>]+>", " ", raw).strip()

            articles.append({
                "title":        title,
                "url":          url,
                "source":       source_name,
                "published_at": pub,
                "raw_text":     raw[:3000],
                "content_hash": _url_hash(url),
            })
    except Exception as e:
        print(f"RSS parse error [{source_name}]: {e}")
    return articles


def _parse_reddit(data: dict, source_name: str) -> List[Dict]:
    articles = []
    try:
        for post in data.get("data", {}).get("children", [])[:25]:
            d     = post.get("data", {})
            title = d.get("title", "").strip()
            url   = d.get("url",   "").strip()
            if not title:
                continue
            if not url.startswith("http"):
                url = f"https://www.reddit.com{d.get('permalink', '')}"

            created = d.get("created_utc", 0)
            pub = (
                datetime.fromtimestamp(created, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                if created else _utc_now_iso()
            )

            selftext = (d.get("selftext") or "").strip()[:2000]
            articles.append({
                "title":        title,
                "url":          url,
                "source":       source_name,
                "published_at": pub,
                "raw_text":     selftext or title,
                "content_hash": _url_hash(url),
            })
    except Exception as e:
        print(f"Reddit parse error [{source_name}]: {e}")
    return articles


def _parse_github(html: str) -> List[Dict]:
    articles = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for repo in soup.select("article.Box-row")[:20]:
            a_tag = repo.select_one("h2 a")
            if not a_tag:
                continue
            href     = a_tag.get("href", "").strip()
            fullname = href.lstrip("/")
            url      = f"https://github.com{href}"
            desc_el  = repo.select_one("p")
            desc     = desc_el.get_text(strip=True) if desc_el else ""
            lang_el  = repo.select_one('[itemprop="programmingLanguage"]')
            lang     = lang_el.get_text(strip=True) if lang_el else ""
            stars_el = repo.select_one('a[href$="/stargazers"]')
            stars    = stars_el.get_text(strip=True).replace("\n", "").strip() if stars_el else ""
            raw      = f"{desc} | Language: {lang} | Stars: {stars}".strip(" |")
            articles.append({
                "title":        f"Trending: {fullname}",
                "url":          url,
                "source":       "GitHub Trending",
                "published_at": _utc_now_iso(),
                "raw_text":     raw or fullname,
                "content_hash": _url_hash(url),
            })
    except Exception as e:
        print(f"GitHub parse error: {e}")
    return articles


def _parse_hf_models(data: list) -> List[Dict]:
    articles = []
    try:
        for model in data[:20]:
            model_id = model.get("modelId", "") or model.get("id", "")
            if not model_id or "/" not in model_id:
                continue
            url      = f"https://huggingface.co/{model_id}"
            task     = model.get("pipeline_tag", "unknown")
            likes    = model.get("likes", 0)
            dl       = model.get("downloads", 0)
            tags     = ", ".join((model.get("tags") or [])[:6])

            # Normalize HF's lastModified
            modified_raw = model.get("lastModified", "")
            pub = modified_raw[:19].replace(" ", "T") + "Z" if modified_raw else _utc_now_iso()

            raw = (
                f"Model: {model_id}. Task: {task}. "
                f"Downloads: {dl:,}. Likes: {likes}. Tags: {tags}."
            )
            articles.append({
                "title":        f"{model_id} [{task}]",
                "url":          url,
                "source":       "HuggingFace Models",
                "published_at": pub,
                "raw_text":     raw,
                "content_hash": _url_hash(url),
            })
    except Exception as e:
        print(f"HF models parse error: {e}")
    return articles


# -- Content extraction --------------------------------------------------------

def extract_content(url: str, fallback: str = "") -> str:
    """Download a URL and extract readable text with trafilatura."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        if text and len(text) > 150:
            return text[:5000]
    except Exception:
        pass
    return fallback


# -- Async fetch-all -----------------------------------------------------------

async def _fetch(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    try:
        async with session.get(url, timeout=TIMEOUT, headers=HEADERS) as resp:
            if resp.status == 200:
                return await resp.text(errors="replace")
    except Exception as e:
        print(f"  [ERR] fetch {url[:60]}  -> {e}")
    return None


async def fetch_all_feeds(domain: str = "ai") -> List[Dict]:
    """Async-fetch every source for the given domain; return normalised article list."""
    feeds = DOMAIN_FEEDS.get(domain, DOMAIN_FEEDS["ai"])
    all_articles: List[Dict] = []

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        tasks   = [_fetch(session, feed["url"]) for feed in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for feed, result in zip(feeds, results):
        name  = feed["name"]
        ftype = feed["type"]

        if isinstance(result, Exception) or not result:
            update_feed_status(
                feed["url"], name, 0,
                str(result) if isinstance(result, Exception) else "empty"
            )
            continue

        try:
            if ftype == "rss":
                arts = _parse_rss(result, name)
            elif ftype == "reddit":
                arts = _parse_reddit(json.loads(result), name)
            elif ftype == "github":
                arts = _parse_github(result)
            elif ftype == "hf_models":
                arts = _parse_hf_models(json.loads(result))
            else:
                arts = []

            # Tag every article with its domain
            for art in arts:
                art["domain"] = domain

            all_articles.extend(arts)
            update_feed_status(feed["url"], name, len(arts))
            print(f"  [OK] {name}: {len(arts)} items")

        except Exception as e:
            update_feed_status(feed["url"], name, 0, str(e))
            print(f"  [ERR] {name} parse error: {e}")

    return all_articles
