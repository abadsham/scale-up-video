import torch
import cv2
import os
import numpy as np
from spandrel import ModelLoader, ImageModelDescriptor
from .base import BaseUpscaler

class AIUpscaler(BaseUpscaler):
    """AI-based upscaler using Spandrel (supports Real-ESRGAN models)."""
    def __init__(self, scale_factor: int, model_path=None):
        super().__init__(scale_factor)
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Default model path if not provided
        if model_path is None:
            model_path = os.path.join("models", "RealESRGAN_x4plus.pth")
        
        self.model_path = model_path
        self.model = None
        
        if os.path.exists(model_path):
            self._load_model()
        else:
            print(f"Warning: Model file not found at {model_path}. AI upscaling will fallback to OpenCV until the model is downloaded.")

    def _load_model(self):
        """Load the model using Spandrel."""
        try:
            loader = ModelLoader()
            self.model = loader.load_from_file(self.model_path)
            self.model.to(self.device)
            self.model.eval()
            print(f"Loaded AI model from {self.model_path}")
        except Exception as e:
            print(f"Failed to load model with Spandrel: {e}")
            self.model = None

    def upscale(self, frame_path: str, output_path: str):
        img = cv2.imread(frame_path)
        if img is None:
            raise ValueError(f"Could not read frame: {frame_path}")

        if self.model is None:
            # Fallback to OpenCV if model not loaded
            self._opencv_fallback(img, output_path)
            return

        try:
            # Convert BGR to RGB and to tensor
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_tensor = torch.from_numpy(img_rgb).permute(2, 0, 1).float().divide(255).unsqueeze(0).to(self.device)

            with torch.no_grad():
                # Spandrel models handle the forward pass
                output_tensor = self.model(img_tensor)
                
                # Convert back to numpy/BGR
                output_img = output_tensor.squeeze(0).permute(1, 2, 0).cpu().clamp(0, 1).numpy()
                output_img = (output_img * 255).astype(np.uint8)
                output_img = cv2.cvtColor(output_img, cv2.COLOR_RGB2BGR)
                
                # Resize to exact scale factor if model output differs (Real-ESRGAN x4 usually outputs 4x)
                if self.scale_factor != 4:
                    h, w = img.shape[:2]
                    target_size = (w * self.scale_factor, h * self.scale_factor)
                    output_img = cv2.resize(output_img, target_size, interpolation=cv2.INTER_LANCZOS4)
                
                cv2.imwrite(output_path, output_img)
                
        except Exception as e:
            print(f"AI Upscaling failed: {e}. Falling back to OpenCV.")
            self._opencv_fallback(img, output_path)

    def _opencv_fallback(self, img, output_path):
        height, width = img.shape[:2]
        new_size = (width * self.scale_factor, height * self.scale_factor)
        upscaled = cv2.resize(img, new_size, interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(output_path, upscaled)
