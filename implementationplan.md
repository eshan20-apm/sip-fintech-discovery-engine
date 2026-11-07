# Implementation Plan: SIP & Fintech Investor Discovery Engine

## Phase Breakdown Overview

| Phase | Focus | Key Deliverables | Estimated Milestone |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Prompt-Driven Discovery & Dynamic Tagging** | Conversational query space (ChatGPT/Gemini style), Query Analyzer LLM, dynamic 2–3 word theme tagger, dynamic stage/action tagger, structured data grid, slide-over detail drawer, Excel export, manual golden set override. | Functional prototype operating on open-ended research queries |
| **Phase 2** | **Multi-Platform Ingestion & YouTube** | Multi-app scrapers (Groww, Zerodha, Angel One, INDmoney, Kuvera), YouTube comment scraper, deduplication engine, and Hinglish normalizer. | Broad cross-platform dataset accumulation |
| **Phase 3** | **Hybrid RAG & Golden Benchmark** | SQLite FTS5 + local vector embeddings, Cohen's Kappa evaluation dashboard, confusion matrix, and Disagreement Inspector. | Complete semantic retrieval & active evaluation |
| **Phase 4** | **Google Stitch UI Polish & Delivery** | Google Stitch UI design implementation, pixel-perfect layout, transitions, multi-tab Excel export, and deployment documentation. | Production-ready research workbench |
| **Phase 5** | **Production Hardening, Zero-Error Assurance & Vercel Cloud** | Type safety, Pyright interpreter binding, SQLite WAL concurrency, self-healing FTS5 sync check, 31-test suite, cross-platform launchers (`run.py`, `run.bat`), "Ready for Discovery" workspace, and Vercel serverless cache-busting. | Enterprise-ready public release & cloud deployment |

---

## Phase 1: Prompt-Driven Discovery & Dynamic Tagging (Clean Working Version)

### Objective
Deliver a simple, user-friendly qualitative research workbench where researchers can enter free-form prompts (just like ChatGPT or Gemini) to research investor behavior across Indian SIP platforms. An LLM analyzes the query, triggers targeted ingestion across public channels (Play Store reviews, Reddit), and dynamically extracts structured fields (Platform, Source, Date, Raw Comment, 2–3 Word Dynamic Theme, Dynamic Journey Stage, Action Taken, and Verbatim Evidence Quote) into an interactive table and slide-over panel without rigid dropdown filters.

### 1.1 Backend Core Setup
* **Query Analyzer Engine**:
  * Interprets the researcher's open-ended prompt (e.g. *"Why do investors pause or cancel SIPs after market drops?"*).
  * Extracts search intents, targeted apps (Groww, Zerodha, Angel One, etc.), and keyword queries for ingestion scrapers.
* **Targeted Free Ingestion**:
  * Google Play Store scraper fetching reviews matching the query keywords across 1–3 star friction ratings.
  * Reddit search module querying `r/IndiaInvestments` and `r/Mutualfunds` with query-aligned terms.
* **Dynamic Comment Tagging Engine**:
  * An LLM reads each raw comment and extracts:
    * `theme`: 2–3 word dynamic summary of the problem or friction (not fixed to a pre-defined list).
    * `journey_stage`: dynamic stage derived from context (not fixed).
    * `what_they_did`: dynamic action taken (not fixed).
    * `who_they_are`: investor persona.
    * `evidence_quote`: exact verbatim substring from raw text.
  * Zero-hallucination validation: `assert evidence_quote in raw_text`.
* **Database & Export**:
  * SQLite database (`sip_discovery.db`) storing `posts`, `post_tags`, `golden_tags`, and FTS5 search table.
  * Excel exporter generating clean `.xlsx` spreadsheets.

### 1.2 Frontend Setup & Minimal Interface
* **Conversational Query Screen (ChatGPT / Gemini Style)**:
  * Top Research Bias Caution Banner.
  * Prominent, clean central prompt bar where researchers type their query.
  * Quick-prompt suggestion chips (e.g. *"Why do investors cancel during market falls?"*, *"What issues happen with SIP date vs salary credit?"*, *"Why switch from Groww to Zerodha Coin?"*).
  * Live status indicator ("Analyzing query...", "Searching Play Store & Reddit...", "Tagging raw comments...").
  * **Removed static categorical filters under query bar**: No `theme`, `stage`, `action`, or `fixer` dropdown clutter.
