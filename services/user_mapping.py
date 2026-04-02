from .config import settings


USER_MAPPING = {
    "john": "accountId_123",
    "alice": "accountId_456",
}


def normalize_name(name: str | None) -> str:
    if not name:
        return "unknown"
    return name.strip().lower().split()[0]


def map_user(name: str | None) -> str:
    normalized = normalize_name(name)
    return USER_MAPPING.get(normalized, settings.default_user)
