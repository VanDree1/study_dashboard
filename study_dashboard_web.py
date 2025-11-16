#!/usr/bin/env python3
"""Simple Flask web dashboard for study tasks."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
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
SCIENTIFIC_SCHEDULE_FILE = Path(__file__).with_name("scientific_methods_schedule.json")

try:
    _schedule_text = SCIENTIFIC_SCHEDULE_FILE.read_text(encoding="utf-8")
    _schedule_data = json.loads(_schedule_text)
    if isinstance(_schedule_data, list):
        scientific_schedule = _schedule_data
    else:
        scientific_schedule = []
except (OSError, json.JSONDecodeError):
    scientific_schedule = []

scientific_methods_schedule = [
    {
        "date": "2025-11-18",
        "title": "L3 – Coding and Analysis of Qualitative Data",
        "type": "Lecture",
        "time": "10:15–12:00",
        "location": "Hörsal 4, Ekonomikum",
        "teacher": "Linda Wedlin",
    },
    {
        "date": "2025-11-24",
        "title": "L4 – Analyzing, Structuring & Presenting Qualitative Data",
        "type": "Lecture",
        "time": "10:15–12:00",
        "location": "Hörsal 4, Ekonomikum",
        "teacher": "Linda Wedlin",
    },
    {
        "date": "2025-11-25",
        "title": "L5 – Data Collection & Interviews",
        "type": "Lecture",
        "time": "15:15–17:00",
        "location": "Hörsal 4, Ekonomikum",
        "teacher": "Anna Bengtson",
    },
    {
        "date": "2025-12-02",
        "title": "L6 – Regression Analysis (Introduction)",
        "type": "Lecture",
        "time": "10:15–12:00",
        "location": "Hörsal 4, Ekonomikum",
        "teacher": "Joachim Landström",
    },
    {
        "date": "2025-12-02",
        "title": "L7 – Panel Data Regressions",
        "type": "Lecture",
        "time": "13:15–15:00",
        "location": "Hörsal 3, Ekonomikum",
        "teacher": "Joachim Landström",
    },
    {
        "date": "2025-12-08",
        "title": "L8 – Event Study Method",
        "type": "Lecture",
        "time": "10:15–12:00",
        "location": "Hörsal 4, Ekonomikum",
        "teacher": "Joachim Landström",
    },
    {
        "date": "2025-12-17",
        "title": "L9 – Portfolio Sorts Method",
        "type": "Lecture",
        "time": "10:15–12:00",
        "location": "Hörsal 3, Ekonomikum",
        "teacher": "Joachim Landström",
    },
    {
        "date": "2026-01-07",
        "title": "L10 – Summary & Exam Preparations",
        "type": "Lecture",
        "time": "13:15–14:00",
        "location": "Hörsal 4, Ekonomikum",
        "teacher": "Anna Bengtson & Joachim Landström",
    },
    {
        "date": "2025-11-21",
        "title": "WS2 – Coding & Analysis",
        "type": "Workshop (Qualitative)",
        "time": "10:15–12:00",
        "location": "Ekonomikum K334",
        "teacher": "Karim Nasr",
    },
    {
        "date": "2025-11-28",
        "title": "WS3 – Presenting Qualitative Research",
        "type": "Workshop (Qualitative)",
        "time": "08:15–10:00",
        "location": "Ekonomikum K334",
        "teacher": "Karim Nasr",
    },
    {
        "date": "2025-12-05",
        "title": "WS4A – Panel Regression",
        "type": "Workshop (Quantitative)",
        "time": "10:15–12:00",
        "location": "Ekonomikum K336",
        "teacher": "Haojun Hu",
    },
    {
        "date": "2025-12-12",
        "title": "WS5A – Event Study Method",
        "type": "Workshop (Quantitative)",
        "time": "10:15–12:00",
        "location": "Ekonomikum A138",
        "teacher": "Joachim Landström",
    },
    {
        "date": "2025-12-19",
        "title": "WS6A – Portfolio Sorts",
        "type": "Workshop (Quantitative)",
        "time": "10:15–12:00",
        "location": "Ekonomikum B153",
        "teacher": "Joachim Landström",
    },
    {
        "date": "2026-01-13",
        "title": "Written Exam (Multiple choice)",
        "type": "Exam",
        "time": "14:00–16:00",
        "location": "Inspera / according to Ladok",
        "teacher": "",
    },
]

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
        .muted {
            color: #666;
            font-size: 0.85rem;
            margin: 4px 0 0;
        }
        .scientific-card .next-up {
            font-weight: 600;
            margin: 0 0 8px;
            color: #333;
        }
        .timeline {
            margin-top: 8px;
        }
        .timeline-row {
            display: grid;
            grid-template-columns: 90px 1fr;
            gap: 12px;
            padding: 12px 0;
            border-bottom: 1px solid #eef0f5;
        }
        .timeline-row:last-child {
            border-bottom: none;
        }
        .scientific-card[data-expanded="false"] .timeline-row.collapsed-row {
            display: none;
        }
        .timeline-date {
            font-weight: 600;
            color: #555;
            font-size: 0.95rem;
        }
        .timeline-details .task-title {
            margin-bottom: 4px;
        }
        .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin: 4px 0 6px;
        }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-kind-workshop {
            background: #ede9fe;
            color: #5b38a4;
        }
        .badge-kind-hand-in {
            background: #e5f7ea;
            color: #297347;
        }
        .badge-kind-exam {
            background: #fde4e4;
            color: #b03030;
        }
        .badge-track-qualitative {
            background: #e3f2ff;
            color: #215b8a;
        }
        .badge-track-quantitative {
            background: #fff2cc;
            color: #927200;
        }
        .badge-track-both {
            background: #f0f0f0;
            color: #555;
        }
        .badge-group {
            background: #f3e5f5;
            color: #7b1fa2;
        }
        .toggle-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-top: 12px;
            padding: 8px 14px;
            border: none;
            border-radius: 999px;
            background: #eef0fb;
            color: #333;
            font-weight: 600;
            cursor: pointer;
        }
        .toggle-button:hover {
            background: #dfe2f6;
        }
        .schedule-toggle {
            padding: 4px 12px;
            border-radius: 999px;
            border: none;
            background: #eef5ff;
            color: #274c77;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.9rem;
        }
        .schedule-toggle:hover {
            background: #d7e9ff;
        }
        .header-flex {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }
        .schedule-card {
            position: relative;
        }
        .schedule-card .full-mode-text {
            display: none;
        }
        .schedule-card[data-mode="full"] .full-mode-text {
            display: block;
        }
        .schedule-card[data-mode="full"] .week-mode-text {
            display: none;
        }
        .schedule-card[data-mode="week"] .schedule-full-view {
            display: none;
        }
        .schedule-card[data-mode="full"] .schedule-week-view {
            display: none;
        }
        .schedule-subtitle {
            margin: 0 0 12px;
            font-weight: 600;
            color: #333;
        }
        .schedule-month {
            margin-bottom: 18px;
        }
        .schedule-month:last-child {
            margin-bottom: 0;
        }
        .schedule-month-title {
            font-weight: 600;
            color: #333;
            margin: 0 0 8px;
        }
        .schedule-event {
            display: grid;
            grid-template-columns: 90px 1fr;
            gap: 12px;
            padding: 10px 0;
            border-bottom: 1px solid #eef0f5;
        }
        .schedule-event:last-child {
            border-bottom: none;
        }
        .schedule-date-block {
            text-align: left;
        }
        .schedule-date-day {
            display: block;
            font-weight: 700;
            color: #333;
        }
        .schedule-date-weekday {
            display: block;
            font-size: 0.85rem;
            color: #777;
        }
        .schedule-body .task-title {
            margin-bottom: 4px;
        }
        .schedule-body .task-meta {
            margin: 2px 0;
        }
        .schedule-badge {
            display: inline-flex;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .schedule-badge-lecture {
            background: #e8f1ff;
            color: #1e5fad;
        }
        .schedule-badge-workshop-qual {
            background: #fce8ff;
            color: #8c2ca3;
        }
        .schedule-badge-workshop-quant {
            background: #fff1d6;
            color: #a26800;
        }
        .schedule-badge-workshop {
            background: #f1f5ff;
            color: #324d8f;
        }
        .schedule-badge-exam {
            background: #ffe2e2;
            color: #b13232;
        }
        .schedule-badge-other {
            background: #ececec;
            color: #555;
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
            <div class="column">
                <div class="column-header" style="background-color: #e3ddff;">Scientific Methods – Upcoming</div>
                {% set total_events = scientific_methods_events|length %}
                {% set hidden_count = total_events - 3 %}
                <div class="tasks scientific-card" id="scientific-methods-card" data-expanded="false">
                    {% if scientific_methods_events %}
                        {% set next_event = scientific_methods_events[0] %}
                        <p class="next-up">
                            Next up: {{ next_event.full_date }}{% if next_event.time_range %}, {{ next_event.time_range }}{% endif %} – {{ next_event.title }}
                        </p>
                        <div class="timeline">
                            {% for event in scientific_methods_events %}
                                <div class="timeline-row{% if loop.index0 >= 3 %} collapsed-row{% endif %}">
                                    <div class="timeline-date">{{ event.date_label }}</div>
                                    <div class="timeline-details">
                                        <p class="task-title">{{ event.title }}</p>
                                        <div class="badge-row">
                                            <span class="badge badge-kind badge-kind-{{ event.kind_class }}">{{ event.kind }}</span>
                                            {% if event.track %}
                                            <span class="badge badge-track badge-track-{{ event.track_class }}">{{ event.track }}</span>
                                            {% endif %}
                                            {% if event.group %}
                                            <span class="badge badge-group">{{ event.group }}</span>
                                            {% endif %}
                                        </div>
                                        <p class="task-meta">
                                            {{ event.full_date }}
                                            {% if event.time_range %}, {{ event.time_range }}{% endif %}
                                        </p>
                                        {% if event.location %}
                                        <p class="muted">{{ event.location }}</p>
                                        {% endif %}
                                        {% if event.submission %}
                                        <p class="muted">{{ event.submission }}</p>
                                        {% endif %}
                                    </div>
                                </div>
                            {% endfor %}
                        </div>
                        {% if hidden_count > 0 %}
                        <button
                            class="toggle-button"
                            type="button"
                            id="scientific-methods-toggle"
                            data-hidden-count="{{ hidden_count }}"
                            data-collapsed-label="Show all ({{ hidden_count }} more)"
                            data-expanded-label="Show less"
                        >
                            Show all ({{ hidden_count }} more)
                        </button>
                        {% endif %}
                    {% else %}
                        <p class="muted">No upcoming items.</p>
                    {% endif %}
                </div>
            </div>
            <div class="column">
                <div class="column-header" style="background-color: #dff3ff;">
                    <div class="header-flex">
                        <span>Scientific Methods – Schedule</span>
                        {% if scientific_methods_schedule_full %}
                        <button
                            class="schedule-toggle"
                            type="button"
                            id="schedule-mode-toggle"
                            data-week-label="Show full schedule"
                            data-full-label="Show this week only"
                        >
                            Show full schedule
                        </button>
                        {% endif %}
                    </div>
                </div>
                <div class="tasks schedule-card" id="scientific-schedule-card" data-mode="week">
                    <p class="schedule-subtitle week-mode-text">
                        This week:
                        {% if scientific_methods_schedule_week_range %}
                            {{ scientific_methods_schedule_week_range.start }} – {{ scientific_methods_schedule_week_range.end }}
                        {% endif %}
                        {% if not scientific_methods_schedule_this_week %}
                            <span class="muted">No scheduled lectures or workshops.</span>
                        {% endif %}
                    </p>
                    <p class="schedule-subtitle full-mode-text">Full schedule for Scientific Methods</p>
                    <div class="schedule-week-view">
                        {% if scientific_methods_schedule_this_week %}
                            {% for event in scientific_methods_schedule_this_week %}
                                <div class="schedule-event">
                                    <div class="schedule-date-block">
                                        <span class="schedule-date-day">{{ event.date_display }}</span>
                                        <span class="schedule-date-weekday">{{ event.weekday }}</span>
                                    </div>
                                    <div class="schedule-body">
                                        <p class="task-title">{{ event.title }}</p>
                                        {% if event.type %}
                                        <span class="schedule-badge schedule-badge-{{ event.badge_class }}">{{ event.type }}</span>
                                        {% endif %}
                                        {% if event.time_display or event.location %}
                                        <p class="task-meta">
                                            {% if event.time_display %}
                                                {{ event.time_display }}
                                            {% endif %}
                                            {% if event.time_display and event.location %}
                                                ·
                                            {% endif %}
                                            {% if event.location %}
                                                {{ event.location }}
                                            {% endif %}
                                        </p>
                                        {% endif %}
                                        {% if event.teacher %}
                                        <p class="muted">{{ event.teacher }}</p>
                                        {% endif %}
                                    </div>
                                </div>
                            {% endfor %}
                        {% else %}
                            <p class="muted">No events this week. Use “Show full schedule” to see the full plan.</p>
                            {% if scientific_methods_schedule_full %}
                            <div class="schedule-fallback">
                                {% for event in scientific_methods_schedule_full[:3] %}
                                    <div class="schedule-event">
                                        <div class="schedule-date-block">
                                            <span class="schedule-date-day">{{ event.date_display }}</span>
                                            <span class="schedule-date-weekday">{{ event.weekday }}</span>
                                        </div>
                                        <div class="schedule-body">
                                            <p class="task-title">{{ event.title }}</p>
                                            {% if event.type %}
                                            <span class="schedule-badge schedule-badge-{{ event.badge_class }}">{{ event.type }}</span>
                                            {% endif %}
                                            {% if event.time_display or event.location %}
                                            <p class="task-meta">
                                                {% if event.time_display %}
                                                    {{ event.time_display }}
                                                {% endif %}
                                                {% if event.time_display and event.location %}
                                                    ·
                                                {% endif %}
                                                {% if event.location %}
                                                    {{ event.location }}
                                                {% endif %}
                                            </p>
                                            {% endif %}
                                            {% if event.teacher %}
                                            <p class="muted">{{ event.teacher }}</p>
                                            {% endif %}
                                        </div>
                                    </div>
                                {% endfor %}
                            </div>
                            {% endif %}
                        {% endif %}
                    </div>
                    <div class="schedule-full-view">
                        {% if scientific_methods_schedule_full %}
                            {% for month_label, events in scientific_methods_schedule_full|groupby('month_label') %}
                                <div class="schedule-month">
                                    <p class="schedule-month-title">{{ month_label }}</p>
                                    {% for event in events %}
                                        <div class="schedule-event">
                                            <div class="schedule-date-block">
                                                <span class="schedule-date-day">{{ event.date_display }}</span>
                                                <span class="schedule-date-weekday">{{ event.weekday }}</span>
                                            </div>
                                            <div class="schedule-body">
                                                <p class="task-title">{{ event.title }}</p>
                                                {% if event.type %}
                                                <span class="schedule-badge schedule-badge-{{ event.badge_class }}">{{ event.type }}</span>
                                                {% endif %}
                                                {% if event.time_display or event.location %}
                                                <p class="task-meta">
                                                    {% if event.time_display %}
                                                        {{ event.time_display }}
                                                    {% endif %}
                                                    {% if event.time_display and event.location %}
                                                        ·
                                                    {% endif %}
                                                    {% if event.location %}
                                                        {{ event.location }}
                                                    {% endif %}
                                                </p>
                                                {% endif %}
                                                {% if event.teacher %}
                                                <p class="muted">{{ event.teacher }}</p>
                                                {% endif %}
                                            </div>
                                        </div>
                                    {% endfor %}
                                </div>
                            {% endfor %}
                        {% else %}
                            <p class="empty">No scheduled events yet.</p>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
    document.addEventListener("DOMContentLoaded", function () {
        var card = document.getElementById("scientific-methods-card");
        var toggle = document.getElementById("scientific-methods-toggle");
        if (card && toggle) {
            var collapsedLabel = toggle.dataset.collapsedLabel || toggle.textContent;
            var expandedLabel = toggle.dataset.expandedLabel || "Show less";
            toggle.addEventListener("click", function () {
                var expanded = card.getAttribute("data-expanded") === "true";
                card.setAttribute("data-expanded", expanded ? "false" : "true");
                toggle.textContent = expanded ? collapsedLabel : expandedLabel;
            });
        }
        var scheduleCard = document.getElementById("scientific-schedule-card");
        var scheduleToggle = document.getElementById("schedule-mode-toggle");
        if (scheduleCard && scheduleToggle) {
            var weekLabel = scheduleToggle.dataset.weekLabel || "Show full schedule";
            var fullLabel = scheduleToggle.dataset.fullLabel || "Show this week only";
            scheduleToggle.textContent = weekLabel;
            scheduleToggle.addEventListener("click", function () {
                var mode = scheduleCard.getAttribute("data-mode") === "full" ? "full" : "week";
                var nextMode = mode === "week" ? "full" : "week";
                scheduleCard.setAttribute("data-mode", nextMode);
                scheduleToggle.textContent = nextMode === "week" ? weekLabel : fullLabel;
            });
        }
    });
    </script>
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


def _parse_date_string(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_datetime_string(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M")
        except ValueError:
            return None


def _split_time_range(value: str | None) -> Tuple[str | None, str | None]:
    if not value:
        return None, None
    normalized = value.replace("–", "-").replace("—", "-")
    parts = [part.strip() for part in normalized.split("-", 1)]
    if len(parts) == 2:
        start, end = parts
        return (start or None, end or None)
    return (parts[0] or None, None)


def _find_schedule_entry(
    *, code: str | None = None, kind: str | None = None, title: str | None = None
) -> Dict[str, object] | None:
    for entry in scientific_schedule:
        if not isinstance(entry, dict):
            continue
        if code is not None and entry.get("code") != code:
            continue
        if kind is not None and entry.get("kind") != kind:
            continue
        if title is not None and entry.get("title") != title:
            continue
        return entry
    return None


def _extract_schedule_details(
    *,
    code: str | None = None,
    kind: str | None = None,
    title: str | None = None,
    use_deadline: bool = False,
) -> Tuple[date | None, str | None, str | None, str | None, str | None]:
    entry = _find_schedule_entry(code=code, kind=kind, title=title)
    date_value: date | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    details: str | None = None
    if entry:
        if use_deadline:
            dt = _parse_datetime_string(entry.get("deadline"))
            if dt:
                date_value = dt.date()
                start_time = dt.strftime("%H:%M")
        else:
            date_value = _parse_date_string(entry.get("date"))
            start_time, end_time = _split_time_range(entry.get("time"))
        loc_value = entry.get("location")
        if isinstance(loc_value, str):
            location = loc_value.strip()
        details_value = entry.get("details")
        if isinstance(details_value, str):
            details = details_value.strip()
    return date_value, start_time, end_time, location, details


def _build_scientific_methods_events() -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []

    def create_event(
        event_id: str,
        *,
        title: str,
        event_kind: str,
        track: str,
        group: str | None = None,
        date_value: date | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        location: str | None = None,
        submission: str | None = None,
    ) -> None:
        events.append(
            {
                "id": event_id,
                "title": title,
                "kind": event_kind,
                "track": track,
                "group": group,
                "date": date_value,
                "start_time": start_time,
                "end_time": end_time,
                "location": location or "",
                "submission": submission or "",
            }
        )

    # Qualitative track
    create_event(
        "ws1_workshop",
        title="WS1 – Topic, purpose & design",
        event_kind="Workshop",
        track="Qualitative",
    )

    ws1_deadline = _extract_schedule_details(code="WS1", kind="deadline", use_deadline=True)
    create_event(
        "ws1_handin",
        title="WS1 – Hand-in",
        event_kind="Hand-in",
        track="Qualitative",
        date_value=ws1_deadline[0],
        start_time=ws1_deadline[1],
        submission=ws1_deadline[4] or "Submission in Studium",
    )

    ws2_workshop = _extract_schedule_details(code="WS2", kind="workshop")
    create_event(
        "ws2_workshop",
        title="WS2 – Coding & Analysis",
        event_kind="Workshop",
        track="Qualitative",
        date_value=ws2_workshop[0],
        start_time=ws2_workshop[1],
        end_time=ws2_workshop[2],
        location=ws2_workshop[3],
    )

    ws2_deadline = _extract_schedule_details(code="WS2", kind="deadline", use_deadline=True)
    create_event(
        "ws2_handin",
        title="WS2 – Hand-in",
        event_kind="Hand-in",
        track="Qualitative",
        date_value=ws2_deadline[0],
        start_time=ws2_deadline[1],
        submission=ws2_deadline[4] or "Submission in Studium",
    )

    ws3_workshop = _extract_schedule_details(code="WS3", kind="workshop")
    create_event(
        "ws3_workshop",
        title="WS3 – Presenting Qualitative Research",
        event_kind="Workshop",
        track="Qualitative",
        date_value=ws3_workshop[0],
        start_time=ws3_workshop[1],
        end_time=ws3_workshop[2],
        location=ws3_workshop[3],
    )

    ws3_deadline = _extract_schedule_details(code="WS3", kind="deadline", use_deadline=True)
    create_event(
        "ws3_handin",
        title="WS3 – Hand-in",
        event_kind="Hand-in",
        track="Qualitative",
        date_value=ws3_deadline[0],
        start_time=ws3_deadline[1],
        submission=ws3_deadline[4] or "Submission in Studium",
    )

    # Quantitative AF-track
    ws4a_workshop = _extract_schedule_details(code="WS4A", kind="workshop")
    create_event(
        "ws4a_workshop",
        title="WS4A – Panel Regression",
        event_kind="Workshop",
        track="Quantitative",
        group="P1–P3",
        date_value=ws4a_workshop[0],
        start_time=ws4a_workshop[1],
        end_time=ws4a_workshop[2],
        location=ws4a_workshop[3],
    )

    ws4a_pre = _extract_schedule_details(code="WS4A_pre", kind="deadline", use_deadline=True)
    create_event(
        "ws4a_pre_assignment",
        title="WS4A – Pre-assignment",
        event_kind="Hand-in",
        track="Quantitative",
        group="P1–P3",
        date_value=ws4a_pre[0],
        start_time=ws4a_pre[1],
        submission=ws4a_pre[4] or "Script + screenshot online",
    )

    ws5a_workshop = _extract_schedule_details(code="WS5A", kind="workshop")
    # Date/time TBA in Studium
    create_event(
        "ws5a_workshop",
        title="WS5A – Event Study",
        event_kind="Workshop",
        track="Quantitative",
        group="P1–P3",
        location=ws5a_workshop[3],
    )

    create_event(
        "ws5a_handin",
        title="WS5A – Hand-in",
        event_kind="Hand-in",
        track="Quantitative",
        group="P1–P3",
        submission="Deadline: 1 working day after the workshop",
    )

    ws6a_workshop = _extract_schedule_details(code="WS6A", kind="workshop")
    # Date/time TBA
    create_event(
        "ws6a_workshop",
        title="WS6A – Portfolio Sorts",
        event_kind="Workshop",
        track="Quantitative",
        group="P1–P3",
        location=ws6a_workshop[3],
    )

    create_event(
        "ws6a_handin",
        title="WS6A – Hand-in",
        event_kind="Hand-in",
        track="Quantitative",
        group="P1–P3",
        submission="Deadline: 1 working day after the workshop",
    )

    exam_entry = _extract_schedule_details(
        kind="exam", title="Multiple Choice Exam (Individual)"
    )
    create_event(
        "exam_mc",
        title="Multiple Choice Exam (Individual)",
        event_kind="Exam",
        track="Both",
        location="Inspera online",
        submission=exam_entry[4] or "Exam in Inspera.",
    )

    return events


scientific_methods_events = _build_scientific_methods_events()


def get_future_scientific_methods_events(
    today: date, limit: int = 10
) -> List[Dict[str, object]]:
    def sort_key(event: Dict[str, object]) -> Tuple[int, date, str]:
        event_date = event.get("date")
        start_time = event.get("start_time") or "99:99"
        if isinstance(event_date, date):
            return (0, event_date, str(start_time))
        return (1, date.max, str(start_time))

    filtered: List[Dict[str, object]] = []
    for event in scientific_methods_events:
        event_date = event.get("date")
        if isinstance(event_date, date):
            if event_date >= today:
                filtered.append(event)
        else:
            filtered.append(event)
    filtered.sort(key=sort_key)
    return filtered[:limit]


def _schedule_badge_class(type_value: str) -> str:
    lowered = type_value.lower()
    if "lecture" in lowered:
        return "lecture"
    if "exam" in lowered:
        return "exam"
    if "quantitative" in lowered:
        return "workshop-quant"
    if "qualitative" in lowered:
        return "workshop-qual"
    if "workshop" in lowered:
        return "workshop"
    return "other"


def _format_scientific_methods_schedule(
    items: List[Dict[str, str]]
) -> List[Dict[str, object]]:
    entries: List[Dict[str, object]] = []
    for entry in items:
        date_value = _parse_date_string(entry.get("date"))
        if not date_value:
            continue
        start_time, end_time = _split_time_range(entry.get("time"))
        time_display = ""
        if start_time and end_time:
            time_display = f"{start_time}\u2013{end_time}"
        elif start_time:
            time_display = start_time
        type_value = entry.get("type", "")
        entries.append(
            {
                "title": entry.get("title", ""),
                "type": type_value,
                "time_display": time_display or entry.get("time", ""),
                "location": entry.get("location", ""),
                "teacher": entry.get("teacher", ""),
                "date_obj": date_value,
                "date_display": date_value.strftime("%d %b"),
                "weekday": date_value.strftime("%a"),
                "month_label": date_value.strftime("%B %Y"),
                "badge_class": _schedule_badge_class(type_value),
                "time_sort": start_time or "",
            }
        )
    entries.sort(key=lambda ev: (ev["date_obj"], ev["time_sort"]))
    return entries


def _copy_schedule_entry_for_template(entry: Dict[str, object]) -> Dict[str, object]:
    return {
        "title": entry.get("title", ""),
        "type": entry.get("type", ""),
        "time_display": entry.get("time_display", ""),
        "location": entry.get("location", ""),
        "teacher": entry.get("teacher", ""),
        "date_display": entry.get("date_display", ""),
        "weekday": entry.get("weekday", ""),
        "month_label": entry.get("month_label", ""),
        "badge_class": entry.get("badge_class", "other"),
    }


def get_scientific_methods_schedule_this_week(
    entries: List[Dict[str, object]], today: date
) -> List[Dict[str, object]]:
    end_date = today + timedelta(days=7)
    return [
        _copy_schedule_entry_for_template(entry)
        for entry in entries
        if today <= entry["date_obj"] <= end_date
    ]


def get_scientific_methods_schedule_full(
    entries: List[Dict[str, object]]
) -> List[Dict[str, object]]:
    return [_copy_schedule_entry_for_template(entry) for entry in entries]


@app.route("/")
def dashboard() -> str:
    grouped = build_grouped_tasks()
    courses = load_courses()
    try:
        canvas_courses = get_active_courses()
    except RuntimeError as exc:
        app.logger.error("Failed to fetch Canvas courses: %s", exc)
        canvas_courses = []
    today = datetime.now(TIMEZONE).date()
    upcoming_events: List[Dict[str, object]] = []
    for event in get_future_scientific_methods_events(today):
        event_copy = dict(event)
        event_date = event_copy.get("date")
        if isinstance(event_date, date):
            event_copy["has_date"] = True
            event_copy["date_label"] = f"{event_date.day} {event_date.strftime('%b')}"
            event_copy["full_date"] = f"{event_date.day} {event_date.strftime('%b %Y')}"
        else:
            event_copy["has_date"] = False
            event_copy["date_label"] = "Date TBA"
            event_copy["full_date"] = "Date TBA"
        start_time = event_copy.get("start_time")
        end_time = event_copy.get("end_time")
        if start_time and end_time:
            event_copy["time_range"] = f"{start_time}\u2013{end_time}"
        elif start_time:
            event_copy["time_range"] = start_time
        else:
            event_copy["time_range"] = ""
        kind_value = str(event_copy.get("kind", "")).lower().replace(" ", "-")
        event_copy["kind_class"] = kind_value
        track_value = str(event_copy.get("track", "")).lower().replace(" ", "-")
        event_copy["track_class"] = track_value
        if not event_copy.get("location"):
            event_copy["location"] = ""
        if not event_copy.get("submission"):
            event_copy["submission"] = ""
        upcoming_events.append(event_copy)
    formatted_schedule_entries = _format_scientific_methods_schedule(
        scientific_methods_schedule
    )
    schedule_this_week = get_scientific_methods_schedule_this_week(
        formatted_schedule_entries, today
    )
    schedule_full = get_scientific_methods_schedule_full(formatted_schedule_entries)
    week_range = {
        "start": today.strftime("%d %b"),
        "end": (today + timedelta(days=7)).strftime("%d %b %Y"),
    }
    return render_template_string(
        HTML_TEMPLATE,
        grouped=grouped,
        sections=SECTION_CONFIG,
        courses=courses,
        canvas_courses=canvas_courses,
        scientific_methods_events=upcoming_events,
        scientific_methods_schedule=scientific_methods_schedule,
        scientific_methods_schedule_this_week=schedule_this_week,
        scientific_methods_schedule_full=schedule_full,
        scientific_methods_schedule_week_range=week_range,
    )


if __name__ == "__main__":
    print("Open http://127.0.0.1:5000 in your browser to see your study dashboard.")
    app.run(host="127.0.0.1", port=5000, debug=False)
