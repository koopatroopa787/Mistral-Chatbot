import os
import streamlit as st
from pathlib import Path
import sys
import datetime

# Add src to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "src"))
sys.path.insert(0, str(parent_dir))

from config import load_settings
from providers import ProviderFactory, Message, MessageRole
from utils import ConversationManager, Conversation, ConversationMessage, setup_logging
from index_functions import search_index, load_index

# Setup
logger = setup_logging()

# Page configuration
st.set_page_config(
    page_title="Chat - Universal AI Chatbot",
    page_icon="💬",
    layout="wide",
)

# Initialize settings
if "settings" not in st.session_state:
    st.session_state.settings = load_settings()

settings = st.session_state.settings

# Initialize conversation manager
if "conversation_manager" not in st.session_state:
    st.session_state.conversation_manager = ConversationManager()

# Get enabled providers
enabled_providers = settings.get_enabled_providers()

if not enabled_providers:
    st.error("⚠️ No AI providers enabled. Please configure providers on the Home page.")
    st.stop()

# Sidebar
with st.sidebar:
    st.title("💬 Chat Settings")

    # Provider selection
    st.subheader("🤖 AI Provider")
    selected_provider = st.selectbox(
        "Provider",
        options=enabled_providers,
        index=0,
        help="Select the AI provider to use"
    )

    # Get available models for selected provider
    try:
        api_key = settings.get_provider_api_key(selected_provider)
        provider = ProviderFactory.create(selected_provider, api_key)
        available_models = provider.get_available_models()
    except Exception as e:
        st.error(f"Error initializing provider: {e}")
        st.stop()

    # Model selection
    default_model = settings.providers[selected_provider].default_model
    if default_model in available_models:
        default_index = available_models.index(default_model)
    else:
        default_index = 0

    selected_model = st.selectbox(
        "Model",
        options=available_models,
        index=default_index,
        help="Select the model to use"
    )

    st.markdown("---")

    # Model parameters
    st.subheader("⚙️ Parameters")

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=settings.default_temperature,
        step=0.1,
        help="Higher values make output more random, lower values more deterministic"
    )

    max_tokens = st.slider(
        "Max Tokens",
        min_value=100,
        max_value=4000,
        value=settings.default_max_tokens,
        step=100,
        help="Maximum number of tokens in the response"
    )

    enable_streaming = st.checkbox(
        "Enable Streaming",
        value=settings.enable_streaming,
        help="Stream responses in real-time"
    )

    st.markdown("---")

    # Document context
    st.subheader("📚 Document Context")

    use_index = st.checkbox(
        "Use indexed documents",
        value=True,
        help="Include relevant documents as context"
    )

    if use_index:
        top_k_results = st.slider(
            "Relevant documents",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            help="Number of documents to retrieve"
        )

    st.markdown("---")

    # System prompt
    st.subheader("📝 System Prompt")
    custom_prompt = st.text_area(
        "Custom system prompt (optional)",
        value="",
        height=100,
        help="Override the default system prompt"
    )

    st.markdown("---")

    # Conversation management
    st.subheader("💾 Conversation")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save", use_container_width=True):
            if "messages" in st.session_state and len(st.session_state.messages) > 0:
                # Create conversation
                title = f"Chat {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                conversation = st.session_state.conversation_manager.create_conversation(
                    title=title,
                    provider=selected_provider,
                    model=selected_model
                )

                # Add messages
                for msg in st.session_state.messages:
                    conversation.messages.append(ConversationMessage(
                        role=msg["role"],
                        content=msg["content"],
                        timestamp=datetime.datetime.now().isoformat()
                    ))

                # Save
                st.session_state.conversation_manager.save_conversation(conversation)
                st.success(f"💾 Saved as: {title}")
            else:
                st.warning("No messages to save")

    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Show token usage if available
    if "last_usage" in st.session_state and settings.show_token_usage:
        st.markdown("---")
        st.subheader("📊 Token Usage")
        usage = st.session_state.last_usage
        st.metric("Prompt Tokens", usage.get("prompt_tokens", 0))
        st.metric("Completion Tokens", usage.get("completion_tokens", 0))
        st.metric("Total Tokens", usage.get("total_tokens", 0))

# Main content
st.title(f"💬 Chat with {selected_provider.upper()} {selected_model}")

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input for user message
prompt = st.chat_input("Ask anything...")

