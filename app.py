"""
Codebase Intelligence Assistant (codeBIAS) - Streamlit Web Interface
A beautiful, production-ready RAG-based code documentation assistant.
"""

import streamlit as st
import time
from pathlib import Path
import sys
from dotenv import load_dotenv
import uuid
import re
import tempfile
import shutil
import git

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.retrieval.vector_store import CodeVectorStore
from src.generation.qa_chain import CodeQAChain
from src.ingestion.loader import CodebaseLoader
from src.ingestion.chunker import CodeChunker

# Constants
MODEL_OPTIONS = {
    "Claude Haiku 4.5 (Fast & Cheap)": "claude-haiku-4-5-20251001",
    "Claude Sonnet 4.5 (Best Quality)": "claude-sonnet-4-5-20250929"
}

MODEL_COSTS = {
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0}
}

# Repository mapping
REPO_MAP = {
    "Flask Web Framework": "permanent_flask",
    "FastAPI Framework": "permanent_fastapi",
    "Django Framework": "permanent_django",
    "RAG Project (This Codebase)": "permanent_rag_project"
}

# Example questions per repository
EXAMPLE_QUESTIONS_BY_REPO = {
    "permanent_flask": [
        "How does Flask handle URL routing?",
        "Explain the Flask application context",
        "How do Flask blueprints work?",
        "What is the request/response cycle in Flask?"
    ],
    "permanent_fastapi": [
        "How to create async endpoints in FastAPI?",
        "Explain dependency injection in FastAPI",
        "How does FastAPI handle request validation?",
        "What are path operations in FastAPI?"
    ],
    "permanent_django": [
        "How does Django ORM work?",
        "Explain Django middleware",
        "How to create custom management commands?",
        "What is the Django request/response cycle?"
    ],
    "permanent_rag_project": [
        "How does the file loader filter code files?",
        "Explain the chunking strategy used in this project",
        "What vector database is being used and why?",
        "How does the Q&A generation work?"
    ]
}

# ============================================================================
# STREAMLIT CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Codebase Intelligence Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS STYLING
# ============================================================================

