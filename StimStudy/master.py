#!/usr/bin/env python3
import os
import json
import shutil
import argparse
import uuid
import concurrent.futures
import time
import sys
import re
import threading
from datetime import datetime
from StimStudy.agent import create_script_and_slides, create_slide
from StimStudy.fish_audio import generate_voice_audio
from StimStudy.render_html import process_html_file
from dotenv import load_dotenv
from tqdm import tqdm

# Import functionality from existing scripts
# from agent import create_script_and_slides, create_slide
# from fish_audio import generate_voice_audio
# from render_html import process_html_file

# Load environment variables
load_dotenv()

# Global semaphore to limit rendering concurrency
# This ensures only 4 videos are sent to the rendering engine at once
render_semaphore = threading.Semaphore(4)

class LogWindow:
    """Class to manage a scrolling log window with limited number of visible logs"""
    def __init__(self, max_logs=10, progress_bar=None, topic=None):
        self.logs = []
        self.max_logs = max_logs
        self.progress_bar = progress_bar
        self.status_message = ""
        self.topic = f"[{topic}] " if topic else ""
        self.lock = threading.Lock()  # Add lock for thread safety
        
    def add_log(self, message):
        """Add a log message to the window"""
        with self.lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {self.topic}{message}"
            self.logs.append(log_entry)
            
            # Keep only the last max_logs entries
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
            
            # Update the display (only if not multi-topic mode)
            if not self.topic:
                self.update_display()
            else:
                # Just print the log when in multi-topic mode
                print(log_entry)
        
    def set_status(self, message):
        """Set the status message shown above the progress bar"""
        with self.lock:
            self.status_message = message
            # Update the display (only if not multi-topic mode)
            if not self.topic:
                self.update_display()
        
    def update_display(self):
        """Update the terminal display with current logs and progress bar"""
        # Clear the terminal (compatible with different platforms)
        if os.name == 'nt':  # For Windows
            os.system('cls')
        else:  # For Linux/Mac
            os.system('clear')
        
        # Print header
        print("\n🎬 VIDEO ASSET GENERATOR 🎬")
        print("=" * 50)
        
        # Print log window
        print("\n📋 LOG WINDOW:")
        print("-" * 50)
        for log in self.logs:
            print(log)
        
        # Fill any remaining log lines with empty space
        remaining = self.max_logs - len(self.logs)
        for _ in range(remaining):
            print()
            
        # Print footer
        print("-" * 50)
        
        # Print status message
        if self.status_message:
            print(f"\nStatus: {self.status_message}")
        
        # If we have a progress bar, tqdm will handle its display
        if self.progress_bar:
            # We don't need to do anything here, as tqdm manages its own display
            pass
        else:
            # Just ensure there's space for a progress bar
            print("\n\n")

# Create a global log window instance
log_window = LogWindow()

def create_project_directory(topic):
    """
    Create a project directory structure for a specific video topic
    Returns the path to the project directory
    """
    # Create a project ID with timestamp and slug of the topic
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    topic_slug = topic.lower().replace(" ", "_")[:10]  # Limit length and make URL-friendly
    project_id = f"{timestamp}_{topic_slug}"
    
    # Create base assets directory if it doesn't exist
    assets_dir = "ASSETS"
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        
    # Create project directory
    project_dir = os.path.join(assets_dir, project_id)
    os.makedirs(project_dir, exist_ok=True)
    
    # Create subdirectories
    os.makedirs(os.path.join(project_dir, "slides"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "audio_clips"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "videos"), exist_ok=True)
    
    log_window.add_log(f"Created project directory: {project_dir}")
    
    return project_dir

