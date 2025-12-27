#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    audio_file: str
    audio_handling: typing.Literal["replace", "mix", "keep_both"] | None
    audio_volume: float | None
    original_audio_volume: float | None
    sync_method: typing.Literal["stretch_audio", "loop_audio", "trim_audio", "trim_video"] | None
    subtitle_file: str | None
class Outputs(typing.TypedDict):
    merged_video: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os
from utils.video_utils import validate_and_probe_video
from utils.ffmpeg_encoder import create_encoder

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
    subtitle_file = params.get("subtitle_file")
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = os.path.join(context.session_dir, f"{base_name}_with_audio.mp4")
    
    try:
        # Validate and probe video file
        video_probe_result = validate_and_probe_video(video_file)
        video_duration = video_probe_result.duration

        # Probe audio file
        audio_probe = ffmpeg.probe(audio_file)
        audio_duration = float(audio_probe['format']['duration'])
        
        # Create input streams
        video_input = ffmpeg.input(video_file)
        audio_input = ffmpeg.input(audio_file)

        # Get video stream and apply subtitle if provided
        video_stream = video_input.video
        if subtitle_file:
            # Escape special characters in subtitle file path for FFmpeg
            subtitle_path = subtitle_file.replace('\\', '/').replace(':', '\\:')
            video_stream = video_stream.filter('subtitles', subtitle_path)
        
        # Handle audio synchronization
        if sync_method == "stretch_audio":
            # Stretch audio to match video duration
            if audio_duration != video_duration:
                tempo_factor = audio_duration / video_duration
                # Clamp tempo_factor to valid range (0.5 to 2.0)
                tempo_factor = max(0.5, min(2.0, tempo_factor))
                audio_stream = audio_input.audio.filter('atempo', tempo_factor)
            else:
                audio_stream = audio_input.audio

        elif sync_method == "loop_audio":
            # Loop audio to match video duration
            if audio_duration < video_duration:
                loop_count = int(video_duration / audio_duration) + 1
                audio_stream = audio_input.audio.filter('aloop', loop=loop_count, size=2e9)
                # Trim to exact duration
                audio_stream = audio_stream.filter('atrim', duration=video_duration)
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

        # Create GPU-optimized encoder
        encoder = create_encoder(context)

        # Get GPU-optimized encoding options
        encoding_options = encoder.get_encoding_options(codec_type="h264", profile="balanced")

        # Handle audio mixing/replacement
        if audio_handling == "replace":
            # Replace existing audio with new audio
            final_audio = audio_stream
            
        elif audio_handling == "mix":
            # Mix new audio with existing audio
            original_audio_volume = params.get("original_audio_volume", 0.5)
            
            # Check if video has audio
            has_audio = video_probe_result.has_audio

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
            output_file = os.path.join(context.session_dir, f"{base_name}_with_audio.mkv")

            # Check if video has audio
            has_audio = video_probe_result.has_audio

            if has_audio:
                # Create output with multiple audio streams
                output_stream = ffmpeg.output(
                    video_stream,
                    video_input.audio,  # Original audio
                    audio_stream,       # New audio
                    output_file,
                    **encoding_options,
                    **{'map': ['0:v:0', '0:a:0', '1:a:0']}  # Map video and both audio streams
                )
            else:
                # No original audio, just add the new audio
                output_stream = ffmpeg.output(
                    video_stream,
                    audio_stream,
                    output_file,
                    **encoding_options
                )
        else:
            raise ValueError(f"Invalid audio handling method: {audio_handling}")
        
        # Create output stream (for replace and mix methods)
        if audio_handling != "keep_both":
            output_stream = ffmpeg.output(
                video_stream,
                final_audio,
                output_file,
                **encoding_options
            )
        
        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
        return {"merged_video": output_file}
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during audio-video merge: {error_msg}")
    except Exception as e:
        raise Exception(f"Error merging audio and video: {str(e)}")