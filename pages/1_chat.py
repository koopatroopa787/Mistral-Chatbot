import os
import streamlit as st
from mistralai import Mistral
import time
from pathlib import Path
import sys
import json

# Add the parent directory to the path so we can import the helper modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper_functions import setup_logging, load_config
from index_functions import search_index, load_index

# Check for response grading module
try:
    from response_grader import (
        grade_response, 
        create_grading_criteria, 
        load_grading_templates
    )
    has_grader = True
except ImportError:
    has_grader = False

# Check for conversation flow module
try:
    from conversation_flow import (
        ConversationFlow,
        ConversationStage,
        ConversationState,
        load_conversation_flow,
        list_conversation_flows,
        process_conversation_turn
    )
    has_flow = True
except ImportError:
    has_flow = False

# Setup
logger = setup_logging()
config = load_config()

# Initialize Mistral client
@st.cache_resource
def get_mistral_client():
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        st.error("Missing API key. Please set your Mistral API Key on the Home page.")
        return None
    return Mistral(api_key=api_key)

# Page configuration
st.set_page_config(
    page_title="Chat - Mistral AI Assistant",
    page_icon="💬",
    layout="wide",
)

# Check if the client is available
client = get_mistral_client()
if not client:
    st.stop()

# Load grading templates if available
grading_templates = {}
if has_grader:
    grading_templates = load_grading_templates()

# Load conversation flows if available
conversation_flows = []
if has_flow:
    conversation_flows = list_conversation_flows()

# Sidebar
with st.sidebar:
    st.title("Chat Settings")
    
    # Model selection
    model_options = [
        "mistral-large-latest",
        "mistral-small-latest",
        "mistral-medium-latest"
    ]
    selected_model = st.selectbox("Select Model", model_options, index=0)
    
    # Temperature slider
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1, 
                          help="Higher values make output more random, lower values more deterministic")
    
    # Max tokens slider
    max_tokens = st.slider("Max Tokens", min_value=100, max_value=4000, value=1000, step=100, 
                         help="Maximum number of tokens in the response")
    
    # Use indexed documents checkbox
    use_index = st.checkbox("Use indexed documents for context", value=True, 
                          help="When enabled, relevant information from indexed documents will be used to inform responses")
    
    # Enhanced context options
    st.markdown("---")
    st.subheader("Enhanced Context")
    
    include_summaries = st.checkbox("Include document summaries", value=True,
                                  help="Include document summaries in the context for more comprehensive responses")
    
    include_keywords = st.checkbox("Include document keywords", value=True,
                                help="Include document keywords in the context to improve relevance")
    
    top_k_results = st.slider("Number of relevant documents", min_value=1, max_value=10, value=3, step=1,
                             help="Number of relevant documents to retrieve for context")
    
    # Conversation flow settings (new)
    if has_flow and conversation_flows:
        st.markdown("---")
        st.subheader("Conversation Flows")
        
        enable_flows = st.checkbox("Enable conversation flows", value=True,
                                 help="Allow structured conversations using the /flow command")
        
        # Flow selection for active conversations
        flow_options = [flow["flow_id"] for flow in conversation_flows]
        default_flow = st.selectbox(
            "Default conversation flow", 
            options=["None"] + flow_options,
            format_func=lambda x: next((flow["name"] for flow in conversation_flows if flow["flow_id"] == x), x) if x != "None" else "None",
            help="Default flow to use when no specific flow is specified"
        )
    else:
        enable_flows = False
        default_flow = "None"
    
    # Response grading settings
    if has_grader:
        st.markdown("---")
        st.subheader("Response Grading")
        
        enable_grading = st.checkbox("Enable response grading", value=True,
                                   help="Allow the assistant to grade your responses when you use the /grade command")
        
        # Template selection for grading
        if grading_templates:
            template_options = list(grading_templates.keys())
            default_grading_template = st.selectbox(
                "Default grading template", 
                options=["None"] + template_options,
                help="Template to use for grading when no specific template is specified"
            )
        else:
            default_grading_template = "None"
    else:
        enable_grading = False
        default_grading_template = "None"
    
    # Clear chat button
    st.markdown("---")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        # Also clear any active conversation flows
        if "active_flow" in st.session_state:
            del st.session_state.active_flow
        if "flow_state" in st.session_state:
            del st.session_state.flow_state
        st.experimental_rerun()
    
    # Conversation management
    st.markdown("---")
    st.subheader("Conversation Management")
    
    # Save conversation
    if st.button("Save Current Conversation"):
        if "messages" in st.session_state and len(st.session_state.messages) > 0:
            # Create conversations directory if it doesn't exist
            os.makedirs("conversations", exist_ok=True)
            
            # Generate filename based on timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversations/conversation_{timestamp}.json"
            
            # Save conversation - ensure we only save the role and content
            clean_messages = []
            for msg in st.session_state.messages:
                # Only keep the role and content fields
                clean_msg = {
                    "role": msg["role"],
                    "content": msg["content"]
                }
                clean_messages.append(clean_msg)
                
            with open(filename, "w") as f:
                json.dump(clean_messages, f, indent=2)
            
            st.success(f"Conversation saved as {filename}")
        else:
            st.warning("No messages to save")
    
    # Link to other pages
    st.markdown("---")
    st.markdown("[Manage Document Index](/Document_Index)", unsafe_allow_html=True)
    if has_grader:
        st.markdown("[Response Grading](/Response_Grading)", unsafe_allow_html=True)
    if has_flow:
        st.markdown("[Conversation Flows](/Conversation_Flows)", unsafe_allow_html=True)

