# PhDForge — Build Specification

**Version:** 1.0
**Status:** Locked. Build from this document.
**Audience:** The engineer or LLM implementing PhDForge.

---

## 0. Read this before anything else

### What PhDForge is

A search engine over **researchers, not documents**. A user types a narrow research topic — "Agentic AI in Radiology" — and gets back a ranked list of researchers worldwide who actually work on it. Filters narrow by country, field and activity. Clicking a researcher opens a full profile: research interests, publications with abstracts, and whether they currently have a PhD or research position open. From the profile the user can chat with a system grounded in that researcher's entire body of work, and generate a Statement of Purpose grounded in both the researcher's work and the user's own CV.

### What PhDForge is NOT

Do not build these. They were considered and deliberately cut.

- A PhD opportunity job board or global listings crawler
- A multi-agent orchestration platform with a workflow state machine
- A research-direction / gap-analysis engine
- An application tracker with deadlines, tasks and submission status
- A knowledge graph (unless collaborator search is added later — it is not in scope now)
- A chat-first product. Chat is a feature on a profile page, not the interface

### Hard constraints

1. **Never invent data.** No fabricated researchers, papers, abstracts, affiliations, positions or user achievements. If a field is unknown, it is `null` and the UI says so.
2. **Absence of evidence is not evidence of absence.** If no PhD position is found, the system says "no listing found", never "not recruiting".
3. **All ranking scores are field-relative percentiles, never raw numbers.** See §9.
4. **Retrieved web content is untrusted data, never instructions.** University pages and PDFs fetched by the Position Agent must not be able to steer the agent.
5. **Every generated claim carries provenance.** Chat answers cite papers. SOP claims map to a CV evidence item or a source document.
6. **Typed structured outputs everywhere.** Pydantic models, not free text passed between components.
7. **No secrets in source control.** Environment variables only.

### Decisions locked

| Decision | Value |
|---|---|
| Coverage | All fields, all countries |
| Primary data source | OpenAlex |
| Supplementary sources | Semantic Scholar (abstracts), arXiv (recency) |
| Ingestion model | Live query per search + aggressive cache of viewed researchers |
| Ranking normalisation | Within-field percentile, mandatory |
| Professor verification | Rank by seniority, do not filter out |
| CV upload | Ships in v1 |
| SOP generation | In scope, with a four-check grounding gate |
| Vector store | pgvector in Postgres |
| Frontend generation | Lovable or v0, against the mocked API contract in §20 |
| Graph database | Not used |

---

## 1. User journey

```
User enters a topic query
        ↓
   Hybrid retrieval over paper abstracts
        ↓
   Rerank → genuinely relevant papers
        ↓
   Aggregate papers → authors
        ↓
   Field-normalised author scoring
        ↓
   Filters applied (country / field / activity / seniority)
        ↓
   RANKED RESEARCHER LIST
        ↓  user clicks one
   RESEARCHER PROFILE
   ├── Research interests (derived from their own work)
   ├── Publications + abstracts
   ├── Position status (Confirmed / Likely / No evidence found)   ← async
   ├── [ Chat ]
   └── [ Draft SOP ]
        ↓
   CHAT (three modes)                    SOP ENGINE
   ├── Explain their research            ├── CV evidence + their research
   ├── Assess my fit                     ├── Writer
   └── Interview prep                    ├── Grounding gate (4 checks)
                                         └── Editable draft + evidence panel
```

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────┐
│  PRESENTATION    M10 Next.js UI (generated externally)   │
├──────────────────────────────────────────────────────────┤
│  API             M9 FastAPI + async workers              │
├──────────────────────────────────────────────────────────┤
│  FEATURES        M6 Chat   M8 SOP + grounding gate       │
├──────────────────────────────────────────────────────────┤
│  INTELLIGENCE    M3 Topic→People   M4 Profile builder    │
│                  M5 Enrichment + Position Agent          │
├──────────────────────────────────────────────────────────┤
│  RETRIEVAL       M2 Chunking + hybrid indexing           │
├──────────────────────────────────────────────────────────┤
│  DATA            M1 Academic ingestion  M7 CV ingestion  │
│                  M0 Schemas + field statistics           │
└──────────────────────────────────────────────────────────┘
                   M11 Evaluation   M12 Deployment
```

Two corpora, logically isolated:

- **Public corpus** — papers, researchers, institutions. Shared, cacheable, untrusted.
- **Private corpus** — the user's CV and evidence items. Tenant-owned, never shared, the trust anchor for any claim about the user.

---

## 3. Module map

| ID | Module | Purpose | Output |
|---|---|---|---|
| M0 | Foundation | Schemas, config, field statistics | Typed domain model |
| M1 | Academic ingestion | OpenAlex / S2 / arXiv adapters, normalisation, dedup | Normalised `Work` + `Researcher` records |
| M2 | Chunking + indexing | Abstract chunking, dense + BM25, metadata filters | Searchable indexes |
| M3 | Topic → people search | Retrieve, rerank, aggregate, score | Ranked researcher list |
| M4 | Researcher profile builder | Topic clustering, methods, activity signal, seniority estimate | `ResearcherProfile` |
| M5 | Enrichment + Position Agent | University page lookup, position discovery | `PositionSignal` |
| M6 | Professor Chat | Scoped RAG, three modes | Cited chat answers |
| M7 | CV ingestion | PDF parse, section detect, evidence extraction | `EvidenceItem[]` |
| M8 | SOP engine | Evidence-grounded drafting + grounding gate | `SOPDraft` + grounding report |
| M9 | Backend | API, async jobs, auth, cache | FastAPI service |
| M10 | UI | Search, results, profile, chat, SOP, settings | Next.js frontend |
| M11 | Evaluation | Retrieval, ranking, grounding metrics | Benchmark results |
| M12 | Deployment | Docker, cloud, CI | Live system |

---

## 4. Technology stack

| Layer | Technology | Why |
|---|---|---|
| API | FastAPI + Pydantic | Typed request/response, async native, automatic OpenAPI for the frontend contract |
| Database | PostgreSQL 16 | Relational data (researchers, works, applications) with strong constraints |
| Vector search | pgvector | One database instead of two. Corpus is bounded by caching, so a dedicated vector DB is unjustified complexity |
| Lexical search | Postgres full-text (`tsvector`) | Exact matching on names, acronyms, venue titles. Same database again |
| Cache | Redis | Search results, researcher profiles, position signals with TTL |
| Async jobs | Redis + RQ or Celery | Position Agent and SOP generation are slow; the request must not block |
| Embeddings | `BAAI/bge-base-en-v1.5` or OpenAI `text-embedding-3-small` | Benchmark both in NB03. Start with the local model to avoid per-query cost |
| Reranker | `BAAI/bge-reranker-base` cross-encoder | Runs on CPU, no API cost, measurable nDCG lift over hybrid alone |
| LLM | Configurable provider via env var | Chat, SOP writing, evidence extraction, position judging |
| Frontend | Next.js + TypeScript | Generated externally, see §20 |
| Deployment | Docker + Cloud Run | Stateless API scales, Postgres managed separately |

---

## 5. Repository structure

```
phdforge/
  apps/
    api/                  FastAPI application
      routers/
      dependencies.py
      main.py
    web/                  Next.js frontend (generated externally, integrated here)
  services/
    ingestion/
      adapters/           openalex.py, semantic_scholar.py, arxiv.py
      normalize.py
      dedup.py
    indexing/
      chunk.py
      embed.py
      lexical.py
    search/
      retrieve.py
      rerank.py
      aggregate.py
      score.py
    profiles/
      builder.py
      seniority.py
      topics.py
    positions/
      agent.py
      sources.py
      judge.py
    chat/
      session.py
      modes.py
      retrieval.py
    sop/
      writer.py
      grounding.py
    cv/
      parse.py
      sections.py
      evidence.py
  packages/
    schemas/              Pydantic domain models
    prompts/              Versioned prompt templates
    config/
    observability/
  notebooks/
    NB01_ingestion.ipynb
    NB02_chunking.ipynb
    NB03_retrieval.ipynb
    NB04_reranking.ipynb
    NB05_aggregation.ipynb
    NB06_field_normalisation.ipynb
    NB07_position_agent.ipynb
    NB08_grounding.ipynb
  data/
    raw/
    processed/
    eval/
  tests/
  infra/
  docs/