* **Structured Data Grid**:
  * Columns: Status (Golden vs. AI Tagged), Platform, Source, Date, Raw Comment, Theme (dynamic 2–3 words), Journey Stage (dynamic), Action Taken (dynamic).
  * "Download Excel" button exporting the active research results.
* **Slide-Over Detail Panel**:
  * Full raw post with verbatim evidence highlighted in yellow/amber `<mark>`.
  * Direct clickable link to the live post.
  * Golden Benchmark editor allowing PMs to refine the dynamic tags and add research rationale.
  * Auto-save handler updating records in `golden_tags`.

### 1.3 Verification & Testing Criteria
- [x] Researcher can enter open-ended natural language prompts (ChatGPT/Gemini style).
- [x] Query analyzer interprets query and extracts targeted ingestion keywords.
- [x] LLM dynamically tags raw comments with 2–3 word open-ended themes, dynamic journey stages, and actions without rigid taxonomy constraints.
- [x] Evidence quotes are guaranteed verbatim substrings of the raw comments.
- [x] Modifying tags in Detail Panel persists to `golden_tags` across page reloads.
- [x] Excel download produces a valid `.xlsx` file matching the active research query.

---

## Phase 2: Multi-Platform Ingestion & YouTube Pipeline (Completed)

### Objective
Expand the ingestion and normalization pipeline beyond single-app reviews to capture authentic retail investor behavior across multiple major Indian fintech platforms (Groww, Zerodha Coin, Angel One, INDmoney, Paytm Money), live YouTube personal finance comments, robust deduplication, and colloquial Hinglish intent extraction.

### 2.1 Multi-Platform Scrapers
* **Play Store Ingestion ([playstore.py](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/backend/ingestion/playstore.py))**:
  * Extends coverage across 5 leading Indian investment platforms: Groww (`com.nextbillion.groww`), Zerodha Coin (`com.zerodha.coin`), Angel One (`com.msf.angelmobile`), INDmoney (`in.indwealth`), and Paytm Money (`com.paytmmoney`).
  * Filters 1–3 star friction reviews dynamically targeted by researcher query keywords.

### 2.2 Live YouTube Comment Extraction
* **YouTube Ingestion Pipeline ([youtube.py](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/backend/ingestion/youtube.py))**:
  * Real-time YouTube video discovery using dynamic search queries (`search_youtube_video_ids`).
  * Live user comment scraping with `youtube-comment-downloader` across prominent Indian personal finance tutorial creators (Asset Yogi, CA Rachana Ranade, Labor Law Advisor, Smart Investor, Pranjal Kamra).
  * Seamless fallback to an authentic public comment archive during anonymous IP throttling.

### 2.3 Token Deduplication & Spam Protection
* **Multi-Stage Deduplication Engine ([dedup.py](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/backend/ingestion/dedup.py))**:
  * **Spam & Bot Filtering**: Rejects promotional Telegram signals, WhatsApp trading groups, crypto bots, and financial advisory advertisements.
  * **Exact Match Deduplication**: Normalizes whitespace/casing and compares SHA-256 hashes.
  * **Fuzzy Jaccard Token Match**: Strips noise stopwords and computes token overlap; drops duplicate cross-posts exceeding 80% similarity.

### 2.4 Hinglish Normalizer & Dynamic Enrichment
* **Indian Fintech Hinglish Engine ([hinglish.py](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/backend/ingestion/hinglish.py))**:
  * Domain dictionary mapping common colloquial phrases (*"paisa cut gaya"*, *"units allocate nahi hue"*, *"mandate bounce"*, *"sip band kaise kare"*, *"pause ka option"*, *"salary date match nahi ho rahi"*, *"nuksan ho gaya"*).
  * Enriches heuristic and LLM taggers with structured intent and contextual English notes, ensuring colloquial comments receive sharp dynamic 2–3 word themes.

### 2.5 Verification & Testing Criteria
- [x] Play Store reviews successfully fetched and parsed for all 5 platforms (Groww, Zerodha Coin, Angel One, INDmoney, Paytm Money).
- [x] Live YouTube comment downloader extracts authentic retail investor discussions from personal finance tutorials.
- [x] Multi-stage deduplication drops duplicate cross-posts and promotional spam links with verified dropped counts.
- [x] Hinglish normalizer maps colloquial Hindi-English complaints to dynamic themes, journey stages, and actions.
- [x] Database populated with 280+ diverse, multi-platform posts across Play Store (206), Reddit (51), and YouTube (30).
- [x] Research query endpoint (`/api/research`) operates seamlessly across all three sources.

