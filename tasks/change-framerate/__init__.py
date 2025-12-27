#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    target_framerate: float
    frame_interpolation: typing.Literal["fps", "minterpolate"]
class Outputs(typing.TypedDict):
    framerate_changed_video: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os
import sys
sys.path.append('/app/workspace')
from utils.ffmpeg_encoder import create_encoder

def main(params: Inputs, context: Context) -> Outputs:
    """
    Change video frame rate
    
    Args:
        params: Input parameters containing video file and framerate settings
        context: OOMOL context object
        
    Returns:
        Output video with changed frame rate
    """
    video_file = params["video_file"]
    target_framerate = params["target_framerate"]
    frame_interpolation = params["frame_interpolation"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = os.path.join(context.session_dir, f"{base_name}_{target_framerate}fps.mp4")
    
    try:
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(video_file)
        
        # Apply frame rate change based on interpolation method
        if frame_interpolation == "fps":
            # Simple fps filter (drops or duplicates frames)
            video_stream = input_stream.video.filter('fps', fps=target_framerate)
        elif frame_interpolation == "minterpolate":
            # Motion interpolation (smoother but slower)
            video_stream = input_stream.video.filter(
                'minterpolate', 
                fps=target_framerate, 
                mi_mode='mci'
            )
        else:
            raise ValueError(f"Invalid frame interpolation method: {frame_interpolation}")
        
        # Create GPU-aware encoder
        encoder = create_encoder(context)
        
        # Get GPU-optimized encoding options
        encoding_options = encoder.get_encoding_options("h264", "balanced")
        
        # Create output stream
        output_stream = ffmpeg.output(
            video_stream, 
            input_stream.audio, 
            output_file,
            **encoding_options
        )
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"framerate_changed_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during frame rate change: {error_msg}")
    except Exception as e:
        raise Exception(f"Error changing frame rate: {str(e)}")