import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.config import settings
from app.models.job import JobStatus
from app.services.job_manager import job_manager
from app.services.mesh_processor import MeshProcessor

logger = logging.getLogger(__name__)

COLMAP_BIN = shutil.which("colmap") or "/usr/bin/colmap"

STAGE_TIMEOUT = 1200  # 20 minutes per stage


class ColmapPipeline:
    """Photogrammetry pipeline using COLMAP for SfM reconstruction."""

    def __init__(self) -> None:
        self.mesh_processor = MeshProcessor()

    def _run_colmap(self, args: list[str], job_id: str, stage_name: str) -> bool:
        """Run a COLMAP command. Returns True on success."""
        cmd = [COLMAP_BIN] + args
        logger.info("Running: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=STAGE_TIMEOUT,
        )

        if result.returncode != 0:
            logger.error(
                "COLMAP %s failed for job %s:\nstdout: %s\nstderr: %s",
                stage_name,
                job_id,
                result.stdout[-500:] if result.stdout else "",
                result.stderr[-500:] if result.stderr else "",
            )
            job_manager.update_job(
                job_id,
                status=JobStatus.ERROR,
                error=f"Reconstruction failed at '{stage_name}': {(result.stderr or result.stdout or 'unknown error')[:500]}",
            )
            return False
        return True

    def run(self, job_id: str) -> None:
        """Run the full COLMAP pipeline. Intended to be called in a background thread."""
        tmp_dir = None
        try:
            upload_dir = settings.UPLOAD_DIR / job_id
            images = list(upload_dir.iterdir())

            if len(images) < 3:
                job_manager.update_job(
                    job_id,
                    status=JobStatus.ERROR,
                    error="At least 3 images are required for reconstruction",
                )
                return

            # Set up workspace
            tmp_dir = Path(tempfile.mkdtemp(prefix=f"colmap_{job_id}_"))
            db_path = tmp_dir / "database.db"
            sparse_dir = tmp_dir / "sparse"
            sparse_dir.mkdir()

            image_dir = settings.UPLOAD_DIR / job_id

            logger.info(
                "Running COLMAP pipeline for job %s with %d images",
                job_id,
                len(images),
            )

            # Stage 1: Feature extraction (0-20%)
            job_manager.update_job(
                job_id,
                status=JobStatus.RECONSTRUCTING,
                progress=0,
                stage="feature_extraction",
            )
            if not self._run_colmap([
                "feature_extractor",
                "--database_path", str(db_path),
                "--image_path", str(image_dir),
                "--ImageReader.single_camera", "1",
                "--ImageReader.camera_model", "SIMPLE_RADIAL",
                "--SiftExtraction.use_gpu", "0",
                "--SiftExtraction.max_num_features", "5000",
                "--SiftExtraction.max_image_size", "2000",
                "--SiftExtraction.first_octave", "0",
                "--SiftExtraction.num_threads", "1",
            ], job_id, "feature_extraction"):
                return
            job_manager.update_job(job_id, progress=20)
            logger.info("Completed feature_extraction for job %s", job_id)

            # Stage 2: Feature matching (20-45%)
            job_manager.update_job(job_id, progress=20, stage="feature_matching")
            if not self._run_colmap([
                "exhaustive_matcher",
                "--database_path", str(db_path),
                "--SiftMatching.use_gpu", "0",
                "--SiftMatching.num_threads", "1",
            ], job_id, "feature_matching"):
                return
            job_manager.update_job(job_id, progress=45)
            logger.info("Completed feature_matching for job %s", job_id)

            # Stage 3: Sparse reconstruction / mapping (45-75%)
            job_manager.update_job(job_id, progress=45, stage="reconstruction")
            if not self._run_colmap([
                "mapper",
                "--database_path", str(db_path),
                "--image_path", str(image_dir),
                "--output_path", str(sparse_dir),
            ], job_id, "reconstruction"):
                return
            job_manager.update_job(job_id, progress=75)
            logger.info("Completed reconstruction for job %s", job_id)

            # Find the best reconstruction (COLMAP creates numbered subdirs: 0, 1, ...)
            sparse_models = sorted(sparse_dir.iterdir())
            if not sparse_models:
                job_manager.update_job(
                    job_id,
                    status=JobStatus.ERROR,
                    error="Sparse reconstruction produced no models",
                )
                return
            sparse_model = sparse_models[0]

            # Stage 4: Export to PLY (75-85%)
            job_manager.update_job(job_id, progress=75, stage="export_ply")
            ply_path = tmp_dir / "reconstruction.ply"
            if not self._run_colmap([
                "model_converter",
                "--input_path", str(sparse_model),
                "--output_path", str(ply_path),
                "--output_type", "PLY",
            ], job_id, "export_ply"):
                return
            job_manager.update_job(job_id, progress=85)
            logger.info("Completed export_ply for job %s", job_id)

            if not ply_path.exists():
                job_manager.update_job(
                    job_id,
                    status=JobStatus.ERROR,
                    error="Reconstruction completed but no PLY file was produced",
                )
                return

            ply_size = ply_path.stat().st_size
            logger.info("PLY file size: %.1f MB", ply_size / (1024 * 1024))

            # Stage 5: Mesh processing (85-100%)
            output_path = self.mesh_processor.process(job_id, ply_path)

            output_url = f"/api/jobs/{job_id}/model"
            job_manager.update_job(
                job_id,
                status=JobStatus.COMPLETE,
                progress=100,
                stage="complete",
                output_url=output_url,
            )
            logger.info("Pipeline complete for job %s → %s", job_id, output_path)

        except subprocess.TimeoutExpired:
            logger.exception("Pipeline timed out for job %s", job_id)
            job_manager.update_job(
                job_id,
                status=JobStatus.ERROR,
                error="Reconstruction timed out (stage exceeded 20 minutes)",
            )
        except Exception:
            logger.exception("Pipeline failed for job %s", job_id)
            job_manager.update_job(
                job_id,
                status=JobStatus.ERROR,
                error="An unexpected error occurred during reconstruction",
            )
        finally:
            if tmp_dir and tmp_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)
