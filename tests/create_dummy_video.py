import cv2
import numpy as np
import os

def create_test_video(output_path, duration_sec=2, fps=24, resolution=(320, 240)):
    """Creates a simple test video with a bouncing square."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, resolution)
    
    width, height = resolution
    square_size = 50
    x, y = 0, 0
    dx, dy = 5, 5
    
    num_frames = duration_sec * fps
    
    for i in range(num_frames):
        # Create a solid background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = [50, 50, 50] # Dark grey
        
        # Draw a bouncing square
        cv2.rectangle(frame, (x, y), (x + square_size, y + square_size), (0, 255, 0), -1)
        
        # Add frame index text
        cv2.putText(frame, f"Frame: {i}", (10, height - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        out.write(frame)
        
        # Move square
        x += dx
        y += dy
        
        # Bounce logic
        if x <= 0 or x + square_size >= width: dx = -dx
        if y <= 0 or y + square_size >= height: dy = -dy
        
    out.release()
    print(f"Test video created: {output_path}")

if __name__ == "__main__":
    os.makedirs("tests/data", exist_ok=True)
    create_test_video("tests/data/test_input.mp4")
