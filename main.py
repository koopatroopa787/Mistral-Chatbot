import os
import sys
from mistralai import Mistral
from helper_functions import setup_logging, load_config, handle_user_input
from index_functions import create_index, search_index

def main():
    # Set up logging
    logger = setup_logging()
    logger.info("Starting chatbot application")
    
    # Load configuration
    config = load_config()
    
    # Initialize Mistral client
    try:
        api_key = os.environ.get("MISTRAL_API_KEY", "RzVjPRq5NWai8PDEBPWT2o1B1fMjmIE2")
        client = Mistral(api_key=api_key)
        logger.info("Mistral client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Mistral client: {e}")
        sys.exit(1)
    
    # Create chat history
    chat_history = []
    
    # Main chat loop
    print("Welcome to Mistral Chatbot! Type 'exit' to quit.")
    print("You can also use 'index [path]' to create an index of documents for reference.")
    
    while True:
        # Get user input
        user_input = handle_user_input()
        
        # Check for exit command
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        # Check for index command
        if user_input.lower().startswith('index '):
            path = user_input[6:].strip()
            create_index(path, logger)
            continue
        
        # Check for search command
        if user_input.lower().startswith('search '):
            query = user_input[7:].strip()
            context = search_index(query, logger)
            if context:
                # Add retrieved context to the user message
                user_input = f"Using this context: {context}\n\nUser question: {query}"
        
        # Add user message to chat history
        chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        try:
            # Get response from Mistral using the new client format
            chat_response = client.chat.complete(
                model=config["model"],
                messages=chat_history,
                temperature=config["temperature"],
                max_tokens=config["max_tokens"]
            )
            
            # Extract assistant message
            assistant_message = {
                "role": "assistant",
                "content": chat_response.choices[0].message.content
            }
            
            # Print response
            print(f"Assistant: {assistant_message['content']}")
            
            # Add assistant message to chat history
            chat_history.append(assistant_message)
            
            # Trim history if it gets too long
            if len(chat_history) > config["max_history_length"]:
                # Keep first message (system prompt) and recent messages
                if chat_history[0]["role"] == "system":
                    chat_history = [chat_history[0]] + chat_history[-config["max_history_length"]+1:]
                else:
                    chat_history = chat_history[-config["max_history_length"]:]
                    
        except Exception as e:
            logger.error(f"Error getting response from Mistral: {e}")
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()