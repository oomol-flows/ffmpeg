#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    output_format: typing.Literal["mp4", "avi", "mov", "mkv", "webm", "flv", "wmv"]
    video_codec: typing.Literal["libx264", "libx265", "libvpx", "libvpx-vp9", "copy"] | None
    audio_codec: typing.Literal["aac", "mp3", "libvorbis", "copy"] | None
    quality_preset: typing.Literal["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"] | None
class Outputs(typing.TypedDict):
    converted_video: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os
import sys
sys.path.append('/app/workspace')
from utils.ffmpeg_encoder import create_encoder

def main(params: Inputs, context: Context) -> Outputs:
    """
    Convert video to different format and codec
    
    Args:
        params: Input parameters containing video file and conversion settings
        context: OOMOL context object
        
    Returns:
        Output converted video file path
    """
    video_file = params["video_file"]
    output_format = params["output_format"]
    video_codec = params["video_codec"]
    audio_codec = params["audio_codec"]
    quality_preset = params["quality_preset"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = os.path.join(context.session_dir, f"{base_name}_converted.{output_format}")
    
    try:
        # Create GPU-aware encoder
        encoder = create_encoder(context)
        
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(video_file)
        
        # Determine codec type and get optimized options
        if video_codec in ['libx264', 'h264_nvenc', 'h264_videotoolbox'] or video_codec == 'copy':
            if video_codec == 'copy':
                conversion_options = {'vcodec': 'copy', 'acodec': audio_codec}
            else:
                profile = "fast" if quality_preset in ["ultrafast", "superfast", "veryfast"] else "balanced" if quality_preset in ["faster", "fast", "medium"] else "quality"
                conversion_options = encoder.get_encoding_options("h264", profile)
                conversion_options['acodec'] = audio_codec
        elif video_codec in ['libx265', 'hevc_nvenc', 'hevc_videotoolbox']:
            profile = "fast" if quality_preset in ["ultrafast", "superfast", "veryfast"] else "balanced" if quality_preset in ["faster", "fast", "medium"] else "quality"
            conversion_options = encoder.get_encoding_options("h265", profile)
            conversion_options['acodec'] = audio_codec
        else:
            # Fallback to original codec selection
            conversion_options = {
                'vcodec': video_codec,
                'acodec': audio_codec
            }
            # Add preset for supported codecs
            if video_codec in ['libx264', 'libx265']:
                conversion_options['preset'] = quality_preset
            
        # Special handling for different formats
        if output_format == 'webm':
            if video_codec == 'libx264':
                conversion_options['vcodec'] = 'libvpx-vp9'
            if audio_codec == 'aac':
                conversion_options['acodec'] = 'libvorbis'
        
        # Create output stream
        output_stream = ffmpeg.output(input_stream, output_file, **conversion_options)
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"converted_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during video conversion: {error_msg}")
    except Exception as e:
        raise Exception(f"Error converting video: {str(e)}")