st.markdown("""
<style>
    /* Main background gradient */
    .stApp {
        background: linear-gradient(135deg, #1a0b2e 0%, #16213e 100%);
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    }
    
    /* Chat container */
    .stChatMessage {
        background: rgba(45, 45, 45, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* User messages */
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, #4158D0 0%, #C850C0 100%);
        color: white;
        margin-left: auto;
        max-width: 80%;
    }
    
    /* Assistant messages */
    .stChatMessage[data-testid="assistant-message"] {
        background: rgba(45, 45, 45, 0.8);
        color: #e0e0e0;
        margin-right: auto;
        max-width: 85%;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #1e1e1e;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    section[data-testid="stSidebar"] > div {
        padding: 20px;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background: #1e1e1e !important;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    code {
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.5;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4158D0 0%, #C850C0 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 12px rgba(200, 80, 192, 0.4);
    }
    
    /* Example question pills */
    .example-pill {
        background: rgba(65, 88, 208, 0.2);
        border: 1px solid rgba(65, 88, 208, 0.5);
        border-radius: 20px;
        padding: 10px 20px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-block;
        color: #e0e0e0;
        font-size: 14px;
    }
    
    .example-pill:hover {
        background: rgba(65, 88, 208, 0.4);
        border-color: rgba(65, 88, 208, 0.8);
        transform: translateY(-2px);
    }
    
    /* Headers */
    h1 {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #4158D0 0%, #C850C0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 10px;
    }
    
    h2 {
        font-size: 24px;
        color: #ffffff;
        font-weight: 600;
    }
    
    h3 {
        font-size: 18px;
        color: #e0e0e0;
        font-weight: 500;
    }
    
    /* Text */
    p, li, span {
        color: #e0e0e0;
        line-height: 1.6;
        font-size: 14px;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #00ff88;
        font-size: 24px;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: #e0e0e0;
        font-size: 14px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(65, 88, 208, 0.2);
        border-radius: 8px;
        color: #e0e0e0;
        font-weight: 500;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: #C850C0;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #4158D0;
    }
    
    /* Chat input */
    .stChatInput {
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(45, 45, 45, 0.6);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #C850C0 !important;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: rgba(0, 255, 136, 0.1);
        border-left: 4px solid #00ff88;
        color: #00ff88;
    }
    
    .stError {
        background: rgba(255, 75, 92, 0.1);
        border-left: 4px solid #ff4b5c;
        color: #ff4b5c;
    }
    
    /* Info messages */
    .stInfo {
        background: rgba(65, 88, 208, 0.1);
        border-left: 4px solid #4158D0;
        color: #e0e0e0;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .stChatMessage {
            max-width: 95% !important;
        }
        
        h1 {
            font-size: 24px;
        }
        
        h2 {
            font-size: 20px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def estimate_cost(model: str, num_tokens: int) -> float:
    """
    Estimate the cost of an API call based on model and token count.
    
    Args:
        model: Model identifier
        num_tokens: Estimated number of input tokens
        
    Returns:
        Estimated cost in dollars
    """
    if model not in MODEL_COSTS:
        return 0.0
    
    costs = MODEL_COSTS[model]
    input_cost = (num_tokens * costs["input"]) / 1_000_000
    output_cost = (num_tokens * 0.3 * costs["output"]) / 1_000_000  # 0.3 = output/input ratio
    
    return input_cost + output_cost


def load_vector_store(collection_name: str) -> CodeVectorStore:
    """
    Load the vector store for a specific collection.
    
    Args:
        collection_name: Name of the ChromaDB collection to load
        
    Returns:
        Initialized CodeVectorStore instance
    """
    vector_store = CodeVectorStore(
        collection_name=collection_name,
        persist_dir="./chroma_db"
    )
    vector_store.load_index()
    return vector_store


def stream_response(text: str, placeholder) -> None:
    """
    Display text with typewriter effect.
    
    Args:
        text: Complete text to display
        placeholder: Streamlit placeholder to update
    """
    words = text.split()
    displayed_text = ""
    
    for word in words:
        displayed_text += word + " "
        placeholder.markdown(displayed_text + "▌")
        time.sleep(0.02)
    
    # Show final text without cursor
    placeholder.markdown(text)


def handle_example_click(question: str) -> None:
    """
    Handle example question button click.
    
    Args:
        question: The example question text
    """
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })


def is_valid_github_url(url: str) -> bool:
    """
    Validate GitHub repository URL format.
    
    Args:
        url: GitHub URL to validate
        
    Returns:
        True if valid GitHub URL, False otherwise
    """
    pattern = r'https://github\.com/[\w-]+/[\w.-]+'
    return bool(re.match(pattern, url))


def extract_repo_info(url: str) -> tuple:
    """
    Extract owner and repo name from GitHub URL.
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo_name)
    """
    # Remove trailing slash and .git if present
    url = url.rstrip('/').replace('.git', '')
    parts = url.split('/')
    owner = parts[-2]
    repo_name = parts[-1]
    return owner, repo_name


def index_github_repo(github_url: str, session_id: str) -> dict:
    """
    Clone and index a GitHub repository.
    
    Args:
        github_url: GitHub repository URL
        session_id: Current session ID
        
    Returns:
        Dictionary with status, message, collection_name, and chunk_count
    """
    temp_dir = None
    
    try:
        # Extract repo info
        owner, repo_name = extract_repo_info(github_url)
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"rag_temp_{session_id}_{repo_name}_")
        
        # Clone repository
        try:
            git.Repo.clone_from(
                github_url,
                temp_dir,
                depth=1,
                single_branch=True
            )
        except git.exc.GitCommandError as e:
            error_msg = str(e)
            if "not found" in error_msg.lower() or "repository not found" in error_msg.lower():
                return {
                    "status": "error",
                    "message": "Repository not found. Please check the URL."
                }
            elif "authentication" in error_msg.lower() or "permission denied" in error_msg.lower():
                return {
                    "status": "error",
                    "message": "Cannot access private repositories. Use public repos only."
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to clone repository: {error_msg}"
                }
        
        # Load files
        loader = CodebaseLoader(temp_dir)
        documents = loader.load_files()
        
        if not documents:
            return {
                "status": "error",
                "message": "Repository appears to be empty or has no supported code files."
            }
        
        # Chunk documents
        chunker = CodeChunker(chunk_size=1000, chunk_overlap=200)
        chunks = chunker.chunk_documents(documents)
        
        if not chunks:
            return {
                "status": "error",
                "message": "No chunks created from repository files."
            }
        
        # Create collection name
        collection_name = f"session_{session_id}_{repo_name}"
        
        # Create vector store and index
        vector_store = CodeVectorStore(
            collection_name=collection_name,
            persist_dir="./chroma_db"
        )
        vector_store.create_index(chunks)
        
        return {
            "status": "success",
            "message": f"Successfully indexed {repo_name}",
            "collection_name": collection_name,
            "repo_name": repo_name,
            "owner": owner,
            "chunk_count": len(chunks)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }
    
    finally:
        # Cleanup temporary directory
        if temp_dir and Path(temp_dir).exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Failed to cleanup temp directory: {e}")


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

# Generate unique session ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "claude-haiku-4-5-20251001"

if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0

if "vector_store_loaded" not in st.session_state:
    st.session_state.vector_store_loaded = False

if "selected_repo" not in st.session_state:
    st.session_state.selected_repo = "permanent_rag_project"

if "selected_repo_display" not in st.session_state:
    st.session_state.selected_repo_display = "RAG Project (This Codebase)"

if "trigger_response" not in st.session_state:
    st.session_state.trigger_response = False

if "repo_switched" not in st.session_state:
    st.session_state.repo_switched = False

if "user_repos" not in st.session_state:
    st.session_state.user_repos = []

if "is_indexing" not in st.session_state:
    st.session_state.is_indexing = False

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("## 🤖 Codebase Intelligence")
    st.markdown("*Your AI-powered code documentation assistant*")
    
    st.markdown("---")
    
    # Repository selector
    st.markdown("### 📦 Select Repository")
    
    # Build combined repo map
    combined_repo_options = list(REPO_MAP.keys())
    combined_repo_map = REPO_MAP.copy()
    
    # Add user repos if any
    if st.session_state.user_repos:
        combined_repo_options.append("--- Your Repositories ---")
        for display_name, collection_name in st.session_state.user_repos:
            combined_repo_options.append(display_name)
            combined_repo_map[display_name] = collection_name
    
    # Find current index
    try:
        current_index = combined_repo_options.index(st.session_state.selected_repo_display)
    except ValueError:
        current_index = 3  # Default to RAG Project
    
    selected_display_name = st.selectbox(
        "Choose a codebase to query:",
        options=combined_repo_options,
        index=current_index,
        key="repo_selector"
    )
    
    # Skip if separator is selected
    if selected_display_name != "--- Your Repositories ---":
        selected_collection = combined_repo_map[selected_display_name]
        
        # Check if repository selection changed
        if selected_collection != st.session_state.selected_repo:
            st.session_state.selected_repo = selected_collection
            st.session_state.selected_repo_display = selected_display_name
            st.session_state.vector_store_loaded = False
            st.session_state.vector_store = None
            st.session_state.messages = []  # Clear conversation history
            st.session_state.repo_switched = True
            st.rerun()
    
    st.markdown("---")
    
    # GitHub Repository Indexing
    st.markdown("### 🔗 Index GitHub Repo")
    st.markdown("*Paste any public GitHub repo URL to analyze it*")
    
    github_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/owner/repo",
        disabled=st.session_state.is_indexing,
        key="github_url_input"
    )
    
    index_button = st.button(
        "🚀 Index Repository",
        disabled=st.session_state.is_indexing or not github_url,
        use_container_width=True
    )
    
    if index_button:
        # Validate URL
        if not github_url:
            st.error("Please enter a GitHub URL")
        elif not is_valid_github_url(github_url):
            st.error("❌ Invalid GitHub URL format. Use: https://github.com/owner/repo")
        else:
            st.session_state.is_indexing = True
            
            # Show progress
            with st.spinner("🔄 Cloning repository..."):
                time.sleep(0.5)  # Brief pause for UI feedback
            
            with st.spinner("📂 Loading files..."):
                time.sleep(0.3)
            
            with st.spinner("✂️ Chunking code..."):
                time.sleep(0.3)
            
            with st.spinner("🧠 Generating embeddings... (this may take 1-2 minutes)"):
                result = index_github_repo(github_url, st.session_state.session_id)
            
            st.session_state.is_indexing = False
            
            if result["status"] == "success":
                # Add to user repos
                display_name = f"{result['owner']}/{result['repo_name']}"
                st.session_state.user_repos.append((display_name, result["collection_name"]))
                
                # Switch to newly indexed repo
                st.session_state.selected_repo = result["collection_name"]
                st.session_state.selected_repo_display = display_name
                st.session_state.vector_store_loaded = False
                st.session_state.vector_store = None
                st.session_state.messages = []
                st.session_state.repo_switched = True
                
                st.success(f"✅ Successfully indexed **{result['repo_name']}**! ({result['chunk_count']:,} chunks)")
                st.info("💡 You can now ask questions about this repository!")
                time.sleep(2)
                st.rerun()
            else:
                st.error(f"❌ {result['message']}")
    
    if st.session_state.is_indexing:
        st.info("⏳ Indexing in progress... This usually takes 1-3 minutes depending on repo size.")
    
    st.markdown("---")
    
    # Model selector
    st.markdown("### ⚙️ Settings")
    selected_model_name = st.selectbox(
        "Model",
        options=list(MODEL_OPTIONS.keys()),
        index=0 if st.session_state.selected_model == "claude-haiku-4-5-20251001" else 1
    )
    
    new_model = MODEL_OPTIONS[selected_model_name]
    if new_model != st.session_state.selected_model:
        st.session_state.selected_model = new_model
        st.session_state.qa_chain = None  # Force reinit
    
    # Repository info
    st.markdown("### 📊 Current Repository")
    if st.session_state.vector_store_loaded and st.session_state.vector_store:
        try:
            stats = st.session_state.vector_store.get_stats()
            st.info(f"**{st.session_state.selected_repo_display}**\n\n📦 Indexed: {stats['total_chunks']:,} chunks")
        except:
            st.info(f"**{st.session_state.selected_repo_display}**")
    else:
        st.info(f"**{st.session_state.selected_repo_display}**\n\n⏳ Loading...")
    
    st.markdown("---")
    
    # Statistics
    st.markdown("### 📊 Statistics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Messages", len(st.session_state.messages))
    with col2:
        st.metric("Cost", f"${st.session_state.total_cost:.4f}")
    
    st.metric("Model", selected_model_name.split()[0] + " " + selected_model_name.split()[1])
    
    st.markdown("---")
    
    # Clear conversation button
    if st.button("🗑️ Clear Conversation", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.total_cost = 0.0
        st.rerun()
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style='text-align: center; color: #888; font-size: 12px; margin-top: 20px;'>
        Made with ❤️ using Claude & Streamlit<br>
        <span style='color: #C850C0;'>Built by PS2</span>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# MAIN AREA
# ============================================================================

# Header
st.markdown("# 🤖 Codebase Intelligence Assistant")
st.markdown("*Ask me anything about the selected codebase. I'll search through the code and provide detailed explanations with citations.*")

# Show current repository prominently
st.markdown(f"### 📦 Querying: **{st.session_state.selected_repo_display}**")
st.markdown("")

# Show repository switch notification
if st.session_state.repo_switched:
    st.success(f"✅ Switched to **{st.session_state.selected_repo_display}**. Previous conversation cleared.")
    st.session_state.repo_switched = False

# ============================================================================
# VECTOR STORE INITIALIZATION
# ============================================================================

if not st.session_state.vector_store_loaded:
    try:
        with st.spinner(f"🔄 Loading vector database for {st.session_state.selected_repo_display}..."):
            st.session_state.vector_store = load_vector_store(st.session_state.selected_repo)
            stats = st.session_state.vector_store.get_stats()
            st.session_state.vector_store_loaded = True
            st.success(f"✅ Loaded {stats['total_chunks']:,} chunks from **{st.session_state.selected_repo_display}**")
    except Exception as e:
        st.error(f"""
        ❌ **Failed to load vector database for {st.session_state.selected_repo_display}**
        
        Error: {str(e)}
        
        **Troubleshooting:**
        1. Ensure the collection `{st.session_state.selected_repo}` exists in `chroma_db`
        2. Run the indexing script to create permanent repositories:
           ```bash
           python index_permanent_repos.py
           ```
        3. Check that OPENAI_API_KEY is set in your .env file
        4. Try selecting a different repository from the sidebar
        
        **Available collections should include:**
        - permanent_flask
        - permanent_fastapi
        - permanent_django
        - permanent_rag_project
        """)
        
        # Provide fallback option
        if st.button("🔄 Try RAG Project (Default)"):
            st.session_state.selected_repo = "permanent_rag_project"
            st.session_state.selected_repo_display = "RAG Project (This Codebase)"
            st.session_state.vector_store_loaded = False
            st.rerun()
        
        st.stop()

# Initialize QA chain if needed
if st.session_state.qa_chain is None:
    try:
        st.session_state.qa_chain = CodeQAChain(model=st.session_state.selected_model)
    except Exception as e:
        st.error(f"""
        ❌ **Failed to initialize Q&A chain**
        
        Error: {str(e)}
        
        **Troubleshooting:**
        1. Ensure ANTHROPIC_API_KEY is set in your .env file
        2. Check that you have access to the selected Claude model
        3. Verify your API key has sufficient credits
        """)
        st.stop()

# ============================================================================
# EXAMPLE QUESTIONS
# ============================================================================

if len(st.session_state.messages) == 0:
    # Only show example questions for permanent repos (not user-indexed repos)
    if st.session_state.selected_repo in EXAMPLE_QUESTIONS_BY_REPO:
        st.markdown("### 💡 Try asking:")
        
        # Get example questions for current repository
        current_examples = EXAMPLE_QUESTIONS_BY_REPO[st.session_state.selected_repo]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(current_examples[0], key="ex1", use_container_width=True):
                handle_example_click(current_examples[0])
                st.rerun()
            
            if st.button(current_examples[2], key="ex3", use_container_width=True):
                handle_example_click(current_examples[2])
                st.rerun()
        
        with col2:
            if st.button(current_examples[1], key="ex2", use_container_width=True):
                handle_example_click(current_examples[1])
                st.rerun()
            
            if st.button(current_examples[3], key="ex4", use_container_width=True):
                handle_example_click(current_examples[3])
                st.rerun()
        
        st.markdown("---")

# ============================================================================
# CHAT INPUT AND MESSAGE HANDLING
# ============================================================================

# Check if there's an unanswered user message (from example button click)
needs_response = False
prompt = None

if len(st.session_state.messages) > 0:
    last_message = st.session_state.messages[-1]
    if last_message["role"] == "user":
        needs_response = True
        prompt = last_message["content"]

# Handle chat input (only if no pending response)
if not needs_response:
    if prompt := st.chat_input(f"Ask me anything about {st.session_state.selected_repo_display}..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        needs_response = True

# ============================================================================
# CHAT HISTORY DISPLAY
# ============================================================================

# Display all messages except the last one if it needs a response
messages_to_display = st.session_state.messages[:-1] if needs_response else st.session_state.messages

for message in messages_to_display:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources for assistant messages
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander("📎 Sources"):
                unique_sources = list(set(message["sources"]))
                for source in unique_sources:
                    st.markdown(f"- 📄 `{source}`")

# ============================================================================
# PROCESS PENDING MESSAGE
# ============================================================================

# Process the message if needed
if needs_response and prompt:
    # Display the user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        try:
            # Search phase
            with st.spinner(f"🔍 Searching {st.session_state.selected_repo_display}..."):
                retrieved_chunks = st.session_state.vector_store.search(prompt, k=5)
            
            st.info(f"Found {len(retrieved_chunks)} relevant chunks")
            
            # Generation phase
            with st.spinner("🧠 Generating answer..."):
                result = st.session_state.qa_chain.ask(prompt, retrieved_chunks)
            
            # Stream response with typewriter effect
            response_placeholder = st.empty()
            stream_response(result['answer'], response_placeholder)
            
            # Show sources
            if result['sources']:
                with st.expander("📎 Sources"):
                    unique_sources = list(set(result['sources']))
                    for source in unique_sources:
                        st.markdown(f"- 📄 `{source}`")
            
            # Add assistant message to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": result['answer'],
                "sources": result['sources']
            })
            
            # Update cost
            estimated_tokens = len(prompt.split()) * 1.3 + len(result['answer'].split()) * 1.3
            cost = estimate_cost(st.session_state.selected_model, int(estimated_tokens))
            st.session_state.total_cost += cost
            
            # Rerun to show the updated conversation
            st.rerun()
            
        except Exception as e:
            error_msg = str(e)
            st.error(f"""
            ❌ **Error generating response**
            
            {error_msg}
            
            **Troubleshooting:**
            - Check your ANTHROPIC_API_KEY is valid
            - Ensure you have API credits available
            - Try switching to a different model
            - Verify your internet connection
            - Ensure the selected repository is properly indexed
            """)
            
            # Add error message to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"I encountered an error: {error_msg}",
                "sources": []
            })