# Function to handle grading requests
def process_grading_request(user_input, last_question=None):
    """Process a grading request from the user"""
    # Extract the response to grade
    if user_input.lower().startswith("/grade "):
        response_to_grade = user_input[7:].strip()
    else:
        return None
    
    if not response_to_grade:
        return "Please provide a response to grade after the /grade command."
    
    # Get template if specified
    template_name = None
    template = None
    
    # Check if template is specified with a colon
    if ":" in response_to_grade and " " in response_to_grade[:response_to_grade.find(" ")]:
        template_part = response_to_grade.split(":", 1)[0].strip()
        if template_part in grading_templates:
            template_name = template_part
            template = grading_templates[template_name]
            response_to_grade = response_to_grade.split(":", 1)[1].strip()
    
    # Use default template if none specified
    if not template and default_grading_template != "None":
        template_name = default_grading_template
        template = grading_templates[template_name]
    
    # Get appropriate context
    if template:
        criteria = template.get("criteria", {})
        reference_answer = template.get("reference_answer", None)
        context = template.get("context", last_question)
    else:
        # Use default criteria
        criteria = create_grading_criteria("general", "medium")
        reference_answer = None
        context = last_question
    
    # Grade the response
    grading_result = grade_response(
        user_response=response_to_grade,
        context=context,
        criteria=criteria,
        reference_answer=reference_answer,
        client=client
    )
    
    if not grading_result:
        return "Error grading response. Please try again."
    
    # Format the result
    score = grading_result.get("score", 0)
    feedback = grading_result.get("feedback", "")
    strengths = grading_result.get("strengths", [])
    weaknesses = grading_result.get("weaknesses", [])
    suggestions = grading_result.get("suggestions", [])
    
    result_text = f"## Response Grading Result: {score}/10\n\n"
    result_text += f"**Overall Assessment:** {feedback}\n\n"
    
    if strengths:
        result_text += "### Strengths\n"
        for strength in strengths:
            result_text += f"✅ {strength}\n"
        result_text += "\n"
    
    if weaknesses:
        result_text += "### Areas for Improvement\n"
        for weakness in weaknesses:
            result_text += f"⚠️ {weakness}\n"
        result_text += "\n"
    
    if suggestions:
        result_text += "### Suggestions\n"
        for suggestion in suggestions:
            result_text += f"💡 {suggestion}\n"
    
    if template_name:
        result_text += f"\n*Graded using template: {template_name}*"
    
    return result_text

