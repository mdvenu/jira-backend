import math
import re
from typing import Any


FILLER_PATTERN = re.compile(r"\b(uh|um|erm|ah|like)\b", re.IGNORECASE)
SPACE_PATTERN = re.compile(r"\s+")


def _normalize_text(text: str) -> str:
    cleaned = FILLER_PATTERN.sub("", text or "")
    cleaned = SPACE_PATTERN.sub(" ", cleaned).strip(" ,.")
    if not cleaned:
        return ""
    cleaned = cleaned[0].upper() + cleaned[1:]
    if cleaned[-1] not in ".!?":
        cleaned = f"{cleaned}."
    return cleaned


def _merge_sentences(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    for entry in entries:
        previous = merged[-1] if merged else None
        if (
            previous
            and previous["speaker"] == entry["speaker"]
            and len(previous["text"]) < 120
            and previous["text"][-1] not in ".!?"
        ):
            previous["text"] = f'{previous["text"].rstrip(".")} {entry["text"]}'.strip()
            continue
        merged.append(entry)
    return merged


def process_transcript(payload: dict[str, Any]) -> list[dict[str, str]]:
    raw_entries = payload.get("value", [])
    normalized_entries: list[dict[str, str]] = []

    for entry in raw_entries:
        speaker = (entry.get("speaker") or "Unknown").strip() or "Unknown"
        text = _normalize_text(entry.get("text", ""))
        if not text:
            continue
        normalized_entries.append(
            {
                "speaker": speaker,
                "text": text,
                "timestamp": entry.get("startTime") or "00:00:00",
            }
        )

    merged_entries = _merge_sentences(normalized_entries)
    if len(merged_entries) <= 20:
        return merged_entries

    chunk_size = math.ceil(len(merged_entries) / math.ceil(len(merged_entries) / 20))
    chunked_output: list[dict[str, str]] = []
    for start in range(0, len(merged_entries), chunk_size):
        chunked_output.extend(merged_entries[start : start + chunk_size])
    return chunked_output
