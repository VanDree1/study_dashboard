#!/usr/bin/env python3
"""Simple Flask web dashboard for study tasks."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from itertools import groupby
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

accounting_theory_schedule = [
    {
        "date": "2025-11-18",
        "title": "Financial Accounting 2",
        "type": "Lecture",
        "time": "08:15–10:00",
        "location": "Hörsal 2, Ekonomikum",
        "teacher": "",
    },
    {
        "date": "2025-11-25",
        "title": "Measurement 1",
        "type": "Lecture",
        "time": "10:15–12:00",
        "location": "Hörsal 2, Ekonomikum",
        "teacher": "",
    },
    {
        "date": "2025-11-26",
        "title": "Measurement 2",
        "type": "Lecture",
        "time": "13:15–15:00",
        "location": "Hörsal 2, Ekonomikum",
        "teacher": "",
    },
    {
        "date": "2025-11-27",
        "title": "Measurement 3",
        "type": "Lecture",
        "time": "15:15–17:00",
        "location": "Hörsal 1, Ekonomikum",
        "teacher": "",
    },
    {
        "date": "2025-12-01",
        "title": "Management Accounting 1",
        "type": "Lecture",
        "time": "15:15–17:00",
        "location": "Hörsal 1, Ekonomikum",
        "teacher": "",
    },
    {
        "date": "2025-12-03",
        "title": "Management Accounting 2",
        "type": "Lecture",
        "time": "08:15–10:00",
        "location": "Hörsal 2, Ekonomikum",
        "teacher": "",
    },
    {
        "date": "2025-12-09",
        "title": "Seminar 1 – Financial Accounting",
        "type": "Seminar",
        "time": "10:15–12:00",
        "location": "K334, Ekonomikum",
        "teacher": "",
    },
    {
        "date": "2025-12-10",
        "title": "Integration",
        "type": "Lecture",
        "time": "08:15–10:00",
        "location": "Hörsal 2, Ekonomikum",
        "teacher": "",
    },
    {
        "date": "2025-12-15",
        "title": "Seminar 2 – Management Accounting",
        "type": "Seminar",
        "time": "10:15–12:00",
        "location": "K334, Ekonomikum",
        "teacher": "",
    },
    {
        "date": "2026-01-09",
        "title": "Written Exam",
        "type": "Exam",
        "time": "08:00–12:00",
        "location": "See Ladok",
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
        .column-subtitle {
            font-size: 0.9rem;
            font-weight: 500;
            color: #556;
            margin: 4px 0 0;
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
        .secondary-row {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 20px;
        }
        .secondary-row .column {
            flex: 1 1 320px;
        }
        .upcoming-card .next-up {
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
        .upcoming-card[data-expanded="false"] .timeline-row.collapsed-row {
            display: none;
        }
        .timeline-date {
            font-weight: 600;
            color: #555;
            font-size: 0.95rem;
        }
        .timeline-date .weekday {
            display: block;
            font-size: 0.8rem;
            color: #777;
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
        .schedule-subtitle {
            margin: 0 0 12px;
            font-weight: 600;
            color: #333;
        }
        .date-group {
            margin-bottom: 18px;
        }
        .date-group:last-child {
            margin-bottom: 0;
        }
        .date-heading {
            font-weight: 600;
            color: #333;
            margin: 0 0 10px;
        }
        .schedule-event-row {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            padding: 10px 0;
            border-bottom: 1px solid #eef0f5;
        }
        .schedule-event-row:last-child {
            border-bottom: none;
        }
        .event-time {
            flex: 0 0 120px;
            font-weight: 600;
            color: #333;
        }
        .event-info {
            flex: 1 1 240px;
        }
        .event-info .task-title {
            margin-bottom: 4px;
        }
        .schedule-event-row .task-meta {
            margin: 4px 0 0;
        }
        .schedule-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            align-items: center;
        }
        .schedule-badge {
            display: inline-flex;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .schedule-badge-lecture {
            background: #e8f1ff;
            color: #1e5fad;
        }
        .schedule-badge-workshop {
            background: #dff6f5;
            color: #0c6b63;
        }
        .schedule-badge-seminar {
            background: #f4e8ff;
            color: #7b3fb9;
        }
        .schedule-badge-hand-in {
            background: #e4f7e7;
            color: #2f7a3d;
        }
        .schedule-badge-exam {
            background: #ffe2e2;
            color: #b13232;
        }
        .schedule-badge-other {
            background: #ececec;
            color: #555;
        }
        .course-chip {
            display: inline-flex;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .course-chip-scientific-methods {
            background: #f0e8ff;
            color: #6135a7;
        }
        .course-chip-accounting-theory {
            background: #e4f2ff;
            color: #1c5d99;
        }
        .calendar-modal {
            position: fixed;
            inset: 0;
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .calendar-modal.open {
            display: flex;
        }
        .calendar-backdrop {
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.3);
            opacity: 0;
            transition: opacity 0.25s ease;
        }
        .calendar-modal.open .calendar-backdrop {
            opacity: 1;
        }
        .calendar-dialog {
            position: relative;
            width: min(1000px, 90vw);
            height: 85vh;
            background: #fff;
            border-radius: 24px;
            box-shadow: 0 30px 70px rgba(0, 0, 0, 0.25);
            display: flex;
            flex-direction: column;
            padding: 24px;
            gap: 16px;
            transform: scale(0.97);
            opacity: 0;
            transition: transform 0.3s ease, opacity 0.3s ease;
        }
        .calendar-modal.open .calendar-dialog {
            transform: scale(1);
            opacity: 1;
        }
        .calendar-toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .calendar-toolbar-title {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .calendar-title {
            margin: 0;
            font-size: 1.3rem;
            font-weight: 600;
        }
        .calendar-subtitle-text {
            margin: 0;
            color: #6b7280;
            font-size: 0.9rem;
        }
        .calendar-controls {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .calendar-nav,
        .calendar-close {
            border: none;
            background: #f2f3f7;
            border-radius: 999px;
            padding: 6px 14px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s ease;
        }
        .calendar-close {
            font-size: 1.1rem;
        }
        .calendar-nav:hover,
        .calendar-close:hover {
            background: #e1e6f5;
        }
        .calendar-body {
            flex: 1;
            display: flex;
            gap: 24px;
            overflow: hidden;
        }
        .calendar-main {
            flex: 2;
            display: flex;
            flex-direction: column;
        }
        .calendar-weekdays {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            font-weight: 600;
            color: #8c94a7;
            text-align: center;
            margin-bottom: 8px;
        }
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            grid-auto-rows: minmax(90px, 1fr);
            gap: 8px;
            flex: 1;
        }
        .calendar-cell {
            background: #f7f8fb;
            border-radius: 14px;
            padding: 10px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            cursor: pointer;
            transition: background 0.2s ease, transform 0.2s ease, border 0.2s ease;
        }
        .calendar-cell:hover {
            background: #eef1ff;
            transform: translateY(-1px);
        }
        .calendar-cell.selected {
            border: 2px solid #577bff;
            background: #fff;
        }
        .calendar-cell.other-month {
            opacity: 0.5;
        }
        .calendar-date-number {
            font-weight: 600;
            color: #2d2f43;
        }
        .calendar-cell-events {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .calendar-chip {
            display: inline-flex;
            align-items: center;
            padding: 1px 6px;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        .calendar-chip-lecture {
            background: rgba(80, 123, 255, 0.15);
            color: #3b5bdb;
        }
        .calendar-chip-workshop {
            background: rgba(163, 114, 255, 0.15);
            color: #6a42c2;
        }
        .calendar-chip-seminar {
            background: rgba(255, 214, 102, 0.2);
            color: #a66a00;
        }
        .calendar-chip-hand-in {
            background: rgba(121, 208, 140, 0.2);
            color: #2f7a3d;
        }
        .calendar-chip-exam {
            background: rgba(255, 163, 163, 0.2);
            color: #b43333;
        }
        .calendar-chip-other {
            background: rgba(180, 190, 205, 0.3);
            color: #4f5b6c;
        }
        .calendar-chip-more {
            background: #e0e5f2;
            color: #5a5f73;
        }
        .calendar-detail {
            flex: 1;
            background: #f7f8fb;
            border-radius: 18px;
            padding: 16px;
            overflow-y: auto;
        }
        .detail-date {
            margin: 0 0 10px;
            font-weight: 600;
            color: #2d2f43;
        }
        .detail-events {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .detail-card {
            background: #fff;
            border-radius: 12px;
            padding: 12px;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
        }
        .detail-time {
            margin: 0;
            font-weight: 600;
            color: #384152;
        }
        .detail-title {
            margin: 4px 0;
            font-weight: 600;
        }
        .detail-meta {
            margin: 0;
            font-size: 0.85rem;
            color: #606a7c;
        }
        .detail-chip {
            display: inline-flex;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        .detail-chip-lecture {
            background: rgba(80, 123, 255, 0.15);
            color: #3b5bdb;
        }
        .detail-chip-workshop {
            background: rgba(163, 114, 255, 0.15);
            color: #6a42c2;
        }
        .detail-chip-seminar {
            background: rgba(255, 214, 102, 0.2);
            color: #a66a00;
        }
        .detail-chip-hand-in {
            background: rgba(121, 208, 140, 0.2);
            color: #2f7a3d;
        }
        .detail-chip-exam {
            background: rgba(255, 163, 163, 0.2);
            color: #b43333;
        }
        .detail-chip-other {
            background: rgba(180, 190, 205, 0.3);
            color: #4f5b6c;
        }
        .detail-location {
            margin: 4px 0 0;
            font-size: 0.85rem;
            color: #4b5563;
        }
        @media (max-width: 900px) {
            .calendar-body {
                flex-direction: column;
            }
            .calendar-dialog {
                width: 95vw;
                height: 90vh;
            }
            .calendar-detail {
                width: 100%;
                min-height: 180px;
            }
        }
    </style>
</head>
<body>
    <h1>Study Dashboard</h1>
    <div class="layout">
        <aside class="sidebar">
            <div class="column">
                <div class="column-header" style="background-color: #e3f6d0;">Current courses</div>
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
                        <p class="empty">No course data available.</p>
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
        </div>
        <div class="secondary-row">
            <div class="column">
                <div class="column-header" style="background-color: #e6f0ff;">
                    <div class="header-flex">
                        <div>
                            <span>Study Schedule – All Courses</span>
                            <p class="column-subtitle">Lectures, seminars, workshops &amp; exams</p>
                        </div>
                        {% if all_courses_schedule_sorted %}
                        <button
                            class="schedule-toggle"
                            type="button"
                            id="open-calendar-btn"
                        >
                            Full schedule ▸
                        </button>
                        {% endif %}
                    </div>
                </div>
                <div class="tasks schedule-card" id="all-courses-schedule-card">
                    <p class="schedule-subtitle">
                        This week:
                        {% if study_schedule_week_range %}
                            {{ study_schedule_week_range.start }} – {{ study_schedule_week_range.end }}
                        {% endif %}
                        {% if not all_courses_schedule_week_grouped %}
                            <span class="muted">No scheduled events.</span>
                        {% endif %}
                    </p>
                    <div class="schedule-week-view">
                        {% if all_courses_schedule_week_grouped %}
                            {% for group in all_courses_schedule_week_grouped %}
                                <div class="date-group">
                                    <p class="date-heading">{{ group.label }}</p>
                                    {% for event in group.events %}
                                        <div class="schedule-event-row">
                                            <div class="event-time">{{ event.time_display }}</div>
                                            <div class="event-info">
                                                <p class="task-title">{{ event.title }}</p>
                                                <p class="task-meta">{{ event.course_short }}{% if event.location %} · {{ event.location }}{% endif %}</p>
                                                {% if event.teacher %}
                                                <p class="muted">{{ event.teacher }}</p>
                                                {% endif %}
                                            </div>
                                            <div class="schedule-badges">
                                                <span class="schedule-badge schedule-badge-{{ event.type_badge_class }}">{{ event.type }}</span>
                                            </div>
                                        </div>
                                    {% endfor %}
                                </div>
                            {% endfor %}
                        {% elif all_courses_schedule_fallback_grouped %}
                            <p class="muted">No events this week. Showing upcoming items.</p>
                            {% for group in all_courses_schedule_fallback_grouped %}
                                <div class="date-group">
                                    <p class="date-heading">{{ group.label }}</p>
                                    {% for event in group.events %}
                                        <div class="schedule-event-row">
                                            <div class="event-time">{{ event.time_display }}</div>
                                            <div class="event-info">
                                                <p class="task-title">{{ event.title }}</p>
                                                <p class="task-meta">{{ event.course_short }}{% if event.location %} · {{ event.location }}{% endif %}</p>
                                                {% if event.teacher %}
                                                <p class="muted">{{ event.teacher }}</p>
                                                {% endif %}
                                            </div>
                                            <div class="schedule-badges">
                                                <span class="schedule-badge schedule-badge-{{ event.type_badge_class }}">{{ event.type }}</span>
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
            <div class="column">
                <div class="column-header" style="background-color: #e3ddff;">Upcoming – All Courses</div>
                <div class="tasks upcoming-card">
                    {% if upcoming_events_all_courses %}
                        {% set next_event = upcoming_events_all_courses[0] %}
                        <p class="next-up">
                            Next up: {{ next_event.date_label }} ({{ next_event.weekday }}){% if next_event.time_range %}, {{ next_event.time_range }}{% endif %} – {{ next_event.title }}
                        </p>
                        <div class="timeline">
                            {% for event in upcoming_events_all_courses %}
                                <div class="timeline-row">
                                    <div class="timeline-date">
                                        {{ event.date_label }}
                                        <span class="weekday">{{ event.weekday }}</span>
                                    </div>
                                    <div class="timeline-details">
                                        <p class="task-title">{{ event.title }}</p>
                                        <div class="badge-row">
                                            <span class="course-chip course-chip-{{ event.course_class }}">{{ event.course_short }}</span>
                                            <span class="badge schedule-badge schedule-badge-{{ event.type_badge_class }}">{{ event.type }}</span>
                                        </div>
                                        <p class="task-meta">
                                            {% if event.time_range %}{{ event.time_range }}{% endif %}
                                            {% if event.time_range and (event.location or event.details) %}
                                                ·
                                            {% endif %}
                                            {% if event.location %}
                                                {{ event.location }}
                                            {% elif event.details %}
                                                {{ event.details }}
                                            {% endif %}
                                        </p>
                                    </div>
                                </div>
                            {% endfor %}
                        </div>
                    {% else %}
                        <p class="muted">No upcoming events.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="calendar-modal" id="calendar-modal" aria-hidden="true">
        <div class="calendar-backdrop" id="calendar-backdrop"></div>
        <div class="calendar-dialog" role="dialog" aria-modal="true">
            <div class="calendar-toolbar">
                <div class="calendar-toolbar-title">
                    <p class="calendar-title">Study Schedule – Full Calendar</p>
                    <p class="calendar-subtitle-text" id="calendar-range-label"></p>
                </div>
                <div class="calendar-controls">
                    <button class="calendar-nav" id="calendar-prev" aria-label="Previous month">◀</button>
                    <button class="calendar-nav" id="calendar-next" aria-label="Next month">▶</button>
                    <button class="calendar-close" id="calendar-close" aria-label="Close calendar">×</button>
                </div>
            </div>
            <div class="calendar-body">
                <div class="calendar-main">
                    <div class="calendar-weekdays">
                        <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
                    </div>
                    <div class="calendar-grid" id="calendar-grid"></div>
                </div>
                <div class="calendar-detail" id="calendar-detail">
                    <p class="detail-date" id="calendar-day-label">Select a date</p>
                    <div id="calendar-day-details" class="detail-events"></div>
                </div>
            </div>
        </div>
    </div>
    <script>
    const studyCalendarEvents = {{ all_courses_schedule_sorted | tojson }};
    document.addEventListener("DOMContentLoaded", function () {
        var openCalendarBtn = document.getElementById("open-calendar-btn");
        var calendarModal = document.getElementById("calendar-modal");
        var calendarBackdrop = document.getElementById("calendar-backdrop");
        var calendarClose = document.getElementById("calendar-close");
        var calendarGrid = document.getElementById("calendar-grid");
        var calendarDayLabel = document.getElementById("calendar-day-label");
        var calendarDayDetails = document.getElementById("calendar-day-details");
        var calendarRangeLabel = document.getElementById("calendar-range-label");
        var prevBtn = document.getElementById("calendar-prev");
        var nextBtn = document.getElementById("calendar-next");
        var currentMonthDate = new Date();
        var selectedDate = new Date();
        var eventsByDate = {};
        studyCalendarEvents.forEach(function (event) {
            var key = event.date_iso;
            if (!eventsByDate[key]) {
                eventsByDate[key] = [];
            }
            eventsByDate[key].push(event);
        });
        var todayIso = new Date().toISOString().slice(0, 10);
        if (eventsByDate[todayIso]) {
            selectedDate = new Date(todayIso);
            currentMonthDate = new Date(todayIso);
        } else if (studyCalendarEvents.length) {
            selectedDate = new Date(studyCalendarEvents[0].date_iso);
            currentMonthDate = new Date(studyCalendarEvents[0].date_iso);
        }

        function openCalendarModal() {
            calendarModal.classList.add("open");
            calendarModal.setAttribute("aria-hidden", "false");
            document.body.style.overflow = "hidden";
            renderCalendar();
            selectDate(selectedDate.toISOString().slice(0, 10));
        }

        function closeCalendarModal() {
            calendarModal.classList.remove("open");
            calendarModal.setAttribute("aria-hidden", "true");
            document.body.style.overflow = "";
        }

        function changeMonth(offset) {
            currentMonthDate.setMonth(currentMonthDate.getMonth() + offset);
            renderCalendar();
        }

        function formatDateLabel(dateObj) {
            return dateObj.toLocaleDateString("en-US", {
                weekday: "long",
                month: "long",
                day: "numeric",
                year: "numeric",
            });
        }

        function renderCalendar() {
            var firstDay = new Date(currentMonthDate.getFullYear(), currentMonthDate.getMonth(), 1);
            var startOffset = (firstDay.getDay() + 6) % 7;
            var startDate = new Date(firstDay);
            startDate.setDate(firstDay.getDate() - startOffset);
            calendarGrid.innerHTML = "";
            for (var i = 0; i < 42; i++) {
                (function () {
                    var cellDate = new Date(startDate);
                    cellDate.setDate(startDate.getDate() + i);
                    var iso = cellDate.toISOString().slice(0, 10);
                    var cell = document.createElement("div");
                    cell.className = "calendar-cell";
                    if (cellDate.getMonth() !== currentMonthDate.getMonth()) {
                        cell.classList.add("other-month");
                    }
                    if (iso === selectedDate.toISOString().slice(0, 10)) {
                        cell.classList.add("selected");
                    }
                    var number = document.createElement("div");
                    number.className = "calendar-date-number";
                    number.textContent = cellDate.getDate();
                    cell.appendChild(number);
                    var events = eventsByDate[iso] || [];
                    if (events.length) {
                        var chips = document.createElement("div");
                        chips.className = "calendar-cell-events";
                        events.slice(0, 3).forEach(function (item) {
                            var chip = document.createElement("span");
                            chip.className = "calendar-chip calendar-chip-" + item.type_badge_class;
                            chip.textContent = (item.start_time || item.time_display) + " · " + item.type;
                            chips.appendChild(chip);
                        });
                        if (events.length > 3) {
                            var more = document.createElement("span");
                            more.className = "calendar-chip calendar-chip-more";
                            more.textContent = "+" + (events.length - 3) + " more";
                            chips.appendChild(more);
                        }
                        cell.appendChild(chips);
                    }
                    cell.addEventListener("click", function () {
                        selectedDate = cellDate;
                        selectDate(iso);
                        renderCalendar();
                    });
                    calendarGrid.appendChild(cell);
                })();
            }
            var monthLabel = currentMonthDate.toLocaleDateString("en-US", {
                month: "long",
                year: "numeric",
            });
            calendarRangeLabel.textContent = monthLabel;
        }

        function selectDate(iso) {
            var dateObj = new Date(iso);
            calendarDayLabel.textContent = formatDateLabel(dateObj);
            calendarDayDetails.innerHTML = "";
            var events = eventsByDate[iso] || [];
            if (!events.length) {
                var empty = document.createElement("p");
                empty.className = "muted";
                empty.textContent = "No events for this date.";
                calendarDayDetails.appendChild(empty);
                return;
            }
            events
                .sort(function (a, b) {
                    var aKey = (a.start_time || "") + a.title;
                    var bKey = (b.start_time || "") + b.title;
                    return aKey.localeCompare(bKey);
                })
                .forEach(function (event) {
                    var card = document.createElement("div");
                    card.className = "detail-card";
                    card.innerHTML =
                        "<p class='detail-time'>" +
                        (event.start_time ? event.start_time : event.time_display) +
                        "</p>" +
                        "<p class='detail-title'>" +
                        event.title +
                        "</p>" +
                        "<p class='detail-meta'>" +
                        event.course_short +
                        " · <span class='detail-chip detail-chip-" +
                        event.type_badge_class +
                        "'>" +
                        event.type +
                        "</span></p>" +
                        "<p class='detail-location'>" +
                        (event.location || event.details || "Details TBA") +
                        "</p>";
                    calendarDayDetails.appendChild(card);
                });
        }

        if (openCalendarBtn) {
            openCalendarBtn.addEventListener("click", openCalendarModal);
        }
        if (calendarBackdrop) {
            calendarBackdrop.addEventListener("click", closeCalendarModal);
        }
        if (calendarClose) {
            calendarClose.addEventListener("click", closeCalendarModal);
        }
        if (prevBtn) {
            prevBtn.addEventListener("click", function () {
                changeMonth(-1);
            });
        }
        if (nextBtn) {
            nextBtn.addEventListener("click", function () {
                changeMonth(1);
            });
        }
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && calendarModal.classList.contains("open")) {
                closeCalendarModal();
            }
        });
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
    if "seminar" in lowered:
        return "seminar"
    if "quantitative" in lowered:
        return "workshop-quant"
    if "qualitative" in lowered:
        return "workshop-qual"
    if "workshop" in lowered:
        return "workshop"
    return "other"


def _slugify_label(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def _normalize_event_type(type_value: str) -> Tuple[str, str | None, str]:
    lowered = type_value.lower()
    track: str | None = None
    if "workshop" in lowered:
        if "qualitative" in lowered:
            track = "Qualitative"
        elif "quantitative" in lowered:
            track = "Quantitative"
        return "Workshop", track, "workshop"
    if "hand-in" in lowered or "handin" in lowered:
        return "Hand-in", None, "hand-in"
    if "seminar" in lowered:
        return "Seminar", None, "seminar"
    if "exam" in lowered:
        return "Exam", None, "exam"
    if "lecture" in lowered:
        return "Lecture", None, "lecture"
    return type_value or "Event", track, "other"


def _normalize_course_schedule(
    entries: List[Dict[str, str]],
    *,
    course_name: str,
    course_short: str,
    course_slug: str,
) -> List[Dict[str, object]]:
    normalized: List[Dict[str, object]] = []
    for index, entry in enumerate(entries):
        date_value = _parse_date_string(entry.get("date"))
        if not date_value:
            continue
        start_time, end_time = _split_time_range(entry.get("time"))
        if start_time and end_time:
            time_display = f"{start_time}\u2013{end_time}"
        elif start_time:
            time_display = start_time
        else:
            time_display = entry.get("time", "") or ""
        type_label, track, type_class = _normalize_event_type(entry.get("type", ""))
        title_value = entry.get("title", "").strip()
        slug = _slugify_label(title_value) or f"item-{index}"
        event_id = f"{course_slug}_{date_value.strftime('%Y%m%d')}_{slug}"
        normalized.append(
            {
                "id": event_id,
                "course": course_name,
                "course_short": course_short,
                "course_slug": course_slug,
                "title": title_value,
                "type": type_label,
                "type_badge_class": type_class,
                "track": track,
                "time_display": time_display or "Time TBA",
                "start_time": start_time or "",
                "end_time": end_time or "",
                "raw_time": entry.get("time", "") or "",
                "location": entry.get("location", ""),
                "details": entry.get("details", ""),
                "teacher": entry.get("teacher", ""),
                "date": date_value,
                "date_iso": date_value.isoformat(),
                "day": date_value.strftime("%d"),
                "weekday": date_value.strftime("%a"),
                "date_heading": f"{date_value.strftime('%d %b')} – {date_value.strftime('%a')}",
                "time_sort": start_time or "",
            }
        )
    return normalized


def _build_all_courses_schedule() -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []
    events.extend(
        _normalize_course_schedule(
            scientific_methods_schedule,
            course_name="Scientific Methods in Business Research",
            course_short="Scientific Methods",
            course_slug="scientific-methods",
        )
    )
    events.extend(
        _normalize_course_schedule(
            accounting_theory_schedule,
            course_name="Accounting Theory – Group B",
            course_short="Accounting Theory",
            course_slug="accounting-theory",
        )
    )
    return events


def get_sorted_schedule(events: List[Dict[str, object]]) -> List[Dict[str, object]]:
    return sorted(events, key=lambda item: (item["date"], item["time_sort"]))


def get_schedule_this_week(
    events: List[Dict[str, object]], today: date
) -> List[Dict[str, object]]:
    end_date = today + timedelta(days=7)
    return [
        item for item in events if isinstance(item["date"], date) and today <= item["date"] <= end_date
    ]


def get_upcoming_schedule(events: List[Dict[str, object]], today: date) -> List[Dict[str, object]]:
    return [item for item in events if isinstance(item["date"], date) and item["date"] >= today]


def group_schedule_by_date(events: List[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: List[Dict[str, object]] = []
    for label, items in groupby(events, key=lambda event: event["date_heading"]):
        grouped.append({"label": label, "events": list(items)})
    return grouped


def get_upcoming_events_all_courses(
    events: List[Dict[str, object]], today: date, limit: int = 8
) -> List[Dict[str, object]]:
    future_events = [
        event for event in events if isinstance(event["date"], date) and event["date"] >= today
    ]
    future_events.sort(key=lambda item: (item["date"], item["time_sort"]))
    upcoming: List[Dict[str, object]] = []
    for event in future_events[:limit]:
        if event["start_time"] and event["end_time"]:
            time_range = f"{event['start_time']}\u2013{event['end_time']}"
        elif event["start_time"]:
            time_range = event["start_time"]
        else:
            time_range = event["time_display"]
        upcoming.append(
            {
                "id": event["id"],
                "title": event["title"],
                "course": event["course"],
                "course_short": event["course_short"],
                "course_class": event["course_slug"],
                "type": event["type"],
                "type_badge_class": event["type_badge_class"],
                "date_label": event["date"].strftime("%d %b"),
                "weekday": event["date"].strftime("%a"),
                "time_range": time_range,
                "location": event["location"],
                "details": event["details"],
            }
        )
    return upcoming


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
    all_courses_schedule = _build_all_courses_schedule()
    all_courses_schedule_sorted = get_sorted_schedule(all_courses_schedule)
    study_schedule_this_week = get_schedule_this_week(
        all_courses_schedule_sorted, today
    )
    study_schedule_upcoming = get_upcoming_schedule(
        all_courses_schedule_sorted, today
    )
    upcoming_events_all_courses = get_upcoming_events_all_courses(
        all_courses_schedule_sorted, today, limit=6
    )
    week_grouped = group_schedule_by_date(study_schedule_this_week)
    fallback_events = study_schedule_upcoming[:5]
    fallback_grouped = group_schedule_by_date(fallback_events)
    full_grouped = group_schedule_by_date(all_courses_schedule_sorted)
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
        all_courses_schedule_sorted=all_courses_schedule_sorted,
        all_courses_schedule_this_week=study_schedule_this_week,
        all_courses_schedule_upcoming=study_schedule_upcoming,
        study_schedule_week_range=week_range,
        all_courses_schedule_week_grouped=week_grouped,
        all_courses_schedule_fallback_grouped=fallback_grouped,
        all_courses_schedule_full_grouped=full_grouped,
        upcoming_events_all_courses=upcoming_events_all_courses,
    )


if __name__ == "__main__":
    print("Open http://127.0.0.1:5000 in your browser to see your study dashboard.")
    app.run(host="127.0.0.1", port=5000, debug=False)
