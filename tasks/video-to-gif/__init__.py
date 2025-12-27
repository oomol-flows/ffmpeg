#region generated meta
import typing
class Inputs(typing.TypedDict):
    video_file: str
    start_time: float | None
    duration: float | None
    output_width: float | None
    framerate: float | None
    quality: typing.Literal["high", "medium", "low"] | None
    dither: bool | None
    loop_count: float | None
class Outputs(typing.TypedDict):
    gif_file: typing.NotRequired[str]
#endregion

from oocana import Context

import os
import subprocess

def main(params: Inputs, context: Context) -> Outputs:
    """
    Convert video to GIF with optimization options

    Args:
        params: Input parameters containing video file and GIF settings
        context: OOMOL context object

    Returns:
        Output GIF file path
    """
    video_file = params["video_file"]

    # Apply default values for optional parameters
    start_time = params.get("start_time") or 0
    duration = params.get("duration") or 0
    output_width = params.get("output_width") or 480
    framerate = params.get("framerate") or 10
    quality = params.get("quality") or "medium"
    dither = params.get("dither") if params.get("dither") is not None else True
    loop_count = params.get("loop_count") if params.get("loop_count") is not None else 0

    # Set quality parameters based on quality setting
    if quality == "high":
        colors = 256
        bayer_scale = 0 if dither else -1
    elif quality == "medium":
        colors = 128
        bayer_scale = 2 if dither else -1
    else:  # low
        colors = 64
        bayer_scale = 4 if dither else -1

    # Generate output filename using session directory
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = os.path.join(context.session_dir, f"{base_name}.gif")

    # Ensure output directory exists
    os.makedirs(context.session_dir, exist_ok=True)

    try:
        # Build ffmpeg filter chain
        filter_complex = f'[0:v]fps={framerate}[s0];[s0]scale={int(output_width)}:-1:flags=lanczos[s1];[s1]split=2[s2][s3];[s2]palettegen=max_colors={colors}[s4];[s3][s4]paletteuse'

        if bayer_scale >= 0:
            filter_complex += f'=dither=bayer\\:bayer_scale\\={bayer_scale}'

        filter_complex += '[s5]'

        # Build ffmpeg command
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', video_file
        ]

        if duration > 0:
            cmd.extend(['-t', str(duration)])

        cmd.extend([
            '-filter_complex', filter_complex,
            '-map', '[s5]'
        ])

        if loop_count > 0:
            cmd.extend(['-loop', str(int(loop_count))])
        elif loop_count == 0:
            cmd.extend(['-loop', '-1'])  # Infinite loop

        cmd.extend(['-y', output_file])

        # Run ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"FFmpeg failed with return code {result.returncode}: {result.stderr}")

        # Verify file was created
        if not os.path.exists(output_file):
            raise Exception(f"GIF file was not created at {output_file}")

        return {"gif_file": output_file}

    except Exception as e:
        raise Exception(f"Error converting video to GIF: {str(e)}")