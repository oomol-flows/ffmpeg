#region generated meta
import typing
class Inputs(typing.TypedDict):
    audio_file: str
    noise_reduction_method: typing.Literal["highpass", "lowpass", "bandpass", "afftdn"]
    highpass_frequency: float | None
    lowpass_frequency: float | None
    bandpass_low_frequency: float | None
    bandpass_high_frequency: float | None
    noise_reduction_strength: float | None
class Outputs(typing.TypedDict):
    noise_reduced_audio: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Reduce audio noise using various filtering methods
    
    Args:
        params: Input parameters containing audio file and noise reduction settings
        context: OOMOL context object
        
    Returns:
        Output noise-reduced audio file path
    """
    audio_file = params["audio_file"]
    noise_reduction_method = params["noise_reduction_method"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    output_file = f"/oomol-driver/oomol-storage/{base_name}_noise_reduced.mp3"
    
    try:
        # Create FFmpeg input stream
        input_stream = ffmpeg.input(audio_file)
        
        # Apply noise reduction filter based on method
        if noise_reduction_method == "highpass":
            # High-pass filter removes low frequency noise
            frequency = params["highpass_frequency"] or 80
            audio_stream = input_stream.audio.filter('highpass', f=frequency)
            
        elif noise_reduction_method == "lowpass":
            # Low-pass filter removes high frequency noise
            frequency = params["lowpass_frequency"] or 8000
            audio_stream = input_stream.audio.filter('lowpass', f=frequency)
            
        elif noise_reduction_method == "bandpass":
            # Band-pass filter keeps only frequencies within specified range
            low_freq = params["bandpass_low_frequency"] or 300
            high_freq = params["bandpass_high_frequency"] or 3000
            audio_stream = input_stream.audio.filter('bandpass', f=f'{low_freq}:width_type=h:width={high_freq-low_freq}')
            
        elif noise_reduction_method == "afftdn":
            # FFT-based noise reduction (advanced)
            strength = params["noise_reduction_strength"] or 0.85
            audio_stream = input_stream.audio.filter('afftdn', nr=strength, nf=-25)
        else:
            raise ValueError(f"Invalid noise reduction method: {noise_reduction_method}")
        
        # Create output stream
        output_stream = ffmpeg.output(audio_stream, output_file, acodec='libmp3lame', audio_bitrate='192k')
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"noise_reduced_audio": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during noise reduction: {error_msg}")
    except Exception as e:
        raise Exception(f"Error reducing noise: {str(e)}")