# Function to handle conversation flow commands
def process_flow_command(user_input):
    """Process a conversation flow command from the user"""
    # Check if it's a start flow command
    if user_input.lower().startswith("/flow "):
        flow_id = user_input[6:].strip()
        
        # If no flow ID provided, use default
        if not flow_id and default_flow != "None":
            flow_id = default_flow
        
        if not flow_id:
            return "Please specify a flow ID after the /flow command or set a default flow in the sidebar."
        
        # Load the flow
        flow = load_conversation_flow(flow_id)
        if not flow:
            return f"Flow not found: {flow_id}. Please check the flow ID and try again."
        
        # Initialize conversation state
        st.session_state.active_flow = flow
        st.session_state.flow_state = ConversationState(
            flow_id=flow.flow_id,
            current_stage_id=flow.initial_stage,
            completed_stages=[],
            stage_turns={flow.initial_stage: 0},
            data={}
        )
        
        # Get the initial stage
        initial_stage = flow.stages.get(flow.initial_stage)
        if not initial_stage:
            return f"Error: Invalid initial stage in flow {flow_id}."
        
        # Return the initial message
        result = f"*Starting conversation flow: **{flow.name}***\n\n"
        result += f"*Current stage: **{initial_stage.name}***\n\n"
        
        # If there's a user prompt for the initial stage, include it
        if initial_stage.user_prompt:
            result += initial_stage.user_prompt
        
        return result
    
    # Check if it's a flow status command
    elif user_input.lower() == "/flow-status":
        if "active_flow" not in st.session_state or "flow_state" not in st.session_state:
            return "No active conversation flow. Start one with the `/flow [flow_id]` command."
        
        flow = st.session_state.active_flow
        state = st.session_state.flow_state
        
        current_stage = flow.stages.get(state.current_stage_id)
        if not current_stage:
            return f"Error: Invalid current stage in flow {flow.flow_id}."
        
        result = f"**Active Flow:** {flow.name} (`{flow.flow_id}`)\n\n"
        result += f"**Current Stage:** {current_stage.name} (`{current_stage.stage_id}`)\n"
        result += f"**Turns in this stage:** {state.stage_turns.get(current_stage.stage_id, 0)}/{current_stage.max_turns}\n\n"
        
        if state.completed_stages:
            result += "**Completed Stages:**\n"
            for stage_id in state.completed_stages:
                stage = flow.stages.get(stage_id)
                if stage:
                    result += f"- {stage.name} (`{stage_id}`)\n"
        
        return result
    
    # Check if it's a flow end command
    elif user_input.lower() == "/flow-end":
        if "active_flow" not in st.session_state:
            return "No active conversation flow to end."
        
        flow = st.session_state.active_flow
        
        # Clear flow state
        del st.session_state.active_flow
        del st.session_state.flow_state
        
        return f"*Ended conversation flow: **{flow.name}***"
    
    # Not a flow command
    return None

# Function to process a message in an active flow
def process_flow_message(user_input):
    """Process a message in an active conversation flow"""
    if "active_flow" not in st.session_state or "flow_state" not in st.session_state:
        return None
    
    flow = st.session_state.active_flow
    state = st.session_state.flow_state
    
    # Process the turn
    system_message, updated_state = process_conversation_turn(
        user_message=user_input,
        conversation_state=state,
        conversation_flow=flow,
        client=client
    )
    
    # Update state
    st.session_state.flow_state = updated_state
    
    # Check if stage changed
    old_stage_id = state.current_stage_id
    new_stage_id = updated_state.current_stage_id
    
    stage_changed = old_stage_id != new_stage_id
    new_stage = flow.stages.get(new_stage_id) if stage_changed else None
    
    # Return the system message and stage change info
    return {
        "system_message": system_message,
        "stage_changed": stage_changed,
        "old_stage": flow.stages.get(old_stage_id),
        "new_stage": new_stage
    }

# Main content
st.title("Chat with Mistral AI")

# Initialize session state for messages if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Track the last question for grading purposes
if "last_question" not in st.session_state:
    st.session_state.last_question = None

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input for user message
prompt = st.chat_input("Ask anything...")

