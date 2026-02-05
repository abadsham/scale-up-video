import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from app.core.pipeline import UpscalePipeline

# Load configuration
load_dotenv()

app = FastAPI(title="Video Upscaler AI")

# Configuration
CONFIG = {
    "SCALE_FACTOR": os.getenv("SCALE_FACTOR", "2"),
    "UPLOAD_DIR": os.getenv("UPLOAD_DIR", "storage/uploads"),
    "OUTPUT_DIR": os.getenv("OUTPUT_DIR", "storage/outputs"),
    "TEMP_DIR": os.getenv("TEMP_DIR", "storage/temp"),
    "USE_AI": os.getenv("USE_AI", "True")
}

# Ensure directories exist
for key in ["UPLOAD_DIR", "OUTPUT_DIR", "TEMP_DIR"]:
    os.makedirs(CONFIG[key], exist_ok=True)

# Templates and Static Files
templates = Jinja2Templates(directory="app/templates")
# Mount output directory to serve processed videos
app.mount("/outputs", StaticFiles(directory=CONFIG["OUTPUT_DIR"]), name="outputs")

# In-memory task tracking (for simplicity)
tasks = {}

def process_video_task(task_id: str, input_path: str, scale: int, use_ai: bool):
    try:
        # Override config for this specific task
        task_config = CONFIG.copy()
        task_config["SCALE_FACTOR"] = str(scale)
        task_config["USE_AI"] = str(use_ai)
        
        pipeline = UpscalePipeline(task_config)
        result = pipeline.process(input_path)
        tasks[task_id] = {
            "status": "completed",
            "result": result
        }
    except Exception as e:
        tasks[task_id] = {
            "status": "failed",
            "error": str(e)
        }
    finally:
        # Optionally cleanup upload file after processing
        # if os.path.exists(input_path):
        #     os.remove(input_path)
        pass

@app.get("/")
async def index(request: Request):
    # List existing outputs for the gallery
    outputs = []
    if os.path.exists(CONFIG["OUTPUT_DIR"]):
        for f in os.listdir(CONFIG["OUTPUT_DIR"]):
            if f.endswith(".mp4"):
                outputs.append({
                    "name": f,
                    "url": f"/outputs/{f}"
                })
    return templates.TemplateResponse("index.html", {"request": request, "outputs": outputs})

@app.post("/upscale")
async def upscale_video(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    scale: int = 2,
    use_ai: bool = True
):
    if not file.filename:
        return JSONResponse(status_code=400, content={"error": "No file uploaded"})
    
    task_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    input_path = os.path.join(CONFIG["UPLOAD_DIR"], f"{task_id}{file_ext}")
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    tasks[task_id] = {
        "status": "processing", 
        "filename": file.filename,
        "config": {"scale": scale, "use_ai": use_ai}
    }
    background_tasks.add_task(process_video_task, task_id, input_path, scale, use_ai)
    
    return {"task_id": task_id, "status": "processing"}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return tasks[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
