"""End-to-end integration test for the complete RAG pipeline."""

import sys
import pathlib
import os
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import src modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src.ingestion.loader import CodebaseLoader
from src.ingestion.chunker import CodeChunker
from src.retrieval.vector_store import CodeVectorStore


def test_full_ingestion_to_retrieval():
    """Test complete pipeline: Load → Chunk → Index → Search"""
    
    project_root = pathlib.Path(__file__).parent.parent
    
    # Phase 1: Ingestion
    print("=" * 60)
    print("PHASE 1: Ingestion")
    print("=" * 60)
    
    loader = CodebaseLoader(str(project_root))
    documents = loader.load_files()
    print(f"✅ Loaded {len(documents)} files")
    
    chunker = CodeChunker()
    chunks = chunker.chunk_documents(documents)
    print(f"✅ Created {len(chunks)} chunks")
    
    # Phase 2: Indexing
    print("\n" + "=" * 60)
    print("PHASE 2: Vector Indexing")
    print("=" * 60)
    
    test_persist_dir = str(project_root / "chroma_db_pipeline_test")
    
    # Clean up any existing test database
    if os.path.exists(test_persist_dir):
        shutil.rmtree(test_persist_dir)
    
    vector_store = CodeVectorStore(
        collection_name="test_pipeline",
        persist_dir=test_persist_dir
    )
    vector_store.create_index(chunks)
    
    stats = vector_store.get_stats()
    print(f"✅ Indexed {stats['total_chunks']} chunks")
    
    # Phase 3: Retrieval
    print("\n" + "=" * 60)
    print("PHASE 3: Semantic Search")
    print("=" * 60)
    
    test_queries = [
        "How does the file loader filter files?",
        "What chunking strategy is used?",
        "How are code files read from disk?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = vector_store.search(query, k=3)
        
        # Assertions
        assert len(results) > 0, f"No results returned for query: {query}"
        assert len(results) <= 3, f"Too many results returned: {len(results)}"
        
        # Print top result details
        top_result = results[0]
        print(f"  Top result: {top_result['file_path']}")
        print(f"  Score: {top_result['score']:.3f}")
        print(f"  Preview: {top_result['content'][:150].replace(chr(10), ' ')}...")
        
        # Verify result structure
        assert 'content' in top_result
        assert 'file_path' in top_result
        assert 'score' in top_result
        assert isinstance(top_result['score'], float)
    
    # Phase 4: Verify persistence and reloading
    print("\n" + "=" * 60)
    print("PHASE 4: Persistence Verification")
    print("=" * 60)
    
    # Create new instance and load
    vector_store2 = CodeVectorStore(
        collection_name="test_pipeline",
        persist_dir=test_persist_dir
    )
    vector_store2.load_index()
    
    # Verify loaded store works
    test_results = vector_store2.search("test search", k=1)
    assert len(test_results) > 0, "Loaded vector store should return results"
    print("✅ Vector store successfully reloaded from disk")
    
    print("\n" + "=" * 60)
    print("✅ FULL PIPELINE TEST PASSED!")
    print("=" * 60)
    
    # Print summary
    print("\n📊 Pipeline Summary:")
    print(f"  Files loaded: {len(documents)}")
    print(f"  Chunks created: {len(chunks)}")
    print(f"  Vectors indexed: {stats['total_chunks']}")
    print(f"  Queries tested: {len(test_queries)}")
    print(f"  Storage location: {test_persist_dir}")
    
    # Cleanup
    shutil.rmtree(test_persist_dir)
    print(f"\n🧹 Cleaned up test database")


if __name__ == "__main__":
    # Run test manually if executed directly
    print("Running full RAG pipeline test...\n")
    
    try:
        test_full_ingestion_to_retrieval()
        
        print("\n" + "="*60)
        print("✅ END-TO-END PIPELINE TEST COMPLETE!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

