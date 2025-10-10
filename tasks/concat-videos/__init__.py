#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_files: list[str]
    concat_method: typing.Literal["filter", "demuxer"]
    audio_handling: typing.Literal["first_only", "mix_all", "keep_all", "silence"]
    resolution_handling: typing.Literal["auto", "match_first", "custom"]
    custom_width: float | None
    custom_height: float | None
    transition_duration: float
class Outputs(typing.TypedDict):
    concatenated_video: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os
import tempfile
from typing import List, Dict, Any
from utils.video_utils import validate_and_probe_video, VideoProbeResult
from utils.ffmpeg_encoder import create_encoder

def main(params: Inputs, context: Context) -> Outputs:
    """
    Concatenate multiple video files into a single output video

    Args:
        params: Input parameters containing video files list and concatenation settings
        context: OOMOL context object

    Returns:
        Output concatenated video file
    """
    video_files = params["video_files"]
    concat_method = params["concat_method"]
    audio_handling = params["audio_handling"]
    resolution_handling = params["resolution_handling"]
    custom_width = params.get("custom_width")
    custom_height = params.get("custom_height")
    transition_duration = params["transition_duration"]

    if len(video_files) < 2:
        raise ValueError("At least 2 video files are required for concatenation")

    # Generate output filename
    base_name = "concatenated_video"
    output_file = f"/oomol-driver/oomol-storage/{base_name}.mp4"

    try:
        # Validate and probe all video files using utility function
        probe_results = []
        for video_file in video_files:
            probe_result = validate_and_probe_video(video_file)
            probe_results.append(probe_result)

        # Convert probe results to info dicts
        video_info = [probe.to_dict() for probe in probe_results]

        # Determine target resolution
        if resolution_handling == "match_first":
            target_width = video_info[0]['width']
            target_height = video_info[0]['height']
        elif resolution_handling == "custom":
            # Convert float to int safely
            target_width = int(custom_width) if custom_width else 1920
            target_height = int(custom_height) if custom_height else 1080
        else:  # auto - use the most common resolution or the first one
            target_width = video_info[0]['width']
            target_height = video_info[0]['height']

        # Use filter method for concatenation
        if concat_method == "filter":
            return _concatenate_with_filter(
                video_info, target_width, target_height,
                audio_handling, output_file, context
            )
        else:  # demuxer method
            return _concatenate_with_demuxer(
                video_info, audio_handling, output_file
            )

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during video concatenation: {error_msg}")
    except Exception as e:
        raise Exception(f"Error concatenating videos: {str(e)}")

def _create_final_audio(
    audio_handling: str,
    audio_streams: List,
    video_info: List[Dict[str, Any]]
):
    """Create final audio stream based on handling mode"""
    total_duration = sum(info['duration'] for info in video_info)

    if audio_handling == "silence":
        # Create silent audio for the entire duration
        return ffmpeg.input('anullsrc', f='lavfi', t=total_duration).audio
    elif audio_handling == "first_only" and audio_streams:
        return audio_streams[0]
    elif audio_handling == "mix_all" and len(audio_streams) > 1:
        return ffmpeg.filter(audio_streams, 'amix', inputs=len(audio_streams))
    elif audio_handling == "keep_all" and len(audio_streams) > 1:
        return ffmpeg.filter(audio_streams, 'concat', n=len(audio_streams), v=0, a=1)
    elif audio_streams:
        return audio_streams[0]
    else:
        # No audio available, create silent audio
        return ffmpeg.input('anullsrc', f='lavfi', t=total_duration).audio


def _concatenate_with_filter(
    video_info: List[Dict[str, Any]],
    target_width: int,
    target_height: int,
    audio_handling: str,
    output_file: str,
    context: Context
) -> Outputs:
    """Concatenate videos using FFmpeg filter method with GPU acceleration"""

    # Create GPU-optimized encoder
    encoder = create_encoder(context)

    # Create input streams and scale if necessary
    video_streams = []
    audio_streams = []

    for info in video_info:
        input_stream = ffmpeg.input(info['file'])

        # Scale video to target resolution if needed
        if info['width'] != target_width or info['height'] != target_height:
            video_stream = input_stream.video.filter('scale', target_width, target_height)
        else:
            video_stream = input_stream.video

        video_streams.append(video_stream)

        # Handle audio streams
        if info['has_audio'] and audio_handling != "silence":
            audio_streams.append(input_stream.audio)

    # Concatenate video streams
    if len(video_streams) == 1:
        final_video = video_streams[0]
    else:
        final_video = ffmpeg.filter(video_streams, 'concat', n=len(video_streams), v=1, a=0)

    # Create final audio stream
    final_audio = _create_final_audio(audio_handling, audio_streams, video_info)

    # Get GPU-optimized encoding options
    encoding_options = encoder.get_encoding_options(codec_type="h264", profile="balanced")

    # Create final output with GPU-optimized settings
    output_stream = ffmpeg.output(
        final_video,
        final_audio,
        output_file,
        **encoding_options
    )

    # Run FFmpeg command
    ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

    return {"concatenated_video": output_file}

def _concatenate_with_demuxer(
    video_info: List[Dict[str, Any]],
    audio_handling: str,
    output_file: str
) -> Outputs:
    """Concatenate videos using FFmpeg demuxer method (requires same format/codec)"""

    # Create temporary concat file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for info in video_info:
            f.write(f"file '{info['file']}'\n")
        concat_file = f.name

    try:
        # Use concat demuxer
        input_stream = ffmpeg.input(concat_file, format='concat', safe=0)

        if audio_handling == "silence":
            # Remove audio and add silent track
            # Reuse already probed duration info
            total_duration = sum(info['duration'] for info in video_info)

            silent_audio = ffmpeg.input('anullsrc', f='lavfi', t=total_duration).audio
            output_stream = ffmpeg.output(
                input_stream.video,
                silent_audio,
                output_file,
                vcodec='copy',  # Copy video without re-encoding
                acodec='aac'
            )
        else:
            # Keep original audio handling (copy everything)
            output_stream = ffmpeg.output(
                input_stream,
                output_file,
                c='copy'  # Copy without re-encoding for speed
            )

        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

    finally:
        # Clean up temporary file
        if os.path.exists(concat_file):
            os.unlink(concat_file)

    return {"concatenated_video": output_file}