def generate_content(topic, project_dir):
    """Generate script and slides content for the given topic"""
    log_window.add_log(f"Generating script and slides for topic: {topic}")
    
    # Get script and slides content
    log_window.set_status("Generating content with AI...")
    response = create_script_and_slides(topic)
    
    # Save output.json in the project directory
    output_file = os.path.join(project_dir, "output.json")
    with open(output_file, 'w') as f:
        f.write(response)
    
    try:
        # Load the content for slides generation
        slides_data = json.loads(response)
        
        # Process slides iteratively, passing previous slide content
        slides_dir = os.path.join(project_dir, "slides")
        previous_slide_html = ""
        
        # Track successful slides
        successful_slides = 0
        
        # Create progress bar for slides
        log_window.set_status("Creating HTML slides...")
        with tqdm(total=len(slides_data), desc="HTML Slides", file=sys.stdout) as slide_progress:
            log_window.progress_bar = slide_progress
            
            for index, slide in enumerate(slides_data):
                try:
                    # Extract script and visual description
                    script = slide["script"]
                    visual_description = slide["visual_description"]
                    
                    # Generate HTML for the slide, passing previous slide content
                    slide_html = create_slide(script, visual_description, previous_slide_html)
                    
                    # Strip markdown code formatting (```html and ```)
                    import re
                    slide_html = re.sub(r'^```html\s*|\s*```$', '', slide_html.strip())
                    
                    # Save the HTML to a file
                    slide_filename = os.path.join(slides_dir, f"slide_{index+1}.html")
                    with open(slide_filename, 'w') as f:
                        f.write(slide_html)
                    
                    # Store this slide's HTML to pass to the next slide
                    previous_slide_html = slide_html
                    
                    log_window.add_log(f"Created slide {index+1}/{len(slides_data)}")
                    successful_slides += 1
                    slide_progress.update(1)
                except Exception as e:
                    log_window.add_log(f"Error creating slide {index+1}: {str(e)}")
                    # Continue with next slide
            
            log_window.progress_bar = None
        
        if successful_slides == 0:
            raise Exception("Failed to create any slides")
            
        return output_file, successful_slides
    except Exception as e:
        log_window.add_log(f"Error generating slides: {str(e)}")
        raise

def process_audio_for_slide(args):
    """Process a single slide's audio (for concurrent processing)"""
    index, script_text, reference_id, audio_dir = args
    
    try:
        # Generate audio for this script
        audio_data = generate_voice_audio(script_text, reference_id=reference_id)
        
        # Save the audio to a file
        output_file = os.path.join(audio_dir, f"slide_{index+1}.mp3")
        with open(output_file, "wb") as f:
            f.write(audio_data)
        
        # Calculate audio duration using mutagen
        from mutagen.mp3 import MP3
        mp3_file = MP3(output_file)
        duration_seconds = mp3_file.info.length
        
        # Create a record for this audio file
        audio_info = {
            "slide_number": index + 1,
            "filename": f"slide_{index+1}.mp3",
            "duration_seconds": duration_seconds
        }
        
        return audio_info
    except Exception as e:
        # Return a default duration to prevent blocking the process
        return {
            "slide_number": index + 1,
            "filename": f"slide_{index+1}.mp3",
            "duration_seconds": 5.0,  # Default duration in case of error
            "error": str(e)
        }

def generate_audio(output_file, project_dir, voice_actor_id, max_workers=4):
    """Generate audio files for the scripts in output.json concurrently"""
    log_window.add_log("Generating audio files concurrently...")
    
    # Define the reference ID for the voice model
    reference_id = voice_actor_id  # Default model from fish_audio.py
    
    # Define output directory for audio
    audio_dir = os.path.join(project_dir, "audio_clips")
    
    # Read the output.json file
    with open(output_file, "r") as f:
        scripts_data = json.load(f)
    
    log_window.add_log(f"Found {len(scripts_data)} script entries in output.json")
    
    # Prepare arguments for concurrent processing
    audio_args = []
    for index, entry in enumerate(scripts_data):
        script_text = entry["script"]
        audio_args.append((index, script_text, reference_id, audio_dir))
    
    # Process audio concurrently with progress bar
    log_window.set_status("Generating audio...")
    audio_durations = []
    
    with tqdm(total=len(audio_args), desc="Audio Generation", file=sys.stdout) as audio_progress:
        log_window.progress_bar = audio_progress
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_slide = {executor.submit(process_audio_for_slide, args): args[0] for args in audio_args}
            
            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_slide):
                slide_index = future_to_slide[future]
                try:
                    audio_info = future.result()
                    audio_durations.append(audio_info)
                    log_window.add_log(f"Generated audio for slide {slide_index+1} ({audio_info['duration_seconds']:.2f}s)")
                except Exception as e:
                    log_window.add_log(f"Error processing slide {slide_index+1}: {str(e)}")
                    # Add default audio info to maintain order
                    audio_durations.append({
                        "slide_number": slide_index + 1,
                        "filename": f"slide_{slide_index+1}.mp3",
                        "duration_seconds": 5.0,
                        "error": str(e)
                    })
                
                # Update progress bar
                audio_progress.update(1)
        
        log_window.progress_bar = None
    
    # Sort audio durations by slide number to ensure correct order
    audio_durations.sort(key=lambda x: x["slide_number"])
    
    # Write the duration information to a JSON file
    durations_file = os.path.join(audio_dir, "audio_durations.json")
    with open(durations_file, "w") as f:
        json.dump(audio_durations, f, indent=2)
    
    log_window.add_log(f"Saved audio durations to {durations_file}")
    
    return durations_file

