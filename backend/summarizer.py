"""
AI Summarisation -- two tiers:
  Tier 1: Google Gemini 2.0 Flash (free -- set GEMINI_API_KEY env var)
  Tier 2: Extractive TF-IDF sentence ranking (default fallback)

Batch-processes articles to minimise API calls.
Cache: articles with summarized_at set are never re-processed.
Rate limit: free tier = 15 RPM -> 4.5s delay between batches of 8.
"""

import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-2.0-flash"
BATCH_SIZE     = 8     # articles per single Gemini call
RATE_DELAY     = 4.5   # seconds between batches (15 RPM free tier)
MAX_PER_RUN    = 80    # max articles to AI-summarize per pipeline run

_model = None


def _get_model():
    """Lazy-load Gemini model (only if GEMINI_API_KEY is set)."""
    global _model
    if _model is None and GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            _model = genai.GenerativeModel(GEMINI_MODEL)
            print(f"[OK] Gemini {GEMINI_MODEL} ready")
        except Exception as e:
            print(f"[WARN] Gemini unavailable ({e}). Using extractive fallback.")
    return _model


# -- Extractive TF-IDF fallback -----------------------------------------------

def _split_sentences(text: str) -> List[str]:
    raw = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in raw if len(s.strip()) > 25]


def extractive_summarize(text: str, n: int = 3) -> Dict:
    sentences = _split_sentences(text)
    if not sentences:
        s = text.strip()
        return {"summary": s, "bullets": [s] if s else []}
    if len(sentences) <= n:
        return {"summary": " ".join(sentences), "bullets": sentences[:n]}
    try:
        vec    = TfidfVectorizer(stop_words="english")
        tfidf  = vec.fit_transform(sentences)
        scores = tfidf.sum(axis=1).A1
        top_idx = sorted(
            sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]
        )
        bullets = [sentences[i] for i in top_idx]
    except Exception:
        bullets = sentences[:n]
    return {"summary": " ".join(bullets), "bullets": bullets}


# -- Gemini batch call ---------------------------------------------------------

