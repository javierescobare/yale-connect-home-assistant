"""Constants for the Yale Connect integration."""

DOMAIN = "yale_connect"

CONF_ENTRY_CODE = "entry_code"
CONF_ALLOW_UNLOCK = "allow_unlock"
CONF_UUID = "uuid"

API_BASE = "https://api.connectservices.assaabloy.com/api/YaleConnect"
BRAND_PLATFORM_GUID = (
    "A46A26A6-2AE7-11ED-A261-0242AC120002.3939e0f2-08e5-4bb1-b3a6-ddb1183666d3"
)

SCAN_INTERVAL_SECONDS = 20

STATE_UNLOCKED = 0
STATE_LOCKED = 1
STATE_MOVING = 2

CATEGORY_LOCK = "Lock"

EVENT_LOCKED = "locked"
EVENT_UNLOCKED = "unlocked"
EVENT_UNKNOWN = "unknown"
# statusId of an access register entry -> event type
REGISTER_STATUS_EVENTS = {1: EVENT_LOCKED, 2: EVENT_UNLOCKED}

SIGNAL_ACTIVITY = f"{DOMAIN}_activity_{{}}"
