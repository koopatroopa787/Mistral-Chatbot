import streamlit as st
import os
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import load_settings, save_settings
from providers import ProviderFactory

# Page configuration
st.set_page_config(
    page_title="Universal AI Chatbot",
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.3rem;
        font-weight: 400;
        color: #555;
        margin-bottom: 2rem;
    }
    .feature-card {
        padding: 1.5rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .feature-icon {
        font-size: 1.8rem;
        margin-right: 0.5rem;
    }
    .feature-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #333;
    }
    .feature-description {
        font-size: 0.95rem;
        color: #666;
        margin-top: 0.5rem;
        line-height: 1.5;
    }
    .provider-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        background-color: #667eea;
        color: white;
        font-size: 0.85rem;
        margin: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize settings
if "settings" not in st.session_state:
    st.session_state.settings = load_settings()

settings = st.session_state.settings

# Sidebar
with st.sidebar:
    st.title("🤖 Universal AI Chatbot")
    st.markdown("**Multi-Model AI Assistant**")

    st.markdown("---")

    # Provider setup
    st.subheader("🔑 AI Provider Setup")

    available_providers = ProviderFactory.get_available_providers()

    for provider_name in available_providers:
        with st.expander(f"**{provider_name.upper()}** Configuration"):
            # Check for API key in environment or settings
            api_key_env = f"{provider_name.upper()}_API_KEY"
            current_key = os.getenv(api_key_env) or ""

            if provider_name in settings.providers and settings.providers[provider_name].api_key:
                current_key = settings.providers[provider_name].api_key

            api_key = st.text_input(
                f"API Key",
                value=current_key,
                type="password",
                key=f"{provider_name}_key",
                help=f"Enter your {provider_name.upper()} API key"
            )

            # Get default model based on provider
            default_models = {
                "openai": "gpt-4o-mini",
                "anthropic": "claude-3-5-sonnet-20241022",
                "mistral": "mistral-large-latest",
                "google": "gemini-1.5-flash"
            }

            default_model = st.text_input(
                "Default Model",
                value=settings.providers.get(provider_name, None).default_model if provider_name in settings.providers else default_models.get(provider_name, ""),
                key=f"{provider_name}_model"
            )

            enabled = st.checkbox(
                "Enable this provider",
                value=provider_name in settings.providers and settings.providers[provider_name].enabled,
                key=f"{provider_name}_enabled"
            )

            if st.button(f"Save {provider_name.upper()}", key=f"{provider_name}_save"):
                if api_key and default_model:
                    settings.add_provider(provider_name, api_key, default_model, enabled)
                    save_settings(settings)
                    st.success(f"{provider_name.upper()} configured!")
                    st.rerun()
                else:
                    st.error("Please provide both API key and default model")

    st.markdown("---")

    # Show enabled providers
    enabled_providers = settings.get_enabled_providers()
    if enabled_providers:
        st.success(f"✅ {len(enabled_providers)} provider(s) enabled")
        for prov in enabled_providers:
            st.markdown(f'<span class="provider-badge">{prov}</span>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ No providers enabled")

    st.markdown("---")
    st.markdown("Navigate using the sidebar menu")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-header">Universal AI Chatbot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">One interface for all your favorite AI models</div>', unsafe_allow_html=True)

    # Features section
    st.markdown("### ✨ Key Features")

    # Feature cards
    feature_data = [
        {
            "icon": "🎯",
            "title": "Multi-Model Support",
            "description": "Switch seamlessly between OpenAI, Anthropic Claude, Google Gemini, Mistral AI, and more providers."
        },
        {
            "icon": "🔌",
            "title": "MCP Server Integration",
            "description": "Connect to Model Context Protocol (MCP) servers for enhanced capabilities and custom tools."
        },
        {
            "icon": "📚",
            "title": "Document Intelligence",
            "description": "Index and search through your documents with semantic understanding for context-aware responses."
        },
        {
            "icon": "💬",
            "title": "Advanced Conversations",
            "description": "Real streaming responses, conversation history, export/import, and structured flows."
        },
        {
            "icon": "⚙️",
            "title": "Highly Configurable",
            "description": "Customize models, parameters, prompts, and behaviors to match your needs."
        },
        {
            "icon": "📊",
            "title": "Response Grading & Reports",
            "description": "Evaluate AI responses, generate conversation reports, and analyze performance."
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
    if enabled_providers:
        st.markdown("### 🚀 Ready to Get Started!")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("💬 Start Chatting", use_container_width=True):
                st.switch_page("pages/1_chat.py")
        with col_b:
            if st.button("📚 Manage Documents", use_container_width=True):
                st.switch_page("pages/4_document_index.py")
        with col_c:
            if st.button("⚙️ Settings", use_container_width=True):
                st.switch_page("pages/7_settings.py")
    else:
        st.info("👈 Please configure at least one AI provider in the sidebar to get started.")

with col2:
    st.markdown("### 🎨 Supported Providers")

    provider_info = {
        "openai": {"name": "OpenAI", "models": "GPT-4, GPT-3.5, O1"},
        "anthropic": {"name": "Anthropic", "models": "Claude 3.5 Sonnet, Opus, Haiku"},
        "google": {"name": "Google", "models": "Gemini 2.0, 1.5 Pro, Flash"},
        "mistral": {"name": "Mistral AI", "models": "Large, Medium, Small, Codestral"}
    }

    for provider, info in provider_info.items():
        is_enabled = provider in enabled_providers
        status = "✅" if is_enabled else "⚪"
        st.markdown(f"""
        **{status} {info['name']}**
        *Models: {info['models']}*
        """)

    st.markdown("---")

    st.markdown("### 📖 Quick Start")
    st.markdown("""
    1. **Configure Providers** - Add API keys for your preferred AI providers in the sidebar
    2. **Start Chatting** - Go to the Chat page and select a model
    3. **Upload Documents** - Add documents for context-aware responses
    4. **Connect MCP Servers** - Extend capabilities with external tools (optional)
    """)

    st.markdown("---")

    st.markdown("### 🆕 What's New in v2.0")
    st.markdown("""
    - ✨ Multi-provider support (OpenAI, Anthropic, Google, Mistral)
    - 🔌 MCP server integration
    - 💾 Enhanced conversation management
    - 🎨 Modern, responsive UI
    - 🔧 Improved configuration system
    - 📊 Better document indexing
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>Universal AI Chatbot v2.0 | Built with ❤️ using Streamlit</p>
    <p>Supporting OpenAI • Anthropic • Google • Mistral AI • MCP Servers</p>
</div>
""", unsafe_allow_html=True)
