import sqlite3
import os
import re
import math
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from backend.database import get_db

ENGLISH_STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", 
    "by", "can", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", 
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", 
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", 
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", 
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same", "she", 
    "should", "so", "some", "such", "t", "than", "that", "the", "their", "theirs", "them", 
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too", 
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", 
    "while", "who", "whom", "why", "will", "with", "you", "your", "yours", "yourself", "yourselves"
}

def extract_features(text: str) -> List[str]:
    words = [w for w in re.findall(r'\b[a-zA-Z0-9]{2,}\b', text.lower()) if w not in ENGLISH_STOP_WORDS]
    bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)]
    return words + bigrams

class PureDenseTfidfIndex:
    """Lightweight, pure-Python sublinear TF-IDF semantic vector index."""
    def __init__(self):
        self.doc_ids: List[str] = []
        self.doc_vectors: List[Dict[str, float]] = []
        self.idf: Dict[str, float] = {}

    def fit_transform(self, doc_ids: List[str], docs: List[str]):
        self.doc_ids = doc_ids
        n_docs = len(docs)
        if n_docs == 0:
            self.doc_vectors = []
            self.idf = {}
            return

        doc_tokens = [extract_features(d) for d in docs]
        df = Counter()
        for tokens in doc_tokens:
            for term in set(tokens):
                df[term] += 1

        self.idf = {term: math.log((1.0 + n_docs) / (1.0 + freq)) + 1.0 for term, freq in df.items()}

        self.doc_vectors = []
        for tokens in doc_tokens:
            counts = Counter(tokens)
            vec = {}
            for term, count in counts.items():
                if term in self.idf:
                    tf = 1.0 + math.log(count)
                    vec[term] = tf * self.idf[term]
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            self.doc_vectors.append({t: v / norm for t, v in vec.items()})

    def query(self, query_text: str, top_k: int = 100, min_score: float = 0.02) -> List[Tuple[str, float]]:
        q_tokens = extract_features(query_text)
        if not q_tokens:
            return []
        q_counts = Counter(q_tokens)
        q_vec = {}
        for term, count in q_counts.items():
            if term in self.idf:
                tf = 1.0 + math.log(count)
                q_vec[term] = tf * self.idf[term]
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
        q_unit = {t: v / q_norm for t, v in q_vec.items()}

        results = []
        for doc_id, doc_vec in zip(self.doc_ids, self.doc_vectors):
            dot = sum(q_unit[t] * doc_vec[t] for t in q_unit if t in doc_vec)
            if dot >= min_score:
                results.append((doc_id, dot))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

class HybridSearchEngine:
    def __init__(self):
        self._dense_index = PureDenseTfidfIndex()
        self._cached_post_count = 0

    def _sync_dense_index(self):
        """Fit or refresh the local dense TF-IDF index across all active posts."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, raw_text FROM posts")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            self._dense_index = PureDenseTfidfIndex()
            self._cached_post_count = 0
            return

        if len(rows) == self._cached_post_count and self._dense_index.doc_ids:
            return

        post_ids = [r[0] for r in rows]
        corpus_texts = [r[1] for r in rows]
        self._dense_index.fit_transform(post_ids, corpus_texts)
        self._cached_post_count = len(rows)

    def search(
        self,
        query: str,
        platform: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        rrf_k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Executes Hybrid RAG retrieval combining:
        1. Sparse lexical search using SQLite FTS5 BM25
        2. Dense semantic vector similarity using TF-IDF sublinear embeddings
        3. Reciprocal Rank Fusion (RRF) for robust joint ranking
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        conn = get_db()
        cursor = conn.cursor()

        # 1. Sparse FTS5 BM25 Search
        sparse_ranks: Dict[str, int] = {}
        tokens = [w for w in re.findall(r'\b[a-zA-Z0-9]{3,}\b', clean_query.lower()) if w not in {"why", "what", "how", "the", "and", "for", "with"}]
        if tokens:
            fts_match_expr = " OR ".join([f'"{t}"*' for t in tokens[:6]])
            try:
                cursor.execute("""
                SELECT post_id, rank 
                FROM posts_fts 
                WHERE posts_fts MATCH ? 
                ORDER BY rank ASC 
                LIMIT 100
                """, (fts_match_expr,))
                sparse_rows = cursor.fetchall()
                for rank_idx, r in enumerate(sparse_rows):
                    sparse_ranks[r[0]] = rank_idx + 1
            except Exception as e:
                print(f"Notice: FTS5 query fallback: {e}")

        # 2. Dense Semantic Vector Search
        self._sync_dense_index()
        dense_ranks: Dict[str, int] = {}
        dense_matches = self._dense_index.query(clean_query, top_k=100, min_score=0.02)
        for rank_idx, (p_id, _) in enumerate(dense_matches):
            dense_ranks[p_id] = rank_idx + 1

        # 3. Reciprocal Rank Fusion (RRF)
        candidate_ids = set(sparse_ranks.keys()).union(set(dense_ranks.keys()))
        rrf_scores: Dict[str, float] = {}

        for p_id in candidate_ids:
            score = 0.0
            if p_id in sparse_ranks:
                score += 1.0 / (rrf_k + sparse_ranks[p_id])
            if p_id in dense_ranks:
                score += 1.0 / (rrf_k + dense_ranks[p_id])
            rrf_scores[p_id] = score

        # Sort candidate IDs by fused RRF score
        ranked_post_ids = sorted(rrf_scores.keys(), key=lambda pid: rrf_scores[pid], reverse=True)

        if not ranked_post_ids:
            # Fallback: substring like search
            cursor.execute("SELECT id FROM posts WHERE raw_text LIKE ? LIMIT ?", (f"%{clean_query[:20]}%", limit))
            ranked_post_ids = [r[0] for r in cursor.fetchall()]

        if not ranked_post_ids:
            conn.close()
            return []

        # 4. Fetch full post details in ranked order with platform/source filters
        placeholders = ",".join(["?"] * len(ranked_post_ids))
        fetch_sql = f"""
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
        WHERE p.id IN ({placeholders})
        """
        filter_params = list(ranked_post_ids)

        if platform and platform != "all":
            fetch_sql += " AND p.platform = ?"
            filter_params.append(platform)

        if source and source != "all":
            fetch_sql += " AND p.source = ?"
            filter_params.append(source)

        if status == "hand_labelled":
            fetch_sql += " AND g.id IS NOT NULL"
        elif status == "ai_tagged":
            fetch_sql += " AND g.id IS NULL"

        cursor.execute(fetch_sql, filter_params)
        fetched_rows = {r["id"]: dict(r) for r in cursor.fetchall()}
        conn.close()

        # Re-order according to RRF ranking
        results = []
        for pid in ranked_post_ids:
            if pid in fetched_rows:
                post = fetched_rows[pid]
                post["rrf_score"] = round(rrf_scores.get(pid, 0.0), 4)
                results.append(post)
                if len(results) >= limit:
                    break

        return results

# Singleton instance for backend reuse
hybrid_searcher = HybridSearchEngine()
