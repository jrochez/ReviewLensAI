import logging
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


def extract_themes(review_texts: list[str], top_n: int = 30) -> list[tuple[str, int]]:
    """Return top_n (theme, frequency_count) pairs using TF-IDF over review corpus."""
    if not review_texts:
        return []

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=200,
            min_df=2 if len(review_texts) >= 5 else 1,
        )
        tfidf_matrix = vectorizer.fit_transform(review_texts)
        feature_names = vectorizer.get_feature_names_out()

        # Average TF-IDF score per term across all documents
        avg_scores = tfidf_matrix.mean(axis=0).A1
        ranked = sorted(zip(feature_names, avg_scores), key=lambda x: x[1], reverse=True)
        top_terms = [term for term, _ in ranked[:top_n]]

        # Count frequency: how many reviews mention each term (as substring)
        term_counts = []
        for term in top_terms:
            count = sum(1 for text in review_texts if term.lower() in text.lower())
            term_counts.append((term, count))

        return sorted(term_counts, key=lambda x: x[1], reverse=True)

    except Exception as exc:
        logger.error("Theme extraction failed: %s", exc)
        # Fallback: simple word frequency
        counter: Counter = Counter()
        for text in review_texts:
            words = text.lower().split()
            stopwords = {"the", "a", "an", "and", "or", "but", "is", "it", "in", "on", "at", "to", "for", "of", "with", "this", "that", "was", "are", "be", "have", "has", "had", "not", "i", "my", "me", "we", "you", "your"}
            counter.update(w.strip(".,!?;:\"'") for w in words if w not in stopwords and len(w) > 3)
        return [(term, count) for term, count in counter.most_common(top_n)]
