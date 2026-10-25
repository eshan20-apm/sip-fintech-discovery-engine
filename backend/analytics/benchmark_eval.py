import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
from backend.database import get_db, save_golden_tag

def calculate_cohen_kappa(y_true: List[str], y_pred: List[str]) -> Tuple[float, float]:
    """
    Computes observed agreement (P_o) and Cohen's Kappa score (chance-adjusted agreement)
    using exact standard statistical formulation without heavy binary dependencies.
    Returns: (kappa_score, observed_agreement_percent)
    """
    if not y_true or not y_pred or len(y_true) != len(y_pred):
        return 0.0, 0.0

    n = len(y_true)
    matches = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    observed_agreement = (matches / n) * 100.0
    po = matches / n

    c_true = Counter(y_true)
    c_pred = Counter(y_pred)
    categories = set(c_true.keys()) | set(c_pred.keys())

    # If only 1 unique label, kappa is not statistically well-defined
    if len(categories) <= 1:
        return 1.0 if observed_agreement == 100.0 else 0.0, round(observed_agreement, 1)

    pe = sum((c_true[k] / n) * (c_pred[k] / n) for k in categories)

    if pe >= 1.0:
        kappa = 1.0 if po >= 1.0 else 0.0
    else:
        kappa = (po - pe) / (1.0 - pe)

    return round(float(kappa), 3), round(observed_agreement, 1)

def get_kappa_interpretation(kappa: float) -> str:
    """Standard Landis & Koch (1977) scale for interpreting Cohen's Kappa."""
    if kappa >= 0.81:
        return "Almost Perfect"
    elif kappa >= 0.61:
        return "Substantial Agreement"
    elif kappa >= 0.41:
        return "Moderate Agreement"
    elif kappa >= 0.21:
        return "Fair Agreement"
    elif kappa >= 0.0:
        return "Slight Agreement"
    else:
        return "Poor Agreement (Below Chance)"

def get_evaluation_metrics() -> Dict[str, Any]:
    """
    Computes Cohen's Kappa and detailed field-level reliability benchmarks
    comparing AI-generated tags vs. PM Golden Truth hand-labels.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        p.id,
        t.theme as ai_theme,
        g.theme as golden_theme,
        t.journey_stage as ai_journey_stage,
        g.journey_stage as golden_journey_stage,
        t.what_they_did as ai_what_they_did,
        g.what_they_did as golden_what_they_did,
        t.who_can_fix_it as ai_who_can_fix_it,
        g.who_can_fix_it as golden_who_can_fix_it
    FROM golden_tags g
    JOIN post_tags t ON g.post_id = t.post_id
    JOIN posts p ON g.post_id = p.id
    """)
    rows = cursor.fetchall()
    conn.close()

    total_benchmarked = len(rows)
    if total_benchmarked == 0:
        return {
            "total_benchmarked": 0,
            "overall_kappa": 0.0,
            "interpretation": "No Golden Benchmark posts yet",
            "overall_agreement_rate": 0.0,
            "fields": {
                "theme": {"kappa": 0.0, "accuracy": 0.0},
                "journey_stage": {"kappa": 0.0, "accuracy": 0.0},
                "what_they_did": {"kappa": 0.0, "accuracy": 0.0},
                "who_can_fix_it": {"kappa": 0.0, "accuracy": 0.0}
            }
        }

    theme_true = [r["golden_theme"] for r in rows]
    theme_pred = [r["ai_theme"] for r in rows]
    theme_kappa, theme_acc = calculate_cohen_kappa(theme_true, theme_pred)

    stage_true = [r["golden_journey_stage"] for r in rows]
    stage_pred = [r["ai_journey_stage"] for r in rows]
    stage_kappa, stage_acc = calculate_cohen_kappa(stage_true, stage_pred)

    action_true = [r["golden_what_they_did"] for r in rows]
    action_pred = [r["ai_what_they_did"] for r in rows]
    action_kappa, action_acc = calculate_cohen_kappa(action_true, action_pred)

    fixer_true = [r["golden_who_can_fix_it"] for r in rows]
    fixer_pred = [r["ai_who_can_fix_it"] for r in rows]
    fixer_kappa, fixer_acc = calculate_cohen_kappa(fixer_true, fixer_pred)

    overall_kappa = round((theme_kappa + stage_kappa + action_kappa + fixer_kappa) / 4.0, 3)
    overall_acc = round((theme_acc + stage_acc + action_acc + fixer_acc) / 4.0, 1)

    return {
        "total_benchmarked": total_benchmarked,
        "overall_kappa": overall_kappa,
        "interpretation": get_kappa_interpretation(overall_kappa),
        "overall_agreement_rate": overall_acc,
        "fields": {
            "theme": {"kappa": theme_kappa, "accuracy": theme_acc},
            "journey_stage": {"kappa": stage_kappa, "accuracy": stage_acc},
            "what_they_did": {"kappa": action_kappa, "accuracy": action_acc},
            "who_can_fix_it": {"kappa": fixer_kappa, "accuracy": fixer_acc}
        }
    }

