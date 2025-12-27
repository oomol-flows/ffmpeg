#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    audio_file: str
    sync_method: typing.Literal["stretch_audio", "loop_audio", "trim_audio", "trim_video"] | None
    audio_volume: float | None
class Outputs(typing.TypedDict):
    output_video: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os
from utils.video_utils import validate_and_probe_video
from utils.ffmpeg_encoder import create_encoder

def main(params: Inputs, context: Context) -> Outputs:
    """
    Replace video's audio track with a new audio file

    Args:
        params: Input parameters containing video file, audio file and replacement settings
        context: OOMOL context object

    Returns:
        Output video with replaced audio track
    """
    video_file = params["video_file"]
    audio_file = params["audio_file"]
    sync_method = params["sync_method"]
    audio_volume = params["audio_volume"]

    # Generate output filename
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = os.path.join(context.session_dir, f"{base_name}_replaced_audio.mp4")

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

        # Create output stream with replaced audio
        output_stream = ffmpeg.output(
            video_input.video,
            audio_stream,
            output_file,
            **encoding_options
        )

        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

        return {"output_video": output_file}

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during audio replacement: {error_msg}")
    except Exception as e:
        raise Exception(f"Error replacing audio: {str(e)}")
