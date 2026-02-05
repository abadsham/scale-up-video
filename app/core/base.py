from abc import ABC, abstractmethod
import cv2

class BaseUpscaler(ABC):
    def __init__(self, scale_factor: int):
        self.scale_factor = scale_factor

    @abstractmethod
    def upscale(self, frame_path: str, output_path: str):
        """Upscale a single frame image."""
        pass

class OpenCVUpscaler(BaseUpscaler):
    """Fallback upscaler using OpenCV's bicubic interpolation."""
    def upscale(self, frame_path: str, output_path: str):
        frame = cv2.imread(frame_path)
        if frame is None:
            raise ValueError(f"Could not read frame: {frame_path}")
        
        height, width = frame.shape[:2]
        new_size = (width * self.scale_factor, height * self.scale_factor)
        
        upscaled = cv2.resize(frame, new_size, interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(output_path, upscaled)
