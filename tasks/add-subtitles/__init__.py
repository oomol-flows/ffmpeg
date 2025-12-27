#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    subtitle_file: str
    subtitle_style: typing.Literal["default", "custom"] | None
    font_name: str | None
    font_size: float | None
    font_color: str | None
    outline_color: str | None
    subtitle_position: typing.Literal["bottom", "top", "center"] | None
    hard_subtitle: bool | None
    use_gpu: bool | None
    subtitle_language: str | None
class Outputs(typing.TypedDict):
    subtitled_video: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os
import re
from utils.ffmpeg_encoder import create_encoder

def detect_subtitle_language(subtitle_file: str, custom_language: str = None) -> str:
    """
    Detect subtitle language from file name or use custom language

    Args:
        subtitle_file: Path to subtitle file
        custom_language: Custom language code provided by user

    Returns:
        Language code (e.g., 'eng', 'chi', 'jpn')
    """
    if custom_language and custom_language.strip():
        return custom_language.strip()

    # Extract language from filename
    filename = os.path.basename(subtitle_file).lower()

    # Common language patterns in filenames
    language_patterns = {
        'eng': r'\b(eng|english|en)\b',
        'chi': r'\b(chi|chinese|zh|cn)\b',
        'jpn': r'\b(jpn|japanese|ja)\b',
        'kor': r'\b(kor|korean|ko)\b',
        'fre': r'\b(fre|french|fr)\b',
        'ger': r'\b(ger|german|de)\b',
        'spa': r'\b(spa|spanish|es)\b',
        'rus': r'\b(rus|russian|ru)\b',
        'por': r'\b(por|portuguese|pt)\b',
        'ita': r'\b(ita|italian|it)\b',
    }

    for lang_code, pattern in language_patterns.items():
        if re.search(pattern, filename):
            return lang_code

    # Default to English if no language detected
    return 'eng'

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
    use_gpu = params["use_gpu"]
    subtitle_language = params.get("subtitle_language")
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]

    if hard_subtitle:
        output_file = os.path.join(context.session_dir, f"{base_name}_with_subtitles.mp4")
    else:
        output_file = os.path.join(context.session_dir, f"{base_name}_with_subtitles.mkv")
    
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
            
            # Create GPU-optimized encoder
            encoder = create_encoder(context)

            # Get encoding options based on GPU availability
            if use_gpu:
                encoding_options = encoder.get_encoding_options(codec_type="h264", profile="balanced")
            else:
                encoding_options = {
                    'vcodec': 'libx264',
                    'acodec': 'aac'
                }

            # Create output with burned-in subtitles
            output_stream = ffmpeg.output(
                video_stream,
                video_input.audio,
                output_file,
                **encoding_options
            )
        else:
            # Soft subtitles (embed as a separate stream)
            subtitle_input = ffmpeg.input(subtitle_file)

            # Detect subtitle language
            detected_language = detect_subtitle_language(subtitle_file, subtitle_language)

            # Create GPU-optimized encoder
            encoder = create_encoder(context)

            # Get encoding options based on GPU availability
            if use_gpu:
                encoding_options = encoder.get_encoding_options(codec_type="h264", profile="balanced")
                # Add subtitle-specific options
                encoding_options.update({
                    'scodec': 'srt',
                    'metadata:s:s:0': f'language={detected_language}'
                })
            else:
                encoding_options = {
                    'vcodec': 'libx264',
                    'acodec': 'aac',
                    'scodec': 'srt',
                    'metadata:s:s:0': f'language={detected_language}'
                }

            # Create output with embedded subtitle stream
            output_stream = ffmpeg.output(
                video_input.video,
                video_input.audio,
                subtitle_input,
                output_file,
                **encoding_options
            )
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"subtitled_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during subtitle addition: {error_msg}")
    except Exception as e:
        raise Exception(f"Error adding subtitles: {str(e)}")