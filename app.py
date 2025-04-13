import json
import os
import time
from StimStudy.master import generate_videos
import chat
from flask import Flask, jsonify
from google import genai
from dotenv import load_dotenv
import prompts
from flask import request
from flask_cors import CORS

from video import generate_and_combine_videos

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

CORS(
    app,
    resources={
        r"/createStudyPlan": {
            "origins": "http://localhost:8080",
            "methods": ["POST"],
            "allow_headers": ["Content-Type"],
        },
        r"/refineStudyPlan": {
            "origins": "http://localhost:8080",
            "methods": ["POST"],
            "allow_headers": ["Content-Type"],
        },
        r"/generateStudyPlanVideos": {
            "origins": "http://localhost:8080",
            "methods": ["POST"],
            "allow_headers": ["Content-Type"],
        },
        r"/chat/message": {
            "origins": "http://localhost:8080",
            "methods": ["POST"],
            "allow_headers": ["Content-Type"],
        },
        r"/chat/start": {
            "origins": "http://localhost:8080",
            "methods": ["POST"],
            "allow_headers": ["Content-Type"],
        },
    },
)

@app.route('/')
def hello_world():
    return 'Hello, World! This is a Flask application running in a Docker container.'


@app.route("/createStudyPlan", methods=["POST"])
def createStudyPlan():

    data = request.get_json()
    userPrompt = data.get("prompt", "")

    prompt = prompts.createStudyPlanPrompt(userPrompt)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    return response.text


@app.route("/refineStudyPlan", methods=["POST"])
def refineStudyPlan():
    data = request.get_json()
    studyPlan = data.get("studyPlan", "")
    refinement = data.get("refinement", "")

    print(json.dumps(studyPlan))
    prompt = prompts.refineStudyPlanPrompt(studyPlan, refinement)
    print(prompt)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text


@app.route("/chat/message", methods=["POST"])
def send_message():
    """Send a message to an existing chat session"""
    data = request.get_json()
    session_id = data.get("session_id")
    message = data.get("message")

    if not session_id or not message:
        return jsonify({"error": "Missing session_id or message"}), 400

    try:
        response_text = chat.send_chat_message(session_id, message)
        return jsonify({"response": response_text})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat/start", methods=["POST"])
def start_chat():
    """Start a new chat session with optional study plan context"""
    data = request.get_json()
    study_plan = data.get("studyPlan", None)

    try:
        session_id = chat.start_new_chat(study_plan)
        return jsonify(
            {"session_id": session_id, "message": "Chat session started successfully"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/generateStudyPlanVideos", methods=["POST"])
def generateStudyPlanVideos():
    # Send request with function declarations
    data = request.get_json()
    studyPlan = data.get("studyPlan", "")
    voiceActor = data.get("voiceActor", "")
    background = data.get("background", "")
    
    return "cool!"

    voiceActorToId = {
        "peter": "a84d19016bc34098b3c89d78f9299e33",
        "spongebob": "54e3a85ac9594ffa83264b8a494b901b",
        "biden": "9b42223616644104a4534968cd612053",
    }

    voiceActorId = voiceActorToId.get(voiceActor, "")

    if not studyPlan:
        return "Invalid study plan provided."

    if not voiceActorId:
        return "Invalid voice actor selected."

    for i in range(len(studyPlan)):
        studyPlan[i] = json.dumps(studyPlan[i])

    results = generate_videos(
        studyPlan,
        voiceActorId,
        max_workers=4,
        max_concurrent_topics=4
    )

    audio_folder = "ASSETS/test/audio_clips"
    sprite_dir = "sprites"
    background_folder = "backgroundVideos"
    output_folder = "output"
    slide_folder = "ASSETS/test/videos"
    final_output_path = "videos"
    index = 0
    selected_character = voiceActor
    selected_background = background
    generate_and_combine_videos(audio_folder=audio_folder,
                                selected_character=selected_character,
                                sprite_dir=sprite_dir,
                                selected_background=selected_background,
                                background_folder=background_folder,
                                output_folder=output_folder,
                                slide_folder=slide_folder,
                                final_output_path=final_output_path,
                                index=index)
    

    return "Videos generated successfully."

if __name__ == "__main__":
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents="Explain how AI works in a few words"
    )
    app.run(host="localhost", port=4000, debug=True)
