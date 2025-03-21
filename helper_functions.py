import os
import logging
import json
from pathlib import Path
import streamlit as st
import io

def setup_logging():
    """Set up logging configuration for the chatbot"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "chatbot.log"),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("chatbot")

def load_config():
    """Load configuration from config.json or return default config"""
    config_path = Path("config.json")
    
    default_config = {
        "model": "mistral-large-latest",
        "temperature": 0.7,
        "max_tokens": 1024,
        "max_history_length": 10,
        "index_type": "simple",
        "embedding_model": "mistral-embed",
        "system_prompt": "You are a helpful assistant that provides accurate and concise information."
    }
    
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                # Merge with default config to ensure all required fields exist
                return {**default_config, **config}
        except Exception as e:
            logging.error(f"Error loading config: {e}. Using default configuration.")
            return default_config
    else:
        # Create default config file
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        
        return default_config

def handle_user_input():
    """Get and process user input"""
    user_input = input("\nYou: ")
    return user_input

def extract_text_from_file(file_path):
    """Extract text content from various file types"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        logging.warning(f"File not found: {file_path}")
        return None
    
    # Text files
    if file_path.suffix.lower() in ['.txt', '.md', '.csv', '.json', '.py', '.js', '.html', '.css']:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
            return None
            
    # PDF files
    elif file_path.suffix.lower() == '.pdf':
        try:
            # Import only if needed
            import pypdf
            
            with open(file_path, 'rb') as f:
                pdf = pypdf.PdfReader(f)
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            logging.error("pypdf not installed. Install with: pip install pypdf")
            return None
        except Exception as e:
            logging.error(f"Error reading PDF {file_path}: {e}")
            return None
    
    # For other file types, you might want to add more specialized extractors
    
    logging.warning(f"Unsupported file type: {file_path.suffix}")
    return None

def extract_text_from_uploaded_file(uploaded_file):
    """Extract text from a Streamlit uploaded file"""
    # Get the file name and extension
    file_name = uploaded_file.name
    file_extension = Path(file_name).suffix.lower()
    
    # Text files
    if file_extension in ['.txt', '.md', '.csv', '.json', '.py', '.js', '.html', '.css']:
        try:
            # Decode the content as text
            text_content = uploaded_file.getvalue().decode('utf-8')
            return text_content
        except Exception as e:
            logging.error(f"Error reading {file_name}: {e}")
            return None
            
    # PDF files
    elif file_extension == '.pdf':
        try:
            # Import only if needed
            import pypdf
            
            # Create a file-like object from the uploaded file's bytes
            pdf_file = io.BytesIO(uploaded_file.getvalue())
            pdf = pypdf.PdfReader(pdf_file)
            
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            logging.error("pypdf not installed. Install with: pip install pypdf")
            return None
        except Exception as e:
            logging.error(f"Error reading PDF {file_name}: {e}")
            return None
    
    # For other file types, you might want to add more specialized extractors
    
    logging.warning(f"Unsupported file type: {file_extension}")
    return None

def save_chat_history(chat_history, filename="chat_history.json"):
    """Save chat history to a file"""
    with open(filename, "w") as f:
        # Ensure chat history is in serializable format
        serializable_history = [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in chat_history
        ]
        json.dump(serializable_history, f, indent=4)

def load_chat_history(filename="chat_history.json"):
    """Load chat history from a file"""
    if not os.path.exists(filename):
        return []
    
    with open(filename, "r") as f:
        serialized_history = json.load(f)
        
    # Return as dictionaries with role and content
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in serialized_history
    ]