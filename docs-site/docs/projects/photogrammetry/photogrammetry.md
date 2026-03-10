# Photogrammetry Backend

## What is this?

This is a FastAPI microservice that turns a set of overlapping photos into a 3D model (`.glb` file). It uses [COLMAP](https://colmap.github.io/) (Structure from Motion) to reconstruct 3D geometry from images, then converts the sparse point cloud into a mesh using Poisson surface reconstruction via Open3D.

The whole thing runs inside a **Docker container** — a lightweight, isolated environment that packages the app along with COLMAP (compiled from source, CPU-only) and all Python dependencies. This means you don't need to install anything on your machine except Docker.

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────────────────────────────────┐
│   Frontend   │────>│         Docker Container (port 8100)     │
│  (React app) │<────│                                          │
│  :5173       │     │  FastAPI Server (uvicorn, 2 workers)     │
└─────────────┘     │    ├── /api/upload        (receive imgs) │
                     │    ├── /api/jobs          (track status) │
                     │    ├── /api/photogrammetry/run  (start)  │
                     │    └── /api/jobs/{id}/model (get .glb)   │
                     │                                          │
                     │  COLMAP Pipeline (background thread)     │
                     │    └── feature_extractor → matcher →     │
                     │        mapper → undistort                │
                     │                                          │
                     │  OpenMVS Dense Pipeline                  │
                     │    └── densify → mesh → texture → .glb   │
                     │                                          │
                     │  /app/data/                              │
                     │    ├── uploads/{job_id}/  (input images) │
                     │    ├── outputs/{job_id}/  (model.glb)    │
                     │    └── jobs.json          (job state)    │
                     └──────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [GitHub CLI](https://cli.github.com/) (`gh`) for pulling the image

### 1. Authenticate with GitHub Container Registry

```bash
# One-time setup: ensure your gh token has packages scope
gh auth refresh -h github.com -s read:packages,write:packages

# Login Docker to GHCR
echo $(gh auth token) | docker login ghcr.io -u $(gh api user -q .login) --password-stdin
```

### 2. Start the container

```bash
docker compose -f docker-compose.photogrammetry.yml up
```

This pulls the pre-built image from `ghcr.io/team-bath-hydrobotics/photogrammetry-backend:latest` and starts the server on **http://localhost:8100**.

### 3. Verify it's running

```bash
curl http://localhost:8100/api/health
# → {"status":"ok","version":"1.0.0"}
```

### 4. Stop the container

Press `Ctrl+C` in the terminal, or:

```bash
docker compose -f docker-compose.photogrammetry.yml down
```

---

## How to Test the Pipeline

### Automated test with coral reef images

The easiest way to test end-to-end. Downloads real underwater coral images from the [wildflow/sweet-corals](https://huggingface.co/datasets/wildflow/sweet-corals) HuggingFace dataset:

```bash
# Run with 15 images (default)
./photogrammetry-backend/scripts/test_coral_pipeline.sh

# Or specify a number
./photogrammetry-backend/scripts/test_coral_pipeline.sh 20
```

The script creates a job, downloads images, uploads them, starts the pipeline, and polls until completion. The output model will be saved as instructed.

### Interactive API docs

Open **http://localhost:8100/docs** in your browser — this gives you a Swagger UI where you can try every endpoint.

### Step-by-step with curl

```bash
# 1. Create a job
curl -X POST http://localhost:8100/api/jobs
# → {"id": "abc-123", "status": "PENDING", ...}

# 2. Upload images (at least 3 overlapping photos of the same object)
curl -X POST http://localhost:8100/api/upload \
  -F "job_id=abc-123" \
  -F "files=@photo1.jpg" \
  -F "files=@photo2.jpg" \
  -F "files=@photo3.jpg"

# 3. Start the photogrammetry pipeline
curl -X POST http://localhost:8100/api/photogrammetry/run \
  -H "Content-Type: application/json" \
  -d '{"job_id": "abc-123"}'
# → {"job_id": "abc-123", "status": "reconstructing"}

# 4. Poll for progress
curl http://localhost:8100/api/jobs/abc-123
# → {"id": "abc-123", "status": "RECONSTRUCTING", "progress": 45, "stage": "feature_matching", ...}
# Keep polling until status is "COMPLETE" or "error"

# 5. Download the 3D model
curl http://localhost:8100/api/jobs/abc-123/model -o model.glb
```

### Tips for good results
- Use **at least 10-20 photos** with significant overlap (60-80%)
- Shoot from different angles around the object
- Consistent lighting, avoid motion blur
- The minimum is 3 images, but more = better reconstruction
- On 8GB RAM machines, the pipeline limits images to 2000px and uses 1 thread to avoid OOM

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/jobs` | Create a new job |
| `GET` | `/api/jobs` | List all jobs |
| `GET` | `/api/jobs/{job_id}` | Get job status and progress |
| `POST` | `/api/upload` | Upload images to a job |
| `POST` | `/api/photogrammetry/run` | Start the reconstruction pipeline |
| `GET` | `/api/jobs/{job_id}/model` | Download the generated `.glb` model |
| `POST` | `/api/manual-cad/generate` | Generate a CAD model from manual measurements |
| `POST` | `/api/scaling/estimate` | Estimate scale from a reference object |

### Job Statuses

```
PENDING → RECONSTRUCTING → MESHING → EXPORTING → COMPLETE
                                                    or
                                               → error
```

The `progress` field (0-100) and `stage` field give finer-grained tracking:

| Stage | Progress | What's happening |
|-------|----------|------------------|
| `feature_extraction` | 0-15% | COLMAP extracts SIFT features from each image |
| `feature_matching` | 15-35% | Matches features between all image pairs |
| `reconstruction` | 35-55% | Solves camera positions and builds sparse 3D point cloud |
| `undistort` | 55-60% | Prepares images for dense matching |
| `convert_to_mvs` | 60-62% | Converts COLMAP model to OpenMVS format |
| `densify` | 62-80% | OpenMVS computes dense depth maps on CPU |
| `reconstruct_mesh` | 80-90% | Creates mesh surface from dense points |
| `texture_mesh` | 90-97% | Projects photos onto mesh for photorealistic texturing |
| `exporting` | 97-100% | Exports final GLB file |
| `complete` | 100% | Done — model is ready to download |

---

## How the Pipeline Works

### 1. COLMAP (Structure from Motion)

COLMAP takes overlapping images and figures out where each camera was when the photo was taken, then builds a sparse 3D point cloud:

1. **Feature Extraction** (`feature_extractor`) — finds distinctive SIFT keypoints in each image (up to 8192 per image, downscaled to max 3200px, using first_octave=-1 for finer detail)
2. **Feature Matching** (`exhaustive_matcher`) — compares every pair of images to find matching keypoints. This is O(n²) so 20 images = 190 pairs
3. **Sparse Reconstruction** (`mapper`) — uses the matches to solve for camera poses (position + orientation) and triangulate 3D points

Each stage runs as a subprocess with a 20-minute timeout. GPU is disabled (`use_gpu=0`) because the Docker image is built CPU-only for broad compatibility.

### 2. OpenMVS Dense Reconstruction

If OpenMVS is available in the Docker image (it is by default), the pipeline continues with dense reconstruction instead of using the sparse point cloud directly. This dramatically improves model quality — going from ~5k sparse points to hundreds of thousands of dense points with proper texture.

4. **Undistort Images** (`colmap image_undistorter`) — prepares images for dense matching
5. **Convert to MVS** (`InterfaceCOLMAP`) — converts the COLMAP model to OpenMVS format
6. **Densify Point Cloud** (`DensifyPointCloud`) — computes dense depth maps for each image on CPU, producing a much denser point cloud (resolution-level 2 for memory safety)
7. **Reconstruct Mesh** (`ReconstructMesh`) — creates a mesh surface from the dense points
8. **Texture Mesh** (`TextureMesh`) — projects the original photos onto the mesh surface for photorealistic texturing, exports to GLB

### 3. Fallback: Sparse Mesh Processing (Open3D + trimesh)

If OpenMVS is not available, the pipeline falls back to sparse-only meshing:

1. **PLY Export** (`model_converter`) — exports the sparse point cloud as a `.ply` file
2. **Outlier removal** — removes statistical outliers (noisy points)
3. **Downsample** — if >200k points, voxel-downsamples for memory safety
4. **Estimate normals** — calculates surface direction at each point using KDTree
5. **Poisson reconstruction** — creates a watertight mesh surface (depth 8-10 depending on point count)
6. **Density trimming** — removes the bottom 1% low-density vertices (noise)
7. **Export GLB** — saves as `.glb` via trimesh (viewable in any 3D viewer or browser)

A Google Colab notebook for GPU-accelerated dense reconstruction (using COLMAP's `patch_match_stereo` instead of OpenMVS) is also available at `scripts/colmap_dense_colab.ipynb`.

---

## Project Structure

```
photogrammetry-backend/
├── app/
│   ├── main.py                    # FastAPI app, startup, CORS, routes
│   ├── config.py                  # Settings (port, dirs, CORS origins)
│   ├── models/
│   │   └── job.py                 # Job model and status enum
│   ├── routers/
│   │   ├── photogrammetry.py      # POST /api/photogrammetry/run
│   │   ├── jobs.py                # Job CRUD endpoints
│   │   ├── upload.py              # Streaming image upload endpoint
│   │   ├── manual_cad.py          # Manual CAD generation
│   │   └── scaling.py             # Scale estimation
│   └── services/
│       ├── colmap_pipeline.py     # COLMAP SfM + OpenMVS dense reconstruction
│       ├── mesh_processor.py      # Point cloud → mesh → GLB (sparse fallback)
│       └── job_manager.py         # File-based job store with flock
├── scripts/
│   ├── test_coral_pipeline.sh     # End-to-end test with coral reef images
│   └── colmap_dense_colab.ipynb   # GPU dense reconstruction notebook
├── Dockerfile                     # Multi-stage build (compile COLMAP + runtime)
├── .dockerignore                  # Excludes data/, cache, etc from build
├── requirements.txt               # Python dependencies
└── PHOTOGRAMMETRY.md              # This file
```

---

## Docker Explained

### What is Docker?

Docker packages an application and all its dependencies into a **container** — like a lightweight virtual machine. This means:

- **"It works on my machine"** → it works everywhere
- No need to install COLMAP, Open3D, Ceres Solver, etc. on your laptop
- The container is isolated from your system

### Key concepts

| Concept | What it is |
|---------|------------|
| **Image** | A snapshot of the app + dependencies (like a template) |
| **Container** | A running instance of an image |
| **Volume** | Persistent storage that survives container restarts |
| **GHCR** | GitHub Container Registry — where our image is stored |
| **docker compose** | Tool to define and run multi-container apps with a YAML file |

### Our Docker setup

The Dockerfile uses a **multi-stage build**:

1. **Builder stage** (Ubuntu 22.04) — installs build dependencies (cmake, Boost, Eigen, Ceres, OpenCV, etc.), then compiles both **COLMAP 3.9.1** (CPU-only, `-DCUDA_ENABLED=OFF`) and **OpenMVS v2.3.0** (CPU-only, `-DOpenMVS_USE_CUDA=OFF`) from source
2. **Runtime stage** (Ubuntu 22.04) — installs only runtime libraries, copies the compiled COLMAP and OpenMVS binaries from the builder, installs Python deps, copies the app

The image is built in the cloud via **GitHub Actions** because compiling COLMAP from source needs significant RAM and time (~1 hour for multi-arch). The image supports both `linux/amd64` and `linux/arm64`.

- Image: `ghcr.io/team-bath-hydrobotics/photogrammetry-backend`
- Volume: `photogrammetry-data` persists uploaded images and output models
- Port: `8100` inside the container → `8100` on your machine
- Workers: 2 uvicorn workers (one can serve API requests while the other runs reconstruction)

### Useful Docker commands

```bash
# Start the service
docker compose -f docker-compose.photogrammetry.yml up

# Start in background (detached)
docker compose -f docker-compose.photogrammetry.yml up -d

# View logs when running in background
docker compose -f docker-compose.photogrammetry.yml logs -f

# Stop the service
docker compose -f docker-compose.photogrammetry.yml down

# Pull the latest image
docker pull ghcr.io/team-bath-hydrobotics/photogrammetry-backend:latest

# See running containers
docker ps

# Shell into the running container (for debugging)
docker exec -it team-bath-rov-software-photogrammetry-backend-1 bash

# Check container memory usage
docker stats --no-stream
```

---

## CI/CD: Automatic Image Builds

The Docker image is automatically rebuilt when any file in `photogrammetry-backend/` changes on push, via GitHub Actions (`.github/workflows/build-photogrammetry.yml`).

The build:
- Triggers on push to `photogrammetry-backend/**` or manual dispatch
- Uses QEMU + buildx for multi-arch (`linux/amd64` + `linux/arm64`)
- Pushes to `ghcr.io/team-bath-hydrobotics/photogrammetry-backend`
- Tags with both `latest` and the commit SHA

You can also trigger a build manually:
1. Go to **Actions** → **Build Photogrammetry Backend** → **Run workflow**

---

## Troubleshooting

### "unauthorized" when pulling the image
```bash
gh auth refresh -h github.com -s read:packages,write:packages
echo $(gh auth token) | docker login ghcr.io -u $(gh api user -q .login) --password-stdin
```

### Container won't start / port already in use
```bash
lsof -i :8100
# Kill the process, or change the port in docker-compose.photogrammetry.yml
```

### Pipeline fails with "not enough images"
You need at least 3 images. For good results, use 10-20 with lots of overlap.

### Docker Desktop crashes / won't reopen (macOS)
If Docker becomes unresponsive (often from OOM during reconstruction):
1. Quit Docker Desktop
2. Kill lingering processes: `killall com.docker.backend com.docker.build com.docker.virtualization docker`
3. If that's not enough: `rm -rf ~/Library/Containers/com.docker.docker/Data/vms/0/data` (this resets Docker's VM disk — containers/images will need to be re-pulled)
4. Reopen Docker Desktop

### Pipeline fails at "feature_extraction" with memory warning
COLMAP's SIFT extraction can use a lot of RAM. The pipeline is configured for 8GB machines with conservative settings (1 thread, 2000px max, first_octave=0). If you still get OOM, reduce `max_image_size` in `colmap_pipeline.py`.

### Pipeline fails at "meshing"
The mesh processor may run out of memory on large point clouds. It automatically downsamples if >50k points and uses Poisson depth 8-9 depending on point count.

### Job state not updating / workers out of sync
Jobs are stored in `data/jobs.json` with file locking (`fcntl.flock`). If the file gets corrupted, delete it and restart: `docker exec <container> rm /app/data/jobs.json`
