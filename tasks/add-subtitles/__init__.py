#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    subtitle_file: str
    subtitle_style: typing.Literal["default", "custom"]
    font_name: str | None
    font_size: float | None
    font_color: str | None
    outline_color: str | None
    subtitle_position: typing.Literal["bottom", "top", "center"]
    hard_subtitle: bool
class Outputs(typing.TypedDict):
    subtitled_video: str
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Add subtitles to video
    
    Args:
        params: Input parameters containing video file and subtitle settings
        context: OOMOL context object
        
    Returns:
        Output video with subtitles
    """
    video_file = params["video_file"]
    subtitle_file = params["subtitle_file"]
    subtitle_style = params["subtitle_style"]
    subtitle_position = params["subtitle_position"]
    hard_subtitle = params["hard_subtitle"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    
    if hard_subtitle:
        output_file = f"/oomol-driver/oomol-storage/{base_name}_with_subtitles.mp4"
    else:
        output_file = f"/oomol-driver/oomol-storage/{base_name}_with_subtitles.mkv"
    
    try:
        # Create FFmpeg input streams
        video_input = ffmpeg.input(video_file)
        
        if hard_subtitle:
            # Burn subtitles into the video (hard subtitles)
            if subtitle_style == "custom":
                # Custom subtitle styling
                font_name = params["font_name"] or "Arial"
                font_size = params["font_size"] or 20
                font_color = (params["font_color"] or "#FFFFFF").lstrip('#')
                outline_color = (params["outline_color"] or "#000000").lstrip('#')
                
                # Calculate vertical position
                if subtitle_position == "bottom":
                    position_y = "h-th-20"
                elif subtitle_position == "top":
                    position_y = "20"
                else:  # center
                    position_y = "(h-th)/2"
                
                # Apply subtitle filter with custom styling
                video_stream = video_input.video.filter(
                    'subtitles', 
                    subtitle_file,
                    force_style=f"FontName={font_name},FontSize={font_size},PrimaryColour=&H{font_color}&,OutlineColour=&H{outline_color}&"
                )
            else:
                # Default subtitle styling
                video_stream = video_input.video.filter('subtitles', subtitle_file)
            
            # Create output with burned-in subtitles
            output_stream = ffmpeg.output(
                video_stream, 
                video_input.audio, 
                output_file,
                vcodec='libx264',
                acodec='aac'
            )
        else:
            # Soft subtitles (embed as a separate stream)
            subtitle_input = ffmpeg.input(subtitle_file)
            
            # Create output with embedded subtitle stream
            output_stream = ffmpeg.output(
                video_input.video,
                video_input.audio,
                subtitle_input,
                output_file,
                vcodec='libx264',
                acodec='aac',
                scodec='srt',  # Subtitle codec
                **{'metadata:s:s:0': 'language=eng'}  # Set subtitle language metadata
            )
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"subtitled_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during subtitle addition: {error_msg}")
    except Exception as e:
        raise Exception(f"Error adding subtitles: {str(e)}")