import os
import shutil
import time
from tqdm import tqdm
from ..utils.ffmpeg import FFmpegRunner
from .base import OpenCVUpscaler

class UpscalePipeline:
    def __init__(self, config):
        self.config = config
        self.ffmpeg = FFmpegRunner()
        
        scale = int(config.get("SCALE_FACTOR", 2))
        use_ai = config.get("USE_AI", "True").lower() == "true"
        
        if use_ai:
            print("Initializing AI Upscaler (Real-ESRGAN)...")
            try:
                from .ai_upscaler import AIUpscaler
                self.upscaler = AIUpscaler(scale_factor=scale)
            except Exception as e:
                print(f"Failed to load AI model/dependencies: {e}. Falling back to OpenCV.")
                self.upscaler = OpenCVUpscaler(scale_factor=scale)
        else:
            print("Using OpenCV Upscaler (Bicubic)...")
            self.upscaler = OpenCVUpscaler(scale_factor=scale)

    def process(self, video_path):
        """Run the full upscaling pipeline."""
        start_time = time.time()
        
        # 1. Get Metadata
        print(f"Extracting metadata for {video_path}...")
        meta = self.ffmpeg.get_video_metadata(video_path)
        print(f"Original Resolution: {meta['width']}x{meta['height']} | FPS: {meta['fps']}")

        # 2. Setup Temp Dirs
        video_id = os.path.splitext(os.path.basename(video_path))[0]
        extraction_dir = os.path.join(self.config["TEMP_DIR"], f"{video_id}_input")
        processed_dir = os.path.join(self.config["TEMP_DIR"], f"{video_id}_output")
        
        os.makedirs(extraction_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)

        try:
            # 3. Extract Frames
            print("Extracting frames...")
            self.ffmpeg.extract_frames(video_path, extraction_dir)
            
            frames = sorted([f for f in os.listdir(extraction_dir) if f.endswith('.png')])
            print(f"Extracted {len(frames)} frames.")

            # 4. Upscale Frames
            print(f"Upscaling frames (Scale: {self.upscaler.scale_factor}x)...")
            for frame_name in tqdm(frames, desc="Upscaling"):
                input_frame = os.path.join(extraction_dir, frame_name)
                output_frame = os.path.join(processed_dir, frame_name)
                self.upscaler.upscale(input_frame, output_frame)

            # 5. Assemble Video
            output_filename = f"{video_id}_upscaled_{self.upscaler.scale_factor}x.mp4"
            output_path = os.path.join(self.config["OUTPUT_DIR"], output_filename)
            
            print("Assembling video...")
            self.ffmpeg.assemble_video(
                processed_dir, 
                video_path, 
                output_path, 
                fps=meta['fps']
            )

            end_time = time.time()
            duration = end_time - start_time
            
            # 6. Return Metadata for output
            final_meta = self.ffmpeg.get_video_metadata(output_path)
            return {
                "status": "success",
                "output_path": output_path,
                "process_duration_sec": round(duration, 2),
                "original_resolution": f"{meta['width']}x{meta['height']}",
                "new_resolution": f"{final_meta['width']}x{final_meta['height']}",
                "filesize": final_meta['filesize']
            }

        finally:
            # 7. Cleanup
            print("Cleaning up temporary files...")
            shutil.rmtree(extraction_dir, ignore_errors=True)
            shutil.rmtree(processed_dir, ignore_errors=True)
