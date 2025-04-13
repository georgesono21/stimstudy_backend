import requests
import json
import time

# Base URL for the API
BASE_URL = "http://localhost:4000"

def interactive_chat():
    """
    Interactive chat session that:
    1. Starts a new chat session with a sample study plan
    2. Allows the user to send messages from the terminal
    3. Displays the responses from Gemini
    4. Continues until the user types 'exit' or 'quit'
    """
    # Sample study plan for testing
    sample_study_plan = {
        "topic": "Machine Learning Fundamentals",
        "sections": [
            {
                "title": "Introduction to ML",
                "content": "Basic concepts and terminology"
            },
            {
                "title": "Supervised Learning",
                "content": "Classification and regression techniques"
            },
            {
                "title": "Unsupervised Learning",
                "content": "Clustering and dimensionality reduction"
            }
        ]
    }
    
    # Step 1: Start a new chat session
    print("Starting a new chat session...")
    start_response = requests.post(
        f"{BASE_URL}/chat/start",
        json={"studyPlan": sample_study_plan}
    )
    
    if start_response.status_code != 200:
        print(f"Error starting chat: {start_response.text}")
        return
    
    start_data = start_response.json()
    session_id = start_data.get("session_id")
    print(f"Chat session started with ID: {session_id}")
    print(f"Response: {start_data.get('message')}")
    print("=" * 50)
    print("You are now chatting with Gemini about your study plan.")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("=" * 50)
    
    # Step 2: Interactive message loop
    while True:
        # Get user input
        user_message = input("\nYou: ")
        
        # Check if user wants to exit
        if user_message.lower() in ['exit', 'quit']:
            print("Ending chat session. Goodbye!")
            break
        
        # Send message to the API
        message_response = requests.post(
            f"{BASE_URL}/chat/message",
            json={
                "session_id": session_id,
                "message": user_message
            }
        )
        
        if message_response.status_code != 200:
            print(f"Error: {message_response.text}")
            continue
        
        # Display the response
        response_data = message_response.json()
        print(f"\nGemini: {response_data.get('response')}")

if __name__ == "__main__":
    interactive_chat() 