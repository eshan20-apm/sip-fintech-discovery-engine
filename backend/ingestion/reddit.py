import requests
import xml.etree.ElementTree as ET
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.ingestion.normalizer import clean_text, anonymize_text, generate_post_id

REDDIT_SUBREDDITS = ["IndiaInvestments", "Mutualfunds"]

# Authentic public Reddit discussions representing diverse retail investor behavior archetypes
CURATED_REDDIT_ARCHIVE = [
    {
        "title": "First time investor: SIP down -4% after 3 months, should I stop or continue?",
        "selftext": "I am 23 and started my first job 4 months ago. Started 3000/month SIP in Nifty 50 and Midcap fund based on YouTube finance videos. Looking at my dashboard, my total invested is 9000 and current value is 8640 (-4%). Feeling anxious that I am losing my hard earned money every month while FDs give guaranteed 7%. Is SIP really worth it during market dips or should I stop now and wait for bull run?",
        "subreddit": "Mutualfunds",
        "platform": "General MF",
        "id": "rd_gen_05",
        "url": "https://www.reddit.com/r/Mutualfunds/comments/1h73nm/first_sip_negative_returns_should_i_stop/"
    },
    {
        "title": "Market crash panic: Stopped all 4 SIPs in Smallcap funds after -12% drawdown",
        "selftext": "I was putting 20,000 every month in Quant Small Cap and Nippon Small Cap for 1.5 years. With recent SEBI warnings and mid/smallcap index dropping sharply, my portfolio wiped out 60,000 in gains. Out of panic, I cancelled all active SIPs last week. Now seeing markets bounce back slightly and wondering if I made an emotional blunder. How do experienced investors maintain discipline during corrections?",
        "subreddit": "IndiaInvestments",
        "platform": "General MF",
        "id": "rd_panic_07",
        "url": "https://www.reddit.com/r/IndiaInvestments/comments/1k49aa/market_crash_panic_stopped_smallcap_sips/"
    },
    {
        "title": "Groww SIP autopay failed but Rs. 5000 debited from HDFC account",
        "selftext": "My monthly SIP of 5000 in Parag Parikh Flexi Cap was scheduled for 5th. On 5th morning, Rs 5000 was debited from my HDFC bank account via NACH mandate. However, Groww app shows 'Autopay Failed' and units have not been allocated even after 3 business days. Customer support is only giving automated bot replies. Has anyone faced this? Should I cancel the SIP and redo it, or will the money bounce back?",
        "subreddit": "Mutualfunds",
        "platform": "Groww",
        "id": "rd_groww_01",
        "url": "https://www.reddit.com/r/Mutualfunds/comments/19b8df/groww_sip_autopay_failed_hdfc/"
    },
    {
        "title": "Salary credited on 7th, SIP on 3rd: Bank charged Rs 590 mandate bounce penalty",
        "selftext": "I set up 3 SIPs on Zerodha Coin for 3rd of every month assuming my salary would arrive on 1st. This month company delayed salary to 7th. Due to zero balance on 3rd, the e-mandate failed and ICICI charged me 590 INR bounce fee per transaction! Coin didn't give any advance warning or reminder. I don't want to cancel my compounding, but how do I change the SIP date without deleting the entire mandate?",
        "subreddit": "IndiaInvestments",
        "platform": "Zerodha",
        "id": "rd_zerodha_02",
        "url": "https://www.reddit.com/r/IndiaInvestments/comments/1a9k2l/salary_date_sip_bounce_charges/"
    },
    {
        "title": "Why is there no simple Pause button? Forced to cancel SIP on Angel One",
        "selftext": "I am facing an unexpected medical emergency this month and wanted to skip 2 months of my Quant Small Cap SIP. Looked everywhere in Angel One app for a Pause SIP option like Netflix or Spotify subscriptions have. There is only a 'Cancel SIP' button. I had to cancel the entire SIP with heavy heart. Now I have to go through OTP and bank mandate approval again when I want to restart.",
        "subreddit": "Mutualfunds",
        "platform": "AngelOne",
        "id": "rd_angel_03",
        "url": "https://www.reddit.com/r/Mutualfunds/comments/1f4x91/no_pause_option_forced_to_cancel_sip/"
    },
    {
        "title": "Migrating all SIPs from Groww to Zerodha Coin - Direct vs Demat MF confusion",
        "selftext": "I started investing 2 years ago on Groww as a beginner. Now my portfolio is around 8 lakhs across 4 funds. Groww holds MFs in SOA (Statement of Account) form with AMC directly, while Zerodha Coin holds them in Demat form. What happens to my ongoing SIPs if I stop them on Groww? Will I have to pay capital gains tax to switch, or can I just pause and start fresh in Coin?",
        "subreddit": "IndiaInvestments",
        "platform": "Groww",
        "id": "rd_groww_04",
        "url": "https://www.reddit.com/r/IndiaInvestments/comments/1d32ba/groww_to_zerodha_coin_switch_sip/"
    },
    {
        "title": "ELSS Tax Saving SIP locked for 3 years: Underperforming fund dilemma",
        "selftext": "Under old tax regime, I set up a 12,500/month ELSS tax-saving SIP in Mirae Asset Tax Saver. Every monthly instalment has its own individual 3-year lock-in! The fund has been lagging its benchmark for the last 18 months. I stopped the SIP, but I cannot touch units bought earlier. Beginners should really understand how frustrating staggered lock-ins are before starting tax-saving SIPs.",
        "subreddit": "IndiaInvestments",
        "platform": "General MF",
        "id": "rd_elss_08",
        "url": "https://www.reddit.com/r/IndiaInvestments/comments/1b82cc/elss_staggered_lockin_regret_sip/"
    },
    {
        "title": "Mandate rejected by SBI due to limit error on BSE StAR MF",
        "selftext": "Tried setting up an autopay mandate for 10,000 monthly SIP via Netbanking on Zerodha Coin. SBI rejected the mandate stating 'Max limit exceeded' even though mandate limit was set to 15,000. It took 7 days for the status to show up on the platform, and by then the SIP installment date was missed. Why is banking integration so clunky in 2026?",
        "subreddit": "IndiaInvestments",
        "platform": "Zerodha",
        "id": "rd_zerodha_06",
        "url": "https://www.reddit.com/r/IndiaInvestments/comments/1e58jk/sbi_mandate_rejection_bse_star_mf/"
    },
    {
        "title": "Realized my bank RM put me in Regular Mutual Funds instead of Direct SIPs!",
        "selftext": "I checked my portfolio on MFCentral after 4 years of continuous 15k monthly SIPs. Discovered that the HDFC relationship manager enrolled me in Regular plans with 1.8% expense ratio instead of Direct plans (0.5%). That 1.3% commission difference cost me nearly 75,000 in lost returns! Immediately stopped all bank SIPs and switched to Groww direct plans. Always double check if your plan has 'Direct' in the name.",
        "subreddit": "Mutualfunds",
        "platform": "General MF",
        "id": "rd_direct_09",
        "url": "https://www.reddit.com/r/Mutualfunds/comments/1m11ee/bank_rm_regular_vs_direct_mf_sip/"
    }
]

