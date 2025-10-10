"""
Video utility functions for validating and probing video files
"""
import os
import ffmpeg
from typing import Dict, Any, Optional


class VideoProbeResult:
    """Structured result from video probe operation"""

    def __init__(self, probe_data: Dict[str, Any], file_path: str):
        self.file_path = file_path
        self.probe_data = probe_data
        self._parse_probe_data()

    def _parse_probe_data(self):
        """Parse probe data into structured attributes"""
        # Get video stream
        video_stream = next(
            (stream for stream in self.probe_data.get('streams', [])
             if stream.get('codec_type') == 'video'),
            None
        )

        if video_stream is None:
            raise ValueError(f"No video stream found in file: {self.file_path}")

        # Get audio streams
        audio_streams = [
            stream for stream in self.probe_data.get('streams', [])
            if stream.get('codec_type') == 'audio'
        ]

        # Extract format info
        format_info = self.probe_data.get('format', {})

        # Store parsed info
        self.video_stream = video_stream
        self.audio_streams = audio_streams
        self.format_info = format_info

        # Common attributes
        self.width = video_stream.get('width', 0)
        self.height = video_stream.get('height', 0)
        self.duration = float(format_info.get('duration', 0))
        self.codec_name = video_stream.get('codec_name', 'unknown')
        self.fps = self._parse_frame_rate(video_stream.get('r_frame_rate', '30/1'))
        self.has_audio = len(audio_streams) > 0
        self.bit_rate = int(format_info.get('bit_rate', 0))

    def _parse_frame_rate(self, frame_rate_str: str) -> float:
        """Safely parse frame rate string like '30/1' or '29.97'"""
        try:
            if '/' in frame_rate_str:
                numerator, denominator = frame_rate_str.split('/')
                return float(numerator) / float(denominator)
            else:
                return float(frame_rate_str)
        except (ValueError, ZeroDivisionError):
            return 30.0  # Default fallback

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy access"""
        return {
            'file': self.file_path,
            'width': self.width,
            'height': self.height,
            'duration': self.duration,
            'fps': self.fps,
            'has_audio': self.has_audio,
            'codec': self.codec_name,
            'bit_rate': self.bit_rate
        }


def validate_and_probe_video(video_file: str) -> VideoProbeResult:
    """
    Validate video file exists and probe its properties

    Args:
        video_file: Path to video file

    Returns:
        VideoProbeResult object with parsed video information

    Raises:
        ValueError: If file doesn't exist, is invalid, or cannot be probed
    """
    # Check if file exists
    if not os.path.exists(video_file):
        raise ValueError(f"Video file does not exist: {video_file}")

    if not os.path.isfile(video_file):
        raise ValueError(f"Path is not a file: {video_file}")

    # Probe the video file
    try:
        probe_data = ffmpeg.probe(video_file)
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise ValueError(f"Unable to probe video file '{video_file}': {error_msg}")
    except Exception as e:
        raise ValueError(f"Unable to probe video file '{video_file}': {str(e)}")

    # Validate probe result (ffmpeg-python may return empty dict for invalid files)
    if not isinstance(probe_data, dict) or not probe_data:
        raise ValueError(
            f"Invalid or empty probe result for file '{video_file}'. "
            f"The file may be corrupted or not a valid video file."
        )

    if 'streams' not in probe_data:
        raise ValueError(
            f"No streams found in video file '{video_file}'. "
            f"The file may be corrupted or not a valid video file."
        )

    if 'format' not in probe_data:
        raise ValueError(
            f"No format info found in video file '{video_file}'. "
            f"The file may be corrupted or not a valid video file."
        )

    # Return structured result
    return VideoProbeResult(probe_data, video_file)


def probe_video_safe(video_file: str) -> Optional[VideoProbeResult]:
    """
    Safe version that returns None instead of raising exceptions

    Args:
        video_file: Path to video file

    Returns:
        VideoProbeResult object or None if probe fails
    """
    try:
        return validate_and_probe_video(video_file)
    except (ValueError, Exception):
        return None
