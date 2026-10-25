import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from google_play_scraper import reviews, Sort
from backend.ingestion.normalizer import clean_text, anonymize_text, generate_post_id

PLAYSTORE_APPS = {
    "Groww": "com.nextbillion.groww",
    "Zerodha": "com.zerodha.coin",
    "AngelOne": "com.msf.angelmobile",
    "INDmoney": "in.indwealth",
    "PaytmMoney": "com.paytmmoney"
}

BROAD_INVESTMENT_KEYWORDS = [
    "sip", "mutual fund", "fund", "money", "invest", "investment", "portfolio",
    "bank", "account", "order", "charge", "fee", "loss", "profit", "return",
    "market", "units", "transaction", "payment", "mandate", "autopay", "cancel",
    "pause", "stop", "fail", "kyc", "switch", "demat", "bse"
]

def fetch_playstore_reviews(
    platform: str,
    query: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    count: int = 30
) -> List[Dict[str, Any]]:
    """Fetch live reviews from Google Play Store for the given platform targeting user behavior topics."""
    app_id = PLAYSTORE_APPS.get(platform)
    if not app_id:
        return []

    collected_posts = []
    seen_hashes = set()

    # Build active keyword set from researcher query
    active_terms = []
    if keywords:
        for kw in keywords:
            active_terms.extend([w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', kw.lower()) if len(w) > 2])
    if query and query.strip():
        active_terms.extend([w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()) if len(w) > 2])

    active_terms = list(dict.fromkeys(active_terms))

    try:
        # Check ratings 1, 2, 3 where frictions and candid behavioral feedback are concentrated
        for score in [1, 2, 3]:
            batch, _ = reviews(
                app_id,
                lang='en',
                country='in',
                sort=Sort.NEWEST,
                filter_score_with=score,
                count=max(count * 2, 50)
            )

            for r in batch:
                raw_content = r.get("content", "")
                if not raw_content or len(raw_content.strip()) < 25:
                    continue

                content_lower = raw_content.lower()

                # If specific research terms provided, prioritize them
                if active_terms:
                    # Match if any active term appears OR if general investment keyword appears
                    matches_term = any(t in content_lower for t in active_terms)
                    matches_general = any(k in content_lower for k in BROAD_INVESTMENT_KEYWORDS)
                    if not (matches_term or matches_general):
                        continue
                else:
                    if not any(k in content_lower for k in BROAD_INVESTMENT_KEYWORDS):
                        continue

                cleaned = clean_text(raw_content)
                anonymized = anonymize_text(cleaned)

                # Deduplicate within batch
                h = anonymized[:80]
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)

                post_id = generate_post_id(platform, "playstore", anonymized)
                pub_date = r.get("at")
                pub_str = pub_date.isoformat() if isinstance(pub_date, datetime) else str(pub_date or "")

                review_id = str(r.get("reviewId", post_id))
                url = f"https://play.google.com/store/apps/details?id={app_id}&reviewId={review_id}"

                collected_posts.append({
                    "id": post_id,
                    "platform": platform,
                    "source": "playstore",
                    "source_id": review_id,
                    "raw_text": anonymized,
                    "url": url,
                    "published_at": pub_str,
                    "score": r.get("score")
                })

                if len(collected_posts) >= count:
                    break

            if len(collected_posts) >= count:
                break

    except Exception as e:
        print(f"Error fetching Play Store reviews for {platform} ({app_id}): {e}")

    return collected_posts