def process_video_for_slide(args):
    """Process a single slide's video (for concurrent processing)"""
    html_file, audio_durations, videos_dir = args
    try:
        # Acquire the semaphore to limit concurrent rendering operations
        with render_semaphore:
            log_window.add_log(f"Rendering video for {os.path.basename(html_file)}")
            success = process_html_file(html_file, audio_durations, videos_dir)
            if success:
                return os.path.basename(html_file)
            else:
                return f"Failed to process {os.path.basename(html_file)}"
    except Exception as e:
        return f"Error: {str(e)}"

def render_videos(project_dir, durations_file, max_workers=4):
    """Render videos from HTML slides using audio durations concurrently"""
    log_window.add_log("Rendering videos from HTML slides concurrently...")
    
    # Load audio durations
    with open(durations_file, 'r') as file:
        audio_durations = json.load(file)
    
    # Get paths
    slides_dir = os.path.join(project_dir, "slides")
    videos_dir = os.path.join(project_dir, "videos")
    
    # Get all HTML files from slides directory
    import glob
    html_files = glob.glob(os.path.join(slides_dir, "*.html"))
    
    if not html_files:
        log_window.add_log(f"No HTML files found in {slides_dir} directory.")
        return []
        
    log_window.add_log(f"Found {len(html_files)} HTML files to process.")
    
    # Prepare arguments for concurrent processing
    video_args = [(html_file, audio_durations, videos_dir) for html_file in html_files]
    
    # Process videos concurrently with progress bar
    log_window.set_status("Rendering videos...")
    successful_videos = []
    
    with tqdm(total=len(video_args), desc="Video Rendering", file=sys.stdout) as video_progress:
        log_window.progress_bar = video_progress
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_html = {executor.submit(process_video_for_slide, args): args[0] for args in video_args}
            
            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_html):
                html_file = future_to_html[future]
                try:
                    result = future.result()
                    if not result.startswith("Failed") and not result.startswith("Error"):
                        successful_videos.append(os.path.join(videos_dir, os.path.splitext(result)[0] + ".mp4"))
                    log_window.add_log(f"Rendered video for {result}")
                except Exception as e:
                    log_window.add_log(f"Error processing video for {html_file}: {str(e)}")
                
                # Update progress bar
                video_progress.update(1)
        
        log_window.progress_bar = None
    
    # Return the list of created video files
    return glob.glob(os.path.join(videos_dir, "*.mp4"))

