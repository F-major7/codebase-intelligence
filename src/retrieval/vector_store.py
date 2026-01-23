"""Vector store for semantic code search using ChromaDB and OpenAI embeddings."""

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from typing import List, Dict, Optional
import os


class CodeVectorStore:
    """Vector store for indexing and searching code chunks using semantic similarity.
    
    This class manages a ChromaDB collection with OpenAI embeddings for efficient
    semantic search over code chunks. Supports persistence to disk for reuse.
    
    Example:
        >>> vector_store = CodeVectorStore(collection_name="my_codebase")
        >>> vector_store.create_index(chunks)
        >>> results = vector_store.search("How does authentication work?", k=5)
        >>> for result in results:
        ...     print(f"File: {result['file_path']}, Score: {result['score']:.3f}")
    """
    
    def __init__(self, collection_name: str = "codebase", persist_dir: str = "./chroma_db"):
        """Initialize the vector store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_dir: Directory to persist the vector database
            
        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set
        """
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please set it to use OpenAI embeddings."
            )
        
        # Initialize OpenAI embeddings with the small model (cost-effective)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Store configuration
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        
        # Vector store will be initialized in create_index or load_index
        self.vectorstore: Optional[Chroma] = None
        
        print(f"Initializing vector store with collection: {collection_name}")
    
    def create_index(self, chunks: List[Dict]) -> None:
        """Create a new vector index from code chunks.
        
        Takes a list of chunk dictionaries (from CodeChunker) and creates
        a vector database with embeddings. Persists to disk for later use.
        
        Args:
            chunks: List of chunk dicts with keys:
                   - content: The code text
                   - file_path: Source file path
                   - file_name: Source file name
                   - chunk_id: Position within file
                   
        Raises:
            ValueError: If chunks list is empty
        """
        if not chunks:
            raise ValueError("Cannot create index from empty chunks list")
        
        # Extract texts and metadata from chunks
        texts = [chunk['content'] for chunk in chunks]
        metadatas = [
            {
                'file_path': chunk['file_path'],
                'file_name': chunk['file_name'],
                'chunk_id': chunk['chunk_id']
            }
            for chunk in chunks
        ]
        
        # Create Chroma vector store from texts
        self.vectorstore = Chroma.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas,
            collection_name=self.collection_name,
            persist_directory=self.persist_dir
        )
        
        print(f"✅ Indexed {len(chunks)} chunks into vector database")
        print(f"💾 Persisted to: {self.persist_dir}")
    
    def load_index(self) -> None:
        """Load an existing vector index from disk.
        
        Loads a previously created and persisted vector store from disk.
        Useful for reusing an index without re-embedding all documents.
        
        Raises:
            ValueError: If no existing index found at persist_dir
        """
        # Check if persist directory exists
        if not os.path.exists(self.persist_dir):
            raise ValueError(
                f"No existing index found at {self.persist_dir}. "
                "Create an index first using create_index()."
            )
        
        # Load existing vector store from disk
        self.vectorstore = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings,
            collection_name=self.collection_name
        )
        
        print(f"✅ Loaded existing index from {self.persist_dir}")
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for relevant code chunks using semantic similarity.
        
        Args:
            query: Natural language query describing what code to find
            k: Number of top results to return
            
        Returns:
            List of result dictionaries with keys:
            - content: The code chunk text
            - file_path: Source file path
            - file_name: Source file name
            - chunk_id: Position within file
            - score: Similarity score (lower is more similar)
            
        Raises:
            ValueError: If vector store hasn't been created or loaded
            
        Example:
            >>> results = vector_store.search("authentication logic", k=3)
            >>> print(results[0]['file_path'])
            src/auth/login.py
        """
        if self.vectorstore is None:
            raise ValueError(
                "Vector store not initialized. "
                "Call create_index() or load_index() first."
            )
        
        # Perform similarity search with scores
        docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=k)
        
        # Format results
        results = []
        for doc, score in docs_and_scores:
            result = {
                'content': doc.page_content,
                'file_path': doc.metadata.get('file_path', 'unknown'),
                'file_name': doc.metadata.get('file_name', 'unknown'),
                'chunk_id': doc.metadata.get('chunk_id', 0),
                'score': score
            }
            results.append(result)
        
        print(f"🔍 Found {len(results)} relevant chunks for query")
        return results
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store.
        
        Returns:
            Dictionary with keys:
            - total_chunks: Number of vectors in collection
            - collection_name: Name of the collection
            - persist_dir: Storage location
            
        Raises:
            ValueError: If vector store hasn't been created or loaded
        """
        if self.vectorstore is None:
            raise ValueError(
                "Vector store not initialized. "
                "Call create_index() or load_index() first."
            )
        
        # Get collection to access count
        collection = self.vectorstore._collection
        total_chunks = collection.count()
        
        stats = {
            'total_chunks': total_chunks,
            'collection_name': self.collection_name,
            'persist_dir': self.persist_dir
        }
        
        # Print stats in readable format
        print(f"\n📊 Vector Store Statistics:")
        print(f"  Collection: {stats['collection_name']}")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Storage: {stats['persist_dir']}")
        
        return stats

