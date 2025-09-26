#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    audio_file: str
    audio_handling: typing.Literal["replace", "mix", "keep_both"]
    audio_volume: float
    original_audio_volume: float | None
    sync_method: typing.Literal["stretch_audio", "loop_audio", "trim_audio", "trim_video"]
class Outputs(typing.TypedDict):
    merged_video: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Merge audio file with video file
    
    Args:
        params: Input parameters containing video file, audio file and merge settings
        context: OOMOL context object
        
    Returns:
        Output video with merged audio
    """
    video_file = params["video_file"]
    audio_file = params["audio_file"]
    audio_handling = params["audio_handling"]
    audio_volume = params["audio_volume"]
    sync_method = params["sync_method"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = f"/oomol-driver/oomol-storage/{base_name}_with_audio.mp4"
    
    try:
        # Get duration information
        video_probe = ffmpeg.probe(video_file)
        audio_probe = ffmpeg.probe(audio_file)
        
        video_duration = float(video_probe['format']['duration'])
        audio_duration = float(audio_probe['format']['duration'])
        
        # Create input streams
        video_input = ffmpeg.input(video_file)
        audio_input = ffmpeg.input(audio_file)
        
        # Handle audio synchronization
        if sync_method == "stretch_audio":
            # Stretch audio to match video duration
            if audio_duration != video_duration:
                tempo_factor = audio_duration / video_duration
                audio_stream = audio_input.audio.filter('atempo', tempo_factor)
            else:
                audio_stream = audio_input.audio
                
        elif sync_method == "loop_audio":
            # Loop audio to match video duration
            if audio_duration < video_duration:
                loop_count = int(video_duration / audio_duration) + 1
                audio_stream = audio_input.audio.filter('aloop', loop=loop_count)
            else:
                audio_stream = audio_input.audio
                
        elif sync_method == "trim_audio":
            # Trim audio to match video duration
            audio_stream = audio_input.audio.filter('atrim', duration=video_duration)
            
        elif sync_method == "trim_video":
            # Trim video to match audio duration
            video_input = ffmpeg.input(video_file, t=audio_duration)
            audio_stream = audio_input.audio
        else:
            raise ValueError(f"Invalid sync method: {sync_method}")
        
        # Apply volume adjustment
        if audio_volume != 1.0:
            audio_stream = audio_stream.filter('volume', audio_volume)
        
        # Handle audio mixing/replacement
        if audio_handling == "replace":
            # Replace existing audio with new audio
            final_audio = audio_stream
            
        elif audio_handling == "mix":
            # Mix new audio with existing audio
            original_audio_volume = params.get("original_audio_volume", 0.5)
            
            # Check if video has audio
            has_audio = any(stream['codec_type'] == 'audio' for stream in video_probe['streams'])
            
            if has_audio:
                # Adjust original audio volume
                original_audio = video_input.audio.filter('volume', original_audio_volume)
                # Mix the two audio streams
                final_audio = ffmpeg.filter([original_audio, audio_stream], 'amix', inputs=2)
            else:
                # No original audio, just use new audio
                final_audio = audio_stream
                
        elif audio_handling == "keep_both":
            # Keep both audio tracks as separate streams (works with MKV)
            output_file = f"/oomol-driver/oomol-storage/{base_name}_with_audio.mkv"
            
            # Check if video has audio
            has_audio = any(stream['codec_type'] == 'audio' for stream in video_probe['streams'])
            
            if has_audio:
                # Create output with multiple audio streams
                output_stream = ffmpeg.output(
                    video_input.video,
                    video_input.audio,  # Original audio
                    audio_stream,       # New audio
                    output_file,
                    vcodec='libx264',
                    acodec='aac',
                    map='0:v:0',  # Video from first input
                    map='0:a:0',  # Audio from first input
                    map='1:a:0'   # Audio from second input
                )
            else:
                # No original audio, just add the new audio
                output_stream = ffmpeg.output(
                    video_input.video,
                    audio_stream,
                    output_file,
                    vcodec='libx264',
                    acodec='aac'
                )
        else:
            raise ValueError(f"Invalid audio handling method: {audio_handling}")
        
        # Create output stream (for replace and mix methods)
        if audio_handling != "keep_both":
            output_stream = ffmpeg.output(
                video_input.video,
                final_audio,
                output_file,
                vcodec='libx264',
                acodec='aac'
            )
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"merged_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during audio-video merge: {error_msg}")
    except Exception as e:
        raise Exception(f"Error merging audio and video: {str(e)}")