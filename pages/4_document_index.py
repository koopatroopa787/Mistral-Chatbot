import os
import streamlit as st
from pathlib import Path
import sys
import json

# Add the parent directory to the path so we can import the helper modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from helper_functions import setup_logging, extract_text_from_file
from index_functions import create_index, load_index, get_index_stats
from document_processor import process_document, get_mistral_client

# Setup
logger = setup_logging()

# Page configuration
st.set_page_config(
    page_title="Document Index - Mistral AI Assistant",
    page_icon="📚",
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
    st.title("Document Index")
    st.markdown("Manage your document index here. Upload files or specify a folder path to index documents.")
    
    # Toggle for advanced document processing
    use_advanced_processing = st.toggle(
        "Enable Advanced Processing",
        value=True,
        help="When enabled, documents will be tokenized, summarized, and have keywords extracted"
    )
    
    # Link back to chat
    st.markdown("---")
    st.markdown("[Back to Chat](/Chat)", unsafe_allow_html=True)

# Main content
st.title("Document Index Management")

# Create tabs for different document management functions
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Upload Files", "Index Folder", "Index Status", "Document Preview", "Manage Index"])

# Tab 1: Upload Files
with tab1:
    st.header("Upload Files for Indexing")
    
    # File uploader for document indexing
    uploaded_files = st.file_uploader(
        "Upload documents for indexing", 
        accept_multiple_files=True, 
        type=["txt", "md", "pdf", "csv", "json", "py", "js", "html", "css"]
    )
    
    if uploaded_files:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            index_button = st.button(
                "Index Uploaded Files", 
                key="index_uploads",
                help="Process and index the uploaded files"
            )
        
        with col2:
            if use_advanced_processing:
                st.info("Advanced processing enabled")
            else:
                st.warning("Standard processing only")
        
        if index_button:
            # Create a temporary directory for uploaded files
            temp_dir = Path("uploaded_files")
            temp_dir.mkdir(exist_ok=True)
            
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            # Save uploaded files to temp directory
            progress_text.text("Saving uploaded files...")
            for i, uploaded_file in enumerate(uploaded_files):
                file_path = temp_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            # Index the files
            progress_text.text("Indexing documents...")
            create_index(str(temp_dir), logger, use_advanced_processing=use_advanced_processing)
            
            # Show success message
            progress_text.empty()
            progress_bar.empty()
            st.success(f"Indexed {len(uploaded_files)} documents successfully!")

# Tab 2: Index Folder
with tab2:
    st.header("Index Documents from Folder")
    
    # Folder path for indexing
    folder_path = st.text_input("Enter a folder path to index", value="")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Validate Path", key="validate_path") and folder_path:
            path = Path(folder_path)
            if path.exists() and path.is_dir():
                # Get file count and types
                files = list(path.glob("**/*"))
                files = [f for f in files if f.is_file()]
                
                file_types = {}
                for f in files:
                    ext = f.suffix.lower()
                    if ext in file_types:
                        file_types[ext] += 1
                    else:
                        file_types[ext] = 1
                
                st.success(f"Valid folder with {len(files)} files")
                st.write("File types found:")
                for ext, count in file_types.items():
                    st.write(f"- {ext}: {count} files")
            else:
                st.error("Invalid folder path or folder doesn't exist")
    
    with col2:
        # Toggle for advanced processing
        process_option = st.radio(
            "Processing Option",
            options=["Standard Indexing", "Advanced Processing"],
            index=1 if use_advanced_processing else 0,
            help="Advanced processing includes document summarization and keyword extraction"
        )
        
        use_adv_process = process_option == "Advanced Processing"
        
        if st.button("Index Folder", key="index_folder") and folder_path:
            path = Path(folder_path)
            if path.exists() and path.is_dir():
                with st.status("Indexing folder..."):
                    create_index(folder_path, logger, use_advanced_processing=use_adv_process)
                st.success(f"Folder indexed successfully!")
            else:
                st.error("Invalid folder path or folder doesn't exist")

# Tab 3: Index Status
with tab3:
    st.header("Index Status")
    
    if st.button("Refresh Index Status", key="refresh_status"):
        if load_index():
            stats = get_index_stats()
            if stats:
                st.success("Index is loaded and ready to use.")
                
                # Display basic stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Documents", stats["document_count"])
                with col2:
                    st.metric("Total Files", stats["file_count"])
                with col3:
                    st.metric("Average Chunk Size", f"{stats['avg_chunk_size']:.0f} chars")
                with col4:
                    st.metric("Enhanced Documents", 
                             f"{stats.get('summary_count', 0)} of {stats['file_count']}")
                
                # Display advanced processing stats if available
                if stats.get("has_summaries") or stats.get("has_keywords"):
                    st.subheader("Enhanced Processing")
                    adv_col1, adv_col2 = st.columns(2)
                    
                    with adv_col1:
                        st.metric("Documents with Summaries", stats.get("summary_count", 0))
                        if stats.get("has_summaries"):
                            st.success("Document summaries are available")
                        else:
                            st.info("No document summaries available")
                    
                    with adv_col2:
                        st.metric("Documents with Keywords", stats.get("keyword_count", 0))
                        if stats.get("has_keywords"):
                            st.success("Document keywords are available")
                        else:
                            st.info("No document keywords available")
                
                # Display indexed files
                with st.expander("Indexed Files"):
                    for file_path in stats["files"]:
                        st.text(file_path)
                
                # Display summary
                st.subheader("Index Summary")
                
                # Try to load the index summary
                if os.path.exists("index_summary.json"):
                    try:
                        with open("index_summary.json", "r") as f:
                            summary = json.load(f)
                        st.json(summary)
                    except:
                        st.warning("Could not load detailed index summary.")
            else:
                st.warning("Index is loaded but no statistics are available.")
        else:
            st.error("No index found. Please index documents first.")

# Tab 4: Document Preview
with tab4:
    st.header("Document Preview")
    st.markdown("Preview and analyze individual documents")
    
    if load_index():
        stats = get_index_stats()
        if stats and stats["files"]:
            # Create a select box with available files
            selected_file = st.selectbox("Select a document to preview", stats["files"])
            
            if selected_file:
                # Process the selected document to get preview
                client = get_mistral_client()
                
                with st.status("Analyzing document..."):
                    doc_info = process_document(selected_file, client)
                
                if doc_info and doc_info["processed"]:
                    # Display document information
                    st.subheader(f"Document: {doc_info['filename']}")
                    
                    # Display metadata
                    meta_col1, meta_col2, meta_col3 = st.columns(3)
                    with meta_col1:
                        st.metric("File Size", f"{doc_info['size'] / 1024:.1f} KB")
                    with meta_col2:
                        st.metric("Text Length", len(doc_info.get("text", "")))
                    with meta_col3:
                        st.metric("Chunks", len(doc_info.get("chunks", [])))
                    
                    # Display summary if available
                    if doc_info.get("summary"):
                        st.subheader("Document Summary")
                        st.info(doc_info["summary"])
                    
                    # Display keywords if available
                    if doc_info.get("keywords"):
                        st.subheader("Keywords")
                        st.write(", ".join(doc_info["keywords"]))
                    
                    # Display document content preview
                    with st.expander("Document Content Preview"):
                        text_preview = doc_info.get("text", "")[:1000]
                        st.text_area("Content Preview (first 1000 characters)", 
                                     text_preview, 
                                     height=300)
                    
                    # Display chunks if available
                    if doc_info.get("chunks"):
                        st.subheader("Document Chunks")
                        
                        # Group chunks by level
                        level_0_chunks = [c for c in doc_info["chunks"] if c["level"] == 0]
                        
                        for i, chunk in enumerate(level_0_chunks):
                            with st.expander(f"Chunk {i+1} (Level 0)"):
                                st.text_area(f"Chunk {i+1} Content", 
                                            chunk["text"][:500] + "...", 
                                            height=150)
                                
                                # Find child chunks if any
                                child_chunks = [c for c in doc_info["chunks"] 
                                              if c["level"] == 1 and c.get("parent_index") == i]
                                
                                if child_chunks:
                                    st.write(f"This chunk has {len(child_chunks)} sub-chunks")
                else:
                    st.error("Error processing document for preview")
        else:
            st.warning("No documents found in the index")
    else:
        st.error("No index found. Please index documents first.")

# Tab 5: Manage Index
with tab5:
    st.header("Manage Index")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Reset Index", key="reset_index"):
            # Ask for confirmation
            if st.checkbox("Confirm reset - this will delete your entire document index"):
                # Delete index files
                index_files = ["index.pkl", "index_summary.json"]
                deleted = False
                
                for file in index_files:
                    if os.path.exists(file):
                        os.remove(file)
                        deleted = True
                
                if deleted:
                    st.success("Index has been reset successfully.")
                else:
                    st.info("No index files found to delete.")
    
    with col2:
        if st.button("Export Index Summary", key="export_summary"):
            if os.path.exists("index_summary.json"):
                try:
                    with open("index_summary.json", "r") as f:
                        summary = json.load(f)
                    
                    # Convert to string for download
                    import json
                    json_str = json.dumps(summary, indent=2)
                    
                    # Create download button
                    st.download_button(
                        label="Download Index Summary",
                        data=json_str,
                        file_name="index_summary.json",
                        mime="application/json"
                    )
                except:
                    st.warning("Could not load index summary for export.")
            else:
                st.error("No index summary file found. Please index documents first.")
    
    # Advanced index management options
    st.subheader("Advanced Options")
    
    # Re-process index with advanced processing
    if st.button("Re-process Index with Advanced Processing"):
        if load_index():
            stats = get_index_stats()
            if stats and not stats.get("has_summaries") and not stats.get("has_keywords"):
                with st.status("Re-processing index with advanced processing..."):
                    # This would need to be implemented in index_functions.py
                    st.info("This feature requires additional implementation")
                    # Placeholder for future implementation
            else:
                st.info("Index already has advanced processing features")
        else:
            st.error("No index found. Please index documents first.")
    
    # Create backup of index
    if st.button("Create Index Backup"):
        if os.path.exists("index.pkl"):
            try:
                import shutil
                import datetime
                
                # Create backup timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"index_backup_{timestamp}.pkl"
                
                # Copy index file
                shutil.copy2("index.pkl", backup_file)
                
                st.success(f"Index backup created: {backup_file}")
            except Exception as e:
                st.error(f"Error creating backup: {str(e)}")
        else:
            st.error("No index file found to backup")

# Add helpful information
st.markdown("---")
with st.expander("About Document Indexing and Processing"):
    st.markdown("""
    ### How Document Processing Works

    #### Standard Processing
    1. **Text Extraction**: The system extracts text from your uploaded documents.
    2. **Chunking**: Long documents are split into fixed-size, overlapping chunks.
    3. **Embedding Generation**: Each chunk is converted into a vector representation.
    4. **Storage**: These embeddings are stored for quick retrieval.

    #### Advanced Processing (Enhanced)
    1. **All standard processing steps**
    2. **Document Summarization**: AI generates a concise summary of each document.
    3. **Keyword Extraction**: Important keywords are identified from each document.
    4. **Hierarchical Chunking**: Documents are split into a two-level hierarchy of chunks.
    5. **Metadata Enrichment**: Chunks are tagged with position and relationship information.

    ### Benefits of Advanced Processing

    - **Improved Context**: Summaries provide a quick overview without reading the entire document.
    - **Better Search**: Keywords help identify the most relevant documents.
    - **More Natural Chunking**: Hierarchical chunks better preserve the document's structure.
    - **Enhanced Responses**: The AI can draw on summaries and keywords for more informed answers.

    ### Supported File Types

    - Text files (.txt)
    - Markdown files (.md)
    - CSV files (.csv)
    - JSON files (.json)
    - Python files (.py)
    - JavaScript files (.js)
    - HTML files (.html)
    - CSS files (.css)
    - PDF files (.pdf) - requires pypdf
    """)