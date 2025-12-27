#region generated meta
import typing
class Inputs(typing.TypedDict):
    audio_file: str
    output_format: typing.Literal["mp3", "wav", "aac", "flac", "ogg", "m4a"]
    audio_quality: float | None
    sample_rate: typing.Literal[0, 8000, 16000, 22050, 44100, 48000, 96000] | None
    channels: typing.Literal[0, 1, 2] | None
class Outputs(typing.TypedDict):
    converted_audio: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Convert audio to different format with quality control
    
    Args:
        params: Input parameters containing audio file and conversion settings
        context: OOMOL context object
        
    Returns:
        Output converted audio file path
    """
    audio_file = params["audio_file"]
    output_format = params["output_format"]
    audio_quality = params["audio_quality"]
    sample_rate = params["sample_rate"]
    channels = params["channels"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    output_file = os.path.join(context.session_dir, f"{base_name}_converted.{output_format}")
    
    try:
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(audio_file)
        
        # Configure conversion options
        conversion_options = {
            'acodec': _get_audio_codec(output_format)
        }
        
        # Set quality/bitrate (not applicable for lossless formats)
        if output_format not in ['wav', 'flac']:
            conversion_options['audio_bitrate'] = f'{audio_quality}k'
        
        # Set sample rate if specified
        if sample_rate > 0:
            conversion_options['ar'] = sample_rate
            
        # Set channels if specified
        if channels > 0:
            conversion_options['ac'] = channels
        
        # Special handling for different formats
        if output_format == 'flac':
            # FLAC specific options
            conversion_options['compression_level'] = 5
        elif output_format == 'wav':
            # WAV specific options
            conversion_options['acodec'] = 'pcm_s16le'
            
        # Create output stream
        output_stream = ffmpeg.output(input_stream, output_file, **conversion_options)
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"converted_audio": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during audio conversion: {error_msg}")
    except Exception as e:
        raise Exception(f"Error converting audio: {str(e)}")

def _get_audio_codec(format_name: str) -> str:
    """Get appropriate audio codec for the output format"""
    codec_map = {
        'mp3': 'libmp3lame',
        'wav': 'pcm_s16le', 
        'aac': 'aac',
        'flac': 'flac',
        'ogg': 'libvorbis',
        'm4a': 'aac'
    }
    return codec_map.get(format_name, 'libmp3lame')