---

## Phase 3: Hybrid RAG & Golden Benchmark Analytics (Completed)

### Objective
Implement high-precision hybrid semantic retrieval combining sparse lexical search (SQLite FTS5 BM25) and dense semantic vector search (TF-IDF sublinear n-gram embeddings) fused via Reciprocal Rank Fusion (RRF). Provide a quantitative reliability evaluation suite measuring Cohen's Kappa ($\kappa$), interactive confusion matrix, and a Disagreement Inspector to audit and resolve divergences between AI tagging and PM Golden Truth hand-labels.

### 3.1 Hybrid RAG Engine ([hybrid_search.py](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/backend/retrieval/hybrid_search.py))
* **Sparse Lexical Search**: Uses SQLite FTS5 with native BM25 rank scoring for exact keyword and prefix matches.
* **Dense Semantic Vector Search**: Sublinear TF-IDF n-gram vectorizer (unigrams + bigrams) computing cosine similarity over comment text to capture semantic synonyms and conceptual relevance without requiring exact keyword overlap.
* **Reciprocal Rank Fusion (RRF)**: Merges sparse and dense ranked candidate lists using $Score(d) = \sum \frac{1}{60 + rank_i(d)}$.

### 3.2 Reliability & Evaluation Suite ([benchmark_eval.py](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/backend/analytics/benchmark_eval.py))
* **Cohen's Kappa ($\kappa$) Metric**: Computes chance-adjusted agreement across multi-class classifications (Theme, Journey Stage, Action Taken, Fixer) using standard Landis & Koch reliability interpretation scale.
* **Interactive Confusion Matrix**: Generates a contingency matrix grid of top theme classifications, highlighting accurate agreements on the diagonal in emerald green and classification divergences in amber.
* **Disagreement Inspector**: Dedicated audit suite isolating posts where AI tags diverge from Golden Truth hand-labels. Provides side-by-side comparison cards and one-click actions:
  * `Accept AI Prediction`: Promotes AI tag to the golden benchmark.
  * `Keep Golden Benchmark`: Maintains researcher hand-labeled truth.

### 3.3 Evaluation Dashboard UI ([EvaluationDashboardModal.jsx](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/frontend/src/components/EvaluationDashboardModal.jsx))
* Added a persistent "Golden Benchmark (κ)" trigger button to the top navbar with live verified count.
* Comprehensive modal containing 3 tabs:
  1. *Cohen's Kappa & Reliability*: Score gauge, qualitative label, observed raw agreement, and field breakdown progress bars.
  2. *Theme Confusion Matrix*: Field selector, cross-tabulation table with diagonal match highlights.
  3. *Disagreement Inspector*: Side-by-side comparison cards, verbatim evidence quotes, mismatch alerts, and instant resolution buttons.

### 3.4 Verification & Testing Criteria
- [x] Hybrid search (`HybridSearchEngine`) successfully fuses SQLite FTS5 BM25 and dense TF-IDF vectors using RRF.
- [x] Natural language queries semantically retrieve conceptually relevant comments without requiring exact keyword matches.
- [x] Cohen's Kappa engine computes field-level $\kappa$ and overall chance-adjusted agreement ($\kappa = 0.665$, "Substantial Agreement").
- [x] Confusion matrix endpoint generates accurate contingency matrix for top themes and stages.
- [x] Disagreement Inspector accurately isolates tag divergences and supports one-click resolution.
- [x] Evaluation Dashboard modal integrates into the frontend with live data updates.

---

## Phase 4: Google Stitch UI Polish & Delivery (Completed)

### Objective
Elevate the research workbench to executive presentation grade with Google Stitch inspired visual design, rich dark-mode micro-interactions, full keyboard accessibility, an executive multi-tab Excel export engine, a master executable launch script, and comprehensive deployment documentation.

### 4.1 Multi-Tab Executive Excel Exporter ([exporter.py](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/backend/exporter.py))
* Generates an executive `.xlsx` workbook featuring 3 formatted sheets:
  1. **Sheet 1 — Active Research Feed**: Filtered and semantically ranked posts matching the researcher's query (Platform, Source, Published Date, Dynamic 2–3 Word Theme, Journey Stage, Action Taken, Persona, Responsible Entity, Verbatim Evidence Quote, RRF Relevance Score, Status, Notes, Raw Text, Link).
  2. **Sheet 2 — Golden Benchmark Set**: Complete PM-verified hand-labeled truth set with classification rationales.
  3. **Sheet 3 — Reliability & Kappa Metrics**: Summary of Cohen's Kappa score ($\kappa = 0.665$, "Substantial Agreement"), observed agreement rates ($82.7\%$), and field-by-field accuracy breakdowns.
