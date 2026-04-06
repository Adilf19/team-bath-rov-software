from fastapi import FastAPI
from pydantic import BaseModel
import base64
import numpy as np
import cv2

from src.pipeline import CrabPipeline

app = FastAPI()

pipeline = CrabPipeline(model_type="yolov8")

class FrameRequest(BaseModel):
    image: str

@app.get("/model")
def model_info():
    return {
        "model_name": "crab_detector",
        "model_version": "0.1",
        "framework": "pytorch"
    }

@app.post("/detect")
def detect(request: FrameRequest):
    image_bytes = base64.b64decode(request.image)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    processed, count, results = pipeline.process_frame(frame)

    detections = []

    return {
        "detections": detections,
        "count": count
    }
