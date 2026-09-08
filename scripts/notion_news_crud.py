"""뉴스 요약 노션 데이터베이스 공용 CRUD/쿼리.

네이버·얀덱스 뉴스 동기화 스크립트가 공유하는 모듈이다. 두 데이터베이스 모두
동일한 속성 스키마(제목/날짜/순위/언론사/요약/링크/카테고리)를 쓰므로, 대상
데이터베이스 ID만 호출부에서 넘겨주면 된다.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class ConfigError(RuntimeError):
    pass


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"환경 변수 {name}이 설정되어 있지 않습니다. .env를 확인하세요.")
    return value


def notion_headers() -> dict[str, str]:
    token = require_env("NOTION_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def build_properties(
    title: str | None = None,
    date: datetime | None = None,
    rank: int | None = None,
    source: str | None = None,
    summary: str | None = None,
    link: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    props: dict[str, Any] = {}
    if title is not None:
        props["제목"] = {"title": [{"text": {"content": title[:2000]}}]}
    if date is not None:
        props["날짜"] = {"date": {"start": date.isoformat()}}
    if rank is not None:
        props["순위"] = {"number": rank}
    if source is not None:
        props["언론사"] = {"rich_text": [{"text": {"content": source[:2000]}}]}
    if summary is not None:
        props["요약"] = {"rich_text": [{"text": {"content": summary[:2000]}}]}
    if link is not None:
        props["링크"] = {"url": link}
    if category is not None:
        props["카테고리"] = {"rich_text": [{"text": {"content": category[:2000]}}]}
    return props


def create_entry(database_id: str, **kwargs: Any) -> dict[str, Any]:
    payload = {
        "parent": {"database_id": database_id},
        "properties": build_properties(**kwargs),
    }
    resp = requests.post(f"{NOTION_API_BASE}/pages", headers=notion_headers(), json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def query_entries(
    database_id: str,
    date: str | None = None,
    link: str | None = None,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    filters = []
    if date:
        filters.append({"property": "날짜", "date": {"equals": date}})
    if link:
        filters.append({"property": "링크", "url": {"equals": link}})

    body: dict[str, Any] = {"page_size": page_size}
    if len(filters) == 1:
        body["filter"] = filters[0]
    elif len(filters) > 1:
        body["filter"] = {"and": filters}

    resp = requests.post(
        f"{NOTION_API_BASE}/databases/{database_id}/query",
        headers=notion_headers(),
        json=body,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def get_entry(page_id: str) -> dict[str, Any]:
    resp = requests.get(f"{NOTION_API_BASE}/pages/{page_id}", headers=notion_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


def update_entry(page_id: str, **kwargs: Any) -> dict[str, Any]:
    resp = requests.patch(
        f"{NOTION_API_BASE}/pages/{page_id}",
        headers=notion_headers(),
        json={"properties": build_properties(**kwargs)},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def delete_entry(page_id: str) -> dict[str, Any]:
    """노션은 완전 삭제 API가 없어 보관(archive) 처리로 삭제를 구현한다."""
    resp = requests.patch(
        f"{NOTION_API_BASE}/pages/{page_id}",
        headers=notion_headers(),
        json={"archived": True},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def format_entry_row(page: dict[str, Any]) -> str:
    props = page.get("properties", {})
    title = "".join(t["plain_text"] for t in props.get("제목", {}).get("title", []))
    date = (props.get("날짜", {}).get("date") or {}).get("start", "")
    rank = props.get("순위", {}).get("number")
    source = "".join(t["plain_text"] for t in props.get("언론사", {}).get("rich_text", []))
    return f"[{rank or '-'}] {date} {title} ({source})  id={page['id']}"
