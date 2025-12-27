#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_files: list[str]
    output_path: str
    codec: typing.Literal["libx264", "libx265", "mpeg4", "copy"] | None
    audio_codec: typing.Literal["aac", "mp3", "copy"] | None
    crf: int | None
    preset: typing.Literal["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"] | None
class Outputs(typing.TypedDict):
    output_file: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os


def main(params: Inputs, context: Context) -> Outputs:
    """
    Merge multiple video files into a single video file.

    This function uses FFmpeg to concatenate videos sequentially.

    Args:
        params: Input parameters containing video files and output settings
        context: OOMOL context object

    Returns:
        Output merged video file path
    """
    video_files = params["video_files"]
    output_path = params["output_path"]

    # Validate inputs
    if not video_files or len(video_files) < 2:
        raise ValueError("At least 2 video files are required for merging")

    # Check if all input files exist
    for video_file in video_files:
        if not os.path.exists(video_file):
            raise FileNotFoundError(f"Video file not found: {video_file}")

    # Get optional parameters
    codec = params.get("codec") or "libx264"
    audio_codec = params.get("audio_codec") or "aac"
    crf = params.get("crf")
    if crf is None:
        crf = 23
    preset = params.get("preset") or "medium"

    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_files[0]))[0]
    if not output_path:
        output_path = f"/oomol-driver/oomol-storage/{base_name}_merged.mp4"

    try:
        # Report initial progress
        context.report_progress(10)

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        context.report_progress(20)

        # Create input streams
        input_streams = [ffmpeg.input(video_file) for video_file in video_files]

        context.report_progress(40)

        # Concatenate using filter_complex
        # Each input needs both video and audio streams
        inputs = []
        for stream in input_streams:
            inputs.append(stream['v'])
            inputs.append(stream['a'])

        # Use concat filter with n=number of videos, v=1 video stream, a=1 audio stream
        joined = ffmpeg.concat(*inputs, n=len(video_files), v=1, a=1).node

        context.report_progress(50)

        # Build output options
        output_options = {
            'vcodec': codec if codec != "copy" else "libx264",
            'acodec': audio_codec if audio_codec != "copy" else "aac"
        }

        if codec != "copy":
            output_options['crf'] = str(crf)
            output_options['preset'] = preset

        # Create output stream - concat returns multiple outputs [v][a]
        output_stream = ffmpeg.output(joined[0], joined[1], output_path, **output_options)

        # Run FFmpeg command
        context.report_progress(60)
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

        context.report_progress(100)

        return {"output_file": output_path}

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during video merging: {error_msg}")
    except Exception as e:
        raise Exception(f"Error merging videos: {str(e)}")
