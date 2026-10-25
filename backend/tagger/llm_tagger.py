import os
import json
import re
from typing import Dict, Any, Optional, List

SYSTEM_PROMPT = """You are a senior Fintech Product Management Research Assistant specializing in retail investor behavior, Systematic Investment Plans (SIPs), and Indian mutual fund platforms (Groww, Zerodha Coin, Angel One, INDmoney, Kuvera, Paytm Money).

Your role is to analyze an unstructured public investor comment/review and extract dynamic behavioral tags. Do NOT force the comment into pre-determined categories. The tags must be completely dependent on what the raw comment actually discusses.

Output MUST be valid JSON with this schema:

{
  "theme": "string (A concise 2 to 3 word tag describing the specific problem, friction, or topic, e.g. 'Market dip panic', 'Autopay bounce charge', 'SOA vs Demat switch', 'SIP date mismatch', 'KYC rejection', 'Negative return anxiety', 'Option to pause missing')",
  "journey_stage": "string (The investor's journey stage inferred from context, e.g. 'Onboarding / KYC', '1st Month Bull Run', 'Months 2-6 Market Dip', 'Year 2+ Experienced', 'Platform Migration', 'Exit / Withdrawal', 'Unclear')",
  "what_they_did": "string (The action taken or contemplated by the investor, e.g. 'Cancelled SIP', 'Switched to Coin', 'Paused indefinitely', 'Continued despite dip', 'Withdrew capital', 'Complained to support', 'Unsure')",
  "who_they_are": "string (Short descriptive persona, e.g. 'Salaried beginner, 23yo', 'Seasoned DIY investor, NRI', 'Student', or 'Unclear')",
  "who_can_fix_it": "string (Entity responsible, e.g. 'Fintech Platform', 'Bank or AMC', 'User life situation', 'Regulator (SEBI/RBI)', or 'Unclear')",
  "evidence_quote": "string (MUST be an EXACT verbatim substring copied word-for-word from the raw text justifying the tags)"
}

CRITICAL RULES:
1. Zero Hallucination: "evidence_quote" MUST be an exact verbatim substring from the provided raw text. Do not paraphrase or alter a single letter.
2. Dynamic Theme: Tag the core problem in 2-3 words based on the comment's content. Do not use generic buckets.
3. Be grounded: If the persona or action is not mentioned, use 'Unclear' or 'Unsure'.
"""

QUERY_ANALYSIS_PROMPT = """You are a search query strategist for Fintech Product Management research.
A researcher has provided a question or topic about SIP (Systematic Investment Plan) investor behavior in India.
Analyze their query and output valid JSON with:
1. "target_platforms": list of specific apps to search (from ["Groww", "Zerodha", "AngelOne", "INDmoney", "Kuvera"]). If the researcher asks generally without mentioning a specific app, return ["Groww", "Zerodha", "AngelOne"].
2. "search_keywords": list of 3 to 6 distinct keyword phrases optimized for searching Google Play Store reviews and Reddit discussions (e.g. ["market crash SIP", "stop SIP loss", "portfolio negative", "SIP pause option"]).
3. "intent_summary": 1 short sentence summarizing what behavioral insight the researcher is seeking.

Output format:
{
  "target_platforms": ["Groww", "Zerodha", ...],
  "search_keywords": ["keyword 1", "keyword 2", ...],
  "intent_summary": "Investigating why..."
}
"""

def analyze_research_query(query: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Analyze a researcher's conversational query to derive target apps and search keywords."""
    active_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    # Domain heuristic fallback
    q_lower = query.lower()
    detected_platforms = []
    if "groww" in q_lower:
        detected_platforms.append("Groww")
    if "zerodha" in q_lower or "coin" in q_lower:
        detected_platforms.append("Zerodha")
    if "angel" in q_lower:
        detected_platforms.append("AngelOne")
    if "indmoney" in q_lower:
        detected_platforms.append("INDmoney")
    if "kuvera" in q_lower:
        detected_platforms.append("Kuvera")

    if not detected_platforms:
        detected_platforms = ["Groww", "Zerodha", "AngelOne"]

    # Extract meaningful keywords from query
    clean_words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', q_lower) if w not in {"why", "what", "how", "when", "the", "and", "for", "with", "from", "user", "users", "people", "investor", "investors"}]
    search_keywords = [query]
    if len(clean_words) >= 2:
        search_keywords.append(" ".join(clean_words[:3]))
    search_keywords.append("SIP " + " ".join(clean_words[:2]))

    default_analysis = {
        "target_platforms": detected_platforms,
        "search_keywords": list(dict.fromkeys(search_keywords))[:5],
        "intent_summary": f"Researching: {query.strip()}"
    }

    if not active_key:
        return default_analysis

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=active_key)
        prompt = f"{QUERY_ANALYSIS_PROMPT}\n\nRESEARCHER QUERY:\n\"\"\"{query}\"\"\""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        parsed = json.loads(response.text.strip())
        return {
            "target_platforms": parsed.get("target_platforms") or detected_platforms,
            "search_keywords": parsed.get("search_keywords") or search_keywords,
            "intent_summary": parsed.get("intent_summary") or default_analysis["intent_summary"]
        }
    except Exception as e:
        print(f"Error in Gemini query analysis, using fallback: {e}")
        return default_analysis

