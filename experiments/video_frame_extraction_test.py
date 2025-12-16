#!/usr/bin/env python
"""
Experiment script to test FFmpeg video frame extraction functionality.

This script demonstrates how to extract frames from a video using FFmpeg.
It shows the commands used in the extract_video_frame API endpoint.

Requirements:
- FFmpeg installed at /usr/bin/ffmpeg
- A test video file

Usage:
    python experiments/video_frame_extraction_test.py /path/to/video.mp4

FFmpeg commands used:

1. Extract frame at specific second (e.g., second 5):
   /usr/bin/ffmpeg -ss 5 -i video.mp4 -vframes 1 -q:v 2 -y output.jpg

2. Extract last frame (method 1 - calculate duration):
   # First get duration:
   /usr/bin/ffmpeg -i video.mp4 -hide_banner

   # Then extract frame near the end:
   /usr/bin/ffmpeg -ss {duration-0.1} -i video.mp4 -vframes 1 -q:v 2 -y output.jpg

3. Extract last frame (method 2 - seek from end):
   /usr/bin/ffmpeg -sseof -0.1 -i video.mp4 -update 1 -q:v 2 -y output.jpg

Quality parameter explanation:
- -q:v 2: High quality JPEG (scale 2-31, lower is better)
- Value 2 provides near-lossless quality with minimal compression

Output format:
- JPG format with high quality (minimal compression)
- Quality setting ensures good visual quality
"""

import subprocess
import sys
import os

def extract_frame_at_second(video_path, second, output_path):
    """Extract a frame from video at specified second."""
    cmd = [
        '/usr/bin/ffmpeg',
        '-ss', str(second),
        '-i', video_path,
        '-vframes', '1',
        '-q:v', '2',  # High quality JPG
        '-y',
        output_path
    ]

    print(f"Extracting frame at second {second}...")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✓ Frame extracted successfully to {output_path}")
    else:
        print(f"✗ Error: {result.stderr}")

    return result.returncode == 0


def get_video_duration(video_path):
    """Get video duration in seconds."""
    cmd = [
        '/usr/bin/ffmpeg',
        '-i', video_path,
        '-hide_banner'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse duration from ffmpeg output
    for line in result.stderr.split('\n'):
        if 'Duration:' in line:
            duration_str = line.split('Duration:')[1].split(',')[0].strip()
            time_parts = duration_str.split(':')
            duration_seconds = float(time_parts[0]) * 3600 + float(time_parts[1]) * 60 + float(time_parts[2])
            return duration_seconds

    return None


def extract_last_frame(video_path, output_path):
    """Extract the last frame from video."""
    duration = get_video_duration(video_path)

    if duration:
        # Seek to slightly before the end
        seek_time = max(0, duration - 0.1)
        print(f"Video duration: {duration:.2f}s, seeking to {seek_time:.2f}s")

        cmd = [
            '/usr/bin/ffmpeg',
            '-ss', str(seek_time),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            output_path
        ]
    else:
        # Alternative: use sseof to seek from end
        print("Using alternative method (sseof)")
        cmd = [
            '/usr/bin/ffmpeg',
            '-sseof', '-0.1',
            '-i', video_path,
            '-update', '1',
            '-q:v', '2',
            '-y',
            output_path
        ]

    print(f"Extracting last frame...")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✓ Last frame extracted successfully to {output_path}")
    else:
        print(f"✗ Error: {result.stderr}")

    return result.returncode == 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python video_frame_extraction_test.py /path/to/video.mp4")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    # Test 1: Extract frame at second 0 (first frame)
    print("\n" + "="*60)
    print("Test 1: Extract first frame (second 0)")
    print("="*60)
    extract_frame_at_second(video_path, 0, 'frame_at_0s.jpg')

    # Test 2: Extract frame at second 5
    print("\n" + "="*60)
    print("Test 2: Extract frame at second 5")
    print("="*60)
    extract_frame_at_second(video_path, 5, 'frame_at_5s.jpg')

    # Test 3: Extract last frame
    print("\n" + "="*60)
    print("Test 3: Extract last frame")
    print("="*60)
    extract_last_frame(video_path, 'frame_last.jpg')

    print("\n" + "="*60)
    print("Tests completed!")
    print("="*60)
