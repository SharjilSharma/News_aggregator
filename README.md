# NeuroPulse v3 — Multi-Domain AI Intelligence Aggregator

> **60+ sources · 5 domains · Gemini AI summaries · One-click fetch · Free deployment**

[![Live Demo](https://img.shields.io/badge/Live_Demo-Render.com-46E3B7?style=for-the-badge)](https://neuropulse.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Gemini AI](https://img.shields.io/badge/Gemini_AI-2.0_Flash-8B5CF6?style=for-the-badge)](https://aistudio.google.com)

---

## 🚀 What This Is

NeuroPulse is an **agentic AI pipeline** that scrapes the internet across multiple domains and delivers summarized, categorized, deduplicated intelligence — in a single click.

| Domain | Sources | What it tracks |
|---|---|---|
| 🤖 **AI & ML** | 35+ | Models, research, lab blogs, newsletters, arXiv |
| 🛡️ **Cybersecurity** | 15+ | Vulnerabilities, exploits, threat intel, CVEs |
| 📈 **Finance & FinTech** | 14+ | Markets, fintech startups, banking tech |
| 🧬 **Biotech & Health** | 14+ | Drug trials, genomics, medical AI |
| ⛓️ **Web3 & Blockchain** | 14+ | Crypto, DeFi, protocol updates |

---

## ✨ Key Features

- **One-click domain fetch** — click any domain card to trigger a full live scrape
- **Gemini AI summaries** — every article gets a rewritten title + 2–3 sentence summary
- **Real-time progress** — animated fetch bar shows exactly what the pipeline is doing
- **Smart deduplication** — TF-IDF cosine similarity removes near-duplicate articles
- **NLP categorization** — KeyBERT + rule-based scoring categorizes every article
- **LinkedIn post generator** — AI generates ready-to-share posts from any article
- **Full-text extraction** — trafilatura pulls complete article text from 30+ sources
- **Auto-refresh** — background scheduler fetches AI/ML domain every 2 hours
- **Dark/light mode** — glassmorphism UI with smooth transitions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  User (Browser)                      │
│             clicks domain card → fetch               │
└──────────────────┬──────────────────────────────────┘
                   │ POST /api/news/fetch-domain
┌──────────────────▼──────────────────────────────────┐
│                FastAPI Backend                       │
│                                                     │
│  ┌────────────┐  ┌────────────┐  ┌───────────────┐ │
│  │  Fetcher   │  │Deduplicator│  │  Categorizer  │ │
│  │ (aiohttp)  │→ │ (TF-IDF)   │→ │ (KeyBERT+NLP) │ │
│  └────────────┘  └────────────┘  └───────┬───────┘ │
│       60+ RSS/Reddit/GitHub feeds        │         │
│                                  ┌───────▼───────┐  │
│                                  │  Gemini 2.0   │  │
│                                  │  Flash (AI)   │  │
│                                  └───────┬───────┘  │
│                                  ┌───────▼───────┐  │
│                                  │  SQLite DB    │  │
│                                  └───────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start (Local)

```bash
cd d:\webscraper\news_aggregator
"Start App.bat"
```

Then open **http://localhost:8000**

> First fetch + AI summarization begins in ~15 seconds.

---

## 🔑 API Keys

### Gemini API (AI Summaries) — FREE
1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **"Create API key"**
4. Add to `.env`: `GEMINI_API_KEY=your-key-here`

> Free tier: **1,500 requests/day, 1M tokens/day** — more than enough.

---

## 🌐 Deploy to Render.com (Free — Get a Live URL)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "NeuroPulse v3 — Multi-domain AI aggregator"
   git remote add origin https://github.com/YOUR_USERNAME/neuropulse.git
   git push -u origin main
   ```

2. **Connect to Render**
   - Go to [render.com](https://render.com) → New → Web Service
   - Connect your GitHub repo
   - Render auto-detects `render.yaml` — click **Deploy**

3. **Set environment variables** in Render dashboard:
   - `GEMINI_API_KEY` = your Gemini key
   - `DB_PATH` = `/data/news.db` (uses the persistent disk)

4. **Done!** Live at `https://neuropulse.onrender.com`

> ⚠️ **Free tier note**: Render spins down after 15 min of inactivity. First load may take ~30s.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/news` | Articles (`?domain=ai&category=all&limit=30&search=`) |
| GET | `/api/domains` | All domains with metadata + article counts |
| POST | `/api/news/fetch-domain` | Trigger domain fetch `{"domain":"cybersec"}` |
| GET/POST | `/api/news/refresh` | Trigger AI/ML fetch (legacy) |
| GET | `/api/news/refresh/status` | Pipeline running? |
| GET/POST | `/api/news/backfill` | AI-summarize existing articles |
| POST | `/api/news/linkedin-post` | Generate LinkedIn post `{"url":"..."}` |
| GET | `/api/stats` | Total articles, AI count, domain breakdown |
| GET | `/api/feeds` | Feed status + last fetch time |
| GET | `/health` | Health check |

---

## 📁 Project Structure

```
news_aggregator/
├── backend/
│   ├── main.py          — FastAPI app + all API endpoints
│   ├── fetcher.py       — Async RSS / Reddit / GitHub fetcher (domain-aware)
│   ├── summarizer.py    — Gemini 2.0 Flash + TF-IDF extractive fallback
│   ├── categorizer.py   — Rule-based + KeyBERT NLP categorization
│   ├── deduplicator.py  — TF-IDF cosine similarity deduplication
│   ├── scheduler.py     — APScheduler pipeline (2h auto-refresh)
│   ├── database.py      — SQLite + domain-aware queries
│   └── feeds_config.py  — 60+ sources across 5 domain bundles
├── frontend/
│   └── index.html       — SPA: domain cards, live fetch progress, AI cards
├── data/
│   └── news.db          — SQLite (auto-created, auto-migrated)
├── .env                 — API keys (DO NOT commit)
├── requirements.txt
├── render.yaml          — Render.com free deployment config
└── Procfile             — Railway/Heroku config
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **AI** | Google Gemini 2.0 Flash |
| **NLP** | KeyBERT, sentence-transformers, scikit-learn TF-IDF |
| **Scraping** | aiohttp (async), feedparser, trafilatura, BeautifulSoup |
| **Scheduling** | APScheduler |
| **Database** | SQLite (WAL mode, indexed) |
| **Frontend** | Vanilla HTML/CSS/JS (zero dependencies) |
| **Deployment** | Render.com (free tier, 1GB persistent disk) |

---

## 📄 Troubleshooting

**`ModuleNotFoundError: No module named 'backend'`**
→ Run from the `news_aggregator/` directory.

**AI summaries not appearing**
→ Check `GEMINI_API_KEY` in `.env`. Must be valid and not rate-limited.

**Reddit feeds return 429**
→ Reddit rate-limits anonymous access. Retries automatically on next cycle.

**Domain fetch seems stuck**
→ The progress bar runs client-side. Backend fetch takes 30–90s for a full domain. Be patient!

**Render.com free tier cold start**
→ First request after 15 min inactivity takes ~30s. Normal behavior.
