import logging
from pathlib import Path

import numpy as np
import open3d as o3d
import trimesh

from app.config import settings
from app.models.job import JobStatus
from app.services.job_manager import job_manager

logger = logging.getLogger(__name__)


class MeshProcessor:
    def process(self, job_id: str, ply_path: Path) -> Path:
        """Convert a PLY point cloud to a GLB mesh via Poisson reconstruction."""
        logger.info("Starting mesh processing for job %s", job_id)

        job_manager.update_job(
            job_id, status=JobStatus.MESHING, progress=85, stage="meshing"
        )

        # Load point cloud
        pcd = o3d.io.read_point_cloud(str(ply_path))
        if len(pcd.points) < 100:
            raise ValueError(
                f"Point cloud has only {len(pcd.points)} points (minimum 100 required)"
            )

        logger.info("Loaded %d points from %s", len(pcd.points), ply_path)

        # Estimate and orient normals
        pcd.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
        )
        pcd.orient_normals_consistent_tangent_plane(k=15)

        # Poisson surface reconstruction
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd, depth=9
        )

        # Remove low-density vertices (bottom 1st percentile) to trim noise
        densities = np.asarray(densities)
        threshold = np.percentile(densities, 1)
        vertices_to_remove = densities < threshold
        mesh.remove_vertices_by_mask(vertices_to_remove)

        logger.info(
            "Mesh has %d vertices, %d triangles",
            len(mesh.vertices),
            len(mesh.triangles),
        )

        job_manager.update_job(job_id, progress=95, stage="exporting")

        # Convert to trimesh for GLB export
        vertices = np.asarray(mesh.vertices)
        faces = np.asarray(mesh.triangles)

        vertex_colors = None
        if mesh.has_vertex_colors():
            vertex_colors = (np.asarray(mesh.vertex_colors) * 255).astype(np.uint8)

        tri_mesh = trimesh.Trimesh(
            vertices=vertices, faces=faces, vertex_colors=vertex_colors
        )

        # Export GLB
        output_dir = settings.OUTPUT_DIR / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "model.glb"
        tri_mesh.export(str(output_path), file_type="glb")

        job_manager.update_job(job_id, progress=100, stage="complete")

        logger.info("Exported mesh to %s", output_path)
        return output_path
