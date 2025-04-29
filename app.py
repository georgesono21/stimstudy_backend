import json
import os
import time
import uuid
from StimStudy.master import generate_videos
import chat
from flask import Flask, jsonify, send_file, request
from google import genai
from dotenv import load_dotenv
import prompts
from flask import request
from flask_cors import CORS
from flask_socketio import SocketIO

from video import generate_and_combine_videos

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv('APIKEY'))
socketio = SocketIO(app)


CORS(
    app,
    resources={
        r"/createStudyPlan": {
            "origins": ["http://localhost:8080"],
            "methods": ["POST"],
            "allow_headers": ["Content-Type"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": True,
        },
        r"/refineStudyPlan": {
            "origins": ["http://localhost:8080"],
            "methods": ["POST"],
            "allow_headers": ["Content-Type"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": True,
        },
        r"/generateStudyPlanVideos": {
            "origins": ["http://localhost:8080"],
            "methods": ["POST", "OPTIONS"],  # Added OPTIONS
            "allow_headers": ["Content-Type"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": True,
        },
        r"/chat/*": {
            "origins": ["http://localhost:8080"],
            "methods": ["POST"],
            "allow_headers": ["Content-Type"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": True,
        },
        r"/videos/*": {
            "origins": ["http://localhost:8080"],
            "methods": ["GET"],
            "allow_headers": ["Content-Type"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": True,
        },
    },
)

@socketio.on("connect")
def handle_connect():
    print("Client connected")
    socketio.emit("server_message", "Welcome to the server!")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")

@socketio.on("message")
def handle_message(data):
    print("received message: " + str(data))
    # Echo the message back to the client
    socketio.emit("message_response", f"Server received: {data}")

def send_progress_update(progress, message):
    """Utility function to send progress updates to connected clients"""
    socketio.emit("progress_update", {
        "progress": progress,
        "message": message
    })

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

    print("studyPlan", studyPlan)
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

    send_progress_update(0, "Starting video generation...")

    for i in range(len(studyPlan)):
        # studyPlan[i] = json.dumps(studyPlan[i])
        progress = (i / len(studyPlan)) * 100
        send_progress_update(progress, f"Processing video {i+1} of {len(studyPlan)}...")

    studyPlan = [
        {"title": "cruzhacks_overview_-_part_1"},
        {"title": "cruzhacks_overview_-_part_2"},
    ]

    # results = generate_videos(
    #     studyPlan,
    #     voiceActorId,
    #     max_workers=4,
    #     max_concurrent_topics=4
    # )

    # print("results", results)

    # print(studyPlan)
    seriesId = uuid.uuid4()
    for i in range(len(studyPlan)):
        # studyPlan[i] = json.loads(studyPlan[i])
        videoName = studyPlan[i]["title"].replace(' ', '_').lower()
        print("videoName", videoName)

        # Query the ASSETS directory for a matching folder name
        assets_dir = "ASSETS"
        matching_dirs = [
            dir_name for dir_name in os.listdir(assets_dir)
            if os.path.isdir(os.path.join(assets_dir, dir_name)) and videoName in dir_name
        ]

        if not matching_dirs:
            return jsonify({
                "error": f"No matching directory found for video name: {videoName}"
            }), 404

        folder_name = matching_dirs[0]
        # Use the first matching directory
        video_folder = os.path.join(assets_dir, matching_dirs[0])

        if not matching_dirs:
            return f"No matching directory found for video name: {videoName}"

        # Use the first matching directory
        audio_folder = f"ASSETS/{folder_name}/audio_clips"
        slide_folder = f"ASSETS/{folder_name}/videos"
        sprite_dir = "sprites"
        background_folder = "backgroundVideos"
        output_folder = "output"

        final_output_path = f"demo/{seriesId}"
        index = i
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
                                    index=index,
                                    title=videoName)
    send_progress_update(100, "Video generation complete!")

    generated_file_paths = []
    if os.path.exists(final_output_path):
        generated_file_paths = [
            os.path.join(final_output_path, file_name)
            for file_name in os.listdir(final_output_path)
            if os.path.isfile(os.path.join(final_output_path, file_name))
        ]
    return generated_file_paths


@app.route("/videos/<video_name>", methods=["GET"])
def serve_video(video_name):
    videos = {
        "dynamicProgrammingFibonacci.mp4": "/Users/coltonkirsten/Desktop/Projects/STIMSTUDYFRONT/stimstudy_frontend/demo/dynamicProgrammingFibonacci.mp4",
        "makingFriends.mp4": "/Users/coltonkirsten/Desktop/Projects/STIMSTUDYFRONT/stimstudy_frontend/demo/makingFriends.mp4",
    }

    if video_name in videos:
        return send_file(videos[video_name], mimetype="video/mp4")
    else:
        return jsonify({"error": "Video not found"}), 404


if __name__ == "__main__":
    socketio.run(app, host="localhost", port=4000, debug=True)
