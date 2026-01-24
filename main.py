"""Command-line interface for Codebase Intelligence Assistant."""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.loader import CodebaseLoader
from src.ingestion.chunker import CodeChunker
from src.retrieval.vector_store import CodeVectorStore
from src.generation.qa_chain import CodeQAChain


def main():
    """Run the interactive Q&A system."""
    
    print("=" * 70)
    print("🤖 CODEBASE INTELLIGENCE ASSISTANT")
    print("=" * 70)
    
    # Check if we have an existing index
    persist_dir = "./chroma_db"
    collection_name = "codebase"
    
    try:
        # Try to load existing index
        print("\n📦 Loading vector store...")
        vector_store = CodeVectorStore(
            collection_name=collection_name,
            persist_dir=persist_dir
        )
        vector_store.load_index()
        stats = vector_store.get_stats()
        print(f"✅ Loaded existing index: {stats['total_chunks']} chunks")
        
    except (ValueError, Exception) as e:
        # No index exists, create one
        print("\n📥 No existing index found. Creating new index...")
        print("This will take a moment...\n")
        
        # Load and chunk current project
        loader = CodebaseLoader(".")
        documents = loader.load_files()
        print(f"✅ Loaded {len(documents)} files")
        
        chunker = CodeChunker()
        chunks = chunker.chunk_documents(documents)
        print(f"✅ Created {len(chunks)} chunks")
        
        # Create vector store
        vector_store = CodeVectorStore(
            collection_name=collection_name,
            persist_dir=persist_dir
        )
        vector_store.create_index(chunks)
        print(f"✅ Indexed {len(chunks)} chunks")
    
    # Initialize Q&A chain
    print("\n🧠 Initializing AI assistant...")
    qa_chain = CodeQAChain()
    print("✅ Ready to answer questions!\n")
    
    print("=" * 70)
    print("💬 Ask me anything about this codebase!")
    print("   (Type 'quit' or 'exit' to stop)")
    print("=" * 70)
    
    # Interactive loop
    while True:
        try:
            # Get question from user
            question = input("\n🔷 You: ").strip()
            
            # Check for exit
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Skip empty questions
            if not question:
                continue
            
            # Search for relevant chunks
            print("\n🔍 Searching codebase...")
            chunks = vector_store.search(question, k=5)
            print(f"   Found {len(chunks)} relevant chunks")
            
            # Generate answer
            print("🧠 Generating answer...\n")
            result = qa_chain.ask(question, chunks)
            
            # Display answer
            print("─" * 70)
            print(result['answer'])
            print("─" * 70)
            
            # Display sources
            if result['sources']:
                print(f"\n📎 Sources: {', '.join(set(result['sources']))}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.\n")


if __name__ == "__main__":
    main()
