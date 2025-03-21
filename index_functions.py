import os
import json
import pickle
from pathlib import Path
import numpy as np
from collections import defaultdict
import streamlit as st
from helper_functions import extract_text_from_file, load_config
from mistralai import Mistral
from document_processor import process_document, process_documents_batch, hierarchical_chunking

# Simple in-memory index for demonstration purposes
index = {
    "documents": [],
    "embeddings": None,
    "id_to_path": {},
    "id_to_metadata": {},  # New field for storing document metadata
    "summaries": {},       # New field for storing document summaries
    "keywords": {},        # New field for storing document keywords
    "initialized": False
}

def create_index(directory_path, logger, use_advanced_processing=True):
    """Create an index of documents in the specified directory with advanced processing"""
    directory = Path(directory_path)
    
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Directory not found: {directory_path}")
        st.error(f"Error: Directory not found: {directory_path}")
        return
    
    logger.info(f"Creating index for directory: {directory_path}")
    
    # Progress tracking
    progress_text = st.empty()
    progress_bar = st.empty()
    
    # Get all files recursively
    files = list(directory.glob("**/*"))
    files = [f for f in files if f.is_file()]
    
    if not files:
        logger.warning(f"No files found in directory: {directory_path}")
        st.warning("No files found in the specified directory.")
        return
    
    # Process documents with advanced processing if enabled
    if use_advanced_processing:
        progress_text.text("Processing documents with tokenizing and summarization...")
        processed_docs = process_documents_batch(files, display_progress=True)
        
        # Extract documents and metadata from processed docs
        documents = []
        file_paths = []
        metadata = {}
        summaries = {}
        all_keywords = {}
        
        for doc in processed_docs:
            if "chunks" in doc and doc["chunks"]:
                # Use hierarchical chunks with their metadata
                for i, chunk in enumerate(doc["chunks"]):
                    chunk_id = f"{doc['path']}:{i}"
                    documents.append(chunk["text"])
                    file_paths.append(chunk_id)
                    
                    # Store metadata for this chunk
                    metadata[chunk_id] = {
                        "path": doc["path"],
                        "filename": doc["filename"],
                        "chunk_level": chunk["level"],
                        "chunk_index": chunk.get("index", i),
                        "parent_index": chunk.get("parent_index", None)
                    }
            else:
                # Fallback to simple text if no chunks
                documents.append(doc.get("text", ""))
                file_paths.append(doc["path"])
                metadata[doc["path"]] = {
                    "path": doc["path"],
                    "filename": doc["filename"]
                }
            
            # Store summary and keywords
            if doc.get("summary"):
                summaries[doc["path"]] = doc["summary"]
            
            if doc.get("keywords"):
                all_keywords[doc["path"]] = doc["keywords"]
    else:
        # Use traditional method without advanced processing
        documents = []
        file_paths = []
        metadata = {}
        
        progress_text.text("Extracting text from files...")
        progress_bar.progress(0)
        
        for i, file_path in enumerate(files):
            try:
                text = extract_text_from_file(file_path)
                if text:
                    # Simple chunking strategy
                    chunks = chunk_text(text, chunk_size=500, overlap=100)
                    for j, chunk in enumerate(chunks):
                        chunk_id = f"{file_path}:{j}"
                        documents.append(chunk)
                        file_paths.append(chunk_id)
                        metadata[chunk_id] = {
                            "path": str(file_path),
                            "filename": file_path.name,
                            "chunk_index": j
                        }
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
            
            # Update progress
            progress_bar.progress((i + 1) / len(files))
    
    if not documents:
        logger.warning("No content extracted from files.")
        st.warning("No content could be extracted from the files.")
        progress_text.empty()
        progress_bar.empty()
        return
    
    # Generate embeddings for documents
    try:
        config = load_config()
        api_key = os.environ.get("MISTRAL_API_KEY", "")
        client = Mistral(api_key=api_key)
        
        # Process documents in batches to avoid API limits
        batch_size = 10
        all_embeddings = []
        
        progress_text.text("Generating embeddings...")
        progress_bar.progress(0)
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            logger.info(f"Generating embeddings for batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            # Use the client format for embeddings
            response = client.embeddings.create(
                model=config.get("embedding_model", "mistral-embed"),
                inputs=batch
            )
            
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            
            # Update progress
            progress_bar.progress(min(1.0, (i + batch_size) / len(documents)))
        
        # Update index
        index["documents"] = documents
        index["embeddings"] = np.array(all_embeddings)
        index["id_to_path"] = {i: path for i, path in enumerate(file_paths)}
        index["id_to_metadata"] = {i: metadata.get(path, {}) for i, path in enumerate(file_paths)}
        
        # Add summaries and keywords if available
        if use_advanced_processing:
            index["summaries"] = summaries
            index["keywords"] = all_keywords
        
        index["initialized"] = True
        
        # Save index to disk for persistence
        save_index(index)
        
        logger.info(f"Index created successfully with {len(documents)} chunks from {len(set([metadata[p].get('path') for p in file_paths]))} files")
        progress_text.text(f"Index created successfully with {len(documents)} chunks from {len(set([metadata[p].get('path') for p in file_paths]))} files")
        progress_bar.progress(1.0)
        
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        st.error(f"Error creating index: {e}")
        progress_text.empty()
        progress_bar.empty()

def search_index(query, logger, top_k=3, include_metadata=True):
    """Search the index for documents relevant to the query"""
    if not index["initialized"]:
        # Try to load index from disk
        if not load_index():
            logger.warning("Index not initialized. Please create an index first.")
            return None
    
    try:
        # Generate embedding for query
        config = load_config()
        api_key = os.environ.get("MISTRAL_API_KEY", "")
        client = Mistral(api_key=api_key)
        
        # Use the client format for embeddings
        response = client.embeddings.create(
            model=config.get("embedding_model", "mistral-embed"),
            inputs=[query]
        )
        
        query_embedding = np.array(response.data[0].embedding)
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, index["embeddings"])
        
        # Get top k results
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Create context from top results
        context = []
        seen_paths = set()
        
        for idx in top_indices:
            doc = index["documents"][idx]
            path_id = index["id_to_path"][idx]
            
            # Extract base path from chunk ID (format may be "path:chunk_index")
            if ":" in path_id:
                base_path = path_id.split(":")[0]
            else:
                base_path = path_id
            
            # Get metadata if available
            metadata = {}
            if include_metadata and idx in index["id_to_metadata"]:
                metadata = index["id_to_metadata"][idx]
            
            # Check if we have a summary for this document
            summary = ""
            if base_path in index.get("summaries", {}):
                summary = index["summaries"][base_path]
            
            # Check if we have keywords for this document
            keywords = []
            if base_path in index.get("keywords", {}):
                keywords = index["keywords"][base_path]
            
            # Add document path if not seen before
            if base_path not in seen_paths:
                seen_paths.add(base_path)
            
            # Add more context with metadata and summary if available
            context_entry = f"From {Path(base_path).name}"
            
            if metadata:
                # Add relevant metadata if available
                if "chunk_level" in metadata:
                    context_entry += f" (Section {metadata.get('chunk_index', 'unknown')})"
            
            context_entry += ":\n"
            
            # Add summary if available
            if summary:
                context_entry += f"\nSUMMARY: {summary}\n"
            
            # Add keywords if available
            if keywords:
                context_entry += f"\nKEYWORDS: {', '.join(keywords)}\n"
            
            # Add the document text
            context_entry += f"\nCONTENT: {doc}\n"
            
            context.append(context_entry)
        
        return "\n".join(context)
        
    except Exception as e:
        logger.error(f"Error searching index: {e}")
        return None