# Handle user input
if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Check for search command
    if prompt.lower().startswith("search:"):
        query = prompt[7:].strip()
        with st.status("🔍 Searching documents..."):
            context = search_index(query, logger, top_k=top_k_results if use_index else 3, include_metadata=True)

        # Display search results
        if context:
            result = f"**🔍 Search Results:**\n\n{context}"
        else:
            result = "No relevant documents found. Please index documents first."

        with st.chat_message("assistant"):
            st.markdown(result)
        st.session_state.messages.append({"role": "assistant", "content": result})

    else:
        # Regular chat
        # Prepare messages
        messages = []

        # System message
        system_content = custom_prompt or settings.default_system_prompt

        # Add document context if enabled
        if use_index and load_index():
            with st.status("🔍 Finding relevant context..."):
                search_context = search_index(
                    prompt,
                    logger,
                    top_k=top_k_results,
                    include_metadata=True
                )

            if search_context:
                system_content += f"\n\nRelevant documents:\n\n{search_context}"

        messages.append(Message(
            role=MessageRole.SYSTEM,
            content=system_content
        ))

        # Add history (limit to max_history_length)
        history_start = max(0, len(st.session_state.messages) - settings.max_history_length * 2 - 1)
        for msg in st.session_state.messages[history_start:-1]:
            role = MessageRole.USER if msg["role"] == "user" else MessageRole.ASSISTANT
            messages.append(Message(role=role, content=msg["content"]))

        # Add current user message
        messages.append(Message(role=MessageRole.USER, content=prompt))

        # Get response
        with st.chat_message("assistant"):
            try:
                if enable_streaming and provider.supports_streaming():
                    # Streaming response
                    message_placeholder = st.empty()
                    full_response = ""

                    for chunk in provider.stream_chat(
                        messages=messages,
                        model=selected_model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    ):
                        full_response += chunk.content
                        message_placeholder.markdown(full_response + "▌")

                    message_placeholder.markdown(full_response)

                    # Store usage if available
                    if hasattr(chunk, 'metadata') and chunk.metadata:
                        st.session_state.last_usage = chunk.metadata.get('usage', {})

                else:
                    # Non-streaming response
                    with st.spinner("Thinking..."):
                        response = provider.chat(
                            messages=messages,
                            model=selected_model,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )

                    full_response = response.content
                    st.markdown(full_response)

                    # Store usage
                    if response.usage:
                        st.session_state.last_usage = response.usage

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                full_response = f"I encountered an error: {str(e)}"
                st.markdown(full_response)

        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# Tips
with st.expander("💡 Tips & Commands"):
    st.markdown(f"""
    ### 🎯 Current Setup
    - **Provider**: {selected_provider.upper()}
    - **Model**: {selected_model}
    - **Streaming**: {"✅ Enabled" if enable_streaming else "❌ Disabled"}
    - **Document Context**: {"✅ Enabled" if use_index else "❌ Disabled"}

    ### 📖 How to Use
    - **Regular chat**: Type your message and press Enter
    - **Search documents**: Type `search: your query` to search indexed documents
    - **Save conversation**: Click the 💾 Save button in the sidebar
    - **Clear chat**: Click the 🗑️ Clear button in the sidebar

    ### ⚙️ Customization
    - Change provider/model in the sidebar
    - Adjust temperature for creativity vs consistency
    - Increase max tokens for longer responses
    - Add custom system prompt for specialized behavior

    ### 📚 Document Context
    When document context is enabled, the AI will automatically search your indexed documents for relevant information and use it to inform responses.

    ### 🔄 Switching Models
    You can switch providers and models at any time. Your conversation history is preserved, but responses may vary based on the model's capabilities.

    ### 💾 Saved Conversations
    Saved conversations can be viewed and loaded from the **Conversations** page.
    """)

# Show MCP servers if enabled
if settings.enable_mcp:
    from mcp import MCPManager

    if "mcp_manager" not in st.session_state:
        st.session_state.mcp_manager = MCPManager()

    mcp_manager = st.session_state.mcp_manager

    if mcp_manager.list_servers():
        with st.expander("🔌 MCP Server Status"):
            health_status = mcp_manager.health_check_all()
            for server_name, is_healthy in health_status.items():
                status_icon = "✅" if is_healthy else "❌"
                st.markdown(f"{status_icon} **{server_name}**: {'Healthy' if is_healthy else 'Unavailable'}")
