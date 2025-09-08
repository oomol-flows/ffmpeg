"""
Test script for FFmpeg encoder utility
"""

import sys
sys.path.append('/app/workspace')
from utils.ffmpeg_encoder import create_encoder
from utils.gpu_detector import detect_gpu

class MockContext:
    """Mock context for testing"""
    def __init__(self, gpu_renderer):
        self.host_info = {"gpu_renderer": gpu_renderer}

def test_encoder_selection():
    """Test encoder selection based on different GPU types"""
    
    # Test NVIDIA GPU
    print("=== NVIDIA GPU Encoder Test ===")
    nvidia_context = MockContext("ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 (0x00002216) Direct3D11 vs_5_0 ps_5_0, D3D11)")
    nvidia_encoder = create_encoder(nvidia_context)
    
    gpu_info = detect_gpu(nvidia_context)
    print(f"GPU Type: {gpu_info.gpu_type}")
    print(f"Optimal H.264 Codec: {nvidia_encoder.get_optimal_video_codec('h264')}")
    print(f"Optimal H.265 Codec: {nvidia_encoder.get_optimal_video_codec('h265')}")
    
    # Test encoding options
    fast_options = nvidia_encoder.get_encoding_options("h264", "fast")
    balanced_options = nvidia_encoder.get_encoding_options("h264", "balanced")
    quality_options = nvidia_encoder.get_encoding_options("h264", "quality")
    
    print(f"Fast encoding options: {fast_options}")
    print(f"Balanced encoding options: {balanced_options}")
    print(f"Quality encoding options: {quality_options}")
    print()
    
    # Test Apple M3 GPU
    print("=== Apple M3 GPU Encoder Test ===")
    apple_context = MockContext("ANGLE (Apple, ANGLE Metal Renderer: Apple M3, Unspecified Version)")
    apple_encoder = create_encoder(apple_context)
    
    gpu_info = detect_gpu(apple_context)
    print(f"GPU Type: {gpu_info.gpu_type}")
    print(f"Optimal H.264 Codec: {apple_encoder.get_optimal_video_codec('h264')}")
    print(f"Optimal H.265 Codec: {apple_encoder.get_optimal_video_codec('h265')}")
    
    # Test encoding options
    apple_options = apple_encoder.get_encoding_options("h264", "balanced")
    print(f"Apple H.264 options: {apple_options}")
    print()
    
    # Test Unknown GPU (Software fallback)
    print("=== Unknown GPU Encoder Test (Software Fallback) ===")
    unknown_context = MockContext("Some Unknown GPU Renderer")
    unknown_encoder = create_encoder(unknown_context)
    
    gpu_info = detect_gpu(unknown_context)
    print(f"GPU Type: {gpu_info.gpu_type}")
    print(f"Optimal H.264 Codec: {unknown_encoder.get_optimal_video_codec('h264')}")
    print(f"Optimal H.265 Codec: {unknown_encoder.get_optimal_video_codec('h265')}")
    
    # Test encoding options
    software_options = unknown_encoder.get_encoding_options("h264", "balanced")
    print(f"Software H.264 options: {software_options}")
    print()
    
    # Test codec info summary
    print("=== Codec Info Summary ===")
    for context_name, context in [("NVIDIA", nvidia_context), ("Apple M3", apple_context), ("Unknown", unknown_context)]:
        encoder = create_encoder(context)
        info = encoder.get_codec_info()
        print(f"{context_name} GPU:")
        print(f"  GPU Type: {info['gpu_type']}")
        print(f"  Recommended H.264: {info['recommended_h264']}")
        print(f"  Recommended H.265: {info['recommended_h265']}")
        print(f"  Recommended AV1: {info['recommended_av1']}")
        print()

if __name__ == "__main__":
    test_encoder_selection()