#!/usr/bin/env python3
"""
Script to pre-index popular repositories for the RAG-based code intelligence system.

This script clones and indexes 4 repositories that will be available to all users:
- Flask (web framework)
- FastAPI (modern web framework)
- Django (full-featured web framework)
- RAG Project (this codebase itself)

Each repository gets its own ChromaDB collection in the shared ./chroma_db directory.
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import git

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.loader import CodebaseLoader
from src.ingestion.chunker import CodeChunker
from src.retrieval.vector_store import CodeVectorStore


# Repository configurations
REPOS_TO_INDEX = [
    {
        'name': 'Flask',
        'url': 'https://github.com/pallets/flask',
        'collection_name': 'permanent_flask'
    },
    {
        'name': 'FastAPI',
        'url': 'https://github.com/tiangolo/fastapi',
        'collection_name': 'permanent_fastapi'
    },
    {
        'name': 'Django',
        'url': 'https://github.com/django/django',
        'collection_name': 'permanent_django'
    }
]

# Configuration
PERSIST_DIR = "./chroma_db"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def print_header(text: str) -> None:
    """Print a formatted header for better readability."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def clone_repository(repo_url: str, temp_dir: str, repo_name: str) -> str:
    """
    Clone a GitHub repository to a temporary directory.
    
    Args:
        repo_url: GitHub repository URL
        temp_dir: Temporary directory path
        repo_name: Name of the repository (for display)
        
    Returns:
        Path to the cloned repository
        
    Raises:
        git.exc.GitCommandError: If cloning fails
    """
    print(f"📥 Cloning {repo_name} from {repo_url}...")
    
    try:
        target_path = Path(temp_dir) / repo_name.lower().replace(' ', '_')
        
        # Use shallow clone for speed (depth=1)
        git.Repo.clone_from(
            repo_url,
            target_path,
            depth=1,
            single_branch=True
        )
        
        print(f"✅ Successfully cloned {repo_name} to {target_path}")
        return str(target_path)
        
    except git.exc.GitCommandError as e:
        print(f"❌ Failed to clone {repo_name}: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error cloning {repo_name}: {e}")
        raise


def index_repository(
    repo_path: str,
    repo_name: str,
    collection_name: str,
    persist_dir: str
) -> int:
    """
    Index a repository into a ChromaDB collection.
    
    Args:
        repo_path: Path to the repository directory
        repo_name: Display name of the repository
        collection_name: Name for the ChromaDB collection
        persist_dir: Directory to persist the vector database
        
    Returns:
        Number of chunks indexed
        
    Raises:
        Exception: If indexing fails at any stage
    """
    print(f"\n📚 Indexing {repo_name}...")
    print(f"   Repository path: {repo_path}")
    print(f"   Collection name: {collection_name}")
    
    try:
        # Step 1: Load files from repository
        print(f"\n   [1/3] Loading files from {repo_name}...")
        loader = CodebaseLoader(repo_path)
        documents = loader.load_files()
        
        if not documents:
            print(f"⚠️  No documents loaded from {repo_name}. Skipping indexing.")
            return 0
        
        print(f"   ✓ Loaded {len(documents)} files")
        
        # Step 2: Chunk documents
        print(f"\n   [2/3] Chunking documents...")
        chunker = CodeChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        chunks = chunker.chunk_documents(documents)
        
        if not chunks:
            print(f"⚠️  No chunks created from {repo_name}. Skipping indexing.")
            return 0
        
        print(f"   ✓ Created {len(chunks)} chunks")
        
        # Step 3: Create vector store index
        print(f"\n   [3/3] Creating vector store index...")
        vector_store = CodeVectorStore(
            collection_name=collection_name,
            persist_dir=persist_dir
        )
        vector_store.create_index(chunks)
        
        print(f"\n✅ Successfully indexed {repo_name}: {len(chunks)} chunks")
        return len(chunks)
        
    except Exception as e:
        print(f"\n❌ Failed to index {repo_name}: {e}")
        raise


