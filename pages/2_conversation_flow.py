import os
import streamlit as st
import sys
import json
from pathlib import Path
import time

# Add the parent directory to the path so we can import the helper modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Check if the conversation_flow module is available
try:
    from conversation_flow import (
        ConversationFlow,
        ConversationStage,
        ConversationState,
        save_conversation_flow,
        load_conversation_flow,
        list_conversation_flows,
        create_default_flows
    )
    has_flow_module = True
except ImportError:
    has_flow_module = False
    st.error("Conversation flow module not found. Make sure conversation_flow.py is in the main directory.")

from helper_functions import setup_logging, load_config

# Setup
logger = setup_logging()
config = load_config()

# Page configuration
st.set_page_config(
    page_title="Conversation Flows - Mistral AI Assistant",
    page_icon="🔄",
    layout="wide",
)

# Initialize conversation flows directory
@st.cache_resource
def initialize_flows():
    flows_dir = Path("conversation_flows")
    if not flows_dir.exists():
        flows_dir.mkdir(exist_ok=True)
        if has_flow_module:
            return create_default_flows()
    return []

# Check if the flow module is available
if not has_flow_module:
    st.error("The Conversation Flows feature requires the conversation_flow.py module. Make sure it exists in your main directory.")
    st.stop()

# Initialize flows
initialize_flows()

# List available flows
flows = list_conversation_flows()

# Sidebar
with st.sidebar:
    st.title("Conversation Flows")
    st.markdown("Create and manage structured conversation flows with stage-specific prompts.")
    
    # Available flows
    st.subheader("Available Flows")
    if flows:
        for flow in flows:
            st.markdown(f"- **{flow['name']}**")
    else:
        st.info("No conversation flows found. Create your first flow using the editor.")
    
    # Create default flows button
    if st.button("Create Default Flows"):
        with st.spinner("Creating default flows..."):
            created_flows = create_default_flows()
            st.success(f"Created {len(created_flows)} default flows!")
            st.experimental_rerun()
    
    # Link back to chat
    st.markdown("---")
    st.markdown("[Back to Chat](/Chat)", unsafe_allow_html=True)

# Main content
st.title("Conversation Flows")
st.markdown("Design structured conversation paths with stage-specific prompts to guide interactions.")

# Create tabs for different flow management functions
tabs = st.tabs(["Flow Browser", "Flow Editor", "Test Flow", "Import/Export"])

# Tab 1: Flow Browser
with tabs[0]:
    st.header("Browse Conversation Flows")
    
    # Select flow to view
    if flows:
        selected_flow_id = st.selectbox(
            "Select a flow to view",
            options=[flow["flow_id"] for flow in flows],
            format_func=lambda x: next((flow["name"] for flow in flows if flow["flow_id"] == x), x)
        )
        
        # Load the selected flow
        if selected_flow_id:
            flow = load_conversation_flow(selected_flow_id)
            
            if flow:
                # Display flow details
                st.subheader(flow.name)
                st.markdown(f"**ID:** `{flow.flow_id}`")
                st.markdown(f"**Description:** {flow.description}")
                st.markdown(f"**Initial Stage:** `{flow.initial_stage}`")
                
                # Display stages
                st.markdown("### Stages")
                
                # Create a visual representation of the flow
                import graphviz
                graph = graphviz.Digraph()
                
                # Add nodes for each stage
                for stage_id, stage in flow.stages.items():
                    label = f"{stage.name}\n(max turns: {stage.max_turns})"
                    
                    # Highlight initial stage
                    if stage_id == flow.initial_stage:
                        graph.node(stage_id, label=label, style="filled", fillcolor="lightblue")
                    # Highlight terminal stages
                    elif not stage.next_stages:
                        graph.node(stage_id, label=label, style="filled", fillcolor="lightgreen")
                    else:
                        graph.node(stage_id, label=label)
                
                # Add edges between stages
                for stage_id, stage in flow.stages.items():
                    for next_stage_id in stage.next_stages:
                        graph.edge(stage_id, next_stage_id)
                
                # Render the graph
                st.graphviz_chart(graph)
                
                # Display detailed stage information
                for stage_id, stage in flow.stages.items():
                    with st.expander(f"Stage: {stage.name} (`{stage_id}`)"):
                        st.markdown(f"**Max Turns:** {stage.max_turns}")
                        
                        # Next stages
                        st.markdown("**Next Stages:**")
                        if stage.next_stages:
                            for next_stage_id in stage.next_stages:
                                next_stage_name = flow.stages.get(next_stage_id, ConversationStage(next_stage_id, next_stage_id, "")).name
                                st.markdown(f"- `{next_stage_id}` ({next_stage_name})")
                        else:
                            st.markdown("- *Terminal stage (no next stages)*")
                        
                        # Completion criteria
                        if stage.completion_criteria:
                            st.markdown("**Completion Criteria:**")
                            for criterion, description in stage.completion_criteria.items():
                                st.markdown(f"- **{criterion}:** {description}")
                        
                        # System prompt
                        st.markdown("**System Prompt:**")
                        st.text_area("", stage.system_prompt, height=150, key=f"view_prompt_{stage_id}", disabled=True)
                        
                        # User prompt if available
                        if stage.user_prompt:
                            st.markdown("**User Prompt:**")
                            st.text_area("", stage.user_prompt, height=100, key=f"view_user_prompt_{stage_id}", disabled=True)
                
                # Delete flow button
                if st.button("Delete Flow", key=f"delete_{flow.flow_id}"):
                    if st.checkbox("Confirm deletion", key=f"confirm_delete_{flow.flow_id}"):
                        flow_path = Path("conversation_flows") / f"{flow.flow_id}.json"
                        if flow_path.exists():
                            try:
                                os.remove(flow_path)
                                st.success(f"Flow '{flow.name}' deleted successfully!")
                                time.sleep(1)
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting flow: {str(e)}")
            else:
                st.error(f"Error loading flow: {selected_flow_id}")
    else:
        st.info("No conversation flows found. Create your first flow using the Flow Editor tab.")

