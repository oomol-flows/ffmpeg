#region generated meta
import typing
class Inputs(typing.TypedDict):
    audio_file: str
    quality_method: typing.Literal["bitrate", "quality", "compression"]
    target_bitrate: float | None
    quality_level: float | None
    compression_level: float | None
    output_format: typing.Literal["mp3", "aac", "ogg", "flac"]
class Outputs(typing.TypedDict):
    quality_adjusted_audio: str
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Adjust audio quality using different methods
    
    Args:
        params: Input parameters containing audio file and quality settings
        context: OOMOL context object
        
    Returns:
        Output quality-adjusted audio file path
    """
    audio_file = params["audio_file"]
    quality_method = params["quality_method"]
    output_format = params["output_format"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    output_file = f"/oomol-driver/oomol-storage/{base_name}_quality_adjusted.{output_format}"
    
    try:
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(audio_file)
        
        # Configure quality options based on method
        quality_options = {
            'acodec': _get_audio_codec(output_format)
        }
        
        if quality_method == "bitrate":
            # Use target bitrate
            target_bitrate = params["target_bitrate"] or 128
            quality_options['audio_bitrate'] = f'{target_bitrate}k'
            
        elif quality_method == "quality":
            # Use quality level (VBR)
            quality_level = params["quality_level"] or 4
            if output_format == 'mp3':
                quality_options['q:a'] = quality_level
            elif output_format == 'ogg':
                quality_options['q:a'] = quality_level
            else:
                # Fall back to bitrate for formats that don't support VBR quality
                bitrate_map = {0: 320, 1: 256, 2: 192, 3: 160, 4: 128, 5: 112, 6: 96, 7: 80, 8: 64, 9: 32}
                quality_options['audio_bitrate'] = f'{bitrate_map[quality_level]}k'
                
        elif quality_method == "compression":
            # Use compression level
            compression_level = params["compression_level"] or 6
            if output_format == 'flac':
                quality_options['compression_level'] = compression_level
            elif output_format == 'ogg':
                quality_options['compression_level'] = compression_level
            else:
                # Fall back to bitrate for formats that don't support compression levels
                bitrate = max(32, 320 - (compression_level * 24))  # Inverse relationship
                quality_options['audio_bitrate'] = f'{bitrate}k'
        else:
            raise ValueError(f"Invalid quality method: {quality_method}")
        
        # Create output stream
        output_stream = ffmpeg.output(input_stream, output_file, **quality_options)
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"quality_adjusted_audio": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during audio quality adjustment: {error_msg}")
    except Exception as e:
        raise Exception(f"Error adjusting audio quality: {str(e)}")

def _get_audio_codec(format_name: str) -> str:
    """Get appropriate audio codec for the output format"""
    codec_map = {
        'mp3': 'libmp3lame',
        'aac': 'aac',
        'flac': 'flac',
        'ogg': 'libvorbis'
    }
    return codec_map.get(format_name, 'libmp3lame')