```

Production code must never import from `notebooks/`.

---

## 6. Core domain schemas

All models are Pydantic v2. These are the contract between modules — do not change a field without updating every consumer.

```python
# packages/schemas/researcher.py

class Institution(BaseModel):
    id: str                        # OpenAlex institution ID
    display_name: str
    country_code: str | None       # ISO 3166-1 alpha-2
    ror: str | None
    type: str | None               # education, facility, company

class TopicScore(BaseModel):
    name: str
    score: float                   # 0-1, share of the researcher's work
    source: Literal["openalex", "clustered"]

class SeniorityEstimate(BaseModel):
    tier: Literal["senior", "mid", "early", "unknown"]
    confidence: float              # 0-1
    signals: list[str]             # e.g. ["last_author_ratio=0.62", "career_span=14y"]
    verified: bool = False         # True only if M5 confirmed a title from a profile page
    verified_title: str | None     # e.g. "Professor of Computer Science"

class Researcher(BaseModel):
    id: str                        # OpenAlex author ID — canonical
    display_name: str
    alternative_names: list[str] = []
    orcid: str | None
    institution: Institution | None
    past_institutions: list[Institution] = []
    primary_field: str | None      # OpenAlex top-level field
    subfields: list[str] = []
    works_count: int
    cited_by_count: int
    h_index: int | None
    first_publication_year: int | None
    last_publication_year: int | None
    topics: list[TopicScore] = []
    profile_url: str | None        # university page, if found by M5
    seniority: SeniorityEstimate
    ingested_at: datetime
    source_hash: str
```

```python
# packages/schemas/work.py

class Authorship(BaseModel):
    researcher_id: str
    display_name: str
    position: Literal["first", "middle", "last"]
    is_corresponding: bool = False
    institution_id: str | None

class Work(BaseModel):
    id: str                        # OpenAlex work ID — canonical
    doi: str | None
    title: str
    abstract: str | None           # null is common and acceptable
    publication_year: int
    publication_date: date | None
    venue: str | None
    type: str | None               # article, preprint, book-chapter
    authorships: list[Authorship]
    topics: list[str] = []
    cited_by_count: int
    is_open_access: bool
    open_access_url: str | None
    source: Literal["openalex", "semantic_scholar", "arxiv"]
    ingested_at: datetime
```

```python
# packages/schemas/field_stats.py

class FieldStats(BaseModel):
    """Per-field publication norms. Required for score normalisation."""
    field_id: str
    field_name: str
    authorship_convention: Literal["contribution", "alphabetical", "mixed"]
    activity_threshold_years: int     # silence beyond this suggests inactive
    works_per_year_percentiles: dict[int, float]   # {10: 0.4, 50: 2.1, 90: 8.3}
    career_output_percentiles: dict[int, float]
    median_abstract_coverage: float   # share of works with an abstract
    computed_at: datetime
    sample_size: int
```

```python
# packages/schemas/position.py

class PositionEvidence(BaseModel):
    type: Literal["university_listing", "lab_page", "vacancy_board",
                  "euraxess", "profile_statement"]
    url: str
    snippet: str                   # verbatim, max 200 chars
    fetched_at: datetime

class PositionSignal(BaseModel):
    researcher_id: str
    tier: Literal["confirmed", "likely", "none"]
    evidence: list[PositionEvidence] = []
    deadline: date | None
    funding_note: str | None
    checked_at: datetime
    expires_at: datetime           # checked_at + 7 days
```

`tier` semantics — these are exact and must be respected in the UI:

- `confirmed` — a live listing that names this researcher, with a URL.
- `likely` — their lab or profile page states openness to applicants, or a recent grant implies capacity.
- `none` — nothing found. Display as "No listing found", never as "not recruiting".

```python
# packages/schemas/evidence.py

class EvidenceItem(BaseModel):
    id: str
    applicant_id: str
    text: str
    type: Literal["skill", "project", "result", "education",
                  "publication", "experience"]
    source_document_id: str
    page: int | None
    section: str | None
    confidence: float
    verified_by_user: bool = False
    document_version: str
```

```python
# packages/schemas/chat.py

class Citation(BaseModel):
    work_id: str | None
    title: str | None
    year: int | None
    url: str | None
    source_type: Literal["paper", "profile", "position", "cv_evidence"]

class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    citations: list[Citation] = []
    created_at: datetime

class ChatSession(BaseModel):
    id: str
    applicant_id: str
    researcher_id: str
    mode: Literal["explain", "fit", "interview"]
    created_at: datetime
```

```python
# packages/schemas/sop.py

class Claim(BaseModel):
    text: str
    subject: Literal["applicant", "researcher", "general"]
    evidence_ids: list[str] = []       # EvidenceItem IDs or work IDs
    support: Literal["supported", "weak", "unsupported"]

