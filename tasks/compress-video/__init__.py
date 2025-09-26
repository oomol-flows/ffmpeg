#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    compression_method: typing.Literal["crf", "bitrate", "filesize"]
    crf_value: float | None
    target_bitrate: float | None
    target_filesize_mb: float | None
    preset: typing.Literal["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
    audio_bitrate: float
class Outputs(typing.TypedDict):
    compressed_video: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os
import sys
sys.path.append('/app/workspace')
from utils.ffmpeg_encoder import create_encoder

def main(params: Inputs, context: Context) -> Outputs:
    """
    Compress video using different compression methods
    
    Args:
        params: Input parameters containing video file and compression settings
        context: OOMOL context object
        
    Returns:
        Output compressed video file path
    """
    video_file = params["video_file"]
    compression_method = params["compression_method"]
    preset = params["preset"]
    audio_bitrate = params["audio_bitrate"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = f"/oomol-driver/oomol-storage/{base_name}_compressed.mp4"
    
    try:
        # Create GPU-aware encoder
        encoder = create_encoder(context)
        
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(video_file)
        
        # Get GPU-optimized encoding options
        profile = "fast" if preset in ["ultrafast", "superfast", "veryfast"] else "balanced" if preset in ["faster", "fast", "medium"] else "quality"
        encoding_options = encoder.get_encoding_options("h264", profile)
        encoding_options['audio_bitrate'] = f'{audio_bitrate}k'
        
        # Configure compression based on method
        if compression_method == "crf":
            # Constant Rate Factor (quality-based)
            crf_value = params["crf_value"] or 23
            encoding_options['crf'] = crf_value
            
        elif compression_method == "bitrate":
            # Target bitrate
            target_bitrate = params["target_bitrate"] or 1000
            encoding_options['video_bitrate'] = f'{target_bitrate}k'
            
        elif compression_method == "filesize":
            # Target file size (requires 2-pass encoding for accuracy)
            target_filesize_mb = params["target_filesize_mb"] or 50
            
            # Get video duration for bitrate calculation
            probe = ffmpeg.probe(video_file)
            duration = float(probe['format']['duration'])
            
            # Calculate target bitrate (leaving room for audio)
            target_size_bits = target_filesize_mb * 8 * 1024 * 1024  # Convert MB to bits
            audio_bits = audio_bitrate * 1000 * duration  # Audio bits
            video_bits = target_size_bits - audio_bits
            target_video_bitrate = int(video_bits / duration)
            
            encoding_options['video_bitrate'] = f'{target_video_bitrate}'
        else:
            raise ValueError(f"Invalid compression method: {compression_method}")
        
        # Create output stream
        output_stream = ffmpeg.output(input_stream, output_file, **encoding_options)
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"compressed_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during video compression: {error_msg}")
    except Exception as e:
        raise Exception(f"Error compressing video: {str(e)}")