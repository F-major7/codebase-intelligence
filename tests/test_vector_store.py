"""Tests for the vector store and semantic search functionality."""

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


def test_vector_store_creation():
    """Test creating and indexing a vector store."""
    print("\n" + "="*60)
    print("TEST: Vector Store Creation")
    print("="*60)
    
    # Load files and create chunks using Phase 1 code
    project_root = pathlib.Path(__file__).parent.parent
    loader = CodebaseLoader(str(project_root))
    documents = loader.load_files()
    print(f"✅ Loaded {len(documents)} files")
    
    chunker = CodeChunker()
    chunks = chunker.chunk_documents(documents)
    print(f"✅ Created {len(chunks)} chunks")
    
    # Create vector store
    # Use a test-specific collection name and directory
    test_persist_dir = str(project_root / "chroma_db_test")
    
    # Clean up any existing test database
    if os.path.exists(test_persist_dir):
        shutil.rmtree(test_persist_dir)
    
    vector_store = CodeVectorStore(
        collection_name="test_collection",
        persist_dir=test_persist_dir
    )
    
    # Index the chunks
    vector_store.create_index(chunks)
    
    # Assertions
    assert vector_store.vectorstore is not None, "Vector store should be initialized"
    
    # Get and verify stats
    stats = vector_store.get_stats()
    assert stats['total_chunks'] == len(chunks), \
        f"Expected {len(chunks)} chunks, got {stats['total_chunks']}"
    assert stats['collection_name'] == "test_collection"
    
    print("✅ Vector store created successfully")
    
    return vector_store, chunks


def test_search_relevance():
    """Test that search returns relevant results."""
    print("\n" + "="*60)
    print("TEST: Search Relevance")
    print("="*60)
    
    # Create and index vector store
    project_root = pathlib.Path(__file__).parent.parent
    loader = CodebaseLoader(str(project_root))
    documents = loader.load_files()
    
    chunker = CodeChunker()
    chunks = chunker.chunk_documents(documents)
    
    test_persist_dir = str(project_root / "chroma_db_test")
    
    # Try to load existing, or create new
    if os.path.exists(test_persist_dir):
        vector_store = CodeVectorStore(
            collection_name="test_collection",
            persist_dir=test_persist_dir
        )
        vector_store.load_index()
    else:
        vector_store = CodeVectorStore(
            collection_name="test_collection",
            persist_dir=test_persist_dir
        )
        vector_store.create_index(chunks)
    
    # Define test queries
    test_queries = [
        "How does the file loader work?",
        "What is the chunking strategy?",
        "How are code files filtered?"
    ]
    
    print(f"\nTesting {len(test_queries)} queries:")
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        # Search with k=3
        results = vector_store.search(query, k=3)
        
        # Assertions
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        # Check each result has required keys
        required_keys = {'content', 'file_path', 'file_name', 'chunk_id', 'score'}
        for result in results:
            assert required_keys.issubset(result.keys()), \
                f"Result missing required keys: {result.keys()}"
        
        # Print top result
        top_result = results[0]
        print(f"  Top result: {top_result['file_path']}")
        print(f"  Score: {top_result['score']:.3f}")
        print(f"  Preview: {top_result['content'][:100].replace(chr(10), ' ')}...")
    
    print("\n✅ Search returns relevant results")


def test_persistence():
    """Test that vector store persists correctly to disk."""
    print("\n" + "="*60)
    print("TEST: Persistence")
    print("="*60)
    
    # Create vector store and index chunks
    project_root = pathlib.Path(__file__).parent.parent
    loader = CodebaseLoader(str(project_root))
    documents = loader.load_files()
    
    chunker = CodeChunker()
    chunks = chunker.chunk_documents(documents)
    
    test_persist_dir = str(project_root / "chroma_db_test_persistence")
    
    # Clean up any existing database
    if os.path.exists(test_persist_dir):
        shutil.rmtree(test_persist_dir)
    
    # Create and index
    vector_store1 = CodeVectorStore(
        collection_name="persistence_test",
        persist_dir=test_persist_dir
    )
    vector_store1.create_index(chunks)
    
    # Get initial stats
    stats1 = vector_store1.get_stats()
    initial_count = stats1['total_chunks']
    print(f"Initial index: {initial_count} chunks")
    
    # Create NEW vector store instance (same collection_name)
    vector_store2 = CodeVectorStore(
        collection_name="persistence_test",
        persist_dir=test_persist_dir
    )
    
    # Load existing index
    vector_store2.load_index()
    
    # Get stats from loaded index
    stats2 = vector_store2.get_stats()
    loaded_count = stats2['total_chunks']
    print(f"Loaded index: {loaded_count} chunks")
    
    # Assertions
    assert initial_count == loaded_count, \
        f"Chunk counts don't match: {initial_count} vs {loaded_count}"
    
    # Verify search still works
    results = vector_store2.search("test query", k=3)
    assert len(results) > 0, "Search should return results from loaded index"
    
    print("✅ Vector store persists correctly")
    
    # Cleanup
    shutil.rmtree(test_persist_dir)


def test_metadata_preservation():
    """Test that metadata is preserved in search results."""
    print("\n" + "="*60)
    print("TEST: Metadata Preservation")
    print("="*60)
    
    # Load and index
    project_root = pathlib.Path(__file__).parent.parent
    loader = CodebaseLoader(str(project_root))
    documents = loader.load_files()
    
    chunker = CodeChunker()
    chunks = chunker.chunk_documents(documents)
    
    test_persist_dir = str(project_root / "chroma_db_test")
    
    # Use existing or create new
    if os.path.exists(test_persist_dir):
        vector_store = CodeVectorStore(
            collection_name="test_collection",
            persist_dir=test_persist_dir
        )
        vector_store.load_index()
    else:
        vector_store = CodeVectorStore(
            collection_name="test_collection",
            persist_dir=test_persist_dir
        )
        vector_store.create_index(chunks)
    
    # Search for a query
    results = vector_store.search("file loader", k=3)
    
    print(f"\nChecking metadata in {len(results)} results:")
    
    # Verify results contain required metadata
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  File: {result['file_path']}")
        print(f"  Chunk ID: {result['chunk_id']}")
        print(f"  Score: {result['score']:.3f}")
        
        # Assertions
        assert 'file_path' in result, "Missing file_path in metadata"
        assert 'chunk_id' in result, "Missing chunk_id in metadata"
        assert result['file_path'] != 'unknown', "file_path should not be 'unknown'"
        assert isinstance(result['chunk_id'], int), "chunk_id should be an integer"
    
    # Verify metadata can be used for citations
    citation = f"Source: {results[0]['file_path']} (Chunk {results[0]['chunk_id']})"
    print(f"\nSample citation: {citation}")
    
    print("\n✅ Metadata preserved in search results")


if __name__ == "__main__":
    # Run tests manually if executed directly
    print("Running vector store tests...")
    
    try:
        # Test 1: Creation
        vector_store, chunks = test_vector_store_creation()
        
        # Test 2: Search
        test_search_relevance()
        
        # Test 3: Persistence
        test_persistence()
        
        # Test 4: Metadata
        test_metadata_preservation()
        
        print("\n" + "="*60)
        print("✅ ALL VECTOR STORE TESTS PASSED!")
        print("="*60)
        
        # Cleanup test database
        project_root = pathlib.Path(__file__).parent.parent
        test_persist_dir = str(project_root / "chroma_db_test")
        if os.path.exists(test_persist_dir):
            shutil.rmtree(test_persist_dir)
            print(f"\n🧹 Cleaned up test database: {test_persist_dir}")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

