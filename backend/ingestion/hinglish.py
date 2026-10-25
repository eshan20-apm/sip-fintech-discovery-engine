import re
from typing import Dict, List, Any, Optional

# Comprehensive Indian Fintech & Mutual Fund Hinglish Glossary
HINGLISH_FINTECH_GLOSSARY = {
    r'\b(?:paisa|rupaye|paise|balance)\s*(?:cut|kat|kata|debit|kat gaya|cut gaya|chala gaya|nikal gaya)\b': {
        'explanation': 'money debited from bank account',
        'theme': 'Units allocation delay',
        'action': 'Seeking support resolution'
    },
    r'\bunits?\s*(?:nahi\s*mile?|allocate\s*nahi|show\s*nahi\s*ho\s*rahe?|allot\s*nahi|dikh\s*nahi\s*raha)\b': {
        'explanation': 'mutual fund units not allocated after payment',
        'theme': 'Units allocation delay',
        'action': 'Awaiting unit allotment'
    },
    r'\b(?:mandate|autopay|nach|ecs)\s*(?:fail|reject|approve\s*nahi|bounc\w*|kat\s*gaya|charge)\b': {
        'explanation': 'bank autopay e-mandate rejection or bounce',
        'theme': 'Autopay bounce penalty',
        'action': 'Contemplating cancellation'
    },
    r'\bsip\s*(?:band|cancel|rok|roka|band\s*kaise\s*kar\w*|rokna\s*hai|hatao)\b': {
        'explanation': 'cancelling or stopping systematic investment plan',
        'theme': 'SIP cancellation friction',
        'action': 'Cancelled SIP'
    },
    r'\bpause\s*(?:ka\s*option\s*nahi|kaise\s*kare|option\s*kyu\s*nahi|nahi\s*mil\s*raha)\b': {
        'explanation': 'missing pause SIP feature in app',
        'theme': 'Missing pause option',
        'action': 'Cancelled instead of pause'
    },
    r'\bsalary\s*(?:late|aayi\s*nahi|date\s*match\s*nahi|aane\s*se\s*pehle|month\s*end)\b': {
        'explanation': 'salary credit delay causing SIP auto-debit failure',
        'theme': 'Salary date mismatch',
        'action': 'Missed SIP installment'
    },
    r'\b(?:loss|nuksan|ghata)\s*(?:ho\s*gaya|mein\s*hai|chal\s*raha|red\s*hai|gir\s*gaya)\b': {
        'explanation': 'negative portfolio returns causing drawdown anxiety',
        'theme': 'Market dip anxiety',
        'action': 'Stopped SIP due to dip'
    },
    r'\bcharges?\s*(?:kat\s*liye|extra\s*kat|hidden|penalt\w*|katte\s*hai)\b': {
        'explanation': 'unexpected bank bounce penalty or platform maintenance charge',
        'theme': 'Hidden platform charges',
        'action': 'Complained about charges'
    },
    r'\b(?:switch|transfer|demat|soa)\s*(?:kaise\s*kare|karna\s*hai|badalna|shift)\b': {
        'explanation': 'switching mutual funds or migrating from Groww to Zerodha Coin',
        'theme': 'SOA vs Demat switch',
        'action': 'Switched Platform'
    },
    r'\bkyc\s*(?:reject|pending|atki\s*hui|lock|band\s*ho\s*gaya)\b': {
        'explanation': 'KYC verification delayed or account locked',
        'theme': 'KYC verification friction',
        'action': 'Onboarding blocked'
    }
}

def detect_hinglish(text: str) -> bool:
    """Detect if the comment contains Indian colloquial Hinglish terms."""
    hinglish_markers = [
        "kare", "karna", "nahi", "paisa", "kat", "gaya", "aaya", "kya", "hai", "bhi",
        "kaise", "band", "rok", "wala", "mein", "mera", "meri", "karo", "raha", "rahi",
        "nuksan", "ghata", "rupaye", "rupay", "dikh", "iska", "uske", "kuch", "hoti"
    ]
    words = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
    matches = words.intersection(hinglish_markers)
    return len(matches) >= 2

def get_hinglish_context_hint(text: str) -> str:
    """Generate an analytical English explanation of Hinglish friction expressions in the comment."""
    hints = []
    text_lower = text.lower()
    for pattern, data in HINGLISH_FINTECH_GLOSSARY.items():
        if re.search(pattern, text_lower):
            hints.append(data['explanation'])

    if hints:
        return "Fintech Context: " + "; ".join(hints)
    return ""

def enrich_with_hinglish_context(text: str) -> Dict[str, Any]:
    """Extract structured intent and suggested theme from Hinglish comments."""
    text_lower = text.lower()
    for pattern, data in HINGLISH_FINTECH_GLOSSARY.items():
        if re.search(pattern, text_lower):
            return {
                'detected': True,
                'explanation': data['explanation'],
                'theme': data['theme'],
                'action': data['action']
            }
    return {'detected': False, 'explanation': '', 'theme': '', 'action': ''}
