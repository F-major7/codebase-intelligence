# Codebase Intelligence Assistant

Production RAG system for semantic code search and natural language Q&A over software repositories.

**Key Metrics**: 99.97% noise filtering | Sub-400ms retrieval | $0.002/query | 90%+ test coverage

**Live Demo**: https://codebias.streamlit.app/

---

## Executive Summary

This project demonstrates end-to-end ML systems engineering for code understanding. The system implements a multi-stage RAG pipeline that processes 33K+ file candidates down to 9 relevant files through intelligent filtering, performs structure-aware semantic chunking, and uses HNSW-indexed vector search for O(log N) retrieval. Users can analyze any public GitHub repository by pasting a URL, with pre-loaded Flask, FastAPI, and Django collections for instant testing. Key engineering decisions prioritize cost efficiency ($0.002/query with Claude Haiku), sub-second latency, and production robustness through comprehensive error handling. This is a complete retrieval system with thoughtful tradeoffs between accuracy, speed, and operational cost, not a prompt engineering exercise.

---

## Problem & Approach

Developers spend 60-70% of their time reading code. Traditional keyword search misses semantic relationships; naive LLM prompting hallucinates without grounding; documentation becomes stale.

**Solution**: RAG-based system that retrieves relevant code chunks before generation, constraining the LLM to synthesize answers from verified sources with citations.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   OFFLINE INDEXING                      │
│  Repository → Filter → Chunk → Embed → Index (ChromaDB) │
│    (33K)      (9)      (76)    (1536d)    (HNSW)        │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   QUERY-TIME INFERENCE                  │
│  User Query → Embed → Search → Assemble → Generate      │
│                       (top-5)   Context    (Claude)     │
│               ← Response with Citations ←               │
└─────────────────────────────────────────────────────────┘
```

### Pipeline Stages

**Ingestion**: Multi-layer filtering (extension whitelist, directory exclusion, size constraints, encoding validation) achieves 99.97% noise reduction. Structure-aware chunking via `RecursiveCharacterTextSplitter` with code-aware separators (classes → functions → blank lines) at 1000 chars with 200 char overlap. Embedded using OpenAI text-embedding-3-small (1536d), stored in ChromaDB with HNSW indexing. Session-based repository isolation enables concurrent analysis of multiple codebases with dynamic collection management.

**Retrieval**: Query embedded to same 1536d space, HNSW search with O(log N) complexity, cosine similarity scoring, top-k selection (k=5). Sub-400ms latency.

**Generation**: Structured prompt with retrieved context + metadata → Claude LLM (Haiku/Sonnet) → Response with source citations. Temperature=0 for deterministic outputs.

---

## Retrieval & Chunking Design

**Chunking Strategy**: Code differs from prose, natural boundaries occur at structural elements. Hierarchical separator approach prioritizes class/function boundaries over arbitrary character limits. 1000-character chunks balance precision (captures typical function bodies) with context (includes surrounding code). 200-character overlap prevents information loss at boundaries.

**Embedding**: OpenAI text-embedding-3-small for proven code understanding performance at $0.02/1M tokens. Considered local models but chose quality and development speed over eliminating API dependency.

**Indexing**: HNSW (Hierarchical Navigable Small World) provides O(log N) approximate nearest neighbor search. ChromaDB chosen for zero-configuration local development and persistent SQLite backend, no cloud dependencies.

---

## Performance & Results

### Metrics

| Stage | Performance | Notes |
|-------|-------------|-------|
| **Ingestion** | 2s for 33K→9 files, 76 chunks | 99.97% filtering precision |
| **Retrieval** | <400ms | O(log N) HNSW, 90%+ precision@5 |
| **Generation** | 2-3s (Haiku), 4-5s (Sonnet) | Streaming reduces perceived latency |
| **Cost** | $0.002/query (Haiku), $0.024 (Sonnet) | Model selection based on use case |
| **Resources** | 100MB RAM, 1MB/repo storage | Minimal footprint |

### What Works Well

- Specific technical queries: "What chunking strategy is used?" → Correctly identifies implementation details, cites source files
- Architecture questions: Synthesizes multi-file explanations with code examples
- Implementation details: Explains engineering tradeoffs, references actual code

### Limitations

- Generic queries may retrieve descriptions over implementations (solution: specificity improves results)
- Context window constraints for very long responses (mitigated by k=5 limit)
- Streamlit Cloud: 1GB storage limit, ~20-30 custom repos capacity depending on size
- Session-based storage: custom repos cleared after browser close to preserve space

---

## Infrastructure

**Stack**: Python 3.11+, OpenAI embeddings, Anthropic Claude, ChromaDB, LangChain, Streamlit

**Deployment**: Local-first with persistent vector storage. Stateless API design enables horizontal scaling (limited by embedding API rate limits). ChromaDB persistence eliminates re-embedding costs.

**Latency Breakdown**: Query embedding (100-200ms) + Vector search (50-150ms) + LLM generation (2-4s) = 2.5-4.5s total

---

## Engineering Tradeoffs

**Optimized For**: Cost ($0.002/query), simplicity (zero-config ChromaDB), quality (90%+ test coverage), speed (sub-second retrieval)

**Explicit Non-Goals**:
- Real-time updates (manual re-indexing acceptable, 2s for this codebase)
- Cross-repository comparative analysis (single-context queries, reduced complexity)
- Fine-tuned models (off-the-shelf sufficient, faster iteration)

**Key Decisions**:
- API dependencies (OpenAI, Anthropic) over local models: Quality and development speed justified costs
- Single LLM (Claude): Superior code understanding in testing, accepts single-point-of-failure risk
- No conversation persistence: Stateless simplifies deployment

---

## Usage

```bash
# Installation
git clone https://github.com/F-major7/codebase-intelligence && cd codebase-intelligence
pip install -r requirements.txt