def process_topic(topic, voice_actor_id, max_workers=4):
    """Process a single topic to generate a video"""
    # Create a topic-specific log window
    topic_log = LogWindow(max_logs=10, topic=topic)
    
    # Use the topic-specific log window for this thread
    global log_window
    log_window = topic_log
    
    # Create project directory
    project_dir = create_project_directory(topic)
    log_window.add_log(f"Starting video generation for topic: {topic}")
    
    result = {
        "topic": topic,
        "project_dir": project_dir,
        "status": "failed",
        "error": None
    }
    
    try:
        # Step 1: Generate content (scripts and slides) - SEQUENTIAL
        log_window.add_log("=== Step 1: Generating content (scripts and slides) ===")
        start_time = time.time()
        output_file, num_slides = generate_content(topic, project_dir)
        end_time = time.time()
        step1_time = end_time - start_time
        
        result["output_json"] = output_file
        result["num_slides"] = num_slides
        log_window.add_log(f"Generated {num_slides} slides and saved to {output_file}")
        log_window.add_log(f"Content generation completed in {step1_time:.2f} seconds")
        
        # Step 2: Generate audio - CONCURRENT
        log_window.add_log(f"=== Step 2: Generating audio (concurrent with {max_workers} workers) ===")
        start_time = time.time()
        durations_file = generate_audio(output_file, project_dir, voice_actor_id, max_workers=max_workers)
        end_time = time.time()
        step2_time = end_time - start_time
        
        result["durations_file"] = durations_file
        log_window.add_log(f"Generated audio files and durations")
        log_window.add_log(f"Audio generation completed in {step2_time:.2f} seconds")
        
        # Step 3: Render videos - CONCURRENT
        log_window.add_log(f"=== Step 3: Rendering videos (concurrent with {max_workers} workers) ===")
        start_time = time.time()
        video_files = render_videos(project_dir, durations_file, max_workers=max_workers)
        end_time = time.time()
        step3_time = end_time - start_time
        
        result["video_files"] = video_files
        result["num_videos"] = len(video_files)
        log_window.add_log(f"Rendered {len(video_files)} video files")
        log_window.add_log(f"Video rendering completed in {step3_time:.2f} seconds")
        
        # Calculate total time
        total_time = step1_time + step2_time + step3_time
        result["processing_time"] = {
            "content_generation": step1_time,
            "audio_generation": step2_time,
            "video_rendering": step3_time,
            "total": total_time
        }
        
        log_window.set_status(f"✅ Project completed successfully in {total_time:.2f}s!")
        log_window.add_log(f"Project completed successfully!")
        log_window.add_log(f"All assets are available in: {project_dir}")
        log_window.add_log(f"Total processing time: {total_time:.2f} seconds")
        
        result["status"] = "success"
        return result
        
    except Exception as e:
        log_window.set_status(f"❌ Error: {str(e)}")
        log_window.add_log(f"Error in processing: {str(e)}")
        import traceback
        log_window.add_log("See full traceback in console")
        traceback.print_exc()
        
        result["status"] = "failed"
        result["error"] = str(e)
        return result

def generate_videos(topics, voice_actor_id, max_workers=4, max_concurrent_topics=None):
    """
    Main function to generate videos for multiple topics concurrently.
    This is the function other scripts should call for batch processing.
    
    Args:
        topics (list): List of topics to generate videos for
        max_workers (int): Maximum number of concurrent workers for audio and video processing per topic
        max_concurrent_topics (int, optional): Maximum number of topics to process concurrently
                                               Defaults to None (uses CPU count)
    
    Returns:
        list: List of results for each topic
    """
    if not topics:
        print("No topics provided")
        return []
    
    if not max_concurrent_topics:
        # Default to CPU count or 4, whichever is less
        max_concurrent_topics = min(os.cpu_count() or 2, 4)
    
    print(f"🎬 PROCESSING {len(topics)} TOPICS CONCURRENTLY (max {max_concurrent_topics} at a time)")
    print("=" * 70)
    print(f"Topics: {', '.join(topics)}")
    print(f"Max workers per topic: {max_workers}")
    print(f"Max concurrent topics: {max_concurrent_topics}")
    print(f"Rendering engine limit: 4 videos at a time")
    print("=" * 70)
    
    results = []
    start_time = time.time()
    
    # Process topics concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent_topics) as executor:
        future_to_topic = {executor.submit(process_topic, topic, voice_actor_id, max_workers): topic for topic in topics}
        
        # Show overall progress bar
        with tqdm(total=len(topics), desc="Overall Progress", unit="topic") as progress:
            for future in concurrent.futures.as_completed(future_to_topic):
                topic = future_to_topic[future]
                try:
                    result = future.result()
                    results.append(result)
                    status = "✅ Success" if result["status"] == "success" else f"❌ Failed: {result['error']}"
                    print(f"\nCompleted topic: {topic} - {status}")
                except Exception as e:
                    print(f"\nError processing topic {topic}: {str(e)}")
                    results.append({
                        "topic": topic,
                        "status": "failed",
                        "error": str(e)
                    })
                progress.update(1)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Print summary
    print("\n" + "=" * 70)
    print("🎬 BATCH PROCESSING COMPLETE 🎬")
    print("=" * 70)
    
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(topics) - successful
    success_rate = (successful / len(topics)) * 100 if topics else 0
    
    print(f"Total topics: {len(topics)}")
    print(f"Successful: {successful} ({success_rate:.1f}%)")
    print(f"Failed: {failed}")
    print(f"Total processing time: {total_time:.2f} seconds")
    
    # List successful projects
    if successful > 0:
        print("\nSuccessful projects:")
        for result in results:
            if result["status"] == "success":
                print(f"- {result['project_dir']} ({result['num_videos']} videos)")
    
    return results

