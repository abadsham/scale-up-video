import os
import sys
from dotenv import load_dotenv
from app.core.pipeline import UpscalePipeline

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m app.main <path_to_video>")
        sys.exit(1)

    video_input = sys.argv[1]
    if not os.path.exists(video_input):
        print(f"Error: File {video_input} not found.")
        sys.exit(1)

    # Load configuration into environment
    load_dotenv()
    
    # Ensure folder config for pipeline
    config = {
        "SCALE_FACTOR": os.getenv("SCALE_FACTOR", "2"),
        "UPLOAD_DIR": os.getenv("UPLOAD_DIR", "storage/uploads"),
        "OUTPUT_DIR": os.getenv("OUTPUT_DIR", "storage/outputs"),
        "TEMP_DIR": os.getenv("TEMP_DIR", "storage/temp"),
        "USE_AI": os.getenv("USE_AI", "True")
    }
    
    # Ensure directories exist
    for key in ["UPLOAD_DIR", "OUTPUT_DIR", "TEMP_DIR"]:
        os.makedirs(config[key], exist_ok=True)

    try:
        pipeline = UpscalePipeline(config)
        result = pipeline.process(video_input)
        
        print("\n--- Upscaling Complete ---")
        print(f"Output saved to: {result['output_path']}")
        print(f"New Resolution: {result['new_resolution']}")
        print(f"Processing Time: {result['process_duration_sec']} seconds")
        print(f"Final File Size: {result['filesize'] / (1024*1024):.2f} MB")
        
    except Exception as e:
        print(f"\nAn error occurred during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
