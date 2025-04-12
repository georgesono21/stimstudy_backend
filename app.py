import json
import os
from flask import Flask
from google import genai
from dotenv import load_dotenv
import prompts
from flask import request

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

@app.route('/')
def hello_world():
    return 'Hello, World! This is a Flask application running in a Docker container.'

@app.route("/createStudyPlan")
def createStudyPlan():

    data = request.get_json()
    userPrompt = data.get("prompt", "")

    prompt = prompts.createStudyPlanPrompt(userPrompt)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    return response.text

@app.route("/refineStudyPlan")
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



if __name__ == "__main__":
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents="Explain how AI works in a few words"
    )
    app.run(host="localhost", port=4000, debug=True)
w
