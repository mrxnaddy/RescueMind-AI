"""Creates any missing tables. Safe to run many times.

Existing tables are never changed or deleted.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.models import (  # noqa: E402,F401
    duplicate_candidate,
    incident_embedding,
    response_plan,
)

NEW_TABLES = ("incident_embeddings", "duplicate_candidates", "response_plans")


def main() -> None:
    before = set(inspect(engine).get_table_names())

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    after = set(inspector.get_table_names())

    created = sorted(after - before)
    print("Newly created tables:", created if created else "none (already existed)")

    print(f"\nAll tables ({len(after)}):")

    for name in sorted(after):
        print(f"  {name}")

    for table in NEW_TABLES:
        columns = [column["name"] for column in inspector.get_columns(table)]
        print(f"\n{table} columns: {columns}")


if __name__ == "__main__":
    main()