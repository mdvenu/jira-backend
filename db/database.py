import json
import logging
from typing import Any

import mysql.connector

from backend.services.config import settings


LOGGER = logging.getLogger(__name__)


def get_connection():
    return mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
    )


def init_db() -> None:
    bootstrap_connection = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
    )

    with bootstrap_connection.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.mysql_database}")
    bootstrap_connection.close()

    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS meetings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                created_at VARCHAR(64) NOT NULL,
                raw_transcript JSON NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                meeting_id INT NOT NULL,
                task TEXT NOT NULL,
                owner VARCHAR(255) NOT NULL,
                mapped_account_id VARCHAR(255),
                priority VARCHAR(32) NOT NULL,
                deadline DATE NULL,
                timestamp VARCHAR(32),
                jira_issue_id VARCHAR(64),
                jira_status VARCHAR(32) NOT NULL DEFAULT 'pending',
                created_at VARCHAR(64) NOT NULL,
                updated_at VARCHAR(64) NOT NULL,
                CONSTRAINT fk_meeting FOREIGN KEY(meeting_id) REFERENCES meetings(id)
            )
            """
        )
        connection.commit()
    connection.close()
    LOGGER.info("MySQL database initialized: %s", settings.mysql_database)


def insert_meeting(created_at: str, raw_transcript: dict[str, Any]) -> int:
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO meetings (created_at, raw_transcript) VALUES (%s, %s)",
            (created_at, json.dumps(raw_transcript)),
        )
        connection.commit()
        meeting_id = int(cursor.lastrowid)
    connection.close()
    return meeting_id


def insert_tasks(meeting_id: int, created_at: str, tasks: list[dict[str, Any]]) -> None:
    if not tasks:
        return

    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO tasks (
                meeting_id, task, owner, mapped_account_id, priority, deadline,
                timestamp, jira_issue_id, jira_status, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    meeting_id,
                    task["task"],
                    task["owner"],
                    task.get("mapped_account_id"),
                    task["priority"],
                    task.get("deadline"),
                    task.get("timestamp"),
                    task.get("jira_issue_id"),
                    task.get("jira_status", "pending"),
                    created_at,
                    created_at,
                )
                for task in tasks
            ],
        )
        connection.commit()
    connection.close()


def update_task_jira_status(
    task_name: str,
    owner: str,
    jira_status: str,
    jira_issue_id: str | None,
    updated_at: str,
) -> None:
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE tasks
            SET jira_status = %s, jira_issue_id = %s, updated_at = %s
            WHERE task = %s AND owner = %s
            """,
            (jira_status, jira_issue_id, updated_at, task_name, owner),
        )
        connection.commit()
    connection.close()


def fetch_all_tasks() -> list[dict[str, Any]]:
    connection = get_connection()
    with connection.cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT
                id, meeting_id, task, owner, mapped_account_id, priority, deadline,
                timestamp, jira_issue_id, jira_status, created_at, updated_at
            FROM tasks
            ORDER BY created_at DESC, id DESC
            """
        )
        rows = cursor.fetchall()
    connection.close()
    return rows
