import re
import hashlib
from typing import Optional, Dict, Any

def clean_text(text: Any) -> str:
    """Strip extraneous whitespace, control characters, and clean up basic formatting."""
    if not text:
        return ""
    text_str = str(text)
    # Normalize multiple newlines/spaces
    text_str = re.sub(r'\r\n', '\n', text_str)
    text_str = re.sub(r'\n{3,}', '\n\n', text_str)
    text_str = re.sub(r'[ \t]{2,}', ' ', text_str)
    return text_str.strip()

def anonymize_text(text: Any) -> str:
    """Remove user handles, emails, and phone numbers for privacy."""
    if not text:
        return ""
    text_str = str(text)
    # Strip emails
    text_str = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED_EMAIL]', text_str)
    # Strip Indian mobile phone numbers (10 digits starting with 6-9, with optional +91 or 0)
    text_str = re.sub(r'(\+91[\-\s]?)?[6-9]\d{9}', '[REDACTED_PHONE]', text_str)
    # Strip social handles e.g. @username or u/username
    text_str = re.sub(r'(@[a-zA-Z0-9_]{3,20}|u/[a-zA-Z0-9_\-]{3,25})', '[REDACTED_USER]', text_str)
    return text_str

def compute_hash(text: Any) -> str:
    """Generate SHA-256 hash of normalized text for exact deduplication."""
    if not text:
        return hashlib.sha256(b"").hexdigest()
    norm = re.sub(r'\s+', ' ', str(text).lower()).strip()
    return hashlib.sha256(norm.encode('utf-8')).hexdigest()

def generate_post_id(platform: Any, source: Any, raw_text: Any) -> str:
    """Generate synthetic readable ID like POST_GROWW_A1B2C."""
    clean_platform = re.sub(r'[^A-Z0-9]', '', str(platform or "").upper())[:8] or "GEN"
    h = compute_hash(raw_text)[:6].upper() or "000000"
    return f"POST_{clean_platform}_{h}"
