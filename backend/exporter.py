import io
import pandas as pd
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from backend.database import get_db
from backend.analytics.benchmark_eval import get_evaluation_metrics

def format_worksheet(worksheet, header_color="1E293B", accent_color="38BDF8"):
    """Applies professional formatting, column auto-width, freeze panes, and clean headers."""
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color=header_color, end_color=header_color, fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=False)
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # Style header row
    for col_idx in range(1, worksheet.max_column + 1):
        cell = worksheet.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    # Freeze header
    worksheet.freeze_panes = "A2"

    # Style data rows and auto-fit widths
    for col in worksheet.columns:
        col_letter = col[0].column_letter
        max_len = 0
        for cell in col:
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
            if cell.row > 1:
                cell.font = Font(name="Calibri", size=10)
                # Align text columns vs IDs/dates
                if col_letter in ['A', 'B', 'C', 'D', 'K']:
                    cell.alignment = center_align
                else:
                    cell.alignment = left_align

        worksheet.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 55)

def export_posts_to_excel(posts: List[Dict[str, Any]]) -> bytes:
    """
    Generates a 3-tab executive research workbook:
    1. 'Active Research Feed': Filtered comments matching the prompt/platform view
    2. 'Golden Benchmark Set': Hand-verified truth set with PM rationales
    3. 'Reliability & Kappa Metrics': Statistical evaluation (Cohen's Kappa κ, accuracy rates)
    """
    # ---------------- TAB 1: ACTIVE RESEARCH FEED ----------------
    rows_active = []
    for p in posts:
        is_golden = p.get("is_hand_labelled") == 1
        theme = p.get("golden_theme") if is_golden else p.get("ai_theme")
        journey_stage = p.get("golden_journey_stage") if is_golden else p.get("ai_journey_stage")
        what_they_did = p.get("golden_what_they_did") if is_golden else p.get("ai_what_they_did")
        who_they_are = p.get("golden_who_they_are") if is_golden else p.get("ai_who_they_are")
        who_can_fix_it = p.get("golden_who_can_fix_it") if is_golden else p.get("ai_who_can_fix_it")
        evidence_quote = p.get("golden_evidence_quote") if (is_golden and p.get("golden_evidence_quote")) else p.get("ai_evidence_quote")

        rows_active.append({
            "Post ID": p.get("id"),
            "Platform": p.get("platform"),
            "Source": p.get("source"),
            "Published Date": p.get("published_at", "")[:10] if p.get("published_at") else "Live",
            "Dynamic Theme (2-3 Words)": theme or "Unclear",
            "Journey Stage": journey_stage or "Active SIP Phase",
            "Action Taken": what_they_did or "Unsure",
            "Investor Persona": who_they_are or "Retail investor",
            "Responsible Entity": who_can_fix_it or "Fintech Platform",
            "Verbatim Evidence Quote": evidence_quote or "",
            "Status": "Golden Benchmark" if is_golden else "AI Tagged",
            "RRF Relevance Score": p.get("rrf_score", "N/A"),
            "PM Notes": p.get("golden_notes", ""),
            "Raw Feedback": p.get("raw_text", ""),
            "Original Source URL": p.get("url", "")
        })

    df_active = pd.DataFrame(rows_active)

    # ---------------- TAB 2: GOLDEN BENCHMARK SET ----------------
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        p.id, p.platform, p.source, p.published_at, p.raw_text, p.url,
        g.theme, g.journey_stage, g.what_they_did, g.who_they_are, g.who_can_fix_it,
        g.evidence_quote, g.notes, g.updated_at
    FROM golden_tags g
    JOIN posts p ON g.post_id = p.id
    ORDER BY g.updated_at DESC
    """)
    rows_golden = [dict(r) for r in cursor.fetchall()]
    conn.close()

    golden_data = []
    for g in rows_golden:
        golden_data.append({
            "Post ID": g.get("id"),
            "Platform": g.get("platform"),
            "Source": g.get("source"),
            "Date": g.get("published_at", "")[:10] if g.get("published_at") else "",
            "Verified Theme": g.get("theme"),
            "Verified Journey Stage": g.get("journey_stage"),
            "Verified Action Taken": g.get("what_they_did"),
            "Investor Persona": g.get("who_they_are"),
            "Responsible Entity": g.get("who_can_fix_it"),
            "Verbatim Evidence Quote": g.get("evidence_quote") or "",
            "PM Benchmark Rationale / Notes": g.get("notes") or "",
            "Raw Comment Text": g.get("raw_text"),
            "Source Link": g.get("url")
        })

    df_golden = pd.DataFrame(golden_data)

    # ---------------- TAB 3: RELIABILITY & KAPPA METRICS ----------------
    eval_metrics = get_evaluation_metrics()
    metrics_summary = [
        {"Metric": "Overall Cohen's Kappa (κ)", "Value": eval_metrics.get("overall_kappa"), "Unit / Scale": "-1.0 to +1.0 (Chance-Adjusted)"},
        {"Metric": "Reliability Interpretation", "Value": eval_metrics.get("interpretation"), "Unit / Scale": "Landis & Koch (1977) Standard"},
        {"Metric": "Overall Observed Raw Agreement (Pₒ)", "Value": f"{eval_metrics.get('overall_agreement_rate')}%", "Unit / Scale": "Exact label match %"},
        {"Metric": "Total Golden Benchmark Posts", "Value": eval_metrics.get("total_benchmarked"), "Unit / Scale": "Hand-verified records"},
        {"Metric": "Theme Classification Kappa", "Value": eval_metrics.get("fields", {}).get("theme", {}).get("kappa"), "Unit / Scale": "Field Reliability"},
        {"Metric": "Theme Raw Accuracy", "Value": f"{eval_metrics.get('fields', {}).get('theme', {}).get('accuracy')}%", "Unit / Scale": "Exact match %"},
        {"Metric": "Journey Stage Kappa", "Value": eval_metrics.get("fields", {}).get("journey_stage", {}).get("kappa"), "Unit / Scale": "Field Reliability"},
        {"Metric": "Journey Stage Raw Accuracy", "Value": f"{eval_metrics.get('fields', {}).get('journey_stage', {}).get('accuracy')}%", "Unit / Scale": "Exact match %"},
        {"Metric": "Action Taken Kappa", "Value": eval_metrics.get("fields", {}).get("what_they_did", {}).get("kappa"), "Unit / Scale": "Field Reliability"},
        {"Metric": "Action Taken Raw Accuracy", "Value": f"{eval_metrics.get('fields', {}).get('what_they_did', {}).get('accuracy')}%", "Unit / Scale": "Exact match %"},
        {"Metric": "Who Can Fix It Kappa", "Value": eval_metrics.get("fields", {}).get("who_can_fix_it", {}).get("kappa"), "Unit / Scale": "Field Reliability"},
        {"Metric": "Who Can Fix It Raw Accuracy", "Value": f"{eval_metrics.get('fields', {}).get('who_can_fix_it', {}).get('accuracy')}%", "Unit / Scale": "Exact match %"}
    ]
    df_metrics = pd.DataFrame(metrics_summary)

    # Build multi-tab Excel workbook
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_active.to_excel(writer, index=False, sheet_name='Active Research Feed')
        df_golden.to_excel(writer, index=False, sheet_name='Golden Benchmark Set')
        df_metrics.to_excel(writer, index=False, sheet_name='Reliability & Kappa Metrics')

        format_worksheet(writer.sheets['Active Research Feed'], header_color="1E293B")
        format_worksheet(writer.sheets['Golden Benchmark Set'], header_color="065F46")
        format_worksheet(writer.sheets['Reliability & Kappa Metrics'], header_color="312E81")

    output.seek(0)
    return output.getvalue()