* Professional openpyxl formatting: Navy blue `#1E293B` bold headers, frozen header panes (`A2`), auto-fitted column widths, and text wrapping.

### 4.2 Google Stitch UI Polish & Micro-Interactions
* **Keyboard Accessibility**: Global `Escape` key listener instantly dismisses the Detail Drawer, Evaluation Dashboard, and API Key modal.
* **Ambient Search Mode Badge**: Table header displays `⚡ Hybrid RAG Active` whenever a semantic query is active.
* **Interactive Metrics Strip**: The Golden Benchmark and Cohen's Kappa cards feature hover elevation and direct click-to-open handlers linking to the evaluation dashboard.
* **Color System**: Tailored dark-mode tokens for each platform (`.badge-groww`, `.badge-zerodha`, `.badge-angelone`, `.badge-indmoney`, `.badge-paytmmoney`, `.badge-youtube`).

### 4.3 Packaging & Deployment Documentation
* **Master Launch Script ([run.sh](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/run.sh))**: Executable startup script that checks Node and Python environments, initializes the SQLite database, launches FastAPI on port 8000, launches Vite on port 5173, and cleanly shuts down on `Ctrl+C`.
* **Documentation ([README.md](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/README.md))**: Complete architecture diagrams, quick-start instructions, LLM configuration guide, and methodology notes.

### 4.4 Verification & Testing Criteria
- [x] Multi-tab Excel export generates a valid 3-sheet `.xlsx` workbook (*Active Research Feed*, *Golden Benchmark Set*, *Reliability & Kappa Metrics*) with auto-fitted columns and freeze panes.
- [x] Global `Escape` key closes all open modals and drawers.
- [x] Metrics Bar cards provide interactive one-click access to the Evaluation Dashboard.
- [x] Table displays ambient `⚡ Hybrid RAG Active` status indicator.
- [x] `run.sh` master script starts both backend and frontend concurrently with graceful exit handling.
- [x] Complete `README.md` provides end-to-end setup and methodology documentation.
- [x] Production build passes cleanly (`npm run build` in 116ms with 0 errors).

---

## Phase 5: Production Hardening, Zero-Error Assurance & Vercel Cloud (Completed)

### Objective
Guarantee that external researchers and public open-source users running the workbench on any operating system (macOS, Windows, Linux) or accessing the hosted cloud application on Vercel experience zero crashes, zero unhandled errors, zero language server squigglies, and a smooth, conversational user experience.

### 5.1 Type Safety & Language Server Diagnostics
* **Interpreter Synchronization**: Added [`.vscode/settings.json`](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/.vscode/settings.json), [`pyrightconfig.json`](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/pyrightconfig.json), and a root `.venv` symlink to prevent IDE language servers from querying system macOS Python.
* **Typed Scraper Interfaces**: Implemented `TypedDict` models (`CuratedReview`, `CuratedRedditPost`, `FintechVideo`, `CuratedYoutubeComment`) across scrapers to eliminate inferred `int | str` union typing mismatches.
* **Text Cleaner Robustness**: Broadened `clean_text` in [`normalizer.py`](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/backend/ingestion/normalizer.py) to accept `Any`, safely handling integer scores and `None` inputs.

### 5.2 Database Self-Healing & Concurrency Hardening
* **WAL Mode & Concurrency**: Enabled `PRAGMA journal_mode=WAL;` and `PRAGMA foreign_keys=ON;` with 30-second busy timeout in [`database.py`](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/backend/database.py).
* **Self-Healing FTS5 Sync**: On `init_db()`, compares record counts between `posts` and `posts_fts`; automatically restores and rebuilds full-text search index if discrepancies are detected.
* **FTS5 Fault-Tolerant Search Fallback**: Automatically catches `sqlite3.OperationalError` from malformed search punctuation/syntax and falls back cleanly to SQL `LIKE ?` search.

### 5.3 Conversational UX Refinement & Discovery Starter
* **Clean Launch Workspace**: Removed the cluttered 100-comment data grid on initial launch, focusing the screen on the conversational prompt bar.
* **"Ready for Discovery" Workspace**: Rendered 3 interactive starter investigation cards (*SIP Cancellation Anxiety*, *Mandate & Bounce Failures*, *Broker Migration & Demat*) when no query is active.
* **Query-Triggered Feed Reveal**: The Structured Investor Feedback Feed displays dynamically only after an inquiry is entered or a starter card is clicked.

