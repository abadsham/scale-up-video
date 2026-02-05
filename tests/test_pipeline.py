import unittest
import os
import shutil
from dotenv import dotenv_values
from app.core.pipeline import UpscalePipeline
from tests.create_dummy_video import create_test_video

class TestVideoUpscaling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configuration for tests
        cls.config = {
            "SCALE_FACTOR": "2",
            "UPLOAD_DIR": "tests/storage/uploads",
            "OUTPUT_DIR": "tests/storage/outputs",
            "TEMP_DIR": "tests/storage/temp",
            "USE_AI": "False" # Use OpenCV for faster testing without model downloads
        }
        
        # Ensure directories exist
        for key in ["UPLOAD_DIR", "OUTPUT_DIR", "TEMP_DIR"]:
            os.makedirs(cls.config[key], exist_ok=True)
            
        # Set environment variables for FFmpeg if found in .env
        from dotenv import load_dotenv
        load_dotenv()
            
        cls.test_input = "tests/data/test_input.mp4"
        os.makedirs("tests/data", exist_ok=True)
        create_test_video(cls.test_input)
        
        cls.pipeline = UpscalePipeline(cls.config)

    @classmethod
    def tearDownClass(cls):
        # Cleanup test files
        shutil.rmtree("tests/storage", ignore_errors=True)
        shutil.rmtree("tests/data", ignore_errors=True)

    def test_metadata_extraction(self):
        """Test if metadata extraction works correctly."""
        try:
            meta = self.pipeline.ffmpeg.get_video_metadata(self.test_input)
            self.assertEqual(meta['width'], 320)
            self.assertEqual(meta['height'], 240)
            self.assertGreater(meta['duration'], 0)
        except Exception as e:
            self.fail(f"Metadata extraction failed: {e}. Ensure ffprobe is installed.")

    def test_full_pipeline_opencv(self):
        """Test the full pipeline using OpenCV fallback."""
        try:
            result = self.pipeline.process(self.test_input)
            
            self.assertEqual(result['status'], 'success')
            self.assertTrue(os.path.exists(result['output_path']))
            self.assertEqual(result['new_resolution'], "640x480") # 320x240 * 2
            
            # Verify temporary files were cleaned up
            video_id = os.path.splitext(os.path.basename(self.test_input))[0]
            self.assertFalse(os.path.exists(os.path.join(self.config["TEMP_DIR"], f"{video_id}_input")))
            self.assertFalse(os.path.exists(os.path.join(self.config["TEMP_DIR"], f"{video_id}_output")))
            
        except Exception as e:
            self.fail(f"Pipeline processing failed: {e}. Ensure ffmpeg is installed.")

if __name__ == "__main__":
    unittest.main()
