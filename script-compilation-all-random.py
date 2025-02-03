import json
import os
import random
import shutil
import traceback
from datetime import date
from moviepy.editor import VideoFileClip, concatenate_videoclips
from urllib.parse import urlparse, parse_qs

# Path to the backup directory containing pre-downloaded videos
backup_dir = os.path.expanduser(
    '/Users/personal/Library/Mobile Documents/com~apple~CloudDocs/python-youtube-knowledge-backup'
)

# Ensure temporary directories exist
os.makedirs('youtube-cut_videos', exist_ok=True)

# Directory to save the final video
final_video_dir = os.path.expanduser(
    '/Users/personal/Library/CloudStorage/GoogleDrive-souhailmerroun.entertainment@gmail.com/My Drive/youtube-knowledge'
)

# Empty out the youtube-knowledge folder before starting
if os.path.exists(final_video_dir):
    shutil.rmtree(final_video_dir)
os.makedirs(final_video_dir, exist_ok=True)

# Function to get video ID from URL
def get_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    elif parsed_url.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        query_params = parse_qs(parsed_url.query)
        return query_params.get('v', [None])[0]
    else:
        return None

# Function to cut video using moviepy
def cut_video(video_path, video_cuts):
    cut_paths = []
    try:
        for idx, video in enumerate(video_cuts):
            start_time = video["start_time"]
            end_time = start_time + video["duration"]
            output_path = f"youtube-cut_videos/cut_{video['title'].replace(' ', '_')}_{idx}.mp4"

            # Load video and extract subclip
            clip = VideoFileClip(video_path).subclip(start_time, end_time)
            clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

            cut_paths.append(output_path)
    except Exception as e:
        print(f"An error occurred while cutting the video '{video_path}': {e}")
    return cut_paths

# Function to format the duration in hours and minutes
def format_duration(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h{minutes:02d}m"
    else:
        return f"{minutes}m"

# Function to remove duplicate snippets from JSON data
def remove_duplicate_snippets(video_snippets):
    seen_snippets = set()
    unique_snippets = []
    
    for snippet in video_snippets:
        snippet_key = (snippet["start_time"], snippet["duration"], snippet["title"])
        if snippet_key not in seen_snippets:
            seen_snippets.add(snippet_key)
            unique_snippets.append(snippet)
    
    return unique_snippets

# Loop through all JSON files in youtube-data folder
data_folder = 'youtube-data'
cut_clips = []
cut_files = []
errors_occurred = False

for root, dirs, files in os.walk(data_folder):
    for json_file in files:
        if json_file.endswith('.json'):
            try:
                json_path = os.path.join(root, json_file)

                # Load video details from JSON file
                with open(json_path, 'r') as file:
                    videos = json.load(file)

                # Organize videos by URL
                videos_by_url = {}
                for video in videos:
                    if video["url"] not in videos_by_url:
                        videos_by_url[video["url"]] = []
                    videos_by_url[video["url"]].append(video)

                # Remove duplicate snippets
                for video_url in videos_by_url.keys():
                    videos_by_url[video_url] = remove_duplicate_snippets(videos_by_url[video_url])

                # Use pre-downloaded videos from backup_dir
                downloaded_videos = {}
                for url in videos_by_url.keys():
                    video_id = get_video_id(url)
                    if video_id is None:
                        print(f"Could not extract video ID from URL: {url}")
                        errors_occurred = True
                        continue
                    backup_video_path = os.path.join(backup_dir, f"{video_id}.mp4")
                    if os.path.exists(backup_video_path):
                        downloaded_videos[url] = backup_video_path
                    else:
                        print(f"Video '{video_id}.mp4' not found in backup directory.")
                        errors_occurred = True

                # Cut all videos and store paths of cut segments
                for url, video_path in downloaded_videos.items():
                    cut_video_paths = cut_video(video_path, videos_by_url[url])
                    for cut_video_path in cut_video_paths:
                        try:
                            cut_files.append(cut_video_path)  # Store path only
                        except Exception as e:
                            print(f"An error occurred while loading cut video '{cut_video_path}': {e}")
                            errors_occurred = True

            except Exception as e:
                print(f"An error occurred while processing '{json_file}': {e}")
                traceback.print_exc()
                errors_occurred = True
                continue

# Remove duplicate clips before concatenation
unique_cut_files = list(set(cut_files))  # Remove duplicate paths
unique_cut_clips = [VideoFileClip(f) for f in unique_cut_files]  # Reload unique clips

# Shuffle the clips randomly
random.shuffle(unique_cut_clips)

# Create the final compilation video
if unique_cut_clips:
    try:
        final_clip = concatenate_videoclips(unique_cut_clips)

        # Calculate the total duration of the final clip
        total_duration = final_clip.duration
        formatted_duration = format_duration(total_duration)

        # Prepare the output filename
        today_date = date.today().strftime('%Y-%m-%d')
        output_video_path = os.path.join(
            final_video_dir, f"{today_date} - random - all - {formatted_duration}.mp4"
        )

        # Save the final video
        final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")
        print(f"Final compilation video created successfully as '{output_video_path}'.")

    except Exception as e:
        print(f"An error occurred while creating the final compilation video: {e}")
        traceback.print_exc()
        errors_occurred = True

# Cleanup: delete all cut video segments and temporary folders
for cut_file in unique_cut_files:
    try:
        os.remove(cut_file)
    except Exception as e:
        print(f"Failed to delete temporary file '{cut_file}': {e}")

if os.path.exists('youtube-cut_videos'):
    shutil.rmtree('youtube-cut_videos')

if errors_occurred:
    print("Some errors occurred during processing. Please check the logs above.")
else:
    print("All videos processed successfully.")
