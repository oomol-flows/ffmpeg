#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    operation: typing.Literal["rotate_90_cw", "rotate_90_ccw", "rotate_180", "flip_horizontal", "flip_vertical", "transpose", "custom_angle"]
    custom_angle: float | None
    background_color: str | None
class Outputs(typing.TypedDict):
    rotated_video: str
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Rotate or flip video
    
    Args:
        params: Input parameters containing video file and rotation settings
        context: OOMOL context object
        
    Returns:
        Output rotated/flipped video file path
    """
    video_file = params["video_file"]
    operation = params["operation"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = f"/oomol-driver/oomol-storage/{base_name}_rotated.mp4"
    
    try:
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(video_file)
        
        # Apply transformation based on operation
        if operation == "rotate_90_cw":
            # Rotate 90 degrees clockwise
            video_stream = input_stream.video.filter('transpose', 1)
            
        elif operation == "rotate_90_ccw":
            # Rotate 90 degrees counter-clockwise
            video_stream = input_stream.video.filter('transpose', 2)
            
        elif operation == "rotate_180":
            # Rotate 180 degrees
            video_stream = input_stream.video.filter('transpose', 1).filter('transpose', 1)
            
        elif operation == "flip_horizontal":
            # Flip horizontally (mirror)
            video_stream = input_stream.video.filter('hflip')
            
        elif operation == "flip_vertical":
            # Flip vertically
            video_stream = input_stream.video.filter('vflip')
            
        elif operation == "transpose":
            # Transpose (flip along diagonal)
            video_stream = input_stream.video.filter('transpose', 0)
            
        elif operation == "custom_angle":
            # Custom rotation angle
            custom_angle = params["custom_angle"] or 45
            background_color = params["background_color"] or "#000000"
            
            # Convert hex color to RGB
            if background_color.startswith('#'):
                background_color = background_color[1:]
            
            # Convert angle to radians for FFmpeg
            angle_radians = custom_angle * 3.14159 / 180
            
            # Apply rotation with background fill
            video_stream = input_stream.video.filter(
                'rotate', 
                angle=angle_radians,
                fillcolor=background_color,
                out_w='rotw(ih)',
                out_h='roth(iw)'
            )
        else:
            raise ValueError(f"Invalid operation: {operation}")
        
        # Create output stream
        output_stream = ffmpeg.output(
            video_stream, 
            input_stream.audio, 
            output_file,
            vcodec='libx264',
            acodec='aac'
        )
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"rotated_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during video rotation: {error_msg}")
    except Exception as e:
        raise Exception(f"Error rotating video: {str(e)}")