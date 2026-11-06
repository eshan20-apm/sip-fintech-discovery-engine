# Problem Statement: SIP & Fintech Investor Discovery Engine

## 1. Context & Background
The Indian mutual fund industry has witnessed exponential retail participation over the past several years, driven by digital-first investment platforms (Groww, Zerodha Coin, Angel One, INDmoney, Kuvera, Paytm Money, Navi) and the popularity of Systematic Investment Plans (SIPs).

However, retaining investors and sustaining active SIPs remains a critical challenge across the fintech ecosystem:
* **High SIP Attrition & Discontinuation**: Millions of SIPs are paused, cancelled, or allowed to lapse each month due to friction points ranging from bank mandate failures and income-SIP date mismatches to expectation gaps during market downturns.
* **Complex Investor Personas**: Investors are not a monolith. The reasons for stopping an SIP differ vastly between a 22-year-old first-time investor entering during a bull run vs. an experienced salaried investor managing tax-saving ELSS funds vs. an NRI navigating FEMA compliance.
* **Cross-Platform Friction**: Each fintech platform introduces distinct operational nuances and bugs—e.g., BSE StAR MF vs. AMC-direct routing, bank autopay/e-mandate approvals, bounce charges, and platform-level switching behavior.

---

## 2. The Core Problem for Product Managers
Product Managers, growth leads, and retention teams studying investor drop-off currently face major obstacles:

1. **Fragmented, Unstructured Public Feedback**:
   Real user sentiment, confusion, and anger are scattered across unstructured public channels:
   * **Google Play Store Reviews**: Rich in immediate bug reports, mandate failures, and customer support grievances.
   * **Reddit (`r/IndiaInvestments`, `r/Mutualfunds`, `r/personalfinanceindia`)**: High-depth qualitative discussions about portfolio reallocation, platform switching, and tax implications.
   * **YouTube Comments**: Beginner questions, anxieties about market drawdowns, and "how-to-cancel" tutorials.

2. **No Real-Time, Zero-Cost Synthesis Tool**:
   PMs either rely on expensive, enterprise-heavy social listening suites (which lack fintech domain awareness) or manually copy-paste comments into spreadsheets. There is no lightweight tool that connects directly to free public sources to pull, deduplicate, and categorize comments on demand.

3. **Hallucination & Lack of Verbatim Grounding**:
   Off-the-shelf LLM summaries tend to synthesize generalizations without linking specific claims back to verbatim quotes or verifiable source links.

4. **Absence of a "Golden Truth" Feedback Loop**:
   PMs have no way to audit or correct AI-generated tags, build an authoritative benchmark ("Golden Set"), or measure model accuracy and drift over time.

5. **Risk of Vocal Minority Bias**:
   Public reviews overwhelmingly represent vocal, dissatisfied users. Without explicit visual warnings and structured sampling, PMs risk treating vocal friction frequency as population-wide statistical prevalence.

---

## 3. Goals & Objectives of the SIP Discovery Engine
The **SIP Discovery Engine** addresses this gap by providing an end-to-end qualitative research workbench:

* **Universal Investor Scope**: Studies investor behavior across all experience levels (first-timers to seasoned DIY investors).
* **Cross-Platform Coverage**: Ingests and tags feedback across all major Indian fintech apps (Groww, Zerodha Coin, Angel One, INDmoney, Kuvera, Paytm Money, etc.).
* **100% Free Live Data**: Utilizes public APIs and scrapers (Google Play Store, Reddit public JSON, YouTube comments) without requiring pre-ingested fixed datasets from the user.
* **Standardized Dynamic 6-Field Enrichment (No Rigid Buckets)**:
  1. *Dynamic Theme* (Concise 2–3 words derived directly from context, e.g., *Market dip anxiety*, *Autopay bounce penalty*, *SOA vs Demat switch*, *Missing pause option*).
  2. *Dynamic Journey Stage* (Inferred investor stage, e.g., *Onboarding / KYC*, *1st Month Beginner*, *Months 2-6 Market Dip*, *Platform Migration*, *Exit / Withdrawal*).
  3. *Dynamic Action Taken* (Actual action, e.g., *Cancelled SIP*, *Paused indefinitely*, *Switched Platform*, *Continued despite dip*, *Seeking forum advice*).
  4. *Who They Are* (Persona, income level, or experience level).
  5. *Who Can Fix It* (Fintech Platform, AMC / Registrar, NPCI / Bank, Investor Education).
  6. *Evidence Quote* (Exact verbatim quote substring + verified source URL with zero hallucination guarantee).
* **Conversational Discovery & Minimalist Interface**:
  * Prompt-driven entry space (ChatGPT / Perplexity style) featuring an initial **"Ready for Discovery" Starter Workspace** with prompt chips and investigation cards.
  * The **Structured Investor Feedback Feed** reveals dynamically upon submitting an inquiry, eliminating clutter on startup.
* **Transparent Golden Set & Reliability Suite**: Allows instant manual tag correction, computing observed agreement %, multi-field Cohen's Kappa ($\kappa$), interactive confusion matrix, and Disagreement Inspector.
* **Production & Deployment Reliability**: Built with cross-platform launchers (`run.py`, `run.bat`, `run.sh`), comprehensive unit test coverage, offline scraper resilience, and Vercel cloud serverless deployment compatibility.
* **Universal Spreadsheet Interoperability**: 1-click dual exports (.xlsx and .csv with UTF-8 BOM) compatible with Mac Numbers, Google Sheets, and Microsoft Excel with zero encoding or truncation glitches.
