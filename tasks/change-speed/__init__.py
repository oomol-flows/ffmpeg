#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    speed_method: typing.Literal["multiplier", "preset"]
    speed_preset: typing.Literal["0.25x", "0.5x", "0.75x", "1.25x", "1.5x", "2x", "4x"] | None
    speed_multiplier: float | None
    maintain_audio_pitch: bool
    audio_handling: typing.Literal["speed_change", "preserve_pitch", "remove_audio"]
class Outputs(typing.TypedDict):
    speed_changed_video: str
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Change video playback speed
    
    Args:
        params: Input parameters containing video file and speed settings
        context: OOMOL context object
        
    Returns:
        Output speed-changed video file path
    """
    video_file = params["video_file"]
    speed_method = params["speed_method"]
    audio_handling = params["audio_handling"]
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = f"/oomol-driver/oomol-storage/{base_name}_speed_changed.mp4"
    
    try:
        # Determine speed multiplier
        if speed_method == "preset":
            speed_preset = params["speed_preset"] or "2x"
            speed_multiplier = float(speed_preset.rstrip('x'))
        elif speed_method == "multiplier":
            speed_multiplier = params["speed_multiplier"] or 2.0
        else:
            raise ValueError(f"Invalid speed method: {speed_method}")
        
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(video_file)
        
        # Apply video speed change
        # Note: setpts filter works inversely - smaller PTS = faster playback
        pts_multiplier = 1.0 / speed_multiplier
        video_stream = input_stream.video.filter('setpts', f'{pts_multiplier}*PTS')
        
        # Handle audio based on the setting
        if audio_handling == "remove_audio":
            # No audio in output
            audio_stream = None
            
        elif audio_handling == "speed_change":
            # Change audio speed (will change pitch)
            audio_stream = input_stream.audio.filter('atempo', speed_multiplier)
            
        elif audio_handling == "preserve_pitch":
            # Change speed while preserving pitch
            # Note: atempo filter preserves pitch automatically
            # For extreme speed changes, may need to chain multiple atempo filters
            audio_stream = _apply_atempo_chain(input_stream.audio, speed_multiplier)
        else:
            raise ValueError(f"Invalid audio handling: {audio_handling}")
        
        # Create output stream
        if audio_stream is not None:
            output_stream = ffmpeg.output(
                video_stream, 
                audio_stream, 
                output_file,
                vcodec='libx264',
                acodec='aac'
            )
        else:
            output_stream = ffmpeg.output(
                video_stream, 
                output_file,
                vcodec='libx264'
            )
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"speed_changed_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during speed change: {error_msg}")
    except Exception as e:
        raise Exception(f"Error changing video speed: {str(e)}")

def _apply_atempo_chain(audio_stream, speed_multiplier: float):
    """
    Apply atempo filter chain for extreme speed changes
    atempo filter can only handle values between 0.5 and 2.0
    For values outside this range, we need to chain multiple atempo filters
    """
    current_stream = audio_stream
    remaining_multiplier = speed_multiplier
    
    # Handle speed increases (>2.0)
    while remaining_multiplier > 2.0:
        current_stream = current_stream.filter('atempo', 2.0)
        remaining_multiplier /= 2.0
    
    # Handle speed decreases (<0.5)
    while remaining_multiplier < 0.5:
        current_stream = current_stream.filter('atempo', 0.5)
        remaining_multiplier /= 0.5
    
    # Apply the final multiplier if it's not 1.0
    if remaining_multiplier != 1.0:
        current_stream = current_stream.filter('atempo', remaining_multiplier)
    
    return current_stream