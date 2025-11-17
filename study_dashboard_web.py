#!/usr/bin/env python3
"""Simple Flask web dashboard for study tasks."""

from __future__ import annotations

import json
import os
import re
import calendar
from datetime import date, datetime, time, timedelta
from itertools import groupby
from pathlib import Path
from typing import Dict, List, Tuple

from flask import Flask, jsonify, render_template_string, request
from openai import OpenAI

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
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
        :root {
            --bg: #f5f5f7;
            --text-strong: #111111;
            --text-body: #333333;
            --text-muted: #777777;
            --card-radius: 18px;
        }
        * {
            box-sizing: border-box;
        }
        body {
            font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: var(--bg);
            margin: 0;
            color: var(--text-body);
            line-height: 1.6;
        }
        .dashboard-shell {
            max-width: 1280px;
            margin: 40px auto 80px auto;
            padding: 0 24px;
        }
        .page-header {
            text-align: center;
            margin-bottom: 32px;
        }
        .page-title {
            font-size: clamp(32px, 3vw, 36px);
            font-weight: 700;
            color: var(--text-strong);
            margin: 0;
        }
        .page-subtitle {
            margin: 10px 0 0;
            font-size: 15px;
            color: #555;
            font-weight: 500;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1.05fr 1.2fr 1.2fr minmax(220px, 260px);
            gap: 24px;
            align-items: start;
        }
        @media (max-width: 1100px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            .mini-calendar-wrapper {
                justify-self: stretch;
                width: 100%;
            }
        }
        .card {
            background: #ffffff;
            border-radius: var(--card-radius);
            box-shadow: 0 18px 40px rgba(0, 0, 0, 0.06);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .card + .card {
            margin-top: 24px;
        }
        .card-header {
            padding: 20px 24px;
            background: #f3f4f6;
        }
        .card-header.header-soft-sage { background: linear-gradient(135deg, #edf5e2, #e3f0d6); }
        .card-header.header-soft-sky { background: linear-gradient(135deg, #ebf2ff, #dfe9ff); }
        .card-header.header-soft-peach { background: linear-gradient(135deg, #ffe9e1, #ffd9d0); }
        .card-header.header-soft-sun { background: linear-gradient(135deg, #fff1d7, #ffe6bf); }
        .card-header.header-soft-lilac { background: linear-gradient(135deg, #f4eeff, #e8e0fb); }
        .card-header.header-soft-slate { background: linear-gradient(135deg, #eceff5, #e2e6ef); }
        .card-title {
            margin: 0;
            font-size: 19px;
            font-weight: 600;
            color: var(--text-strong);
        }
        .card-subtitle {
            margin: 8px 0 0;
            font-size: 14px;
            font-weight: 500;
            color: #555;
        }
        .card-body {
            padding: 24px;
        }
        .course-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .course-row {
            padding-bottom: 12px;
            border-bottom: 1px solid #f0f0f2;
        }
        .course-row:last-child {
            border-bottom: none;
            padding-bottom: 0;
        }
        .course-name {
            margin: 0;
            font-weight: 600;
            font-size: 15px;
            color: var(--text-strong);
        }
        .course-code {
            margin: 4px 0 0;
            font-size: 13px;
            color: var(--text-muted);
        }
        .mini-calendar-wrapper {
            align-self: start;
            justify-self: end;
            grid-column: 4;
        }
        .mini-calendar-card {
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 18px 40px rgba(0, 0, 0, 0.07);
            padding: 18px;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            user-select: none;
            min-width: 220px;
            overflow: visible;
        }
        .mini-calendar-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 24px 45px rgba(0, 0, 0, 0.08);
        }
        .mini-calendar-card:focus {
            outline: none;
        }
        .mini-calendar-card:focus-visible {
            box-shadow: 0 0 0 3px rgba(87, 123, 255, 0.4);
        }
        .mini-calendar-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        .mini-calendar-title {
            margin: 0;
            font-size: 15px;
            font-weight: 600;
            color: var(--text-strong);
        }
        .mini-calendar-subtitle {
            margin: 4px 0 0;
            font-size: 12px;
            color: #6b7280;
        }
        .mini-calendar-icon {
            font-size: 18px;
            color: #6b7086;
        }
        .mini-calendar-controls {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .mini-calendar-nav {
            width: 28px;
            height: 28px;
            border-radius: 999px;
            background: #eef0f7;
            border: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #4d5670;
            font-weight: 600;
            text-decoration: none;
            transition: background 0.2s ease;
        }
        .mini-calendar-nav:hover {
            background: #e1e8ff;
        }
        .mini-calendar-weekdays {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            text-align: center;
            font-size: 10px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #9aa0b3;
            gap: 4px;
            margin-bottom: 8px;
        }
        .mini-calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
        }
        .mini-day {
            border-radius: 12px;
            padding: 6px 0;
            text-align: center;
            min-height: 36px;
            position: relative;
            background: rgba(244, 245, 248, 0.9);
            font-size: 13px;
            color: #2b2f40;
            border: none;
            cursor: pointer;
            transition: background 0.2s ease, box-shadow 0.2s ease;
            width: 100%;
        }
        .mini-day:focus-visible {
            outline: 2px solid rgba(87, 123, 255, 0.5);
            outline-offset: 2px;
        }
        .mini-day.has-events {
            background: #ffffff;
            box-shadow: inset 0 0 0 1px rgba(86, 108, 154, 0.12);
        }
        .mini-day.is-today {
            box-shadow: inset 0 0 0 2px rgba(87, 123, 255, 0.4);
            background: #f0f4ff;
        }
        .mini-day.is-selected {
            box-shadow: inset 0 0 0 2px rgba(59, 130, 246, 0.5);
            background: #e9efff;
        }
        .mini-day.is-placeholder {
            background: transparent;
            pointer-events: none;
        }
        .mini-day-number {
            display: block;
            font-weight: 600;
        }
        .mini-day-dots {
            display: flex;
            justify-content: center;
            gap: 4px;
            margin-top: 4px;
        }
        .event-dot {
            width: 6px;
            height: 6px;
            border-radius: 999px;
        }
        .event-lecture {
            background: #8bb4ff;
        }
        .event-seminar {
            background: #c5a6f6;
        }
        .event-workshop {
            background: #7fd5c5;
        }
        .event-deadline {
            background: #f9a8a8;
        }
        .event-other {
            background: #cfd5e4;
        }
        .mini-day-tooltip {
            position: absolute;
            bottom: 115%;
            left: 50%;
            transform: translate(-50%, 8px);
            background: rgba(255, 255, 255, 0.98);
            color: #1f2937;
            border-radius: 16px;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.18);
            padding: 12px 14px;
            width: 200px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.15s ease, transform 0.15s ease;
            z-index: 10;
        }
        .mini-day-tooltip::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border-width: 6px;
            border-style: solid;
            border-color: #ffffff transparent transparent transparent;
        }
        .mini-day:hover .mini-day-tooltip,
        .mini-day:focus-within .mini-day-tooltip {
            opacity: 1;
            transform: translate(-50%, 0);
        }
        .mini-tooltip-date {
            margin: 0 0 6px;
            font-size: 12px;
            font-weight: 600;
            color: #111827;
        }
        .mini-tooltip-list {
            margin: 0;
            padding: 0;
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .mini-tooltip-item {
            font-size: 12px;
            color: #374151;
        }
        .mini-tooltip-meta {
            display: block;
            font-size: 11px;
            color: #6b7280;
            margin-top: 2px;
        }
        .focus-stack {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }
        .section-subtitle {
            font-size: 14px;
            color: #555;
            font-weight: 500;
            margin: 6px 0 0;
        }
        .task-list {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .task-item {
            border: 1px solid #ececf5;
            border-radius: 14px;
            padding: 16px;
            background: #fafbfe;
        }
        .task-title {
            margin: 0;
            font-size: 15px;
            font-weight: 600;
            color: var(--text-strong);
        }
        .task-meta {
            margin: 6px 0 0;
            font-size: 13px;
            color: var(--text-muted);
        }
        .task-details {
            margin: 4px 0 0;
            font-size: 14px;
            color: var(--text-body);
        }
        .task-empty {
            margin: 0;
            color: var(--text-muted);
            font-size: 14px;
        }
        .highlight-task {
            background: linear-gradient(135deg, #fff5e8, #ffe8d7);
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 170, 125, 0.4);
        }
        .highlight-title {
            margin: 6px 0;
            font-size: 16px;
            font-weight: 600;
            color: var(--text-strong);
        }
        .highlight-due {
            margin: 0;
            font-size: 13px;
            color: var(--text-muted);
        }
        .highlight-note {
            margin: 8px 0 0;
            font-size: 13px;
            color: var(--text-muted);
        }
        .pill {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.01em;
        }
        .course-pill {
            background: #eef1f6;
            color: #3a4a6b;
        }
        .course-pill[data-course*="Accounting"] {
            background: #e0edff;
            color: #2250c4;
        }
        .course-pill[data-course*="Scientific"] {
            background: #f2e7ff;
            color: #6b32c4;
        }
        .course-pill[data-course*="Research"] {
            background: #f2e7ff;
            color: #6b32c4;
        }
        .schedule-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
        }
        .schedule-card-body {
            padding-top: 16px;
        }
        .card-upcoming-all {
            display: flex;
            flex-direction: column;
        }
        .card-upcoming-all .card-header {
            margin-bottom: 0.5rem;
        }
        .card-upcoming-all .card-subtitle {
            font-size: 0.85rem;
            color: rgba(0, 0, 0, 0.55);
            margin-top: 0.15rem;
        }
        .upcoming-preview-body {
            max-height: 260px;
            overflow: hidden;
        }
        .upcoming-list {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        .preview-row {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 0.6rem;
            padding: 0.4rem 0.2rem;
            border-bottom: 1px solid rgba(15, 23, 42, 0.08);
        }
        .preview-row:last-child {
            border-bottom: none;
        }
        .preview-date {
            min-width: 2.6rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 0.35rem 0.3rem;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.7);
        }
        .preview-date .date-number {
            font-weight: 600;
            font-size: 1rem;
            color: var(--text-strong);
            line-height: 1;
        }
        .preview-date .date-weekday {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: rgba(0, 0, 0, 0.45);
        }
        .preview-main {
            display: flex;
            flex-direction: column;
            gap: 0.12rem;
        }
        .preview-title {
            margin: 0;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-strong);
        }
        .preview-meta {
            margin: 0;
            font-size: 0.78rem;
            color: rgba(0, 0, 0, 0.6);
        }
        .preview-location {
            color: rgba(0, 0, 0, 0.55);
        }
        .upcoming-modal-events {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }
        .event-row {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 0.35rem 1rem;
            padding: 0.35rem 0.4rem;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.75);
        }
        .event-row.event-row-modal {
            border: 1px solid rgba(15, 23, 42, 0.08);
            padding: 0.45rem 0.55rem;
        }
        .event-row-title {
            font-size: 0.9rem;
            font-weight: 600;
            margin: 0;
            color: var(--text-strong);
        }
        .event-row-meta {
            font-size: 0.78rem;
            color: rgba(0, 0, 0, 0.6);
        }
        .event-row-badges {
            display: flex;
            gap: 0.25rem;
            align-items: center;
            justify-content: flex-end;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 500;
        }
        .badge-xs {
            font-size: 0.65rem;
            padding: 0.15rem 0.5rem;
        }
        .badge-course {
            background: rgba(99, 102, 241, 0.1);
            color: #4f46e5;
        }
        .badge-kind {
            background: rgba(139, 92, 246, 0.1);
            color: #7c3aed;
        }
        .upcoming-location {
            font-size: 0.75rem;
            color: rgba(0, 0, 0, 0.55);
        }
        .upcoming-time {
            font-size: 0.78rem;
            color: rgba(0, 0, 0, 0.65);
        }
        .upcoming-footer {
            margin-top: 0.75rem;
            display: flex;
            justify-content: flex-end;
        }
        .link-button.upcoming-show-all {
            background: none;
            border: none;
            color: #2563eb;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            padding: 0;
        }
        .link-button.upcoming-show-all:hover {
            text-decoration: underline;
        }
        .upcoming-empty {
            margin: 0;
            color: rgba(0, 0, 0, 0.55);
            font-size: 0.85rem;
        }
        .type-pill {
            background: #f1f2f4;
            color: #4b5563;
            margin-left: 8px;
        }
        .type-pill.type-lecture { background: #e5edff; color: #2d4ab8; }
        .type-pill.type-workshop { background: #f4e9ff; color: #6b32c4; }
        .type-pill.type-seminar { background: #fff1d6; color: #9a6400; }
        .type-pill.type-exam { background: #ffe1e1; color: #b42318; }
        .type-pill.type-hand-in { background: #e7f6ec; color: #1e7a46; }
        .type-pill.type-workshop-qual { background: #f4e9ff; color: #6b32c4; }
        .type-pill.type-workshop-quant { background: #e6f5ff; color: #0369a1; }
        .type-pill.type-other { background: #f1f2f4; color: #4b5563; }
        .task-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }
        .assistant-chat {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .chat-bubble {
            padding: 12px 16px;
            border-radius: 16px;
            font-size: 13px;
            line-height: 1.5;
        }
        .bubble-user {
            align-self: flex-end;
            background: #e9efff;
            color: #1e3a8a;
        }
        .bubble-ai {
            align-self: flex-start;
            background: #f3f4f6;
            color: var(--text-body);
        }
        .assistant-input {
            border: 1px solid #e1e4ec;
            border-radius: 14px;
            padding: 12px 16px;
            font-size: 13px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .placeholder {
            color: var(--text-muted);
            font-size: 14px;
        }
        .calendar-overlay {
            position: fixed;
            inset: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px 20px;
            z-index: 1000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.25s ease;
        }
        .calendar-overlay.open {
            opacity: 1;
            pointer-events: auto;
        }
        .calendar-backdrop {
            position: absolute;
            inset: 0;
            background: rgba(17, 18, 23, 0.55);
            backdrop-filter: blur(6px);
        }
        .calendar-dialog {
            position: relative;
            z-index: 1;
            background: #ffffff;
            border-radius: 24px;
            box-shadow: 0 40px 90px rgba(15, 23, 42, 0.2);
            width: 100%;
            max-width: 1100px;
            max-height: 90vh;
            padding: 32px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .upcoming-modal-overlay {
            position: fixed;
            inset: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px 20px;
            z-index: 900;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.25s ease;
        }
        .upcoming-modal-overlay.open {
            opacity: 1;
            pointer-events: auto;
        }
        .upcoming-modal-backdrop {
            position: absolute;
            inset: 0;
            background: rgba(15, 23, 42, 0.55);
            backdrop-filter: blur(6px);
        }
        .upcoming-modal-dialog {
            position: relative;
            z-index: 1;
            background: #ffffff;
            border-radius: 22px;
            box-shadow: 0 40px 90px rgba(15, 23, 42, 0.25);
            width: 100%;
            max-width: 960px;
            max-height: 80vh;
            display: flex;
            flex-direction: column;
        }
        .upcoming-modal-head {
            padding: 24px 32px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
            border-bottom: 1px solid rgba(15, 23, 42, 0.08);
        }
        .upcoming-modal-title {
            margin: 0;
            font-size: 1.35rem;
            font-weight: 600;
            color: var(--text-strong);
        }
        .upcoming-modal-subtitle {
            margin: 6px 0 0;
            font-size: 0.9rem;
            color: rgba(17, 24, 39, 0.65);
        }
        .upcoming-modal-close {
            border: none;
            background: #eef0f7;
            width: 34px;
            height: 34px;
            border-radius: 50%;
            font-size: 1.2rem;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .upcoming-modal-close:hover {
            background: #e1e5ef;
        }
        .upcoming-modal-body {
            padding: 22px 32px 28px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        .upcoming-modal-day {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            padding-bottom: 0.6rem;
            border-bottom: 1px solid rgba(15, 23, 42, 0.08);
        }
        .upcoming-modal-day:last-child {
            border-bottom: none;
        }
        @media (max-width: 900px) {
            .calendar-dialog {
                padding: 24px;
                border-radius: 20px;
            }
        }
        .calendar-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
        }
        .calendar-title {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
            color: var(--text-strong);
        }
        .calendar-month {
            margin: 6px 0 0;
            color: #555;
            font-size: 16px;
        }
        .calendar-controls {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .calendar-nav-btn,
        .calendar-close-btn {
            border: none;
            background: #eef1f7;
            border-radius: 999px;
            width: 38px;
            height: 38px;
            font-size: 18px;
            font-weight: 600;
            color: #111;
            cursor: pointer;
            transition: background 0.2s ease;
        }
        .calendar-nav-btn:hover,
        .calendar-close-btn:hover {
            background: #e1e5ef;
        }
        .calendar-weekdays {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #8d94a3;
            text-align: center;
        }
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            grid-auto-rows: minmax(110px, 1fr);
            gap: 10px;
            overflow-y: auto;
        }
        .calendar-cell {
            border: none;
            background: #f6f7fb;
            border-radius: 18px;
            padding: 12px;
            text-align: left;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 8px;
            transition: background 0.2s ease, transform 0.2s ease;
        }
        .calendar-cell:focus {
            outline: 2px solid #6d7cff;
            outline-offset: 2px;
        }
        .calendar-cell.other-month {
            opacity: 0.4;
        }
        .calendar-cell.has-events {
            background: #ffffff;
        }
        .calendar-cell.selected {
            box-shadow: 0 0 0 2px #7a89ff;
            background: #ffffff;
        }
        .calendar-cell.is-today {
            box-shadow: 0 0 0 2px rgba(87, 123, 255, 0.5);
            background: #eef2ff;
        }
        .calendar-cell.is-past {
            opacity: 0.55;
        }
        .calendar-date {
            font-weight: 600;
            color: var(--text-strong);
            font-size: 14px;
        }
        .calendar-events {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .calendar-chip {
            display: inline-flex;
            align-items: center;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 600;
        }
        .calendar-chip.more-chip {
            background: transparent;
            color: #6b7280;
        }
        .calendar-chip.chip-lecture { background: #e0e9ff; color: #1e3a8a; }
        .calendar-chip.chip-workshop { background: #f0e7ff; color: #6b32c4; }
        .calendar-chip.chip-workshop-qual { background: #f0e7ff; color: #6b32c4; }
        .calendar-chip.chip-workshop-quant { background: #e2f2ff; color: #0f4f71; }
        .calendar-chip.chip-hand-in { background: #e7f6ec; color: #1e7a46; }
        .calendar-chip.chip-seminar { background: #fff2d9; color: #935c00; }
        .calendar-chip.chip-exam { background: #ffe1e1; color: #b42318; }
        .calendar-chip.chip-other { background: #eef1f7; color: #4b5563; }
        .calendar-detail {
            background: #f7f8fb;
            border-radius: 20px;
            padding: 20px;
            max-height: 220px;
            overflow-y: auto;
        }
        .calendar-detail-heading {
            margin: 0 0 6px;
            font-size: 16px;
            font-weight: 600;
            color: var(--text-strong);
        }
        .calendar-detail-empty {
            margin: 0;
            font-size: 13px;
            color: #7b8194;
        }
        .calendar-detail-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .calendar-detail-item {
            background: #ffffff;
            border-radius: 16px;
            padding: 12px 14px;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.08);
        }
        .calendar-detail-time {
            margin: 0;
            font-weight: 600;
            font-size: 14px;
            color: #374151;
        }
        .calendar-detail-title {
            margin: 6px 0 0;
            font-weight: 600;
            color: var(--text-strong);
        }
        .calendar-detail-meta {
            margin: 4px 0 0;
            font-size: 13px;
            color: #6b7280;
        }
        @media (max-width: 600px) {
            .card-body {
                padding: 20px;
            }
            .event-row {
                grid-template-columns: 1fr;
            }
            .event-row-badges {
                justify-content: flex-start;
            }
        }
    </style>
</head>
<body>
    <main class="dashboard-shell">
        <header class="page-header">
            <h1 class="page-title">Study Dashboard</h1>
            <p class="page-subtitle">A calm overview of your courses and schedule</p>
        </header>
        <div class="dashboard-grid">
            <div>
                <section class="card">
                    <div class="card-header header-soft-sage">
                        <p class="card-title">Current courses</p>
                        <p class="card-subtitle">Active modules this term</p>
                    </div>
                    <div class="card-body">
                        {% if courses %}
                        <div class="course-list">
                            {% for course in courses %}
                            <div class="course-row">
                                <p class="course-name">{{ course.name }}</p>
                                {% if course.code %}
                                <p class="course-code">{{ course.code }}</p>
                                {% endif %}
                            </div>
                            {% endfor %}
                        </div>
                        {% else %}
                        <p class="placeholder">No courses linked yet.</p>
                        {% endif %}
                    </div>
                </section>
            </div>
            <div>
                <div class="focus-stack">
                    {% for key, label, _ in sections %}
                    <section class="card focus-card">
                        <div class="card-header {% if label == 'Today' %}header-soft-peach{% elif label == 'This Week' %}header-soft-sun{% else %}header-soft-lilac{% endif %}">
                            <p class="card-title">{{ label }}</p>
                            {% if label == 'This Week' and study_schedule_week_range %}
                            <p class="card-subtitle">This week: {{ study_schedule_week_range.start }} – {{ study_schedule_week_range.end }}</p>
                            {% endif %}
                        </div>
                        <div class="card-body">
                            {% set tasks = grouped[key] %}
                            {% if label == 'Today' and not tasks %}
                                <p class="placeholder">No tasks today yet.</p>
                            {% elif label == 'Later' and not tasks %}
                                <p class="placeholder">No later tasks scheduled.</p>
                            {% elif not tasks %}
                                <p class="placeholder">No items here.</p>
                            {% else %}
                                {% if label == 'This Week' %}
                                    {% set primary = tasks[0] %}
                                    <div class="highlight-task">
                                        <div class="task-badges">
                                            <span class="pill course-pill" data-course="{{ primary.course }}">{{ primary.course }}</span>
                                            <span class="pill type-pill type-{{ (primary.type or 'other')|lower|replace(' ', '-') }}">{{ (primary.type or 'Task')|title }}</span>
                                        </div>
                                        <p class="highlight-title">{{ primary.title }}</p>
                                        <p class="highlight-due">Due {{ primary.due_nice }}</p>
                                        {% if primary.location %}
                                        <p class="highlight-note">{{ primary.location }}</p>
                                        {% elif primary.submission %}
                                        <p class="highlight-note">{{ primary.submission }}</p>
                                        {% elif primary.description %}
                                        <p class="highlight-note">{{ primary.description }}</p>
                                        {% endif %}
                                    </div>
                                    {% if tasks|length > 1 %}
                                    <div class="task-list">
                                        {% for task in tasks[1:] %}
                                        <div class="task-item">
                                            <p class="task-title">{{ task.title }}</p>
                                            <div class="task-badges">
                                                <span class="pill course-pill" data-course="{{ task.course }}">{{ task.course }}</span>
                                                <span class="pill type-pill type-{{ (task.type or 'other')|lower|replace(' ', '-') }}">{{ (task.type or 'Task')|title }}</span>
                                            </div>
                                            <p class="task-meta">Due {{ task.due_nice }}</p>
                                        </div>
                                        {% endfor %}
                                    </div>
                                    {% endif %}
                                {% else %}
                                    <div class="task-list">
                                        {% for task in tasks %}
                                        <div class="task-item">
                                            <p class="task-title">{{ task.title }}</p>
                                            <div class="task-badges">
                                                <span class="pill course-pill" data-course="{{ task.course }}">{{ task.course }}</span>
                                                <span class="pill type-pill type-{{ (task.type or 'other')|lower|replace(' ', '-') }}">{{ (task.type or 'Task')|title }}</span>
                                            </div>
                                            <p class="task-meta">Due {{ task.due_nice }}</p>
                                        </div>
                                        {% endfor %}
                                    </div>
                                {% endif %}
                            {% endif %}
                        </div>
                    </section>
                    {% endfor %}
                </div>
            </div>
            <div>
                <section class="card card-upcoming-all">
                    <div class="card-header header-soft-sky">
                        <p class="card-title">Upcoming – All Courses</p>
                        <p class="card-subtitle">Next few focus events across your courses</p>
                    </div>
                    <div class="card-body upcoming-preview-body">
                        <div class="upcoming-list">
                            {% if upcoming_preview_events and upcoming_preview_events|length > 0 %}
                                {% for event in upcoming_preview_events %}
                                <div class="preview-row">
                                    <div class="preview-date">
                                        <span class="date-number">{{ event.day_label }}</span>
                                        <span class="date-weekday">{{ event.weekday }}</span>
                                    </div>
                                    <div class="preview-main">
                                        <p class="preview-title">{{ event.title }}</p>
                                        <p class="preview-meta">{{ event.course_short }} · {{ event.kind }}</p>
                                        <p class="preview-meta">
                                            {{ event.time_label }}
                                            {% if event.location %}
                                                · <span class="preview-location">{{ event.location }}</span>
                                            {% endif %}
                                        </p>
                                    </div>
                                </div>
                                {% endfor %}
                            {% else %}
                                <p class="upcoming-empty">No upcoming events found.</p>
                            {% endif %}
                        </div>
                        {% if upcoming_total_events > 0 %}
                        <div class="upcoming-footer">
                            <button
                                type="button"
                                class="link-button upcoming-show-all"
                                data-open-upcoming-schedule="true"
                            >
                                Show full upcoming schedule ({{ upcoming_total_events }} events)
                            </button>
                        </div>
                        {% endif %}
                    </div>
                </section>
                <section class="card assistant-card">
                    <div class="card-header header-soft-slate">
                        <p class="card-title">Study Assistant</p>
                        <p class="card-subtitle">Quick questions for ChatGPT</p>
                    </div>
                    <div class="card-body">
                        <div class="assistant-chat">
                            <div class="chat-bubble bubble-user">Need a quick way to recap the WS2 workshop readings?</div>
                            <div class="chat-bubble bubble-ai">Start by outlining the key research questions, then map each reading to the question it helps answer. Want a short bullet list?</div>
                        </div>
                        <div class="assistant-input">
                            <span>Ask a quick question about your courses…</span>
                        </div>
                    </div>
                </section>
            </div>
            <div class="mini-calendar-wrapper">
                <section
                    class="card mini-calendar-card"
                    id="mini-calendar-card"
                    role="button"
                    tabindex="0"
                    aria-label="Open full schedule calendar"
                >
                    <div class="mini-calendar-header">
                        <div>
                            <p class="mini-calendar-title" id="mini-calendar-title">{{ mini_calendar.month_label }}</p>
                            <p class="mini-calendar-subtitle">Tap to view the full calendar</p>
                        </div>
                        <div class="mini-calendar-controls">
                            <button
                                type="button"
                                class="mini-calendar-nav"
                                data-mini-nav="prev"
                                aria-label="Previous month"
                            >‹</button>
                            <button
                                type="button"
                                class="mini-calendar-nav"
                                data-mini-nav="next"
                                aria-label="Next month"
                            >›</button>
                        </div>
                    </div>
                    <div class="mini-calendar-weekdays">
                        {% for label in mini_calendar.weekday_labels %}
                        <span>{{ label }}</span>
                        {% endfor %}
                    </div>
                    <div class="mini-calendar-grid" id="mini-calendar-grid"></div>
                </section>
            </div>
        </div>
    </main>
    <div class="calendar-overlay" id="calendar-overlay" aria-hidden="true">
        <div class="calendar-backdrop" id="calendar-backdrop"></div>
        <div class="calendar-dialog" role="dialog" aria-modal="true" aria-labelledby="calendar-month-label">
            <div class="calendar-head">
                <div>
                    <p class="calendar-title">Full schedule</p>
                    <p class="calendar-month" id="calendar-month-label"></p>
                </div>
                <div class="calendar-controls">
                    <button class="calendar-nav-btn" type="button" data-calendar-nav="prev" aria-label="Previous month">‹</button>
                    <button class="calendar-nav-btn" type="button" data-calendar-nav="next" aria-label="Next month">›</button>
                    <button class="calendar-close-btn" type="button" id="calendar-close" aria-label="Close calendar">×</button>
                </div>
            </div>
            <div class="calendar-weekdays">
                <span>Mon</span>
                <span>Tue</span>
                <span>Wed</span>
                <span>Thu</span>
                <span>Fri</span>
                <span>Sat</span>
                <span>Sun</span>
            </div>
            <div class="calendar-grid" id="calendar-grid" role="grid"></div>
            <div class="calendar-detail" id="calendar-detail">
                <p class="calendar-detail-heading" id="calendar-detail-heading">Select a day</p>
                <p class="calendar-detail-empty" id="calendar-detail-empty">Tap a day with events to see details.</p>
                <div class="calendar-detail-list" id="calendar-detail-list"></div>
            </div>
        </div>
    </div>
    <div class="upcoming-modal-overlay" id="upcoming-modal" aria-hidden="true">
        <div class="upcoming-modal-backdrop" id="upcoming-modal-backdrop"></div>
        <div class="upcoming-modal-dialog" role="dialog" aria-modal="true" aria-labelledby="upcoming-modal-title">
            <div class="upcoming-modal-head">
                <div>
                    <p class="upcoming-modal-title" id="upcoming-modal-title">Upcoming schedule</p>
                    <p class="upcoming-modal-subtitle">All upcoming events across your courses</p>
                </div>
                <button class="upcoming-modal-close" type="button" id="upcoming-modal-close" aria-label="Close upcoming schedule">×</button>
            </div>
            <div class="upcoming-modal-body">
                {% if upcoming_all_events and upcoming_all_events|length > 0 %}
                    {% for day in upcoming_all_events %}
                    <div class="upcoming-modal-day">
                        <div class="upcoming-day-header">
                            <span class="day-number">{{ day.day_label }}</span>
                            <span class="day-weekday">{{ day.weekday }}</span>
                            <span class="day-full">{{ day.full_label }}</span>
                        </div>
                        <div class="upcoming-modal-events">
                            {% for event in day.events %}
                            <div class="event-row event-row-modal">
                                <div>
                                    <p class="event-row-title">{{ event.title }}</p>
                                    <p class="event-row-meta">
                                        <span class="upcoming-time">{{ event.time_label }}</span>
                                        {% if event.location %}
                                            · <span class="upcoming-location">{{ event.location }}</span>
                                        {% endif %}
                                    </p>
                                </div>
                                <div class="event-row-badges">
                                    <span class="badge badge-course badge-xs">{{ event.course_short }}</span>
                                    <span class="badge badge-kind badge-xs">{{ event.kind }}</span>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p class="upcoming-empty">No upcoming events found.</p>
                {% endif %}
            </div>
        </div>
    </div>
    <script>
        document.addEventListener("DOMContentLoaded", function () {
            var scheduleEvents = {{ calendar_events_data|tojson }};
            var eventsByDate = {};
            scheduleEvents.forEach(function (event) {
                if (!eventsByDate[event.date]) {
                    eventsByDate[event.date] = [];
                }
                eventsByDate[event.date].push(event);
            });
            Object.keys(eventsByDate).forEach(function (dateKey) {
                eventsByDate[dateKey].sort(function (a, b) {
                    var aKey = a.start_time || a.time_display || "";
                    var bKey = b.start_time || b.time_display || "";
                    return aKey.localeCompare(bKey);
                });
            });

            var todayIso = "{{ today_iso }}";
            var initialYear = {{ mini_calendar.year }};
            var initialMonth = {{ mini_calendar.month }};
            var overlay = document.getElementById("calendar-overlay");
            var miniGrid = document.getElementById("mini-calendar-grid");
            var miniTitle = document.getElementById("mini-calendar-title");
            var miniCalendarCard = document.getElementById("mini-calendar-card");
            var miniNavButtons = document.querySelectorAll("[data-mini-nav]");
            var calendarGrid = document.getElementById("calendar-grid");
            var detailHeading = document.getElementById("calendar-detail-heading");
            var detailList = document.getElementById("calendar-detail-list");
            var detailEmpty = document.getElementById("calendar-detail-empty");
            var monthLabel = document.getElementById("calendar-month-label");
            var closeBtn = document.getElementById("calendar-close");
            var backdrop = document.getElementById("calendar-backdrop");
            var navButtons = document.querySelectorAll("[data-calendar-nav]");
            var fullScheduleButtons = document.querySelectorAll("[data-open-full-schedule='true']");
            var upcomingModal = document.getElementById("upcoming-modal");
            var upcomingModalBackdrop = document.getElementById("upcoming-modal-backdrop");
            var upcomingModalClose = document.getElementById("upcoming-modal-close");
            var upcomingModalButtons = document.querySelectorAll("[data-open-upcoming-schedule='true']");

            var calendarState = {
                currentYear: initialYear,
                currentMonth: initialMonth,
                selectedDate: null,
                todayIso: todayIso,
                eventsByDate: eventsByDate,
            };

            function pad(value) {
                return String(value).padStart(2, "0");
            }

            function monthPrefix(year, month) {
                return year + "-" + pad(month);
            }

            function formatMonthYear(year, month) {
                var formatter = new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric" });
                return formatter.format(new Date(year, month - 1, 1));
            }

            function buildMiniCells(year, month) {
                var firstDay = new Date(year, month - 1, 1);
                var startWeekday = (firstDay.getDay() + 6) % 7;
                var daysInMonth = new Date(year, month, 0).getDate();
                var cells = [];
                for (var i = 0; i < startWeekday; i++) {
                    cells.push({ placeholder: true });
                }
                for (var day = 1; day <= daysInMonth; day++) {
                    var iso = monthPrefix(year, month) + "-" + pad(day);
                    cells.push({
                        placeholder: false,
                        iso: iso,
                        dayNumber: day,
                        year: year,
                        month: month,
                        events: eventsByDate[iso] || [],
                        isToday: iso === todayIso,
                    });
                }
                while (cells.length % 7 !== 0) {
                    cells.push({ placeholder: true });
                }
                return cells;
            }

            function buildFullCells(year, month) {
                var firstOfMonth = new Date(year, month - 1, 1);
                var startDay = (firstOfMonth.getDay() + 6) % 7;
                var startDate = new Date(year, month - 1, 1 - startDay);
                var cells = [];
                for (var i = 0; i < 42; i++) {
                    var cellDate = new Date(startDate);
                    cellDate.setDate(startDate.getDate() + i);
                    var iso = cellDate.toISOString().split("T")[0];
                    cells.push({
                        iso: iso,
                        dayNumber: cellDate.getDate(),
                        year: cellDate.getFullYear(),
                        month: cellDate.getMonth() + 1,
                        isCurrentMonth:
                            cellDate.getFullYear() === year && cellDate.getMonth() + 1 === month,
                        isToday: iso === todayIso,
                        events: eventsByDate[iso] || [],
                    });
                }
                return cells;
            }

            function ensureSelectedDateForMonth(force) {
                var prefix = monthPrefix(calendarState.currentYear, calendarState.currentMonth);
                if (!force && calendarState.selectedDate && calendarState.selectedDate.startsWith(prefix)) {
                    return;
                }
                if (calendarState.todayIso && calendarState.todayIso.startsWith(prefix)) {
                    calendarState.selectedDate = calendarState.todayIso;
                    return;
                }
                var monthEvents = Object.keys(eventsByDate)
                    .filter(function (date) {
                        return date.startsWith(prefix);
                    })
                    .sort();
                if (monthEvents.length) {
                    calendarState.selectedDate = monthEvents[0];
                    return;
                }
                calendarState.selectedDate = prefix + "-01";
            }

            ensureSelectedDateForMonth(false);

            function createTooltip(events, iso) {
                if (!events.length) {
                    return null;
                }
                var tooltip = document.createElement("div");
                tooltip.className = "mini-day-tooltip";
                var tooltipDate = document.createElement("p");
                tooltipDate.className = "mini-tooltip-date";
                tooltipDate.textContent = new Date(iso + "T00:00:00").toLocaleDateString(undefined, {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                });
                tooltip.appendChild(tooltipDate);
                var list = document.createElement("ul");
                list.className = "mini-tooltip-list";
                events.forEach(function (eventItem) {
                    var listItem = document.createElement("li");
                    listItem.className = "mini-tooltip-item";
                    var heading = document.createElement("div");
                    var strong = document.createElement("strong");
                    strong.textContent = eventItem.course_short;
                    heading.appendChild(strong);
                    heading.appendChild(document.createTextNode(" · " + eventItem.type));
                    listItem.appendChild(heading);
                    var title = document.createElement("div");
                    title.textContent = eventItem.title;
                    listItem.appendChild(title);
                    var meta = document.createElement("span");
                    meta.className = "mini-tooltip-meta";
                    var timeLabel = "";
                    if (eventItem.start_time && eventItem.end_time) {
                        timeLabel = eventItem.start_time + "–" + eventItem.end_time;
                    } else if (eventItem.start_time) {
                        timeLabel = eventItem.start_time;
                    } else if (eventItem.time_display) {
                        timeLabel = eventItem.time_display;
                    }
                    meta.textContent = timeLabel + (eventItem.location ? " · " + eventItem.location : "");
                    listItem.appendChild(meta);
                    list.appendChild(listItem);
                });
                tooltip.appendChild(list);
                return tooltip;
            }

            function renderMiniCalendar() {
                if (!miniGrid || !miniTitle) {
                    return;
                }
                miniTitle.textContent = formatMonthYear(calendarState.currentYear, calendarState.currentMonth);
                miniGrid.innerHTML = "";
                var cells = buildMiniCells(calendarState.currentYear, calendarState.currentMonth);
                cells.forEach(function (cell) {
                    if (cell.placeholder) {
                        var placeholder = document.createElement("div");
                        placeholder.className = "mini-day is-placeholder";
                        miniGrid.appendChild(placeholder);
                        return;
                    }
                    var button = document.createElement("button");
                    button.type = "button";
                    button.className = "mini-day";
                    if (cell.events.length) {
                        button.classList.add("has-events");
                    }
                    if (cell.isToday) {
                        button.classList.add("is-today");
                    }
                    if (calendarState.selectedDate === cell.iso) {
                        button.classList.add("is-selected");
                    }
                    button.setAttribute("data-date", cell.iso);
                    var label = document.createElement("span");
                    label.className = "mini-day-number";
                    label.textContent = cell.dayNumber;
                    button.appendChild(label);
                    if (cell.events.length) {
                        var dots = document.createElement("div");
                        dots.className = "mini-day-dots";
                        var typeSet = {};
                        cell.events.forEach(function (eventItem) {
                            var typeClass = (
                                eventItem.type_badge_class ||
                                eventItem.type ||
                                "other"
                            )
                                .toString()
                                .toLowerCase()
                                .replace(/\s+/g, "-");
                            typeSet[typeClass] = true;
                        });
                        Object.keys(typeSet)
                            .slice(0, 3)
                            .forEach(function (typeClass) {
                                var dot = document.createElement("span");
                                dot.className = "event-dot event-" + typeClass;
                                dots.appendChild(dot);
                            });
                        button.appendChild(dots);
                        var tooltip = createTooltip(cell.events, cell.iso);
                        if (tooltip) {
                            button.appendChild(tooltip);
                        }
                    }
                    button.addEventListener("click", function (event) {
                        event.stopPropagation();
                        calendarState.selectedDate = cell.iso;
                        openOverlay({ forceSelection: false, scroll: true });
                    });
                    button.addEventListener("keydown", function (event) {
                        if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            calendarState.selectedDate = cell.iso;
                            openOverlay({ forceSelection: false, scroll: true });
                        }
                    });
                    miniGrid.appendChild(button);
                });
            }

            function renderEventList() {
                if (!detailHeading || !detailList || !detailEmpty) {
                    return;
                }
                var iso = calendarState.selectedDate;
                if (!iso) {
                    detailHeading.textContent = "Select a day";
                    detailList.innerHTML = "";
                    detailEmpty.style.display = "block";
                    return;
                }
                detailHeading.textContent = new Date(iso + "T00:00:00").toLocaleDateString(undefined, {
                    weekday: "short",
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                });
                var events = eventsByDate[iso] || [];
                detailList.innerHTML = "";
                if (!events.length) {
                    detailEmpty.style.display = "block";
                    return;
                }
                detailEmpty.style.display = "none";
                events.forEach(function (event) {
                    var item = document.createElement("div");
                    item.className = "calendar-detail-item";
                    var time = document.createElement("p");
                    time.className = "calendar-detail-time";
                    if (event.start_time && event.end_time) {
                        time.textContent = event.start_time + "–" + event.end_time;
                    } else if (event.start_time) {
                        time.textContent = event.start_time;
                    } else {
                        time.textContent = event.time_display || "";
                    }
                    var title = document.createElement("p");
                    title.className = "calendar-detail-title";
                    title.textContent = event.title;
                    var meta = document.createElement("p");
                    meta.className = "calendar-detail-meta";
                    var location = event.location ? " • " + event.location : "";
                    meta.textContent = event.course_short + " • " + event.type + location;
                    item.appendChild(time);
                    item.appendChild(title);
                    item.appendChild(meta);
                    detailList.appendChild(item);
                });
            }

            function renderFullCalendar() {
                if (!calendarGrid) {
                    return;
                }
                calendarGrid.innerHTML = "";
                if (monthLabel) {
                    monthLabel.textContent = formatMonthYear(
                        calendarState.currentYear,
                        calendarState.currentMonth
                    );
                }
                var cells = buildFullCells(calendarState.currentYear, calendarState.currentMonth);
                var currentPrefix = monthPrefix(calendarState.currentYear, calendarState.currentMonth);
                var highlightPast = calendarState.todayIso && calendarState.todayIso.startsWith(currentPrefix);
                cells.forEach(function (cell) {
                    var button = document.createElement("button");
                    button.type = "button";
                    button.className = "calendar-cell";
                    if (!cell.isCurrentMonth) {
                        button.classList.add("other-month");
                    }
                    if (cell.isToday) {
                        button.classList.add("is-today");
                    }
                    if (highlightPast && cell.isCurrentMonth && cell.iso < calendarState.todayIso) {
                        button.classList.add("is-past");
                    }
                    if (calendarState.selectedDate === cell.iso) {
                        button.classList.add("selected");
                    }
                    button.setAttribute("data-date", cell.iso);
                    var dateLabel = document.createElement("div");
                    dateLabel.className = "calendar-date";
                    dateLabel.textContent = cell.dayNumber;
                    button.appendChild(dateLabel);
                    if (cell.events.length) {
                        var eventsWrap = document.createElement("div");
                        eventsWrap.className = "calendar-events";
                        cell.events.slice(0, 2).forEach(function (eventItem) {
                            var chip = document.createElement("span");
                            chip.className = "calendar-chip chip-" + (eventItem.type_badge_class || "other");
                            var label = eventItem.start_time ? eventItem.start_time + " " : "";
                            var title = eventItem.title || "";
                            chip.textContent = label + (title.length > 18 ? title.slice(0, 17) + "…" : title);
                            eventsWrap.appendChild(chip);
                        });
                        if (cell.events.length > 2) {
                            var moreChip = document.createElement("span");
                            moreChip.className = "calendar-chip more-chip";
                            moreChip.textContent = "+" + (cell.events.length - 2);
                            eventsWrap.appendChild(moreChip);
                        }
                        button.appendChild(eventsWrap);
                    }
                    button.addEventListener("click", function () {
                        calendarState.currentYear = cell.year;
                        calendarState.currentMonth = cell.month;
                        calendarState.selectedDate = cell.iso;
                        ensureSelectedDateForMonth(false);
                        renderMiniCalendar();
                        renderFullCalendar();
                        renderEventList();
                    });
                    calendarGrid.appendChild(button);
                });
            }

            function scrollSelectedCellIntoView() {
                if (!calendarGrid) {
                    return;
                }
                var selectedCell = calendarGrid.querySelector(".calendar-cell.selected");
                if (selectedCell) {
                    selectedCell.scrollIntoView({ block: "center" });
                }
            }

            function openOverlay(options) {
                var opts = options || {};
                if (opts.forceSelection) {
                    ensureSelectedDateForMonth(true);
                }
                if (overlay) {
                    overlay.classList.add("open");
                    overlay.setAttribute("aria-hidden", "false");
                }
                document.body.style.overflow = "hidden";
                renderFullCalendar();
                renderEventList();
                if (opts.scroll !== false) {
                    scrollSelectedCellIntoView();
                }
            }

            function closeOverlay() {
                if (!overlay) {
                    return;
                }
                overlay.classList.remove("open");
                overlay.setAttribute("aria-hidden", "true");
                document.body.style.overflow = "";
            }

            function changeMonth(offset, forceSelection) {
                var newMonth = calendarState.currentMonth + offset;
                var newYear = calendarState.currentYear;
                while (newMonth < 1) {
                    newMonth += 12;
                    newYear -= 1;
                }
                while (newMonth > 12) {
                    newMonth -= 12;
                    newYear += 1;
                }
                calendarState.currentMonth = newMonth;
                calendarState.currentYear = newYear;
                ensureSelectedDateForMonth(!!forceSelection);
                renderMiniCalendar();
                if (overlay && overlay.classList.contains("open")) {
                    renderFullCalendar();
                    renderEventList();
                }
            }

            renderMiniCalendar();

            miniNavButtons.forEach(function (button) {
                button.addEventListener("click", function (event) {
                    event.stopPropagation();
                    var direction = button.getAttribute("data-mini-nav");
                    var offset = direction === "next" ? 1 : -1;
                    changeMonth(offset, false);
                });
                button.addEventListener("keydown", function (event) {
                    event.stopPropagation();
                });
            });

            if (miniCalendarCard) {
                miniCalendarCard.addEventListener("click", function (event) {
                    if (event.target.closest(".mini-day") || event.target.closest(".mini-calendar-nav")) {
                        return;
                    }
                    openOverlay({ forceSelection: true });
                });
                miniCalendarCard.addEventListener("keydown", function (event) {
                    if (event.target.closest(".mini-day") || event.target.closest(".mini-calendar-nav")) {
                        return;
                    }
                    if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        openOverlay({ forceSelection: true });
                    }
                });
            }

            fullScheduleButtons.forEach(function (button) {
                button.addEventListener("click", function (event) {
                    event.preventDefault();
                    event.stopPropagation();
                    openOverlay({ forceSelection: true });
                });
            });

            function openUpcomingModal() {
                if (!upcomingModal) {
                    return;
                }
                upcomingModal.classList.add("open");
                upcomingModal.setAttribute("aria-hidden", "false");
                document.body.style.overflow = "hidden";
            }

            function closeUpcomingModal() {
                if (!upcomingModal) {
                    return;
                }
                upcomingModal.classList.remove("open");
                upcomingModal.setAttribute("aria-hidden", "true");
                document.body.style.overflow = "";
            }

            upcomingModalButtons.forEach(function (button) {
                button.addEventListener("click", function (event) {
                    event.preventDefault();
                    event.stopPropagation();
                    openUpcomingModal();
                });
            });

            if (upcomingModalClose) {
                upcomingModalClose.addEventListener("click", closeUpcomingModal);
            }
            if (upcomingModalBackdrop) {
                upcomingModalBackdrop.addEventListener("click", closeUpcomingModal);
            }

            navButtons.forEach(function (button) {
                button.addEventListener("click", function () {
                    var direction = button.getAttribute("data-calendar-nav");
                    var offset = direction === "next" ? 1 : -1;
                    changeMonth(offset, true);
                });
            });

            if (closeBtn) {
                closeBtn.addEventListener("click", closeOverlay);
            }
            if (backdrop) {
                backdrop.addEventListener("click", closeOverlay);
            }
            document.addEventListener("keydown", function (event) {
                if (event.key === "Escape") {
                    if (overlay && overlay.classList.contains("open")) {
                        closeOverlay();
                    }
                    if (upcomingModal && upcomingModal.classList.contains("open")) {
                        closeUpcomingModal();
                    }
                }
            });

            if (calendarGrid) {
                calendarGrid.addEventListener("click", function (event) {
                    var cell = event.target.closest(".calendar-cell");
                    if (!cell) {
                        return;
                    }
                    var iso = cell.getAttribute("data-date");
                    if (!iso) {
                        return;
                    }
                    var parts = iso.split("-");
                    calendarState.currentYear = parseInt(parts[0], 10);
                    calendarState.currentMonth = parseInt(parts[1], 10);
                    calendarState.selectedDate = iso;
                    renderMiniCalendar();
                    renderFullCalendar();
                    renderEventList();
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


def _parse_time_string(value: str | None) -> time | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None


def _combine_date_time(date_value: date, time_value: time | None) -> datetime:
    base_time = time_value or time(0, 0)
    return datetime.combine(date_value, base_time, TIMEZONE)


def _estimate_prep_text(event: Dict[str, object]) -> str:
    kind_value = str(event.get("kind") or event.get("type") or "").lower()
    course_label = event.get("course_short") or event.get("course")
    if "hand" in kind_value or "exam" in kind_value:
        return "Prep: finalize your submission materials and review the instructions."
    if "workshop" in kind_value:
        return "Prep: skim your latest notes and bring one question to discuss."
    if "seminar" in kind_value:
        return "Prep: review the assigned readings and note a takeaway."
    if "lecture" in kind_value:
        return f"Prep: glance through the next chapter for {course_label}."
    return "Prep: check the agenda and make sure everything is ready."


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
        start_time_obj = _parse_time_string(start_time)
        end_time_obj = _parse_time_string(end_time)
        start_dt = _combine_date_time(date_value, start_time_obj)
        end_dt = _combine_date_time(date_value, end_time_obj) if end_time_obj else None
        has_time = start_time_obj is not None
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
                "start_dt": start_dt,
                "end_dt": end_dt,
                "has_time": has_time,
                "day": date_value.strftime("%d"),
                "weekday": date_value.strftime("%a"),
                "date_heading": f"{date_value.strftime('%d %b')} – {date_value.strftime('%a')}",
                "time_sort": start_time or "",
                "kind": type_label,
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


def build_calendar_events_data(events: List[Dict[str, object]]) -> List[Dict[str, str]]:
    calendar_items: List[Dict[str, str]] = []
    for event in events:
        event_date = event.get("date")
        if not isinstance(event_date, date):
            continue
        start_time = str(event.get("start_time") or "") or ""
        end_time = str(event.get("end_time") or "") or ""
        calendar_items.append(
            {
                "id": str(event.get("id", "")),
                "date": event_date.isoformat(),
                "title": str(event.get("title") or ""),
                "course": str(event.get("course") or ""),
                "course_short": str(event.get("course_short") or ""),
                "type": str(event.get("type") or ""),
                "type_badge_class": str(event.get("type_badge_class") or "other"),
                "time_display": str(event.get("time_display") or ""),
                "start_time": start_time,
                "end_time": end_time,
                "location": str(event.get("location") or ""),
            }
        )
    return calendar_items


def build_upcoming_highlights(
    events: List[Dict[str, object]], max_items: int = 5
) -> List[Dict[str, object]]:
    now = datetime.now(TIMEZONE)
    future_events: List[Dict[str, object]] = [
        event
        for event in events
        if isinstance(event.get("start_dt"), datetime) and event["start_dt"] >= now
    ]
    highlights: List[Dict[str, object]] = []
    used_ids: set[str] = set()

    def add_event(event: Dict[str, object]) -> None:
        event_id = str(event.get("id") or "")
        if not event_id or event_id in used_ids:
            return
        event_copy = dict(event)
        event_copy["prep_estimate"] = _estimate_prep_text(event_copy)
        highlights.append(event_copy)
        used_ids.add(event_id)

    def kind_label(event: Dict[str, object]) -> str:
        return str(event.get("kind") or event.get("type") or "").lower()

    for event in future_events:
        kind = kind_label(event)
        if "hand" in kind or "exam" in kind:
            add_event(event)
            break

    for event in future_events:
        if len(highlights) >= max_items:
            break
        kind = kind_label(event)
        if "workshop" in kind:
            add_event(event)
            break

    lecture_courses: set[str] = set()
    for event in future_events:
        if len(highlights) >= max_items:
            break
        kind = kind_label(event)
        if "lecture" not in kind:
            continue
        course_key = str(
            event.get("course_short") or event.get("course") or event.get("course_slug") or ""
        )
        if not course_key or course_key in lecture_courses:
            continue
        add_event(event)
        lecture_courses.add(course_key)

    if len(highlights) < max_items:
        for event in future_events:
            if len(highlights) >= max_items:
                break
            if str(event.get("id") or "") in used_ids:
                continue
            add_event(event)

    highlights.sort(key=lambda item: item.get("start_dt") or now)
    return highlights[:max_items]


def _format_event_display(event: Dict[str, object]) -> Dict[str, object]:
    start_dt = event.get("start_dt")
    end_dt = event.get("end_dt")
    has_time = bool(event.get("has_time"))
    if isinstance(start_dt, datetime) and has_time:
        time_label = start_dt.strftime("%H:%M")
        if isinstance(end_dt, datetime):
            time_label = f"{time_label} – {end_dt.strftime('%H:%M')}"
    else:
        time_label = str(event.get("time_display") or "Time TBA")
    day_label = ""
    weekday_short = ""
    full_day = ""
    if isinstance(start_dt, datetime):
        day_label = start_dt.strftime("%d")
        weekday_short = start_dt.strftime("%a")
        full_day = start_dt.strftime("%A, %d %B %Y")
    display = {
        "id": event.get("id"),
        "title": event.get("title"),
        "course": event.get("course"),
        "course_short": event.get("course_short") or event.get("course"),
        "kind": event.get("kind") or event.get("type"),
        "kind_badge_class": event.get("type_badge_class") or "other",
        "location": event.get("location") or "",
        "time_label": time_label,
        "prep_estimate": _estimate_prep_text(event),
        "has_time": has_time,
        "start_dt": start_dt,
        "end_dt": end_dt,
        "day_label": day_label,
        "weekday": weekday_short,
        "full_day_label": full_day,
    }
    return display


def _group_future_events_by_date(
    events: List[Dict[str, object]], today: date, *, max_days: int | None = None
) -> List[Dict[str, object]]:
    grouped: List[Dict[str, object]] = []
    day_lookup: Dict[str, Dict[str, object]] = {}
    for event in events:
        start_dt = event.get("start_dt")
        if not isinstance(start_dt, datetime):
            continue
        event_date = start_dt.date()
        if event_date < today:
            continue
        date_key = event_date.isoformat()
        if date_key not in day_lookup:
            if max_days is not None and len(grouped) >= max_days:
                break
            day_info = {
                "date": event_date,
                "date_iso": date_key,
                "day_label": event_date.strftime("%d"),
                "weekday": event_date.strftime("%a"),
                "full_label": event_date.strftime("%A, %d %B %Y"),
                "events": [],
            }
            grouped.append(day_info)
            day_lookup[date_key] = day_info
        day_lookup[date_key]["events"].append(_format_event_display(event))
    return grouped


def build_upcoming_preview_events(
    events: List[Dict[str, object]], today: date, limit: int = 3
) -> List[Dict[str, object]]:
    preview_events: List[Dict[str, object]] = []
    count = 0
    for day in _group_future_events_by_date(events, today, max_days=None):
        for event in day["events"]:
            preview_events.append(event)
            count += 1
            if count >= limit:
                return preview_events
    return preview_events


def build_upcoming_modal_days(
    events: List[Dict[str, object]], today: date
) -> List[Dict[str, object]]:
    return _group_future_events_by_date(events, today, max_days=None)


def _mini_calendar_category(type_value: str) -> str:
    lowered = type_value.lower()
    if "lecture" in lowered:
        return "lecture"
    if "seminar" in lowered:
        return "seminar"
    if "workshop" in lowered:
        return "workshop"
    if "hand-in" in lowered or "deadline" in lowered:
        return "deadline"
    if "exam" in lowered:
        return "deadline"
    return "other"


def build_month_events_map(
    events: List[Dict[str, object]], year: int, month: int
) -> Dict[str, List[Dict[str, object]]]:
    event_map: Dict[str, List[Dict[str, object]]] = {}
    for event in events:
        event_date = event.get("date")
        if not isinstance(event_date, date):
            continue
        if event_date.year != year or event_date.month != month:
            continue
        iso_key = event_date.isoformat()
        time_label = ""
        start_time = str(event.get("start_time") or "").strip()
        end_time = str(event.get("end_time") or "").strip()
        if start_time and end_time:
            time_label = f"{start_time}\u2013{end_time}"
        elif start_time:
            time_label = start_time
        else:
            time_label = str(event.get("time_display") or "")
        event_info = {
            "title": str(event.get("title") or ""),
            "course": str(event.get("course") or ""),
            "course_short": str(event.get("course_short") or ""),
            "type": str(event.get("type") or ""),
            "type_badge_class": str(event.get("type_badge_class") or "other"),
            "time": time_label,
            "location": str(event.get("location") or ""),
        }
        event_map.setdefault(iso_key, []).append(event_info)
    return event_map


def build_mini_calendar_data(
    events: List[Dict[str, object]],
    today: date,
    *,
    target_year: int | None = None,
    target_month: int | None = None,
) -> Dict[str, object]:
    year = target_year or today.year
    month = target_month or today.month
    if month < 1:
        month = 1
    if month > 12:
        month = 12
    first_day = date(year, month, 1)
    _, total_days = calendar.monthrange(year, month)
    weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    event_map = build_month_events_map(events, year, month)
    days: List[Dict[str, object]] = []
    leading_blanks = first_day.weekday()
    for _ in range(leading_blanks):
        days.append({"is_current_month": False})
    for day_number in range(1, total_days + 1):
        current_day = date(year, month, day_number)
        iso_key = current_day.isoformat()
        event_entries = event_map.get(iso_key, [])
        type_set = {
            _mini_calendar_category(str(entry.get("type") or entry.get("type_badge_class", "")))
            for entry in event_entries
            if entry
        }
        event_types = sorted(t for t in type_set if t)
        days.append(
            {
                "day_number": day_number,
                "is_current_month": True,
                "is_today": current_day == today,
                "event_types": event_types,
                "has_events": bool(event_types),
                "events": event_entries,
                "full_label": current_day.strftime("%A, %d %B %Y"),
                "date_iso": iso_key,
            }
        )
    while len(days) % 7 != 0:
        days.append({"is_current_month": False})
    return {
        "month_label": first_day.strftime("%B %Y"),
        "weekday_labels": weekday_labels,
        "year": year,
        "month": month,
        "month_value": f"{year:04d}-{month:02d}",
        "days": days,
    }


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
    upcoming_highlights = build_upcoming_highlights(all_courses_schedule_sorted, max_items=5)
    upcoming_preview_events = build_upcoming_preview_events(study_schedule_upcoming, today, limit=3)
    upcoming_all_events = build_upcoming_modal_days(study_schedule_upcoming, today)
    upcoming_total_events = sum(len(day["events"]) for day in upcoming_all_events)
    calendar_events_data = build_calendar_events_data(all_courses_schedule_sorted)
    mini_month_param = request.args.get("mini_month", "")
    target_year: int | None = None
    target_month: int | None = None
    match = re.fullmatch(r"(\d{4})-(\d{2})", mini_month_param)
    if match:
        potential_year = int(match.group(1))
        potential_month = int(match.group(2))
        if 1 <= potential_month <= 12:
            target_year = potential_year
            target_month = potential_month
    mini_calendar = build_mini_calendar_data(
        all_courses_schedule_sorted, today, target_year=target_year, target_month=target_month
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
        upcoming_highlights=upcoming_highlights,
        upcoming_preview_events=upcoming_preview_events,
        upcoming_all_events=upcoming_all_events,
        upcoming_total_events=upcoming_total_events,
        calendar_events_data=calendar_events_data,
        mini_calendar=mini_calendar,
        today_iso=today.isoformat(),
    )


@app.route("/chat", methods=["POST"])
def chat() -> tuple[dict[str, str], int] | tuple[dict[str, str], int, dict[str, str]]:
    data = request.get_json()
    user_message = data.get("message", "") if isinstance(data, dict) else ""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are Peggy’s study assistant. Always clear, helpful, and concise.",
            },
            {"role": "user", "content": user_message},
        ],
    )

    reply = response.choices[0].message["content"]
    return jsonify({"reply": reply})


if __name__ == "__main__":
    print("Open http://127.0.0.1:5000 in your browser to see your study dashboard.")
    app.run(host="127.0.0.1", port=5000, debug=False)
