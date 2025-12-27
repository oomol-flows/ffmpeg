#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    output_format: typing.Literal["mp3", "wav", "aac", "flac", "ogg"]
    audio_quality: float
class Outputs(typing.TypedDict):
    audio_file: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Extract audio from video file
    
    Args:
        params: Input parameters containing video file path, output format, and quality
        context: OOMOL context object
        
    Returns:
        Output audio file path
    """
    video_file = params["video_file"]
    output_format = params["output_format"]
    audio_quality = params["audio_quality"]

    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = os.path.join(context.session_dir, f"{base_name}_audio.{output_format}")

    try:
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(video_file)

        # Configure audio output options
        audio_options = {
            'acodec': _get_audio_codec(output_format),
            'audio_bitrate': f'{audio_quality}k'
        }

        # Create output stream
        output_stream = ffmpeg.output(input_stream, output_file, **audio_options)

        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"audio_file": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during audio extraction: {error_msg}")
    except Exception as e:
        raise Exception(f"Error extracting audio: {str(e)}")

def _get_audio_codec(format_name: str) -> str:
    """Get appropriate audio codec for the output format"""
    codec_map = {
        'mp3': 'libmp3lame',
        'wav': 'pcm_s16le', 
        'aac': 'aac',
        'flac': 'flac',
        'ogg': 'libvorbis'
    }
    return codec_map.get(format_name, 'libmp3lame')