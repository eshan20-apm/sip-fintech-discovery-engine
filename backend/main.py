import os
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env variables
load_dotenv()

from backend.database import init_db, fetch_posts, save_post_with_tag, save_golden_tag, get_stats
from backend.ingestion.playstore import fetch_playstore_reviews
from backend.ingestion.reddit import fetch_reddit_posts
from backend.ingestion.youtube import fetch_youtube_comments
from backend.ingestion.dedup import deduplicate_posts
from backend.tagger.llm_tagger import tag_post, analyze_research_query
from backend.exporter import export_posts_to_excel

app = FastAPI(title="SIP & Fintech Investor Discovery Engine API", version="2.1.0")

# CORS middleware for React client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to ensure SQLite tables exist
@app.on_event("startup")
def on_startup():
    init_db()

class ResearchQueryRequest(BaseModel):
    query: str
    platforms: Optional[List[str]] = None
    sources: Optional[List[str]] = ["playstore", "reddit", "youtube"]
    limit: Optional[int] = 25

class FetchLiveRequest(BaseModel):
    query: Optional[str] = "SIP investor behavior"
    platforms: Optional[List[str]] = ["Groww", "Zerodha", "AngelOne", "INDmoney", "PaytmMoney"]
    sources: Optional[List[str]] = ["playstore", "reddit", "youtube"]
    limit_per_source: Optional[int] = 20

class GoldenTagRequest(BaseModel):
    post_id: str
    theme: str
    journey_stage: str
    what_they_did: str
    who_they_are: str
    who_can_fix_it: Optional[str] = "Fintech Platform"
    evidence_quote: Optional[str] = ""
    notes: Optional[str] = ""

class ApiKeyRequest(BaseModel):
    api_key: str

from backend.retrieval.hybrid_search import hybrid_searcher
from backend.analytics.benchmark_eval import (
    get_evaluation_metrics,
    get_confusion_matrix_data,
    get_disagreements,
    resolve_disagreement,
    seed_golden_benchmarks
)

class ResolveDisagreementRequest(BaseModel):
    post_id: str
    resolution_type: str  # "accept_ai" or "override_golden"
    custom_tags: Optional[dict] = None

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "SIP Discovery Engine", "phase": "Phase 3 Active (Hybrid RAG & Evaluation)"}

@app.post("/api/research")
def conduct_research(req: ResearchQueryRequest):
    """
    Open-ended conversational research endpoint (ChatGPT/Gemini style):
    1. Analyzes the researcher's query using LLM
    2. Dynamically ingests matching posts from Play Store, Reddit, and YouTube
    3. De-spams and deduplicates (exact SHA-256 + fuzzy Jaccard similarity >80%)
    4. Tags each raw comment dynamically (2-3 word theme, dynamic stage, dynamic action)
    5. Retrieves top results using Hybrid RAG (Dense Semantic Vector + Sparse BM25 via RRF)
    """
    query_text = req.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Step 1: LLM query analysis to derive search intent, platforms, and keywords
    analysis = analyze_research_query(query_text)
    target_platforms = req.platforms or analysis.get("target_platforms") or ["Groww", "Zerodha", "AngelOne"]
    search_keywords = analysis.get("search_keywords") or [query_text]
    sources_to_query = req.sources or ["playstore", "reddit", "youtube"]

    raw_posts = []

    # Step 2: Fetch live Play Store reviews matching the analyzed keywords
    if "playstore" in sources_to_query:
        for p in target_platforms:
            p_reviews = fetch_playstore_reviews(
                platform=p,
                query=query_text,
                keywords=search_keywords,
                count=req.limit
            )
            raw_posts.extend(p_reviews)

    # Step 3: Fetch Reddit discussions matching the query
    if "reddit" in sources_to_query:
        reddit_results = fetch_reddit_posts(
            query=" ".join(search_keywords[:2]) if search_keywords else query_text,
            limit=req.limit
        )
        raw_posts.extend(reddit_results)

    # Step 4: Fetch YouTube personal finance comments
    if "youtube" in sources_to_query:
        youtube_results = fetch_youtube_comments(
            query=query_text,
            limit=req.limit
        )
        raw_posts.extend(youtube_results)

    # Step 5: De-spam and Deduplicate (exact SHA-256 + fuzzy Jaccard >80%)
    clean_posts, dropped_count = deduplicate_posts(raw_posts, similarity_threshold=0.80)

    # Step 6: Dynamically tag and persist each comment
    newly_saved = 0
    for post in clean_posts:
        tag_data = tag_post(post["raw_text"])
        tag_data["post_id"] = post["id"]
        if save_post_with_tag(post, tag_data):
            newly_saved += 1

    # Step 7: Hybrid RAG Search (Dense Vector + Sparse BM25 via RRF)
    results = hybrid_searcher.search(
        query=query_text,
        limit=req.limit * 2
    )

    if not results:
        results = fetch_posts(limit=req.limit * 2)

    return {
        "query": query_text,
        "analysis": analysis,
        "posts": results,
        "total_results": len(results),
        "newly_ingested": newly_saved,
        "duplicates_dropped": dropped_count
    }

