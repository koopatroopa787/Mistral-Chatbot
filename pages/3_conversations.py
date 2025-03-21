import os
import streamlit as st
import json
from pathlib import Path
import sys
import datetime

# Add the parent directory to the path so we can import the helper modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Page configuration
st.set_page_config(
    page_title="Saved Conversations - Mistral AI Assistant",
    page_icon="📝",
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

# Sidebar
with st.sidebar:
    st.title("Saved Conversations")
    st.markdown("View and manage your saved conversations")
    
    # Link back to chat
    st.markdown("---")
    st.markdown("[Back to Chat](/Chat)", unsafe_allow_html=True)

# Main content
st.title("Saved Conversations")

# Create conversations directory if it doesn't exist
os.makedirs("conversations", exist_ok=True)

# Get list of saved conversations
conversation_files = list(Path("conversations").glob("*.json"))
conversation_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

if not conversation_files:
    st.info("No saved conversations found. You can save conversations from the Chat page.")
else:
    # Display list of conversations
    st.subheader("Select a conversation to view")
    
    # Create a container for the conversation list
    with st.container():
        # Create a grid of conversation cards
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Create select box with conversation dates
            conversation_options = []
            for file in conversation_files:
                try:
                    # Get creation time
                    timestamp = file.stat().st_mtime
                    date_str = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Get message count
                    with open(file, "r") as f:
                        messages = json.load(f)
                    
                    # Create option label
                    label = f"{date_str} ({len(messages)} messages)"
                    conversation_options.append((label, file))
                except:
                    # Skip invalid files
                    continue
            
            if conversation_options:
                # Extract just the labels for the selectbox
                labels = [label for label, _ in conversation_options]
                selected_label = st.selectbox("Select conversation", labels)
                
                # Find the selected file
                selected_file = next((file for label, file in conversation_options if label == selected_label), None)
                
                # Delete button
                if st.button("Delete Selected Conversation"):
                    try:
                        os.remove(selected_file)
                        st.success("Conversation deleted successfully.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error deleting conversation: {str(e)}")
                
                # Export button
                if st.button("Export Selected Conversation"):
                    try:
                        with open(selected_file, "r") as f:
                            conversation_data = f.read()
                        
                        # Create download button
                        st.download_button(
                            label="Download Conversation",
                            data=conversation_data,
                            file_name=f"conversation_{selected_label.split(' ')[0]}.json",
                            mime="application/json"
                        )
                    except Exception as e:
                        st.error(f"Error exporting conversation: {str(e)}")
            else:
                st.warning("No valid conversation files found.")
        
        # Display the selected conversation
        with col2:
            if conversation_options:
                try:
                    with open(selected_file, "r") as f:
                        messages = json.load(f)
                    
                    # Create a chat-like display
                    st.subheader("Conversation")
                    
                    # Add summary info
                    user_messages = sum(1 for msg in messages if msg["role"] == "user")
                    assistant_messages = sum(1 for msg in messages if msg["role"] == "assistant")
                    
                    # Display stats
                    stats_col1, stats_col2, stats_col3 = st.columns(3)
                    with stats_col1:
                        st.metric("Total Messages", len(messages))
                    with stats_col2:
                        st.metric("User Messages", user_messages)
                    with stats_col3:
                        st.metric("Assistant Messages", assistant_messages)
                    
                    # Display messages
                    with st.container():
                        for message in messages:
                            with st.chat_message(message["role"]):
                                st.markdown(message["content"])
                    
                    # Option to continue this conversation
                    if st.button("Continue this conversation in Chat"):
                        # Store the conversation in session state to be loaded in the Chat page
                        st.session_state.messages = messages
                        # Redirect to Chat page
                        st.switch_page("pages/1_Chat.py")
                        
                except Exception as e:
                    st.error(f"Error loading conversation: {str(e)}")

# Import conversation
st.markdown("---")
st.subheader("Import Conversation")

uploaded_conversation = st.file_uploader("Upload a conversation file", type=["json"])

if uploaded_conversation and st.button("Import Conversation"):
    try:
        # Read the uploaded JSON
        conversation_data = json.loads(uploaded_conversation.getvalue().decode("utf-8"))
        
        # Validate the structure (basic check)
        if isinstance(conversation_data, list) and all(isinstance(msg, dict) and "role" in msg and "content" in msg for msg in conversation_data):
            # Create a new file name based on current time
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            new_file_path = Path("conversations") / f"conversation_{timestamp}.json"
            
            # Save the file
            with open(new_file_path, "w") as f:
                json.dump(conversation_data, f, indent=2)
            
            st.success(f"Conversation imported successfully as {new_file_path.name}")
            st.experimental_rerun()
        else:
            st.error("The uploaded file is not a valid conversation file.")
    except Exception as e:
        st.error(f"Error importing conversation: {str(e)}")

# User guide
with st.expander("About Conversations"):
    st.markdown("""
    ### Managing Your Conversations

    - **Save Conversations**: From the Chat page, use the "Save Current Conversation" button in the sidebar.
    - **View Conversations**: Select from the list on the left to view the full conversation.
    - **Continue Conversations**: Click "Continue this conversation in Chat" to resume a saved conversation.
    - **Delete Conversations**: Select a conversation and click "Delete Selected Conversation".
    - **Export/Import**: You can export conversations to share them or back them up, and import them later.

    ### Privacy Note

    Saved conversations are stored locally on your device. They are not sent to or stored on any external servers.
    """)