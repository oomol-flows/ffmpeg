# FFmpeg

A comprehensive video and audio processing toolkit for OOMOL platform, providing a collection of reusable blocks for multimedia manipulation powered by FFmpeg.

## Overview

FFmpeg-NG is an OOMOL workflow project that offers a complete suite of video and audio processing capabilities. It provides modular, reusable blocks that can be combined to create powerful multimedia processing workflows without requiring deep knowledge of FFmpeg command-line syntax.

## Features

### Video Processing
- **Format Conversion**: Convert between various video formats (MP4, AVI, MOV, MKV, WebM, etc.)
- **Video Editing**: Trim, resize, rotate, and concatenate videos
- **Quality Control**: Adjust framerate, change playback speed, and compress videos
- **Visual Enhancement**: Add watermarks (text or image) and subtitles
- **Format Transformation**: Convert videos to GIF format

### Audio Processing  
- **Audio Extraction**: Extract audio tracks from video files
- **Format Conversion**: Convert between audio formats (MP3, WAV, AAC, FLAC, OGG)
- **Audio Editing**: Trim audio clips and adjust volume levels
- **Quality Enhancement**: Noise reduction and audio quality adjustment
- **Audio Merging**: Combine audio with video streams

### Media Utilities
- **Media Information**: Retrieve detailed metadata about media files
- **Batch Processing**: Process multiple files through workflow chains

## Available Blocks

### Video Blocks

| Block Name | Purpose | Key Features |
|------------|---------|--------------|
| `convert-video-format` | Convert video formats | Supports major formats, customizable codecs and quality presets |
| `trim-video` | Extract video segments | Precise start time and duration control |
| `resize-video` | Resize video dimensions | Maintain aspect ratio or custom dimensions |
| `rotate-video` | Rotate video orientation | 90°, 180°, 270° rotation options |
| `change-framerate` | Modify video framerate | Smooth framerate conversion with various methods |
| `change-speed` | Adjust playback speed | Speed up or slow down video with audio sync |
| `compress-video` | Reduce file size | Quality-preserving compression with bitrate control |
| `concat-videos` | Merge multiple videos | Seamless video concatenation |
| `add-watermark` | Add branding/protection | Text or image watermarks with position control |
| `add-subtitles` | Add subtitle tracks | SRT file support with customizable styling |
| `video-to-gif` | Create GIF animations | Convert video segments to optimized GIFs |

### Audio Blocks

| Block Name | Purpose | Key Features |
|------------|---------|--------------|
| `extract-audio` | Extract audio from video | Multiple output formats, quality control |
| `convert-audio-format` | Convert audio formats | Support for MP3, WAV, AAC, FLAC, OGG |
| `trim-audio` | Cut audio segments | Precise timing control |
| `adjust-volume` | Modify audio levels | Volume boost/reduction with clipping protection |
| `adjust-audio-quality` | Change audio bitrate | Quality optimization for different use cases |
| `audio-noise-reduction` | Clean audio tracks | Remove background noise and artifacts |
| `merge-audio-video` | Combine audio/video | Sync audio with video streams |

### Utility Blocks

| Block Name | Purpose | Key Features |
|------------|---------|--------------|
| `get-media-info` | Analyze media files | Extract metadata, duration, resolution, codecs |

## Usage

### Basic Workflow
1. **Import Media**: Use file input widgets to select your source media
2. **Process**: Chain together processing blocks based on your needs
3. **Export**: Save the processed media in your desired format

### Example Workflows

**Video Editing Pipeline**:
```
Input Video → Trim → Resize → Add Watermark → Convert Format → Output
```

**Audio Extraction & Processing**:
```
Input Video → Extract Audio → Noise Reduction → Adjust Volume → Convert Format → Output
```

**Subtitle Addition**:
```
Input Video + Subtitle File → Add Subtitles → Output Video
```

## Block Configuration

Each block provides intuitive configuration options:

- **File Inputs**: Drag-and-drop or browse for media files
- **Format Selection**: Choose from supported output formats
- **Quality Settings**: Adjust compression, bitrate, and encoding parameters  
- **Visual Controls**: Position watermarks, style subtitles, set colors
- **Timing Controls**: Precise start/end times, duration settings

## Technical Details

- **Engine**: Powered by FFmpeg for reliable, high-quality media processing
- **Platform**: Built for OOMOL workflow system
- **Languages**: Python implementation with Node.js dependencies
- **File Support**: Comprehensive format support for video, audio, and subtitle files

## Getting Started

1. Import the project into your OOMOL workspace
2. Create a new workflow using the available blocks
3. Configure each block's parameters through the intuitive UI
4. Connect blocks to create your processing pipeline
5. Run the workflow to process your media files

## Requirements

- OOMOL Platform
- Python 3.11+
- Node.js (for certain operations)
- FFmpeg (automatically configured)

This toolkit makes professional-grade video and audio processing accessible through visual workflows, eliminating the need for complex command-line operations while maintaining the full power of FFmpeg.