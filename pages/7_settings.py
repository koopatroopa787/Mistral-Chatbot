import os
import streamlit as st
import json
from pathlib import Path
import sys

# Add the parent directory to the path so we can import the helper modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper_functions import load_config

# Page configuration
st.set_page_config(
    page_title="Settings - Mistral AI Assistant",
    page_icon="⚙️",
    layout="wide",
)

# Initialize Mistral client
@st.cache_resource
def check_api_key():
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        st.error("Missing API key. Please set your Mistral API Key on the Home page.")
        return False
    return True

# Check if the API key is available
if not check_api_key():
    st.stop()

# Load current configuration
config = load_config()

# Sidebar
with st.sidebar:
    st.title("Settings")
    st.markdown("Configure your Mistral AI Assistant")
    
    # Link back to chat
    st.markdown("---")
    st.markdown("[Back to Chat](/Chat)", unsafe_allow_html=True)

# Main content
st.title("Application Settings")

# Create tabs for different settings categories
tab1, tab2, tab3 = st.tabs(["General Settings", "Model Settings", "Advanced Settings"])

# Tab 1: General Settings
with tab1:
    st.header("General Settings")
    
    # Default model
    default_model = st.selectbox(
        "Default Model",
        options=["mistral-large-latest", "mistral-small-latest", "mistral-medium-latest"],
        index=["mistral-large-latest", "mistral-small-latest", "mistral-medium-latest"].index(config.get("model", "mistral-large-latest"))
    )
    
    # System prompt
    system_prompt = st.text_area(
        "Default System Prompt",
        value=config.get("system_prompt", "You are a helpful assistant that provides accurate and concise information."),
        height=100
    )
    
    # Max history length
    max_history_length = st.slider(
        "Maximum Conversation History Length",
        min_value=5,
        max_value=50,
        value=config.get("max_history_length", 10),
        help="Maximum number of messages to keep in conversation history"
    )

# Tab 2: Model Settings
with tab2:
    st.header("Model Settings")
    
    # Default temperature
    temperature = st.slider(
        "Default Temperature",
        min_value=0.0,
        max_value=1.0,
        value=config.get("temperature", 0.7),
        step=0.1,
        help="Higher values make output more random, lower values more deterministic"
    )
    
    # Default max tokens
    max_tokens = st.slider(
        "Default Max Tokens",
        min_value=100,
        max_value=4000,
        value=config.get("max_tokens", 1024),
        step=100,
        help="Maximum number of tokens in the response"
    )
    
    # Embedding model
    embedding_model = st.selectbox(
        "Embedding Model",
        options=["mistral-embed"],
        index=0,
        help="Model used for generating document embeddings"
    )

# Tab 3: Advanced Settings
with tab3:
    st.header("Advanced Settings")
    
    # Index type
    index_type = st.selectbox(
        "Index Type",
        options=["simple"],
        index=0,
        help="Type of document index to use"
    )
    
    # Document chunking settings
    st.subheader("Document Chunking")
    
    col1, col2 = st.columns(2)
    with col1:
        chunk_size = st.number_input(
            "Chunk Size (characters)",
            min_value=100,
            max_value=2000,
            value=500,
            step=50,
            help="Size of document chunks for indexing"
        )
    
    with col2:
        chunk_overlap = st.number_input(
            "Chunk Overlap (characters)",
            min_value=0,
            max_value=500,
            value=100,
            step=10,
            help="Overlap between document chunks"
        )

# Save settings button
if st.button("Save Settings"):
    # Update config with new values
    updated_config = {
        "model": default_model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "max_history_length": max_history_length,
        "index_type": index_type,
        "embedding_model": embedding_model,
        "system_prompt": system_prompt,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap
    }
    
    # Write to config file
    config_path = Path("config.json")
    try:
        with open(config_path, "w") as f:
            json.dump(updated_config, f, indent=4)
        
        st.success("Settings saved successfully!")
    except Exception as e:
        st.error(f"Error saving settings: {str(e)}")

# Reset to defaults button
if st.button("Reset to Defaults"):
    default_config = {
        "model": "mistral-large-latest",
        "temperature": 0.7,
        "max_tokens": 1024,
        "max_history_length": 10,
        "index_type": "simple",
        "embedding_model": "mistral-embed",
        "system_prompt": "You are a helpful assistant that provides accurate and concise information.",
        "chunk_size": 500,
        "chunk_overlap": 100
    }
    
    # Write default config to file
    config_path = Path("config.json")
    try:
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        
        st.success("Settings reset to defaults! Refresh the page to see changes.")
    except Exception as e:
        st.error(f"Error resetting settings: {str(e)}")

# Export and import settings
st.markdown("---")
st.subheader("Export/Import Settings")

col1, col2 = st.columns(2)

with col1:
    if st.button("Export Settings"):
        # Convert config to JSON string
        config_json = json.dumps(config, indent=4)
        
        # Create download button
        st.download_button(
            label="Download Settings",
            data=config_json,
            file_name="mistral_assistant_config.json",
            mime="application/json"
        )

with col2:
    uploaded_config = st.file_uploader("Import Settings", type=["json"])
    
    if uploaded_config and st.button("Apply Imported Settings"):
        try:
            # Read and parse the uploaded JSON
            imported_config = json.loads(uploaded_config.getvalue().decode("utf-8"))
            
            # Validate the imported config (basic check)
            required_keys = ["model", "temperature", "max_tokens"]
            
            if all(key in imported_config for key in required_keys):
                # Write to config file
                config_path = Path("config.json")
                with open(config_path, "w") as f:
                    json.dump(imported_config, f, indent=4)
                
                st.success("Imported settings applied successfully! Refresh the page to see changes.")
            else:
                st.error("The uploaded file is not a valid configuration file.")
        except Exception as e:
            st.error(f"Error importing settings: {str(e)}")

# Debug information
with st.expander("Debug Information"):
    st.subheader("Current Configuration")
    st.json(config)
    
    st.subheader("Environment")
    st.write(f"Python version: {sys.version}")
    st.write(f"Streamlit version: {st.__version__}")