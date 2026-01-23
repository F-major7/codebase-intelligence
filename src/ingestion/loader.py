"""Repository file loader for codebase ingestion."""

import pathlib
from typing import List, Dict
import git


class CodebaseLoader:
    """Loads and filters code files from a repository.
    
    This class handles cloning repositories and loading code files with
    appropriate filtering for size, file type, and directory exclusions.
    """
    
    # Supported programming language file extensions
    ALLOWED_EXTENSIONS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs'}
    
    # Directories to skip during traversal
    SKIP_DIRECTORIES = {
        'node_modules', '__pycache__', '.git', 'venv', 'env', 
        'dist', 'build', '.next'
    }
    
    # File size constraints (in bytes)
    MIN_FILE_SIZE = 10
    MAX_FILE_SIZE = 100 * 1024  # 100KB
    
    def __init__(self, repo_path: str):
        """Initialize the codebase loader.
        
        Args:
            repo_path: Path to the repository directory
        """
        self.repo_path = pathlib.Path(repo_path).resolve()
        
    def clone_repo(self, repo_url: str, target_dir: str) -> str:
        """Clone a GitHub repository with shallow clone for speed.
        
        Args:
            repo_url: GitHub repository URL (e.g., https://github.com/user/repo)
            target_dir: Local directory to clone into
            
        Returns:
            Path to the cloned repository directory
            
        Raises:
            git.exc.GitCommandError: If cloning fails due to network or Git errors
        """
        target_path = pathlib.Path(target_dir).resolve()
        
        # Skip if directory already exists
        if target_path.exists():
            print(f"Directory {target_dir} already exists, skipping clone")
            return str(target_path)
        
        try:
            print(f"Cloning {repo_url} into {target_dir}...")
            # Shallow clone (depth=1) for faster cloning
            git.Repo.clone_from(
                repo_url, 
                target_path, 
                depth=1,
                single_branch=True
            )
            print(f"✅ Successfully cloned to {target_dir}")
            return str(target_path)
            
        except git.exc.GitCommandError as e:
            print(f"❌ Failed to clone repository: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error during cloning: {e}")
            raise
    
    def load_files(self) -> List[Dict[str, str]]:
        """Load and filter code files from the repository.
        
        Walks through the repository directory structure, applying filters for:
        - File extensions (programming languages only)
        - Directory exclusions (node_modules, .git, etc.)
        - Hidden files and directories
        - File size constraints
        - Encoding (UTF-8 only)
        
        Returns:
            List of dictionaries containing file metadata and content:
            - content: File text content
            - file_path: Relative path from repo root
            - file_name: Just the filename
            - extension: File extension
            
        Raises:
            FileNotFoundError: If repository path doesn't exist
        """
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {self.repo_path}")
        
        if not self.repo_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {self.repo_path}")
        
        documents = []
        candidates_count = 0
        
        # Walk through all files in the repository
        for file_path in self.repo_path.rglob('*'):
            # Skip if not a file
            if not file_path.is_file():
                continue
            
            candidates_count += 1
            
            # Skip hidden files and directories (starting with .)
            if any(part.startswith('.') for part in file_path.parts):
                continue
            
            # Skip excluded directories
            if any(skip_dir in file_path.parts for skip_dir in self.SKIP_DIRECTORIES):
                continue
            
            # Check file extension
            if file_path.suffix not in self.ALLOWED_EXTENSIONS:
                continue
            
            # Check file size constraints
            try:
                file_size = file_path.stat().st_size
                if file_size < self.MIN_FILE_SIZE or file_size > self.MAX_FILE_SIZE:
                    continue
            except (OSError, PermissionError) as e:
                print(f"⚠️  Cannot access {file_path}: {e}")
                continue
            
            # Read file content with UTF-8 encoding
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Get relative path from repository root
                relative_path = file_path.relative_to(self.repo_path)
                
                documents.append({
                    'content': content,
                    'file_path': str(relative_path),
                    'file_name': file_path.name,
                    'extension': file_path.suffix
                })
                
            except UnicodeDecodeError:
                # Skip files that aren't valid UTF-8 (likely binary files)
                continue
            except PermissionError as e:
                print(f"⚠️  Permission denied: {file_path}")
                continue
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
                continue
        
        print(f"Loaded {len(documents)} files from {candidates_count} total candidates")
        return documents
