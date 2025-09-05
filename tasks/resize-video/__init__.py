#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    resize_method: typing.Literal["preset", "custom", "scale_percentage"]
    preset_size: typing.Literal["1920x1080", "1280x720", "854x480", "640x360", "426x240"] | None
    custom_width: float | None
    custom_height: float | None
    scale_percentage: float | None
    maintain_aspect_ratio: bool
class Outputs(typing.TypedDict):
    resized_video: str
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Resize video resolution
    
    Args:
        params: Input parameters containing video file and resize settings
        context: OOMOL context object
        
    Returns:
        Output resized video file path
    """
    video_file = params["video_file"]
    resize_method = params["resize_method"]
    maintain_aspect_ratio = params["maintain_aspect_ratio"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = f"/oomol-driver/oomol-storage/{base_name}_resized.mp4"
    
    try:
        # Get video information first if needed
        probe = ffmpeg.probe(video_file)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        original_width = int(video_stream['width'])
        original_height = int(video_stream['height'])
        
        # Calculate target dimensions based on method
        if resize_method == "preset":
            preset_size = params["preset_size"] or "1280x720"
            target_width, target_height = map(int, preset_size.split('x'))
        elif resize_method == "custom":
            target_width = params["custom_width"] or 1280
            target_height = params["custom_height"] or 720
        elif resize_method == "scale_percentage":
            scale = (params["scale_percentage"] or 50) / 100.0
            target_width = int(original_width * scale)
            target_height = int(original_height * scale)
        else:
            raise ValueError(f"Invalid resize method: {resize_method}")
        
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(video_file)
        
        # Configure scale filter
        if maintain_aspect_ratio:
            # Use scale filter with aspect ratio preservation
            scale_filter = f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease"
        else:
            # Force exact dimensions
            scale_filter = f"scale={target_width}:{target_height}"
        
        # Apply video filter and create output
        output_stream = (
            input_stream
            .video
            .filter('scale', target_width, target_height)
            .output(input_stream.audio, output_file, vcodec='libx264', acodec='aac')
        )
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"resized_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during video resizing: {error_msg}")
    except Exception as e:
        raise Exception(f"Error resizing video: {str(e)}")