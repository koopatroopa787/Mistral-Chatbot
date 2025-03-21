import streamlit as st
from PIL import Image
import os

# Page configuration
st.set_page_config(
    page_title="Mistral AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide the Streamlit menu and footer
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4B7BEC;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        color: #333;
        margin-bottom: 2rem;
    }
    .feature-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #F5F7FA;
        margin-bottom: 1rem;
        border-left: 4px solid #4B7BEC;
    }
    .feature-icon {
        font-size: 1.5rem;
        margin-right: 0.5rem;
    }
    .feature-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #333;
    }
    .feature-description {
        font-size: 1rem;
        color: #555;
        margin-top: 0.5rem;
    }
    .cta-button {
        background-color: #4B7BEC;
        color: white;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
        font-weight: 600;
        text-align: center;
        margin: 2rem 0;
        cursor: pointer;
    }
    .cta-button:hover {
        background-color: #3867D6;
    }
</style>
""", unsafe_allow_html=True)

# Check and set API key if it exists
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = False

if "MISTRAL_API_KEY" in os.environ:
    st.session_state.api_key_set = True

# Sidebar
with st.sidebar:
    st.title("Mistral AI Assistant")
    
    # API Key input
    if not st.session_state.api_key_set:
        st.subheader("Setup")
        api_key = st.text_input("Enter your Mistral AI API Key:", type="password")
        if st.button("Save API Key"):
            if api_key and api_key.strip():
                # In a real app, you would want to store this more securely
                os.environ["MISTRAL_API_KEY"] = api_key
                st.session_state.api_key_set = True
                st.success("API Key saved!")
                st.experimental_rerun()
            else:
                st.error("Please enter a valid API Key")
    else:
        st.success("API Key is set! ✅")
        if st.button("Clear API Key"):
            if "MISTRAL_API_KEY" in os.environ:
                del os.environ["MISTRAL_API_KEY"]
            st.session_state.api_key_set = False
            st.experimental_rerun()
    
    st.markdown("---")
    st.markdown("Navigate to different pages using the sidebar menu")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-header">Welcome to Mistral AI Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your intelligent document-aware chat companion</div>', unsafe_allow_html=True)
    
    # Features section
    st.markdown("### Key Features")
    
    # Feature cards
    feature_data = [
        {
            "icon": "💬",
            "title": "Intelligent Chat",
            "description": "Chat with a state-of-the-art language model powered by Mistral AI."
        },
        {
            "icon": "📚",
            "title": "Document Indexing & Search",
            "description": "Index your documents and get context-aware responses based on your data."
        },
        {
            "icon": "🔍",
            "title": "Semantic Search",
            "description": "Find information in your documents using natural language queries."
        },
        {
            "icon": "📊",
            "title": "Multi-step Analysis",
            "description": "Generate summaries, extract insights, and create reports from your conversations."
        }
    ]
    
    for feature in feature_data:
        st.markdown(f"""
        <div class="feature-card">
            <span class="feature-icon">{feature['icon']}</span>
            <span class="feature-title">{feature['title']}</span>
            <div class="feature-description">{feature['description']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Call to action
    if st.session_state.api_key_set:
        st.markdown(
            '<a href="/Chat" target="_self"><div class="cta-button">Start Chatting Now</div></a>', 
            unsafe_allow_html=True
        )
    else:
        st.info("Please set your Mistral API Key in the sidebar to start using the assistant.")

with col2:
    # Placeholder for an image or graphic
    st.markdown("### How It Works")
    st.markdown("""
    1. **Set up your API key** in the sidebar
    2. **Navigate to the Chat page** to start a conversation
    3. **Upload documents** for context-aware responses
    4. **Ask questions** about your documents or general topics
    5. **Save conversations** for future reference
    """)
    
    st.markdown("### Getting Started")
    if st.session_state.api_key_set:
        st.markdown("""
        You're all set up! Use the navigation menu in the sidebar to:
        - Chat with the AI Assistant
        - Manage your document index
        - Configure settings
        - View saved conversations
        """)
    else:
        st.markdown("""
        To get started:
        1. Enter your Mistral AI API Key in the sidebar
        2. Navigate to the Chat or other pages from the sidebar menu
        3. Start interacting with your AI assistant!
        """)

# Footer
st.markdown("---")
st.markdown("© 2025 Mistral AI Assistant | Powered by Mistral AI and Streamlit")