def _call_gemini_batch(model, articles: List[Dict]) -> None:
    """
    Send a batch to Gemini; mutates each article dict in-place with
    'ai_title' and 'ai_summary' keys. Fails silently on error.
    """
    block = ""
    for j, art in enumerate(articles, 1):
        raw_text = (art.get("raw_text") or art.get("summary") or "")[:1500]
        block += (
            f"\n---\nARTICLE {j}:\n"
            f"Source: {art.get('source', '')}\n"
            f"Title: {art.get('title', '')}\n"
            f"Content: {raw_text}\n"
        )

    prompt = f"""You are a tech/AI news analyst. For each article below, do two things:

1. Rewrite the title to be clear, human-readable, and self-contained (max 12 words).
   Rules:
   - Convert model card names like "mistralai/Mistral-7B-v0.3" to "Mistral Releases Mistral 7B v0.3 Language Model"
   - Convert GitHub repo slugs into plain-English project descriptions
   - Keep proper nouns (GPT-4, Gemini, NVIDIA H100, etc.)
   - Remove click-bait phrasing

2. Write a 2-3 sentence plain-English summary: WHAT happened, WHY it matters to the AI/tech community.
   Be concrete -- mention specific models, numbers, or claims when present.

{block}

Respond ONLY with a valid JSON array (no markdown, no code fences):
[{{"n":1,"title":"rewritten title","summary":"2-3 sentence summary"}}, ..., {{"n":{len(articles)},"title":"...","summary":"..."}}]"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown code fences if Gemini wraps the response
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:].strip()

        # Find the JSON array boundaries
        start = raw.find("[")
        end   = raw.rfind("]") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]

        parsed = json.loads(raw)
        for item in parsed:
            idx = int(item.get("n", 1)) - 1
            if 0 <= idx < len(articles):
                articles[idx]["ai_title"]   = (item.get("title")   or "").strip()
                articles[idx]["ai_summary"] = (item.get("summary") or "").strip()

    except Exception as e:
        print(f"  [ERR] Gemini batch error: {e}")
        # Articles remain with empty ai_title / ai_summary -- that's fine


# -- Public: pipeline batch summarizer ----------------------------------------

def batch_ai_summarize(articles: List[Dict]) -> List[Dict]:
    """
    AI-summarize a list of fresh article dicts (adds ai_title + ai_summary).
    Call this BEFORE insert_article so the AI fields are saved on first write.

    Falls back gracefully if Gemini is unavailable.
    Returns the same list (mutated in-place).
    """
    model = _get_model()

    # Ensure keys exist regardless of AI availability
    for art in articles:
        art.setdefault("ai_title", "")
        art.setdefault("ai_summary", "")
        art.setdefault("summarized_at", "")

    if not model:
        return articles

    to_process = articles[:MAX_PER_RUN]
    total      = len(to_process)

    for i in range(0, total, BATCH_SIZE):
        batch = to_process[i : i + BATCH_SIZE]
        n_end = min(i + BATCH_SIZE, total)
        print(f"  [AI] Gemini [{i+1}-{n_end} / {total}] ...")
        _call_gemini_batch(model, batch)

        # Mark summarized_at for each successfully processed article
        now = datetime.utcnow().isoformat()
        for art in batch:
            if art.get("ai_title") or art.get("ai_summary"):
                art["summarized_at"] = now

        if i + BATCH_SIZE < total:
            time.sleep(RATE_DELAY)

    return articles


# -- Public: back-fill unsummarized articles -----------------------------------

def backfill_ai_summaries(unsummarized: List[Dict]) -> int:
    """
    AI-summarize existing articles pulled from DB.
    Articles must have keys: url, title, source, summary.
    Updates the DB directly. Returns count of successfully summarized articles.
    """
    from .database import update_article_ai

    model = _get_model()
    if not model or not unsummarized:
        return 0

    # Build synthetic raw_text from stored data
    for art in unsummarized:
        art["raw_text"] = (
            (art.get("title") or "") + ". " + (art.get("summary") or "")
        ).strip()

    summarized = 0
    total = len(unsummarized)

    for i in range(0, total, BATCH_SIZE):
        batch = unsummarized[i : i + BATCH_SIZE]
        n_end = min(i + BATCH_SIZE, total)
        print(f"  [AI] Backfill [{i+1}-{n_end} / {total}] ...")
        _call_gemini_batch(model, batch)
        for art in batch:
            ai_title   = art.get("ai_title", "")
            ai_summary = art.get("ai_summary", "")
            if ai_title or ai_summary:
                update_article_ai(art["url"], ai_title, ai_summary)
                summarized += 1

        if i + BATCH_SIZE < total:
            time.sleep(RATE_DELAY)

    return summarized


# -- Public: legacy entry point (extractive only) -----------------------------

def summarize(text: str) -> Dict:
    """Extractive summary used during pipeline (fast, no API call)."""
    if not text or len(text) < 40:
        return {"summary": text or "", "bullets": [text] if text else []}
    return extractive_summarize(text)


# -- Public: LinkedIn Post Generation ------------------------------------------

def generate_linkedin_post(article: Dict) -> Optional[Dict]:
    """Generates a professional LinkedIn post from an article using Gemini."""
    model = _get_model()
    if not model:
        return None
        
    raw_text = (article.get("raw_text") or article.get("summary") or "")[:2000]
    title = article.get("title", "")
    url = article.get("url", "")
    
    prompt = f"""You are a friendly AI news writer who helps people understand technology in plain, simple words. Write a LinkedIn post about the following AI news article to share with followers who want to stay updated on AI — but are NOT experts.

Article Title: {title}
Article Content: {raw_text}
Article URL: {url}

Strict writing rules (follow ALL of these):
1. START with a punchy 1-line hook that makes people stop scrolling. Use everyday language. Examples: "OpenAI just dropped something BIG 🤯" or "AI can now do something that would have sounded like sci-fi 2 years ago."
2. EXPLAIN the news in simple words — like you are texting a smart friend who doesn\'t follow tech news. Avoid technical jargon. If you must use a term like "LLM" or "fine-tuning", explain it in one simple phrase right after.
3. COVER: What happened? What does it actually DO? Why should a regular person care?
4. Share a 🔥 personal opinion or insight — why is this exciting, surprising, or important?
5. End with a question to spark comments. Example: "What do you think — is this a game changer? 💬"
6. Add a "🔖 Tag Someone" line suggesting 1-2 roles to tag (e.g., "Tag a marketer or founder who needs to see this!").
7. Add 5-6 popular LinkedIn hashtags on the last line.
8. The very last line MUST be exactly: "Read the full article here: {url}"

Tone: Warm, excited, conversational. NOT corporate. NOT academic. Feel free to use emojis tastefully throughout.
Length: 150-250 words max. Short paragraphs. Easy to skim.

Also create a short lowercase slug for the filename (e.g., openai-sora-release, max 4 words, hyphens only).

Respond ONLY with a valid JSON object (no markdown fences) with keys:
- "post_content": the full LinkedIn post as a string.
- "slug": the short filename slug string.
"""
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:].strip()
                
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]
            
        return json.loads(raw)
    except Exception as e:
        err_str = str(e)
        if "quota" in err_str.lower() or "429" in err_str:
            return {"error": "Gemini Free Tier Rate Limit exceeded. Please wait a minute and try again."}
        print(f"  [ERR] LinkedIn generation error: {e}")
        return {"error": str(e)}
