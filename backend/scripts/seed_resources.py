"""Loads the simulated resources from datasets/simulated_resources.json.

Safe to run many times: a resource whose name already exists is skipped.
All of this data is SIMULATED (names start with [SIM]).
"""

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal  # noqa: E402
from app.models.resource import Resource  # noqa: E402
from app.schemas.resource import ResourceCreate  # noqa: E402
from app.services.resource_service import derive_status  # noqa: E402

DATASET = PROJECT_ROOT / "datasets" / "simulated_resources.json"


def main() -> None:
    if not DATASET.exists():
        print(f"Dataset file not found: {DATASET}")
        return

    entries = json.loads(DATASET.read_text(encoding="utf-8"))

    db = SessionLocal()
    created = 0
    skipped = 0

    try:
        for entry in entries:
            data = ResourceCreate(**entry)

            exists = (
                db.query(Resource)
                .filter(Resource.name == data.name)
                .first()
            )

            if exists is not None:
                skipped += 1
                continue

            available = (
                data.quantity
                if data.available_quantity is None
                else data.available_quantity
            )

            db.add(
                Resource(
                    name=data.name,
                    resource_type=data.resource_type,
                    quantity=data.quantity,
                    available_quantity=available,
                    latitude=data.latitude,
                    longitude=data.longitude,
                    location_name=data.location_name,
                    status=derive_status(data.status, available),
                )
            )
            created += 1

        db.commit()
    finally:
        db.close()

    print(f"Created {created} simulated resources, skipped {skipped} (already existed).")


if __name__ == "__main__":
    main()