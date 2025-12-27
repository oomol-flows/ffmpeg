#region generated meta
import typing
class Inputs(typing.TypedDict):
    main_audio: str
    background_audio: str
    merge_mode: typing.Literal["overlay", "sequential"] | None
    main_volume: float | None
    background_volume: float | None
    background_sync_method: typing.Literal["loop", "stretch", "trim"] | None
    fade_in_duration: float | None
    fade_out_duration: float | None
    output_format: typing.Literal["mp3", "wav", "aac", "flac", "ogg", "m4a"] | None
class Outputs(typing.TypedDict):
    merged_audio: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Merge multiple audio files with volume control and various sync options

    Args:
        params: Input parameters containing audio files and merge settings
        context: OOMOL context object

    Returns:
        Output merged audio file path
    """
    main_audio = params["main_audio"]
    background_audio = params["background_audio"]
    merge_mode = params["merge_mode"]
    main_volume = params["main_volume"]
    background_volume = params["background_volume"]
    background_sync_method = params.get("background_sync_method", "loop")
    fade_in_duration = params["fade_in_duration"]
    fade_out_duration = params["fade_out_duration"]
    output_format = params["output_format"]

    # Generate output filename
    base_name = os.path.splitext(os.path.basename(main_audio))[0]
    output_file = os.path.join(context.session_dir, f"{base_name}_merged.{output_format}")

    try:
        # Probe audio files to get durations
        main_probe = ffmpeg.probe(main_audio)
        main_duration = float(main_probe['format']['duration'])

        background_probe = ffmpeg.probe(background_audio)
        background_duration = float(background_probe['format']['duration'])

        # Create input streams
        main_input = ffmpeg.input(main_audio)
        background_input = ffmpeg.input(background_audio)

        # Process main audio stream
        main_stream = main_input.audio
        if main_volume != 1.0:
            main_stream = main_stream.filter('volume', main_volume)

        # Process background audio stream
        background_stream = background_input.audio
        if background_volume != 1.0:
            background_stream = background_stream.filter('volume', background_volume)

        # Merge audio based on mode
        if merge_mode == "overlay":
            # Overlay mode: mix main and background audio together

            # Sync background audio with main audio
            if background_sync_method == "loop":
                # Loop background audio to match main audio duration
                if background_duration < main_duration:
                    loop_count = int(main_duration / background_duration) + 1
                    background_stream = background_stream.filter('aloop', loop=loop_count, size=2e9)
                    background_stream = background_stream.filter('atrim', duration=main_duration)
                elif background_duration > main_duration:
                    # Trim if background is longer
                    background_stream = background_stream.filter('atrim', duration=main_duration)

            elif background_sync_method == "stretch":
                # Stretch background audio to match main audio duration
                if background_duration != main_duration:
                    tempo_factor = background_duration / main_duration
                    # Clamp tempo_factor to valid range (0.5 to 2.0)
                    tempo_factor = max(0.5, min(2.0, tempo_factor))
                    background_stream = background_stream.filter('atempo', tempo_factor)

            elif background_sync_method == "trim":
                # Trim background audio to match main audio duration
                if background_duration > main_duration:
                    background_stream = background_stream.filter('atrim', duration=main_duration)
                elif background_duration < main_duration:
                    # Pad with silence if background is shorter
                    silence_duration = main_duration - background_duration
                    background_stream = background_stream.filter('apad', pad_dur=silence_duration)

            # Mix the two audio streams
            merged_stream = ffmpeg.filter([main_stream, background_stream], 'amix', inputs=2, duration='longest')

        elif merge_mode == "sequential":
            # Sequential mode: play main audio first, then background audio
            merged_stream = ffmpeg.filter([main_stream, background_stream], 'concat', n=2, v=0, a=1)

        else:
            raise ValueError(f"Invalid merge mode: {merge_mode}")

        # Apply fade effects
        if fade_in_duration > 0:
            merged_stream = merged_stream.filter('afade', t='in', ss=0, d=fade_in_duration)

        if fade_out_duration > 0:
            # Calculate total duration for fade out
            if merge_mode == "overlay":
                total_duration = main_duration
            else:  # sequential
                total_duration = main_duration + background_duration

            fade_start = max(0, total_duration - fade_out_duration)
            merged_stream = merged_stream.filter('afade', t='out', st=fade_start, d=fade_out_duration)

        # Set output codec based on format
        codec_map = {
            "mp3": "libmp3lame",
            "wav": "pcm_s16le",
            "aac": "aac",
            "flac": "flac",
            "ogg": "libvorbis",
            "m4a": "aac"
        }

        audio_codec = codec_map.get(output_format, "libmp3lame")

        # Create output stream
        output_options = {'acodec': audio_codec}

        # Add format-specific options
        if output_format == "mp3":
            output_options['audio_bitrate'] = '192k'
        elif output_format == "aac" or output_format == "m4a":
            output_options['audio_bitrate'] = '192k'
        elif output_format == "ogg":
            output_options['audio_bitrate'] = '192k'

        output_stream = ffmpeg.output(merged_stream, output_file, **output_options)

        # Run FFmpeg command
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

        return {"merged_audio": output_file}

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during audio merge: {error_msg}")
    except Exception as e:
        raise Exception(f"Error merging audio files: {str(e)}")
