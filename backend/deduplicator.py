"""
Title-similarity deduplication using TF-IDF cosine similarity.
Filters articles whose titles are too similar to existing ones.
"""

from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SIMILARITY_THRESHOLD = 0.75


def deduplicate(new_articles: List[Dict], existing_titles: List[str]) -> List[Dict]:
    """
    Remove articles from new_articles whose titles are too similar to
    existing_titles or to each other. Returns filtered list.
    """
    if not new_articles:
        return []

    # Start with existing titles as the "seen" set
    seen_titles = list(existing_titles)
    unique: List[Dict] = []

    for article in new_articles:
        title = article.get("title", "").strip()
        if not title:
            continue

        if not seen_titles:
            seen_titles.append(title)
            unique.append(article)
            continue

        try:
            vec   = TfidfVectorizer(stop_words="english")
            all_t = seen_titles + [title]
            tfidf = vec.fit_transform(all_t)
            # Compare the last title against all seen titles
            sims  = cosine_similarity(tfidf[-1], tfidf[:-1]).flatten()
            if sims.max() < SIMILARITY_THRESHOLD:
                seen_titles.append(title)
                unique.append(article)
        except Exception:
            # If vectorisation fails (e.g. all stop words), just include the article
            seen_titles.append(title)
            unique.append(article)

    return unique
