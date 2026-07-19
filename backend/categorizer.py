"""
Categorisation (rule-based keyword scoring + source boosting)
and keyword extraction (KeyBERT with all-MiniLM-L6-v2, ~80 MB).
"""

import re
from typing import Dict, List

CATEGORY_RULES: Dict[str, List[str]] = {
    "AI Models": [
        "gpt", "llm", "llama", "mistral", "claude", "gemini", "phi",
        "qwen", "falcon", "vicuna", "model weights", "fine-tun",
        "foundation model", "language model", "multimodal", "vision model",
        "embedding", "tokenizer", "rlhf", "sft", "peft", "lora",
        "text-to-image", "diffusion model", "stable diffusion",
        "model release", "model card", "huggingface model",
    ],
    "ML Research": [
        "paper", "arxiv", "benchmark", "dataset", "training", "gradient",
        "neural network", "attention", "transformer", "algorithm",
        "loss function", "accuracy", "state-of-the-art", "ablation",
        "experiment", "few-shot", "zero-shot", "pre-train", "representation",
        "contrastive", "generalization", "overfitting", "backpropagation",
    ],
    "Products & Launches": [
        "launch", "release", "announc", "product", " app ", "platform",
        "tool", "beta", "version", "update", "feature", "available now",
        "introducing", "startup", "funding", "series a", "series b",
        "raises", "acquisition", "ipo", "valuation", "partnership",
    ],
    "Policy & Ethics": [
        "regulation", "safety", "alignment", "bias", "copyright",
        "governance", "eu ai act", "risk", "ethics", "responsible ai",
        "compliance", "fairness", "privacy", "gdpr", "policy", "law",
        "congress", "senate", "ban", "deepfake", "misinformation",
        "existential", "agi risk", "open letter",
    ],
    "Infra & Chips": [
        "nvidia", "gpu", "tpu", "chip", "hardware", "cuda", "h100",
        "a100", "b200", "compute", "amd", "intel", "semiconductor",
        "data center", "inference infra", "cloud", "bandwidth", "memory",
        "cooling", "rack", "server", "cluster", "silicon", "wafer", "foundry",
    ],
    "Open Source": [
        "open source", "open-source", "open weight", "apache license",
        "mit license", "github", "hugging face", "community",
        "repository", "fork", "pull request", "open model",
        "weights released", "open release", "llama.cpp", "ollama",
        "trending repo", "stars",
    ],
}

SOURCE_BOOST: Dict[str, str] = {
    "arxiv":              "ML Research",
    "papers with code":   "ML Research",
    "huggingface papers": "ML Research",
    "bair":               "ML Research",
    "github trending":    "Open Source",
    "huggingface models": "AI Models",
    "huggingface blog":   "AI Models",
    "openai":             "AI Models",
    "anthropic":          "AI Models",
    "deepmind":           "ML Research",
    "meta ai":            "AI Models",
    "mistral":            "AI Models",
    "stanford hai":       "Policy & Ethics",
    "future of life":     "Policy & Ethics",
    "ai now":             "Policy & Ethics",
    "nvidia":             "Infra & Chips",
    "anandtech":          "Infra & Chips",
    "tom's hardware":     "Infra & Chips",
    "semiengineering":    "Infra & Chips",
    "reddit":             None,
}


def categorize(article: Dict) -> str:
    text   = (article.get("title", "") + " " + article.get("raw_text", "")).lower()
    source = article.get("source", "").lower()

    scores: Dict[str, float] = {cat: 0.0 for cat in CATEGORY_RULES}
    for cat, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw in text:
                scores[cat] += 1

    for src_key, cat in SOURCE_BOOST.items():
        if src_key in source and cat:
            scores[cat] = scores.get(cat, 0) + 5

    best_cat = max(scores, key=lambda c: scores[c])
    return best_cat if scores[best_cat] > 0 else "Other"


_kw_model = None


def _get_kw_model():
    global _kw_model
    if _kw_model is None:
        from keybert import KeyBERT
        print("Loading KeyBERT (all-MiniLM-L6-v2, ~80 MB first run) ...")
        _kw_model = KeyBERT(model="all-MiniLM-L6-v2")
        print("KeyBERT loaded OK")
    return _kw_model


def _tfidf_keywords(text: str, n: int) -> List[str]:
    words = re.findall(r"\b[a-z]{4,}\b", text.lower())
    freq: Dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    stopwords = {
        "this", "that", "with", "from", "have", "been", "will",
        "their", "they", "what", "when", "also", "more", "which",
    }
    ranked = sorted(
        [w for w in freq if w not in stopwords],
        key=lambda w: freq[w], reverse=True,
    )
    return ranked[:n]


def extract_keywords(text: str, n: int = 6) -> List[str]:
    if not text or len(text) < 50:
        return []
    try:
        model = _get_kw_model()
        kws = model.extract_keywords(
            text[:2000],
            keyphrase_ngram_range=(1, 2),
            stop_words="english",
            top_n=n,
        )
        return [kw[0] for kw in kws] if kws else _tfidf_keywords(text, n)
    except Exception as e:
        print(f"KeyBERT error: {e} -- using TF fallback")
        return _tfidf_keywords(text, n)
