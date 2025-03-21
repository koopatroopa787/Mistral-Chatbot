import os
import streamlit as st
import sys
import json
from pathlib import Path
import time

# Add the parent directory to the path so we can import the helper modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Check if the response_grader module is available
try:
    from response_grader import (
        grade_response, 
        create_grading_criteria, 
        load_grading_templates, 
        save_grading_template,
        get_mistral_client
    )
    has_grader = True
except ImportError:
    has_grader = False
    st.error("Response grading module not found. Make sure response_grader.py is in the main directory.")

from helper_functions import setup_logging, load_config

# Setup
logger = setup_logging()
config = load_config()

# Page configuration
st.set_page_config(
    page_title="Response Grading - Mistral AI Assistant",
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

if not has_grader:
    st.error("The Response Grading feature requires the response_grader.py module. Make sure it exists in your main directory.")
    st.stop()

# Templates
templates = load_grading_templates()

# Sidebar
with st.sidebar:
    st.title("Response Grading")
    st.markdown("Grade user responses and improve AI replies with automated assessment.")
    
    # Available templates
    st.subheader("Saved Templates")
    if templates:
        template_options = list(templates.keys())
        selected_template = st.selectbox(
            "Select a template", 
            options=["None"] + template_options
        )
    else:
        st.info("No saved templates found.")
        selected_template = "None"
    
    # Link back to chat
    st.markdown("---")
    st.markdown("[Back to Chat](/Chat)", unsafe_allow_html=True)

# Main content
st.title("Response Grading")

# Create tabs for different grading functions
tab1, tab2, tab3 = st.tabs(["Simple Grading", "Advanced Grading", "Manage Templates"])

# Tab 1: Simple Grading
with tab1:
    st.header("Simple Response Grading")
    st.markdown("Grade a response quickly without complex settings.")
    
    # Question or prompt
    question = st.text_area("Question or Prompt", 
                           height=100,
                           placeholder="Enter the question or prompt the response is addressing...",
                           key="simple_question")  # Added unique key
    
    # User response
    user_response = st.text_area("User Response to Grade", 
                                height=200,
                                placeholder="Enter the user's response to be graded...",
                                key="simple_response")  # Added unique key
    
    # Subject selection for appropriate criteria
    subject_options = ["General", "Math", "Science", "History", "English", "Programming"]
    subject = st.selectbox("Subject Area", options=subject_options, key="simple_subject")  # Added unique key
    
    # Difficulty level
    difficulty = st.select_slider(
        "Difficulty Level",
        options=["Easy", "Medium", "Hard"],
        value="Medium",
        key="simple_difficulty"  # Added unique key
    )
    
    # Grade button
    if st.button("Grade Response", key="simple_grade") and user_response:
        with st.status("Grading response..."):
            # Use the selected template if available
            if selected_template != "None":
                template = templates[selected_template]
                criteria = template.get("criteria")
                reference_answer = template.get("reference_answer")
                context = template.get("context") or question
            else:
                # Create criteria based on subject and difficulty
                criteria = create_grading_criteria(
                    subject=subject, 
                    difficulty=difficulty.lower()
                )
                reference_answer = None
                context = question
            
            # Grade the response
            client = get_mistral_client()
            grading_result = grade_response(
                user_response=user_response,
                context=context,
                criteria=criteria,
                reference_answer=reference_answer,
                client=client
            )
            
            if grading_result:
                # Display score
                score = grading_result.get("score", 0)
                feedback = grading_result.get("feedback", "")
                
                # Calculate score color
                if score >= 8:
                    score_color = "green"
                elif score >= 6:
                    score_color = "orange"
                else:
                    score_color = "red"
                
                # Display score and feedback
                st.markdown(f"## Score: <span style='color:{score_color};'>{score}/10</span>", unsafe_allow_html=True)
                st.markdown(f"**Overall Assessment:** {feedback}")
                
                # Display strengths
                strengths = grading_result.get("strengths", [])
                if strengths:
                    st.markdown("### Strengths")
                    for strength in strengths:
                        st.markdown(f"✅ {strength}")
                
                # Display weaknesses
                weaknesses = grading_result.get("weaknesses", [])
                if weaknesses:
                    st.markdown("### Areas for Improvement")
                    for weakness in weaknesses:
                        st.markdown(f"⚠️ {weakness}")
                
                # Display suggestions
                suggestions = grading_result.get("suggestions", [])
                if suggestions:
                    st.markdown("### Suggestions")
                    for suggestion in suggestions:
                        st.markdown(f"💡 {suggestion}")
                
                # Save as template option
                st.divider()
                with st.expander("Save as Template"):
                    template_name = st.text_input("Template Name", 
                                                 value=f"{subject}_{difficulty}_Template",
                                                 key="simple_template_name")  # Added unique key
                    if st.button("Save Template", key="simple_save_template"):  # Added unique key
                        success = save_grading_template(
                            template_name=template_name,
                            criteria=criteria,
                            reference_answer=reference_answer,
                            context=context
                        )
                        if success:
                            st.success(f"Template '{template_name}' saved successfully!")
                            # Refresh templates
                            templates = load_grading_templates()
                        else:
                            st.error("Error saving template.")
            else:
                st.error("Error grading response. Please try again.")

# Tab 2: Advanced Grading
with tab2:
    st.header("Advanced Response Grading")
    st.markdown("Customize your grading criteria, set reference answers, and more.")
    
    # Load template data if selected
    if selected_template != "None":
        template = templates[selected_template]
        default_question = template.get("context", "")
        default_reference = template.get("reference_answer", "")
        template_criteria = template.get("criteria", {})
    else:
        default_question = ""
        default_reference = ""
        template_criteria = {}
    
    # Question or prompt
    question = st.text_area("Question or Prompt", 
                           value=default_question,
                           height=100,
                           placeholder="Enter the question or prompt the response is addressing...",
                           key="advanced_question")  # Added unique key
    
    # Reference answer
    reference_answer = st.text_area("Reference Answer (Optional)", 
                                    value=default_reference,
                                    height=150,
                                    placeholder="Enter a model answer to compare against...",
                                    key="advanced_reference")  # Added unique key
    
    # User response
    user_response = st.text_area("User Response to Grade", 
                                height=200,
                                placeholder="Enter the user's response to be graded...",
                                key="advanced_response")  # Added unique key
    
    # Custom criteria
    st.subheader("Grading Criteria")
    
    # Start with template criteria or defaults
    if template_criteria:
        criteria = template_criteria.copy()
    else:
        criteria = {
            "accuracy": "Correctness of the information and concepts",
            "completeness": "Coverage of all relevant points",
            "clarity": "Clear explanation and logical structure",
            "analysis": "Depth of analysis and critical thinking"
        }
    
    # Display existing criteria
    criteria_list = []
    for criterion, description in criteria.items():
        criteria_list.append({"name": criterion, "description": description})
    
    # Allow editing of criteria
    updated_criteria = {}
    st.markdown("Edit existing criteria or add new ones")
    
    # Custom criteria editor
    for i, criterion in enumerate(criteria_list):
        col1, col2, col3 = st.columns([3, 6, 1])
        with col1:
            criterion_name = st.text_input(f"Criterion {i+1} Name", 
                                           value=criterion["name"],
                                           key=f"criterion_name_{i}")
        with col2:
            criterion_desc = st.text_input(f"Description", 
                                           value=criterion["description"],
                                           key=f"criterion_desc_{i}")
        with col3:
            st.write("")
            st.write("")
            remove = st.checkbox("Remove", key=f"remove_{i}")
        
        if not remove and criterion_name:
            updated_criteria[criterion_name] = criterion_desc
    
    # Add new criterion button
    if st.button("Add New Criterion", key="add_criterion"):  # Added unique key
        criteria_list.append({"name": "", "description": ""})
    
    # Grading settings
    st.subheader("Grading Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        sensitivity = st.select_slider(
            "Grading Sensitivity",
            options=["Lenient", "Balanced", "Strict"],
            value="Balanced",
            help="Determines how strictly the response will be evaluated",
            key="advanced_sensitivity"  # Added unique key
        )
    
    with col2:
        feedback_detail = st.select_slider(
            "Feedback Detail",
            options=["Minimal", "Standard", "Detailed"],
            value="Standard",
            help="Amount of detail in the feedback",
            key="advanced_feedback_detail"  # Added unique key
        )
    
    # Grade button
    if st.button("Grade Response", key="advanced_grade") and user_response:
        with st.status("Grading response..."):
            # Add sensitivity and detail to the criteria
            grading_context = f"""
            Question: {question}
            
            Grading Sensitivity: {sensitivity}
            Feedback Detail: {feedback_detail}
            """
            
            # Grade the response
            client = get_mistral_client()
            grading_result = grade_response(
                user_response=user_response,
                context=grading_context,
                criteria=updated_criteria,
                reference_answer=reference_answer,
                client=client
            )
            
            if grading_result:
                # Display score
                score = grading_result.get("score", 0)
                feedback = grading_result.get("feedback", "")
                
                # Calculate score color
                if score >= 8:
                    score_color = "green"
                elif score >= 6:
                    score_color = "orange"
                else:
                    score_color = "red"
                
                # Display score and feedback
                st.markdown(f"## Score: <span style='color:{score_color};'>{score}/10</span>", unsafe_allow_html=True)
                st.markdown(f"**Overall Assessment:** {feedback}")
                
                # Display strengths
                strengths = grading_result.get("strengths", [])
                if strengths:
                    st.markdown("### Strengths")
                    for strength in strengths:
                        st.markdown(f"✅ {strength}")
                
                # Display weaknesses
                weaknesses = grading_result.get("weaknesses", [])
                if weaknesses:
                    st.markdown("### Areas for Improvement")
                    for weakness in weaknesses:
                        st.markdown(f"⚠️ {weakness}")
                
                # Display suggestions
                suggestions = grading_result.get("suggestions", [])
                if suggestions:
                    st.markdown("### Suggestions")
                    for suggestion in suggestions:
                        st.markdown(f"💡 {suggestion}")
                
                # Save as template option
                st.divider()
                with st.expander("Save as Template"):
                    template_name = st.text_input("Template Name", 
                                                 value="Custom_Grading_Template",
                                                 key="advanced_template_name")  # Added unique key
                    if st.button("Save Template", key="advanced_save_template"):  # Added unique key
                        success = save_grading_template(
                            template_name=template_name,
                            criteria=updated_criteria,
                            reference_answer=reference_answer,
                            context=question
                        )
                        if success:
                            st.success(f"Template '{template_name}' saved successfully!")
                            # Refresh templates
                            templates = load_grading_templates()
                        else:
                            st.error("Error saving template.")
            else:
                st.error("Error grading response. Please try again.")

# Tab 3: Manage Templates
with tab3:
    st.header("Manage Grading Templates")
    
    # Display and manage templates
    if templates:
        st.subheader("Saved Templates")
        
        for template_name, template in templates.items():
            with st.expander(template_name):
                # Display template details
                st.markdown("**Context/Question:**")
                st.text(template.get("context", "None"))
                
                st.markdown("**Criteria:**")
                for criterion, description in template.get("criteria", {}).items():
                    st.markdown(f"- **{criterion}**: {description}")
                
                st.markdown("**Reference Answer:**")
                if template.get("reference_answer"):
                    st.text(template.get("reference_answer"))
                else:
                    st.text("None")
                
                # Delete button
                if st.button("Delete Template", key=f"delete_{template_name}"):
                    template_path = Path("grading_templates") / f"{template_name}.json"
                    if template_path.exists():
                        try:
                            os.remove(template_path)
                            st.success(f"Template '{template_name}' deleted successfully!")
                            # Refresh templates
                            templates = load_grading_templates()
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error deleting template: {str(e)}")
    else:
        st.info("No saved templates found. Create a template by grading a response and saving it.")
    
    # Create new template from scratch
    st.subheader("Create New Template")
    
    with st.expander("Create Template"):
        new_template_name = st.text_input("Template Name", value="New_Template", key="new_template_name")  # Added unique key
        new_template_context = st.text_area("Context/Question", height=100, key="new_template_context")  # Added unique key
        new_template_reference = st.text_area("Reference Answer (Optional)", height=150, key="new_template_reference")  # Added unique key
        
        st.markdown("**Criteria**")
        new_criteria = {}
        
        # Default criteria
        default_criteria = create_grading_criteria("general", "medium")
        
        # Display criteria editor
        for i, (criterion, description) in enumerate(default_criteria.items()):
            col1, col2, col3 = st.columns([3, 6, 1])
            with col1:
                criterion_name = st.text_input(f"Criterion {i+1} Name", 
                                              value=criterion,
                                              key=f"new_criterion_name_{i}")
            with col2:
                criterion_desc = st.text_input(f"Description", 
                                              value=description,
                                              key=f"new_criterion_desc_{i}")
            with col3:
                st.write("")
                st.write("")
                remove = st.checkbox("Remove", key=f"new_remove_{i}")
            
            if not remove and criterion_name:
                new_criteria[criterion_name] = criterion_desc
        
        # Save button
        if st.button("Save New Template", key="save_new_template"):  # Added unique key
            if new_template_name:
                success = save_grading_template(
                    template_name=new_template_name,
                    criteria=new_criteria,
                    reference_answer=new_template_reference,
                    context=new_template_context
                )
                if success:
                    st.success(f"Template '{new_template_name}' created successfully!")
                    # Refresh templates
                    templates = load_grading_templates()
                    st.experimental_rerun()
                else:
                    st.error("Error creating template.")
            else:
                st.error("Please provide a template name.")

# Add helpful information
st.markdown("---")
with st.expander("About Response Grading"):
    st.markdown("""
    ### How Response Grading Works

    The Response Grading feature uses Mistral AI to evaluate responses based on specified criteria. 
    This feature is particularly useful for:

    - **Educational Applications**: Grade answers to questions for learning assessment
    - **Self-assessment**: Evaluate your own responses to improve understanding
    - **Content Evaluation**: Assess the quality of written content
    - **Interview Preparation**: Evaluate practice answers to interview questions

    ### Grading Process

    1. **Input**: The system takes the user's response, the question/prompt, optional reference answer, and grading criteria
    2. **Analysis**: Mistral AI evaluates the response based on the criteria
    3. **Output**: The system provides a score, feedback, strengths, weaknesses, and suggestions

    ### Templates

    Templates allow you to save grading configurations for reuse, including:
    - Questions/prompts
    - Reference answers
    - Custom grading criteria

    ### Integration with Chat

    You can integrate response grading with the chat interface by using the `/grade` command followed by your response. 
    This will automatically grade your response and provide feedback.
    """)