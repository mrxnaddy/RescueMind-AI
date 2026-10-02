from app.models.accounts import Organization, Role, User
from app.models.base import Base
from app.models.campaigns import (
    Campaign,
    CampaignProperty,
    CampaignRecipient,
    MessageTemplate,
)
from app.models.crm import Appointment, FollowUp, Lead, LeadAssignment, LeadNote
from app.models.customers import (
    Customer,
    CustomerConsent,
    CustomerGroup,
    CustomerGroupMember,
    CustomerRequirement,
    CustomerTag,
    SuppressionEntry,
)
from app.models.messaging import Integration, Message, MessageEvent, WebhookEvent
from app.models.properties import (
    Property,
    PropertyAmenity,
    PropertyDocument,
    PropertyImage,
    PropertyMatch,
    PropertyTag,
)
from app.models.system import AiGeneration, AuditLog, ScheduledJob

__all__ = [
    "Base",
    "Organization", "Role", "User",
    "Customer", "CustomerRequirement", "CustomerGroup", "CustomerGroupMember",
    "CustomerTag", "CustomerConsent", "SuppressionEntry",
    "Property", "PropertyImage", "PropertyDocument", "PropertyAmenity",
    "PropertyTag", "PropertyMatch",
    "Lead", "LeadNote", "LeadAssignment", "Appointment", "FollowUp",
    "Campaign", "CampaignProperty", "CampaignRecipient", "MessageTemplate",
    "Message", "MessageEvent", "Integration", "WebhookEvent",
    "ScheduledJob", "AuditLog", "AiGeneration",
]