import os
import streamlit as st
from mistralai import Mistral
import time
from pathlib import Path
from helper_functions import setup_logging, load_config
from index_functions import create_index, search_index, load_index

# Setup
logger = setup_logging()
config = load_config()

# Initialize Mistral client
@st.cache_resource
def get_mistral_client():
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        st.error("Please set your Mistral API Key in the Home page or as an environment variable.")
        return None
    return Mistral(api_key=api_key)

# Page configuration
st.set_page_config(
    page_title="Mistral AI Chatbot",
    page_icon="🤖",
    layout="wide",
)

# Sidebar
st.sidebar.title("Mistral AI Chatbot")
st.sidebar.markdown("A chatbot powered by Mistral AI with document indexing capabilities.")

# Model selection
model_options = [
    "mistral-large-latest",
    "mistral-small-latest",
    "mistral-medium-latest"
]
selected_model = st.sidebar.selectbox("Select Model", model_options, index=0)

# Temperature slider
temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1, 
                              help="Higher values make output more random, lower values more deterministic")

# Max tokens slider
max_tokens = st.sidebar.slider("Max Tokens", min_value=100, max_value=4000, value=1000, step=100, 
                             help="Maximum number of tokens in the response")

# Document indexing
st.sidebar.markdown("---")
st.sidebar.subheader("Document Indexing")

# File uploader for document indexing
uploaded_files = st.sidebar.file_uploader("Upload documents for indexing", accept_multiple_files=True, type=["txt", "md", "pdf", "csv", "json", "py", "js", "html", "css"])

if uploaded_files:
    if st.sidebar.button("Index Uploaded Documents"):
        # Create a temporary directory for uploaded files
        temp_dir = Path("uploaded_files")
        temp_dir.mkdir(exist_ok=True)
        
        # Save uploaded files to temp directory
        for uploaded_file in uploaded_files:
            file_path = temp_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        # Index the files
        with st.sidebar.status("Indexing documents..."):
            create_index(str(temp_dir), logger)
        
        st.sidebar.success(f"Indexed {len(uploaded_files)} documents successfully!")

# Folder path for indexing
folder_path = st.sidebar.text_input("Or enter a folder path to index")
if folder_path:
    if st.sidebar.button("Index Folder"):
        with st.sidebar.status("Indexing documents..."):
            create_index(folder_path, logger)
        st.sidebar.success(f"Indexed folder successfully!")

# Load index status
if st.sidebar.button("Check Index Status"):
    if load_index():
        st.sidebar.success("Index is loaded and ready to use.")
    else:
        st.sidebar.warning("No index found. Please index documents first.")

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
st.title("Chat with Mistral AI")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input for user message
prompt = st.chat_input("Ask anything...")

# Handle user input
if prompt:
    # Check for special commands
    if prompt.lower().startswith("search:"):
        query = prompt[7:].strip()
        with st.status("Searching documents..."):
            context = search_index(query, logger)
        
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display search results
        if context:
            with st.chat_message("assistant"):
                st.markdown("**Search Results:**\n\n" + context)
            st.session_state.messages.append({"role": "assistant", "content": "**Search Results:**\n\n" + context})
        else:
            with st.chat_message("assistant"):
                st.markdown("No relevant documents found. Please make sure you've indexed documents.")
            st.session_state.messages.append({"role": "assistant", "content": "No relevant documents found. Please make sure you've indexed documents."})
    
    else:
        # Regular chat - add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Check if we have indexed content to add as context
        search_context = ""
        if load_index():
            with st.status("Searching for relevant context..."):
                search_context = search_index(prompt, logger, top_k=2)
        
        # Prepare messages including history and context
        messages = []
        
        # Add system message with context if available
        if search_context:
            messages.append({
                "role": "system", 
                "content": f"You are a helpful assistant with access to the following information. Use it to inform your responses when relevant:\n\n{search_context}"
            })
        
        # Add chat history (excluding the latest user message which we'll add separately)
        for message in st.session_state.messages[:-1]:
            messages.append({"role": message["role"], "content": message["content"]})
        
        # Add the latest user message
        messages.append({"role": "user", "content": prompt})
        
        # Get response from Mistral
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Get client
            client = get_mistral_client()
            
            try:
                # Make API call
                response = client.chat.complete(
                    model=selected_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                full_response = response.choices[0].message.content
                
                # Simulate streaming for better UX
                for chunk in full_response.split():
                    full_response_so_far = full_response[:full_response.find(chunk) + len(chunk)]
                    message_placeholder.markdown(full_response_so_far + "▌")
                    time.sleep(0.01)
                
                # Final display
                message_placeholder.markdown(full_response)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                full_response = f"I encountered an error: {str(e)}"
                message_placeholder.markdown(full_response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

# Add helpful information
with st.expander("Tips & Commands"):
    st.markdown("""
    ### How to use this chatbot:
    
    - **Regular chat**: Simply type your message and press Enter.
    - **Search indexed documents**: Type `search: your query` to search the indexed documents.
    - **Add documents**: Use the sidebar to upload files or specify a folder path for indexing.
    
    ### Model Settings:
    
    You can adjust the model, temperature, and max tokens in the sidebar to control the AI's responses.
    
    ### Document Indexing:
    
    1. Upload files or provide a folder path in the sidebar
    2. Click "Index Uploaded Documents" or "Index Folder"
    3. Wait for indexing to complete
    4. Your documents will be used to provide context for chat responses
    """)
