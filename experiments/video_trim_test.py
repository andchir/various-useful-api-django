#!/usr/bin/env python
"""
Experiment script to test FFmpeg video trimming functionality.

This script demonstrates how to trim videos using FFmpeg.
It shows the commands used in the trim_video API endpoint.

Requirements:
- FFmpeg installed at /usr/bin/ffmpeg
- A test video file

Usage:
    python experiments/video_trim_test.py /path/to/video.mp4

FFmpeg commands used:

1. Trim video from second_start to second_end (with codec copy for speed):
   /usr/bin/ffmpeg -ss {second_start} -i video.mp4 -t {duration} -c copy -y output.mp4

   Where:
   - -ss: Start time in seconds
   - -t: Duration of the output (second_end - second_start)
   - -c copy: Copy codec without re-encoding (fast but keyframe-dependent)
   - -y: Overwrite output file without asking

2. Get video duration:
   /usr/bin/ffmpeg -i video.mp4 -hide_banner
   (Parse Duration from stderr output)

Quality and performance:
- Using -c copy avoids re-encoding, making the process very fast
- Output quality is identical to source since no re-encoding occurs
- Trim points may snap to nearest keyframe (usually acceptable)
- For frame-accurate cuts, use -c:v libx264 instead (slower but precise)

Output format:
- MP4 container format
- Same codecs as input (no re-encoding)
- Maximum input file size: 100 MB
"""

import subprocess
import sys
import os


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


def trim_video(video_path, second_start, second_end, output_path):
    """
    Trim video from second_start to second_end.

    Args:
        video_path: Path to input video file
        second_start: Start time in seconds
        second_end: End time in seconds
        output_path: Path for output trimmed video

    Returns:
        True if successful, False otherwise
    """
    # Validate parameters
    if second_start < 0:
        print(f"✗ Error: second_start must be non-negative")
        return False

    if second_end <= second_start:
        print(f"✗ Error: second_end must be greater than second_start")
        return False

    # Get video duration
    duration = get_video_duration(video_path)
    if duration is None:
        print(f"✗ Error: Could not determine video duration")
        return False

    print(f"Video duration: {duration:.2f}s")

    if second_end > duration:
        print(f"✗ Error: second_end ({second_end}) exceeds video duration ({duration:.2f}s)")
        return False

    # Calculate trim duration
    trim_duration = second_end - second_start

    print(f"Trimming from {second_start}s to {second_end}s (duration: {trim_duration}s)")

    # Build ffmpeg command
    cmd = [
        '/usr/bin/ffmpeg',
        '-ss', str(second_start),
        '-i', video_path,
        '-t', str(trim_duration),
        '-c', 'copy',  # Copy codec without re-encoding
        '-y',
        output_path
    ]

    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✓ Video trimmed successfully to {output_path}")
        # Check output file size
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  Output file size: {size_mb:.2f} MB")
        return True
    else:
        print(f"✗ Error: {result.stderr}")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python video_trim_test.py /path/to/video.mp4")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    # Get video duration first
    duration = get_video_duration(video_path)
    if duration is None:
        print("Error: Could not determine video duration")
        sys.exit(1)

    print(f"Input video: {video_path}")
    print(f"Total duration: {duration:.2f}s")

    # Check file size
    size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"File size: {size_mb:.2f} MB")

    if size_mb > 100:
        print("Warning: File size exceeds 100 MB limit for API")

    # Test 1: Trim first 10 seconds
    print("\n" + "="*60)
    print("Test 1: Trim first 10 seconds (0s to 10s)")
    print("="*60)
    trim_end = min(10, duration)
    trim_video(video_path, 0, trim_end, 'trimmed_0_to_10s.mp4')

    # Test 2: Trim middle section (if video is long enough)
    if duration > 20:
        print("\n" + "="*60)
        print("Test 2: Trim middle 10 seconds (10s to 20s)")
        print("="*60)
        trim_video(video_path, 10, 20, 'trimmed_10_to_20s.mp4')

    # Test 3: Trim last 5 seconds
    if duration > 5:
        print("\n" + "="*60)
        print("Test 3: Trim last 5 seconds")
        print("="*60)
        start = max(0, duration - 5)
        trim_video(video_path, start, duration, 'trimmed_last_5s.mp4')

    print("\n" + "="*60)
    print("Tests completed!")
    print("="*60)
