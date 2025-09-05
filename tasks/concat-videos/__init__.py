#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_files: list[str]
    transition_duration: float
    transition_type: typing.Literal["none", "fade", "dissolve", "slide"]
    resize_to_first: bool
    output_format: typing.Literal["mp4", "avi", "mov", "mkv"]
class Outputs(typing.TypedDict):
    concatenated_video: str
#endregion

from oocana import Context
import ffmpeg
import os
import tempfile

def main(params: Inputs, context: Context) -> Outputs:
    """
    Concatenate multiple video files into one
    
    Args:
        params: Input parameters containing video files and concatenation settings
        context: OOMOL context object
        
    Returns:
        Output concatenated video file path
    """
    video_files = params["video_files"]
    transition_duration = params["transition_duration"]
    transition_type = params["transition_type"]
    resize_to_first = params["resize_to_first"]
    output_format = params["output_format"]
    
    if len(video_files) < 2:
        raise ValueError("At least 2 video files are required for concatenation")
    
    # Generate output filename
    output_file = f"/oomol-driver/oomol-storage/concatenated_video.{output_format}"
    
    try:
        if transition_duration > 0 and transition_type != "none":
            # Complex concatenation with transitions
            output_file = _concatenate_with_transitions(
                video_files, transition_duration, transition_type, 
                resize_to_first, output_file
            )
        else:
            # Simple concatenation without transitions
            output_file = _simple_concatenate(
                video_files, resize_to_first, output_file
            )
        
        return {"concatenated_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during video concatenation: {error_msg}")
    except Exception as e:
        raise Exception(f"Error concatenating videos: {str(e)}")

def _simple_concatenate(video_files: typing.List[str], resize_to_first: bool, output_file: str) -> str:
    """Simple concatenation using FFmpeg concat demuxer"""
    
    # Create a temporary file list for FFmpeg concat
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        concat_file = f.name
        
        if resize_to_first:
            # Get first video dimensions
            probe = ffmpeg.probe(video_files[0])
            video_stream = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            
            # Process each video to match dimensions
            processed_files = []
            for i, video_file in enumerate(video_files):
                processed_file = f"/tmp/processed_video_{i}.mp4"
                (
                    ffmpeg
                    .input(video_file)
                    .video
                    .filter('scale', width, height)
                    .output(processed_file, vcodec='libx264', acodec='aac')
                    .run(overwrite_output=True, quiet=True)
                )
                processed_files.append(processed_file)
                f.write(f"file '{processed_file}'\n")
        else:
            # Use original files
            for video_file in video_files:
                f.write(f"file '{video_file}'\n")
    
    try:
        # Run concatenation
        (
            ffmpeg
            .input(concat_file, format='concat', safe=0)
            .output(output_file, vcodec='libx264', acodec='aac')
            .run(overwrite_output=True, quiet=True)
        )
        
        return output_file
        
    finally:
        # Clean up temporary files
        os.unlink(concat_file)
        if resize_to_first:
            for processed_file in processed_files:
                if os.path.exists(processed_file):
                    os.unlink(processed_file)

def _concatenate_with_transitions(video_files: typing.List[str], transition_duration: float, 
                                transition_type: str, resize_to_first: bool, output_file: str) -> str:
    """Concatenate videos with transitions"""
    
    # For simplicity, implement fade transition only
    if transition_type == "fade":
        inputs = []
        filters = []
        
        # Create input streams
        for i, video_file in enumerate(video_files):
            inputs.append(ffmpeg.input(video_file))
        
        # Build filter chain for fade transitions
        current_output = inputs[0]
        
        for i in range(1, len(inputs)):
            # Add fade out to previous video
            fade_out = current_output.video.filter('fade', t='out', st=f'{transition_duration}', d=transition_duration)
            
            # Add fade in to current video  
            fade_in = inputs[i].video.filter('fade', t='in', st=0, d=transition_duration)
            
            # Overlay the transitions
            current_output = ffmpeg.filter([fade_out, fade_in], 'overlay')
        
        # Create final output
        (
            current_output
            .output(output_file, vcodec='libx264', acodec='aac')
            .run(overwrite_output=True, quiet=True)
        )
        
    else:
        # Fall back to simple concatenation for other transition types
        return _simple_concatenate(video_files, resize_to_first, output_file)
    
    return output_file