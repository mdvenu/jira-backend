import json
import logging
from typing import Any

from groq import Groq

from .config import settings


LOGGER = logging.getLogger(__name__)

PROMPT = """You extract only explicitly stated action items from meeting transcript chunks.
Rules:
- Return strict JSON only.
- Do not invent tasks, owners, priorities, or deadlines.
- Include only tasks that are directly stated.
- If a field is not explicit, use null.
- Output schema:
{"tasks":[{"task":"string","owner":"string|null","priority":"string|null","deadline":"string|null","timestamp":"string|null"}]}
"""


def _fallback_extract(cleaned_transcript: list[dict[str, Any]]) -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    trigger_words = ("need to", "should", "must", "action item", "follow up", "finish", "complete")
    for item in cleaned_transcript:
        lowered = item["text"].lower()
        if any(trigger in lowered for trigger in trigger_words):
            tasks.append(
                {
                    "task": item["text"].rstrip("."),
                    "owner": item["speaker"],
                    "priority": None,
                    "deadline": None,
                    "timestamp": item["timestamp"],
                }
            )
    return {"tasks": tasks}


def extract_tasks(cleaned_transcript: list[dict[str, Any]]) -> dict[str, Any]:
    if not settings.groq_api_key:
        LOGGER.warning("GROQ_API_KEY not configured. Using fallback extraction.")
        return _fallback_extract(cleaned_transcript)

    client = Groq(api_key=settings.groq_api_key)
    transcript_text = json.dumps(cleaned_transcript, ensure_ascii=True)

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": transcript_text},
                ],
                temperature=0.00000001,
            )
            content = response.choices[0].message.content or '{"tasks":[]}'
            return json.loads(content)
        except Exception as exc:  # pragma: no cover
            LOGGER.exception("Groq extraction attempt %s failed: %s", attempt + 1, exc)

    return {"tasks": []}
