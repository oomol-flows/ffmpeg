#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    subtitle_file: str
    subtitle_language: str | None
    subtitle_title: str | None
class Outputs(typing.TypedDict):
    output_video: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Mux SRT subtitle file with video file without re-encoding.
    The subtitle is added as an external subtitle track in MKV container.

    Args:
        params: Input parameters containing video file, subtitle file and metadata
        context: OOMOL context object

    Returns:
        Output MKV video with muxed subtitle track
    """
    video_file = params["video_file"]
    subtitle_file = params["subtitle_file"]
    subtitle_language = params.get("subtitle_language")
    subtitle_title = params.get("subtitle_title")

    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = os.path.join(context.session_dir, f"{base_name}_with_subtitle.mkv")

    try:
        # Create input streams
        video_input = ffmpeg.input(video_file)
        subtitle_input = ffmpeg.input(subtitle_file)

        # Build metadata for subtitle track
        subtitle_metadata = {}

        # Add subtitle language if provided
        if subtitle_language:
            subtitle_metadata[f'metadata:s:s:0'] = f'language={subtitle_language}'

        # Add subtitle title if provided
        if subtitle_title:
            if subtitle_language:
                subtitle_metadata[f'metadata:s:s:0'] = f'language={subtitle_language},title={subtitle_title}'
            else:
                subtitle_metadata[f'metadata:s:s:0'] = f'title={subtitle_title}'

        # Mux video, audio and subtitle without re-encoding
        # Use -c copy to avoid re-encoding
        output_stream = ffmpeg.output(
            video_input.video,
            video_input.audio,
            subtitle_input,
            output_file,
            vcodec='copy',      # Copy video codec (no re-encoding)
            acodec='copy',      # Copy audio codec (no re-encoding)
            scodec='srt',       # Subtitle codec
            **subtitle_metadata
        )

        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

        return {"output_video": output_file}

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise ValueError(f"FFmpeg error during muxing: {error_msg}")
    except Exception as e:
        raise ValueError(f"Error muxing video and subtitle: {str(e)}")
