from datetime import datetime, timezone

from fastapi import APIRouter

from backend.db.database import fetch_all_tasks, insert_meeting, insert_tasks, update_task_jira_status
from backend.models.schemas import (
    DashboardResponse,
    JiraPushResult,
    ProcessMeetingRequest,
    ProcessMeetingResponse,
    PushToJiraRequest,
)
from backend.services.config import settings
from backend.services.jira_service import JiraServiceError, create_jira_issue
from backend.services.llm_service import extract_tasks
from backend.services.nlp_engine import process_transcript
from backend.services.user_mapping import map_user
from backend.services.validation import validate_tasks


router = APIRouter()


@router.post("/process-meeting", response_model=ProcessMeetingResponse)
def process_meeting(request: ProcessMeetingRequest) -> ProcessMeetingResponse:
    transcript = request.transcript.model_dump()
    cleaned_transcript = process_transcript(transcript)
    llm_output = extract_tasks(cleaned_transcript)
    tasks = validate_tasks(llm_output)

    timestamp = datetime.now(timezone.utc).isoformat()
    meeting_id = insert_meeting(timestamp, transcript)
    insert_tasks(meeting_id, timestamp, tasks)

    return ProcessMeetingResponse(
        meeting_id=meeting_id,
        tasks=tasks,
        cleaned_transcript=cleaned_transcript,
    )


@router.post("/push-to-jira", response_model=list[JiraPushResult])
def push_to_jira(request: PushToJiraRequest) -> list[JiraPushResult]:
    results: list[JiraPushResult] = []
    updated_at = datetime.now(timezone.utc).isoformat()

    for task in request.tasks:
        mapped_account_id = map_user(task.owner)
        if not settings.jira_enabled:
            update_task_jira_status(task.task, task.owner, "not_connected", None, updated_at)
            results.append(
                JiraPushResult(
                    task=task.task,
                    owner=task.owner,
                    jira_issue_id=None,
                    jira_status="not_connected",
                )
            )
            continue

        try:
            jira_issue_id = create_jira_issue(task.model_dump(), mapped_account_id)
            update_task_jira_status(task.task, task.owner, "created", jira_issue_id, updated_at)
            results.append(
                JiraPushResult(
                    task=task.task,
                    owner=task.owner,
                    jira_issue_id=jira_issue_id,
                    jira_status="created",
                )
            )
        except JiraServiceError:
            update_task_jira_status(task.task, task.owner, "failed", None, updated_at)
            results.append(
                JiraPushResult(
                    task=task.task,
                    owner=task.owner,
                    jira_issue_id=None,
                    jira_status="failed",
                )
            )

    return results


@router.get("/dashboard-data", response_model=DashboardResponse)
def dashboard_data() -> DashboardResponse:
    tasks = fetch_all_tasks()
    summary = {
        "total_tasks": len(tasks),
        "created": sum(task["jira_status"] == "created" for task in tasks),
        "failed": sum(task["jira_status"] == "failed" for task in tasks),
        "pending": sum(task["jira_status"] == "pending" for task in tasks),
        "not_connected": sum(task["jira_status"] == "not_connected" for task in tasks),
    }
    return DashboardResponse(tasks=tasks, summary=summary)
