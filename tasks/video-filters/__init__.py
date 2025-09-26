#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    filter_type: typing.Literal["blur", "sharpen", "brightness", "contrast", "saturation", "hue", "sepia", "grayscale", "vintage", "noise", "vignette"]
    blur_strength: float | None
    sharpen_strength: float | None
    brightness_level: float | None
    contrast_level: float | None
    saturation_level: float | None
    hue_shift: float | None
    noise_strength: float | None
    vignette_strength: float | None
class Outputs(typing.TypedDict):
    filtered_video: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Apply various visual filters to video
    
    Args:
        params: Input parameters containing video file and filter settings
        context: OOMOL context object
        
    Returns:
        Output filtered video file path
    """
    video_file = params["video_file"]
    filter_type = params["filter_type"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = f"/oomol-driver/oomol-storage/{base_name}_{filter_type}_filtered.mp4"
    
    try:
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(video_file)
        
        # Apply filter based on type
        if filter_type == "blur":
            blur_strength = params.get("blur_strength", 2.0)
            video_filter = input_stream.video.filter('boxblur', blur_strength)
        
        elif filter_type == "sharpen":
            sharpen_strength = params.get("sharpen_strength", 1.0)
            video_filter = input_stream.video.filter('unsharp', 5, 5, sharpen_strength)
        
        elif filter_type == "brightness":
            brightness_level = params.get("brightness_level", 0.2)
            video_filter = input_stream.video.filter('eq', brightness=brightness_level)
        
        elif filter_type == "contrast":
            contrast_level = params.get("contrast_level", 1.5)
            video_filter = input_stream.video.filter('eq', contrast=contrast_level)
        
        elif filter_type == "saturation":
            saturation_level = params.get("saturation_level", 1.5)
            video_filter = input_stream.video.filter('eq', saturation=saturation_level)
        
        elif filter_type == "hue":
            hue_shift = params.get("hue_shift", 30)
            # Convert degrees to radians for hue filter
            hue_radians = hue_shift * 3.14159 / 180
            video_filter = input_stream.video.filter('hue', h=hue_radians)
        
        elif filter_type == "sepia":
            # Apply sepia effect using colorchannelmixer
            video_filter = input_stream.video.filter('colorchannelmixer', 
                                                   rr=0.393, rg=0.769, rb=0.189,
                                                   gr=0.349, gg=0.686, gb=0.168,
                                                   br=0.272, bg=0.534, bb=0.131)
        
        elif filter_type == "grayscale":
            video_filter = input_stream.video.filter('hue', s=0)
        
        elif filter_type == "vintage":
            # Apply vintage effect with slight sepia and reduced saturation
            video_filter = (input_stream.video
                          .filter('eq', contrast=1.2, brightness=0.1, saturation=0.8)
                          .filter('colorchannelmixer', 
                                rr=0.393, rg=0.769, rb=0.189,
                                gr=0.349, gg=0.686, gb=0.168,
                                br=0.272, bg=0.534, bb=0.131, 
                                aa=0.8))
        
        elif filter_type == "noise":
            noise_strength = params.get("noise_strength", 20)
            video_filter = input_stream.video.filter('noise', alls=noise_strength)
        
        elif filter_type == "vignette":
            vignette_strength = params.get("vignette_strength", 0.5)
            # Create vignette effect
            video_filter = input_stream.video.filter('vignette', angle=vignette_strength)
        
        else:
            raise ValueError(f"Unsupported filter type: {filter_type}")
        
        # Create output with filtered video and original audio
        output_stream = ffmpeg.output(
            video_filter, 
            input_stream.audio,
            output_file,
            vcodec='libx264',
            acodec='aac'
        )
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"filtered_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during video filtering: {error_msg}")
    except Exception as e:
        raise Exception(f"Error applying video filter: {str(e)}")