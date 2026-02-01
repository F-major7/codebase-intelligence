#!/usr/bin/env python3
"""
Example script showing how to query the permanent indexed repositories.

This demonstrates how to:
1. Load a permanent collection
2. Search for code
3. Query multiple collections
4. Display results
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.vector_store import CodeVectorStore


def query_single_collection(collection_name: str, query: str, k: int = 5):
    """
    Query a single permanent collection.
    
    Args:
        collection_name: Name of the collection (e.g., 'permanent_flask')
        query: Natural language query
        k: Number of results to return
    """
    print(f"\n{'=' * 70}")
    print(f"Querying: {collection_name}")
    print(f"Query: {query}")
    print(f"{'=' * 70}\n")
    
    # Load the collection
    vector_store = CodeVectorStore(
        collection_name=collection_name,
        persist_dir="./chroma_db"
    )
    vector_store.load_index()
    
    # Search for relevant code
    results = vector_store.search(query, k=k)
    
    # Display results
    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} (Score: {result['score']:.3f}) ---")
        print(f"File: {result['file_path']}")
        print(f"Chunk: {result['chunk_id']}")
        print(f"\nCode Preview:")
        print("-" * 70)
        # Show first 300 characters
        preview = result['content'][:300]
        if len(result['content']) > 300:
            preview += "..."
        print(preview)
        print("-" * 70)


def query_multiple_collections(query: str, collections: list, k: int = 3):
    """
    Query multiple collections and compare results.
    
    Args:
        query: Natural language query
        collections: List of collection names
        k: Number of results per collection
    """
    print(f"\n{'=' * 70}")
    print(f"Multi-Collection Query")
    print(f"Query: {query}")
    print(f"Collections: {', '.join(collections)}")
    print(f"{'=' * 70}\n")
    
    all_results = {}
    
    for collection_name in collections:
        print(f"\n📚 Searching {collection_name}...")
        
        try:
            vector_store = CodeVectorStore(
                collection_name=collection_name,
                persist_dir="./chroma_db"
            )
            vector_store.load_index()
            results = vector_store.search(query, k=k)
            all_results[collection_name] = results
            print(f"   Found {len(results)} results")
            
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            all_results[collection_name] = []
    
    # Display top result from each collection
    print(f"\n{'=' * 70}")
    print("Top Result from Each Collection")
    print(f"{'=' * 70}\n")
    
    for collection_name, results in all_results.items():
        if results:
            top_result = results[0]
            print(f"\n🏆 {collection_name}")
            print(f"   File: {top_result['file_path']}")
            print(f"   Score: {top_result['score']:.3f}")
            print(f"   Preview: {top_result['content'][:150]}...")
        else:
            print(f"\n❌ {collection_name}: No results")


def get_collection_stats(collection_name: str):
    """
    Get statistics about a collection.
    
    Args:
        collection_name: Name of the collection
    """
    print(f"\n{'=' * 70}")
    print(f"Collection Statistics: {collection_name}")
    print(f"{'=' * 70}\n")
    
    try:
        vector_store = CodeVectorStore(
            collection_name=collection_name,
            persist_dir="./chroma_db"
        )
        vector_store.load_index()
        stats = vector_store.get_stats()
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run example queries."""
    # Load environment variables
    load_dotenv()
    
    print("=" * 70)
    print("  Permanent Repository Query Examples")
    print("=" * 70)
    
    # Example 1: Query Flask for routing
    print("\n\n### EXAMPLE 1: Flask Routing ###")
    query_single_collection(
        collection_name="permanent_flask",
        query="How does URL routing work in Flask?",
        k=3
    )
    
    # Example 2: Query FastAPI for async
    print("\n\n### EXAMPLE 2: FastAPI Async ###")
    query_single_collection(
        collection_name="permanent_fastapi",
        query="How to use async endpoints in FastAPI?",
        k=3
    )
    
    # Example 3: Compare across frameworks
    print("\n\n### EXAMPLE 3: Compare Frameworks ###")
    query_multiple_collections(
        query="How to handle authentication?",
        collections=[
            "permanent_flask",
            "permanent_fastapi",
            "permanent_django"
        ],
        k=2
    )
    
    # Example 4: Query the RAG project itself
    print("\n\n### EXAMPLE 4: RAG Project ###")
    query_single_collection(
        collection_name="permanent_rag_project",
        query="How does the vector store work?",
        k=3
    )
    
    # Example 5: Get collection statistics
    print("\n\n### EXAMPLE 5: Collection Statistics ###")
    for collection in ["permanent_flask", "permanent_fastapi", 
                       "permanent_django", "permanent_rag_project"]:
        get_collection_stats(collection)
    
    print("\n\n" + "=" * 70)
    print("  Examples Complete!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)