def dynamic_heuristic_tagger(raw_text: str) -> Dict[str, Any]:
    """Generates dynamic 2-3 word themes and contextual stages without rigid buckets."""
    text_lower = raw_text.lower()

    from backend.ingestion.hinglish import enrich_with_hinglish_context
    hinglish_info = enrich_with_hinglish_context(raw_text)

    # Dynamic Theme (2-3 words)
    if any(k in text_lower for k in ["cancel", "cancelled", "band"]) and any(k in text_lower for k in ["invested amount", "paisa kaise", "refund", "wapas", "nikale", "redeem", "milega", "kab milega", "get the"]):
        theme = "Redemption after cancellation"
    elif any(k in text_lower for k in ["do baar", "twice", "double", "duplicate", "two times"]) and any(k in text_lower for k in ["sip", "debit", "installment", "order"]):
        theme = "Duplicate SIP debit"
    elif any(k in text_lower for k in ["restart", "continue", "again", "phir se"]) and any(k in text_lower for k in ["cancel", "cancelled", "band"]):
        theme = "Restarting cancelled SIP"
    elif hinglish_info.get("detected"):
        theme = hinglish_info["theme"]
    elif any(k in text_lower for k in ["loss", "negative", "down", "red", "crash", "bear", "dip", "nuksan", "ghata"]):
        theme = "Market dip anxiety"
    elif any(k in text_lower for k in ["salary", "timing", "delayed", "month end"]):
        theme = "Salary date mismatch"
    elif any(k in text_lower for k in ["mandate", "autopay", "bounce", "penalty", "nach"]):
        theme = "Autopay bounce penalty"
    elif any(k in text_lower for k in ["deducted", "cut", "money debit", "not credited", "units not", "paisa"]):
        theme = "Units allocation delay"
    elif any(k in text_lower for k in ["pause", "no pause", "option to pause", "skip"]):
        theme = "Missing pause option"
    elif any(k in text_lower for k in ["switch", "transfer", "demat", "soa", "coin to", "groww to"]):
        theme = "SOA vs Demat switch"
    elif any(k in text_lower for k in ["kyc", "re-kyc", "lock", "blocked", "onboard"]):
        theme = "KYC verification friction"
    elif any(k in text_lower for k in ["charge", "tax", "gst", "hidden fee", "maintenance"]):
        theme = "Hidden platform charges"
    elif any(k in text_lower for k in ["glitch", "crash", "bug", "stuck", "error", "otp"]):
        theme = "App crash during order"
    else:
        # Dynamically extract 2 prominent nouns/verbs excluding stopwords
        stop_words = {
            "this", "that", "with", "have", "from", "they", "will", "been", "app", "fund", "money",
            "when", "what", "where", "which", "then", "them", "some", "more", "than", "just", "about",
            "kare", "kaise", "karna", "wala", "meri", "mera", "mere", "peise", "bohot", "hoga", "raha",
            "kiye", "kiya", "karo", "gaya", "aaya", "hota", "hoti", "isme", "usme", "bhai", "sirf"
        }
        words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', text_lower) if w not in stop_words]
        theme = f"{words[0].capitalize()} {words[1].capitalize()}" if len(words) >= 2 else "Retail investor friction"

    # Dynamic Journey Stage
    if any(k in text_lower for k in ["redeem", "withdrawal", "exit", "nikale", "refund", "invested amount"]):
        journey_stage = "Exit / Withdrawal"
    elif any(k in text_lower for k in ["kyc", "first time", "start investing", "account opening", "new to"]):
        journey_stage = "Onboarding / KYC"
    elif any(k in text_lower for k in ["first sip", "first installment", "1st month", "just started"]):
        journey_stage = "1st Month Beginner"
    elif any(k in text_lower for k in ["few months", "2 months", "3 months", "months", "started in"]):
        journey_stage = "Months 2-6 Market Dip"
    elif any(k in text_lower for k in ["years", "long term", "portfolio", "5 years", "3 years", "lakhs"]):
        journey_stage = "Year 2+ Experienced"
    elif any(k in text_lower for k in ["switch", "migrate", "transfer", "moving"]):
        journey_stage = "Platform Migration"
    else:
        journey_stage = "Active SIP Phase"

    # Dynamic Action Taken
    if hinglish_info.get("detected") and hinglish_info.get("action"):
        what_they_did = hinglish_info["action"]
    elif any(k in text_lower for k in ["stopped", "cancelled", "canceling", "cancel sip", "deleted app", "uninstalled", "band"]):
        what_they_did = "Cancelled SIP"
    elif any(k in text_lower for k in ["paused", "skip", "holding off"]):
        what_they_did = "Paused SIP"
    elif any(k in text_lower for k in ["reduced", "lowered"]):
        what_they_did = "Reduced SIP amount"
    elif any(k in text_lower for k in ["switched", "moved to", "migrated"]):
        what_they_did = "Switched Platform"
    elif any(k in text_lower for k in ["continuing", "holding", "invested", "buying"]):
        what_they_did = "Continued despite dip"
    else:
        what_they_did = "Seeking forum advice"

    # Who Can Fix It
    if any(k in theme.lower() for k in ["autopay", "bounce", "charge", "bank", "mandate"]):
        who_can_fix_it = "Bank or AMC"
    elif any(k in theme.lower() for k in ["salary", "anxiety", "panic"]):
        who_can_fix_it = "User life situation"
    else:
        who_can_fix_it = "Fintech Platform"

    who_they_are = "Salaried retail investor" if "salary" in text_lower else "Retail investor"

    # Extract best sentence as evidence quote
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', raw_text) if len(s.strip()) >= 15]
    best_sentence = ""
    for s in sentences:
        s_lower = s.lower()
        if any(k in s_lower for k in ["sip", "mandate", "autopay", "cancel", "fail", "deduct", "loss", "pause", "switch", "bank"]):
            best_sentence = s
            break
    if not best_sentence and sentences:
        best_sentence = sentences[0]
    if not best_sentence:
        best_sentence = raw_text[:80].strip()

    return {
        "theme": theme,
        "journey_stage": journey_stage,
        "what_they_did": what_they_did,
        "who_they_are": who_they_are,
        "who_can_fix_it": who_can_fix_it,
        "evidence_quote": best_sentence,
        "model_name": "dynamic-heuristic-engine"
    }

