"""
Codebase Intelligence Assistant - Streamlit Web Interface
A beautiful, production-ready RAG-based code documentation assistant.
"""

import streamlit as st
import time
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.retrieval.vector_store import CodeVectorStore
from src.generation.qa_chain import CodeQAChain

# Constants
MODEL_OPTIONS = {
    "Claude Haiku 4.5 ⚡ (Fast & Cheap)": "claude-haiku-4-5-20251001",
    "Claude Sonnet 4.5 🧠 (Best Quality)": "claude-sonnet-4-5-20250929"
}

MODEL_COSTS = {
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0}
}

EXAMPLE_QUESTIONS = [
    "How does the file loader filter code files?",
    "Explain the chunking strategy used in this project",
    "What vector database is being used and why?",
    "How does the Q&A generation work?"
]

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


@st.cache_resource
def load_vector_store() -> CodeVectorStore:
    """
    Load the vector store (cached to avoid reloading on every interaction).
    
    Returns:
        Initialized CodeVectorStore instance
    """
    vector_store = CodeVectorStore(
        collection_name="codebase",
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
    st.session_state.trigger_response = True


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

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

if "current_repo" not in st.session_state:
    st.session_state.current_repo = "This Project (Codebase Intelligence)"

if "trigger_response" not in st.session_state:
    st.session_state.trigger_response = False

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("## 🤖 Codebase Intelligence")
    st.markdown("*Your AI-powered code documentation assistant*")
    
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
    st.markdown("### 📦 Repository")
    if st.session_state.vector_store_loaded and st.session_state.vector_store:
        try:
            stats = st.session_state.vector_store.get_stats()
            st.info(f"**{st.session_state.current_repo}**\n\n📊 Indexed: {stats['total_chunks']} chunks")
        except:
            st.info(f"**{st.session_state.current_repo}**")
    else:
        st.info(f"**{st.session_state.current_repo}**")
    
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
st.markdown("*Ask me anything about this codebase. I'll search through the code and provide detailed explanations with citations.*")
st.markdown("")

# ============================================================================
# VECTOR STORE INITIALIZATION
# ============================================================================

if not st.session_state.vector_store_loaded:
    try:
        with st.spinner("🔄 Loading vector database..."):
            st.session_state.vector_store = load_vector_store()
            stats = st.session_state.vector_store.get_stats()
            st.session_state.vector_store_loaded = True
            st.success(f"✅ Loaded {stats['total_chunks']} chunks from vector database")
    except Exception as e:
        st.error(f"""
        ❌ **Failed to load vector database**
        
        Error: {str(e)}
        
        **Troubleshooting:**
        1. Ensure the `chroma_db` directory exists
        2. Run the ingestion pipeline first to create the vector database
        3. Check that OPENAI_API_KEY is set in your .env file
        
        **To create the database, run:**
        ```bash
        python -c "from src.ingestion.loader import CodebaseLoader; from src.ingestion.chunker import CodeChunker; from src.retrieval.vector_store import CodeVectorStore; loader = CodebaseLoader('.'); docs = loader.load_files(); chunker = CodeChunker(); chunks = chunker.chunk_documents(docs); vs = CodeVectorStore(); vs.create_index(chunks)"
        ```
        """)
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
    st.markdown("### 💡 Try asking:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(EXAMPLE_QUESTIONS[0], key="ex1", use_container_width=True):
            handle_example_click(EXAMPLE_QUESTIONS[0])
            st.rerun()
        
        if st.button(EXAMPLE_QUESTIONS[2], key="ex3", use_container_width=True):
            handle_example_click(EXAMPLE_QUESTIONS[2])
            st.rerun()
    
    with col2:
        if st.button(EXAMPLE_QUESTIONS[1], key="ex2", use_container_width=True):
            handle_example_click(EXAMPLE_QUESTIONS[1])
            st.rerun()
        
        if st.button(EXAMPLE_QUESTIONS[3], key="ex4", use_container_width=True):
            handle_example_click(EXAMPLE_QUESTIONS[3])
            st.rerun()
    
    st.markdown("---")

# ============================================================================
# CHAT HISTORY DISPLAY
# ============================================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources for assistant messages
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander("📎 Sources"):
                unique_sources = list(set(message["sources"]))
                for source in unique_sources:
                    st.markdown(f"- 📄 `{source}`")

# ============================================================================
# CHAT INPUT AND MESSAGE HANDLING
# ============================================================================

# Handle chat input
if prompt := st.chat_input("Ask me anything about this codebase..."):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        try:
            # Search phase
            with st.spinner("🔍 Searching codebase..."):
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
            """)
            
            # Add error message to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"I encountered an error: {error_msg}",
                "sources": []
            })

# Handle example question trigger
if st.session_state.trigger_response:
    st.session_state.trigger_response = False
    st.rerun()

