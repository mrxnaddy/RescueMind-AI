from enum import Enum


class CustomerType(str, Enum):
    BUYER = "buyer"
    TENANT = "tenant"
    SELLER = "seller"
    LANDLORD = "landlord"
    INVESTOR = "investor"
    GENERAL_INQUIRY = "general_inquiry"


class Channel(str, Enum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"


class ConsentStatus(str, Enum):
    GRANTED = "granted"
    REVOKED = "revoked"


class SuppressionReason(str, Enum):
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    COMPLAINT = "complaint"
    INVALID = "invalid"
    MANUAL = "manual"


class PropertyCategory(str, Enum):
    HOUSE = "house"
    APARTMENT = "apartment"
    PLOT = "plot"
    SHOP = "shop"
    OFFICE = "office"
    WAREHOUSE = "warehouse"
    FARMHOUSE = "farmhouse"
    COMMERCIAL_BUILDING = "commercial_building"
    OTHER = "other"


class PropertyPurpose(str, Enum):
    SALE = "sale"
    RENT = "rent"
    LEASE = "lease"


class PropertyUse(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"


class PropertyStatus(str, Enum):
    DRAFT = "draft"
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    RENTED = "rented"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class FurnishingStatus(str, Enum):
    FURNISHED = "furnished"
    SEMI_FURNISHED = "semi_furnished"
    UNFURNISHED = "unfurnished"


class MatchStatus(str, Enum):
    SUGGESTED = "suggested"
    APPROVED = "approved"
    REJECTED = "rejected"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPERTY_SHARED = "property_shared"
    VISIT_SCHEDULED = "visit_scheduled"
    NEGOTIATION = "negotiation"
    CONVERTED = "converted"
    LOST = "lost"
    UNRESPONSIVE = "unresponsive"


class AppointmentStatus(str, Enum):
    REQUESTED = "requested"
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class InterestLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FollowUpStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    CANCELLED = "cancelled"


class CampaignType(str, Enum):
    NEW_PROPERTY_ALERT = "new_property_alert"
    PRICE_REDUCTION = "price_reduction"
    OPEN_HOUSE_INVITATION = "open_house_invitation"
    VIEWING_REMINDER = "viewing_reminder"
    CUSTOMER_FOLLOW_UP = "customer_follow_up"
    RENTAL_AVAILABILITY_ALERT = "rental_availability_alert"
    SOLD_OR_RENTED_ANNOUNCEMENT = "sold_or_rented_announcement"
    SEASONAL_CAMPAIGN = "seasonal_campaign"
    INVESTOR_OPPORTUNITY = "investor_opportunity"
    CUSTOM = "custom"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    FAILED = "failed"


class RecipientStatus(str, Enum):
    PENDING = "pending"
    EXCLUDED = "excluded"
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class MessageStatus(str, Enum):
    QUEUED = "queued"
    ACCEPTED = "accepted"  # provider accepted the request (NOT delivery!)
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    UNKNOWN = "unknown"


class MessageLanguage(str, Enum):
    ENGLISH = "english"
    URDU = "urdu"
    ROMAN_URDU = "roman_urdu"


class TemplateApprovalStatus(str, Enum):
    NOT_APPLICABLE = "not_applicable"  # SMS / email templates
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"