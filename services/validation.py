from datetime import datetime
from typing import Any

from dateutil import parser


PRIORITY_MAP = {
    "urgent": "High",
    "critical": "High",
    "high": "High",
    "medium": "Medium",
    "normal": "Medium",
    "low": "Low",
}


def normalize_priority(priority: str | None) -> str:
    if not priority:
        return "Medium"
    return PRIORITY_MAP.get(priority.strip().lower(), "Medium")


def normalize_deadline(deadline: str | None) -> str | None:
    if not deadline:
        return None
    try:
        parsed = parser.parse(deadline, fuzzy=True, default=datetime.utcnow())
        return parsed.date().isoformat()
    except (ValueError, TypeError, OverflowError):
        return None


def validate_tasks(llm_output: dict[str, Any]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    validated: list[dict[str, Any]] = []

    for item in llm_output.get("tasks", []):
        task = str(item.get("task") or "").strip()
        owner = str(item.get("owner") or "Unknown").strip() or "Unknown"
        if not task:
            continue

        dedupe_key = (task.lower(), owner.lower())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        validated.append(
            {
                "task": task,
                "owner": owner,
                "priority": normalize_priority(item.get("priority")),
                "deadline": normalize_deadline(item.get("deadline")),
                "timestamp": item.get("timestamp"),
                "jira_status": "pending",
            }
        )

    return validated
