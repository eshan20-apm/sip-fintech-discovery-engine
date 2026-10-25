import re
import hashlib
from typing import List, Dict, Any, Set, Tuple

STOPWORDS = {
    'the', 'is', 'was', 'are', 'were', 'a', 'an', 'and', 'or', 'in', 'on', 'at',
    'to', 'for', 'of', 'with', 'by', 'my', 'your', 'it', 'this', 'that', 'i', 'me', 'we'
}

SPAM_PATTERNS = [
    r't\.me/[a-zA-Z0-9_+]+',
    r'telegram(?:\.me|:\s*@)',
    r'whatsapp(?:\s*no|\.com|\s*group|\s*link)',
    r'(?:call|dm|message)\s*(?:me\s*on|for\s*tips)',
    r'(?:crypto|forex|binary|guaranteed\s*returns\s*daily)',
    r'(?:subscribe|click\s*the\s*link\s*below|free\s*signals|jackpot\s*call)',
    r'(?:trading\s*group|vip\s*channel|daily\s*profit\s*guarantee)'
]

def is_spam(text: str) -> bool:
    """Filter out promotional Telegram links, WhatsApp spam, and bot advertisements."""
    if len(text.strip()) < 20:
        return True
    text_lower = text.lower()
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False

def compute_token_set(text: str) -> Set[str]:
    """Extract set of normalized alphanumeric tokens without common noise stopwords."""
    words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', text.lower())
    return {w for w in words if w not in STOPWORDS}

def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Calculate Jaccard similarity between two token sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def deduplicate_posts(posts: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> Tuple[List[Dict[str, Any]], int]:
    """
    Deduplicates a list of posts:
    1. Removes bot spam & promotional links
    2. Performs SHA-256 exact match deduplication
    3. Performs fuzzy Jaccard similarity match (>85% token match) to drop duplicate cross-posts
    Returns: (clean_posts, dropped_count)
    """
    clean_posts = []
    seen_hashes = set()
    seen_token_sets: List[Tuple[Set[str], str]] = []
    dropped_count = 0

    for post in posts:
        raw_text = post.get("raw_text", "")
        if is_spam(raw_text):
            dropped_count += 1
            continue

        # 1. Exact SHA-256 match
        norm_text = re.sub(r'\s+', ' ', raw_text.lower()).strip()
        h = hashlib.sha256(norm_text.encode('utf-8')).hexdigest()
        if h in seen_hashes:
            dropped_count += 1
            continue

        # 2. Fuzzy similarity check
        token_set = compute_token_set(norm_text)
        is_duplicate = False
        for existing_set, _ in seen_token_sets:
            sim = jaccard_similarity(token_set, existing_set)
            if sim >= similarity_threshold:
                is_duplicate = True
                break

        if is_duplicate:
            dropped_count += 1
            continue

        seen_hashes.add(h)
        seen_token_sets.append((token_set, post.get("id", "")))
        clean_posts.append(post)

    return clean_posts, dropped_count
