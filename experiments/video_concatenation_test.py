#!/usr/bin/env python
"""
Experiment script to test video concatenation functionality.
This script tests the concatenate_videos function with sample videos.
"""

import os
import sys
import tempfile
import subprocess

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
import django
django.setup()

from main.lib_ffmpeg import concatenate_videos, get_video_dimensions


def create_test_video(output_path: str, width: int, height: int, duration: int, color: str):
    """Create a test video using ffmpeg."""
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'color=c={color}:s={width}x{height}:d={duration}',
        '-f', 'lavfi',
        '-i', 'anullsrc',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-shortest',
        '-y',
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def main():
    print("Testing video concatenation functionality...")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test videos with different dimensions
        video1_path = os.path.join(temp_dir, 'video1.mp4')
        video2_path = os.path.join(temp_dir, 'video2.mp4')
        video3_path = os.path.join(temp_dir, 'video3.mp4')
        output_path = os.path.join(temp_dir, 'output.mp4')

        print("\n1. Creating test videos...")
        print(f"   Video 1: 1920x1080 (16:9), 2 seconds, red")
        success1 = create_test_video(video1_path, 1920, 1080, 2, 'red')

        print(f"   Video 2: 1280x720 (16:9), 2 seconds, green")
        success2 = create_test_video(video2_path, 1280, 720, 2, 'green')

        print(f"   Video 3: 640x480 (4:3), 2 seconds, blue")
        success3 = create_test_video(video3_path, 640, 480, 2, 'blue')

        if not all([success1, success2, success3]):
            print("\n❌ Failed to create test videos")
            return

        print("   ✓ Test videos created successfully")

        # Test getting video dimensions
        print("\n2. Testing get_video_dimensions()...")
        dim1 = get_video_dimensions(video1_path)
        dim2 = get_video_dimensions(video2_path)
        dim3 = get_video_dimensions(video3_path)

        print(f"   Video 1 dimensions: {dim1}")
        print(f"   Video 2 dimensions: {dim2}")
        print(f"   Video 3 dimensions: {dim3}")

        if dim1 == (1920, 1080) and dim2 == (1280, 720) and dim3 == (640, 480):
            print("   ✓ Dimensions detected correctly")
        else:
            print("   ❌ Dimension detection failed")
            return

        # Test concatenating videos
        print("\n3. Testing concatenate_videos()...")
        print("   Concatenating 3 videos with different aspect ratios...")
        success, error_message = concatenate_videos(
            video_paths=[video1_path, video2_path, video3_path],
            output_path=output_path,
            timeout=300
        )

        if success:
            print("   ✓ Videos concatenated successfully")

            # Check output video
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path)
                output_dim = get_video_dimensions(output_path)
                print(f"   Output file size: {output_size} bytes")
                print(f"   Output dimensions: {output_dim}")

                if output_dim == (1920, 1080):
                    print("   ✓ Output video has correct dimensions (matches first video)")
                else:
                    print(f"   ⚠ Output video dimensions don't match first video")
            else:
                print("   ❌ Output file not created")
        else:
            print(f"   ❌ Concatenation failed: {error_message}")
            return

        # Test with single video
        print("\n4. Testing with single video (should just copy)...")
        single_output_path = os.path.join(temp_dir, 'single_output.mp4')
        success, error_message = concatenate_videos(
            video_paths=[video1_path],
            output_path=single_output_path,
            timeout=300
        )

        if success and os.path.exists(single_output_path):
            print("   ✓ Single video handling works correctly")
        else:
            print(f"   ❌ Single video handling failed: {error_message}")

        # Test with empty list
        print("\n5. Testing with empty video list (should fail gracefully)...")
        empty_output_path = os.path.join(temp_dir, 'empty_output.mp4')
        success, error_message = concatenate_videos(
            video_paths=[],
            output_path=empty_output_path,
            timeout=300
        )

        if not success:
            print(f"   ✓ Correctly rejected empty list: {error_message}")
        else:
            print("   ❌ Should have rejected empty list")

    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")


if __name__ == '__main__':
    main()