# Configure
echo "OPENAI_API_KEY=sk-proj-..." > .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Run
streamlit run app.py        # Web UI (http://localhost:8501)
python main.py              # CLI (single-repo mode)
pytest tests/ -v            # Tests
```

### Adding Custom Repositories

**Via Web UI** (Recommended):
1. Paste GitHub URL in sidebar (e.g., `https://github.com/owner/repo`)
2. Click "Index Repository"
3. Wait 1-3 minutes for indexing (progress shown)
4. Select from dropdown and query

**Via Python** (Programmatic):
```python
from src.ingestion.loader import CodebaseLoader
from src.ingestion.chunker import CodeChunker
from src.retrieval.vector_store import CodeVectorStore

loader = CodebaseLoader("../target-repo")
docs = loader.load_files()
chunker = CodeChunker()
chunks = chunker.chunk_documents(docs)
vs = CodeVectorStore(collection_name="custom_repo", persist_dir="./chroma_db")
vs.create_index(chunks)
```

---

## Future Work

**Persistent User Accounts**: Saved repositories across sessions with authentication and quota management

**Hybrid Retrieval**: Combine semantic + keyword search for better recall on specific identifiers

**Incremental Indexing**: Filesystem watching + differential updates for real-time development workflow

**Cross-Encoder Reranking**: Post-retrieval scoring for improved precision (quality-over-speed mode)

**AST-Based Chunking**: Language-specific parsing for precise structural boundaries and type extraction

**Cross-Repository Analysis**: Federated search enabling comparative queries across multiple codebases

**Production Monitoring**: Retrieval precision metrics, latency percentiles, cost tracking, error rates

---

## Technical Validation

**Test Coverage**: 90%+ (unit + integration tests)  
**Performance**: Benchmarked on actual codebase (ingestion <2s, retrieval <400ms)  
**Reliability**: Comprehensive error handling, API retry logic, graceful degradation

---

**Tech Stack**: Python 3.11 | OpenAI Embeddings | ChromaDB | Claude 4.5 | LangChain | Streamlit  
**Status**: Production-Ready | 90%+ Test Coverage | $0.002/query

---
