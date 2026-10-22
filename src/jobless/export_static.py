import json
import logging
from datetime import UTC, date, datetime
from pathlib import Path

from . import db

logger = logging.getLogger(__name__)

# frontend/ is served directly by GitHub Pages, so this file becomes a plain
# static asset the page fetches with no backend involved at all.
OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / "frontend" / "data" / "jobs.json"
# Lets the frontend show a real "updated X ago" freshness indicator instead
# of a hardcoded "updated daily" claim it can't actually back up.
META_OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / "frontend" / "data" / "meta.json"


def _json_default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def export(output_path: Path = OUTPUT_PATH) -> int:
    conn = db.get_connection()
    try:
        jobs = db.list_all_jobs(conn)
    finally:
        conn.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(jobs, f, default=_json_default, indent=2)

    logger.info("exported %d jobs to %s", len(jobs), output_path)
    return len(jobs)


def export_meta(output_path: Path = META_OUTPUT_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now(UTC).isoformat()}, f, indent=2)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    export()
    export_meta()


if __name__ == "__main__":
    main()
