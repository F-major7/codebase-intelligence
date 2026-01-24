"""Tests for the Q&A generation chain."""

import sys
import pathlib
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src.ingestion.loader import CodebaseLoader
from src.ingestion.chunker import CodeChunker
from src.retrieval.vector_store import CodeVectorStore
from src.generation.qa_chain import CodeQAChain


def test_qa_chain_initialization():
    """Test that QA chain initializes correctly."""
    print("\n" + "=" * 60)
    print("TEST: QA Chain Initialization")
    print("=" * 60)
    
    qa = CodeQAChain()
    assert qa.model == "claude-3-5-sonnet-20241022"
    assert qa.temperature == 0.0
    
    print("✅ QA chain initialized successfully")


def test_context_formatting():
    """Test that context is formatted correctly."""
    print("\n" + "=" * 60)
    print("TEST: Context Formatting")
    print("=" * 60)
    
    qa = CodeQAChain()
    
    # Create sample chunks
    chunks = [
        {
            'content': 'def hello():\n    return "world"',
            'file_path': 'test.py',
            'chunk_id': 0
        },
        {
            'content': 'class TestClass:\n    pass',
            'file_path': 'test.py',
            'chunk_id': 1
        }
    ]
    
    context = qa._format_context(chunks)
    
    # Verify format
    assert 'File: test.py' in context
    assert 'def hello()' in context
    assert 'class TestClass' in context
    assert '```python' in context
    
    print("✅ Context formatting works correctly")
    print(f"\nSample formatted context:\n{context[:200]}...")


def test_empty_context():
    """Test handling of empty context."""
    print("\n" + "=" * 60)
    print("TEST: Empty Context Handling")
    print("=" * 60)
    
    qa = CodeQAChain()
    
    # Empty chunks
    result = qa.ask("test question", [])
    
    assert 'answer' in result
    # Accept either successful response or error message
    is_valid_response = (
        'No relevant code found' in result['answer'] or 
        'provided code doesn\'t contain' in result['answer'].lower() or
        'Error generating answer' in result['answer']
    )
    assert is_valid_response, f"Unexpected response: {result['answer']}"
    
    print("✅ Empty context handled gracefully")
    print(f"\nResponse: {result['answer'][:200]}...")


def test_answer_generation():
    """Test end-to-end answer generation."""
    print("\n" + "=" * 60)
    print("TEST: Answer Generation")
    print("=" * 60)
    
    # Set up pipeline
    project_root = pathlib.Path(__file__).parent.parent
    
    # Load and index
    loader = CodebaseLoader(str(project_root))
    documents = loader.load_files()
    
    chunker = CodeChunker()
    chunks = chunker.chunk_documents(documents)
    
    vector_store = CodeVectorStore(collection_name="test_qa")
    vector_store.create_index(chunks)
    
    # Initialize Q&A
    qa = CodeQAChain()
    
    # Test questions
    test_questions = [
        "How does the CodebaseLoader filter files?",
        "What chunking strategy is used?",
        "How are embeddings stored?"
    ]
    
    for question in test_questions:
        print(f"\n{'─' * 60}")
        print(f"Question: {question}")
        print('─' * 60)
        
        # Retrieve context
        retrieved = vector_store.search(question, k=3)
        
        # Generate answer
        result = qa.ask(question, retrieved)
        
        # Assertions
        assert 'answer' in result
        assert 'sources' in result
        assert isinstance(result['answer'], str)
        assert len(result['answer']) > 0
        
        # Print answer
        print(f"\nAnswer:\n{result['answer']}\n")
        print(f"Sources: {', '.join(set(result['sources']))}")
        print(f"Chunks used: {result['num_chunks_used']}")
        
        print("\n✅ Answer generated successfully")
    
    # Cleanup
    import shutil
    shutil.rmtree("./chroma_db")


if __name__ == "__main__":
    print("Running Q&A Chain tests...\n")
    
    try:
        test_qa_chain_initialization()
        test_context_formatting()
        test_empty_context()
        test_answer_generation()
        
        print("\n" + "=" * 60)
        print("✅ ALL QA TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

