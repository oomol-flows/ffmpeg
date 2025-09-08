from typing import Dict, Optional, Literal
import re

GPUType = Literal["NVIDIA", "APPLE_M", "UNKNOWN"]

class GPUInfo:
    """GPU information class containing detection results"""
    
    def __init__(self, gpu_type: GPUType, renderer: str, details: Optional[Dict] = None):
        self.gpu_type = gpu_type
        self.renderer = renderer
        self.details = details or {}

def detect_gpu(context) -> GPUInfo:
    """
    Detect GPU type from context.host_info
    
    Args:
        context: OOMOL context object with host_info
        
    Returns:
        GPUInfo: Object containing GPU type and details
    """
    gpu_renderer = context.host_info.get("gpu_renderer")
    
    if not gpu_renderer:
        return GPUInfo("UNKNOWN", "", {"error": "No GPU renderer information available"})
    
    return _parse_gpu_renderer(gpu_renderer)

def _parse_gpu_renderer(renderer: str) -> GPUInfo:
    """
    Parse GPU renderer string to determine GPU type
    
    Args:
        renderer: GPU renderer string from context.host_info
        
    Returns:
        GPUInfo: Parsed GPU information
    """
    renderer = renderer.strip()
    
    # Check for NVIDIA GPU
    if "NVIDIA" in renderer.upper():
        return _parse_nvidia_gpu(renderer)
    
    # Check for Apple M series GPU
    if "APPLE" in renderer.upper() and "M" in renderer:
        return _parse_apple_gpu(renderer)
    
    return GPUInfo("UNKNOWN", renderer, {"error": "Unknown GPU type"})

def _parse_nvidia_gpu(renderer: str) -> GPUInfo:
    """Parse NVIDIA GPU information"""
    details = {"vendor": "NVIDIA"}
    
    # Extract GPU model using regex
    # Example: ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 (0x00002216) Direct3D11 vs_5_0 ps_5_0, D3D11)
    gpu_model_match = re.search(r'NVIDIA\s+([^(]+)', renderer)
    if gpu_model_match:
        details["model"] = gpu_model_match.group(1).strip()
    
    # Extract device ID
    device_id_match = re.search(r'\(0x([0-9A-Fa-f]+)\)', renderer)
    if device_id_match:
        details["device_id"] = device_id_match.group(1)
    
    # Extract API information
    if "Direct3D11" in renderer:
        details["api"] = "Direct3D11"
    elif "OpenGL" in renderer:
        details["api"] = "OpenGL"
    
    # Extract shader versions
    shader_match = re.search(r'(vs_\d+_\d+)\s+(ps_\d+_\d+)', renderer)
    if shader_match:
        details["vertex_shader"] = shader_match.group(1)
        details["pixel_shader"] = shader_match.group(2)
    
    return GPUInfo("NVIDIA", renderer, details)

def _parse_apple_gpu(renderer: str) -> GPUInfo:
    """Parse Apple M series GPU information"""
    details = {"vendor": "Apple"}
    
    # Extract Apple M series chip
    # Example: ANGLE (Apple, ANGLE Metal Renderer: Apple M3, Unspecified Version)
    m_series_match = re.search(r'Apple\s+(M\d+(?:\s+\w+)?)', renderer, re.IGNORECASE)
    if m_series_match:
        details["chip"] = m_series_match.group(1).strip()
    
    # Check for Metal renderer
    if "Metal" in renderer:
        details["api"] = "Metal"
    
    # Extract version if available
    version_match = re.search(r'Version\)\s*(.+?)(?:,|$)', renderer)
    if version_match and "Unspecified" not in version_match.group(1):
        details["version"] = version_match.group(1).strip()
    
    return GPUInfo("APPLE_M", renderer, details)

def is_nvidia_gpu(context) -> bool:
    """Check if the GPU is NVIDIA"""
    gpu_info = detect_gpu(context)
    return gpu_info.gpu_type == "NVIDIA"

def is_apple_m_series(context) -> bool:
    """Check if the GPU is Apple M series"""
    gpu_info = detect_gpu(context)
    return gpu_info.gpu_type == "APPLE_M"

def get_gpu_vendor(context) -> str:
    """Get GPU vendor name"""
    gpu_info = detect_gpu(context)
    if gpu_info.gpu_type == "NVIDIA":
        return "NVIDIA"
    elif gpu_info.gpu_type == "APPLE_M":
        return "Apple"
    else:
        return "Unknown"

def get_gpu_model(context) -> Optional[str]:
    """Get GPU model name"""
    gpu_info = detect_gpu(context)
    if gpu_info.gpu_type == "NVIDIA":
        return gpu_info.details.get("model")
    elif gpu_info.gpu_type == "APPLE_M":
        return gpu_info.details.get("chip")
    else:
        return None