def generate_video(topic, max_workers=4):
    """
    Generate a video for a single topic (for backward compatibility)
    
    Args:
        topic (str): The topic for the video
        max_workers (int): Maximum number of concurrent workers for audio and video processing
        
    Returns:
        dict: Information about the generated video
    """
    # Initialize the log window
    global log_window
    log_window = LogWindow(max_logs=10)
    
    return process_topic(topic, max_workers)

def main():
    """Interactive function to get topics from the user and generate videos"""
    print("\n🎬 VIDEO ASSET GENERATOR 🎬")
    print("=" * 60)
    print("This tool generates educational videos from topics you provide.")
    print("Multiple topics will be processed concurrently.")
    print("-" * 60)
    
    # Get topics from user input
    topics_input = input("\nEnter topics (separated by commas): ")
    topics = [topic.strip() for topic in topics_input.split(",") if topic.strip()]
    
    if not topics:
        print("No topics provided. Using default example topics.")
        topics = ["explain the fourth dimension", "quantum physics for beginners", "history of jazz music"]
    
    # Get number of worker threads (optional)
    workers_input = input(f"\nEnter max workers per topic [default: 4]: ")
    try:
        max_workers = int(workers_input) if workers_input.strip() else 4
    except ValueError:
        print("Invalid input. Using default value of 4 workers.")
        max_workers = 4
    
    # Get number of concurrent topics (optional)
    concurrent_input = input(f"\nEnter max concurrent topics [default: {min(os.cpu_count() or 2, 4)}]: ")
    try:
        max_concurrent_topics = int(concurrent_input) if concurrent_input.strip() else None
    except ValueError:
        print("Invalid input. Using default value.")
        max_concurrent_topics = None
    
    print("\n" + "-" * 60)
    print(f"Processing {len(topics)} topics:")
    for i, topic in enumerate(topics):
        print(f"{i+1}. {topic}")
    print("-" * 60)
    
    # Confirm with the user
    confirm = input("\nStart processing? (y/n): ").lower().strip()
    if confirm != 'y' and confirm != 'yes':
        print("Operation cancelled.")
        return
    
    # Generate videos for multiple topics concurrently
    results = generate_videos(
        topics=topics, 
        max_workers=max_workers,
        max_concurrent_topics=max_concurrent_topics
    )
    
    # Print summary statistics
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful
    
    print(f"\nGenerated {successful} videos successfully, {failed} failed")
    
    # For backward compatibility, if only one topic provided, print individual details
    if len(topics) == 1 and successful == 1:
        result = next(r for r in results if r["status"] == "success")
        print("\n" + "="*50)
        print("GENERATION SUMMARY")
        print("="*50)
        print(f"Successfully generated video for '{topics[0]}'")
        print(f"Project directory: {result['project_dir']}")
        print(f"Number of slides: {result['num_slides']}")
        print(f"Number of videos: {result['num_videos']}")
        print(f"Processing times:")
        print(f"  - Content generation: {result['processing_time']['content_generation']:.2f}s")
        print(f"  - Audio generation: {result['processing_time']['audio_generation']:.2f}s")
        print(f"  - Video rendering: {result['processing_time']['video_rendering']:.2f}s")
        print(f"  - Total time: {result['processing_time']['total']:.2f}s")

if __name__ == "__main__":
    main() 