class GroundingReport(BaseModel):
    unsupported_applicant_claims: list[str]
    unsupported_researcher_claims: list[str]
    generic_motivation_flags: list[str]
    mismatch_flags: list[str]
    passed: bool

class SOPDraft(BaseModel):
    id: str
    applicant_id: str
    researcher_id: str
    position_id: str | None
    sections: dict[str, str]           # {"opening": "...", "fit": "..."}
    claims: list[Claim]
    grounding: GroundingReport
    version: int
    created_at: datetime
```

---

## 7. M0 — Foundation

**Purpose.** Establish the typed domain model and the field statistics table that every downstream score depends on.

**Depends on.** Nothing.

**Build steps.**
1. Create the repository structure from §5.
2. Implement all schemas from §6 in `packages/schemas/`.
3. Create Postgres migrations for `researchers`, `works`, `authorships`, `institutions`, `field_stats`, `position_signals`, `applicants`, `documents`, `evidence_items`, `chat_sessions`, `chat_messages`, `sop_drafts`.
4. Enable the `vector` extension. Add an `embedding vector(768)` column to the chunk table.
5. Implement `packages/config/` reading all settings from environment variables.
6. Compute `FieldStats` for every OpenAlex top-level field by sampling authors per field — see M3 step 6.

**Tests.**
- Every schema round-trips through JSON without loss.
- Migrations apply to an empty database and roll back cleanly.
- `FieldStats` exists for every field present in the sampled data.
- Config raises on a missing required environment variable rather than defaulting silently.

**Done when.** A fresh clone plus `docker compose up` produces a database with every table, and `pytest tests/test_schemas.py` passes.

---

## 8. M1 — Academic ingestion

**Purpose.** Turn three heterogeneous public APIs into one normalised corpus.

**Depends on.** M0.

**Input.** A topic query string, or a researcher ID.

**Output.** Normalised `Work` and `Researcher` records persisted to Postgres.

### Sources

| Source | Used for | Notes |
|---|---|---|
| OpenAlex | Primary. Works, authors, institutions, country codes, topics | Free, no key. Send a `mailto` in the User-Agent for the polite pool |
| Semantic Scholar | Abstract backfill where OpenAlex has none | Rate limited without a key; request one |
| arXiv | Recency in fast-moving fields | Preprints appear months before indexed versions |

### Ingestion model

Live query per search, with caching. Do not attempt to pre-ingest the corpus.

```
Search query
   ↓
Check Redis for cached result (TTL 24h)
   ↓ miss
Query OpenAlex works endpoint with the topic
   ↓
Normalise + dedup
   ↓
Persist works and stub researcher records
   ↓
Cache
```

When a user opens a researcher profile, fetch that researcher's full work list and persist it permanently. Viewed researchers become permanently cached; the rest are transient.

### Normalisation rules

1. Canonical ID is always the OpenAlex ID. Semantic Scholar and arXiv records are merged into an existing OpenAlex record by DOI, then by normalised title plus year.
2. OpenAlex stores abstracts as an inverted index. Reconstruct to plain text; if reconstruction yields fewer than 20 tokens, treat as absent and try Semantic Scholar.
3. Author position: `first` if index 0, `last` if index n-1 and n > 1, otherwise `middle`.
4. Country code comes from the institution, not the author. Missing institution means missing country — do not guess.
5. Store `source_hash` (SHA-256 of the raw response body) and `ingested_at` on every record.

### Deduplication

Order of precedence: DOI exact match → OpenAlex ID → normalised title (lowercase, punctuation stripped, whitespace collapsed) plus publication year within ±1. Preprint and published versions of the same work collapse to one record, keeping the published metadata and the preprint's earlier date.

### Failure handling

- HTTP 429: exponential backoff, three retries, then serve stale cache if available.
- HTTP 5xx: two retries, then fail the source and continue with the remaining sources. A search must not fail because arXiv is down.
- Malformed record: log, skip, increment a counter. Never crash a batch.

**Build steps.**
1. `services/ingestion/adapters/openalex.py` — a client with the polite pool header, pagination via cursor, and typed responses.
2. Test it standalone: fetch 50 works for one query, print titles.
3. `normalize.py` — raw response to `Work`.
4. Test: assert every required field populated, abstracts reconstructed correctly on a known sample.
5. `adapters/semantic_scholar.py` — abstract backfill only.
6. `adapters/arxiv.py` — recency supplement.
7. `dedup.py` — the precedence chain above.
8. Persistence layer with upsert on canonical ID.

**Tests.**
- Abstract reconstruction matches a known-good fixture exactly.
- Dedup collapses a preprint/published pair into one record.
- A simulated 429 triggers backoff and eventually succeeds.
- A simulated arXiv outage still returns OpenAlex results.
- Re-ingesting the same query twice produces no duplicate rows.

**Done when.** `python -m services.ingestion.cli --query "agentic AI radiology" --limit 200` persists 200 deduplicated works with populated abstracts for at least 70% of them.

**Failure modes to expect.** Elsevier-published works often have no abstract anywhere. Author IDs for common names are unreliable — see M4. Some institutions have no country code.

---

## 9. M2 — Chunking and indexing

**Purpose.** Make the corpus searchable by both meaning and exact terms.

**Depends on.** M1.

**Input.** `Work` records.

**Output.** Populated dense and lexical indexes with metadata filters.

### Chunking

Abstracts are short and self-contained. Do not over-engineer this.

- Abstract ≤ 400 tokens: one chunk, whole abstract.
- Abstract > 400 tokens: split on sentence boundaries into ~300-token chunks with 50-token overlap.
- Title is prepended to every chunk of that work — it carries strong topical signal.
- Full text is out of scope for v1, including for open-access works.

Each chunk stores: `work_id`, `chunk_index`, `text`, `embedding`, `tsvector`, and denormalised filter fields (`publication_year`, `country_codes`, `field`, `institution_ids`).

### Indexing

- **Dense.** pgvector, cosine distance, HNSW index. Embed with the configured model.
- **Lexical.** Postgres `tsvector` with `english` configuration, GIN index. This is what catches exact terms — "MRI", "U-Net", "DICOM", author surnames, venue names.
- **Filters.** B-tree indexes on `publication_year`, `field`. GIN on `country_codes` and `institution_ids` arrays.

Metadata filters must be applied **inside** the SQL query, not as a post-filter on results. Post-filtering silently shrinks the candidate set below the intended K.

**Build steps.**
1. `chunk.py` with the rules above. Test on 100 abstracts, inspect boundaries manually.
2. `embed.py` with batching and a configurable model. Test embedding dimensions and determinism.
3. `lexical.py` building `tsvector` on insert via a generated column.
4. Create HNSW and GIN indexes. Measure query latency before and after.
5. A single `index_works(works: list[Work])` entrypoint that does all three.

**Tests.**
- Chunk count matches expectation on a fixture set.
- Embedding dimension matches the configured model.
- A dense query for a paraphrased abstract returns the original in the top 5.
- A lexical query for a rare acronym returns the work containing it.
- Filtering by `country_codes = ["GB"]` returns only GB-affiliated works.
- Re-indexing the same work updates rather than duplicating.

**Done when.** 10,000 indexed chunks return dense results in under 100ms P95.

---

## 10. M3 — Topic → people search

**This is the core of the product. Build it before anything downstream.**

**Purpose.** Convert a topic query into a ranked list of the researchers who actually work on it.

**Depends on.** M0, M1, M2.

**Input.** `query: str`, `filters: SearchFilters`.

**Output.** `list[RankedResearcher]` with per-researcher matched papers as evidence.

### Pipeline

```
Query: "agentic AI in radiology"
   ↓
