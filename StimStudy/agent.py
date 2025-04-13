import os
from StimStudy.prompt import get_script_and_slides_prompt, get_slide_prompt
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
import concurrent.futures

# Load environment variables
load_dotenv()

guidlines = """
When creating this video follow these guidelines:
1. Be funny and use genz slang and humor.
1. The whole video should be 200 words or less.
2. Create only 1-4 slides.
4. Keep slides simple and concise.
5. The slide visuals will eventually be created with HTML, so keep the detail in range of what is possible with HTML.
"""

class Video(BaseModel):
  script: str
  visual_description: str

# Configure the client and tools
client = genai.Client(api_key=os.getenv("APIKEY"))
config={
        'response_mime_type': 'application/json',
        'response_schema': list[Video],
}

def create_script_and_slides(prompt):
    # Send request with function declarations
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=get_script_and_slides_prompt(prompt, guidlines),
        config=config,
    )

    return response.text

def save_to_json(content, filename="output.json"):
    """Save content to a JSON file"""
    import json
    with open(filename, 'w') as f:
        f.write(content)
    return filename


def create_slide(script, visual_description, previous_slides):
    # Send request with function declarations
    response = client.models.generate_content(
        model="gemini-2.5-pro-exp-03-25",
        contents=get_slide_prompt(script, visual_description, previous_slides),
        # config=config,
    )
    
    return response.text

def create_video(output_file):
    import json
    import os
    import shutil
    import re
    
    # Clean slides directory if it exists
    if os.path.exists("slides"):
        shutil.rmtree("slides")
    
    # Create slides directory
    os.makedirs("slides", exist_ok=True)
    
    # Read the JSON file
    with open(output_file, 'r') as f:
        slides_data = json.loads(f.read())
    
    # Process slides iteratively, passing previous slide content
    previous_slide_html = ""
    for index, slide in enumerate(slides_data):
        # Extract script and visual description
        script = slide["script"]
        visual_description = slide["visual_description"]
        
        # Generate HTML for the slide, passing previous slide content
        slide_html = create_slide(script, visual_description, previous_slide_html)
        
        # Strip markdown code formatting (```html and ```)
        slide_html = re.sub(r'^```html\s*|\s*```$', '', slide_html.strip())
        
        # Save the HTML to a file
        slide_filename = f"slides/slide_{index+1}.html"
        with open(slide_filename, 'w') as f:
            f.write(slide_html)
        
        # Store this slide's HTML to pass to the next slide
        previous_slide_html = slide_html
        
        print(f"Created {slide_filename}")
    
    return f"Created {len(slides_data)} slides iteratively in the 'slides' directory"
