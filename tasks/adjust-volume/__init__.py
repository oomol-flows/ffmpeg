#region generated meta
import typing
class Inputs(typing.TypedDict):
    audio_file: str
    volume_method: typing.Literal["percentage", "decibels", "normalize"]
    volume_percentage: float | None
    volume_decibels: float | None
    normalize_target: float | None
    fade_in_duration: float | None
    fade_out_duration: float | None
class Outputs(typing.TypedDict):
    volume_adjusted_audio: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Adjust audio volume using different methods
    
    Args:
        params: Input parameters containing audio file and volume settings
        context: OOMOL context object
        
    Returns:
        Output volume-adjusted audio file path
    """
    audio_file = params["audio_file"]
    volume_method = params["volume_method"]
    fade_in_duration = params["fade_in_duration"]
    fade_out_duration = params["fade_out_duration"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    output_file = os.path.join(context.session_dir, f"{base_name}_volume_adjusted.mp3")
    
    try:
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(audio_file)
        
        # Build audio filter chain
        audio_filters = []
        
        # Add volume adjustment filter
        if volume_method == "percentage":
            volume_percentage = params["volume_percentage"] or 100
            volume_factor = volume_percentage / 100.0
            audio_filters.append(f"volume={volume_factor}")
            
        elif volume_method == "decibels":
            volume_decibels = params["volume_decibels"] or 0
            audio_filters.append(f"volume={volume_decibels}dB")
            
        elif volume_method == "normalize":
            normalize_target = params["normalize_target"] or -23
            audio_filters.append(f"loudnorm=I={normalize_target}")
        else:
            raise ValueError(f"Invalid volume method: {volume_method}")
        
        # Add fade in filter if specified
        if fade_in_duration > 0:
            audio_filters.append(f"afade=t=in:ss=0:d={fade_in_duration}")
        
        # Add fade out filter if specified
        if fade_out_duration > 0:
            # Get audio duration to calculate fade out start time
            probe = ffmpeg.probe(audio_file)
            duration = float(probe['format']['duration'])
            fade_start = max(0, duration - fade_out_duration)
            audio_filters.append(f"afade=t=out:st={fade_start}:d={fade_out_duration}")
        
        # Apply audio filters
        audio_stream = input_stream.audio
        if audio_filters:
            filter_chain = ','.join(audio_filters)
            audio_stream = audio_stream.filter('aformat').filter('loudnorm' if 'loudnorm' in filter_chain else 'volume', filter_chain)
        
        # Create output stream
        output_stream = ffmpeg.output(audio_stream, output_file, acodec='libmp3lame', audio_bitrate='192k')
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"volume_adjusted_audio": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during volume adjustment: {error_msg}")
    except Exception as e:
        raise Exception(f"Error adjusting volume: {str(e)}")