# Tab 2: Flow Editor
with tabs[1]:
    st.header("Conversation Flow Editor")
    
    # Edit existing flow or create new
    edit_mode = st.radio("", ["Create New Flow", "Edit Existing Flow"], horizontal=True)
    
    if edit_mode == "Edit Existing Flow" and flows:
        # Select flow to edit
        edit_flow_id = st.selectbox(
            "Select a flow to edit",
            options=[flow["flow_id"] for flow in flows],
            format_func=lambda x: next((flow["name"] for flow in flows if flow["flow_id"] == x), x),
            key="edit_flow_select"
        )
        
        # Load the selected flow
        if edit_flow_id:
            flow = load_conversation_flow(edit_flow_id)
            
            if flow:
                # Flow details
                flow_id = flow.flow_id
                flow_name = st.text_input("Flow Name", value=flow.name)
                flow_description = st.text_area("Flow Description", value=flow.description, height=100)
                
                # Stage management
                st.subheader("Stage Management")
                
                # List existing stages with edit/delete options
                st.markdown("### Existing Stages")
                
                existing_stages = list(flow.stages.keys())
                
                # Allow selecting initial stage
                initial_stage = st.selectbox(
                    "Initial Stage",
                    options=existing_stages,
                    index=existing_stages.index(flow.initial_stage) if flow.initial_stage in existing_stages else 0
                )
                
                # Display existing stages
                for stage_id, stage in flow.stages.items():
                    with st.expander(f"Stage: {stage.name} (`{stage_id}`)"):
                        # Stage details
                        stage_name = st.text_input("Stage Name", value=stage.name, key=f"edit_name_{stage_id}")
                        
                        # Next stages (multiselect)
                        next_stages = st.multiselect(
                            "Next Stages",
                            options=[s for s in existing_stages if s != stage_id],
                            default=stage.next_stages,
                            key=f"edit_next_{stage_id}"
                        )
                        
                        # Max turns
                        max_turns = st.number_input(
                            "Max Turns",
                            min_value=1,
                            max_value=10,
                            value=stage.max_turns,
                            key=f"edit_turns_{stage_id}"
                        )
                        
                        # System prompt
                        system_prompt = st.text_area(
                            "System Prompt",
                            value=stage.system_prompt,
                            height=150,
                            key=f"edit_prompt_{stage_id}"
                        )
                        
                        # User prompt
                        user_prompt = st.text_area(
                            "User Prompt (Optional)",
                            value=stage.user_prompt or "",
                            height=100,
                            key=f"edit_user_prompt_{stage_id}"
                        )
                        
                        # Completion criteria
                        st.markdown("**Completion Criteria** (key-value pairs)")
                        
                        criteria = {}
                        existing_criteria = stage.completion_criteria.items()
                        
                        # Display existing criteria with option to edit
                        for i, (key, value) in enumerate(existing_criteria):
                            col1, col2, col3 = st.columns([3, 6, 1])
                            with col1:
                                new_key = st.text_input("Criterion", value=key, key=f"edit_crit_key_{stage_id}_{i}")
                            with col2:
                                new_value = st.text_input("Description", value=value, key=f"edit_crit_value_{stage_id}_{i}")
                            with col3:
                                st.write("")
                                st.write("")
                                remove = st.checkbox("Remove", key=f"edit_crit_remove_{stage_id}_{i}")
                            
                            if not remove and new_key:
                                criteria[new_key] = new_value
                        
                        # Add new criterion
                        st.markdown("**Add New Criterion**")
                        new_crit_col1, new_crit_col2 = st.columns([3, 6])
                        with new_crit_col1:
                            new_crit_key = st.text_input("Criterion", key=f"new_crit_key_{stage_id}")
                        with new_crit_col2:
                            new_crit_value = st.text_input("Description", key=f"new_crit_value_{stage_id}")
                        
                        if new_crit_key:
                            criteria[new_crit_key] = new_crit_value
                        
                        # Update or delete stage
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Update Stage", key=f"update_{stage_id}"):
                                # Create updated stage
                                updated_stage = ConversationStage(
                                    stage_id=stage_id,
                                    name=stage_name,
                                    system_prompt=system_prompt,
                                    user_prompt=user_prompt if user_prompt else None,
                                    next_stages=next_stages,
                                    completion_criteria=criteria,
                                    max_turns=max_turns
                                )
                                
                                # Update stage in flow
                                flow.stages[stage_id] = updated_stage
                                
                                # Update flow
                                flow.name = flow_name
                                flow.description = flow_description
                                flow.initial_stage = initial_stage
                                
                                # Save flow
                                if save_conversation_flow(flow):
                                    st.success(f"Stage '{stage_name}' updated successfully!")
                                else:
                                    st.error("Error updating stage")
                        
                        with col2:
                            if st.button("Delete Stage", key=f"delete_stage_{stage_id}"):
                                if st.checkbox("Confirm deletion", key=f"confirm_stage_delete_{stage_id}"):
                                    # Remove stage from flow
                                    if stage_id in flow.stages:
                                        del flow.stages[stage_id]
                                        
                                        # Remove stage from next_stages of other stages
                                        for s in flow.stages.values():
                                            if stage_id in s.next_stages:
                                                s.next_stages.remove(stage_id)
                                        
                                        # Update initial stage if needed
                                        if flow.initial_stage == stage_id and flow.stages:
                                            flow.initial_stage = next(iter(flow.stages.keys()))
                                        
                                        # Save flow
                                        if save_conversation_flow(flow):
                                            st.success(f"Stage '{stage_name}' deleted successfully!")
                                            st.experimental_rerun()
                                        else:
                                            st.error("Error deleting stage")
                
                # Add new stage
                st.markdown("### Add New Stage")
                with st.expander("Create New Stage"):
                    new_stage_id = st.text_input("Stage ID", key="new_stage_id")
                    new_stage_name = st.text_input("Stage Name", key="new_stage_name")
                    new_stage_prompt = st.text_area("System Prompt", height=150, key="new_stage_prompt")
                    new_stage_user_prompt = st.text_area("User Prompt (Optional)", height=100, key="new_stage_user_prompt")
                    new_stage_max_turns = st.number_input("Max Turns", min_value=1, max_value=10, value=3, key="new_stage_turns")
                    
                    # Next stages
                    new_stage_next = st.multiselect(
                        "Next Stages",
                        options=existing_stages,
                        key="new_stage_next"
                    )
                    
                    # Create stage button
                    if st.button("Add Stage", key="add_stage"):
                        if new_stage_id and new_stage_name and new_stage_prompt:
                            # Check if stage ID already exists
                            if new_stage_id in flow.stages:
                                st.error(f"Stage ID '{new_stage_id}' already exists")
                            else:
                                # Create new stage
                                new_stage = ConversationStage(
                                    stage_id=new_stage_id,
                                    name=new_stage_name,
                                    system_prompt=new_stage_prompt,
                                    user_prompt=new_stage_user_prompt if new_stage_user_prompt else None,
                                    next_stages=new_stage_next,
                                    completion_criteria={},
                                    max_turns=new_stage_max_turns
                                )
                                
                                # Add stage to flow
                                flow.stages[new_stage_id] = new_stage
                                
                                # Update flow
                                flow.name = flow_name
                                flow.description = flow_description
                                flow.initial_stage = initial_stage
                                
                                # Save flow
                                if save_conversation_flow(flow):
                                    st.success(f"Stage '{new_stage_name}' added successfully!")
                                    st.experimental_rerun()
                                else:
                                    st.error("Error adding stage")
                        else:
                            st.error("Stage ID, Name, and System Prompt are required")
                
                # Save flow button
                if st.button("Save Flow", key="save_flow"):
                    # Update flow
                    flow.name = flow_name
                    flow.description = flow_description
                    flow.initial_stage = initial_stage
                    
                    # Save flow
                    if save_conversation_flow(flow):
                        st.success(f"Flow '{flow_name}' saved successfully!")
                    else:
                        st.error("Error saving flow")
            else:
                st.error(f"Error loading flow: {edit_flow_id}")
    
    else:  # Create new flow
        st.subheader("Create New Flow")
        
        new_flow_id = st.text_input("Flow ID (unique identifier)", key="new_flow_id")
        new_flow_name = st.text_input("Flow Name", key="new_flow_name")
        new_flow_description = st.text_area("Flow Description", height=100, key="new_flow_desc")
        
        # Validate and create flow
        if st.button("Create Flow", key="create_flow"):
            if new_flow_id and new_flow_name:
                # Check if flow ID already exists
                existing_flow_ids = [flow["flow_id"] for flow in flows]
                if new_flow_id in existing_flow_ids:
                    st.error(f"Flow ID '{new_flow_id}' already exists")
                else:
                    # Create new flow
                    new_flow = ConversationFlow(
                        flow_id=new_flow_id,
                        name=new_flow_name,
                        description=new_flow_description,
                        initial_stage=None,
                        stages={}
                    )
                    
                    # Save flow
                    if save_conversation_flow(new_flow):
                        st.success(f"Flow '{new_flow_name}' created successfully!")
                        st.info("Now add stages to your flow using the Edit Existing Flow option.")
                        time.sleep(1)
                        st.experimental_rerun()
                    else:
                        st.error("Error creating flow")
            else:
                st.error("Flow ID and Name are required")

