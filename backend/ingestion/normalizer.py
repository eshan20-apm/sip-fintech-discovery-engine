import re
import hashlib
from typing import Optional, Dict, Any

def clean_text(text: str) -> str:
    """Strip extraneous whitespace, control characters, and clean up basic formatting."""
    if not text:
        return ""
    # Normalize multiple newlines/spaces
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()

def anonymize_text(text: str) -> str:
    """Remove user handles, emails, and phone numbers for privacy."""
    # Strip emails
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED_EMAIL]', text)
    # Strip Indian mobile phone numbers (10 digits starting with 6-9, with optional +91 or 0)
    text = re.sub(r'(\+91[\-\s]?)?[6-9]\d{9}', '[REDACTED_PHONE]', text)
    # Strip social handles e.g. @username or u/username
    text = re.sub(r'(@[a-zA-Z0-9_]{3,20}|u/[a-zA-Z0-9_\-]{3,25})', '[REDACTED_USER]', text)
    return text

def compute_hash(text: str) -> str:
    """Generate SHA-256 hash of normalized text for exact deduplication."""
    norm = re.sub(r'\s+', ' ', text.lower()).strip()
    return hashlib.sha256(norm.encode('utf-8')).hexdigest()

def generate_post_id(platform: str, source: str, raw_text: str) -> str:
    """Generate synthetic readable ID like POST_GROWW_A1B2C."""
    clean_platform = re.sub(r'[^A-Z0-9]', '', platform.upper())[:8] or "GEN"
    h = compute_hash(raw_text)[:6].upper()
    return f"POST_{clean_platform}_{h}"
