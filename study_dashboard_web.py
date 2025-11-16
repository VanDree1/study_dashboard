#!/usr/bin/env python3
"""Simple Flask web dashboard for study tasks."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from flask import Flask, render_template_string

from study_dashboard import (
    GROUP_TITLES,
    TASKS_FILE,
    TIMEZONE,
    format_due_display,
    group_task,
    load_tasks,
)
from courses_client import get_active_courses

app = Flask(__name__)
COURSES_FILE = Path(__file__).with_name("canvas_courses.json")

SECTION_CONFIG: Tuple[Tuple[str, str, str], ...] = (
    ("TODAY", "Today", "#ffd5cc"),
    ("THIS WEEK", "This Week", "#ffe8b3"),
    ("LATER", "Later", "#d7e8ff"),
)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Study Dashboard</title>
    <style>
        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #f4f6fb;
            margin: 0;
            padding: 20px;
            color: #222;
        }
        h1 {
            text-align: center;
            margin-bottom: 20px;
        }
        .layout {
            display: grid;
            grid-template-columns: minmax(260px, 320px) 1fr;
            gap: 20px;
            align-items: start;
        }
        @media (max-width: 768px) {
            .layout {
                grid-template-columns: 1fr;
            }
        }
        .columns {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .sidebar .column {
            flex: none;
        }
        .column {
            flex: 1 1 280px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            overflow: hidden;
        }
        .column-header {
            padding: 16px;
            font-size: 1.1rem;
            font-weight: 600;
            color: #333;
        }
        .tasks {
            padding: 16px;
        }
        .task-card {
            border: 1px solid #e1e5ee;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 12px;
            background: #fafbff;
        }
        .task-card:last-child {
            margin-bottom: 0;
        }
        .task-title {
            font-weight: 600;
            margin: 0;
        }
        .task-meta {
            margin: 6px 0 0;
            font-size: 0.95rem;
            color: #555;
        }
        .task-meta .due-inline {
            font-size: 0.85rem;
            color: #777;
            margin-left: 4px;
        }
        .task-course {
            font-size: 0.9rem;
            color: #444;
        }
        .course-item {
            padding: 10px;
            border-bottom: 1px solid #ecf0f8;
        }
        .course-item:last-child {
            border-bottom: none;
        }
        .course-name {
            font-weight: 600;
            margin: 0;
        }
        .course-code {
            color: #555;
            font-size: 0.9rem;
            margin: 2px 0 0;
        }
        .empty {
            color: #999;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>Study Dashboard</h1>
    <div class="layout">
        <aside class="sidebar">
            <div class="column">
                <div class="column-header" style="background-color: #e3f6d0;">Aktuella kurser</div>
                <div class="tasks">
                    {% if courses %}
                        {% for course in courses %}
                            <div class="course-item">
                                <p class="course-name">{{ course.name }}</p>
                                {% if course.code %}
                                <p class="course-code">{{ course.code }}</p>
                                {% endif %}
                            </div>
                        {% endfor %}
                    {% else %}
                        <p class="empty">No course data.</p>
                    {% endif %}
                </div>
            </div>
        </aside>
        <div class="columns">
            {% for key, label, color in sections %}
            <div class="column">
                <div class="column-header" style="background-color: {{ color }};">{{ label }}</div>
                <div class="tasks">
                    {% if grouped[key] %}
                        {% for task in grouped[key] %}
                            <div class="task-card">
                                <p class="task-title">{{ task.title }}</p>
                                <p class="task-course">{{ task.course }} • {{ task.type|title }}</p>
                                <p class="task-meta">Due: {{ task.due_nice }} <span class="due-inline">{{ task.due_display }}</span></p>
                            </div>
                        {% endfor %}
                    {% else %}
                        <p class="empty">No tasks.</p>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
            <div class="column">
                <div class="column-header" style="background-color: #fbe4ff;">Courses</div>
                <div class="tasks">
                    {% if canvas_courses %}
                        {% for course in canvas_courses %}
                            <div class="course-item">
                                <p class="course-name">{{ course.name }}</p>
                                {% if course.code %}
                                <p class="course-code">{{ course.code }}</p>
                                {% endif %}
                            </div>
                        {% endfor %}
                    {% else %}
                        <p class="empty">No active courses.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""


def build_grouped_tasks() -> Dict[str, List[Dict[str, object]]]:
    """Load tasks and arrange them for the template."""
    tasks = load_tasks(TASKS_FILE)
    today = datetime.now(TIMEZONE).date()

    grouped: Dict[str, List[Dict[str, object]]] = {title: [] for title in GROUP_TITLES}
    for task in tasks:
        group = group_task(task["due_datetime"], today)  # type: ignore[arg-type]
        task_copy = dict(task)
        due_dt: datetime = task["due_datetime"]  # type: ignore[assignment]
        task_copy["due_display"] = format_due_display(task, today)
        due_time_str = task.get("due_time")
        if due_time_str:
            task_copy["due_nice"] = due_dt.strftime("%A, %d %B %Y %H:%M")
        else:
            task_copy["due_nice"] = due_dt.strftime("%A, %d %B %Y")
        grouped[group].append(task_copy)

    for chunk in grouped.values():
        chunk.sort(key=lambda t: t["due_datetime"])  # type: ignore[arg-type]
    return grouped


def load_courses() -> List[Dict[str, str]]:
    try:
        text = COURSES_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except OSError:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    courses: List[Dict[str, str]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        code_value = entry.get("code")
        code = code_value.strip() if isinstance(code_value, str) else ""
        courses.append({"name": name.strip(), "code": code})
    return courses


@app.route("/")
def dashboard() -> str:
    grouped = build_grouped_tasks()
    courses = load_courses()
    try:
        canvas_courses = get_active_courses()
    except RuntimeError as exc:
        app.logger.error("Failed to fetch Canvas courses: %s", exc)
        canvas_courses = []
    return render_template_string(
        HTML_TEMPLATE,
        grouped=grouped,
        sections=SECTION_CONFIG,
        courses=courses,
        canvas_courses=canvas_courses,
    )


if __name__ == "__main__":
    print("Open http://127.0.0.1:5000 in your browser to see your study dashboard.")
    app.run(host="127.0.0.1", port=5000, debug=False)
