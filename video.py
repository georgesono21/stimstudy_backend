import os
import random
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    clips_array,
    concatenate_videoclips,
)


def generate_and_combine_videos(
    audio_folder,
    selected_character,
    sprite_dir,
    selected_background,
    background_folder,
    output_folder,
    slide_folder,
    final_output_path,
    index,
):
    # Resolve background video
    background_video_path = os.path.join(
        background_folder, f"{selected_background}.mp4"
    )

    if not os.path.isfile(background_video_path):
        raise FileNotFoundError(
            f"Background video '{background_video_path}' not found."
        )
    

    # Resolve character sprite directory and image
    character_dir = os.path.join(sprite_dir, selected_character)
    if not os.path.isdir(character_dir):
        raise FileNotFoundError(f"Character directory '{character_dir}' not found.")
    
    def get_character_image(character_dir, lastUsed):
        image_files = [
            file
            for file in os.listdir(character_dir)
            if file.endswith(".png") or file.endswith(".jpg")
        ]
        if not image_files:
            raise FileNotFoundError(
                f"No image found in character directory '{character_dir}'."
            )
        
        # Filter out the last used sprite
        available_images = [file for file in image_files if file != lastUsed]
        if not available_images:
            raise ValueError(
                "No available images left after excluding the last used one."
            )
        
        sprite_path = os.path.join(character_dir, random.choice(available_images))
        return sprite_path

    def generateAllCharacterVideos():
        print("🎬 Generating character videos...")
        audio_files = sorted(
            [f for f in os.listdir(audio_folder) if f.endswith(".mp3")]
        )

        lastUsed = ""
        for audio_file in audio_files:
            audio_name = os.path.splitext(audio_file)[0]
            audio_path = os.path.join(audio_folder, audio_file)
            audio_clip = AudioFileClip(audio_path)

            bg_clip = VideoFileClip(background_video_path).subclip(
                0, audio_clip.duration
            )
            output_name = os.path.join(output_folder, f"{audio_name}_video.mp4")
            
            sprite_path = get_character_image(character_dir, lastUsed)
            createCharacterVideo(audio_clip, sprite_path, bg_clip, output_name)
            lastUsed = sprite_path

        print("✅ Character videos generated.\n")

    def createCharacterVideo(audio_clip, character_img_path, bg_clip, output_path):
        character_clip = ImageClip(character_img_path)
        character_clip = (
            character_clip.set_duration(audio_clip.duration)
            .set_position((150, "bottom"))
            .resize(height=300)
        )

        final_video = CompositeVideoClip([bg_clip, character_clip])
        final_video = final_video.set_audio(audio_clip)

        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

    def combineSlidesWithSlides():
        print("🎞️ Combining slides with character videos...")
        final_clips = []

        slide_files = sorted(
            [f for f in os.listdir(slide_folder) if f.endswith(".mp4")]
        )
        for i, slide_file in enumerate(slide_files, 1):
            slide_path = os.path.join(slide_folder, slide_file)
            character_video_path = os.path.join(output_folder, f"slide_{i}_video.mp4")
            audio_path = os.path.join(audio_folder, f"slide_{i}.mp3")

            if not os.path.exists(character_video_path):
                print(f"⚠️ Missing character video: {character_video_path}")
                continue

            slide_clip = VideoFileClip(slide_path)
            character_clip = VideoFileClip(character_video_path)
            audio_clip = AudioFileClip(audio_path)

            width = max(slide_clip.w, character_clip.w)
            slide_clip = slide_clip.resize(width=width)
            character_clip = character_clip.resize(width=width)

            slide_clip = slide_clip.subclip(0, audio_clip.duration)
            character_clip = character_clip.subclip(0, audio_clip.duration)

            combined = clips_array([[slide_clip], [character_clip]])
            combined = combined.set_audio(audio_clip)

            final_clips.append(combined)

        if final_clips:
            os.makedirs(final_output_path, exist_ok=True)
            final_video_path = os.path.join(
                final_output_path, "final_combined_video.mp4"
            )
            final_video = concatenate_videoclips(final_clips, method="compose")
            final_video.write_videofile(
                final_video_path, codec="libx264", audio_codec="aac"
            )
            print(f"✅ Final video saved at: {final_video_path}")
        else:
            print("⚠️ No combined clips were created.")

    generateAllCharacterVideos()
    combineSlidesWithSlides()