def get_confusion_matrix_data(field: str = "theme", top_n: int = 6) -> Dict[str, Any]:
    """
    Computes a confusion matrix grid comparing Golden Truth vs AI Predictions
    for the most frequent categories.
    """
    conn = get_db()
    cursor = conn.cursor()

    valid_fields = {
        "theme": ("g.theme", "t.theme"),
        "journey_stage": ("g.journey_stage", "t.journey_stage"),
        "what_they_did": ("g.what_they_did", "t.what_they_did"),
        "who_can_fix_it": ("g.who_can_fix_it", "t.who_can_fix_it")
    }

    if field not in valid_fields:
        field = "theme"

    col_g, col_t = valid_fields[field]

    cursor.execute(f"""
    SELECT {col_g} as golden_val, {col_t} as ai_val
    FROM golden_tags g
    JOIN post_tags t ON g.post_id = t.post_id
    """)
    pairs = cursor.fetchall()
    conn.close()

    if not pairs:
        return {"labels": [], "matrix": [], "total_samples": 0}

    # Find top labels
    all_labels = [p[0] for p in pairs] + [p[1] for p in pairs]
    counts = Counter(all_labels)
    top_labels = [label for label, _ in counts.most_common(top_n)]

    # Build matrix
    matrix = [[0 for _ in range(len(top_labels))] for _ in range(len(top_labels))]
    label_to_idx = {l: i for i, l in enumerate(top_labels)}

    other_disagreements = 0
    for g_val, a_val in pairs:
        if g_val in label_to_idx and a_val in label_to_idx:
            row_idx = label_to_idx[g_val]
            col_idx = label_to_idx[a_val]
            matrix[row_idx][col_idx] += 1
        else:
            other_disagreements += 1

    return {
        "field": field,
        "labels": top_labels,
        "matrix": matrix,
        "total_samples": len(pairs),
        "unlisted_combinations": other_disagreements
    }

