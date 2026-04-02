from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class TranscriptEntry(BaseModel):
    speaker: str | None = None
    text: str
    startTime: str | None = None


class TranscriptPayload(BaseModel):
    value: list[TranscriptEntry] = Field(default_factory=list)

    @field_validator("value")
    @classmethod
    def validate_entries(cls, value: list[TranscriptEntry]) -> list[TranscriptEntry]:
        if not isinstance(value, list):
            raise ValueError("value must be a list")
        return value


class ProcessMeetingRequest(BaseModel):
    transcript: TranscriptPayload


class ExtractedTask(BaseModel):
    task: str
    owner: str
    priority: str
    deadline: str | None = None
    timestamp: str | None = None
    mapped_account_id: str | None = None
    jira_issue_id: str | None = None
    jira_status: Literal["pending", "created", "failed", "not_connected"] = "pending"


class ProcessMeetingResponse(BaseModel):
    meeting_id: int
    tasks: list[ExtractedTask]
    cleaned_transcript: list[dict[str, Any]]


class PushToJiraRequest(BaseModel):
    tasks: list[ExtractedTask]


class JiraPushResult(BaseModel):
    task: str
    owner: str
    jira_issue_id: str | None = None
    jira_status: Literal["created", "failed", "not_connected"]


class DashboardResponse(BaseModel):
    tasks: list[dict[str, Any]]
    summary: dict[str, Any]
