import os
import streamlit as st
from mistralai import Mistral
from pathlib import Path
import logging
import json
import re
from helper_functions import load_config

# Initialize logger
logger = logging.getLogger("chatbot.document_processor")

def get_mistral_client():
    """Get Mistral client instance"""
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        logger.error("Missing API key")
        return None
    return Mistral(api_key=api_key)

def summarize_text(text, client=None, min_length=500):
    """Summarize text if it exceeds minimum length"""
    if not text or len(text) < min_length:
        return None
    
    if client is None:
        client = get_mistral_client()
        if not client:
            return None
    
    config = load_config()
    
    try:
        # Create a prompt for summarization
        prompt = f"""
        Please create a concise summary of the following text. 
        Focus on the key points, main ideas, and essential information.
        The summary should capture the core meaning while being much shorter than the original.
        
        Text to summarize:
        {text[:6000]}  # Limit to prevent token overflow
        """
        
        # Get response from Mistral
        response = client.chat.complete(
            model=config.get("model", "mistral-small-latest"),  # Use smaller model for efficiency
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for more deterministic output
            max_tokens=500  # Limit summary length
        )
        
        summary = response.choices[0].message.content
        logger.info(f"Successfully summarized text of length {len(text)} to summary of length {len(summary)}")
        return summary
    
    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}")
        return None

def extract_keywords(text, client=None, min_length=200):
    """Extract keywords from text if it exceeds minimum length"""
    if not text or len(text) < min_length:
        return []
    
    if client is None:
        client = get_mistral_client()
        if not client:
            return []
    
    config = load_config()
    
    try:
        # Create a prompt for keyword extraction
        prompt = f"""
        Extract 5-10 important keywords or key phrases from the following text.
        Focus on subject-specific terminology, important concepts, and significant entities.
        Return ONLY the keywords, separated by commas, with no additional text or explanation.
        
        Text for keyword extraction:
        {text[:4000]}  # Limit to prevent token overflow
        """
        
        # Get response from Mistral
        response = client.chat.complete(
            model=config.get("model", "mistral-small-latest"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        
        keyword_text = response.choices[0].message.content
        
        # Clean the keyword text and split it
        keyword_text = keyword_text.strip()
        if keyword_text.startswith("Keywords:"):
            keyword_text = keyword_text[len("Keywords:"):].strip()
        
        # Split by commas and clean up
        keywords = [k.strip() for k in keyword_text.split(",") if k.strip()]
        
        logger.info(f"Extracted {len(keywords)} keywords from text of length {len(text)}")
        return keywords
    
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        return []

def hierarchical_chunking(text, chunk_sizes=(1000, 500), overlaps=(100, 50)):
    """
    Split text into hierarchical chunks of different sizes.
    Returns a list of dictionaries with the chunks and their level.
    Level 0 is the largest chunk size, level 1 is the smaller chunk size.
    """
    if not text:
        return []
    
    chunks = []
    
    # First level - larger chunks
    level_0_chunks = []
    for i in range(0, len(text), chunk_sizes[0] - overlaps[0]):
        chunk = text[i:i + chunk_sizes[0]]
        if len(chunk) < chunk_sizes[0] // 4:  # Skip very small chunks
            continue
        level_0_chunks.append(chunk)
    
    # Process each large chunk into smaller chunks
    for i, large_chunk in enumerate(level_0_chunks):
        # Add the large chunk
        chunks.append({
            "text": large_chunk,
            "level": 0,
            "index": i
        })
        
        # Add smaller chunks from within the large chunk
        for j in range(0, len(large_chunk), chunk_sizes[1] - overlaps[1]):
            small_chunk = large_chunk[j:j + chunk_sizes[1]]
            if len(small_chunk) < chunk_sizes[1] // 4:  # Skip very small chunks
                continue
            chunks.append({
                "text": small_chunk,
                "level": 1,
                "parent_index": i,
                "index": j
            })
    
    return chunks

def process_document(file_path, client=None):
    """
    Process a document file: extract text, generate summary, extract keywords,
    and create hierarchical chunks.
    
    Returns a dictionary with the processed document information.
    """
    from helper_functions import extract_text_from_file
    
    file_path = Path(file_path)
    
    # Initialize document info
    doc_info = {
        "path": str(file_path),
        "filename": file_path.name,
        "extension": file_path.suffix.lower(),
        "size": file_path.stat().st_size if file_path.exists() else 0,
        "text": "",
        "summary": "",
        "keywords": [],
        "chunks": [],
        "processed": False
    }
    
    try:
        # Extract text from the file
        text = extract_text_from_file(file_path)
        if not text:
            logger.warning(f"No text extracted from {file_path}")
            return doc_info
        
        doc_info["text"] = text
        
        # Get Mistral client if not provided
        if client is None:
            client = get_mistral_client()
            if not client:
                logger.error("Could not initialize Mistral client")
                return doc_info
        
        # Generate summary
        summary = summarize_text(text, client)
        if summary:
            doc_info["summary"] = summary
        
        # Extract keywords
        keywords = extract_keywords(text, client)
        if keywords:
            doc_info["keywords"] = keywords
        
        # Create hierarchical chunks
        chunks = hierarchical_chunking(text)
        doc_info["chunks"] = chunks
        
        doc_info["processed"] = True
        logger.info(f"Successfully processed document: {file_path}")
        
        return doc_info
    
    except Exception as e:
        logger.error(f"Error processing document {file_path}: {str(e)}")
        return doc_info

def process_documents_batch(file_paths, display_progress=False):
    """
    Process a batch of documents with progress tracking.
    
    If display_progress is True, assumes this is running in a Streamlit app
    and will display a progress bar.
    """
    if not file_paths:
        return []
    
    # Get client once to reuse
    client = get_mistral_client()
    if not client:
        logger.error("Could not initialize Mistral client")
        return []
    
    processed_docs = []
    
    # Setup progress tracking
    if display_progress:
        progress_text = st.empty()
        progress_bar = st.progress(0)
    
    for i, file_path in enumerate(file_paths):
        if display_progress:
            progress_text.text(f"Processing document {i+1}/{len(file_paths)}: {Path(file_path).name}")
            progress_bar.progress((i) / len(file_paths))
        
        doc_info = process_document(file_path, client)
        if doc_info["processed"]:
            processed_docs.append(doc_info)
        
        if display_progress:
            progress_bar.progress((i + 1) / len(file_paths))
    
    if display_progress:
        progress_text.empty()
        progress_bar.empty()
    
    return processed_docs

def save_processed_documents(processed_docs, output_dir="processed_documents"):
    """Save processed document information to JSON files."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    saved_files = []
    
    for doc in processed_docs:
        try:
            filename = Path(doc["path"]).stem
            output_file = output_path / f"{filename}_processed.json"
            
            # Save to JSON file
            with open(output_file, "w") as f:
                # Create a copy of the doc info without the full text to save space
                save_doc = doc.copy()
                # Keep only the first 100 chars of text as a preview
                if len(save_doc.get("text", "")) > 100:
                    save_doc["text_preview"] = save_doc["text"][:100] + "..."
                    del save_doc["text"]
                
                json.dump(save_doc, f, indent=2)
            
            saved_files.append(str(output_file))
            
        except Exception as e:
            logger.error(f"Error saving processed document {doc.get('path')}: {str(e)}")
    
    return saved_files

def load_processed_document(file_path):
    """Load processed document information from a JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading processed document {file_path}: {str(e)}")
        return None