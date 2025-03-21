import os
import streamlit as st
from mistralai import Mistral
import json
from pathlib import Path
import sys
import datetime

# Add the parent directory to the path so we can import the helper modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper_functions import setup_logging, load_config
from index_functions import search_index, load_index

# Setup
logger = setup_logging()
config = load_config()

# Page configuration
st.set_page_config(
    page_title="Reports - Mistral AI Assistant",
    page_icon="📊",
    layout="wide",
)

# Initialize Mistral client
@st.cache_resource
def get_mistral_client():
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        st.error("Missing API key. Please set your Mistral API Key on the Home page.")
        return None
    return Mistral(api_key=api_key)

# Check if the client is available
client = get_mistral_client()
if not client:
    st.stop()

# Sidebar
with st.sidebar:
    st.title("Report Generation")
    st.markdown("Generate reports from your conversations or documents")
    
    # Link back to chat
    st.markdown("---")
    st.markdown("[Back to Chat](/Chat)", unsafe_allow_html=True)

# Main content
st.title("Report Generation")

# Create tabs for different report types
tab1, tab2, tab3 = st.tabs(["Conversation Summary", "Document Analysis", "Custom Report"])

# Tab 1: Conversation Summary
with tab1:
    st.header("Conversation Summary Report")
    st.markdown("Generate a summary report from a saved conversation")
    
    # Get list of saved conversations
    os.makedirs("conversations", exist_ok=True)
    conversation_files = list(Path("conversations").glob("*.json"))
    conversation_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not conversation_files:
        st.info("No saved conversations found. You can save conversations from the Chat page.")
    else:
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
                conversation_options.append((label, file, messages))
            except:
                # Skip invalid files
                continue
        
        if conversation_options:
            # Extract just the labels for the selectbox
            labels = [label for label, _, _ in conversation_options]
            selected_label = st.selectbox("Select conversation", labels)
            
            # Find the selected file and messages
            selected_data = next((data for label, _, data in conversation_options if label == selected_label), None)
            
            if selected_data:
                # Display options for report generation
                st.subheader("Report Options")
                
                report_type = st.radio(
                    "Report Type",
                    options=["Executive Summary", "Detailed Analysis", "Key Points", "Action Items"]
                )
                
                include_timestamps = st.checkbox("Include timestamps", value=False)
                
                if st.button("Generate Report"):
                    with st.status("Generating report..."):
                        # Prepare prompt based on report type
                        if report_type == "Executive Summary":
                            system_prompt = "You are an executive assistant tasked with creating a concise executive summary of a conversation. Focus on the main points, decisions, and outcomes. The summary should be professional and to the point."
                        elif report_type == "Detailed Analysis":
                            system_prompt = "You are a business analyst tasked with creating a detailed analysis of a conversation. Analyze the main topics, insights, challenges, and opportunities discussed. Include recommendations where appropriate."
                        elif report_type == "Key Points":
                            system_prompt = "You are a note-taker tasked with extracting key points from a conversation. Create a bulleted list of the most important points, organized by topic."
                        else:  # Action Items
                            system_prompt = "You are a project manager tasked with extracting action items from a conversation. Create a list of specific tasks, who is responsible (if mentioned), and any deadlines or priorities (if mentioned)."
                        
                        # Create a prompt for the report
                        prompt = f"""
                        Based on the following conversation, create a {report_type}.
                        
                        {f"Include timestamps in the report." if include_timestamps else ""}
                        
                        Format the report in Markdown with clear headings, bullet points, and sections.
                        """
                        
                        # Prepare the conversation as context
                        conversation_text = ""
                        for msg in selected_data:
                            role = msg["role"]
                            content = msg["content"]
                            conversation_text += f"{role.upper()}: {content}\n\n"
                        
                        # Get response from Mistral
                        try:
                            response = client.chat.complete(
                                model=config["model"],
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": prompt + "\n\nCONVERSATION:\n" + conversation_text}
                                ],
                                temperature=0.3,  # Lower temperature for more focused output
                                max_tokens=2000
                            )
                            
                            report_content = response.choices[0].message.content
                            
                            # Display the report
                            st.subheader(f"{report_type} Report")
                            st.markdown(report_content)
                            
                            # Provide download option
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            report_filename = f"{report_type.lower().replace(' ', '_')}_{timestamp}.md"
                            
                            st.download_button(
                                label="Download Report",
                                data=report_content,
                                file_name=report_filename,
                                mime="text/markdown"
                            )
                            
                        except Exception as e:
                            st.error(f"Error generating report: {str(e)}")
        else:
            st.warning("No valid conversation files found.")