def index_current_project(persist_dir: str) -> int:
    """
    Index the current RAG project itself.
    
    Args:
        persist_dir: Directory to persist the vector database
        
    Returns:
        Number of chunks indexed
    """
    current_dir = Path(__file__).parent
    return index_repository(
        repo_path=str(current_dir),
        repo_name="RAG Project",
        collection_name="permanent_rag_project",
        persist_dir=persist_dir
    )


def main():
    """Main execution function."""
    print_header("Permanent Repository Indexing Script")
    print("This script will index 4 repositories into ChromaDB collections:")
    print("  1. Flask")
    print("  2. FastAPI")
    print("  3. Django")
    print("  4. RAG Project (this codebase)")
    print(f"\nAll collections will be stored in: {PERSIST_DIR}")
    
    # Load environment variables
    print("\n🔑 Loading environment variables...")
    load_dotenv()
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set!")
        print("   Please set it in your .env file or environment.")
        sys.exit(1)
    
    print("✅ Environment variables loaded")
    
    # Track results
    results: List[Tuple[str, int]] = []
    temp_dirs: List[str] = []
    
    try:
        # Create temporary directory for cloning
        temp_base = tempfile.mkdtemp(prefix="rag_repos_")
        print(f"\n📁 Created temporary directory: {temp_base}")
        
        # Index external repositories
        for repo_config in REPOS_TO_INDEX:
            print_header(f"Processing: {repo_config['name']}")
            
            try:
                # Clone repository
                repo_path = clone_repository(
                    repo_url=repo_config['url'],
                    temp_dir=temp_base,
                    repo_name=repo_config['name']
                )
                temp_dirs.append(repo_path)
                
                # Index repository
                num_chunks = index_repository(
                    repo_path=repo_path,
                    repo_name=repo_config['name'],
                    collection_name=repo_config['collection_name'],
                    persist_dir=PERSIST_DIR
                )
                
                results.append((repo_config['name'], num_chunks))
                
            except Exception as e:
                print(f"\n❌ Failed to process {repo_config['name']}: {e}")
                print(f"   Continuing with remaining repositories...")
                results.append((repo_config['name'], 0))
                continue
        
        # Index current project
        print_header("Processing: RAG Project (Current Codebase)")
        try:
            num_chunks = index_current_project(PERSIST_DIR)
            results.append(("RAG Project", num_chunks))
        except Exception as e:
            print(f"\n❌ Failed to process RAG Project: {e}")
            results.append(("RAG Project", 0))
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Cleaning up...")
        
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        
    finally:
        # Clean up temporary directories
        if temp_dirs or 'temp_base' in locals():
            print_header("Cleaning Up")
            print("🧹 Removing temporary clone directories...")
            
            try:
                if 'temp_base' in locals():
                    shutil.rmtree(temp_base, ignore_errors=True)
                    print(f"✅ Removed temporary directory: {temp_base}")
            except Exception as e:
                print(f"⚠️  Error during cleanup: {e}")
    
    # Print final summary
    print_header("Indexing Summary")
    
    total_chunks = 0
    successful_repos = 0
    
    for repo_name, num_chunks in results:
        status = "✅" if num_chunks > 0 else "❌"
        print(f"{status} {repo_name:20s}: {num_chunks:,} chunks")
        total_chunks += num_chunks
        if num_chunks > 0:
            successful_repos += 1
    
    print(f"\n{'=' * 70}")
    print(f"Total: {successful_repos}/{len(results)} repositories indexed successfully")
    print(f"Total chunks: {total_chunks:,}")
    print(f"Storage location: {PERSIST_DIR}")
    print(f"{'=' * 70}\n")
    
    if successful_repos == len(results):
        print("🎉 All repositories indexed successfully!")
        return 0
    elif successful_repos > 0:
        print("⚠️  Some repositories failed to index. Check logs above for details.")
        return 1
    else:
        print("❌ All repositories failed to index. Please check your configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

