#region generated meta
import typing
class Inputs(typing.TypedDict):
    input_file: str
    extraction_mode: typing.Literal["single", "interval", "count", "all"]
    timestamp: typing.NotRequired[float]
    interval: typing.NotRequired[float]
    frame_count: typing.NotRequired[int]
    output_format: typing.Literal["jpg", "png", "webp"]
    quality: int
    output_prefix: str

class Outputs(typing.TypedDict):
    output_frames: list[str]
    output_directory: str
    frame_info: dict
#endregion

from oocana import Context
import ffmpeg
import os
import json
from pathlib import Path

def main(params: Inputs, context: Context) -> Outputs:
    """
    Extract frames from video at specified intervals, timestamps, or count

    Args:
        params: Input parameters containing video file and extraction settings
        context: OOMOL context object

    Returns:
        Extracted frame files and extraction information
    """
    input_file = params["input_file"]
    extraction_mode = params["extraction_mode"]
    output_format = params["output_format"]
    quality = params["quality"]
    output_prefix = params["output_prefix"]

    # Create output directory
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = f"/oomol-driver/oomol-storage/{base_name}_frames"
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Get video information
        probe = ffmpeg.probe(input_file)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

        if not video_stream:
            raise Exception("No video stream found in the input file")

        # Calculate video duration
        duration = float(probe['format']['duration'])

        # Get frame rate
        fps_str = video_stream.get('r_frame_rate', '25/1')
        fps_parts = fps_str.split('/')
        fps = float(fps_parts[0]) / float(fps_parts[1])

        output_frames = []
        frame_info = {
            "video_file": os.path.basename(input_file),
            "duration": duration,
            "fps": fps,
            "extraction_mode": extraction_mode,
            "frames": []
        }

        # Determine output extension
        ext = output_format

        if extraction_mode == "single":
            # Extract single frame at specified timestamp
            timestamp = params.get("timestamp", 0)
            if timestamp > duration:
                timestamp = duration - 0.1

            output_file = os.path.join(output_dir, f"{output_prefix}_{timestamp:.2f}s.{ext}")

            stream = ffmpeg.input(input_file, ss=timestamp)
            stream = ffmpeg.output(stream, output_file, vframes=1, **_get_quality_params(output_format, quality))
            ffmpeg.run(stream, overwrite_output=True, quiet=True)

            output_frames.append(output_file)
            frame_info["frames"].append({
                "filename": os.path.basename(output_file),
                "timestamp": timestamp
            })

        elif extraction_mode == "interval":
            # Extract frames at regular intervals
            interval = params.get("interval", 1.0)
            timestamp = 0
            frame_num = 0

            while timestamp < duration:
                output_file = os.path.join(output_dir, f"{output_prefix}_{frame_num:05d}.{ext}")

                stream = ffmpeg.input(input_file, ss=timestamp)
                stream = ffmpeg.output(stream, output_file, vframes=1, **_get_quality_params(output_format, quality))
                ffmpeg.run(stream, overwrite_output=True, quiet=True)

                output_frames.append(output_file)
                frame_info["frames"].append({
                    "filename": os.path.basename(output_file),
                    "timestamp": timestamp,
                    "frame_number": frame_num
                })

                timestamp += interval
                frame_num += 1

            frame_info["interval"] = interval

        elif extraction_mode == "count":
            # Extract specified number of frames evenly distributed
            frame_count = params.get("frame_count", 10)
            if frame_count < 1:
                frame_count = 1

            if frame_count == 1:
                timestamps = [duration / 2]
            else:
                timestamps = [i * duration / (frame_count - 1) for i in range(frame_count)]

            for frame_num, timestamp in enumerate(timestamps):
                output_file = os.path.join(output_dir, f"{output_prefix}_{frame_num:05d}.{ext}")

                stream = ffmpeg.input(input_file, ss=timestamp)
                stream = ffmpeg.output(stream, output_file, vframes=1, **_get_quality_params(output_format, quality))
                ffmpeg.run(stream, overwrite_output=True, quiet=True)

                output_frames.append(output_file)
                frame_info["frames"].append({
                    "filename": os.path.basename(output_file),
                    "timestamp": timestamp,
                    "frame_number": frame_num
                })

            frame_info["requested_count"] = frame_count

        elif extraction_mode == "all":
            # Extract all frames
            output_pattern = os.path.join(output_dir, f"{output_prefix}_%05d.{ext}")

            stream = ffmpeg.input(input_file)
            stream = ffmpeg.output(stream, output_pattern, **_get_quality_params(output_format, quality))
            ffmpeg.run(stream, overwrite_output=True, quiet=True)

            # List all generated frames
            frame_files = sorted([f for f in os.listdir(output_dir) if f.startswith(output_prefix)])
            for frame_num, frame_file in enumerate(frame_files):
                output_file = os.path.join(output_dir, frame_file)
                output_frames.append(output_file)
                frame_info["frames"].append({
                    "filename": frame_file,
                    "frame_number": frame_num
                })

        frame_info["total_frames_extracted"] = len(output_frames)

        return {
            "output_frames": output_frames,
            "output_directory": output_dir,
            "frame_info": frame_info
        }

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during frame extraction: {error_msg}")
    except Exception as e:
        raise Exception(f"Error extracting frames: {str(e)}")


def _get_quality_params(output_format: str, quality: int) -> dict:
    """
    Get quality parameters for different output formats

    Args:
        output_format: Output image format (jpg, png, webp)
        quality: Quality value (1-100)

    Returns:
        Dictionary of ffmpeg parameters for quality control
    """
    params = {}

    if output_format == "jpg":
        # JPEG quality: 2-31 (lower is better), convert from 1-100 scale
        jpeg_quality = max(2, min(31, int(31 - (quality / 100) * 29)))
        params['q:v'] = jpeg_quality
    elif output_format == "png":
        # PNG compression: 0-9 (higher is more compression)
        png_compression = max(0, min(9, int((100 - quality) / 11)))
        params['compression_level'] = png_compression
    elif output_format == "webp":
        # WebP quality: 0-100
        params['quality'] = quality
        params['compression_level'] = 4

    return params
