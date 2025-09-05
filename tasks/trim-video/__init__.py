#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    start_time: float
    duration: float
    output_format: typing.Literal["mp4", "avi", "mov", "mkv", "webm"]
class Outputs(typing.TypedDict):
    trimmed_video: str
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Trim video to specific time segment
    
    Args:
        params: Input parameters containing video file, start time, duration, and output format
        context: OOMOL context object
        
    Returns:
        Output trimmed video file path
    """
    video_file = params["video_file"]
    start_time = params["start_time"]
    duration = params["duration"]
    output_format = params["output_format"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = f"/oomol-driver/oomol-storage/{base_name}_trimmed.{output_format}"
    
    try:
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(video_file)
        
        # Configure trim options
        trim_options = {
            'ss': start_time,  # Start time
            'vcodec': 'libx264',
            'acodec': 'aac'
        }
        
        # Add duration if specified (0 means to end of video)
        if duration > 0:
            trim_options['t'] = duration
            
        # Create output stream
        output_stream = ffmpeg.output(input_stream, output_file, **trim_options)
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"trimmed_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during video trimming: {error_msg}")
    except Exception as e:
        raise Exception(f"Error trimming video: {str(e)}")