[1] Query preparation
       ↓
[2] Hybrid retrieval  →  ~500 candidate chunks
       ↓
[3] Cross-encoder rerank  →  top ~200 genuinely relevant works
       ↓
[4] Aggregate works → authors
       ↓
[5] Fetch each candidate author's total output counts
       ↓
[6] Field-normalised scoring
       ↓
[7] Apply filters
       ↓
Ranked researcher list
```

### [1] Query preparation

- Embed the raw query for dense retrieval.
- Build a `tsquery` for lexical retrieval.
- Optional LLM rewrite producing 2–3 alternative phrasings. **Benchmark this in NB03; keep only if recall improves on the held-out set.** Do not include it by default.

### [2] Hybrid retrieval

Run dense and lexical independently, then fuse with Reciprocal Rank Fusion.

```
RRF_score(d) = Σ  1 / (k + rank_i(d))        k = 60
```

Take top 250 from each, fuse, keep top 500 unique works. Dense handles "agentic AI" meaning autonomous LLM systems; lexical handles a user searching a specific method name or an author surname.

### [3] Reranking

Cross-encoder over `(query, title + abstract)` pairs for all 500 candidates. Keep works scoring above a threshold, capped at 200. The threshold is calibrated in NB04 — do not hardcode a guess.

The reranker score is retained; it feeds `MatchStrength` in step 6.

### [4] Aggregation

Group the surviving works by author. For each author collect: matched works, their reranker scores, their publication years, and the author's position on each.

Discard authors with only one matched work **unless** that work has an unusually high reranker score and the author is first or last. A single middle-author paper is not evidence of a research focus.

### [5] Author context

For each candidate author, fetch `works_count`, `first_publication_year`, `last_publication_year` and `primary_field`. Batch these — do not make one API call per author.

### [6] Scoring — field-normalised

Four components. **Every component is converted to a within-field percentile before weighting.** A raw count comparison across fields is invalid and is the single most likely way to make this product useless.

```
TopicCentrality = matched_works / total_works
    → What share of their career is this topic? A researcher with 3 of 4
      works matching outranks one with 5 of 400.
    → Percentile-normalised within field.

MatchStrength   = log(1 + Σ reranker_scores)
    → Raw relevance mass. Log-damped so volume cannot dominate.
    → Percentile-normalised within field.

Recency         = Σ (reranker_score × decay(year))
                  decay(year) = 0.5 ^ ((current_year - year) / half_life)
                  half_life = FieldStats.activity_threshold_years / 2
    → Field-relative. Four years of silence is dead in ML and normal
      in philosophy.

AuthorPosition  = weighted share of first/last authorships among matched works
                  first = 1.0, last = 1.0, middle = 0.3
    → DISABLED when FieldStats.authorship_convention == "alphabetical".
      Its 0.15 weight redistributes proportionally across the other three.
```

```
AuthorScore = 0.40 × TopicCentrality
            + 0.25 × MatchStrength
            + 0.20 × Recency
            + 0.15 × AuthorPosition
