#!/usr/bin/env python3
"""Simple CLI study dashboard grouped by due date."""

from __future__ import annotations

import json
from datetime import date, datetime, time
from pathlib import Path
from typing import Dict, List
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("Europe/Stockholm")
TASKS_FILE = Path(__file__).with_name("tasks.json")

GROUP_TITLES = ("TODAY", "THIS WEEK", "LATER")


def load_tasks(path: Path) -> List[Dict[str, object]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Could not find {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc

    parsed_tasks: List[Dict[str, object]] = []
    for raw in data:
        try:
            due_date = datetime.strptime(raw["due_date"], "%Y-%m-%d").date()
        except KeyError as exc:
            raise SystemExit(f"Missing due_date in task: {raw}") from exc
        due_time_str = raw.get("due_time") or ""
        if due_time_str:
            due_time = datetime.strptime(due_time_str, "%H:%M").time()
        else:
            due_time = time(hour=23, minute=59)

        due_datetime = datetime.combine(due_date, due_time, tzinfo=TIMEZONE)
        parsed_tasks.append(
            {
                "title": raw["title"],
                "course": raw["course"],
                "type": raw["type"],
                "due_time": due_time_str,
                "due_datetime": due_datetime,
            }
        )
    return parsed_tasks


def group_task(due_dt: datetime, today: date) -> str:
    if due_dt.date() == today:
        return "TODAY"

    today_iso = today.isocalendar()
    due_iso = due_dt.date().isocalendar()
    if due_iso.year == today_iso.year and due_iso.week == today_iso.week:
        return "THIS WEEK"
    return "LATER"


def format_due_display(task: Dict[str, object], today: date) -> str:
    due_dt: datetime = task["due_datetime"]  # type: ignore[assignment]
    due_time_str = task["due_time"]
    if due_dt.date() == today and due_time_str:
        return f"({due_dt.strftime('%H:%M')})"
    if due_time_str:
        return f"({due_dt.strftime('%Y-%m-%d %H:%M')})"
    return f"({due_dt.strftime('%Y-%m-%d')})"


def print_group(title: str, tasks: List[Dict[str, object]], today: date) -> None:
    print(f"{title}:")
    if not tasks:
        print("No tasks.\n")
        return

    for task in tasks:
        due_display = format_due_display(task, today)
        print(f"- [{task['course']}] {task['title']} {due_display}  [{task['type']}]")
    print()


def main() -> None:
    tasks = load_tasks(TASKS_FILE)
    today = datetime.now(TIMEZONE).date()

    grouped: Dict[str, List[Dict[str, object]]] = {title: [] for title in GROUP_TITLES}
    for task in tasks:
        grouping = group_task(task["due_datetime"], today)  # type: ignore[arg-type]
        grouped[grouping].append(task)

    for task_list in grouped.values():
        task_list.sort(key=lambda t: t["due_datetime"])  # type: ignore[arg-type]

    for title in GROUP_TITLES:
        print_group(title, grouped[title], today)


if __name__ == "__main__":
    main()
