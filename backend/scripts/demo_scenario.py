"""End-to-end rehearsal of the RescueMind AI demo scenario.

Run it while the API server is running:

    python backend\\scripts\\demo_scenario.py

The coordinator's decisions (merge duplicates, approve the plan) are SIMULATED
by this script so the whole flow can be tested quickly. In the real demo a
human does these in the dashboard. All data is simulated.
"""

import argparse
import sys

import httpx

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}

# The first three reports describe the SAME flood (should be flagged as
# duplicates). The last two are floods in other places (should not be).
DEMO_REPORTS = [
    {
        "label": "R1 English, Canal Road underpass",
        "body": {
            "reporter_name": "Demo Citizen 1",
            "emergency_type": "flood",
            "description": (
                "Heavy flooding at the Canal Road underpass. Several cars are "
                "stuck in rising water and a family of five is trapped inside "
                "a minibus. One person looks injured."
            ),
            "address": "Canal Road Underpass",
            "latitude": 31.4750,
            "longitude": 74.3950,
        },
    },
    {
        "label": "R2 Roman Urdu, Canal Road underpass",
        "body": {
            "reporter_name": "Demo Citizen 2",
            "emergency_type": "flood",
            "description": (
                "Canal Road ke underpass mein bohat pani bhar gaya hai, ek "
                "minibus mein phansa hua khandaan madad ke liye cheekh raha "
                "hai, pani barhta ja raha hai."
            ),
            "address": "Canal Road Underpass",
            "latitude": 31.4756,
            "longitude": 74.3955,
        },
    },
    {
        "label": "R3 English, Canal Road underpass",
        "body": {
            "reporter_name": "Demo Citizen 3",
            "emergency_type": "flood",
            "description": (
                "Underpass on Canal Road is completely flooded. A minibus with "
                "about five people is stuck in the water and one of them is "
                "hurt. Please send boats."
            ),
            "address": "Canal Road Underpass",
            "latitude": 31.4748,
            "longitude": 74.3946,
        },
    },
    {
        "label": "R4 English, old grain market (different place)",
        "body": {
            "reporter_name": "Demo Citizen 4",
            "emergency_type": "flood",
            "description": (
                "Water from the drain is entering ground floor shops in the "
                "old grain market. Shopkeepers are moving goods upstairs. "
                "Nobody is hurt."
            ),
            "address": "Old Grain Market",
            "latitude": 31.5100,
            "longitude": 74.3700,
        },
    },
    {
        "label": "R5 English, bus terminal road (different place)",
        "body": {
            "reporter_name": "Demo Citizen 5",
            "emergency_type": "flood",
            "description": (
                "Flood water has covered the road near the bus terminal and "
                "traffic is blocked. No one is in danger right now."
            ),
            "address": "Bus Terminal Road",
            "latitude": 31.5500,
            "longitude": 74.3300,
        },
    },
]


def title(text: str) -> None:
    print(f"\n=== {text} ===")


def api(client, method, path, ok=(200, 201), **kwargs):
    response = client.request(method, path, **kwargs)

    if response.status_code not in ok:
        print(f"ERROR {method} {path} -> {response.status_code}")
        print(response.text[:600])
        sys.exit(1)

    return response.json()


