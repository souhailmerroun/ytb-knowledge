import json
import os
import traceback
from yt_dlp import YoutubeDL

# Backup directory path
backup_dir = os.path.expanduser(
    '/Users/personal/Library/Mobile Documents/com~apple~CloudDocs/python-youtube-knowledge-backup'
)

# Ensure backup directory exists
os.makedirs(backup_dir, exist_ok=True)

# Function to get video ID from URL
def get_video_id(url):
    return url.split("v=")[-1].split("&")[0]

# Function to download video using yt-dlp
def download_video(url, save_path):
    try:
        ydl_opts = {
            'format': 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]',
            'merge_output_format': 'mp4',
            'outtmpl': save_path,
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"Downloaded and saved: {save_path}")
        return save_path
    except Exception as e:
        print(f"An error occurred while downloading the video with URL '{url}': {e}")
        return None

# Process JSON files in the youtube-data folder
data_folder = 'youtube-data'
errors_occurred = False  # Flag to track errors

for root, dirs, files in os.walk(data_folder):
    for json_file in files:
        if json_file.endswith('.json'):
            try:
                json_path = os.path.join(root, json_file)

                # Load video details from JSON file
                with open(json_path, 'r') as file:
                    videos = json.load(file)

                # Check and ensure backups exist for all videos
                for video in videos:
                    url = video["url"]
                    video_id = get_video_id(url)
                    backup_path = os.path.join(backup_dir, f"{video_id}.mp4")

                    if not os.path.exists(backup_path):
                        print(f"Backup missing for video ID: {video_id}. Downloading...")
                        download_video(url, backup_path)
                    else:
                        print(f"Backup already exists for video ID: {video_id}.")
            
            except Exception as e:
                print(f"An error occurred while processing '{json_file}': {e}")
                traceback.print_exc()
                errors_occurred = True
                continue  # Skip to the next file

if errors_occurred:
    print("Some errors occurred during processing. Please check the logs above.")
else:
    print("All backups verified and created successfully.")
