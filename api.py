"""FastAPI wrapper around the codebase RAG pipeline."""

import os
import re
import shutil
import threading
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

from src.ingestion.loader import CodebaseLoader
from src.ingestion.chunker import CodeChunker
from src.retrieval.vector_store import CodeVectorStore
from src.generation.qa_chain import CodeQAChain

app = FastAPI(title="Codebase Intelligence API")


# ── Auto-seed on startup ───────────────────────────────────────────────────
SEED_REPOS = [
    ("flask",   "https://github.com/pallets/flask"),
    ("fastapi", "https://github.com/tiangolo/fastapi"),
    ("django",  "https://github.com/django/django"),
]
PERSIST_DIR = "./chroma_db"


def _seed():
    """Index pre-loaded repos if not already present. Runs in background thread."""
    import chromadb
    try:
        existing = {c.name for c in chromadb.PersistentClient(PERSIST_DIR).list_collections()}
    except Exception:
        existing = set()

    for name, url in SEED_REPOS:
        if name in existing:
            print(f"[seed] {name} already indexed — skipping")
            continue
        print(f"[seed] Indexing {name} from {url} …")
        try:
            clone_path = f"/tmp/{name}_seed"
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            loader = CodebaseLoader(clone_path)
            loader.clone_repo(url, clone_path)
            docs = loader.load_files()
            chunks = CodeChunker().chunk_documents(docs)
            vs = CodeVectorStore(collection_name=name, persist_dir=PERSIST_DIR)
            vs.create_index(chunks)
            print(f"[seed] ✓ {name}: {len(docs)} files, {len(chunks)} chunks")
        except Exception as e:
            print(f"[seed] ✗ {name} failed: {e}")


@app.on_event("startup")
async def startup_event():
    """Kick off seeding in a background thread so the server starts immediately."""
    threading.Thread(target=_seed, daemon=True).start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    repo: str
    question: str


class IndexRequest(BaseModel):
    github_url: str


@app.post("/query")
async def query(body: QueryRequest):
    try:
        vs = CodeVectorStore(collection_name=body.repo, persist_dir="./chroma_db")
        vs.load_index()
        stats = vs.get_stats()
        results = vs.search(body.question, k=5)
        qa = CodeQAChain()
        result = qa.ask(body.question, results)
        return {
            "answer": result["answer"],
            "sources": results,
            "chunks_searched": stats["total_chunks"],
            "chunks_retrieved": len(results),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index")
async def index_repo(body: IndexRequest):
    match = re.search(r"github\.com/([^/]+)/([^/\s]+)", body.github_url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
    owner, repo_name = match.group(1), match.group(2).rstrip(".git")
    collection_name = f"{owner}_{repo_name}"
    clone_path = Path(f"/tmp/{collection_name}")

    try:
        if clone_path.exists():
            shutil.rmtree(clone_path)
        loader = CodebaseLoader(str(clone_path))
        loader.clone_repo(body.github_url, str(clone_path))
        docs = loader.load_files()
        if not docs:
            raise HTTPException(status_code=422, detail="No indexable files found in repository")
        chunks = CodeChunker().chunk_documents(docs)
        vs = CodeVectorStore(collection_name=collection_name, persist_dir="./chroma_db")
        vs.create_index(chunks)
        return {
            "collection_name": collection_name,
            "files_indexed": len(docs),
            "chunks_created": len(chunks),
            "status": "ready",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