def units_available(summary: dict) -> dict:
    return {
        item["resource_type"]: item["units_available"]
        for item in summary["by_type"]
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="Do not resolve the incident at the end (resources stay assigned).",
    )
    args = parser.parse_args()

    client = httpx.Client(base_url=args.base_url, timeout=180.0)
    checks: list[tuple[str, bool]] = []

    # 1. Health and baseline ------------------------------------------------
    title("1. Health check and baseline")

    try:
        api(client, "GET", "/health")
        api(client, "GET", "/health/database")
    except httpx.HTTPError as exc:
        print(f"Cannot reach the server at {args.base_url}: {exc}")
        print("Start the API server first, then run this script again.")
        sys.exit(1)

    baseline_resources = api(client, "GET", "/api/resources/summary")
    baseline_stats = api(client, "GET", "/api/dashboard/stats")

    print("Server and database are healthy.")
    print("Units available at start:", units_available(baseline_resources))
    print(
        "Dashboard at start: total",
        baseline_stats["total_incidents"],
        "| pending",
        baseline_stats["pending"],
        "| urgent",
        baseline_stats["urgent"],
        "| assigned",
        baseline_stats["assigned"],
        "| resolved",
        baseline_stats["resolved"],
    )

    # 2. Reports ------------------------------------------------------------
    title("2. Five citizens submit flood reports")

    report_ids: list[int] = []

    for item in DEMO_REPORTS:
        report = api(
            client,
            "POST",
            "/api/emergency-reports/",
            json=item["body"],
        )
        report_ids.append(report["id"])
        print(f"  report #{report['id']}: {item['label']}")

    # 3. AI analysis --------------------------------------------------------
    title("3. AI analysis (this takes a little while)")

    incident_ids: list[int] = []
    analyzed_ok = 0

    for item, report_id in zip(DEMO_REPORTS, report_ids):
        result = api(
            client,
            "POST",
            f"/api/analysis/reports/{report_id}/analyze",
        )
        summary = result["summary"]
        duplicate_check = result.get("duplicate_check") or {}

        if result["status"] == "completed":
            analyzed_ok += 1

        incident_ids.append(result["incident_id"])

        print(
            f"  {result['incident_code']}  analysis {result['status']}"
            f" | severity {summary.get('severity')}"
            f" (score {summary.get('severity_score')})"
            f" | location {summary.get('location_certainty')}"
            f" | possible duplicates {duplicate_check.get('potential_duplicates')}"
        )

    checks.append(
        (f"All reports analyzed ({analyzed_ok}/{len(DEMO_REPORTS)})",
         analyzed_ok == len(DEMO_REPORTS))
    )

    demo_incident_ids = set(incident_ids)

    # 4. Duplicate review queue ---------------------------------------------
    title("4. Duplicate review queue (AI suggestions, nothing merged yet)")

    candidates = api(
        client,
        "GET",
        "/api/duplicates/candidates",
        params={"status": "pending", "limit": 100},
    )

    demo_candidates = [
        item
        for item in candidates
        if item["incident"]["id"] in demo_incident_ids
        and item["candidate"]["id"] in demo_incident_ids
    ]

    if not demo_candidates:
        print("  No duplicate suggestions were found among the demo reports.")

    for item in demo_candidates:
        factors = item.get("factors") or {}
        print(
            f"  {item['incident']['incident_code']} <-> "
            f"{item['candidate']['incident_code']}"
            f" | similarity {item['similarity']} ({item['strength']})"
            f" | distance {factors.get('distance_km')} km"
        )

    checks.append(
        ("At least 2 duplicate suggestions among the Canal Road reports",
         len(demo_candidates) >= 2)
    )

    # 5. Coordinator confirms the duplicates (simulated) ---------------------
    title("5. Coordinator confirms the duplicates (SIMULATED by this script)")

    merged = 0

    for item in sorted(
        demo_candidates, key=lambda entry: entry["similarity"], reverse=True
    ):
        response = client.post(
            f"/api/duplicates/candidates/{item['id']}/confirm",
            json={"notes": "Same flood at the underpass (demo script)"},
        )

        if response.status_code == 200:
            data = response.json()
            merged += 1
            print(
                f"  merged {data['merged_incident']['incident_code']} into "
                f"{data['primary_incident']['incident_code']}"
                f" (reports now: {data['report_count']})"
            )
        elif response.status_code == 409:
            print(f"  candidate #{item['id']} skipped (already decided or stale)")
        else:
            print(f"ERROR confirm -> {response.status_code}: {response.text[:300]}")
            sys.exit(1)

    checks.append(("Duplicate incidents were merged", merged >= 1))

    # 6. Most urgent incident ------------------------------------------------
    title("6. Most urgent open incident of this demo")

    open_incidents = []

    for incident_id in sorted(demo_incident_ids):
        detail = api(client, "GET", f"/api/incidents/{incident_id}")

        if detail["status"] != "merged":
            open_incidents.append(detail)

    open_incidents.sort(
        key=lambda entry: (-SEVERITY_RANK.get(entry["severity"], 0), entry["id"])
    )

    for detail in open_incidents:
        print(
            f"  {detail['incident_code']} | severity {detail['severity']}"
            f" | reports {detail['report_count']} | {detail['title']}"
        )

    target = open_incidents[0]
    target_id = target["id"]

    print(f"\n  Chosen: {target['incident_code']}")

    api(
        client,
        "PATCH",
        f"/api/incidents/{target_id}/status",
        json={"status": "under_review", "notes": "Review started (demo script)"},
    )
    print("  Coordinator started the review (SIMULATED): under_review")

    # 7. Response plan -------------------------------------------------------
    title("7. AI response plan (proposal only)")

    plan_record = api(
        client,
        "POST",
        f"/api/plans/incidents/{target_id}/generate",
    )
    plan = plan_record["plan"]

    print(f"  Plan #{plan_record['id']} | status {plan_record['status']}"
          f" | priority {plan['priority']}")

    print("  Proposed resources:")

    for allocation in plan["proposed_allocations"]:
        distance = allocation["distance_km"]
        distance_text = "distance unknown" if distance is None else f"{distance} km"
        print(
            f"    - {allocation['quantity']} x {allocation['resource_type']}"
            f" from {allocation['name']} ({distance_text})"
        )

    if plan["unmet_requirements"]:
        print("  NOT fully covered:", plan["unmet_requirements"])

    print("  Actions:")

    for action in plan["actions"]:
        print(f"    {action['order']}. {action['action']}")

    if plan["information_to_verify"]:
        print("  To verify:")

        for text in plan["information_to_verify"]:
            print(f"    - {text}")

    print("  Briefing:", plan["coordinator_briefing"] or f"(none) {plan['briefing_note']}")

    checks.append(
        ("Plan proposes at least one resource",
         len(plan["proposed_allocations"]) > 0)
    )

    # 8. Human approval (simulated) ------------------------------------------
    title("8. Coordinator approves the plan (SIMULATED by this script)")

    approval = api(
        client,
        "POST",
        f"/api/plans/{plan_record['id']}/approve",
        json={"notes": "Approved (demo script)"},
    )

    print(f"  Incident status: {approval['incident']['status']}")

    for assignment in approval["assignments"]:
        print(
            f"    assigned {assignment['quantity']} x "
            f"{assignment['resource_type']} ({assignment['resource_name']})"
        )

    checks.append(("Plan approved and resources assigned",
                   len(approval["assignments"]) > 0))

    api(
        client,
        "PATCH",
        f"/api/incidents/{target_id}/status",
        json={"status": "in_progress", "notes": "Teams on the way (demo script)"},
    )
    print("  Response started (SIMULATED): in_progress")

    # 9. Dashboard -----------------------------------------------------------
    title("9. Dashboard and resources now")

    stats = api(client, "GET", "/api/dashboard/stats")
    resources_now = api(client, "GET", "/api/resources/summary")

    print(
        "  Dashboard: total", stats["total_incidents"],
        "| pending", stats["pending"],
        "| urgent", stats["urgent"],
        "| assigned", stats["assigned"],
        "| in_progress", stats["in_progress"],
        "| resolved", stats["resolved"],
    )
    print("  Units available now:", units_available(resources_now))

    # 10. Resolve and restore ------------------------------------------------
    if args.keep_open:
        title("10. Left open (--keep-open)")
        print("  The incident stays in_progress and its resources stay assigned.")
    else:
        title("10. Incident resolved, resources released")

        resolved = api(
            client,
            "PATCH",
            f"/api/incidents/{target_id}/status",
            json={"status": "resolved", "notes": "All clear (demo script)"},
        )
        print(f"  Released assignments: {resolved['released_assignments']}")

        resources_after = api(client, "GET", "/api/resources/summary")
        restored = units_available(resources_after) == units_available(
            baseline_resources
        )

        print("  Units available after:", units_available(resources_after))
        checks.append(("Resources are back to the starting numbers", restored))

    # Summary ----------------------------------------------------------------
    title("CHECKPOINT SUMMARY")

    for text, passed in checks:
        print(f"  [{'PASS' if passed else 'WARN'}] {text}")

    print(
        "\nNote: the AI's answers can vary a little between runs. A WARN is "
        "something to look at, not always a bug."
    )


if __name__ == "__main__":
    main()