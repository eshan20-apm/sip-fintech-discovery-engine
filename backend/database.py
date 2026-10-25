import sqlite3
import os
import shutil
from typing import List, Dict, Any, Optional

ORIGINAL_DB_PATH = os.path.join(os.path.dirname(__file__), "sip_discovery.db")

# In Vercel serverless environment, filesystem is read-only except /tmp
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/sip_discovery.db"
    if not os.path.exists(DB_PATH) and os.path.exists(ORIGINAL_DB_PATH):
        try:
            shutil.copyfile(ORIGINAL_DB_PATH, DB_PATH)
        except Exception as e:
            print(f"Notice: unable to copy DB to /tmp: {e}")
            DB_PATH = ORIGINAL_DB_PATH
else:
    DB_PATH = ORIGINAL_DB_PATH

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Core posts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        platform TEXT NOT NULL,
        source TEXT NOT NULL,
        source_id TEXT NOT NULL,
        raw_text TEXT NOT NULL,
        url TEXT NOT NULL,
        published_at TEXT,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # AI-generated tags table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS post_tags (
        post_id TEXT PRIMARY KEY REFERENCES posts(id) ON DELETE CASCADE,
        theme TEXT NOT NULL,
        journey_stage TEXT NOT NULL,
        what_they_did TEXT NOT NULL,
        who_they_are TEXT NOT NULL,
        who_can_fix_it TEXT NOT NULL,
        evidence_quote TEXT NOT NULL,
        model_name TEXT NOT NULL,
        tagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Golden truth tags table (PM overrides)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS golden_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id TEXT UNIQUE REFERENCES posts(id) ON DELETE CASCADE,
        theme TEXT NOT NULL,
        journey_stage TEXT NOT NULL,
        what_they_did TEXT NOT NULL,
        who_they_are TEXT NOT NULL,
        who_can_fix_it TEXT NOT NULL,
        evidence_quote TEXT,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Full-Text Search virtual table
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
        post_id UNINDEXED,
        platform,
        raw_text
    );
    """)

    conn.commit()
    conn.close()

def save_post_with_tag(post: Dict[str, Any], tag: Dict[str, Any]) -> bool:
    """Save post and its AI tag in a single transaction, syncing FTS5."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO posts (id, platform, source, source_id, raw_text, url, published_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            post["id"],
            post["platform"],
            post["source"],
            post["source_id"],
            post["raw_text"],
            post["url"],
            post.get("published_at")
        ))

        # If it was inserted, update FTS
        if cursor.rowcount > 0:
            cursor.execute("""
            INSERT INTO posts_fts (post_id, platform, raw_text)
            VALUES (?, ?, ?)
            """, (post["id"], post["platform"], post["raw_text"]))

        # Insert or replace AI tag
        cursor.execute("""
        INSERT OR REPLACE INTO post_tags (
            post_id, theme, journey_stage, what_they_did, who_they_are,
            who_can_fix_it, evidence_quote, model_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tag["post_id"],
            tag["theme"],
            tag["journey_stage"],
            tag["what_they_did"],
            tag["who_they_are"],
            tag["who_can_fix_it"],
            tag["evidence_quote"],
            tag.get("model_name", "gemini-2.5-flash")
        ))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving post {post.get('id')}: {e}")
        return False
    finally:
        conn.close()

def save_golden_tag(tag: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a golden tag override for a post."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO golden_tags (
            post_id, theme, journey_stage, what_they_did,
            who_they_are, who_can_fix_it, evidence_quote, notes, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(post_id) DO UPDATE SET
            theme = excluded.theme,
            journey_stage = excluded.journey_stage,
            what_they_did = excluded.what_they_did,
            who_they_are = excluded.who_they_are,
            who_can_fix_it = excluded.who_can_fix_it,
            evidence_quote = excluded.evidence_quote,
            notes = excluded.notes,
            updated_at = CURRENT_TIMESTAMP
        """, (
            tag["post_id"],
            tag["theme"],
            tag["journey_stage"],
            tag["what_they_did"],
            tag["who_they_are"],
            tag["who_can_fix_it"],
            tag.get("evidence_quote"),
            tag.get("notes")
        ))
        conn.commit()

        cursor.execute("SELECT * FROM golden_tags WHERE post_id = ?", (tag["post_id"],))
        row = cursor.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()

