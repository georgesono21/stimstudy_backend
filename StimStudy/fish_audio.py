from dotenv import load_dotenv
import os
import json
from fish_audio_sdk import Session, TTSRequest
from mutagen.mp3 import MP3
from io import BytesIO

# Load environment variables from the .env file
load_dotenv()

def generate_voice_audio(text: str, reference_id: str | None = None) -> bytes:
    """
    Converts text to speech using the Fish Audio API and returns the audio as bytes.
    
    Parameters:
        text (str): The text to be converted into speech.
        reference_id (str, optional): The model ID to be used (if any). 
                                      This should be the ID of a model you have uploaded or chosen from the Fish Audio playground.
    
    Returns:
        bytes: The complete audio stream data.
    """
    # Retrieve the API key from the environment variable
    API_KEY = os.environ.get("FISHAUDIO_API_KEY")
    if not API_KEY:
        raise ValueError("FISHAUDIO_API_KEY not found in environment variables. "
                         "Ensure you have a .env file with FISHAUDIO_API_KEY set.")

    # Initialize a session with the Fish Audio API using your API key.
    session = Session(API_KEY)
    
    # Create the TTS request.
    # If reference_id is provided, it will be used to select the model.
    request_payload = TTSRequest(text=text)
    if reference_id:
        request_payload.reference_id = reference_id

    # Stream the audio chunks and collect them into a single bytes object.
    audio_bytes = b""
    for chunk in session.tts(request_payload):
        audio_bytes += chunk

    return audio_bytes

def main():
    # Define the reference ID for the voice model
    reference_id = "54e3a85ac9594ffa83264b8a494b901b"
    
    # Define output directory
    output_dir = "audio_clips"
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    try:
        # Read the output.json file
        with open("output.json", "r") as f:
            scripts_data = json.load(f)
        
        print(f"Found {len(scripts_data)} script entries in output.json")
        
        # List to store audio duration information
        audio_durations = []
        
        # Process each script entry
        for index, entry in enumerate(scripts_data):
            script_text = entry["script"]
            
            # Generate audio for this script
            print(f"Generating audio for script {index+1}...")
            audio_data = generate_voice_audio(script_text, reference_id=reference_id)
            
            # Save the audio to a file
            output_file = os.path.join(output_dir, f"slide_{index+1}.mp3")
            with open(output_file, "wb") as f:
                f.write(audio_data)
            
            # Calculate audio duration using mutagen
            mp3_file = MP3(output_file)
            duration_seconds = mp3_file.info.length
            
            # Create a record for this audio file
            audio_info = {
                "slide_number": index + 1,
                "filename": f"slide_{index+1}.mp3",
                "duration_seconds": duration_seconds
            }
            audio_durations.append(audio_info)
            
            print(f"Saved audio to {output_file} (duration: {duration_seconds:.2f} seconds)")
        
        # Write the duration information to a JSON file
        durations_file = os.path.join(output_dir, "audio_durations.json")
        with open(durations_file, "w") as f:
            json.dump(audio_durations, f, indent=2)
        
        print(f"Saved audio durations to {durations_file}")
        print(f"Successfully generated {len(scripts_data)} audio files in the '{output_dir}' folder.")
        
    except Exception as e:
        print("An error occurred:", str(e))

if __name__ == "__main__":
    main()
