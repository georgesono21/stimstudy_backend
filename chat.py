import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the Google Generative AI API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Create a chat model
model = genai.GenerativeModel(model_name="gemini-2.0-flash")

# Initialize chat sessions dictionary to store conversation history
chat_sessions = {}

def start_new_chat(study_plan=None):
    """
    Start a new chat session
    
    Args:
        study_plan (dict, optional): The study plan to contextualize the chat
        
    Returns:
        tuple: (session_id, chat_instance)
    """
    session_id = str(len(chat_sessions) + 1)  # Simple ID generation
    chat = model.start_chat(history=[])
    
    # If a study plan is provided, send an initial system message
    if study_plan:
        # Create a system message that provides context about the study plan
        context_message = f"The user is currently studying the following study plan: {study_plan} When responding be very concise and to the point, 2 sentences max."
        chat.send_message(context_message)
    
    # Store the chat session
    chat_sessions[session_id] = chat
    
    return session_id

def send_chat_message(session_id, message):
    """
    Send a message to an existing chat session
    
    Args:
        session_id (str): The ID of the chat session
        message (str): The message to send
        
    Returns:
        str: The response from the model
        
    Raises:
        ValueError: If the session_id is invalid
    """
    if session_id not in chat_sessions:
        raise ValueError(f"Invalid session ID: {session_id}")
    
    # Get the chat session
    chat = chat_sessions[session_id]
    
    # Send the message to the model
    response = chat.send_message(message)
    
    return response.text

def get_chat_session(session_id):
    """
    Get a chat session by ID
    
    Args:
        session_id (str): The ID of the chat session
        
    Returns:
        object: The chat session object
        
    Raises:
        ValueError: If the session_id is invalid
    """
    if session_id not in chat_sessions:
        raise ValueError(f"Invalid session ID: {session_id}")
    
    return chat_sessions[session_id]