def fetch_posts(
    search_query: Optional[str] = None,
    platform: Optional[str] = None,
    theme: Optional[str] = None,
    journey_stage: Optional[str] = None,
    what_they_did: Optional[str] = None,
    who_can_fix_it: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None, # 'all', 'hand_labelled', 'ai_tagged'
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        p.id, p.platform, p.source, p.source_id, p.raw_text, p.url, p.published_at, p.fetched_at,
        t.theme as ai_theme, t.journey_stage as ai_journey_stage, t.what_they_did as ai_what_they_did,
        t.who_they_are as ai_who_they_are, t.who_can_fix_it as ai_who_can_fix_it,
        t.evidence_quote as ai_evidence_quote, t.model_name, t.tagged_at,
        g.id as golden_id, g.theme as golden_theme, g.journey_stage as golden_journey_stage,
        g.what_they_did as golden_what_they_did, g.who_they_are as golden_who_they_are,
        g.who_can_fix_it as golden_who_can_fix_it, g.evidence_quote as golden_evidence_quote,
        g.notes as golden_notes, g.updated_at as golden_updated_at,
        CASE WHEN g.id IS NOT NULL THEN 1 ELSE 0 END as is_hand_labelled
    FROM posts p
    LEFT JOIN post_tags t ON p.id = t.post_id
    LEFT JOIN golden_tags g ON p.id = g.post_id
    """
    
    where_clauses = []
    params = []

    if search_query and search_query.strip():
        # Clean search query for FTS5
        clean_search = "".join(c for c in search_query if c.isalnum() or c.isspace()).strip()
        if clean_search:
            fts_tokens = [f'"{token}"*' for token in clean_search.split()]
            fts_expr = " AND ".join(fts_tokens)
            where_clauses.append("p.id IN (SELECT post_id FROM posts_fts WHERE posts_fts MATCH ?)")
            params.append(fts_expr)
        else:
            where_clauses.append("p.raw_text LIKE ?")
            params.append(f"%{search_query.strip()}%")

    if platform and platform != "all":
        where_clauses.append("p.platform = ?")
        params.append(platform)

    if source and source != "all":
        where_clauses.append("p.source = ?")
        params.append(source)

    if theme and theme != "all":
        where_clauses.append("(COALESCE(g.theme, t.theme) = ?)")
        params.append(theme)

    if journey_stage and journey_stage != "all":
        where_clauses.append("(COALESCE(g.journey_stage, t.journey_stage) = ?)")
        params.append(journey_stage)

    if what_they_did and what_they_did != "all":
        where_clauses.append("(COALESCE(g.what_they_did, t.what_they_did) = ?)")
        params.append(what_they_did)

    if who_can_fix_it and who_can_fix_it != "all":
        where_clauses.append("(COALESCE(g.who_can_fix_it, t.who_can_fix_it) = ?)")
        params.append(who_can_fix_it)

    if status == "hand_labelled":
        where_clauses.append("g.id IS NOT NULL")
    elif status == "ai_tagged":
        where_clauses.append("g.id IS NULL")

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY p.fetched_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results

def get_stats() -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM posts")
    total_posts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM golden_tags")
    golden_count = cursor.fetchone()[0]

    cursor.execute("SELECT platform, COUNT(*) FROM posts GROUP BY platform")
    platform_counts = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("""
    SELECT COALESCE(g.theme, t.theme) as active_theme, COUNT(*) 
    FROM posts p
    LEFT JOIN post_tags t ON p.id = t.post_id
    LEFT JOIN golden_tags g ON p.id = g.post_id
    GROUP BY active_theme
    """)
    theme_counts = {row[0] or "Unclear": row[1] for row in cursor.fetchall()}

    # Calculate agreement between AI and Golden tags if there are golden records
    agreement_rate = 0.0
    field_accuracies = {}
    if golden_count > 0:
        cursor.execute("""
        SELECT 
            SUM(CASE WHEN t.theme = g.theme THEN 1 ELSE 0 END) as theme_match,
            SUM(CASE WHEN t.journey_stage = g.journey_stage THEN 1 ELSE 0 END) as journey_match,
            SUM(CASE WHEN t.what_they_did = g.what_they_did THEN 1 ELSE 0 END) as action_match,
            SUM(CASE WHEN t.who_can_fix_it = g.who_can_fix_it THEN 1 ELSE 0 END) as fixer_match,
            COUNT(*) as total
        FROM post_tags t
        JOIN golden_tags g ON t.post_id = g.post_id
        """)
        row = cursor.fetchone()
        if row and row[4] > 0:
            total = row[4]
            field_accuracies = {
                "theme": round((row[0] / total) * 100, 1),
                "journey_stage": round((row[1] / total) * 100, 1),
                "what_they_did": round((row[2] / total) * 100, 1),
                "who_can_fix_it": round((row[3] / total) * 100, 1)
            }
            avg_acc = (row[0] + row[1] + row[2] + row[3]) / (total * 4)
            agreement_rate = round(avg_acc * 100, 1)

    conn.close()
    return {
        "total_posts": total_posts,
        "golden_count": golden_count,
        "agreement_rate": agreement_rate,
        "field_accuracies": field_accuracies,
        "platform_counts": platform_counts,
        "theme_counts": theme_counts
    }
