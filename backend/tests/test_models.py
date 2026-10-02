from sqlalchemy.orm import configure_mappers

from app.models import Base

EXPECTED_TABLES = {
    "users", "roles", "organizations", "customers", "customer_requirements",
    "customer_groups", "customer_group_members", "customer_tags",
    "customer_consents", "suppression_lists", "properties", "property_images",
    "property_documents", "property_amenities", "property_tags",
    "property_matches", "leads", "lead_notes", "lead_assignments",
    "appointments", "follow_ups", "campaigns", "campaign_properties",
    "campaign_recipients", "message_templates", "messages", "message_events",
    "integrations", "scheduled_jobs", "audit_logs", "ai_generations",
    "webhook_events",
}


def test_all_model_relationships_are_valid():
    configure_mappers()  # raises an error if any relationship is broken


def test_all_32_tables_are_defined():
    assert set(Base.metadata.tables.keys()) == EXPECTED_TABLES


def test_every_business_table_has_organization_id():
    for name, table in Base.metadata.tables.items():
        if name not in {"organizations", "roles"}:
            assert "organization_id" in table.c, f"{name} has no organization_id"