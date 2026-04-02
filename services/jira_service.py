import logging
import time
from typing import Any

import requests

from .config import settings
from .validation import normalize_deadline, normalize_priority


LOGGER = logging.getLogger(__name__)


class JiraServiceError(Exception):
    pass


def create_jira_issue(task: dict[str, Any], account_id: str) -> str:
    if not settings.jira_enabled:
        LOGGER.info('Jira integration is disabled. Skipping external issue creation for "%s".', task["task"])
        raise JiraServiceError("Jira integration is currently disabled.")

    if not settings.jira_url or not settings.jira_email or not settings.jira_api_token:
        raise JiraServiceError("Jira configuration is incomplete.")

    payload = {
        "fields": {
            "project": {"key": settings.jira_project_key},
            "summary": task["task"],
            "description": "Auto-generated from meeting",
            "priority": {"name": normalize_priority(task.get("priority"))},
            "duedate": normalize_deadline(task.get("deadline")),
            "assignee": {"id": account_id},
        }
    }

    for attempt in range(3):
        response = requests.post(
            f"{settings.jira_url.rstrip('/')}/rest/api/3/issue",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            auth=(settings.jira_email, settings.jira_api_token),
            json=payload,
            timeout=20,
        )

        if response.status_code in (200, 201):
            data = response.json()
            return data.get("key") or data.get("id")

        if response.status_code == 429:
            time.sleep(int(response.headers.get("Retry-After", "1")))
            continue

        LOGGER.error("Jira create failed on attempt %s: %s", attempt + 1, response.text)
        time.sleep(1)

    raise JiraServiceError(f'Unable to create Jira issue for task "{task["task"]}" after retries.')
