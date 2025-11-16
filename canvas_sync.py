from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta
from html import unescape
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, cast
from urllib import error, parse, request
from zoneinfo import ZoneInfo


LOCAL_TZ = ZoneInfo("Europe/Stockholm")
UTC_TZ = ZoneInfo("UTC")
LOOKAHEAD_DAYS = 60
DEFAULT_COURSE_KEYWORDS = [
    "uppsala",
    "ht24",
    "ht25",
    "fek",
    "fe",
    "2fe",
    "accounting",
    "strategic",
    "scientific",
    "business",
]
DEFAULT_DOCUMENT_KEYWORDS = ["accounting", "scientific", "business", "model", "theory"]
DOCUMENT_HIGHLIGHT_LIMIT = 5
HTML_TAG_RE = re.compile(r"<[^>]+>")


def normalize_keywords(values: Iterable[str] | None, fallback: List[str]) -> List[str]:
    if not values:
        return fallback
    normalized = []
    for value in values:
        trimmed = value.strip().lower()
        if trimmed:
            normalized.append(trimmed)
    return normalized or fallback


def course_matches_keywords(name: str, keywords: Iterable[str] | None) -> bool:
    if not keywords:
        return True
    lowered = name.lower()
    return any(keyword in lowered for keyword in keywords)


def load_config(config_path: Path) -> Dict[str, object]:
    if not config_path.exists():
        print("Missing canvas_config.json in home directory.")
        sys.exit(1)

    try:
        with config_path.open("r", encoding="utf-8") as cfg_file:
            config = json.load(cfg_file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Failed to read canvas_config.json: {exc}")
        sys.exit(1)

    api_token = config.get("api_token", "").strip()
    base_url = config.get("base_url", "").strip().rstrip("/")

    if not api_token:
        print("Canvas API token missing in canvas_config.json.")
        sys.exit(1)

    if not base_url:
        print("Canvas base_url missing in canvas_config.json.")
        sys.exit(1)

    course_keywords = normalize_keywords(config.get("course_filter_keywords"), DEFAULT_COURSE_KEYWORDS)
    document_keywords = normalize_keywords(config.get("document_focus_keywords"), DEFAULT_DOCUMENT_KEYWORDS)

    return {
        "api_token": api_token,
        "base_url": base_url,
        "course_keywords": course_keywords,
        "document_keywords": document_keywords,
    }


def request_canvas(
    url: str,
    headers: Dict[str, str],
    *,
    suppress_auth_error: bool = False,
) -> Tuple[str | None, Dict[str, str]]:
    req = request.Request(url, headers=headers)
    try:
        with request.urlopen(req, timeout=30) as response:
            data = response.read().decode("utf-8")
            return data, dict(response.headers.items())
    except error.HTTPError as http_error:
        if http_error.code in (401, 403):
            if suppress_auth_error:
                return None, {}
            print("Canvas authentication failed.")
            sys.exit(1)
        if http_error.code == 404 and suppress_auth_error:
            return None, {}
        print(f"HTTP error while contacting Canvas: {http_error}")
        sys.exit(1)
    except error.URLError as url_error:
        print(f"Network error while contacting Canvas: {url_error}")
        sys.exit(1)


def parse_next_link(link_header: str | None) -> str | None:
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


def fetch_json(url: str, headers: Dict[str, str], params: Dict[str, Iterable[str] | str] | None = None):
    if params:
        query = parse.urlencode(params, doseq=True)
        url = f"{url}?{query}"

    data, _ = request_canvas(url, headers)
    if data is None:
        print("Canvas returned an empty response.")
        sys.exit(1)

    try:
        return json.loads(data)
    except json.JSONDecodeError as json_error:
        print(f"Invalid JSON from Canvas: {json_error}")
        sys.exit(1)


def fetch_paginated_list(
    url: str,
    headers: Dict[str, str],
    params: Dict[str, Iterable[str] | str] | None = None,
) -> List[Dict[str, object]]:
    next_url = url
    if params:
        next_url = f"{url}?{parse.urlencode(params, doseq=True)}"

    collected: List[Dict[str, object]] = []
    while next_url:
        data, response_headers = request_canvas(next_url, headers)
        if data is None:
            print("Canvas returned an empty response while fetching paginated data.")
            sys.exit(1)
        try:
            page = json.loads(data)
        except json.JSONDecodeError as json_error:
            print(f"Invalid JSON from Canvas: {json_error}")
            sys.exit(1)

        if not isinstance(page, list):
            print("Expected a list response from Canvas when fetching paginated data.")
            sys.exit(1)

        collected.extend(page)
        next_url = parse_next_link(response_headers.get("Link"))
    return collected


def parse_due_at(value: str | None) -> datetime | None:
    if not value:
        return None

    iso_value = value.replace("Z", "+00:00")
    try:
        due_dt = datetime.fromisoformat(iso_value)
    except ValueError:
        return None

    if due_dt.tzinfo is None:
        due_dt = due_dt.replace(tzinfo=UTC_TZ)

    return due_dt.astimezone(LOCAL_TZ)


def to_local_timestamp(value: str | None) -> str | None:
    if not value:
        return None
    iso_value = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso_value)
    except ValueError:
        return value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC_TZ)
    return parsed.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")


