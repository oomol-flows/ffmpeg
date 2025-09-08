from typing import Dict, Optional, Any, Literal
from .gpu_detector import detect_gpu
import ffmpeg

EncodingProfile = Literal["fast", "balanced", "quality"]
VideoCodec = Literal["h264", "h265", "av1"]

class FFmpegEncoder:
    """GPU-aware FFmpeg encoding utility"""
    
    def __init__(self, context):
        self.context = context
        self.gpu_info = detect_gpu(context)
        self._initialize_codec_support()
    
    def _initialize_codec_support(self):
        """Initialize supported codecs based on GPU type"""
        self.supported_codecs = {
            "NVIDIA": {
                "h264": ["h264_nvenc", "libx264"],
                "h265": ["hevc_nvenc", "libx265"], 
                "av1": ["av1_nvenc", "libaom-av1"]
            },
            "APPLE_M": {
                "h264": ["h264_videotoolbox", "libx264"],
                "h265": ["hevc_videotoolbox", "libx265"],
                "av1": ["libsvtav1", "libaom-av1"]
            },
            "UNKNOWN": {
                "h264": ["libx264"],
                "h265": ["libx265"],
                "av1": ["libsvtav1", "libaom-av1"]
            }
        }
    
    def get_optimal_video_codec(self, codec_type: VideoCodec = "h264") -> str:
        """Get optimal video codec based on GPU"""
        codecs = self.supported_codecs.get(self.gpu_info.gpu_type, self.supported_codecs["UNKNOWN"])
        return codecs.get(codec_type, ["libx264"])[0]
    
    def get_encoding_options(self, codec_type: VideoCodec = "h264", profile: EncodingProfile = "balanced") -> Dict[str, Any]:
        """Get encoding options optimized for GPU"""
        optimal_codec = self.get_optimal_video_codec(codec_type)
        
        # Base options
        options = {
            'vcodec': optimal_codec,
            'acodec': 'aac'
        }
        
        # GPU-specific encoding options
        if self.gpu_info.gpu_type == "NVIDIA" and optimal_codec.endswith("_nvenc"):
            options.update(self._get_nvidia_options(optimal_codec, profile))
        elif self.gpu_info.gpu_type == "APPLE_M" and optimal_codec.endswith("_videotoolbox"):
            options.update(self._get_apple_options(optimal_codec, profile))
        else:
            options.update(self._get_software_options(optimal_codec, profile))
        
        return options
    
    def _get_nvidia_options(self, codec: str, profile: EncodingProfile) -> Dict[str, Any]:
        """NVIDIA GPU encoding options"""
        base_options = {
            'gpu': 0,
            'rc': 'vbr'  # Variable bitrate
        }
        
        if codec == "h264_nvenc":
            if profile == "fast":
                base_options.update({
                    'preset': 'fast',
                    'profile': 'high',
                    'cq': 28
                })
            elif profile == "balanced":
                base_options.update({
                    'preset': 'medium', 
                    'profile': 'high',
                    'cq': 23
                })
            else:  # quality
                base_options.update({
                    'preset': 'slow',
                    'profile': 'high',
                    'cq': 18
                })
        
        elif codec == "hevc_nvenc":
            if profile == "fast":
                base_options.update({
                    'preset': 'fast',
                    'profile': 'main',
                    'cq': 28
                })
            elif profile == "balanced":
                base_options.update({
                    'preset': 'medium',
                    'profile': 'main', 
                    'cq': 23
                })
            else:  # quality
                base_options.update({
                    'preset': 'slow',
                    'profile': 'main',
                    'cq': 18
                })
        
        return base_options
    
    def _get_apple_options(self, codec: str, profile: EncodingProfile) -> Dict[str, Any]:
        """Apple VideoToolbox encoding options"""
        base_options = {
            'allow_sw': 1,  # Allow fallback to software if needed
            'realtime': 0   # Disable realtime for better quality
        }
        
        if codec == "h264_videotoolbox":
            if profile == "fast":
                base_options.update({
                    'profile': 'high',
                    'q': 70
                })
            elif profile == "balanced":
                base_options.update({
                    'profile': 'high',
                    'q': 60
                })
            else:  # quality
                base_options.update({
                    'profile': 'high',
                    'q': 50
                })
        
        elif codec == "hevc_videotoolbox":
            if profile == "fast":
                base_options.update({
                    'profile': 'main',
                    'q': 70
                })
            elif profile == "balanced":
                base_options.update({
                    'profile': 'main',
                    'q': 60
                })
            else:  # quality
                base_options.update({
                    'profile': 'main',
                    'q': 50
                })
        
        return base_options
    
    def _get_software_options(self, codec: str, profile: EncodingProfile) -> Dict[str, Any]:
        """Software encoding options (fallback)"""
        base_options = {}
        
        if codec == "libx264":
            if profile == "fast":
                base_options.update({
                    'preset': 'veryfast',
                    'crf': 28
                })
            elif profile == "balanced":
                base_options.update({
                    'preset': 'medium',
                    'crf': 23
                })
            else:  # quality
                base_options.update({
                    'preset': 'slow',
                    'crf': 18
                })
        
        elif codec == "libx265":
            if profile == "fast":
                base_options.update({
                    'preset': 'fast',
                    'crf': 28
                })
            elif profile == "balanced":
                base_options.update({
                    'preset': 'medium',
                    'crf': 23
                })
            else:  # quality
                base_options.update({
                    'preset': 'slow',
                    'crf': 18
                })
        
        return base_options
    
    def create_encoding_stream(self, 
                             input_stream, 
                             output_path: str,
                             codec_type: VideoCodec = "h264",
                             profile: EncodingProfile = "balanced",
                             custom_options: Optional[Dict[str, Any]] = None) -> Any:
        """Create FFmpeg output stream with optimal encoding settings"""
        
        # Get base encoding options
        encoding_options = self.get_encoding_options(codec_type, profile)
        
        # Apply custom options if provided
        if custom_options:
            encoding_options.update(custom_options)
        
        # Create output stream
        return ffmpeg.output(input_stream, output_path, **encoding_options)
    
    def get_codec_info(self) -> Dict[str, Any]:
        """Get information about selected codecs and GPU"""
        return {
            "gpu_type": self.gpu_info.gpu_type,
            "gpu_details": self.gpu_info.details,
            "recommended_h264": self.get_optimal_video_codec("h264"),
            "recommended_h265": self.get_optimal_video_codec("h265"),
            "recommended_av1": self.get_optimal_video_codec("av1")
        }
    
    def encode_video(self,
                    input_path: str,
                    output_path: str,
                    codec_type: VideoCodec = "h264",
                    profile: EncodingProfile = "balanced",
                    custom_options: Optional[Dict[str, Any]] = None,
                    quiet: bool = True) -> str:
        """Encode video with GPU-optimized settings"""
        
        try:
            # Create input stream
            input_stream = ffmpeg.input(input_path)
            
            # Create output stream with optimal settings
            output_stream = self.create_encoding_stream(
                input_stream, output_path, codec_type, profile, custom_options
            )
            
            # Run encoding
            ffmpeg.run(output_stream, overwrite_output=True, quiet=quiet)
            
            return output_path
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            raise Exception(f"FFmpeg encoding error: {error_msg}")
        except Exception as e:
            raise Exception(f"Encoding error: {str(e)}")

def create_encoder(context) -> FFmpegEncoder:
    """Factory function to create encoder instance"""
    return FFmpegEncoder(context)

def get_recommended_settings(context) -> Dict[str, Any]:
    """Get recommended encoding settings for current GPU"""
    encoder = FFmpegEncoder(context)
    return encoder.get_codec_info()