# Tab 2: Document Analysis
with tab2:
    st.header("Document Analysis Report")
    st.markdown("Generate an analysis report from your indexed documents")
    
    # Check if index is loaded
    index_loaded = load_index()
    
    if not index_loaded:
        st.warning("No document index found. Please index documents first in the Document Index page.")
    else:
        # Display options for document analysis
        st.subheader("Analysis Options")
        
        analysis_type = st.radio(
            "Analysis Type",
            options=["Summary", "Key Concepts", "Comparative Analysis"]
        )
        
        # For summary and key concepts, we need a query to find relevant documents
        if analysis_type in ["Summary", "Key Concepts"]:
            query = st.text_input("Enter a topic or query to analyze", 
                                 help="This will be used to find relevant documents in your index")
            
            if st.button("Generate Analysis") and query:
                with st.status("Searching documents and generating analysis..."):
                    # Search for relevant documents
                    context = search_index(query, logger, top_k=5)
                    
                    if not context:
                        st.error("No relevant documents found. Try a different query.")
                    else:
                        # Prepare prompt based on analysis type
                        if analysis_type == "Summary":
                            system_prompt = "You are a research assistant tasked with creating a concise summary of documents related to a specific topic. Focus on the main points and insights."
                            prompt = f"""
                            Create a comprehensive summary of the following documents related to: "{query}".
                            
                            Organize the summary with clear headings and sections. Include citations to the source documents where appropriate.
                            Format the report in Markdown.
                            """
                        else:  # Key Concepts
                            system_prompt = "You are a knowledge manager tasked with extracting and explaining key concepts from documents related to a specific topic."
                            prompt = f"""
                            Extract and explain the key concepts from the following documents related to: "{query}".
                            
                            For each key concept:
                            1. Provide a clear definition
                            2. Explain its significance
                            3. Note how it relates to other concepts (if applicable)
                            
                            Format the report in Markdown with clear headings for each concept.
                            """
                        
                        # Get response from Mistral
                        try:
                            response = client.chat.complete(
                                model=config["model"],
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": prompt + "\n\nDOCUMENTS:\n" + context}
                                ],
                                temperature=0.3,
                                max_tokens=2000
                            )
                            
                            analysis_content = response.choices[0].message.content
                            
                            # Display the analysis
                            st.subheader(f"{analysis_type} Report")
                            st.markdown(analysis_content)
                            
                            # Provide download option
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            analysis_filename = f"{analysis_type.lower()}_{timestamp}.md"
                            
                            st.download_button(
                                label="Download Analysis",
                                data=analysis_content,
                                file_name=analysis_filename,
                                mime="text/markdown"
                            )
                            
                        except Exception as e:
                            st.error(f"Error generating analysis: {str(e)}")
        
        # For comparative analysis, we need two queries
        else:  # Comparative Analysis
            col1, col2 = st.columns(2)
            
            with col1:
                query1 = st.text_input("First topic", help="Enter the first topic to compare")
            
            with col2:
                query2 = st.text_input("Second topic", help="Enter the second topic to compare")
            
            if st.button("Generate Comparison") and query1 and query2:
                with st.status("Searching documents and generating comparison..."):
                    # Search for relevant documents for both topics
                    context1 = search_index(query1, logger, top_k=3)
                    context2 = search_index(query2, logger, top_k=3)
                    
                    if not context1 or not context2:
                        st.error("Insufficient relevant documents found for one or both topics.")
                    else:
                        system_prompt = "You are a research analyst tasked with comparing and contrasting two topics based on document evidence."
                        prompt = f"""
                        Create a comparative analysis between "{query1}" and "{query2}" based on the provided documents.
                        
                        Include the following sections:
                        1. Overview of each topic
                        2. Similarities
                        3. Differences
                        4. Implications or insights from this comparison
                        
                        Format the report in Markdown with clear headings and tables where appropriate.
                        """
                        
                        # Get response from Mistral
                        try:
                            response = client.chat.complete(
                                model=config["model"],
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": prompt + f"\n\nDOCUMENTS ON {query1}:\n{context1}\n\nDOCUMENTS ON {query2}:\n{context2}"}
                                ],
                                temperature=0.3,
                                max_tokens=2000
                            )
                            
                            comparison_content = response.choices[0].message.content
                            
                            # Display the comparison
                            st.subheader("Comparative Analysis Report")
                            st.markdown(comparison_content)
                            
                            # Provide download option
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            comparison_filename = f"comparison_{timestamp}.md"
                            
                            st.download_button(
                                label="Download Comparison",
                                data=comparison_content,
                                file_name=comparison_filename,
                                mime="text/markdown"
                            )
                            
                        except Exception as e:
                            st.error(f"Error generating comparison: {str(e)}")