```

These weights are a starting hypothesis. Run sensitivity analysis in NB05 and record the result. Do not present a single number to the user — the UI shows the dimensions.

### [7] Filters

| Filter | Applied |
|---|---|
| Country | Institution country code, multi-select |
| Field | OpenAlex top-level field, multi-select |
| Active since | `last_publication_year >= X`, default = field-relative |
| Seniority | Minimum tier, ordering boost — **never removes results** |

Country and field filters are pushed into the SQL in step [2] so the candidate set is not silently starved.

**Build steps.**
1. `retrieve.py` — dense only. Notebook NB03: does it find known-relevant papers? Record Recall@50.
2. Add lexical. NB03: what does BM25 recover that dense missed?
3. Add RRF fusion. NB03: does fusion beat both? Record the number. **KEEP/REJECT.**
4. `rerank.py` — cross-encoder. NB04: nDCG@20 lift over hybrid alone. Calibrate the threshold. **KEEP/REJECT.**
5. `aggregate.py` — works to authors. NB05: inspect the raw grouped output for 10 queries.
6. Compute `FieldStats` across a sample of at least 5,000 authors per top-level field.
7. `score.py` — the four components with percentile normalisation. NB06: verify that a humanities query and an ML query both return sensible people.
8. Sensitivity analysis on the weights. Record which weights matter.

**Tests.**
- Ten hand-built queries where you know the correct top-5 researchers. At least 3 of 5 appear in the returned top 10 for each. **This is the acceptance test for the entire product.**
- A researcher with 3/4 topical works outranks one with 5/400.
- Disabling `AuthorPosition` for an alphabetical-convention field changes the ranking and the remaining weights still sum to 1.0.
- A country filter returns only that country and does not reduce the result count below the requested page size when enough candidates exist.
- An inactive researcher (last published 2015) ranks below an equivalent active one.

**Done when.** The ten-query benchmark passes and results return in under 3 seconds P95 on a warm cache.

**Failure modes to expect.** Author disambiguation errors will surface here as one person appearing twice or two people merged. Common surnames are the worst case. Log suspected duplicates (same display name, same institution, disjoint work sets) for manual review; do not attempt automatic merging in v1.

---

## 11. M4 — Researcher profile builder

**Purpose.** Turn a researcher's work list into the profile shown on their page.

**Depends on.** M1, M2.

**Input.** `researcher_id`.

**Output.** `Researcher` with populated `topics` and `seniority`.

### Research interests

Two sources, combined:

1. OpenAlex topic assignments, weighted by how many of the researcher's works carry each topic.
2. Clustering their abstract embeddings into 3–6 clusters and labelling each cluster with an LLM given the 5 nearest abstracts. Label only — the LLM never invents topics not present in the cluster.

Display the top 6, most recent first where scores tie. Show the year range each interest spans, because interests change.

### Seniority estimation

No data source carries an academic title. Estimate from signals, and be explicit that it is an estimate.

| Signal | Suggests senior |
|---|---|
| Last-author ratio > 0.4 (contribution-convention fields only) | Strong |
| Career span > 10 years | Moderate |
| Stable institution over 5+ years | Weak |
| Corresponding author frequently | Moderate |
| Works count above field 75th percentile | Weak |

Combine into `tier` and `confidence`. `verified` stays `false` until M5 confirms a title from a real profile page.

### Activity

`last_publication_year` compared against `FieldStats.activity_threshold_years`. Surface as a plain label: "Active", "Possibly inactive — last published 2019".

**Build steps.**
1. `topics.py` — OpenAlex topic aggregation. Test on 20 researchers you can verify by hand.
2. Add embedding clustering. Compare labels against the OpenAlex topics; keep clustering only if it adds interpretable detail.
3. `seniority.py` — the signal table above. Test against 30 researchers whose titles you look up manually. Record accuracy.
4. Activity computation.

**Tests.**
- Seniority estimation is at least 75% accurate on the 30-person manual set.
- Alphabetical-convention fields do not use the last-author signal.
- A researcher with no abstracts still produces a profile using OpenAlex topics alone.
- Interests reflect recent work, not a 20-year average.

**Done when.** A profile for any researcher in the corpus renders with interests, activity and a seniority estimate, in under 500ms from cache.

---

## 12. M5 — Enrichment and Position Agent

**Purpose.** Answer "does this person have a PhD or research position open?" and confirm their title.

**Depends on.** M4.

**Input.** `researcher_id`, name, institution.

**Output.** `PositionSignal`, and optionally `verified_title` and `profile_url` on the `Researcher`.

**This is the only agentic component in PhDForge.** It plans, uses tools, judges heterogeneous results, and recovers from failures.

### Why an agent and not a scraper

The target is not a known URL. It is "somewhere on this university's web estate, if it exists at all". The agent decides which sources to try, in what order, and when to stop, and it has to judge whether a retrieved page actually names this person.

### Sources, in order

1. **University profile page.** Search `"{name}" site:{institution_domain}`. Yields the title, lab page and often an explicit "I am recruiting" statement.
2. **Research group / lab page.** Usually linked from the profile.
3. **University vacancies page.** Filtered by the researcher's name.
4. **EURAXESS.** For EU/UK positions, has a usable search.
5. **Targeted web search.** `"{name}" "{institution}" (PhD OR studentship OR vacancy OR "research assistant")`.

### Agent loop

```
Plan: which sources apply given country and institution?
   ↓
For each source, bounded by max 8 fetches total:
   fetch → parse → judge
   ↓
Judge: does this page name THIS researcher AND describe an open position?
   Return: tier contribution + evidence snippet + URL
   ↓
Stop early if a Confirmed listing is found
   ↓
Assemble PositionSignal
```

### Judging rules

- A page naming the researcher with a position, deadline or application link → `confirmed`.
- A lab or profile page stating openness to applicants, with no specific listing → `likely`.
- A generic university PhD page that does not name the researcher → **ignore**. This is the most common false positive.
- Nothing → `none`.

Every tier above `none` must carry at least one `PositionEvidence` with a real URL and a verbatim snippet. No evidence means no claim.

### Prompt injection defence

Fetched pages are untrusted. Pass page content to the judging LLM inside a clearly delimited data block with an instruction that content inside the block is data only. Test with a page containing an injected instruction — see M11.

### Execution and caching

Runs asynchronously. The profile page renders immediately and the position card fills in when the job completes. Cache for 7 days (`expires_at`). Cap at 8 fetches and 60 seconds per run. On timeout, return `none` with a `checked_at` so the UI can say when it last looked.

**Build steps.**
1. `sources.py` — one fetcher per source, each independently testable.
2. Test each fetcher against 5 known researchers with known outcomes.
3. `judge.py` — the LLM judging step with typed output. Test against hand-labelled pages including the generic-university-page false positive.
4. `agent.py` — the loop, budgets, early stop, error handling.
5. Wire to the async queue with a 7-day cache.

**Tests.**
- A researcher with a known live listing returns `confirmed` with the correct URL.
- A researcher with no listing returns `none`, never a fabricated tier.
- A generic university PhD admissions page does not produce `confirmed`.
- An injected instruction in a fetched page does not change the agent's behaviour.
- The fetch budget is respected; a slow source does not hang the run.
- A cached signal within 7 days does not re-run the agent.

**Done when.** Across 20 researchers with manually verified ground truth, the agent achieves zero false `confirmed` results. False negatives are acceptable; false positives are not.

---

## 13. M6 — Professor Chat

**Purpose.** Let the user interrogate a researcher's body of work, assess their own fit, and prepare for an interview.

**Depends on.** M2, M4, M7 (for fit and interview modes).

**Input.** `researcher_id`, `mode`, message history, user message.

**Output.** `ChatMessage` with citations.

### Design principle

Their corpus does not fit in context and stuffing it would be wasteful and worse. Chat is RAG scoped to one researcher.

```
User message
   ↓
Retrieve from THIS researcher's works only (hard filter on researcher_id)
   ↓
Assemble context:
   ├── Profile summary          always included, it is small
   ├── Retrieved abstracts       top 8 after reranking
   ├── Position signal           if present
   └── User CV evidence          fit and interview modes only
   ↓
Mode-specific system prompt
   ↓
