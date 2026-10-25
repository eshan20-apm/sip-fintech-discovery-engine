import sqlite3
import os
import re
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.database import get_db

class HybridSearchEngine:
    def __init__(self):
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._corpus_matrix = None
        self._corpus_post_ids: List[str] = []
        self._cached_post_count = 0

    def _sync_dense_index(self):
        """Fit or refresh the local dense TF-IDF index across all active posts."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, raw_text FROM posts")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            self._vectorizer = None
            self._corpus_matrix = None
            self._corpus_post_ids = []
            self._cached_post_count = 0
            return

        if len(rows) == self._cached_post_count and self._vectorizer is not None:
            return

        self._corpus_post_ids = [r[0] for r in rows]
        corpus_texts = [r[1] for r in rows]

        # Fit sublinear TF-IDF with unigrams and bigrams
        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
            max_features=10000
        )
        self._corpus_matrix = self._vectorizer.fit_transform(corpus_texts)
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
        if self._vectorizer is not None and self._corpus_matrix is not None:
            try:
                query_vec = self._vectorizer.transform([clean_query])
                sim_scores = cosine_similarity(query_vec, self._corpus_matrix)[0]
                
                # Sort descending by cosine similarity
                sorted_indices = np.argsort(sim_scores)[::-1]
                rank_counter = 1
                for idx in sorted_indices:
                    score = float(sim_scores[idx])
                    if score < 0.02 or rank_counter > 100:
                        break
                    p_id = self._corpus_post_ids[idx]
                    dense_ranks[p_id] = rank_counter
                    rank_counter += 1
            except Exception as e:
                print(f"Notice: Dense vector search error: {e}")

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
