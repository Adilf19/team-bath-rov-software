import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.config import settings
from app.models.job import JobStatus
from app.services.job_manager import job_manager
from app.services.mesh_processor import MeshProcessor

logger = logging.getLogger(__name__)

OPENSFM_BIN = shutil.which("opensfm") or "/opt/OpenSfM/bin/opensfm"

OPENSFM_CONFIG = """\
feature_type: SIFT
matching_gps_distance: 0
matching_gps_neighbors: 0
use_altitude_tag: false
align_method: naive
"""

STAGES = [
    ("extract_metadata", 0, 10),
    ("detect_features", 10, 25),
    ("match_features", 25, 45),
    ("create_tracks", 45, 50),
    ("reconstruct", 50, 75),
    ("export_ply", 75, 85),
]

STAGE_TIMEOUT = 600  # 10 minutes per stage


class OpenSfMPipeline:
    def __init__(self) -> None:
        self.mesh_processor = MeshProcessor()

    def run(self, job_id: str) -> None:
        """Run the full OpenSfM pipeline. Intended to be called in a background thread."""
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

            # Set up OpenSfM project in a temp directory
            tmp_dir = Path(tempfile.mkdtemp(prefix=f"opensfm_{job_id}_"))
            project_dir = tmp_dir / "project"
            project_dir.mkdir()

            # Create images directory with symlinks
            images_dir = project_dir / "images"
            images_dir.mkdir()
            for img in images:
                (images_dir / img.name).symlink_to(img.resolve())

            # Write config
            (project_dir / "config.yaml").write_text(OPENSFM_CONFIG)

            logger.info(
                "Running OpenSfM pipeline for job %s with %d images",
                job_id,
                len(images),
            )

            # Run each stage
            for stage_name, start_pct, end_pct in STAGES:
                job_manager.update_job(
                    job_id,
                    status=JobStatus.RECONSTRUCTING,
                    progress=start_pct,
                    stage=stage_name,
                )

                result = subprocess.run(
                    [OPENSFM_BIN, stage_name, str(project_dir)],
                    capture_output=True,
                    text=True,
                    timeout=STAGE_TIMEOUT,
                )

                if result.returncode != 0:
                    logger.error(
                        "OpenSfM %s failed for job %s: %s",
                        stage_name,
                        job_id,
                        result.stderr,
                    )
                    job_manager.update_job(
                        job_id,
                        status=JobStatus.ERROR,
                        error=f"Reconstruction failed at stage '{stage_name}': {result.stderr[:500]}",
                    )
                    return

                job_manager.update_job(job_id, progress=end_pct)
                logger.info("Completed stage %s for job %s", stage_name, job_id)

            # Find the exported PLY file
            ply_path = project_dir / "undistorted" / "reconstruction.ply"
            if not ply_path.exists():
                # Some versions export to a different location
                depthmaps_ply = project_dir / "undistorted" / "depthmaps" / "merged.ply"
                if depthmaps_ply.exists():
                    ply_path = depthmaps_ply
                else:
                    job_manager.update_job(
                        job_id,
                        status=JobStatus.ERROR,
                        error="Reconstruction completed but no PLY file was produced",
                    )
                    return

            # Mesh processing
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
                error="Reconstruction timed out (stage exceeded 10 minutes)",
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
