import os
import urllib.request

def download_model(url, output_path):
    if os.path.exists(output_path):
        print(f"Model already exists at {output_path}")
        return

    print(f"Downloading model from {url}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"Download complete: {output_path}")
    except Exception as e:
        print(f"Error downloading model: {e}")

if __name__ == "__main__":
    # Real-ESRGAN x4plus model URL
    model_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
    save_path = os.path.join("models", "RealESRGAN_x4plus.pth")
    
    download_model(model_url, save_path)
    
    # You can add more models here if needed
