"""
Test script for GPU detector utility
"""

from gpu_detector import detect_gpu, is_nvidia_gpu, is_apple_m_series, get_gpu_vendor, get_gpu_model

class MockContext:
    """Mock context for testing"""
    def __init__(self, gpu_renderer):
        self.host_info = {"gpu_renderer": gpu_renderer}

def test_gpu_detection():
    """Test GPU detection with sample data"""
    
    # Test NVIDIA GPU
    nvidia_renderer = "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 (0x00002216) Direct3D11 vs_5_0 ps_5_0, D3D11)"
    nvidia_context = MockContext(nvidia_renderer)
    
    print("=== NVIDIA GPU Test ===")
    nvidia_info = detect_gpu(nvidia_context)
    print(f"GPU Type: {nvidia_info.gpu_type}")
    print(f"Renderer: {nvidia_info.renderer}")
    print(f"Details: {nvidia_info.details}")
    print(f"Is NVIDIA: {is_nvidia_gpu(nvidia_context)}")
    print(f"Is Apple M: {is_apple_m_series(nvidia_context)}")
    print(f"Vendor: {get_gpu_vendor(nvidia_context)}")
    print(f"Model: {get_gpu_model(nvidia_context)}")
    print()
    
    # Test Apple M3 GPU
    apple_renderer = "ANGLE (Apple, ANGLE Metal Renderer: Apple M3, Unspecified Version)"
    apple_context = MockContext(apple_renderer)
    
    print("=== Apple M3 GPU Test ===")
    apple_info = detect_gpu(apple_context)
    print(f"GPU Type: {apple_info.gpu_type}")
    print(f"Renderer: {apple_info.renderer}")
    print(f"Details: {apple_info.details}")
    print(f"Is NVIDIA: {is_nvidia_gpu(apple_context)}")
    print(f"Is Apple M: {is_apple_m_series(apple_context)}")
    print(f"Vendor: {get_gpu_vendor(apple_context)}")
    print(f"Model: {get_gpu_model(apple_context)}")
    print()
    
    # Test unknown GPU
    unknown_context = MockContext("Some Unknown GPU Renderer")
    
    print("=== Unknown GPU Test ===")
    unknown_info = detect_gpu(unknown_context)
    print(f"GPU Type: {unknown_info.gpu_type}")
    print(f"Renderer: {unknown_info.renderer}")
    print(f"Details: {unknown_info.details}")
    print(f"Vendor: {get_gpu_vendor(unknown_context)}")
    print()
    
    # Test no GPU info
    no_gpu_context = MockContext(None)
    
    print("=== No GPU Info Test ===")
    no_gpu_info = detect_gpu(no_gpu_context)
    print(f"GPU Type: {no_gpu_info.gpu_type}")
    print(f"Details: {no_gpu_info.details}")

if __name__ == "__main__":
    test_gpu_detection()