Answer with inline citations
```

### Modes

| Mode | Behaviour |
|---|---|
| **Explain** | Answers about their research. Cites papers. Says "I don't have that" rather than guessing |
| **Fit** | Compares user evidence against their work. **Must state gaps honestly.** Overlap and mismatch both, never flattery |
| **Interview** | Simulates the researcher asking questions grounded in their actual papers. One question at a time, follows up on the answer |

### The framing rule, non-negotiable

The system never claims to know what the researcher thinks. Every mode operates as an evidence-grounded approximation from public work, and the UI states this on the chat screen. Interview mode in particular must be labelled as a simulation.

### Fit mode honesty

Fit mode exists to be useful, not encouraging. It must name missing skills, methodological mismatches and experience gaps explicitly. A fit assessment that only lists overlaps is a broken fit assessment.

**Build steps.**
1. `retrieval.py` — scoped retrieval with a hard `researcher_id` filter. Test that no other researcher's work can leak in.
2. `modes.py` — three versioned system prompts in `packages/prompts/`.
3. `session.py` — history persistence and context window management.
4. Citation extraction and validation: every cited work ID must exist in the retrieved set.

**Tests.**
- A question about an unrelated field returns "I don't have evidence of that in their work" rather than a general answer.
- No citation references a work outside the retrieved context.
- No work from another researcher appears in retrieval.
- Fit mode on a deliberately poor match produces explicit gaps.
- Interview mode asks one question per turn and follows up on the previous answer.

**Done when.** All three modes work on a researcher with 40+ indexed works, with every factual claim carrying a valid citation.

---

## 14. M7 — CV ingestion

**Purpose.** Build the private evidence base that powers fit assessment and SOP generation.

**Depends on.** M0.

**Input.** Uploaded PDF or DOCX.

**Output.** `EvidenceItem[]` with full provenance.

### Pipeline

```
Upload → MIME validation → text extraction → section detection
       → section-aware chunking → LLM evidence extraction
       → provenance record → storage
```

- **Extraction.** PyMuPDF for PDF, python-docx for DOCX. Preserve page numbers.
- **Section detection.** Rule-based. ALL-CAPS lines and known heading patterns (Education, Experience, Publications, Skills, Projects). Fall back to whole-document chunking if fewer than two sections are detected.
- **Evidence extraction.** LLM with structured output, one section at a time. The prompt must forbid inference — only what the text states.
- **Provenance.** Every item stores `source_document_id`, `page`, `section` and a document hash.

### The verified/inferred boundary

`verified_by_user` defaults to `false`. An extracted item is a model's reading of the document, not a fact. The UI lets the user confirm or correct each item. **An inferred skill never becomes a verified skill automatically.** SOP generation treats unverified items as weaker support.

### Tenant isolation

Documents and evidence items are owned by one applicant. Every query filters by `applicant_id` at the repository layer, not the route layer.

**Build steps.**
1. `parse.py` — extraction with page tracking. Test on 5 varied CVs.
2. `sections.py` — rule-based detection. Test against hand-labelled section boundaries.
3. `evidence.py` — LLM extraction with typed output.
4. Measure hallucination rate: for 100 extracted items across 10 CVs, how many state something not in the source text? **Target zero.**

**Tests.**
- Every evidence item's text is traceable to its cited page and section.
- A CV with unusual formatting still produces evidence, via fallback chunking.
- Applicant A cannot retrieve applicant B's evidence through any endpoint.
- Re-uploading the same document creates a new version, not duplicates.
- Hallucination rate on the 100-item sample is zero.

**Done when.** A real CV produces a correct, fully traceable evidence list with zero fabricated items.

---

## 15. M8 — SOP engine

**Purpose.** Draft a Statement of Purpose grounded in both the user's verified evidence and the researcher's actual work.

**Depends on.** M4, M6, M7. M5 optionally, for the specific position.

**Input.** `applicant_id`, `researcher_id`, optional `position_id`.

**Output.** `SOPDraft` with a `GroundingReport`.

### Pipeline

```
CV evidence + Researcher profile + Their specific papers + Position (if confirmed)
        ↓
    Writer  →  sectioned draft with claims tagged by subject
        ↓
    Grounding gate (four checks)
        ↓
    ├── passed → draft returned
    └── failed → flagged claims returned with the draft, marked in the UI
```

### Writer

Produces sections: opening, research background, fit with their work, proposed direction, closing. Every sentence making a factual claim is tagged `applicant`, `researcher` or `general`.

The writer must not produce a claim about the applicant that no evidence item supports. If it lacks material for a section, it produces a shorter section — never invented content.

### Grounding gate — four checks

| Check | Fails when |
|---|---|
| **Unsupported applicant claim** | A claim tagged `applicant` maps to no `EvidenceItem` |
| **Unsupported researcher claim** | A claim tagged `researcher` maps to no work or profile source |
| **Generic motivation** | A passage would be true of any applicant to any supervisor |
| **Supervisor mismatch** | The draft attributes research to them that their corpus does not support |

Checks 1 and 2 run by retrieval: take the claim, retrieve against the relevant corpus, score support, classify `supported` / `weak` / `unsupported`. Checks 3 and 4 are LLM judgements with typed output.

**Unsupported claims are never silently removed and never silently kept.** They surface in the UI marked, for the user to fix or delete.

### The user is the author

Every section is editable. Every claim's evidence is inspectable. The system drafts; the applicant decides.

**Build steps.**
1. `writer.py` — prompt producing sections with tagged claims.
2. `grounding.py` — checks 1 and 2 via retrieval scoring.
3. Add checks 3 and 4.
4. Build a deliberately flawed draft set with planted unsupported claims. Measure detection rate.

**Tests.**
- A planted unsupported applicant claim is caught. Target: 100% on the planted set.
- A planted mis-attribution of research is caught.
- A draft generated for an applicant with thin evidence produces shorter sections, not invented ones.
- Every `Claim` in the output has a `support` value and, where supported, real evidence IDs.
- Regenerating produces a new version; prior versions remain retrievable.

**Done when.** Every planted error in the test set is caught, and no clean draft is falsely flagged more than 10% of the time.

---

## 16. M9 — Backend

**Purpose.** Expose everything above as the API the frontend consumes.

**Depends on.** M1–M8.

### Structure

- FastAPI with routers per domain: `search`, `researchers`, `chat`, `profile`, `sop`, `runs`.
- Pydantic request and response models — the same schemas from §6, no parallel DTOs.
- Auth: OAuth/OIDC. Every applicant-owned resource checks ownership in the repository layer.
- Async: Redis-backed queue. Position Agent and SOP generation return a `run_id` immediately.
- Cache: Redis. Search results 24h, researcher profiles 7d, position signals 7d.
- Rate limits per user on search and chat.
- Structured JSON logging with a `trace_id` per request, propagated to workers.

### Observability

Every request logs: `trace_id`, endpoint, latency, and for AI paths the model, token counts and cost. Every search logs retrieval counts at each pipeline stage — this is how you debug a bad ranking without guessing.

**Tests.**
- Every applicant-owned endpoint rejects a request from another applicant.
- A long-running job survives a client disconnect and is retrievable by `run_id`.
- Rate limits return 429 with a retry hint.
- Cache hit and miss both produce identical response shapes.

**Done when.** The full API in §20 is implemented, documented via OpenAPI, and every endpoint has an integration test.

---

## 17. M11 — Evaluation

**Purpose.** Prove the system works rather than asserting it.

Build the evaluation set **before** optimising anything.

### Evaluation sets

1. **Ranking set.** 30 topic queries across at least 8 fields, each with 5 manually verified correct researchers. This is the product's acceptance test.
2. **Retrieval set.** 150 query/relevant-work pairs for Recall@K, MRR and nDCG.
3. **Seniority set.** 30 researchers with manually looked-up titles.
4. **Position set.** 20 researchers with manually verified position status.
5. **Grounding set.** 20 SOP drafts with planted unsupported claims.
6. **Injection set.** 10 fetched pages containing injected instructions.

### Metrics

| Area | Metric | Target |
|---|---|---|
| Retrieval | Recall@50 | Establish baseline, then improve |
| Retrieval | nDCG@20 after reranking | Measurable lift over hybrid alone |
| Ranking | Top-5 hit rate on the ranking set | ≥ 3 of 5 in top 10 |
| Seniority | Accuracy | ≥ 75% |
| Position | False `confirmed` rate | 0% |
| CV extraction | Hallucination rate | 0% |
| Grounding | Planted error detection | 100% |
| System | Search P95 latency | < 3s warm |

### Ablation, mandatory

```
A: dense only
B: lexical only
C: hybrid (RRF)
D: hybrid + reranker
E: hybrid + reranker + query rewriting
```

Record the number for each. Each optional technique gets an explicit **KEEP / REJECT / INVESTIGATE** verdict with the evidence. "Because it's modern RAG" is not a reason to ship something.

---

## 18. M12 — Deployment

Progression: local → Docker Compose → Cloud Run + managed Postgres → separate API and worker services → monitoring.

- Docker images for API and worker.
- Managed Postgres with pgvector. Backups configured.
- Managed Redis.
- Secrets via the platform's secret manager. Never in the image, never in git.
- GitHub Actions: lint, type-check, test, build, deploy on merge to main.

**Load tests.** 10 concurrent searches. Concurrent CV uploads. Position Agent runs under concurrency. Cache on versus off. Database pool saturation.

---

## 19. Build order

```
PHASE 1 — PROVE THE CORE
  M0 → M1 → M2 → M3
  NB01–NB06, ablation, ranking benchmark
  Gate: the ten-query ranking benchmark passes.
        If it does not, nothing downstream is worth building.

