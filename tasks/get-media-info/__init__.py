#region generated meta
import typing
class Inputs(typing.TypedDict):
    input_file: str
    output_format: typing.Literal["json", "text"]
    include_streams: bool
    include_chapters: bool
class Outputs(typing.TypedDict):
    media_info: typing.NotRequired[dict]
    info_file: typing.NotRequired[str]
#endregion

from oocana import Context
import ffmpeg
import json
import os

def main(params: Inputs, context: Context) -> Outputs:
    """
    Extract detailed information about media file
    
    Args:
        params: Input parameters containing media file and info extraction settings
        context: OOMOL context object
        
    Returns:
        Media information as structured data and file
    """
    media_file = params["input_file"]
    output_format = params["output_format"]
    include_streams = params["include_streams"]
    include_chapters = params["include_chapters"]
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(media_file))[0]
    file_extension = "json" if output_format == "json" else "txt"
    info_file_path = f"/oomol-driver/oomol-storage/{base_name}_info.{file_extension}"
    
    try:
        # Get media information using ffprobe
        probe_data = ffmpeg.probe(media_file)
        
        # Extract basic information
        format_info = probe_data.get('format', {})
        streams = probe_data.get('streams', [])
        
        # Build structured media information
        media_info = {
            "filename": os.path.basename(media_file),
            "format": {
                "name": format_info.get('format_name'),
                "long_name": format_info.get('format_long_name'),
                "duration": float(format_info.get('duration', 0)),
                "size": int(format_info.get('size', 0)),
                "bit_rate": int(format_info.get('bit_rate', 0))
            },
            "metadata": format_info.get('tags', {})
        }
        
        # Add streams information if requested
        if include_streams:
            media_info["streams"] = []
            
            for stream in streams:
                stream_info = {
                    "index": stream.get('index'),
                    "type": stream.get('codec_type'),
                    "codec": stream.get('codec_name'),
                    "codec_long_name": stream.get('codec_long_name')
                }
                
                # Add video-specific information
                if stream.get('codec_type') == 'video':
                    stream_info.update({
                        "width": stream.get('width'),
                        "height": stream.get('height'),
                        "aspect_ratio": stream.get('display_aspect_ratio'),
                        "frame_rate": stream.get('r_frame_rate'),
                        "pixel_format": stream.get('pix_fmt'),
                        "bit_rate": stream.get('bit_rate')
                    })
                
                # Add audio-specific information
                elif stream.get('codec_type') == 'audio':
                    stream_info.update({
                        "sample_rate": stream.get('sample_rate'),
                        "channels": stream.get('channels'),
                        "channel_layout": stream.get('channel_layout'),
                        "bit_rate": stream.get('bit_rate'),
                        "bits_per_sample": stream.get('bits_per_raw_sample')
                    })
                
                # Add stream metadata
                if stream.get('tags'):
                    stream_info["metadata"] = stream.get('tags')
                
                media_info["streams"].append(stream_info)
        
        # Add chapters information if requested
        if include_chapters:
            chapters = probe_data.get('chapters', [])
            if chapters:
                media_info["chapters"] = []
                for chapter in chapters:
                    chapter_info = {
                        "id": chapter.get('id'),
                        "start": float(chapter.get('start', 0)),
                        "end": float(chapter.get('end', 0)),
                        "start_time": float(chapter.get('start_time', 0)),
                        "end_time": float(chapter.get('end_time', 0)),
                        "metadata": chapter.get('tags', {})
                    }
                    media_info["chapters"].append(chapter_info)
        
        # Save information to file
        if output_format == "json":
            with open(info_file_path, 'w', encoding='utf-8') as f:
                json.dump(media_info, f, indent=2, ensure_ascii=False)
        else:
            # Text format
            with open(info_file_path, 'w', encoding='utf-8') as f:
                f.write(f"Media Information: {media_info['filename']}\n")
                f.write("=" * 50 + "\n\n")
                
                # Format information
                f.write("Format Information:\n")
                f.write(f"  Format: {media_info['format']['name']} ({media_info['format']['long_name']})\n")
                f.write(f"  Duration: {media_info['format']['duration']:.2f} seconds\n")
                f.write(f"  File Size: {media_info['format']['size']:,} bytes\n")
                f.write(f"  Bit Rate: {media_info['format']['bit_rate']:,} bps\n\n")
                
                # Streams information
                if include_streams and "streams" in media_info:
                    f.write("Streams:\n")
                    for i, stream in enumerate(media_info["streams"]):
                        f.write(f"  Stream {i} ({stream['type']}):\n")
                        f.write(f"    Codec: {stream['codec']} ({stream.get('codec_long_name', '')})\n")
                        
                        if stream['type'] == 'video':
                            f.write(f"    Resolution: {stream.get('width', 'N/A')}x{stream.get('height', 'N/A')}\n")
                            f.write(f"    Frame Rate: {stream.get('frame_rate', 'N/A')}\n")
                            f.write(f"    Pixel Format: {stream.get('pixel_format', 'N/A')}\n")
                        elif stream['type'] == 'audio':
                            f.write(f"    Sample Rate: {stream.get('sample_rate', 'N/A')} Hz\n")
                            f.write(f"    Channels: {stream.get('channels', 'N/A')}\n")
                            f.write(f"    Channel Layout: {stream.get('channel_layout', 'N/A')}\n")
                        f.write("\n")
                
                # Metadata
                if media_info['metadata']:
                    f.write("Metadata:\n")
                    for key, value in media_info['metadata'].items():
                        f.write(f"  {key}: {value}\n")
        
        return {
            "media_info": media_info,
            "info_file": info_file_path
        }
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception(f"FFmpeg error during media info extraction: {error_msg}")
    except Exception as e:
        raise Exception(f"Error extracting media information: {str(e)}")