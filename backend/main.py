"""FastAPI application — serves both the REST API and the frontend SPA."""

import threading
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .database import (
    init_db, get_articles, get_total_count, get_stats,
    get_feeds, get_unsummarized, get_domain_stats,
)
from .scheduler import start_scheduler, run_pipeline, is_pipeline_running
from .feeds_config import DOMAIN_META, DOMAIN_FEEDS

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="NeuroPulse — AI Intelligence Aggregator",
    description="Multi-domain AI news aggregator powered by Gemini + 60+ sources",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# ── Lifecycle ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    init_db()
    start_scheduler()


# ── Frontend ──────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/manifest.json", include_in_schema=False)
def serve_manifest():
    return FileResponse(str(FRONTEND_DIR / "manifest.json"))

@app.get("/sw.js", include_in_schema=False)
def serve_sw():
    return FileResponse(str(FRONTEND_DIR / "sw.js"))


# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/api/news")
def api_news(
    category: str = Query("all",  description="Category filter"),
    domain:   str = Query("all",  description="Domain filter (ai|cybersec|finance|biotech|web3)"),
    limit:    int = Query(30,     ge=1, le=100),
    offset:   int = Query(0,      ge=0),
    search:   str = Query("",     description="Search term"),
):
    articles = get_articles(category=category, domain=domain, limit=limit, offset=offset, search=search)
    total    = get_total_count(category=category, domain=domain, search=search)
    return {
        "articles": articles,
        "total":    total,
        "limit":    limit,
        "offset":   offset,
        "has_more": offset + len(articles) < total,
    }


@app.get("/api/domains")
def api_domains():
    """Return available domains with metadata and article counts."""
    domain_counts = get_domain_stats()
    result = []
    for key, meta in DOMAIN_META.items():
        source_count = len(DOMAIN_FEEDS.get(key, []))
        result.append({
            "key":          key,
            "label":        meta["label"],
            "icon":         meta["icon"],
            "color":        meta["color"],
            "description":  meta["description"],
            "source_count": source_count,
            "article_count": domain_counts.get(key, 0),
        })
    return {"domains": result}


class FetchDomainRequest(BaseModel):
    domain: str = "ai"

@app.post("/api/news/fetch-domain")
def api_fetch_domain(req: FetchDomainRequest, background_tasks: BackgroundTasks):
    """Trigger a full pipeline fetch for a specific domain."""
    if req.domain not in DOMAIN_META:
        return JSONResponse(
            status_code=400,
            content={"message": f"Unknown domain '{req.domain}'. Valid: {list(DOMAIN_META.keys())}"},
        )
    if is_pipeline_running():
        return {"status": "already_running", "message": "Pipeline is already in progress."}

    background_tasks.add_task(run_pipeline, domain=req.domain)
    meta = DOMAIN_META[req.domain]
    return {
        "status":  "fetch_started",
        "domain":  req.domain,
        "label":   meta["label"],
        "sources": len(DOMAIN_FEEDS.get(req.domain, [])),
        "message": f"Fetching {meta['label']} from {len(DOMAIN_FEEDS.get(req.domain, []))} sources...",
    }


@app.get("/api/news/refresh")
@app.post("/api/news/refresh")
def api_refresh(background_tasks: BackgroundTasks):
    """Manually trigger the AI domain fetch pipeline -- returns immediately, runs in background."""
    if is_pipeline_running():
        return {"status": "already_running", "message": "Pipeline is already in progress."}
    background_tasks.add_task(run_pipeline, domain="ai")
    return {"status": "refresh_started", "message": "Pipeline triggered -- check back in ~60 s"}


@app.get("/api/news/refresh/status")
def api_refresh_status():
    """Poll whether the pipeline is currently running."""
    return {"running": is_pipeline_running()}


@app.get("/api/news/backfill")
@app.post("/api/news/backfill")
def api_backfill(
    background_tasks: BackgroundTasks,
    limit: int = Query(50, ge=1, le=200, description="Max articles to back-fill"),
):
    """
    AI-summarize existing articles that have no ai_summary yet.
    Runs in background; uses Gemini API (requires GEMINI_API_KEY).
    """
    def _do_backfill():
        from .summarizer import backfill_ai_summaries
        arts = get_unsummarized(limit=limit)
        if not arts:
            print("Back-fill: nothing to do (all articles already summarized).")
            return
        print(f"Back-fill: processing {len(arts)} unsummarized articles ...")
        n = backfill_ai_summaries(arts)
        print(f"Back-fill complete: {n} articles updated.")

    background_tasks.add_task(_do_backfill)
    return {
        "status":  "backfill_started",
        "message": f"Back-filling up to {limit} unsummarized articles in background.",
    }


@app.get("/api/stats")
def api_stats():
    stats = get_stats()
    stats["domain_counts"] = get_domain_stats()
    return stats


@app.get("/api/feeds")
def api_feeds():
    return {"feeds": get_feeds()}


@app.get("/health")
def health():
    return {"status": "ok", "version": "3.0.0"}


class LinkedInPostRequest(BaseModel):
    url: str

@app.post("/api/news/linkedin-post")
def api_linkedin_post(req: LinkedInPostRequest):
    from .database import get_article_by_url
    from .summarizer import generate_linkedin_post
    import os
    import re

    art = get_article_by_url(req.url)
    if not art:
        return JSONResponse(status_code=404, content={"message": "Article not found in database"})

    res = generate_linkedin_post(art)
    if not res:
        return JSONResponse(status_code=500, content={"message": "Failed to generate LinkedIn post"})
    if "error" in res:
        return JSONResponse(status_code=500, content={"message": res["error"]})

    post_content = res.get("post_content", "")
    slug = res.get("slug", "aboutnews")
    if not slug.strip():
        slug = "aboutnews"

    out_dir = Path(__file__).parent.parent / "linkedin_posts"
    out_dir.mkdir(exist_ok=True)

    max_id = 0
    for f in os.listdir(out_dir):
        m = re.match(r"Post_(\d+)_", f)
        if m:
            val = int(m.group(1))
            if val > max_id:
                max_id = val

    next_id = max_id + 1
    fname = f"Post_{next_id}_{slug}.txt"
    fpath = out_dir / fname

    fpath.write_text(post_content, encoding="utf-8")

    return {
        "status":   "success",
        "content":  post_content,
        "filename": fname,
    }
