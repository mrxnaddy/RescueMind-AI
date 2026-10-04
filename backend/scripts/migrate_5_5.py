"""One-time migration for Step 5.5 (adds new columns to existing tables).

Safe to run more than once. Fresh databases do not need it, because
Base.metadata.create_all() already creates the new columns.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text  # noqa: E402

from app.database import engine  # noqa: E402


def column_names(table: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table)}


def main() -> None:
    incident_columns = column_names("incidents")
    report_columns = column_names("emergency_reports")

    with engine.begin() as connection:
        if "ai_analysis" not in incident_columns:
            connection.execute(
                text("ALTER TABLE incidents ADD COLUMN ai_analysis JSON NULL")
            )
            print("Added incidents.ai_analysis")
        else:
            print("incidents.ai_analysis already exists - skipped")

        if "incident_id" not in report_columns:
            connection.execute(
                text(
                    "ALTER TABLE emergency_reports "
                    "ADD COLUMN incident_id INT NULL"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE emergency_reports "
                    "ADD INDEX ix_emergency_reports_incident_id (incident_id)"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE emergency_reports "
                    "ADD CONSTRAINT fk_emergency_reports_incident_id "
                    "FOREIGN KEY (incident_id) REFERENCES incidents (id) "
                    "ON DELETE SET NULL"
                )
            )
            print("Added emergency_reports.incident_id (index + foreign key)")
        else:
            print("emergency_reports.incident_id already exists - skipped")

    print("\nCurrent columns:")

    for table in ("incidents", "emergency_reports"):
        print(f"  {table}: {sorted(column_names(table))}")


if __name__ == "__main__":
    main()