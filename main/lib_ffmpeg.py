import os
import subprocess
import tempfile
import logging
from typing import Tuple, Optional

logger = logging.getLogger('django')

FFMPEG_PATH = '/usr/bin/ffmpeg'


def get_video_duration(video_path: str, timeout: int = 30) -> Optional[float]:
    """
    Get video duration in seconds using ffmpeg.

    Args:
        video_path: Path to the video file
        timeout: Timeout in seconds for the ffmpeg command

    Returns:
        Video duration in seconds, or None if unable to determine
    """
    probe_cmd = [
        FFMPEG_PATH,
        '-i', video_path,
        '-hide_banner'
    ]

    try:
        probe_result = subprocess.run(
            probe_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Parse duration from ffmpeg output
        for line in probe_result.stderr.split('\n'):
            if 'Duration:' in line:
                duration_str = line.split('Duration:')[1].split(',')[0].strip()
                # Convert duration to seconds
                time_parts = duration_str.split(':')
                duration = float(time_parts[0]) * 3600 + float(time_parts[1]) * 60 + float(time_parts[2])
                return duration

        return None

    except (subprocess.TimeoutExpired, Exception) as e:
        logger.error(f'Error getting video duration: {str(e)}')
        return None


def extract_frame_from_video(
    video_path: str,
    output_path: str,
    second: float = 0,
    is_last: bool = False,
    quality: int = 2,
    timeout: int = 60
) -> Tuple[bool, Optional[str]]:
    """
    Extract a frame from a video file at a specified time or the last frame.

    Args:
        video_path: Path to the input video file
        output_path: Path where the extracted frame should be saved
        second: Time in seconds from which to extract the frame (default: 0)
        is_last: If True, extract the last frame instead of frame at 'second'
        quality: JPEG quality for the output (2-5, lower is better, default: 2)
        timeout: Timeout in seconds for the ffmpeg command

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        if is_last:
            # Get video duration to extract the last frame
            duration = get_video_duration(video_path, timeout=30)

            if duration is not None:
                # Seek to a moment slightly before the end to ensure we get a frame
                seek_time = max(0, duration - 0.1)
                cmd = [
                    FFMPEG_PATH,
                    '-ss', str(seek_time),
                    '-i', video_path,
                    '-vframes', '1',
                    '-q:v', str(quality),
                    '-y',
                    output_path
                ]
            else:
                # Alternative: use sseof to seek from end
                cmd = [
                    FFMPEG_PATH,
                    '-sseof', '-0.1',
                    '-i', video_path,
                    '-update', '1',
                    '-q:v', str(quality),
                    '-y',
                    output_path
                ]
        else:
            # Extract frame at specified second
            cmd = [
                FFMPEG_PATH,
                '-ss', str(second),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', str(quality),
                '-y',
                output_path
            ]

        # Execute ffmpeg command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            logger.error(f'FFmpeg error: {result.stderr}')
            return False, 'Failed to extract frame from video.'

        # Check if output file was created
        if not os.path.exists(output_path):
            return False, 'Frame extraction failed.'

        return True, None

    except subprocess.TimeoutExpired:
        return False, 'Video processing timeout.'
    except Exception as e:
        logger.error(f'Error extracting video frame: {str(e)}')
        return False, f'Error: {str(e)}'


def replace_audio_in_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    use_fade_out: bool = False,
    fade_duration: float = 3.0,
    audio_bitrate: str = '192k',
    timeout: int = 180
) -> Tuple[bool, Optional[str]]:
    """
    Replace or add audio track to a video file.

    Args:
        video_path: Path to the input video file
        audio_path: Path to the audio file to add/replace
        output_path: Path where the output video should be saved
        use_fade_out: If True and audio is longer than video, apply fade-out to audio
        fade_duration: Duration of fade-out in seconds (default: 3.0)
        audio_bitrate: Audio bitrate for output (default: '192k')
        timeout: Timeout in seconds for the ffmpeg command

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        # Get video and audio durations
        video_duration = get_video_duration(video_path, timeout=30)
        audio_duration = get_video_duration(audio_path, timeout=30)

        # Check if we need to apply fade-out
        apply_fade_out = (
            use_fade_out and
            audio_duration is not None and
            video_duration is not None and
            audio_duration > video_duration
        )

        if apply_fade_out:
            # Calculate fade-out start time
            fade_start = max(0, video_duration - fade_duration)

            # Build command with audio fade-out filter
            cmd = [
                FFMPEG_PATH,
                '-i', video_path,
                '-i', audio_path,
                '-map', '0:v',  # Map video from first input
                '-map', '1:a',  # Map audio from second input
                '-c:v', 'copy',  # Copy video codec (no re-encoding)
                '-c:a', 'aac',   # Encode audio to AAC
                '-b:a', audio_bitrate,
                '-af', f'afade=t=out:st={fade_start}:d={fade_duration}',
                '-shortest',     # Use shortest duration
                '-y',
                output_path
            ]
        else:
            # Build standard command without fade-out
            cmd = [
                FFMPEG_PATH,
                '-i', video_path,
                '-i', audio_path,
                '-map', '0:v',
                '-map', '1:a',
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', audio_bitrate,
                '-shortest',
                '-y',
                output_path
            ]

        # Execute ffmpeg command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            logger.error(f'FFmpeg error: {result.stderr}')
            return False, 'Failed to replace audio in video.'

        # Check if output file was created
        if not os.path.exists(output_path):
            return False, 'Video processing failed.'

        return True, None

    except subprocess.TimeoutExpired:
        return False, 'Video processing timeout.'
    except Exception as e:
        logger.error(f'Error replacing video audio: {str(e)}')
        return False, f'Error: {str(e)}'


def trim_video_segment(
    video_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    timeout: int = 180
) -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Trim a video file to extract a segment between start and end times.

    Args:
        video_path: Path to the input video file
        output_path: Path where the trimmed video should be saved
        start_time: Start time in seconds
        end_time: End time in seconds
        timeout: Timeout in seconds for the ffmpeg command

    Returns:
        Tuple of (success: bool, error_message: Optional[str], video_duration: Optional[float])
    """
    try:
        # Validate parameters
        if start_time < 0:
            return False, 'Start time must be non-negative.', None

        if end_time <= start_time:
            return False, 'End time must be greater than start time.', None

        # Get video duration to validate parameters
        video_duration = get_video_duration(video_path, timeout=30)

        if video_duration is None:
            return False, 'Could not determine video duration.', None

        if end_time > video_duration:
            return False, f'End time ({end_time}) exceeds video duration ({video_duration:.2f} seconds).', video_duration

        # Calculate trim duration
        trim_duration = end_time - start_time

        # Build ffmpeg command to trim video
        cmd = [
            FFMPEG_PATH,
            '-ss', str(start_time),
            '-i', video_path,
            '-t', str(trim_duration),
            '-c', 'copy',  # Copy codec without re-encoding
            '-y',
            output_path
        ]

        # Execute ffmpeg command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            logger.error(f'FFmpeg error: {result.stderr}')
            return False, 'Failed to trim video.', video_duration

        # Check if output file was created
        if not os.path.exists(output_path):
            return False, 'Video trimming failed.', video_duration

        return True, None, video_duration

    except subprocess.TimeoutExpired:
        return False, 'Video processing timeout.', None
    except Exception as e:
        logger.error(f'Error trimming video: {str(e)}')
        return False, f'Error: {str(e)}', None


def save_uploaded_file_to_temp(uploaded_file, suffix: str = '') -> str:
    """
    Save an uploaded file to a temporary location.

    Args:
        uploaded_file: Django TemporaryUploadedFile object
        suffix: File extension suffix (e.g., '.mp4', '.mp3')

    Returns:
        Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        return temp_file.name
