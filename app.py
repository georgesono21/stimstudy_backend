import json
import os
import time
from flask import Flask, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import prompts
from flask import request
# import video
from flask_cors import CORS
import chat

load_dotenv()

app = Flask(__name__)
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

CORS(
    app,
    resources={
        r"/createStudyPlan": {
            "origins": "http://localhost:3000",
            "methods": ["POST"],
            "allow_headers": ["Content-Type"],
        },
        r"/refineStudyPlan": {
            "origins": "http://localhost:3000",
            "methods": ["POST"],
            "allow_headers": ["Content-Type"],
        },
        r"/generateStudyPlanVideos": {
            "origins": "http://localhost:3000",
            "methods": ["POST"],
            "allow_headers": ["Content-Type"],
        },
        r"/chat/*": {
            "origins": "http://localhost:3000",
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

    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    response = model.generate_content(
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
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    response = model.generate_content(
        contents=prompt,
    )
    return response.text


# @app.route("/generateStudyPlanVideos", methods=["POST"])
# def generateStudyPlanVideos():
#     # Send request with function declarations
#     data = request.get_json()
#     studyPlanWithVoiceActor = data.get("studyPlan", "")
#     voiceActor = data.get("voiceActor", "")
#     background = data.get("background", "")
    
#     generatedStudyPlanVideoPaths = []

#     voiceActorToId = {
#         "Peter Griffin": "ZKKGJ1ndjlgyRQkzl9CE",
#         "SpongeBob": "ZKKGJ1ndjlgyRQkzl9CE",
#         "Joe Biden": "ZKKGJ1ndjlgyRQkzl9CE",
#     }

#     voiceActorId = voiceActorToId.get(voiceActor, "")
#     if not voiceActorId:
#         return "Invalid voice actor selected."

#     for videoInfo in studyPlanWithVoiceActor:
#         # Send request with function declarations
#         videoPath = video.generateAndSaveVideo(videoInfo, voiceActorId, studyPlanWithVoiceActor)
#         generateStudyPlanVideos.append(videoPath)

#     return generatedStudyPlanVideoPaths

@app.route("/chat/start", methods=["POST"])
def start_chat():
    """Start a new chat session with optional study plan context"""
    data = request.get_json()
    study_plan = data.get("studyPlan", None)
    
    try:
        session_id = chat.start_new_chat(study_plan)
        return jsonify({
            "session_id": session_id,
            "message": "Chat session started successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        return jsonify({
            "response": response_text
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    response = model.generate_content("Explain how AI works in a few words")
    print(response.text)
    app.run(host="localhost", port=4000, debug=True)
