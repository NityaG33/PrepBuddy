# PrepBuddy Roadmap

## Vision

PrepBuddy is a production-grade, PDF-based RAG study assistant. Users upload
documents, ask grounded questions, and eventually receive personalized study
materials through controlled AI workflows.

## Development principles

1. Build strong, measurable foundations before introducing agents.
2. Preserve working functionality through incremental changes.
3. Keep the modular monolith maintainable and independently testable.
4. Treat continuous testing, evaluation, security, and observability as work
   that spans every phase, with focused unit and integration gates for changes.
5. Use LangChain and LangGraph only where they provide clear value.

## Phase 1 — Foundation

FastAPI and React, workspaces, SQLite/SQLAlchemy persistence, PDF upload and
deletion, FAISS, Gemini, and a basic RAG chat flow.

## Phase 2 — Document Processing

Processor abstraction, PyMuPDF raw extraction, normalization, page/layout
metadata, paragraph/heading/list reconstruction, and explicit handling for
invalid, password-protected, empty-text, oversized, and over-limit PDFs.

Phase 2 includes early upload security: bounded streaming uploads, extension
and PDF-signature validation, page/text limits, and documented extraction
limitations. OCR remains out of scope.

The current limits are configured through `backend/.env`:

```dotenv
MAX_PDF_UPLOAD_BYTES=20971520
UPLOAD_READ_CHUNK_BYTES=1048576
MAX_PDF_PAGE_COUNT=500
MAX_EXTRACTED_TEXT_CHARS=5000000
```

## Phase 3 — Intelligent Chunking and Indexing

Introduce explicit data contracts before changing chunking:

`RawDocument -> NormalizedDocument -> Chunk -> RetrievalResult`

Define and validate these versioned contracts before Phase 3 implementation.
Then add structure-aware, token-aware chunking with heading context and rich
metadata. Establish a document lifecycle covering content hashes,
processor/chunker/embedding versions, processing states, reprocessing, and
idempotent document-to-vector updates for duplicate detection and safe
re-indexing. Keep source-file and index versions traceable so failed updates
do not silently replace a working indexed version.

## Phase 4 — Retrieval and Grounded RAG

Evaluate chunk sizes, embedding models, filtering, top-k, thresholds, hybrid
search, reranking, query rewriting, context assembly, and page-level
citations. Measure Recall@K, Precision@K, MRR, faithfulness, and citation
correctness using a versioned evaluation dataset.

## Phase 5 — Selective LangChain Integration

Use LangChain only for helpful integrations: provider adapters, prompt
templates, structured outputs, retriever abstractions, tools, and reusable AI
chains. Existing application services are not replaced merely to use a
framework.

## Phase 6 — LangGraph and Controlled Agents

Add stateful, bounded workflows such as intent routing, adaptive retrieval,
evidence evaluation, query refinement, answer generation, and citation
validation. Agents use explicit tools, iteration limits, permissions, and
human review where appropriate.

## Phase 7 — Study Intelligence

Document summaries, explanations at several levels, flashcards, MCQs, quizzes,
interview questions, progress tracking, weak-topic detection, adaptive
revision, and study-plan generation.

## Phase 8 — Reliability, Security, and Infrastructure

PostgreSQL/Alembic, background jobs, retries and idempotency, structured
logging, monitoring, health checks, rate limiting, caching, authentication,
authorization, workspace ownership, safe vector updates, backups, secrets,
prompt-injection protection, and model/agent limits.

## Phase 9 — Testing, Evaluation, and Deployment

Maintain continuous unit, integration, API, RAG, agent, and regression tests;
add performance and load tests as service limits and deployment targets are
defined. Dockerize the application, add CI/CD and cloud deployment, then
operate it with production-grade observability, alerting, backups, recovery,
and documented operational procedures.
