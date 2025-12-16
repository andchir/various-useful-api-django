#!/usr/bin/env python3
"""
Experiment script to test video audio replacement API endpoint with fade-out feature.
This script demonstrates the usage of the replace_video_audio API with use_fade_out parameter.
"""

import requests
import os
import sys

# Configuration
API_URL = "http://localhost:8000/api/v1/replace_video_audio"
USERNAME = "admin"  # Change to your username
PASSWORD = "admin"  # Change to your password

def test_replace_video_audio_with_fadeout(video_path, audio_path, use_fade_out=False):
    """
    Test the replace_video_audio API endpoint with fade-out option.

    Args:
        video_path: Path to the video file
        audio_path: Path to the audio file
        use_fade_out: Whether to enable fade-out when audio > video duration
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return False

    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found: {audio_path}")
        return False

    print(f"Testing video audio replacement API with fade-out...")
    print(f"Video file: {video_path}")
    print(f"Audio file: {audio_path}")
    print(f"Use fade-out: {use_fade_out}")
    print(f"API URL: {API_URL}")

    try:
        with open(video_path, 'rb') as video_file, open(audio_path, 'rb') as audio_file:
            files = {
                'video': (os.path.basename(video_path), video_file, 'video/mp4'),
                'audio': (os.path.basename(audio_path), audio_file, 'audio/mpeg')
            }
            data = {
                'use_fade_out': str(use_fade_out).lower()
            }

            response = requests.post(
                API_URL,
                files=files,
                data=data,
                auth=(USERNAME, PASSWORD)
            )

        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.json()}")

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"\n✓ Success! Video URL: {result.get('video_url')}")
                return True
            else:
                print(f"\n✗ API returned success=false: {result.get('message')}")
                return False
        else:
            print(f"\n✗ Request failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False

def main():
    """Main function to run the test."""
    if len(sys.argv) < 3:
        print("Usage: python test_audio_fade_out.py <video_path> <audio_path> [use_fade_out]")
        print("\nArguments:")
        print("  video_path    - Path to the video file")
        print("  audio_path    - Path to the audio file")
        print("  use_fade_out  - Optional: 'true' or 'false' (default: 'false')")
        print("\nExample:")
        print("  python test_audio_fade_out.py sample_video.mp4 sample_audio.mp3 true")
        sys.exit(1)

    video_path = sys.argv[1]
    audio_path = sys.argv[2]
    use_fade_out = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else False

    success = test_replace_video_audio_with_fadeout(video_path, audio_path, use_fade_out)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