# Tab 3: Custom Report
with tab3:
    st.header("Custom Report")
    st.markdown("Generate a custom report based on your specifications")
    
    # Report title
    report_title = st.text_input("Report Title", "Custom Analysis Report")
    
    # Report input options
    input_source = st.radio(
        "Input Source",
        options=["Conversation", "Documents", "Custom Text"]
    )
    
    # Input content based on selected source
    if input_source == "Conversation":
        # Get list of saved conversations
        os.makedirs("conversations", exist_ok=True)
        conversation_files = list(Path("conversations").glob("*.json"))
        conversation_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not conversation_files:
            st.info("No saved conversations found. You can save conversations from the Chat page.")
            input_content = ""
        else:
            # Create select box with conversation dates
            conversation_options = []
            for file in conversation_files:
                try:
                    # Get creation time
                    timestamp = file.stat().st_mtime
                    date_str = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Create option label
                    label = f"{date_str}"
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
                
                # Load the conversation
                try:
                    with open(selected_file, "r") as f:
                        messages = json.load(f)
                    
                    # Convert messages to text
                    input_content = ""
                    for msg in messages:
                        role = msg["role"]
                        content = msg["content"]
                        input_content += f"{role.upper()}: {content}\n\n"
                except:
                    st.error("Error loading conversation.")
                    input_content = ""
            else:
                st.warning("No valid conversation files found.")
                input_content = ""
    
    elif input_source == "Documents":
        # Check if index is loaded
        index_loaded = load_index()
        
        if not index_loaded:
            st.warning("No document index found. Please index documents first in the Document Index page.")
            input_content = ""
        else:
            query = st.text_input("Enter a topic or query to analyze",
                               help="This will be used to find relevant documents in your index")
            
            if query:
                # Search for relevant documents
                context = search_index(query, logger, top_k=5)
                
                if not context:
                    st.error("No relevant documents found. Try a different query.")
                    input_content = ""
                else:
                    input_content = context
            else:
                input_content = ""
    
    else:  # Custom Text
        input_content = st.text_area("Enter or paste your text here", height=200)
    
    # Report format and structure
    st.subheader("Report Format")
    
    report_format = st.selectbox(
        "Report Format",
        options=[
            "Standard Report", 
            "Bulleted Summary", 
            "FAQ Style",
            "Technical Documentation",
            "Newsletter",
            "Academic Paper"
        ]
    )
    
    # Additional instructions
    additional_instructions = st.text_area(
        "Additional Instructions (optional)",
        placeholder="Add any specific requirements or instructions for the report...",
        height=100
    )
    
    # Generate the report
    if st.button("Generate Custom Report") and input_content:
        with st.status("Generating custom report..."):
            # Prepare system prompt based on report format
            if report_format == "Standard Report":
                system_prompt = "You are a professional report writer tasked with creating a clear and well-structured report."
            elif report_format == "Bulleted Summary":
                system_prompt = "You are a professional summarizer tasked with creating a concise, bullet-point summary of information."
            elif report_format == "FAQ Style":
                system_prompt = "You are a knowledge base manager tasked with organizing information into a FAQ format with questions and detailed answers."
            elif report_format == "Technical Documentation":
                system_prompt = "You are a technical writer tasked with creating clear, precise documentation with appropriate technical details and explanations."
            elif report_format == "Newsletter":
                system_prompt = "You are a newsletter editor tasked with creating an engaging newsletter with key information and highlights."
            else:  # Academic Paper
                system_prompt = "You are an academic researcher tasked with organizing information into a formal academic paper structure."
            
            # Create a prompt for the report
            prompt = f"""
            Create a {report_format} titled "{report_title}" based on the following information.
            
            {additional_instructions if additional_instructions else ""}
            
            Format the report in Markdown with appropriate headings, sections, and formatting.
            """
            
            # Get response from Mistral
            try:
                response = client.chat.complete(
                    model=config["model"],
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt + "\n\nINFORMATION:\n" + input_content}
                    ],
                    temperature=0.4,
                    max_tokens=3000
                )
                
                report_content = response.choices[0].message.content
                
                # Display the report
                st.subheader(report_title)
                st.markdown(report_content)
                
                # Provide download option
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                report_filename = f"{report_title.lower().replace(' ', '_')}_{timestamp}.md"
                
                st.download_button(
                    label="Download Report",
                    data=report_content,
                    file_name=report_filename,
                    mime="text/markdown"
                )
                
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")

# Add helpful information
with st.expander("About Report Generation"):
    st.markdown("""
    ### How Report Generation Works

    The report generation feature uses Mistral AI's language capabilities to analyze and summarize information from various sources:

    1. **Conversation Summaries**: Extracts key points, action items, or creates executive summaries from your saved conversations.
    2. **Document Analysis**: Generates summaries, extracts key concepts, or compares topics based on your indexed documents.
    3. **Custom Reports**: Creates tailored reports from any source in various formats to suit your needs.

    ### Best Practices for Quality Reports

    - **Be Specific**: Provide clear topics or queries when searching documents
    - **Choose the Right Format**: Select the report format that best matches your needs
    - **Add Custom Instructions**: Use the additional instructions field to specify exactly what you want
    - **Review and Edit**: AI-generated reports are a starting point - review and refine as needed

    ### Report Formats

    - **Standard Report**: Traditional structured report with introduction, body, and conclusion
    - **Bulleted Summary**: Concise bullet points organized by topic
    - **FAQ Style**: Information organized as questions and answers
    - **Technical Documentation**: Detailed technical explanations with precise language
    - **Newsletter**: Engaging format with highlights and key points
    - **Academic Paper**: Formal structure with introduction, methodology, results, and discussion
    """)