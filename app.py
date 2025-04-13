import json
import os
import time
from flask import Flask
from google import genai
from dotenv import load_dotenv
import prompts
from flask import request
import video
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

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


@app.route("/generateStudyPlanVideos", methods=["POST"])
def generateStudyPlanVideos():
    # Send request with function declarations
    data = request.get_json()
    studyPlanWithVoiceActor = data.get("studyPlan", "")
    voiceActor = data.get("voiceActor", "")
    background = data.get("background", "")
    
    generatedStudyPlanVideoPaths = []

    voiceActorToId = {
        "Peter Griffin": "ZKKGJ1ndjlgyRQkzl9CE",
        "SpongeBob": "ZKKGJ1ndjlgyRQkzl9CE",
        "Joe Biden": "ZKKGJ1ndjlgyRQkzl9CE",
    }

    voiceActorId = voiceActorToId.get(voiceActor, "")
    if not voiceActorId:
        return "Invalid voice actor selected."

    for videoInfo in studyPlanWithVoiceActor:
        # Send request with function declarations
        videoPath = video.generateAndSaveVideo(videoInfo, voiceActorId, studyPlanWithVoiceActor)
        generateStudyPlanVideos.append(videoPath)

    return generatedStudyPlanVideoPaths


if __name__ == "__main__":
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents="Explain how AI works in a few words"
    )
    app.run(host="localhost", port=4000, debug=True)