### 5.4 Cross-Platform Launchers & Packaging
* **Universal Launcher ([run.py](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/run.py))**: Platform-agnostic Python runner supporting macOS, Linux, and Windows. Automatically provisions virtual environments, installs requirements, builds frontend dependencies, and runs FastAPI + Vite concurrently.
* **Native Windows Launcher ([run.bat](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/run.bat))**: Dedicated batch script for Windows users.
* **Native Bash Launcher ([run.sh](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/run.sh))**: Hardened POSIX launcher with automated dependency checks.

### 5.5 Comprehensive Automated Test Suite
* Built 33 unit and integration tests under [`tests/`](file:///Users/eshan/Documents/NestLeap_graduation%20project/Attempt%202/SIP_AI_engine_build/tests):
  * `test_api.py`: FastAPI endpoints, health checks, search parameters, dual-format export (.xlsx and .csv), and settings.
  * `test_database.py`: CRUD operations, stats aggregation, golden overrides, and FTS5 punctuation resilience.
  * `test_evaluation.py`: Cohen's Kappa chance calculation, confusion matrix structure, and disagreement resolution.
  * `test_exporter.py`: Multi-tab openpyxl workbook structure, UTF-8 BOM CSV export, and XML-illegal character control filtering.
  * `test_ingestion.py`: Deduplication math, Hinglish normalization, spam link rejection, and scrapers.
  * `test_retrieval.py`: Hybrid RAG fusion and TF-IDF semantic scoring.
  * `test_tagger.py`: Zero-hallucination verbatim quote assertions and heuristic categorization.

### 5.6 Vercel Serverless Cloud Deployment & Cache-Busting
* **Request Forwarding Middleware**: Intercepts `x-matched-path` in `backend/main.py` for seamless ASGI routing on Vercel.
* **Cache-Busting HTTP Headers**: Added `Cache-Control: no-cache, no-store, must-revalidate` to `index.html` to eliminate browser caching of stale JavaScript hashes.
* **Cold-Start Persistence**: Safely hydrates the SQLite database into `/tmp/` in serverless execution environments.

### 5.7 Universal Spreadsheet Export (Mac Numbers, Google Sheets & MS Excel)
* **XML Control Character Sanitization**: Added `clean_cell_val()` in `backend/exporter.py` stripping illegal XML control characters (`\x00`–`\x1f`) via `ILLEGAL_CHARACTERS_RE` to eliminate corruption errors when opening in Apple Numbers or Microsoft Excel.
* **Dual Format Support**: Extended `/api/export` in `backend/main.py` to support both formatted Excel (`format=xlsx`) and universal CSV (`format=csv`).
* **UTF-8 Byte Order Mark (BOM)**: Added `\ufeff` to CSV generation so Apple Numbers, Google Sheets, and Excel automatically recognize UTF-8 characters, rupee signs (₹), and Hinglish terms.
* **Client-Side Blob Lifecycle Resilience**: Fixed synchronous `URL.revokeObjectURL()` in `frontend/src/App.jsx` with a 60-second delayed cleanup and direct browser navigation fallback, eliminating truncated `.bin` or `.txt` downloads on Safari and Chrome.
* **Smart Filename & macOS Extension Guard**: Added query-aware filename generation and an optional filename input in the prompt bar that automatically enforces and appends `.xlsx` / `.csv` (e.g. `1.4` $\rightarrow$ `1.4.xlsx`), preventing macOS Save sheets from dropping extensions when periods are entered.

### 5.8 Verification & Testing Criteria
- [x] Zero language server / type checker errors across all backend modules.
- [x] All 33 automated tests pass cleanly (`Ran 33 tests in 0.413s - OK`).
- [x] Database self-healing automatically synchronizes FTS5 records.
- [x] Startup screen displays the clean "Ready for Discovery" workspace; reveals the structured feed only upon research prompt execution.
- [x] Cross-platform launchers (`run.py`, `run.bat`, `run.sh`) successfully orchestrate backend and frontend.
- [x] Universal exports (.xlsx and .csv) open natively without conversion errors in Mac Numbers, Google Sheets, and Microsoft Excel.
- [x] Live Vercel deployment ([https://sip-fintech-discovery-engine.vercel.app](https://sip-fintech-discovery-engine.vercel.app)) serves the latest build with cache-busting headers.