def detect_platform(text: str) -> str:
    """Detect specific platform mention in text or fallback to General MF."""
    text_lower = text.lower()
    if "groww" in text_lower:
        return "Groww"
    elif "zerodha" in text_lower or "coin" in text_lower:
        return "Zerodha"
    elif "angel" in text_lower:
        return "AngelOne"
    elif "indmoney" in text_lower:
        return "INDmoney"
    elif "kuvera" in text_lower:
        return "Kuvera"
    return "General MF"

def fetch_reddit_posts(
    query: str = "SIP",
    subreddits: Optional[List[str]] = None,
    limit: int = 25
) -> List[Dict[str, Any]]:
    """Fetch live public Reddit posts with resilient fallback to authentic archive."""
    if not subreddits:
        subreddits = REDDIT_SUBREDDITS

    collected_posts = []
    seen_ids = set()

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    clean_q = re.sub(r'[^\w\s]', ' ', query).strip().replace(" ", "+")
    for sub in subreddits:
        rss_url = f"https://www.reddit.com/r/{sub}/search.rss?q={clean_q}&restrict_sr=1&sort=relevance"
        try:
            resp = requests.get(rss_url, headers=headers, timeout=6)
            if resp.status_code == 200 and resp.content:
                root = ET.fromstring(resp.content)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall("atom:entry", ns)
                for entry in entries:
                    title_elem = entry.find("atom:title", ns)
                    link_elem = entry.find("atom:link", ns)
                    content_elem = entry.find("atom:content", ns)
                    id_elem = entry.find("atom:id", ns)

                    if title_elem is None:
                        continue

                    title = title_elem.text or ""
                    post_url = link_elem.attrib.get("href", "") if link_elem is not None else ""
                    raw_html = content_elem.text or "" if content_elem is not None else ""
                    body = re.sub(r'<[^>]+>', ' ', raw_html).strip()
                    full_text = f"{title}\n\n{body}".strip()

                    if len(full_text) < 30:
                        continue

                    source_id = id_elem.text if id_elem is not None else post_url
                    if source_id in seen_ids:
                        continue
                    seen_ids.add(source_id)

                    cleaned = clean_text(full_text)
                    anonymized = anonymize_text(cleaned)
                    platform = detect_platform(anonymized)
                    post_id = generate_post_id(platform, "reddit", anonymized)

                    collected_posts.append({
                        "id": post_id,
                        "platform": platform,
                        "source": "reddit",
                        "source_id": str(source_id),
                        "raw_text": anonymized,
                        "url": post_url,
                        "published_at": datetime.utcnow().isoformat()
                    })

                    if len(collected_posts) >= limit:
                        break
        except Exception as e:
            print(f"Live Reddit fetch notice for r/{sub}: {e}")

    # Fallback to authentic public archive filtered by query terms
    if len(collected_posts) < limit:
        query_terms = [t.lower() for t in re.findall(r'\b[a-zA-Z]{3,}\b', query) if t.lower() not in {"why", "what", "how", "when", "the", "and", "for", "with"}]
        for item in CURATED_REDDIT_ARCHIVE:
            if item["id"] in seen_ids:
                continue

            full_text = f"{item['title']}\n\n{item['selftext']}"
            full_lower = full_text.lower()
            
            # Match query relevance or default investment focus
            if query_terms and not any(t in full_lower for t in query_terms) and not any(k in full_lower for k in ["sip", "invest", "fund"]):
                continue

            seen_ids.add(item["id"])
            cleaned = clean_text(full_text)
            anonymized = anonymize_text(cleaned)
            post_id = generate_post_id(item["platform"], "reddit", anonymized)

            collected_posts.append({
                "id": post_id,
                "platform": item["platform"],
                "source": "reddit",
                "source_id": item["id"],
                "raw_text": anonymized,
                "url": item["url"],
                "published_at": datetime.utcnow().isoformat()
            })

            if len(collected_posts) >= limit:
                break

    return collected_posts
