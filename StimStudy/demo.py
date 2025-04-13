#!/usr/bin/env python3
"""
Demo script showing how to generate multiple videos using the master script.
"""

import os
import time
import argparse
import sys
from master import generate_video
from tqdm import tqdm

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate multiple educational videos")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent workers (default: 4)")
    parser.add_argument("--topics", type=str, nargs="+", 
                        default=["pythagorean theorem", "how photosynthesis works", "basics of machine learning"],
                        help="List of topics to generate videos for")
    args = parser.parse_args()
    
    # Get the topics and worker count
    topics = args.topics
    max_workers = args.workers
    
    print("\n🎬 BATCH VIDEO GENERATOR 🎬")
    print("=" * 50)
    print(f"Starting video generation for {len(topics)} topics using {max_workers} concurrent workers")
    
    # Store results for each topic
    results = []
    
    # Create a progress bar for topics
    with tqdm(total=len(topics), desc="Overall Progress", unit="video") as topic_progress:
        # Generate videos for each topic
        for i, topic in enumerate(topics):
            print(f"\n{'='*50}")
            print(f"Generating video {i+1}/{len(topics)}: '{topic}'")
            print(f"{'='*50}\n")
            
            # Call the generate_video function with concurrent processing
            start_time = time.time()
            result = generate_video(topic, max_workers=max_workers)
            end_time = time.time()
            
            # Add total processing time to result if not already there
            if "processing_time" not in result or not isinstance(result["processing_time"], dict):
                result["processing_time"] = {
                    "total": end_time - start_time,
                    "measured_externally": True
                }
            
            results.append(result)
            
            total_time = result["processing_time"]["total"] if isinstance(result["processing_time"], dict) else result["processing_time"]
            
            # Use short feedback after each video is complete
            status_symbol = "✅" if result["status"] == "success" else "❌"
            print(f"\n{status_symbol} Video {i+1}/{len(topics)} ({topic}): {result['status']} in {total_time:.2f}s")
            
            # Update overall progress
            topic_progress.update(1)
            
            # Wait a bit before starting the next topic
            if i < len(topics) - 1:
                wait_time = 5
                print(f"Starting next video in {wait_time} seconds...")
                time.sleep(wait_time)
    
    # Print summary of all generations
    print("\n\n" + "="*70)
    print("🎬 BATCH GENERATION SUMMARY 🎬")
    print("="*70)
    
    # Calculate total time for all videos
    total_batch_time = sum(
        result["processing_time"]["total"] if isinstance(result["processing_time"], dict) else result["processing_time"]
        for result in results
    )
    
    # Calculate success rate
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful
    success_rate = (successful / len(topics)) * 100 if topics else 0
    
    # Print summary statistics
    print(f"Total videos requested: {len(topics)}")
    print(f"Successfully generated: {successful} ({success_rate:.1f}%)")
    print(f"Failed: {failed}")
    print(f"Total batch processing time: {total_batch_time:.2f} seconds")
    print(f"Average time per video: {(total_batch_time / len(topics)):.2f} seconds" if topics else "N/A")
    print("\nDetails for each video:")
    print("-" * 70)
    
    # Print details for each video
    for i, result in enumerate(results):
        topic = result["topic"]
        status = result["status"]
        
        if status == "success":
            # Get processing time details
            proc_time = result["processing_time"]
            if isinstance(proc_time, dict):
                total_time = proc_time["total"]
                has_details = "content_generation" in proc_time
            else:
                total_time = proc_time
                has_details = False
                
            print(f"{i+1}. Topic: {topic}")
            print(f"   Status: ✅ Success")
            print(f"   Project directory: {result['project_dir']}")
            print(f"   Created {result['num_slides']} slides and {result['num_videos']} videos")
            
            # Print detailed timing if available
            if has_details:
                print(f"   Timing breakdown:")
                print(f"     - Content generation: {proc_time['content_generation']:.2f}s ({proc_time['content_generation']/total_time*100:.1f}%)")
                print(f"     - Audio generation: {proc_time['audio_generation']:.2f}s ({proc_time['audio_generation']/total_time*100:.1f}%)")
                print(f"     - Video rendering: {proc_time['video_rendering']:.2f}s ({proc_time['video_rendering']/total_time*100:.1f}%)")
            
            print(f"   Total processing time: {total_time:.2f} seconds")
        else:
            print(f"{i+1}. Topic: {topic}")
            print(f"   Status: ❌ Failed")
            print(f"   Error: {result['error']}")
            print(f"   Project directory: {result['project_dir']}")
        
        print()
    
    # List the output directories
    print("=" * 70)
    print("📁 OUTPUT DIRECTORIES:")
    for result in results:
        if result["status"] == "success":
            print(f"- {result['project_dir']} ({result['num_videos']} videos)")
    
    print("\nBatch processing complete!")

if __name__ == "__main__":
    main() 