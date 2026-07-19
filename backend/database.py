"""SQLite database layer -- all queries live here."""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Allow DB path override via environment (useful for cloud deployments)
_env_path = os.getenv("DB_PATH", "")
DB_PATH = Path(_env_path) if _env_path else Path(__file__).parent.parent / "data" / "news.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Safely add new columns that did not exist in earlier versions."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(articles)").fetchall()}
    new_cols = {
        "ai_title":     "TEXT DEFAULT ''",
        "ai_summary":   "TEXT DEFAULT ''",
        "summarized_at":"TEXT DEFAULT ''",
        "domain":        "TEXT DEFAULT 'ai'",
    }
    for col, defn in new_cols.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE articles ADD COLUMN {col} {defn}")
            print(f"  [+] DB migrated: added column '{col}'")


def init_db() -> None:
    conn = get_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                title         TEXT    NOT NULL,
                url           TEXT    UNIQUE NOT NULL,
                source        TEXT    DEFAULT '',
                category      TEXT    DEFAULT 'Other',
                domain        TEXT    DEFAULT 'ai',
                summary       TEXT    DEFAULT '',
                bullets       TEXT    DEFAULT '[]',
                keywords      TEXT    DEFAULT '[]',
                published_at  TEXT    DEFAULT '',
                fetched_at    TEXT    DEFAULT (datetime('now')),
                content_hash  TEXT    DEFAULT '',
                ai_title      TEXT    DEFAULT '',
                ai_summary    TEXT    DEFAULT '',
                summarized_at TEXT    DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feed_status (
                url           TEXT PRIMARY KEY,
                name          TEXT,
                last_fetched  TEXT,
                article_count INTEGER DEFAULT 0,
                error         TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_category  ON articles(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_fetched   ON articles(fetched_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC)")
        _migrate(conn)  # adds new columns if not present
        # Create indexes after migration guarantees the columns exist
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_summarized ON articles(summarized_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_domain     ON articles(domain)")
    conn.close()
    print("Database initialised OK")


# -- Write operations ---------------------------------------------------------

def insert_article(article: Dict) -> bool:
    """Insert an article; return True if inserted, False if duplicate URL."""
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
                INSERT OR IGNORE INTO articles
                    (title, url, source, category, domain, summary, bullets, keywords,
                     published_at, content_hash, ai_title, ai_summary, summarized_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article.get("title", ""),
                article.get("url", ""),
                article.get("source", ""),
                article.get("category", "Other"),
                article.get("domain", "ai"),
                article.get("summary", ""),
                json.dumps(article.get("bullets", [])),
                json.dumps(article.get("keywords", [])),
                article.get("published_at", ""),
                article.get("content_hash", ""),
                article.get("ai_title", ""),
                article.get("ai_summary", ""),
                article.get("summarized_at", ""),
            ))
        return True
    except Exception as e:
        print(f"DB insert error: {e}")
        return False
    finally:
        conn.close()


def update_article_ai(url: str, ai_title: str, ai_summary: str) -> None:
    """Update an article's AI-generated title and summary."""
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE articles SET ai_title=?, ai_summary=?, summarized_at=? WHERE url=?",
                (ai_title, ai_summary, datetime.utcnow().isoformat(), url),
            )
    finally:
        conn.close()


def update_feed_status(url: str, name: str, count: int, error: Optional[str] = None) -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO feed_status (url, name, last_fetched, article_count, error)
                VALUES (?, ?, ?, ?, ?)
            """, (url, name, datetime.utcnow().isoformat(), count, error))
    finally:
        conn.close()


# -- Read operations ----------------------------------------------------------

def get_article_by_url(url: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM articles WHERE url = ?", [url]).fetchone()
        if not row:
            return None
        a = dict(row)
        a["bullets"]  = json.loads(a.get("bullets")  or "[]")
        a["keywords"] = json.loads(a.get("keywords") or "[]")
        return a
    finally:
        conn.close()

def filter_known_urls(articles: List[Dict]) -> List[Dict]:
    """Return only articles whose URLs are not already stored."""
    if not articles:
        return []
    conn = get_connection()
    try:
        urls = [a["url"] for a in articles]
        placeholders = ",".join("?" * len(urls))
        existing = {
            row["url"]
            for row in conn.execute(
                f"SELECT url FROM articles WHERE url IN ({placeholders})", urls
            ).fetchall()
        }
        return [a for a in articles if a["url"] not in existing]
    finally:
        conn.close()


def get_recent_titles(limit: int = 500) -> List[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT title FROM articles ORDER BY fetched_at DESC LIMIT ?", [limit]
        ).fetchall()
        return [r["title"] for r in rows]
    finally:
        conn.close()


def get_unsummarized(limit: int = 50) -> List[Dict]:
    """Return articles that haven't been AI-summarized yet."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT id, title, url, source, summary, category
            FROM articles
            WHERE (summarized_at IS NULL OR summarized_at = '')
            ORDER BY fetched_at DESC LIMIT ?
        """, [limit]).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_articles(
    category: str = "all",
    domain: str = "all",
    limit: int = 30,
    offset: int = 0,
    search: str = "",
) -> List[Dict]:
    conn = get_connection()
    try:
        query = "SELECT * FROM articles WHERE 1=1"
        params: list = []

        if domain and domain != "all":
            query += " AND domain = ?"
            params.append(domain)

        if category and category != "all":
            query += " AND category = ?"
            params.append(category)

        if search:
            query += (
                " AND (title LIKE ? OR ai_title LIKE ? OR source LIKE ?"
                " OR keywords LIKE ? OR ai_summary LIKE ?)"
            )
            s = f"%{search}%"
            params += [s, s, s, s, s]

        # Timestamp fix: order by actual publish date, fall back to fetch time
        query += """
            ORDER BY COALESCE(
                NULLIF(TRIM(published_at), ''),
                fetched_at
            ) DESC
            LIMIT ? OFFSET ?
        """
        params += [limit, offset]

        rows = conn.execute(query, params).fetchall()
        result = []
        for row in rows:
            a = dict(row)
            a["bullets"]  = json.loads(a.get("bullets")  or "[]")
            a["keywords"] = json.loads(a.get("keywords") or "[]")
            result.append(a)
        return result
    finally:
        conn.close()


def get_total_count(category: str = "all", domain: str = "all", search: str = "") -> int:
    conn = get_connection()
    try:
        query = "SELECT COUNT(*) AS c FROM articles WHERE 1=1"
        params: list = []
        if domain and domain != "all":
            query += " AND domain = ?"
            params.append(domain)
        if category and category != "all":
            query += " AND category = ?"
            params.append(category)
        if search:
            query += " AND (title LIKE ? OR ai_title LIKE ? OR keywords LIKE ?)"
            s = f"%{search}%"
            params += [s, s, s]
        return conn.execute(query, params).fetchone()["c"]
    finally:
        conn.close()


def get_domain_stats() -> Dict:
    """Return article count per domain."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT domain, COUNT(*) AS c FROM articles GROUP BY domain ORDER BY c DESC"
        ).fetchall()
        return {r["domain"]: r["c"] for r in rows}
    finally:
        conn.close()


def get_stats() -> Dict:
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) AS c FROM articles").fetchone()["c"]
        summarized = conn.execute(
            "SELECT COUNT(*) AS c FROM articles WHERE summarized_at != '' AND summarized_at IS NOT NULL"
        ).fetchone()["c"]
        by_cat = conn.execute(
            "SELECT category, COUNT(*) AS c FROM articles GROUP BY category ORDER BY c DESC"
        ).fetchall()
        last_updated = conn.execute(
            "SELECT MAX(fetched_at) AS t FROM articles"
        ).fetchone()["t"]
        return {
            "total":       total,
            "summarized":  summarized,
            "by_category": {r["category"]: r["c"] for r in by_cat},
            "last_updated": last_updated,
        }
    finally:
        conn.close()


def get_feeds() -> List[Dict]:
    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM feed_status ORDER BY name").fetchall()]
    finally:
        conn.close()
