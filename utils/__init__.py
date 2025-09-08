"""
OOMOL GPU Detection Utilities

This module provides utilities for detecting and identifying GPU information
from the OOMOL context.host_info.
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

__all__ = [
    "GPUInfo",
    "GPUType", 
    "detect_gpu",
    "is_nvidia_gpu",
    "is_apple_m_series",
    "get_gpu_vendor",
    "get_gpu_model",
    "FFmpegEncoder",
    "EncodingProfile",
    "VideoCodec",
    "create_encoder",
    "get_recommended_settings"
]