def cosine_similarity(query_embedding, document_embeddings):
    """Calculate cosine similarity between query and documents"""
    # Normalize the embeddings
    query_norm = np.linalg.norm(query_embedding)
    query_normalized = query_embedding / query_norm
    
    # Calculate dot product
    dot_products = np.dot(document_embeddings, query_normalized)
    
    # Normalize document embeddings
    doc_norms = np.linalg.norm(document_embeddings, axis=1)
    similarities = dot_products / doc_norms
    
    return similarities

def chunk_text(text, chunk_size=500, overlap=100):
    """Split text into overlapping chunks"""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if len(chunk) < 50:  # Skip very small chunks
            continue
        chunks.append(chunk)
    return chunks

def save_index(index_data, filename="index.pkl"):
    """Save index to disk"""
    try:
        with open(filename, "wb") as f:
            pickle.dump(index_data, f)
        
        # Also save a human-readable summary
        summary = {
            "document_count": len(index_data["documents"]),
            "file_count": len(set([
                index_data["id_to_metadata"].get(i, {}).get("path", path) 
                for i, path in index_data["id_to_path"].items()
            ])),
            "has_summaries": len(index_data.get("summaries", {})) > 0,
            "has_keywords": len(index_data.get("keywords", {})) > 0,
            "files": list(set([
                index_data["id_to_metadata"].get(i, {}).get("path", path) 
                for i, path in index_data["id_to_path"].items()
            ]))
        }
        
        with open("index_summary.json", "w") as f:
            json.dump(summary, f, indent=4)
            
        return True
    except Exception as e:
        st.error(f"Error saving index: {e}")
        return False

def load_index(filename="index.pkl"):
    """Load index from disk"""
    global index
    try:
        if not os.path.exists(filename):
            return False
            
        with open(filename, "rb") as f:
            loaded_index = pickle.load(f)
            
        index.update(loaded_index)
        return True
    except Exception as e:
        st.error(f"Error loading index: {e}")
        return False

def get_index_stats():
    """Get statistics about the current index"""
    if not index["initialized"]:
        if not load_index():
            return None
    
    # Count unique base paths
    unique_paths = set()
    for path_id in index["id_to_path"].values():
        if ":" in path_id:
            base_path = path_id.split(":")[0]
        else:
            base_path = path_id
        unique_paths.add(base_path)
    
    stats = {
        "document_count": len(index["documents"]),
        "file_count": len(unique_paths),
        "files": list(unique_paths),
        "avg_chunk_size": sum(len(doc) for doc in index["documents"]) / max(1, len(index["documents"])),
        "has_summaries": len(index.get("summaries", {})) > 0,
        "has_keywords": len(index.get("keywords", {})) > 0,
        "summary_count": len(index.get("summaries", {})),
        "keyword_count": len(index.get("keywords", {}))
    }
    
    return stats