PHASE 2 — PROFILES
  M4 → M5

PHASE 3 — USER LAYER
  M7 → M6 → M8

PHASE 4 — PRODUCT
  M9 → M10 → M12

PHASE 5 — PROOF
  M11 full evaluation, ablation report, case study
```

Do not build the UI first. Do not build chat before search ranks correctly. Do not add query rewriting without the experiment.

---

## 20. API contract

**This section is the contract handed to the frontend generator. The frontend is built against these shapes with mocked responses, in parallel with the backend.**

### `POST /api/search`

```json
// request
{
  "query": "agentic AI in radiology",
  "filters": {
    "countries": ["GB", "US"],
    "fields": ["Computer Science", "Medicine"],
    "active_since": 2021,
    "min_seniority": "mid"
  },
  "page": 1,
  "page_size": 20
}
```

```json
// response
{
  "query": "agentic AI in radiology",
  "total": 143,
  "page": 1,
  "results": [
    {
      "researcher_id": "A5023888391",
      "display_name": "Jane Okafor",
      "institution": {
        "display_name": "University of Edinburgh",
        "country_code": "GB"
      },
      "primary_field": "Computer Science",
      "seniority": {
        "tier": "senior",
        "confidence": 0.81,
        "verified": false,
        "verified_title": null
      },
      "score": 0.87,
      "score_breakdown": {
        "topic_centrality": 0.92,
        "match_strength": 0.78,
        "recency": 0.95,
        "author_position": 0.80
      },
      "matched_works_count": 11,
      "total_works_count": 34,
      "last_publication_year": 2026,
      "top_interests": ["Medical imaging", "LLM agents", "Clinical decision support"],
      "matched_works_preview": [
        {
          "work_id": "W4390112233",
          "title": "Autonomous agents for radiology report generation",
          "year": 2026
        }
      ]
    }
  ]
}
```

### `GET /api/researchers/{id}`

```json
{
  "id": "A5023888391",
  "display_name": "Jane Okafor",
  "orcid": "0000-0002-1825-0097",
  "institution": {
    "display_name": "University of Edinburgh",
    "country_code": "GB",
    "ror": "https://ror.org/01nrxwf90"
  },
  "primary_field": "Computer Science",
  "profile_url": "https://www.ed.ac.uk/profile/jokafor",
  "works_count": 34,
  "cited_by_count": 1204,
  "h_index": 18,
  "first_publication_year": 2012,
  "last_publication_year": 2026,
  "activity_status": "active",
  "seniority": {
    "tier": "senior",
    "confidence": 0.81,
    "verified": true,
    "verified_title": "Reader in Medical AI",
    "signals": ["last_author_ratio=0.58", "career_span=14y"]
  },
  "interests": [
    { "name": "Medical imaging", "score": 0.41, "year_range": [2014, 2026] },
    { "name": "LLM agents", "score": 0.29, "year_range": [2023, 2026] }
  ]
}
```

### `GET /api/researchers/{id}/works?page=1&page_size=20&sort=year_desc`

```json
{
  "total": 34,
  "page": 1,
  "results": [
    {
      "id": "W4390112233",
      "title": "Autonomous agents for radiology report generation",
      "abstract": "We present a multi-step agent that...",
      "publication_year": 2026,
      "venue": "MICCAI",
      "doi": "10.1007/xxxxx",
      "cited_by_count": 7,
      "is_open_access": true,
      "open_access_url": "https://arxiv.org/abs/xxxx.xxxxx",
      "author_position": "last"
    }
  ]
}
```

### `GET /api/researchers/{id}/position`

Returns `202` with `{"status": "pending", "run_id": "..."}` while the agent runs.

```json
// 200
{
  "researcher_id": "A5023888391",
  "tier": "confirmed",
  "deadline": "2027-01-12",
  "funding_note": "Fully funded, home and international",
  "evidence": [
    {
      "type": "university_listing",
      "url": "https://www.ed.ac.uk/phd/agentic-radiology-2027",
      "snippet": "Supervisor: Dr Jane Okafor. Applications close 12 January.",
      "fetched_at": "2026-09-14T09:12:00Z"
    }
  ],
  "checked_at": "2026-09-14T09:12:00Z",
  "expires_at": "2026-09-21T09:12:00Z"
}
```

```json
// 200, nothing found — note the wording
{
  "researcher_id": "A5023888391",
  "tier": "none",
  "evidence": [],
  "checked_at": "2026-09-14T09:12:00Z",
  "expires_at": "2026-09-21T09:12:00Z"
}
```

### `POST /api/chat/sessions`

```json
// request
{ "researcher_id": "A5023888391", "mode": "fit" }
// response
{ "session_id": "cs_01H...", "mode": "fit", "researcher_id": "A5023888391" }
```

### `POST /api/chat/sessions/{id}/messages`

```json
// request
{ "content": "Would my speech-AI background fit their work?" }
```

Streams tokens over SSE, then a final message object:

```json
{
  "id": "msg_01H...",
  "role": "assistant",
  "content": "Your speech-processing work overlaps with...",
  "citations": [
    {
      "work_id": "W4390112233",
      "title": "Autonomous agents for radiology report generation",
      "year": 2026,
      "url": "https://arxiv.org/abs/xxxx.xxxxx",
      "source_type": "paper"
    }
  ]
}
```

### `POST /api/profile/documents`

Multipart upload. Returns `{ "document_id": "...", "status": "processing", "run_id": "..." }`.

### `GET /api/profile/evidence`

```json
{
  "items": [
    {
      "id": "ev_01H...",
      "text": "Built a speech-based depression detection pipeline using Whisper",
      "type": "project",
      "source_document_id": "doc_01H...",
      "page": 2,
      "section": "Projects",
      "confidence": 0.94,
      "verified_by_user": false
    }
  ]
}
```

### `PATCH /api/profile/evidence/{id}`

```json
{ "verified_by_user": true, "text": "corrected text" }
```

### `POST /api/sop/draft`

```json
// request
{ "researcher_id": "A5023888391", "position_id": null }
// response
{ "run_id": "run_01H...", "status": "queued" }
```

### `GET /api/sop/{id}`

```json
{
  "id": "sop_01H...",
  "researcher_id": "A5023888391",
  "version": 1,
  "sections": {
    "opening": "...",
    "research_background": "...",
    "fit": "...",
    "proposed_direction": "...",
    "closing": "..."
  },
  "claims": [
    {
      "text": "I built a speech-based depression detection pipeline",
      "subject": "applicant",
      "evidence_ids": ["ev_01H..."],
      "support": "supported"
    }
  ],
  "grounding": {
    "unsupported_applicant_claims": [],
    "unsupported_researcher_claims": [],
    "generic_motivation_flags": ["The closing paragraph is generic"],
    "mismatch_flags": [],
    "passed": true
  }
}
```

### `GET /api/runs/{run_id}`

```json
{ "run_id": "run_01H...", "status": "running", "progress": 0.6, "error": null }
```

### Error shape, all endpoints

```json
{ "error": { "code": "RATE_LIMITED", "message": "...", "retry_after": 30 } }
```

---

## 21. UI specification

**The frontend is generated externally (Lovable, v0 or similar) against §20 with mocked responses, then integrated.** It must not invent its own backend, its own data shapes or its own persistence layer. Presentation only.

### Design direction

References: Linear, Elicit, Semantic Scholar. Restrained and typography-led. Academic credibility comes from looking calm and precise, not from looking like an AI product.

- **Type.** Serif for researcher names and paper titles. Clean sans for interface text. This one choice does most of the work of making it feel scholarly rather than generic SaaS.
- **Colour.** Near-white background, near-black text, one accent colour used sparingly for interactive elements and the position badge. No gradients.
- **Space.** Generous. Dense where density helps (result lists, publication lists), airy where it does not (profile header, chat).
- **Depth.** Borders and background tints, not drop shadows on everything.
- **Motion.** Minimal. Loading skeletons, not spinners.

### Screens

**1. Search.** A single centred input. Example queries below it to show the intended narrowness of the query. Nothing else.

**2. Results.** Left filter rail: country (multi-select with search), field, active since, seniority. Main column: researcher rows showing name, institution with country flag, top 3 interests, matched/total works, activity year, and the score shown as its four dimensions — never as one number alone.

**3. Researcher profile.**
- Header: name, title if verified, institution, country, activity status.
- Position card, prominent: Confirmed (accent, with deadline and link) / Likely (muted, with link) / **"No listing found"** (grey). Never "not recruiting". Shows when it was last checked. Renders in a loading state while the agent runs.
- Research interests as chips with year ranges.
- Publications list: year, title, abstract expandable, venue, link.
- Two actions: **Chat** and **Draft SOP**.

**4. Chat.** Mode selector (Explain / Fit / Interview). Messages with inline citations that open the cited paper. A persistent, quiet note that responses are grounded in public work and are not the researcher's own words. Interview mode labelled as a simulation.

**5. SOP workspace.** Sections editable inline. An evidence panel on the right: clicking a claim highlights its supporting evidence. Unsupported claims visibly marked. Version history.

**6. Your profile.** Uploaded documents. Extracted evidence items, each confirmable, editable or deletable. Unverified items visibly distinct from verified ones.

### Required states

Every list has an empty state, a loading skeleton and an error state. The position card has a fourth: checking. Thin researcher profiles (no abstracts) must degrade gracefully and say what is missing rather than rendering blank space.

---

## 22. Definition of done

- [ ] Ten-query ranking benchmark passes: ≥3 of 5 known researchers in the top 10, across at least 8 fields
- [ ] Retrieval ablation A–E recorded, with a KEEP/REJECT verdict per technique
- [ ] Reranker shows measurable nDCG lift over hybrid alone
- [ ] All ranking scores are field-normalised percentiles
- [ ] Alphabetical-convention fields do not use the author-position signal
- [ ] Seniority estimation ≥75% accurate on the manual set
- [ ] Position Agent: zero false `confirmed` across the 20-researcher set
- [ ] Position Agent resists injected instructions in fetched pages
- [ ] "No listing found" never rendered as "not recruiting"
- [ ] CV evidence extraction: zero hallucinated items on the 100-item sample
- [ ] Chat citations always resolve to works in the retrieved context
- [ ] Chat cannot retrieve another researcher's work
- [ ] Fit mode states gaps, not only overlaps
- [ ] SOP grounding gate catches 100% of planted errors
- [ ] Tenant isolation verified: no cross-applicant access on any endpoint
- [ ] Search P95 under 3s warm
- [ ] Long-running jobs survive client disconnect
- [ ] Cost and latency logged per AI call
- [ ] Deployment reproducible from a clean clone
- [ ] Load tests run and recorded
