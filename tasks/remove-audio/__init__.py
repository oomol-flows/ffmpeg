#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    output_format: typing.Literal["mp4", "avi", "mov", "mkv", "webm"]
class Outputs(typing.TypedDict):
    output_video: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Remove audio track from video file

    Args:
        params: Input parameters containing video file and output format
        context: OOMOL context object

    Returns:
        Output video file path without audio
    """
    video_file = params["video_file"]
    output_format = params["output_format"]

    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = os.path.join(context.session_dir, f"{base_name}_no_audio.{output_format}")

    try:
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(video_file)

        # Create output stream without audio (-an flag removes audio)
        # Use copy for video to avoid re-encoding
        output_stream = ffmpeg.output(
            input_stream,
            output_file,
            vcodec='copy',  # Copy video stream without re-encoding
            an=None  # Remove audio stream
        )

        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

        return {"output_video": output_file}

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise ValueError(f"FFmpeg error during audio removal: {error_msg}")
    except Exception as e:
        raise ValueError(f"Error removing audio from video: {str(e)}")