# Handle user input
if prompt:
    # Check for conversation flow commands
    if has_flow and enable_flows and prompt.lower().startswith("/flow"):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process flow command
        flow_result = process_flow_command(prompt)
        
        if flow_result:
            # Display flow command result
            with st.chat_message("assistant"):
                st.markdown(flow_result)
            st.session_state.messages.append({"role": "assistant", "content": flow_result})
            st.experimental_rerun()
    
    # Check for grading request
    elif has_grader and enable_grading and prompt.lower().startswith("/grade"):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process grading request
        grading_result = process_grading_request(prompt, st.session_state.last_question)
        
        if grading_result:
            # Display grading result
            with st.chat_message("assistant"):
                st.markdown(grading_result)
            st.session_state.messages.append({"role": "assistant", "content": grading_result})
        else:
            # Display error message
            with st.chat_message("assistant"):
                st.markdown("I couldn't process your grading request. Please make sure to include text to grade after the /grade command.")
            st.session_state.messages.append({"role": "assistant", "content": "I couldn't process your grading request. Please make sure to include text to grade after the /grade command."})
    
    # Check for special commands
    elif prompt.lower().startswith("search:"):
        query = prompt[7:].strip()
        with st.status("Searching documents..."):
            context = search_index(query, logger, top_k=top_k_results, include_metadata=True)
        
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
        
        # Save this as the last question for potential grading
        st.session_state.last_question = prompt
        
        # Check if we're in an active flow
        flow_context = None
        if has_flow and enable_flows and "active_flow" in st.session_state:
            flow_context = process_flow_message(prompt)
        
        # Check if we have indexed content to add as context
        search_context = ""
        if use_index and load_index():
            with st.status("Searching for relevant context..."):
                search_context = search_index(
                    prompt, 
                    logger, 
                    top_k=top_k_results, 
                    include_metadata=True
                )
        
        # Prepare messages including history and context
        messages = []
        
        # Add system message with context if available
        system_prompt = ""
        
        # Add flow context if available
        if flow_context:
            system_prompt = flow_context["system_message"]
        
        # Add search context if available
        if search_context:
            # If we already have a system prompt from flow, append the search context
            if system_prompt:
                system_prompt += "\n\nAdditionally, you have access to the following information. "
                system_prompt += "Use it to inform your responses when relevant:\n\n"
                system_prompt += search_context
            else:
                # Otherwise, create a new system prompt with the search context
                system_prompt = """You are a helpful assistant with access to the following information. 
                Use it to inform your responses when relevant. 
                
                Pay special attention to document SUMMARIES which give an overview of the documents.
                Pay attention to KEYWORDS which indicate important concepts.
                Use the CONTENT sections for specific details when needed.
                
                Provide accurate, concise responses based on this context:
                """
                
                system_prompt += f"\n\n{search_context}"
        
        # If we have a system prompt, add it
        if system_prompt:
            messages.append({
                "role": "system", 
                "content": system_prompt
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
            
            # If we had a stage change in a flow, add a system message
            if flow_context and flow_context["stage_changed"] and flow_context["new_stage"]:
                new_stage = flow_context["new_stage"]
                old_stage = flow_context["old_stage"]
                
                # Add a system message about the stage change
                transition_message = f"*[System: Moving from {old_stage.name} to {new_stage.name} stage]*"
                
                with st.chat_message("system"):
                    st.markdown(transition_message)
                
                st.session_state.messages.append({"role": "system", "content": transition_message})
                
                # If the new stage has a user prompt, display it
                if new_stage.user_prompt:
                    with st.chat_message("assistant"):
                        st.markdown(new_stage.user_prompt)
                    
                    st.session_state.messages.append({"role": "assistant", "content": new_stage.user_prompt})
                
                # Rerun to update the UI
                st.experimental_rerun()

# Add helpful information
with st.expander("Tips & Commands"):
    st.markdown("""
    ### How to use this chatbot:
    
    - **Regular chat**: Simply type your message and press Enter.
    - **Search indexed documents**: Type `search: your query` to search the indexed documents.
    - **Add documents**: Use the Document Index page to upload files or specify a folder path for indexing.
    """)
    
    if has_grader and enable_grading:
        st.markdown("""
        ### Response Grading:
        
        You can have your responses graded by using the `/grade` command followed by your response:
        
        ```
        /grade Your answer to be graded goes here...
        ```
        
        You can also specify a grading template by including the template name:
        
        ```
        /grade [template_name]: Your answer to be graded goes here...
        ```
        
        The AI will evaluate your response and provide a score, feedback, strengths, weaknesses, and suggestions for improvement.
        """)
    
    if has_flow and enable_flows:
        st.markdown("""
        ### Conversation Flows:
        
        You can start a structured conversation using the `/flow` command followed by the flow ID:
        
        ```
        /flow customer_support
        ```
        
        The conversation will follow a predefined flow with stage-specific prompts. You can:
        
        - Check the current flow status with `/flow-status`
        - End the current flow with `/flow-end`
        
        The assistant will guide you through the stages of the conversation automatically.
        """)
    
    st.markdown("""    
    ### Enhanced Context Features:
    
    This chatbot supports enhanced document processing:
    
    - **Document Summaries**: Automatically generated summaries help the AI understand the big picture.
    - **Keyword Extraction**: Important concepts are identified to improve relevance.
    - **Hierarchical Chunking**: Documents are split intelligently to preserve context.
    
    ### Model Settings:
    
    You can adjust the model, temperature, and max tokens in the sidebar to control the AI's responses.
    
    ### Document Indexing:
    
    For best results, use the Document Index page to process your documents with Advanced Processing enabled.
    """)