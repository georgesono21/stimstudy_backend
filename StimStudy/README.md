# Video Asset Generator

This system generates educational videos automatically from a given topic. It creates HTML slides, audio narration, and rendered videos.

## Setup

1. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

2. Make sure you have `.env` file with the following keys:

   - `APIKEY` - Google Gemini API key
   - `FISHAUDIO_API_KEY` - Fish Audio API key

3. Ensure the HTML-to-video conversion server is running at `http://localhost:3000/convert`

## How It Works

The system has three main components:

1. **Content Generation** (agent.py): Uses Google Gemini to generate scripts and visual descriptions for slides
2. **Audio Generation** (fish_audio.py): Creates audio narration from scripts using Fish Audio API
3. **Video Rendering** (render_html.py): Converts HTML slides to videos with proper timing

All these components are integrated in the master.py script, which executes the workflow:

1. Generate output.json and HTML slides (sequential)
2. Generate audio files (concurrent)
3. Render videos (concurrent)

### Concurrent Processing

The system implements several levels of concurrency:

- **Multiple Topics**: Process multiple topics simultaneously (new!)
- **Audio Generation**: Generate audio files for each slide concurrently
- **Video Rendering**: Render video files for each slide concurrently

**Rendering Engine Protection**: The system ensures that only 4 videos are sent to the rendering engine simultaneously, regardless of how many topics are being processed.

### UI Features

The system includes a modern terminal UI with:

- **Log Window**: Shows the 10 most recent log messages in a scrolling window
- **Progress Bars**: Visual indicators of progress for each stage of processing
- **Status Updates**: Current status displayed at the bottom of the console
- **Completion Summary**: Detailed timing breakdown after processing completes

### Video Rendering API

The system uses a local API server to render videos from HTML:

```
POST http://localhost:3000/convert
Content-Type: application/json

{
  "html": "<your HTML content>",
  "duration": 10,
  "frameRate": 30,
  "outputPath": "/path/to/your/video.mp4"
}
```

The server returns a JSON response with information about the generated video, and the system saves the file at the specified path.

## Using the System

You can use the system in several ways:

### 1. Run directly from the command line (Interactive Mode)

```
python master.py
```

This will prompt you to:

- Enter topics (comma-separated)
- Set the number of worker threads per topic
- Set the maximum number of concurrent topics to process

The interactive interface provides guidance through the setup process and allows you to confirm before starting the video generation.

### 2. Run the demo script

```
python demo.py --workers 4 --topics "pythagorean theorem" "quantum computing" "history of jazz"
```

The demo script processes topics sequentially but provides a detailed summary report.

### 3. Import in your own script

```python
from master import generate_video, generate_videos

# For a single topic
result = generate_video("quantum computing", max_workers=4)

# For multiple topics concurrently
results = generate_videos(
    topics=["quantum computing", "history of jazz", "machine learning"],
    max_workers=4,  # Workers per topic
    max_concurrent_topics=3  # Topics to process simultaneously
)
```

## Performance Optimization

The system uses concurrent processing at multiple levels:

- **Multiple Topics**: Process different topics in parallel (configurable)
- **Audio Generation**: Generate audio files concurrently (configurable workers per topic)
- **Video Rendering**: Render videos concurrently (configurable workers per topic, max 4 rendering operations at once)

You can tune the concurrency parameters to match your system's capabilities:

- More `max_workers` will speed up audio generation and video rendering for each topic
- Higher `max_concurrent_topics` will process more topics simultaneously
- The system automatically limits rendering operations to prevent overloading the API

## Project Structure

When you generate a video, a project directory is created with the following structure:

```
ASSETS/
├── 20230615_123456_your_topic/
│   ├── output.json          # Scripts and visual descriptions
│   ├── slides/              # HTML slides
│   │   ├── slide_1.html
│   │   ├── slide_2.html
│   │   └── ...
│   ├── audio_clips/         # Audio narration
│   │   ├── slide_1.mp3
│   │   ├── slide_2.mp3
│   │   ├── audio_durations.json
│   │   └── ...
│   └── videos/              # Rendered videos
│       ├── slide_1.mp4
│       ├── slide_2.mp4
│       └── ...
```

Each video generation creates a separate project folder with timestamp and topic.
