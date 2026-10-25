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
* **Standardized 6-Field Enrichment**:
  1. *Theme* (e.g., Income timing, Unnoticed failed autopay, Expectation gap, Cancel instead of pause, Platform UX, Charges/Taxes).
  2. *Journey Stage* (e.g., Before starting, First instalment, Months 2 to 6, Experienced).
  3. *What They Did* (e.g., Continued, Paused, Reduced, Stopped, Switched Platform).
  4. *Who They Are* (Persona, income type, experience level).
  5. *Who Can Fix It* (Fintech Platform, Bank or AMC, User's own life, Regulator).
  6. *Evidence* (Exact verbatim quote substring + verified source URL).
* **Transparent Golden Set & Evaluation**: Allows instant manual tag correction, calculating Agreement %, Cohen's Kappa, and confusion matrices.
* **Minimalist PM Interface**: Single-screen data grid with slide-over Detail Panel, instant filtering, and one-click Excel export.
