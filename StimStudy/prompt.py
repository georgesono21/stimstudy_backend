

def get_script_and_slides_prompt(prompt, guidlines):
    return f"""
    You are a video script generator for a learning platform. Your task is to convert a user's learning prompt into an engaging, educational TikTok-style video that effectively teaches the topic.

    Create a short form video script and slides based on the following prompt: {prompt}

    When creating this video follow these guidelines: {guidlines}

    The output must be a JSON array where each element is a JSON object representing one slide. Every JSON object must contain the following keys:

    "script": The script that will be read aloud while the slide is displayed.
    "visual_description": A detailed description of the visual content of the slide. This will be used to create an animated HTML slide.
"""

def get_slide_prompt(script, visual_description, previous_slides):
    return f"""
    Create an animated HTML slide. return only valid HTML, such that if your whole response is pasted into a file, it is valid HTML. The final slide will be displayed on a 1920 pixel width and 1080 pixel height screen.

    Script: <script>{script}</script> (this will be read aloud alongside HTML slide while itis displayed)
    Visual Description: <visual_description>{visual_description}</visual_description> (generate the HTML for the slide based on this description)
    Previous slides: <previous_slides>{previous_slides}</previous_slides> (the HTML for the previous slide that is shown just before this one. If there is no code provided, this is the first slide.)
"""