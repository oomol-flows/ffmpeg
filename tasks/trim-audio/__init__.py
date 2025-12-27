#region generated meta
import typing
class Inputs(typing.TypedDict):
    audio_file: str
    start_time: float
    duration: float
    output_format: typing.Literal["mp3", "wav", "aac", "flac", "ogg"] | None
class Outputs(typing.TypedDict):
    trimmed_audio: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Trim audio to specific time segment
    
    Args:
        params: Input parameters containing audio file, start time, duration, and output format
        context: OOMOL context object
        
    Returns:
        Output trimmed audio file path
    """
    audio_file = params["audio_file"]
    start_time = params["start_time"]
    duration = params["duration"]
    output_format = params["output_format"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    output_file = os.path.join(context.session_dir, f"{base_name}_trimmed.{output_format}")
    
    try:
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(audio_file)
        
        # Configure trim options
        trim_options = {
            'ss': start_time,  # Start time
            'acodec': _get_audio_codec(output_format)
        }
        
        # Add duration if specified (0 means to end of audio)
        if duration > 0:
            trim_options['t'] = duration
            
        # Create output stream
        output_stream = ffmpeg.output(input_stream, output_file, **trim_options)
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"trimmed_audio": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during audio trimming: {error_msg}")
    except Exception as e:
        raise Exception(f"Error trimming audio: {str(e)}")

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