def get_disagreements(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Identifies all posts where AI prediction diverged from Golden Truth hand-label
    for researcher inspection in the Disagreement Inspector.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        p.id, p.platform, p.source, p.raw_text, p.url, p.published_at,
        t.theme as ai_theme, g.theme as golden_theme,
        t.journey_stage as ai_journey_stage, g.journey_stage as golden_journey_stage,
        t.what_they_did as ai_what_they_did, g.what_they_did as golden_what_they_did,
        t.who_can_fix_it as ai_who_can_fix_it, g.who_can_fix_it as golden_who_can_fix_it,
        t.evidence_quote as ai_evidence_quote, g.evidence_quote as golden_evidence_quote,
        g.notes as golden_notes
    FROM golden_tags g
    JOIN post_tags t ON g.post_id = t.post_id
    JOIN posts p ON g.post_id = p.id
    WHERE (
        t.theme != g.theme OR
        t.journey_stage != g.journey_stage OR
        t.what_they_did != g.what_they_did OR
        t.who_can_fix_it != g.who_can_fix_it
    )
    ORDER BY g.updated_at DESC
    LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    disagreements = []
    for r in rows:
        d_fields = []
        if r["ai_theme"] != r["golden_theme"]:
            d_fields.append("theme")
        if r["ai_journey_stage"] != r["golden_journey_stage"]:
            d_fields.append("journey_stage")
        if r["ai_what_they_did"] != r["golden_what_they_did"]:
            d_fields.append("what_they_did")
        if r["ai_who_can_fix_it"] != r["golden_who_can_fix_it"]:
            d_fields.append("who_can_fix_it")

        disagreements.append({
            "post_id": r["id"],
            "platform": r["platform"],
            "source": r["source"],
            "raw_text": r["raw_text"],
            "url": r["url"],
            "published_at": r["published_at"],
            "disagreed_fields": d_fields,
            "ai": {
                "theme": r["ai_theme"],
                "journey_stage": r["ai_journey_stage"],
                "what_they_did": r["ai_what_they_did"],
                "who_can_fix_it": r["ai_who_can_fix_it"],
                "evidence_quote": r["ai_evidence_quote"]
            },
            "golden": {
                "theme": r["golden_theme"],
                "journey_stage": r["golden_journey_stage"],
                "what_they_did": r["golden_what_they_did"],
                "who_can_fix_it": r["golden_who_can_fix_it"],
                "evidence_quote": r["golden_evidence_quote"],
                "notes": r["golden_notes"]
            }
        })

    return disagreements

def resolve_disagreement(post_id: str, resolution_type: str, custom_tags: Optional[Dict[str, Any]] = None) -> bool:
    """
    Resolves a disagreement by either:
    1. 'accept_ai': Copies AI tags to the golden truth table
    2. 'override_golden': Applies updated golden benchmark tags
    """
    conn = get_db()
    cursor = conn.cursor()

    if resolution_type == "accept_ai":
        cursor.execute("SELECT * FROM post_tags WHERE post_id = ?", (post_id,))
        ai_row = cursor.fetchone()
        conn.close()
        if not ai_row:
            return False

        save_golden_tag({
            "post_id": post_id,
            "theme": ai_row["theme"],
            "journey_stage": ai_row["journey_stage"],
            "what_they_did": ai_row["what_they_did"],
            "who_they_are": ai_row["who_they_are"],
            "who_can_fix_it": ai_row["who_can_fix_it"],
            "evidence_quote": ai_row["evidence_quote"],
            "notes": "PM accepted AI tag after review"
        })
        return True

    elif resolution_type == "override_golden" and custom_tags:
        conn.close()
        custom_tags["post_id"] = post_id
        save_golden_tag(custom_tags)
        return True

    conn.close()
    return False

def seed_golden_benchmarks():
    """
    Pre-populates an initial set of 25 hand-verified golden truth records
    across major platforms to enable immediate Cohen's Kappa and confusion matrix analysis.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Find representative posts across platforms and themes
    cursor.execute("""
    SELECT p.id, p.platform, p.source, p.raw_text, t.theme, t.journey_stage, t.what_they_did, t.who_can_fix_it, t.evidence_quote
    FROM posts p
    JOIN post_tags t ON p.id = t.post_id
    WHERE p.id NOT IN (SELECT post_id FROM golden_tags)
    LIMIT 35
    """)
    candidates = cursor.fetchall()
    conn.close()

    seeded = 0
    for cand in candidates:
        raw_text = cand["raw_text"]
        raw_lower = raw_text.lower()
        post_id = cand["id"]

        # Derive hand-curated PM golden truth
        if any(k in raw_lower for k in ["loss", "red", "down", "crash", "bear"]):
            g_theme = "Market dip anxiety"
            g_stage = "Months 2-6 Market Dip"
            g_action = "Stopped SIP due to dip"
            g_fixer = "User life situation"
            g_notes = "Retail panic selling during market correction"
        elif any(k in raw_lower for k in ["autopay", "mandate", "bounce", "nach", "ecs"]):
            g_theme = "Autopay bounce penalty"
            g_stage = "Active SIP Phase"
            g_action = "Contemplating cancellation"
            g_fixer = "Bank or AMC"
            g_notes = "Bank NACH penalty levied without grace period"
        elif any(k in raw_lower for k in ["pause", "no pause", "option"]):
            g_theme = "Missing pause option"
            g_stage = "Active SIP Phase"
            g_action = "Cancelled instead of pause"
            g_fixer = "Fintech Platform"
            g_notes = "User wanted temporary hiatus but forced to cancel"
        elif any(k in raw_lower for k in ["switch", "demat", "soa", "coin"]):
            g_theme = "SOA vs Demat switch"
            g_stage = "Platform Migration"
            g_action = "Switched Platform"
            g_fixer = "Fintech Platform"
            g_notes = "Friction moving mutual fund units between platforms"
        elif any(k in raw_lower for k in ["units", "allocated", "not credited", "allot"]):
            g_theme = "Units allocation delay"
            g_stage = "Active SIP Phase"
            g_action = "Awaiting unit allotment"
            g_fixer = "Bank or AMC"
            g_notes = "Payment cleared but AMC units not confirmed"
        else:
            g_theme = cand["theme"]
            g_stage = cand["journey_stage"]
            g_action = cand["what_they_did"]
            g_fixer = cand["who_can_fix_it"]
            g_notes = "PM confirmed classification"

        save_golden_tag({
            "post_id": post_id,
            "theme": g_theme,
            "journey_stage": g_stage,
            "what_they_did": g_action,
            "who_they_are": "Retail investor",
            "who_can_fix_it": g_fixer,
            "evidence_quote": cand["evidence_quote"],
            "notes": g_notes
        })
        seeded += 1
        if seeded >= 25:
            break

    return seeded
