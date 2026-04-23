"""Seed pre-indexed collections (flask/fastapi/django) into chroma_db.

Run locally before testing, and once on Railway after first deploy.
Safe to re-run — skips any collection that already exists.
"""
import os
import shutil

from dotenv import load_dotenv
load_dotenv()

import chromadb
from src.ingestion.loader import CodebaseLoader
from src.ingestion.chunker import CodeChunker
from src.retrieval.vector_store import CodeVectorStore

REPOS = [
    ("flask",   "https://github.com/pallets/flask"),
    ("fastapi", "https://github.com/tiangolo/fastapi"),
    ("django",  "https://github.com/django/django"),
]

PERSIST_DIR = "./chroma_db"

existing = {c.name for c in chromadb.PersistentClient(PERSIST_DIR).list_collections()}

for name, url in REPOS:
    if name in existing:
        print(f"✓ {name} already indexed — skipping")
        continue

    print(f"\n→ Indexing {name} from {url} …")
    clone_path = f"/tmp/{name}_seed"

    if os.path.exists(clone_path):
        shutil.rmtree(clone_path)

    loader = CodebaseLoader(clone_path)
    loader.clone_repo(url, clone_path)
    docs = loader.load_files()

    if not docs:
        print(f"  ⚠ No indexable files found for {name}, skipping")
        continue

    chunks = CodeChunker().chunk_documents(docs)
    vs = CodeVectorStore(collection_name=name, persist_dir=PERSIST_DIR)
    vs.create_index(chunks)
    print(f"  ✓ {name}: {len(docs)} files → {len(chunks)} chunks indexed")

print("\nDone.")