# Tab 3: Test Flow
with tabs[2]:
    st.header("Test Conversation Flow")
    
    # Select flow to test
    if flows:
        test_flow_id = st.selectbox(
            "Select a flow to test",
            options=[flow["flow_id"] for flow in flows],
            format_func=lambda x: next((flow["name"] for flow in flows if flow["flow_id"] == x), x),
            key="test_flow_select"
        )
        
        # Load the selected flow
        if test_flow_id:
            flow = load_conversation_flow(test_flow_id)
            
            if flow:
                # Initialize or retrieve conversation state
                if "conversation_state" not in st.session_state:
                    st.session_state.conversation_state = ConversationState(
                        flow_id=flow.flow_id,
                        current_stage_id=flow.initial_stage,
                        completed_stages=[],
                        stage_turns={flow.initial_stage: 0},
                        data={}
                    )
                
                # Reset conversation button
                if st.button("Reset Conversation"):
                    st.session_state.conversation_state = ConversationState(
                        flow_id=flow.flow_id,
                        current_stage_id=flow.initial_stage,
                        completed_stages=[],
                        stage_turns={flow.initial_stage: 0},
                        data={}
                    )
                    st.session_state.test_messages = []
                    st.experimental_rerun()
                
                # Initialize messages if needed
                if "test_messages" not in st.session_state:
                    st.session_state.test_messages = []
                
                # Get current stage
                current_stage_id = st.session_state.conversation_state.current_stage_id
                current_stage = flow.stages.get(current_stage_id)
                
                if current_stage:
                    # Display current stage information
                    st.subheader(f"Current Stage: {current_stage.name}")
                    
                    # Stage info expander
                    with st.expander("Stage Information"):
                        st.markdown(f"**Stage ID:** `{current_stage.stage_id}`")
                        st.markdown(f"**Turns in this stage:** {st.session_state.conversation_state.stage_turns.get(current_stage_id, 0)}/{current_stage.max_turns}")
                        
                        # Next stages
                        st.markdown("**Possible Next Stages:**")
                        if current_stage.next_stages:
                            for next_stage_id in current_stage.next_stages:
                                next_stage_name = flow.stages.get(next_stage_id, ConversationStage(next_stage_id, next_stage_id, "")).name
                                st.markdown(f"- `{next_stage_id}` ({next_stage_name})")
                        else:
                            st.markdown("- *Terminal stage (conversation will end)*")
                        
                        # Completion criteria
                        if current_stage.completion_criteria:
                            st.markdown("**Completion Criteria:**")
                            for criterion, description in current_stage.completion_criteria.items():
                                st.markdown(f"- **{criterion}:** {description}")
                        
                        # System prompt
                        st.markdown("**System Prompt:**")
                        st.text_area("", current_stage.system_prompt, height=150, key="test_system_prompt", disabled=True)
                    
                    # Display conversation
                    st.markdown("### Conversation")
                    
                    for message in st.session_state.test_messages:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])
                    
                    # If there are no messages yet, display the initial system message
                    if not st.session_state.test_messages:
                        with st.chat_message("assistant"):
                            # If there's a user prompt for this stage, display it
                            if current_stage.user_prompt:
                                st.markdown(current_stage.user_prompt)
                                # Add to messages
                                st.session_state.test_messages.append({
                                    "role": "assistant", 
                                    "content": current_stage.user_prompt
                                })
                            else:
                                # Generate a default message based on the system prompt
                                default_message = f"*[System: Now in the {current_stage.name} stage]*"
                                st.markdown(default_message)
                                # Add to messages
                                st.session_state.test_messages.append({
                                    "role": "assistant", 
                                    "content": default_message
                                })
                    
                    # User input
                    user_input = st.chat_input("Type your message here...")
                    
                    if user_input:
                        # Display user message
                        with st.chat_message("user"):
                            st.markdown(user_input)
                        
                        # Add to messages
                        st.session_state.test_messages.append({
                            "role": "user", 
                            "content": user_input
                        })
                        
                        # Process the user input
                        from conversation_flow import process_conversation_turn, get_mistral_client
                        
                        client = get_mistral_client()
                        if client:
                            # Get system message and updated state
                            system_message, updated_state = process_conversation_turn(
                                user_message=user_input,
                                conversation_state=st.session_state.conversation_state,
                                conversation_flow=flow,
                                client=client
                            )
                            
                            # Update conversation state
                            st.session_state.conversation_state = updated_state
                            
                            # Generate assistant response
                            try:
                                # Create messages for the API call
                                messages = [{"role": "system", "content": system_message}]
                                
                                # Add conversation history
                                for msg in st.session_state.test_messages:
                                    messages.append({"role": msg["role"], "content": msg["content"]})
                                
                                # Get response from Mistral
                                response = client.chat.complete(
                                    model=config.get("model", "mistral-small-latest"),
                                    messages=messages,
                                    temperature=0.7,
                                    max_tokens=500
                                )
                                
                                assistant_message = response.choices[0].message.content
                                
                                # Check if stage changed
                                old_stage_id = current_stage_id
                                new_stage_id = st.session_state.conversation_state.current_stage_id
                                
                                if old_stage_id != new_stage_id:
                                    # Stage changed, add a system message
                                    new_stage = flow.stages.get(new_stage_id)
                                    if new_stage:
                                        transition_message = f"*[System: Moving from {current_stage.name} to {new_stage.name} stage]*"
                                        
                                        with st.chat_message("system"):
                                            st.markdown(transition_message)
                                        
                                        # Add to messages
                                        st.session_state.test_messages.append({
                                            "role": "system", 
                                            "content": transition_message
                                        })
                                
                                # Display assistant response
                                with st.chat_message("assistant"):
                                    st.markdown(assistant_message)
                                
                                # Add to messages
                                st.session_state.test_messages.append({
                                    "role": "assistant", 
                                    "content": assistant_message
                                })
                                
                                # If new stage has a user prompt, display it
                                if old_stage_id != new_stage_id:
                                    new_stage = flow.stages.get(new_stage_id)
                                    if new_stage and new_stage.user_prompt:
                                        with st.chat_message("assistant"):
                                            st.markdown(new_stage.user_prompt)
                                        
                                        # Add to messages
                                        st.session_state.test_messages.append({
                                            "role": "assistant", 
                                            "content": new_stage.user_prompt
                                        })
                                
                                # Rerun to update the UI
                                st.experimental_rerun()
                                
                            except Exception as e:
                                st.error(f"Error generating response: {str(e)}")
                        else:
                            st.error("Could not initialize Mistral client. Please check your API key.")
                else:
                    st.error(f"Invalid stage ID: {current_stage_id}")
            else:
                st.error(f"Error loading flow: {test_flow_id}")
    else:
        st.info("No conversation flows found. Create or import a flow first.")

