"""
OOMOL GPU Detection and Video Utilities

This module provides utilities for:
- GPU detection and identification from OOMOL context.host_info
- GPU-optimized FFmpeg encoding
- Video file validation and probing
"""

from .gpu_detector import (
    GPUInfo,
    GPUType,
    detect_gpu,
    is_nvidia_gpu,
    is_apple_m_series,
    get_gpu_vendor,
    get_gpu_model
)

from .ffmpeg_encoder import (
    FFmpegEncoder,
    EncodingProfile,
    VideoCodec,
    create_encoder,
    get_recommended_settings
)

from .video_utils import (
    VideoProbeResult,
    validate_and_probe_video,
    probe_video_safe
)

__all__ = [
    # GPU Detection
    "GPUInfo",
    "GPUType",
    "detect_gpu",
    "is_nvidia_gpu",
    "is_apple_m_series",
    "get_gpu_vendor",
    "get_gpu_model",
    # FFmpeg Encoder
    "FFmpegEncoder",
    "EncodingProfile",
    "VideoCodec",
    "create_encoder",
    "get_recommended_settings",
    # Video Utils
    "VideoProbeResult",
    "validate_and_probe_video",
    "probe_video_safe"
]