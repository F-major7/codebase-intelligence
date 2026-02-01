#!/usr/bin/env python3
"""
Quick validation test for index_permanent_repos.py

This script performs basic validation without actually running the full indexing:
- Checks imports
- Validates configuration
- Tests helper functions
- Verifies environment setup
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    
    try:
        import os
        import shutil
        import tempfile
        from dotenv import load_dotenv
        import git
        from src.ingestion.loader import CodebaseLoader
        from src.ingestion.chunker import CodeChunker
        from src.retrieval.vector_store import CodeVectorStore
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_script_structure():
    """Test that the script file exists and is readable."""
    print("\nTesting script structure...")
    
    script_path = Path(__file__).parent / "index_permanent_repos.py"
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    print(f"✅ Script exists: {script_path}")
    
    # Check if executable
    if script_path.stat().st_mode & 0o111:
        print("✅ Script is executable")
    else:
        print("⚠️  Script is not executable (run: chmod +x index_permanent_repos.py)")
    
    return True


def test_configuration():
    """Test configuration values in the script."""
    print("\nTesting configuration...")
    
    # Import the script module
    import index_permanent_repos
    
    # Check REPOS_TO_INDEX
    if not hasattr(index_permanent_repos, 'REPOS_TO_INDEX'):
        print("❌ REPOS_TO_INDEX not found")
        return False
    
    repos = index_permanent_repos.REPOS_TO_INDEX
    print(f"✅ Found {len(repos)} repositories configured")
    
    # Validate each repo config
    required_keys = {'name', 'url', 'collection_name'}
    for repo in repos:
        missing_keys = required_keys - set(repo.keys())
        if missing_keys:
            print(f"❌ Repository config missing keys: {missing_keys}")
            return False
        print(f"   - {repo['name']}: {repo['collection_name']}")
    
    # Check other config
    if hasattr(index_permanent_repos, 'PERSIST_DIR'):
        print(f"✅ Persist directory: {index_permanent_repos.PERSIST_DIR}")
    
    if hasattr(index_permanent_repos, 'CHUNK_SIZE'):
        print(f"✅ Chunk size: {index_permanent_repos.CHUNK_SIZE}")
    
    if hasattr(index_permanent_repos, 'CHUNK_OVERLAP'):
        print(f"✅ Chunk overlap: {index_permanent_repos.CHUNK_OVERLAP}")
    
    return True


def test_helper_functions():
    """Test that helper functions are defined."""
    print("\nTesting helper functions...")
    
    import index_permanent_repos
    
    required_functions = [
        'print_header',
        'clone_repository',
        'index_repository',
        'index_current_project',
        'main'
    ]
    
    for func_name in required_functions:
        if not hasattr(index_permanent_repos, func_name):
            print(f"❌ Function not found: {func_name}")
            return False
        print(f"✅ Function defined: {func_name}")
    
    return True


def test_environment():
    """Test environment setup."""
    print("\nTesting environment...")
    
    from dotenv import load_dotenv
    import os
    
    # Load .env file
    load_dotenv()
    
    # Check for API key (don't print it)
    if os.getenv("OPENAI_API_KEY"):
        print("✅ OPENAI_API_KEY is set")
    else:
        print("⚠️  OPENAI_API_KEY not set (required for actual indexing)")
    
    return True


def test_dependencies():
    """Test that required packages are installed."""
    print("\nTesting dependencies...")
    
    # Map package names to their import names
    required_packages = {
        'langchain': 'langchain',
        'langchain_openai': 'langchain_openai',
        'langchain_community': 'langchain_community',
        'chromadb': 'chromadb',
        'gitpython': 'git',
        'python-dotenv': 'dotenv'
    }
    
    all_installed = True
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name} installed")
        except ImportError:
            print(f"❌ {package_name} not installed")
            all_installed = False
    
    return all_installed


def main():
    """Run all tests."""
    print("=" * 70)
    print("  Index Script Validation Tests")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Script Structure", test_script_structure),
        ("Configuration", test_configuration),
        ("Helper Functions", test_helper_functions),
        ("Environment", test_environment),
        ("Dependencies", test_dependencies)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("  Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All validation tests passed!")
        print("The script is ready to run: python index_permanent_repos.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