def validate_and_repair_quote(evidence_quote: str, raw_text: str) -> str:
    """Ensure evidence_quote is an exact verbatim substring of raw_text."""
    if evidence_quote and evidence_quote in raw_text:
        return evidence_quote

    # Try case-insensitive substring
    if evidence_quote:
        idx = raw_text.lower().find(evidence_quote.lower())
        if idx != -1:
            return raw_text[idx:idx + len(evidence_quote)]

    # Split raw text into sentences and pick best match
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', raw_text) if len(s.strip()) > 10]
    if sentences:
        if evidence_quote:
            eq_words = set(re.findall(r'\w+', evidence_quote.lower()))
            best_s = max(sentences, key=lambda s: len(eq_words.intersection(set(re.findall(r'\w+', s.lower())))))
            if best_s in raw_text:
                return best_s
        return sentences[0]

    return raw_text[:100]

def tag_post(raw_text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Tag an individual post using Gemini API with dynamic extraction, falling back to dynamic heuristic."""
    active_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not active_key:
        tag_data = dynamic_heuristic_tagger(raw_text)
        tag_data["evidence_quote"] = validate_and_repair_quote(tag_data["evidence_quote"], raw_text)
        return tag_data

    from backend.ingestion.hinglish import get_hinglish_context_hint

    # Use Gemini API via google-genai
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=active_key)
        hinglish_hint = get_hinglish_context_hint(raw_text)
        hint_str = f"\n\nContext Note: {hinglish_hint}" if hinglish_hint else ""
        prompt = f"{SYSTEM_PROMPT}\n\nRAW TEXT TO ANALYZE:\n\"\"\"\n{raw_text}\n\"\"\"{hint_str}"

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )

        content = response.text.strip()
        parsed = json.loads(content)

        theme = str(parsed.get("theme", "Retail investor friction")).strip()[:40]
        journey_stage = str(parsed.get("journey_stage", "Active SIP Phase")).strip()[:40]
        what_they_did = str(parsed.get("what_they_did", "Unsure")).strip()[:40]
        who_can_fix_it = str(parsed.get("who_can_fix_it", "Fintech Platform")).strip()[:40]
        who_they_are = str(parsed.get("who_they_are", "Retail investor")).strip()[:60]
        raw_evidence = str(parsed.get("evidence_quote", "")).strip()

        evidence_quote = validate_and_repair_quote(raw_evidence, raw_text)

        return {
            "theme": theme,
            "journey_stage": journey_stage,
            "what_they_did": what_they_did,
            "who_they_are": who_they_are,
            "who_can_fix_it": who_can_fix_it,
            "evidence_quote": evidence_quote,
            "model_name": "gemini-2.5-flash"
        }

    except Exception as e:
        print(f"Gemini API dynamic tagging error, falling back to dynamic heuristic: {e}")
        fallback = dynamic_heuristic_tagger(raw_text)
        fallback["evidence_quote"] = validate_and_repair_quote(fallback["evidence_quote"], raw_text)
        return fallback
