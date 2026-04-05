import fcntl
import json
from pathlib import Path
from typing import Any

from app.models.job import Job


class JobManager:
    def __init__(self) -> None:
        self._db_path = Path("data/jobs.json")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._db_path.exists():
            self._db_path.write_text("{}")

    def _read_db(self) -> dict[str, dict]:
        with open(self._db_path, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def _write_db(self, data: dict[str, dict]) -> None:
        with open(self._db_path, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump(data, f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def create_job(self) -> Job:
        job = Job()
        db = self._read_db()
        db[job.id] = job.model_dump(mode="json")
        self._write_db(db)
        return job

    def get_job(self, job_id: str) -> Job | None:
        db = self._read_db()
        data = db.get(job_id)
        if data is None:
            return None
        return Job(**data)

    def list_jobs(self) -> list[Job]:
        db = self._read_db()
        return [Job(**data) for data in db.values()]

    def update_job(self, job_id: str, **fields: Any) -> Job | None:
        with open(self._db_path, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                db = json.load(f)
                data = db.get(job_id)
                if data is None:
                    return None
                job = Job(**data)
                updated = job.model_copy(update=fields)
                db[job_id] = updated.model_dump(mode="json")
                f.seek(0)
                f.truncate()
                json.dump(db, f)
                return updated
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)


job_manager = JobManager()
