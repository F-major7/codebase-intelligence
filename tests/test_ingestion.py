"""Integration tests for the ingestion pipeline."""

import sys
import pathlib

# Add parent directory to path to import src modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src.ingestion.loader import CodebaseLoader
from src.ingestion.chunker import CodeChunker


def test_loader():
    """Test the CodebaseLoader loads files from current project."""
    print("\n" + "="*60)
    print("TEST: CodebaseLoader")
    print("="*60)
    
    # Use current project directory as test data
    project_root = pathlib.Path(__file__).parent.parent
    loader = CodebaseLoader(str(project_root))
    
    # Load files
    documents = loader.load_files()
    
    # Assertions
    assert len(documents) >= 3, f"Expected at least 3 files, got {len(documents)}"
    print(f"✅ Loaded {len(documents)} files")
    
    # Check all documents have required keys
    required_keys = {'content', 'file_path', 'file_name', 'extension'}
    for doc in documents:
        assert required_keys.issubset(doc.keys()), f"Missing keys in document: {doc.keys()}"
        assert isinstance(doc['content'], str), "Content should be a string"
        assert len(doc['content']) > 0, "Content should be non-empty"
    
    print(f"✅ All documents have required keys: {required_keys}")
    print(f"✅ All content is non-empty strings")
    
    # Print sample files loaded
    print(f"\nSample files loaded:")
    for doc in documents[:5]:
        print(f"  - {doc['file_path']} ({len(doc['content'])} chars)")
    
    return documents


def test_chunker():
    """Test the CodeChunker splits documents correctly."""
    print("\n" + "="*60)
    print("TEST: CodeChunker")
    print("="*60)
    
    # Load files first
    project_root = pathlib.Path(__file__).parent.parent
    loader = CodebaseLoader(str(project_root))
    documents = loader.load_files()
    
    # Chunk the documents
    chunker = CodeChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk_documents(documents)
    
    # Assertions
    assert len(chunks) > len(documents), \
        f"Expected more chunks than documents (got {len(chunks)} chunks from {len(documents)} docs)"
    print(f"✅ Created {len(chunks)} chunks from {len(documents)} documents")
    
    # Check all chunks have required keys
    required_keys = {'content', 'file_path', 'file_name', 'chunk_id', 'metadata'}
    for chunk in chunks:
        assert required_keys.issubset(chunk.keys()), \
            f"Missing keys in chunk: {chunk.keys()}"
    print(f"✅ All chunks have required keys: {required_keys}")
    
    # Check chunk_ids are sequential within same file
    file_chunks = {}
    for chunk in chunks:
        file_path = chunk['file_path']
        if file_path not in file_chunks:
            file_chunks[file_path] = []
        file_chunks[file_path].append(chunk['chunk_id'])
    
    for file_path, chunk_ids in file_chunks.items():
        expected_ids = list(range(len(chunk_ids)))
        assert chunk_ids == expected_ids, \
            f"Chunk IDs not sequential for {file_path}: {chunk_ids}"
    print(f"✅ Chunk IDs are sequential within same file")
    
    # Check metadata string format
    for chunk in chunks:
        metadata = chunk['metadata']
        assert 'File:' in metadata, f"Metadata missing 'File:' prefix: {metadata}"
        assert '(Part' in metadata, f"Metadata missing '(Part' section: {metadata}"
        assert '/' in metadata, f"Metadata missing '/' separator: {metadata}"
    print(f"✅ All metadata strings have correct format")
    
    # Print sample chunks
    print(f"\nSample chunks:")
    for chunk in chunks[:3]:
        content_preview = chunk['content'][:60].replace('\n', '\\n')
        print(f"  - {chunk['metadata']}")
        print(f"    Preview: {content_preview}...")
    
    return chunks


def test_full_pipeline():
    """Test the full ingestion pipeline end-to-end."""
    print("\n" + "="*60)
    print("TEST: Full Pipeline (Loader → Chunker)")
    print("="*60)
    
    # Step 1: Load files
    project_root = pathlib.Path(__file__).parent.parent
    loader = CodebaseLoader(str(project_root))
    documents = loader.load_files()
    print(f"✅ Step 1: Loaded {len(documents)} files")
    
    # Step 2: Chunk documents
    chunker = CodeChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk_documents(documents)
    print(f"✅ Step 2: Created {len(chunks)} chunks")
    
    # Summary statistics
    print(f"\n" + "="*60)
    print("PIPELINE SUMMARY")
    print("="*60)
    print(f"Total files loaded: {len(documents)}")
    print(f"Total chunks created: {len(chunks)}")
    print(f"Average chunks per file: {len(chunks) / len(documents):.1f}")
    
    # Calculate total content size
    total_chars = sum(len(doc['content']) for doc in documents)
    print(f"Total characters processed: {total_chars:,}")
    
    # File type breakdown
    extensions = {}
    for doc in documents:
        ext = doc['extension']
        extensions[ext] = extensions.get(ext, 0) + 1
    
    print(f"\nFile type breakdown:")
    for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ext}: {count} files")
    
    print(f"\n✅ Pipeline completed successfully!")
    
    # Final assertion
    assert len(chunks) > 0, "Pipeline should produce at least one chunk"
    assert len(documents) > 0, "Pipeline should load at least one document"


if __name__ == "__main__":
    # Run tests manually if executed directly
    print("Running ingestion pipeline tests...")
    
    try:
        docs = test_loader()
        chunks = test_chunker()
        test_full_pipeline()
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
