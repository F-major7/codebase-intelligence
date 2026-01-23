"""Code chunking logic for splitting documents into manageable pieces."""

from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter


class CodeChunker:
    """Splits code documents into smaller chunks while preserving code structure.
    
    Uses a recursive character text splitter with code-aware separators that
    prioritize splitting at natural code boundaries (classes, functions) before
    falling back to line breaks and character-level splitting.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize the code chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
                          (helps maintain context across boundaries)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Configure code-aware separators in priority order
        # We want to split at natural code boundaries first
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\nclass ",      # Split at class definitions (highest priority)
                "\n\ndef ",        # Split at function definitions
                "\n\nasync def ",  # Split at async function definitions
                "\n\n",            # Split at blank lines (paragraph breaks)
                "\n",              # Split at line breaks
                " ",               # Split at spaces
                ""                 # Character-level split (last resort)
            ]
        )
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Split documents into smaller chunks while preserving metadata.
        
        Takes a list of document dictionaries (typically from CodebaseLoader)
        and splits each one into smaller chunks. Each chunk maintains a reference
        to its source file and position within that file.
        
        Args:
            documents: List of document dicts with keys:
                      - content: File text content
                      - file_path: Path to source file
                      - file_name: Name of source file
                      
        Returns:
            List of chunk dictionaries with keys:
            - content: The chunk text
            - file_path: Original file path
            - file_name: Original file name
            - chunk_id: Position within the file (0-indexed)
            - metadata: Human-readable string for citations
            
        Example:
            >>> documents = [{'content': 'def foo():\n    pass\n' * 100, 
            ...               'file_path': 'src/main.py', 
            ...               'file_name': 'main.py'}]
            >>> chunker = CodeChunker(chunk_size=500)
            >>> chunks = chunker.chunk_documents(documents)
            >>> len(chunks) > len(documents)  # Files got split
            True
        """
        all_chunks = []
        chunk_sizes = []
        
        for doc in documents:
            content = doc.get('content', '')
            file_path = doc.get('file_path', 'unknown')
            file_name = doc.get('file_name', 'unknown')
            
            # Handle edge case: empty files
            if not content or not content.strip():
                continue
            
            # Split the content into chunks
            splits = self.text_splitter.split_text(content)
            total_chunks = len(splits)
            
            # Create a chunk dict for each split
            for i, chunk_content in enumerate(splits):
                chunk_dict = {
                    'content': chunk_content,
                    'file_path': file_path,
                    'file_name': file_name,
                    'chunk_id': i,
                    'metadata': f"File: {file_path} (Part {i+1}/{total_chunks})"
                }
                all_chunks.append(chunk_dict)
                chunk_sizes.append(len(chunk_content))
        
        # Calculate and log statistics
        if chunk_sizes:
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            min_size = min(chunk_sizes)
            max_size = max(chunk_sizes)
            
            print(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
            print(f"Chunk size stats - Min: {min_size}, Max: {max_size}, Avg: {avg_size:.0f}")
        else:
            print(f"Created 0 chunks from {len(documents)} documents (all empty)")
        
        return all_chunks
