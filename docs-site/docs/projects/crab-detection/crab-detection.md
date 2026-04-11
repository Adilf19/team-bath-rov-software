
## What is this?

This is a FastAPI microservice for **MATE 2026 Task 2.1** (Mitigate invasive species) that runs model inference to detect european green crabs and returns a count, detections (bounding boxes) and a post processed frame with canvas overlays of bounding boxes and count.

3 models are available namely yolov8, YOLO and rf-detr.

## Running the api
You'll need to follow the steps in both the crab_detection folder in the software repo + the steps to run the secondary ui in it's repo.

## Model training
Documentation for how to train the model can be found in the crab-detection folder of the software repo.