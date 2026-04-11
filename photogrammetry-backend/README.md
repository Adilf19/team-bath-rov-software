# Photogrammetry Backend

FastAPI service for 3D coral reef reconstruction — **MATE 2026 Task 1.2** (Coral Garden Ridge Modelling). Takes uploaded images of coral gardens and produces 3D `.glb` models using COLMAP (sparse SfM) + OpenMVS (dense reconstruction).

The competition flow: pilot measures length → judge gives true length → system scales the 3D model → estimates height. See the [Pilot Operations Guide](../../docs-site/docs/projects/photogrammetry/pilot-operations-guide.md) for the full procedure.

## Prerequisites

- Python 3.11+

## Install & Run

```bash
cd photogrammetry-backend
pip install -e .
uvicorn app.main:app --reload --port 8100
```

- API: `http://localhost:8100`
- Interactive docs (Swagger): `http://localhost:8100/docs`

### Docker (recommended)

```bash
docker compose -f docker-compose.photogrammetry.yml up
```

This runs the full COLMAP + OpenMVS pipeline inside a container with all dependencies pre-compiled.

### Configuration

The server is configured via environment variables (defaults shown):

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8100` | Server port |
| `UPLOAD_DIR` | `data/uploads` | Where uploaded images are stored |
| `OUTPUT_DIR` | `data/outputs` | Where generated models are saved |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |

## API Endpoints

All endpoints are prefixed with `/api`.

| Route | Description |
|---|---|
| `GET /api/health` | Health check |
| `POST /api/jobs` | Create a new job |
| `GET /api/jobs` | List all jobs |
| `GET /api/jobs/{job_id}` | Get job status and progress |
| `POST /api/upload` | Upload images for a job |
| `POST /api/photogrammetry/run` | Start COLMAP + OpenMVS pipeline |
| `GET /api/jobs/{job_id}/model` | Download the generated `.glb` model |
| `POST /api/scaling/estimate` | Scale model with true length, estimate height |
| `POST /api/manual-cad/generate` | Generate a manual CAD model (3 rectangular prisms with dimensions) |

## Architecture

The service is consumed by the [`team-bath-rov-secondary-ui`](https://github.com/Team-Bath-Hydrobotics/team-bath-rov-secondary-ui) React app, which proxies `/api` requests to this backend via Vite's dev server.

## Further Reading

- [Pilot Operations Guide](../../docs-site/docs/projects/photogrammetry/pilot-operations-guide.md) — Competition procedure and scoring
- [Technical Documentation](../../docs-site/docs/projects/photogrammetry/photogrammetry.md) — Pipeline details, Docker setup, troubleshooting
