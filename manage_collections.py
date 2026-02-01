#!/usr/bin/env python3
"""
Utility script to manage ChromaDB collections.

This script provides commands to:
- List all collections
- Get statistics for collections
- Delete specific collections
- Backup and restore collections
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.retrieval.vector_store import CodeVectorStore


PERSIST_DIR = "./chroma_db"


def list_collections():
    """List all ChromaDB collections."""
    print("\n" + "=" * 70)
    print("  ChromaDB Collections")
    print("=" * 70 + "\n")
    
    try:
        client = chromadb.PersistentClient(path=PERSIST_DIR)
        collections = client.list_collections()
        
        if not collections:
            print("No collections found.")
            return
        
        print(f"Found {len(collections)} collection(s):\n")
        
        for i, collection in enumerate(collections, 1):
            count = collection.count()
            print(f"{i}. {collection.name}")
            print(f"   Chunks: {count:,}")
            print(f"   ID: {collection.id}")
            print()
        
    except Exception as e:
        print(f"❌ Error listing collections: {e}")


def get_collection_stats(collection_name: str):
    """Get detailed statistics for a specific collection."""
    print("\n" + "=" * 70)
    print(f"  Collection Statistics: {collection_name}")
    print("=" * 70 + "\n")
    
    try:
        # Load environment for API key
        load_dotenv()
        
        vector_store = CodeVectorStore(
            collection_name=collection_name,
            persist_dir=PERSIST_DIR
        )
        vector_store.load_index()
        stats = vector_store.get_stats()
        
        # Additional details
        client = chromadb.PersistentClient(path=PERSIST_DIR)
        collection = client.get_collection(collection_name)
        
        # Get a sample document to show metadata
        results = collection.peek(limit=1)
        
        if results['metadatas']:
            print("\nSample Metadata:")
            for key, value in results['metadatas'][0].items():
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")


def delete_collection(collection_name: str, confirm: bool = False):
    """Delete a specific collection."""
    print("\n" + "=" * 70)
    print(f"  Delete Collection: {collection_name}")
    print("=" * 70 + "\n")
    
    if not confirm:
        response = input(f"Are you sure you want to delete '{collection_name}'? (yes/no): ")
        if response.lower() != 'yes':
            print("Deletion cancelled.")
            return
    
    try:
        client = chromadb.PersistentClient(path=PERSIST_DIR)
        client.delete_collection(collection_name)
        print(f"✅ Successfully deleted collection: {collection_name}")
        
    except Exception as e:
        print(f"❌ Error deleting collection: {e}")


def backup_collections(backup_dir: str = None):
    """Backup all collections to a tar.gz file."""
    if backup_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"chroma_db_backup_{timestamp}"
    
    print("\n" + "=" * 70)
    print("  Backup Collections")
    print("=" * 70 + "\n")
    
    try:
        # Create backup directory
        backup_path = Path(backup_dir)
        
        # Copy chroma_db directory
        print(f"Creating backup: {backup_dir}.tar.gz")
        shutil.copytree(PERSIST_DIR, backup_path)
        
        # Create tar.gz archive
        shutil.make_archive(backup_dir, 'gztar', '.', backup_dir)
        
        # Remove temporary directory
        shutil.rmtree(backup_path)
        
        # Get file size
        archive_path = Path(f"{backup_dir}.tar.gz")
        size_mb = archive_path.stat().st_size / (1024 * 1024)
        
        print(f"✅ Backup created: {archive_path}")
        print(f"   Size: {size_mb:.2f} MB")
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")


def restore_collections(backup_file: str):
    """Restore collections from a backup file."""
    print("\n" + "=" * 70)
    print("  Restore Collections")
    print("=" * 70 + "\n")
    
    backup_path = Path(backup_file)
    
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_file}")
        return
    
    # Confirm restoration
    response = input(f"This will replace existing collections. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Restoration cancelled.")
        return
    
    try:
        # Backup existing collections first
        if Path(PERSIST_DIR).exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety_backup = f"chroma_db_before_restore_{timestamp}"
            print(f"Creating safety backup: {safety_backup}.tar.gz")
            shutil.make_archive(safety_backup, 'gztar', '.', PERSIST_DIR)
        
        # Remove existing directory
        if Path(PERSIST_DIR).exists():
            shutil.rmtree(PERSIST_DIR)
        
        # Extract backup
        print(f"Restoring from: {backup_file}")
        shutil.unpack_archive(backup_file, '.')
        
        print(f"✅ Collections restored successfully")
        
    except Exception as e:
        print(f"❌ Error restoring collections: {e}")


def search_all_collections(query: str, k: int = 3):
    """Search across all collections."""
    print("\n" + "=" * 70)
    print(f"  Search All Collections")
    print(f"  Query: {query}")
    print("=" * 70 + "\n")
    
    try:
        # Load environment
        load_dotenv()
        
        # Get all collections
        client = chromadb.PersistentClient(path=PERSIST_DIR)
        collections = client.list_collections()
        
        if not collections:
            print("No collections found.")
            return
        
        # Search each collection
        for collection in collections:
            print(f"\n📚 {collection.name}")
            print("-" * 70)
            
            try:
                vector_store = CodeVectorStore(
                    collection_name=collection.name,
                    persist_dir=PERSIST_DIR
                )
                vector_store.load_index()
                results = vector_store.search(query, k=k)
                
                if results:
                    top_result = results[0]
                    print(f"   Top Result: {top_result['file_path']}")
                    print(f"   Score: {top_result['score']:.3f}")
                    print(f"   Preview: {top_result['content'][:150]}...")
                else:
                    print("   No results found")
                    
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
        
    except Exception as e:
        print(f"❌ Error searching collections: {e}")


def print_usage():
    """Print usage information."""
    print("""
Usage: python manage_collections.py <command> [options]

Commands:
  list                          List all collections
  stats <collection_name>       Get statistics for a collection
  delete <collection_name>      Delete a collection
  backup [backup_name]          Backup all collections
  restore <backup_file>         Restore collections from backup
  search <query> [k]            Search across all collections

Examples:
  python manage_collections.py list
  python manage_collections.py stats permanent_flask
  python manage_collections.py delete permanent_test
  python manage_collections.py backup my_backup
  python manage_collections.py restore chroma_db_backup_20260131.tar.gz
  python manage_collections.py search "authentication" 5
""")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        return 1
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_collections()
        
    elif command == "stats":
        if len(sys.argv) < 3:
            print("❌ Error: Collection name required")
            print("Usage: python manage_collections.py stats <collection_name>")
            return 1
        collection_name = sys.argv[2]
        get_collection_stats(collection_name)
        
    elif command == "delete":
        if len(sys.argv) < 3:
            print("❌ Error: Collection name required")
            print("Usage: python manage_collections.py delete <collection_name>")
            return 1
        collection_name = sys.argv[2]
        delete_collection(collection_name)
        
    elif command == "backup":
        backup_name = sys.argv[2] if len(sys.argv) > 2 else None
        backup_collections(backup_name)
        
    elif command == "restore":
        if len(sys.argv) < 3:
            print("❌ Error: Backup file required")
            print("Usage: python manage_collections.py restore <backup_file>")
            return 1
        backup_file = sys.argv[2]
        restore_collections(backup_file)
        
    elif command == "search":
        if len(sys.argv) < 3:
            print("❌ Error: Query required")
            print("Usage: python manage_collections.py search <query> [k]")
            return 1
        query = sys.argv[2]
        k = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        search_all_collections(query, k)
        
    else:
        print(f"❌ Unknown command: {command}")
        print_usage()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