@app.get("/api/posts")
def get_posts(
    search_query: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    status: Optional[str] = Query("all"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    # Use Hybrid RAG if search query is provided
    if search_query and search_query.strip():
        posts = hybrid_searcher.search(
            query=search_query.strip(),
            platform=platform,
            source=source,
            status=status,
            limit=limit
        )
        if posts:
            return {"posts": posts, "count": len(posts), "search_mode": "hybrid_rag"}

    posts = fetch_posts(
        search_query=search_query,
        platform=platform,
        source=source,
        status=status,
        limit=limit,
        offset=offset
    )
    return {"posts": posts, "count": len(posts), "search_mode": "lexical_fts"}

@app.get("/api/stats")
def get_system_stats():
    return get_stats()

@app.get("/api/evaluation/metrics")
def get_eval_metrics():
    """Returns Cohen's Kappa score and field reliability metrics comparing AI vs Golden Truth."""
    return get_evaluation_metrics()

@app.get("/api/evaluation/confusion-matrix")
def get_eval_confusion_matrix(field: str = Query("theme", pattern="^(theme|journey_stage|what_they_did|who_can_fix_it)$")):
    """Returns confusion matrix data for the specified categorical field."""
    return get_confusion_matrix_data(field=field, top_n=6)

@app.get("/api/evaluation/disagreements")
def get_eval_disagreements(limit: int = Query(50, ge=1, le=200)):
    """Returns posts where AI prediction diverged from Golden Truth benchmark."""
    return {"disagreements": get_disagreements(limit=limit)}

@app.post("/api/evaluation/resolve")
def post_resolve_disagreement(req: ResolveDisagreementRequest):
    """Resolves an AI vs Golden disagreement."""
    success = resolve_disagreement(
        post_id=req.post_id,
        resolution_type=req.resolution_type,
        custom_tags=req.custom_tags
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to resolve disagreement")
    return {"success": True, "post_id": req.post_id, "resolution": req.resolution_type}

@app.post("/api/evaluation/seed")
def post_seed_golden():
    """Seeds or supplements verified golden benchmark posts."""
    count = seed_golden_benchmarks()
    return {"success": True, "seeded_count": count}

@app.post("/api/fetch-live")
def fetch_live_data(req: FetchLiveRequest):
    """Direct multi-platform ingestion trigger across specified apps and sources."""
    raw_posts = []

    if "playstore" in req.sources:
        for p in req.platforms:
            reviews_list = fetch_playstore_reviews(
                platform=p,
                query=req.query,
                count=req.limit_per_source
            )
            raw_posts.extend(reviews_list)

    if "reddit" in req.sources:
        reddit_list = fetch_reddit_posts(
            query=req.query,
            limit=req.limit_per_source
        )
        raw_posts.extend(reddit_list)

    if "youtube" in req.sources:
        youtube_list = fetch_youtube_comments(
            query=req.query,
            limit=req.limit_per_source
        )
        raw_posts.extend(youtube_list)

    clean_posts, dropped_count = deduplicate_posts(raw_posts, similarity_threshold=0.85)

    saved_count = 0
    for post in clean_posts:
        tag_result = tag_post(post["raw_text"])
        tag_result["post_id"] = post["id"]
        success = save_post_with_tag(post, tag_result)
        if success:
            saved_count += 1

    return {
        "success": True,
        "total_fetched": len(raw_posts),
        "clean_posts": len(clean_posts),
        "saved_count": saved_count,
        "duplicates_dropped": dropped_count
    }

@app.post("/api/golden-tag")
def set_golden_tag(req: GoldenTagRequest):
    """Save PM override tag to the golden truth benchmark table."""
    try:
        updated = save_golden_tag(req.dict())
        return {"success": True, "golden_tag": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export")
def export_filtered_posts(
    search_query: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    status: Optional[str] = Query("all")
):
    posts = fetch_posts(
        search_query=search_query,
        platform=platform,
        source=source,
        status=status,
        limit=1000,
        offset=0
    )
    excel_bytes = export_posts_to_excel(posts)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=sip_discovery_research.xlsx"}
    )

@app.post("/api/settings/api-key")
def set_gemini_api_key(req: ApiKeyRequest):
    key = req.api_key.strip()
    if key:
        os.environ["GEMINI_API_KEY"] = key
        return {"success": True, "message": "Gemini API key updated for current session"}
    else:
        os.environ.pop("GEMINI_API_KEY", None)
        return {"success": True, "message": "Cleared API key, using dynamic heuristic engine"}

# ==========================================
# Frontend SPA & Static Assets Serving
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
FRONTEND_DIST = os.path.join(PROJECT_ROOT, "frontend", "dist")

if not os.path.exists(FRONTEND_DIST):
    for candidate in [
        os.path.join(os.getcwd(), "frontend", "dist"),
        os.path.join(CURRENT_DIR, "frontend", "dist"),
        os.path.join(CURRENT_DIR, "dist"),
        os.path.join(os.getcwd(), "dist")
    ]:
        if os.path.exists(candidate):
            FRONTEND_DIST = candidate
            break

if os.path.exists(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_root():
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"detail": "Frontend index.html not found"}

    @app.get("/{full_path:path}")
    async def serve_frontend_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"detail": "Frontend index.html not found"}

