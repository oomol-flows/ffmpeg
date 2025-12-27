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
    codec = params.get("codec", "libx264")
    audio_codec = params.get("audio_codec", "aac")
    crf = params.get("crf", 23)
    preset = params.get("preset", "medium")

    try:
        # Report initial progress
        context.report_progress(10)

        # Create input streams for all videos
        input_streams = [ffmpeg.input(video_file) for video_file in video_files]

        # Prepare video and audio streams for concatenation
        video_streams = [stream.video for stream in input_streams]
        audio_streams = [stream.audio for stream in input_streams]

        context.report_progress(30)

        # Concatenate video and audio streams
        joined_video = ffmpeg.concat(*video_streams, v=1, a=0).node
        joined_audio = ffmpeg.concat(*audio_streams, v=0, a=1).node

        context.report_progress(50)

        # Build output options
        output_kwargs = {}

        if codec == "copy":
            output_kwargs['vcodec'] = 'copy'
        else:
            output_kwargs['vcodec'] = codec
            output_kwargs['crf'] = str(crf)
            output_kwargs['preset'] = preset

        if audio_codec == "copy":
            output_kwargs['acodec'] = 'copy'
        else:
            output_kwargs['acodec'] = audio_codec

        context.report_progress(60)

        # Create output with both video and audio
        output = ffmpeg.output(
            joined_video[0],
            joined_audio[0],
            output_path,
            **output_kwargs
        )

        # Run FFmpeg command
        ffmpeg.run(output, overwrite_output=True, quiet=True)

        context.report_progress(90)

        # Verify output file was created
        if not os.path.exists(output_path):
            raise RuntimeError("Failed to create merged video file")

        context.report_progress(100)

        return {"output_file": output_path}

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during video merging: {error_msg}")
    except Exception as e:
        raise Exception(f"Error merging videos: {str(e)}")