def format_description_excerpt(value: str | None, limit: int = 300) -> str:
    if not value:
        return ""
    without_tags = HTML_TAG_RE.sub(" ", value)
    collapsed = " ".join(unescape(without_tags).split())
    if not collapsed:
        return ""
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[:limit].rstrip()}..."


def read_tasks(tasks_path: Path) -> Tuple[List[Dict[str, object]], str]:
    if not tasks_path.exists():
        return [], "[]\n"

    try:
        original_text = tasks_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Failed to read {tasks_path.name}: {exc}")
        sys.exit(1)

    try:
        tasks = json.loads(original_text)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {tasks_path.name}: {exc}")
        sys.exit(1)

    if not isinstance(tasks, list):
        print(f"{tasks_path.name} must contain a JSON array of tasks.")
        sys.exit(1)

    return tasks, original_text


def write_tasks(
    tasks_path: Path,
    backup_path: Path,
    original_text: str,
    tasks: List[Dict[str, object]],
) -> None:
    try:
        backup_path.write_text(original_text, encoding="utf-8")
    except OSError as exc:
        print(f"Failed to write backup {backup_path.name}: {exc}")
        sys.exit(1)

    try:
        with tasks_path.open("w", encoding="utf-8") as handle:
            json.dump(tasks, handle, indent=2)
            handle.write("\n")
    except OSError as exc:
        print(f"Failed to write {tasks_path.name}: {exc}")
        sys.exit(1)


def write_documents(documents_path: Path, documents: Dict[str, List[Dict[str, object]]]) -> None:
    try:
        with documents_path.open("w", encoding="utf-8") as handle:
            json.dump(documents, handle, indent=2)
            handle.write("\n")
    except OSError as exc:
        print(f"Failed to write {documents_path.name}: {exc}")
        sys.exit(1)


def simplify_courses(courses: List[Dict[str, object]]) -> List[Dict[str, object]]:
    simplified: List[Dict[str, object]] = []
    for course in courses:
        course_name = course.get("name")
        if not isinstance(course_name, str) or not course_name:
            continue
        course_code = course.get("course_code")
        term_name = None
        term = course.get("term")
        if isinstance(term, dict):
            raw_term_name = term.get("name")
            if isinstance(raw_term_name, str):
                term_name = raw_term_name
        simplified.append(
            {
                "name": course_name,
                "code": course_code if isinstance(course_code, str) else "",
                "term": term_name or "",
            }
        )
    simplified.sort(key=lambda entry: entry.get("name", ""))
    return simplified


def write_courses(courses_path: Path, courses: List[Dict[str, object]]) -> None:
    try:
        with courses_path.open("w", encoding="utf-8") as handle:
            json.dump(courses, handle, indent=2)
            handle.write("\n")
    except OSError as exc:
        print(f"Failed to write {courses_path.name}: {exc}")
        sys.exit(1)


def build_task_key(task: Dict[str, object]) -> Tuple[str, str, str, str]:
    return (
        str(task.get("course", "")),
        str(task.get("title", "")),
        str(task.get("due_date", "")),
        str(task.get("due_time", "")),
    )


def collect_course_documents(
    courses: List[Dict[str, object]],
    headers: Dict[str, str],
    base_url: str,
    focus_keywords: List[str],
) -> Dict[str, List[Dict[str, object]]]:
    documents_map: Dict[str, List[Dict[str, object]]] = {}
    for course in courses:
        course_name = course.get("name")
        course_id = course.get("id")
        if not isinstance(course_name, str) or not course_name:
            continue
        if not course_id:
            continue
        if not course_matches_keywords(course_name, focus_keywords):
            continue

        files_url = f"{base_url}/courses/{course_id}/files"
        params = {
            "per_page": "100",
            "sort": "updated_at",
            "order": "desc",
        }
        next_url = f"{files_url}?{parse.urlencode(params, doseq=True)}"
        files: List[Dict[str, object]] = []
        unauthorized = False
        while next_url:
            data, response_headers = request_canvas(next_url, headers, suppress_auth_error=True)
            if data is None:
                unauthorized = True
                break
            try:
                page = json.loads(data)
            except json.JSONDecodeError as json_error:
                print(f"Invalid JSON from Canvas: {json_error}")
                sys.exit(1)
            if not isinstance(page, list):
                break
            for file_data in page:
                if isinstance(file_data, dict):
                    files.append(file_data)
            next_url = parse_next_link(response_headers.get("Link"))

        if unauthorized:
            print(f"Skipping documents for {course_name}: Canvas token lacks file access.")
            continue

        if not files:
            continue

        simplified = []
        for file_data in files:
            if not isinstance(file_data, dict):
                continue
            simplified.append(
                {
                    "id": file_data.get("id"),
                    "name": file_data.get("display_name") or file_data.get("filename"),
                    "content_type": file_data.get("content-type") or file_data.get("content_type"),
                    "size": file_data.get("size"),
                    "updated_at": to_local_timestamp(
                        file_data.get("updated_at") if isinstance(file_data.get("updated_at"), str) else None
                    ),
                    "url": file_data.get("url"),
                }
            )
        documents_map[course_name] = simplified
    return documents_map


