#!/usr/bin/env python3
"""Lightweight Canvas API client for fetching active courses."""

from __future__ import annotations

import json
import os
from typing import Dict, Iterable, List
from urllib import error, parse, request


def _get_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Environment variable {name} is required.")
    return value


def _parse_next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip()
        if 'rel="next"' not in section:
            continue
        start = section.find("<")
        end = section.find(">", start + 1)
        if start == -1 or end == -1:
            continue
        return section[start + 1 : end]
    return None


def _fetch_paginated(url: str, headers: Dict[str, str], params: Dict[str, Iterable[str] | str]) -> List[Dict[str, object]]:
    next_url = f"{url}?{parse.urlencode(params, doseq=True)}"
    collected: List[Dict[str, object]] = []
    while next_url:
        req = request.Request(next_url, headers=headers)
        try:
            with request.urlopen(req, timeout=30) as resp:
                payload = resp.read().decode("utf-8")
                page_headers = dict(resp.headers.items())
        except error.HTTPError as exc:
            raise RuntimeError(f"Canvas request failed: {exc}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Network error while contacting Canvas: {exc}") from exc

        try:
            page_data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON from Canvas: {exc}") from exc
        if not isinstance(page_data, list):
            raise RuntimeError("Canvas response is not a list.")
        collected.extend(page_data)
        next_url = _parse_next_link(page_headers.get("Link"))
    return collected


def get_active_courses() -> List[Dict[str, str]]:
    """Return active Canvas courses with full name and short code."""
    base_url = _get_env("CANVAS_BASE_URL").rstrip("/")
    token = _get_env("CANVAS_TOKEN")
    api_url = f"{base_url}/api/v1/courses"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    params = {
        "enrollment_state": "active",
        "per_page": "50",
    }
    raw_courses = _fetch_paginated(api_url, headers, params)

    simplified: List[Dict[str, str]] = []
    for course in raw_courses:
        if not isinstance(course, dict):
            continue
        name = course.get("name")
        code = course.get("course_code") or course.get("code")
        workflow_state = course.get("workflow_state")
        if not isinstance(name, str) or not name.strip():
            continue
        if workflow_state and workflow_state != "available":
            continue
        code_str = code.strip() if isinstance(code, str) else ""
        simplified.append({"name": name.strip(), "code": code_str})
    return simplified


__all__ = ["get_active_courses"]
