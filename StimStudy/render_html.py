#!/usr/bin/env python3
import requests
import os
import json
import glob
import uuid

# Configuration
API_URL = "http://localhost:3000/convert"
SLIDES_DIR = "slides"
VIDEOS_DIR = "videos"
AUDIO_DURATIONS_FILE = "audio_clips/audio_durations.json"

def load_audio_durations():
    """Load audio durations from JSON file"""
    try:
        with open(AUDIO_DURATIONS_FILE, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading audio durations file: {e}")
        return []

def get_slide_number(filename):
    """Extract slide number from filename"""
    # Extract base name without extension
    base_name = os.path.splitext(os.path.basename(filename))[0]
    
    # Try to extract the number from different possible formats
    # Format: slide_X or slideX
    if '_' in base_name:
        parts = base_name.split('_')
        if len(parts) > 1 and parts[-1].isdigit():
            return int(parts[-1])
    else:
        # Try to extract any digits from the end of the filename
        import re
        match = re.search(r'(\d+)$', base_name)
        if match:
            return int(match.group(1))
    
    # If we couldn't extract a number, return None
    print(f"Warning: Could not extract slide number from {filename}")
    return None

def get_duration_for_slide(slide_number, audio_durations):
    """Get the duration for a slide number from the audio durations data"""
    for entry in audio_durations:
        if entry.get("slide_number") == slide_number:
            return entry.get("duration_seconds")
    
    # Default duration if not found
    print(f"Warning: No duration found for slide {slide_number}, using default 5 seconds")
    return 5

def main():
    # Load audio durations
    audio_durations = load_audio_durations()
    
    # Create videos directory if it doesn't exist
    if not os.path.exists(VIDEOS_DIR):
        os.makedirs(VIDEOS_DIR)
        print(f"Created directory: {VIDEOS_DIR}")
    
    # Get all HTML files from slides directory
    html_files = glob.glob(os.path.join(SLIDES_DIR, "*.html"))
    
    if not html_files:
        print(f"No HTML files found in {SLIDES_DIR} directory.")
        return
        
    print(f"Found {len(html_files)} HTML files to process.")
    
    for html_file in html_files:
        process_html_file(html_file, audio_durations)
    
    print("All videos generated successfully!")

def process_html_file(html_file_path, audio_durations, output_videos_dir=None):
    # Use the provided output directory or fall back to the default
    videos_dir = output_videos_dir if output_videos_dir else VIDEOS_DIR
    
    # Ensure the output directory exists
    if not os.path.exists(videos_dir):
        os.makedirs(videos_dir)
        print(f"Created directory: {videos_dir}")
    
    # Get base filename without extension
    base_name = os.path.basename(html_file_path)
    file_name_without_ext = os.path.splitext(base_name)[0]
    output_video = os.path.join(videos_dir, f"{file_name_without_ext}.mp4")
    
    # Get slide number from filename
    slide_number = get_slide_number(html_file_path)
    
    # Get duration for this slide
    duration = get_duration_for_slide(slide_number, audio_durations)
    
    print(f"Processing: {html_file_path} (Slide {slide_number}, Duration: {duration}s)")
    
    # Read HTML file
    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except Exception as e:
        print(f"Error reading HTML file {html_file_path}: {e}")
        return
    
    # Get absolute path for output video
    abs_output_video = os.path.abspath(output_video)
    
    # Prepare request payload
    payload = {
        "html": html_content,
        "duration": duration,  # Use the duration from audio file
        "frameRate": 30,
        "outputPath": abs_output_video  # Use absolute path for the output video
    }
    
    try:
        # Make request to the API server
        response = requests.post(
            API_URL, 
            json=payload, 
            headers={"Content-Type": "application/json"}
        )
        
        # Check response status
        if response.status_code == 200:
            # Parse the JSON response
            result = response.json()
            
            if result.get("success"):
                print(f"Video successfully generated and saved to: {result.get('videoPath')}")
                return True
            else:
                print(f"Error in API response: {result}")
                
                # If the API didn't save to the specified path, but provides a URL, download it
                if not os.path.exists(output_video) and "jobId" in result:
                    video_url = f"http://localhost:3000/videos/video_{result.get('jobId')}.mp4"
                    print(f"Downloading video from: {video_url}")
                    
                    # Download the video
                    video_response = requests.get(video_url, stream=True)
                    if video_response.status_code == 200:
                        with open(output_video, 'wb') as video_file:
                            for chunk in video_response.iter_content(chunk_size=8192):
                                if chunk:
                                    video_file.write(chunk)
                        print(f"Video downloaded and saved to: {output_video}")
                        return True
                    else:
                        print(f"Failed to download video: {video_response.status_code}")
                        return False
        else:
            print(f"Error response received: {response.status_code}")
            print(response.text)
            return False
    
    except Exception as e:
        print(f"Error making request: {e}")
        return False

if __name__ == "__main__":
    main() 