def main() -> None:
    home_dir = Path.home()
    config_path = home_dir / "canvas_config.json"
    tasks_path = home_dir / "tasks.json"
    backup_path = home_dir / "tasks_backup_before_canvas.json"
    documents_path = home_dir / "canvas_documents.json"
    courses_path = home_dir / "canvas_courses.json"

    config = load_config(config_path)
    headers = {
        "Authorization": f"Bearer {config['api_token']}",
        "Accept": "application/json",
    }
    course_keywords = cast(List[str], config["course_keywords"])
    document_keywords = cast(List[str], config["document_keywords"])

    courses_url = f"{config['base_url']}/courses"
    courses = fetch_paginated_list(
        courses_url,
        headers,
        params={
            "enrollment_state": "active",
            "include[]": ["term"],
            "per_page": "100",
        },
    )

    available_courses = [course for course in courses if course.get("workflow_state") == "available"]

    document_data = collect_course_documents(available_courses, headers, cast(str, config["base_url"]), document_keywords)
    write_documents(documents_path, document_data)
    document_highlights = {}
    for course_name, docs in document_data.items():
        highlights: List[str] = []
        for doc in docs[:DOCUMENT_HIGHLIGHT_LIMIT]:
            name = doc.get("name")
            if isinstance(name, str) and name:
                highlights.append(name)
        if highlights:
            document_highlights[course_name] = highlights
    document_counts = {course_name: len(files) for course_name, files in document_data.items()}

    assignments_collected: List[Dict[str, object]] = []
    total_assignments = 0
    window_start = datetime.now(LOCAL_TZ).date()
    window_end = window_start + timedelta(days=LOOKAHEAD_DAYS)

    filtered_courses: List[Dict[str, object]] = []
    for course in available_courses:
        course_name = course.get("name")
        course_id = course.get("id")
        if not isinstance(course_name, str) or not course_name:
            continue
        if not course_id:
            continue
        if not course_matches_keywords(course_name, course_keywords):
            continue
        filtered_courses.append(course)

        assignments_url = f"{config['base_url']}/courses/{course_id}/assignments"
        assignments = fetch_paginated_list(
            assignments_url,
            headers,
            params={"bucket": "upcoming", "per_page": "100"},
        )

        total_assignments += len(assignments)

        for assignment in assignments:
            due_at = assignment.get("due_at")
            local_due = parse_due_at(due_at)
            if local_due is None:
                continue
            local_due_date = local_due.date()
            if local_due_date < window_start or local_due_date > window_end:
                continue

            description_excerpt = format_description_excerpt(assignment.get("description"))
            task_entry: Dict[str, object] = {
                "title": assignment.get("name", "Untitled assignment"),
                "course": course_name,
                "due_date": local_due.strftime("%Y-%m-%d"),
                "due_time": local_due.strftime("%H:%M"),
                "type": "assignment",
                "canvas_url": assignment.get("html_url", ""),
            }
            if description_excerpt:
                task_entry["description"] = description_excerpt
            if course_name in document_highlights:
                highlights = document_highlights[course_name]
                if highlights:
                    task_entry["related_documents"] = highlights
                    task_entry["document_count"] = document_counts.get(course_name, 0)
            assignments_collected.append(task_entry)

    existing_tasks, original_text = read_tasks(tasks_path)
    existing_keys = {build_task_key(task) for task in existing_tasks}
    task_lookup = {build_task_key(task): task for task in existing_tasks}
    preserved_fields = {"title", "course", "due_date", "due_time", "type"}

    new_tasks_added = 0
    for task in assignments_collected:
        key = build_task_key(task)
        if key in existing_keys:
            existing_task = task_lookup.get(key)
            if isinstance(existing_task, dict):
                for field, value in task.items():
                    if field in preserved_fields:
                        continue
                    existing_task[field] = value
            continue
        existing_tasks.append(task)
        existing_keys.add(key)
        task_lookup[key] = task
        new_tasks_added += 1

    write_tasks(tasks_path, backup_path, original_text, existing_tasks)
    document_total = sum(document_counts.values())
    simplified_courses = simplify_courses(filtered_courses)
    write_courses(courses_path, simplified_courses)

    print(
        f"Fetched {len(filtered_courses)} courses, "
        f"{total_assignments} assignments, "
        f"added {new_tasks_added} new tasks within {LOOKAHEAD_DAYS} days. "
        f"Cataloged {document_total} documents across {len(document_counts)} courses. "
        f"Saved {len(simplified_courses)} current courses."
    )


if __name__ == "__main__":
    main()