# Tab 4: Import/Export
with tabs[3]:
    st.header("Import/Export Conversation Flows")
    
    # Export flow
    st.subheader("Export Flow")
    
    if flows:
        export_flow_id = st.selectbox(
            "Select a flow to export",
            options=[flow["flow_id"] for flow in flows],
            format_func=lambda x: next((flow["name"] for flow in flows if flow["flow_id"] == x), x),
            key="export_flow_select"
        )
        
        if export_flow_id:
            flow = load_conversation_flow(export_flow_id)
            
            if flow:
                # Convert flow to JSON
                flow_json = json.dumps(flow.to_dict(), indent=2)
                
                # Provide download button
                st.download_button(
                    label="Download Flow as JSON",
                    data=flow_json,
                    file_name=f"{flow.flow_id}.json",
                    mime="application/json"
                )
    else:
        st.info("No conversation flows found to export.")
    
    # Import flow
    st.subheader("Import Flow")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload Flow JSON", type=["json"])
    
    if uploaded_file:
        try:
            # Load the JSON data
            flow_data = json.load(uploaded_file)
            
            # Preview flow data
            st.json(flow_data)
            
            # Import button
            if st.button("Import Flow"):
                # Check if flow ID already exists
                existing_flow_ids = [flow["flow_id"] for flow in flows]
                flow_id = flow_data.get("flow_id", "")
                
                if flow_id in existing_flow_ids:
                    # Ask to overwrite
                    if st.checkbox(f"Flow ID '{flow_id}' already exists. Overwrite?"):
                        # Create flow from data
                        flow = ConversationFlow.from_dict(flow_data)
                        
                        # Save flow
                        if save_conversation_flow(flow):
                            st.success(f"Flow '{flow.name}' imported successfully!")
                            time.sleep(1)
                            st.experimental_rerun()
                        else:
                            st.error("Error importing flow")
                else:
                    # Create flow from data
                    flow = ConversationFlow.from_dict(flow_data)
                    
                    # Save flow
                    if save_conversation_flow(flow):
                        st.success(f"Flow '{flow.name}' imported successfully!")
                        time.sleep(1)
                        st.experimental_rerun()
                    else:
                        st.error("Error importing flow")
        except json.JSONDecodeError:
            st.error("Invalid JSON file")
        except Exception as e:
            st.error(f"Error importing flow: {str(e)}")

# Add helpful information
st.markdown("---")
with st.expander("About Conversation Flows"):
    st.markdown("""
    ### Benefits of Using Conversation Flows
    
    - **Structured Interactions**: Guide conversations through logical stages
    - **Consistent Experience**: Ensure conversations follow best practices
    - **Context Awareness**: Each stage has specific goals and context
    - **Specialized Prompts**: Optimize AI behavior for different parts of a conversation
    - **Process Automation**: Automate complex conversation patterns
    
    ### Example Use Cases
    
    - **Customer Support**: Guide users through problem identification, troubleshooting, and resolution
    - **Interviews**: Structure job interviews with appropriate questions for each phase
    - **Educational Tutorials**: Step through learning material in a pedagogical sequence
    - **Medical Screening**: Systematically gather patient information
    - **Sales Conversations**: Guide potential customers through discovery, demonstration, and closing
    
    ### Getting Started
    
    1. Browse existing flows or create a new one
    2. Define stages with appropriate prompts
    3. Set up transitions between stages
    4. Test your flow in the test environment
    5. Use it in regular chat with the `/flow` command
    """)