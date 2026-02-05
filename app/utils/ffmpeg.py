import subprocess
import json
import os
import shutil

class FFmpegRunner:
    def __init__(self, ffmpeg_path=None, ffprobe_path=None):
        self.ffmpeg = ffmpeg_path or os.getenv("FFMPEG_PATH", "ffmpeg")
        self.ffprobe = ffprobe_path or os.getenv("FFPROBE_PATH", "ffprobe")

    def get_video_metadata(self, video_path):
        """Extract metadata using ffprobe."""
        cmd = [
            self.ffprobe, 
            "-v", "quiet", 
            "-print_format", "json", 
            "-show_format", 
            "-show_streams", 
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFprobe failed: {result.stderr}")
        
        data = json.loads(result.stdout)
        video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
        
        if not video_stream:
            raise ValueError("No video stream found in file.")

        return {
            "width": int(video_stream['width']),
            "height": int(video_stream['height']),
            "fps": eval(video_stream['avg_frame_rate']),
            "duration": float(data['format']['duration']),
            "filesize": int(data['format']['size']),
            "codec": video_stream['codec_name']
        }

    def extract_frames(self, video_path, output_dir):
        """Extract all frames from video to a directory."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        cmd = [
            self.ffmpeg,
            "-i", video_path,
            "-vsync", "0",
            os.path.join(output_dir, "frame_%06d.png")
        ]
        subprocess.run(cmd, check=True)

    def assemble_video(self, frames_dir, audio_path, output_path, fps, codec="libx264"):
        """Merge upscaled frames and original audio into a final video.
        
        Args:
            frames_dir: Directory containing the upscaled PNG frames.
            audio_path: Path to the original video (to source audio from).
            output_path: Final output MP4 path.
            fps: Frame rate for the output video.
            codec: Video codec to use (libx264 or libx265).
        """
        cmd = [
            self.ffmpeg,
            "-y", # Overwrite output
            "-framerate", str(fps),
            "-i", os.path.join(frames_dir, "frame_%06d.png"),
            "-i", audio_path,
            "-c:v", codec,
            "-pix_fmt", "yuv420p",
            "-c:a", "copy", # Copy original audio
            "-map", "0:v:0", # Use video from first input
            "-map", "1:a:0?", # Use audio from second input (optional if no audio)
            "-shortest", 
            output_path
        ]
        subprocess.run(cmd, check=True)
