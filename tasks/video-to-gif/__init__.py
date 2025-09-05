#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    start_time: float
    duration: float
    output_width: float
    framerate: float
    quality: typing.Literal["high", "medium", "low"]
    dither: bool
    loop_count: float
class Outputs(typing.TypedDict):
    gif_file: str
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Convert video to GIF with optimization options
    
    Args:
        params: Input parameters containing video file and GIF settings
        context: OOMOL context object
        
    Returns:
        Output GIF file path
    """
    video_file = params["video_file"]
    start_time = params["start_time"]
    duration = params["duration"]
    output_width = params["output_width"]
    framerate = params["framerate"]
    quality = params["quality"]
    dither = params["dither"]
    loop_count = params["loop_count"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = f"/oomol-driver/oomol-storage/{base_name}.gif"
    
    try:
        # Create FFmpeg input stream with timing
        input_options = {'ss': start_time}
        if duration > 0:
            input_options['t'] = duration
            
        input_stream = ffmpeg.input(video_file, **input_options)
        
        # Set quality parameters based on quality setting
        if quality == "high":
            colors = 256
            bayer_scale = 0 if dither else -1
        elif quality == "medium":
            colors = 128
            bayer_scale = 2 if dither else -1
        else:  # low
            colors = 64
            bayer_scale = 4 if dither else -1
        
        # Create filter chain for GIF optimization
        # Step 1: Scale and set framerate
        video_stream = (
            input_stream
            .video
            .filter('fps', framerate)
            .filter('scale', output_width, -1, flags='lanczos')  # -1 maintains aspect ratio
        )
        
        # Step 2: Generate optimal palette
        palette_stream = video_stream.filter('palettegen', max_colors=colors)
        
        # Step 3: Use palette for final GIF with dithering options
        paletteuse_options = {'dither': 'bayer:bayer_scale=' + str(bayer_scale)} if bayer_scale >= 0 else {}
        
        gif_stream = ffmpeg.filter(
            [video_stream, palette_stream], 
            'paletteuse',
            **paletteuse_options
        )
        
        # Create output with loop settings
        output_options = {}
        if loop_count > 0:
            output_options['loop'] = loop_count
        elif loop_count == 0:
            output_options['loop'] = -1  # Infinite loop
        
        output_stream = ffmpeg.output(gif_stream, output_file, **output_options)
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"gif_file": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during GIF conversion: {error_msg}")
    except Exception as e:
        raise Exception(f"Error converting video to GIF: {str(e)}")