#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    watermark_type: typing.Literal["text", "image"]
    watermark_text: str | None
    watermark_image: str | None
    position: typing.Literal["top-left", "top-right", "bottom-left", "bottom-right", "center"]
    opacity: float
    font_size: float | None
    font_color: str | None
    padding: float
class Outputs(typing.TypedDict):
    watermarked_video: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Add text or image watermark to video
    
    Args:
        params: Input parameters containing video file and watermark settings
        context: OOMOL context object
        
    Returns:
        Output watermarked video file path
    """
    video_file = params["video_file"]
    watermark_type = params["watermark_type"]
    position = params["position"]
    opacity = params["opacity"]
    padding = params["padding"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = f"/oomol-driver/oomol-storage/{base_name}_watermarked.mp4"
    
    try:
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(video_file)
        
        if watermark_type == "text":
            # Text watermark
            watermark_text = params["watermark_text"] or "WATERMARK"
            font_size = params["font_size"] or 24
            font_color = params["font_color"] or "#FFFFFF"
            
            # Remove # from color if present
            if font_color.startswith('#'):
                font_color = font_color[1:]
            
            # Calculate position coordinates
            position_coords = _get_text_position_coordinates(position, padding)
            
            # Create text overlay filter
            text_filter = f"drawtext=text='{watermark_text}':fontsize={font_size}:fontcolor={font_color}@{opacity}:x={position_coords['x']}:y={position_coords['y']}"
            
            # Apply text overlay
            output_stream = (
                input_stream
                .video
                .filter('drawtext', 
                       text=watermark_text,
                       fontsize=font_size,
                       fontcolor=f"{font_color}@{opacity}",
                       x=position_coords['x'],
                       y=position_coords['y'])
                .output(input_stream.audio, output_file, vcodec='libx264', acodec='aac')
            )
            
        elif watermark_type == "image":
            # Image watermark
            watermark_image = params["watermark_image"]
            if not watermark_image:
                raise ValueError("Watermark image is required when watermark_type is image")
            
            # Create watermark input stream
            watermark_stream = ffmpeg.input(watermark_image)
            
            # Calculate position coordinates for image
            position_coords = _get_image_position_coordinates(position, padding)
            
            # Apply opacity to watermark image
            watermark_with_opacity = watermark_stream.filter('format', 'rgba').filter('colorchannelmixer', aa=opacity)
            
            # Overlay watermark on video
            output_stream = (
                input_stream
                .video
                .overlay(watermark_with_opacity, x=position_coords['x'], y=position_coords['y'])
                .output(input_stream.audio, output_file, vcodec='libx264', acodec='aac')
            )
        else:
            raise ValueError(f"Invalid watermark type: {watermark_type}")
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"watermarked_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during watermarking: {error_msg}")
    except Exception as e:
        raise Exception(f"Error adding watermark: {str(e)}")

def _get_text_position_coordinates(position: str, padding: int) -> dict:
    """Get text position coordinates based on position setting"""
    position_map = {
        'top-left': {'x': padding, 'y': padding},
        'top-right': {'x': f'(w-text_w-{padding})', 'y': padding},
        'bottom-left': {'x': padding, 'y': f'(h-text_h-{padding})'},
        'bottom-right': {'x': f'(w-text_w-{padding})', 'y': f'(h-text_h-{padding})'},
        'center': {'x': '(w-text_w)/2', 'y': '(h-text_h)/2'}
    }
    return position_map.get(position, position_map['bottom-right'])

def _get_image_position_coordinates(position: str, padding: int) -> dict:
    """Get image position coordinates based on position setting"""
    position_map = {
        'top-left': {'x': padding, 'y': padding},
        'top-right': {'x': f'(main_w-overlay_w-{padding})', 'y': padding},
        'bottom-left': {'x': padding, 'y': f'(main_h-overlay_h-{padding})'},
        'bottom-right': {'x': f'(main_w-overlay_w-{padding})', 'y': f'(main_h-overlay_h-{padding})'},
        'center': {'x': '(main_w-overlay_w)/2', 'y': '(main_h-overlay_h)/2'}
    }
    return position_map.get(position, position_map['bottom-right'])