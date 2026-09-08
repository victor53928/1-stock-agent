#!/usr/bin/env python3
"""네이버 뉴스 주요 기사를 노션 데이터베이스에 CRUD/쿼리하는 CLI.

환경 변수 (.env):
    NOTION_TOKEN        노션 내부 통합(Internal Integration) 토큰
    NOTION_DATABASE_ID  대상 데이터베이스 ID
    NAVER_CLIENT_ID     네이버 오픈API 클라이언트 ID
    NAVER_CLIENT_SECRET 네이버 오픈API 클라이언트 시크릿
    NAVER_NEWS_QUERY    검색 키워드 (기본값: 증시)

서브커맨드:
    sync    네이버 뉴스 주요 기사 상위 N개를 요약해 노션에 저장 (매일 실행용)
    create  기사를 하나 직접 생성
    list    저장된 기사를 날짜 등으로 조회
    get     단일 기사 상세 조회
    update  기존 기사 수정
    delete  기사 삭제(보관 처리)
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"
KST = timezone(timedelta(hours=9))


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


def notion_database_id() -> str:
    return require_env("NOTION_DATABASE_ID")


# --------------------------------------------------------------------------
# 네이버 뉴스
# --------------------------------------------------------------------------


def strip_html(text: str) -> str:
    """네이버 API가 내려주는 <b> 하이라이트 태그 등을 제거하고 엔티티를 복원한다."""
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def fetch_naver_news(query: str, display: int = 30, sort: str = "date") -> list[dict[str, Any]]:
    """네이버 뉴스 검색 API에서 기사 목록을 가져온다."""
    client_id = require_env("NAVER_CLIENT_ID")
    client_secret = require_env("NAVER_CLIENT_SECRET")
    resp = requests.get(
        NAVER_NEWS_URL,
        params={"query": query, "display": display, "sort": sort},
        headers={
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("items", [])


def parse_pub_date(raw: str) -> datetime:
    # 예: "Mon, 08 Sep 2026 09:00:00 +0900"
    return datetime.strptime(raw, "%a, %d %b %Y %H:%M:%S %z")


def pick_top_articles(items: list[dict[str, Any]], target_date: datetime.date, count: int) -> list[dict[str, Any]]:
    """target_date(KST 기준)에 발행된 기사를 우선으로 상위 count개를 고른다."""
    same_day = []
    others = []
    for item in items:
        try:
            pub = parse_pub_date(item["pubDate"]).astimezone(KST)
        except (KeyError, ValueError):
            continue
        item["_pub_dt"] = pub
        (same_day if pub.date() == target_date else others).append(item)
    ordered = same_day + others
    return ordered[:count]


# --------------------------------------------------------------------------
# 노션 CRUD + 쿼리
# --------------------------------------------------------------------------


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


def create_entry(**kwargs: Any) -> dict[str, Any]:
    payload = {
        "parent": {"database_id": notion_database_id()},
        "properties": build_properties(**kwargs),
    }
    resp = requests.post(f"{NOTION_API_BASE}/pages", headers=notion_headers(), json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def query_entries(
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
        f"{NOTION_API_BASE}/databases/{notion_database_id()}/query",
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


# --------------------------------------------------------------------------
# 출력 helper
# --------------------------------------------------------------------------


def format_entry_row(page: dict[str, Any]) -> str:
    props = page.get("properties", {})
    title = "".join(t["plain_text"] for t in props.get("제목", {}).get("title", []))
    date = (props.get("날짜", {}).get("date") or {}).get("start", "")
    rank = props.get("순위", {}).get("number")
    source = "".join(t["plain_text"] for t in props.get("언론사", {}).get("rich_text", []))
    return f"[{rank or '-'}] {date} {title} ({source})  id={page['id']}"


# --------------------------------------------------------------------------
# 서브커맨드
# --------------------------------------------------------------------------


def cmd_sync(args: argparse.Namespace) -> None:
    query = args.query or os.environ.get("NAVER_NEWS_QUERY", "증시")
    target_date = datetime.now(KST).date() if not args.date else datetime.strptime(args.date, "%Y-%m-%d").date()

    items = fetch_naver_news(query, display=max(args.count * 3, 30), sort="date")
    top_items = pick_top_articles(items, target_date, args.count)

    if not top_items:
        print(f"'{query}' 검색 결과가 없습니다.")
        return

    created, skipped = 0, 0
    for rank, item in enumerate(top_items, start=1):
        link = item["originallink"] or item["link"]
        if query_entries(link=link):
            skipped += 1
            continue
        title = strip_html(item["title"])
        summary = strip_html(item["description"])
        pub_dt = item.get("_pub_dt") or datetime.now(KST)
        create_entry(
            title=title,
            date=pub_dt,
            rank=rank,
            source=query,
            summary=summary,
            link=link,
            category=query,
        )
        created += 1

    print(f"완료: {target_date} 기준 {created}건 생성, {skipped}건 중복 스킵 (쿼리='{query}')")


def cmd_create(args: argparse.Namespace) -> None:
    date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now(KST)
    entry = create_entry(
        title=args.title,
        date=date,
        rank=args.rank,
        source=args.source,
        summary=args.summary,
        link=args.link,
        category=args.category,
    )
    print(f"생성됨: id={entry['id']}")


def cmd_list(args: argparse.Namespace) -> None:
    results = query_entries(date=args.date)
    if not results:
        print("결과 없음")
        return
    for page in results:
        print(format_entry_row(page))


def cmd_get(args: argparse.Namespace) -> None:
    page = get_entry(args.page_id)
    print(format_entry_row(page))


def cmd_update(args: argparse.Namespace) -> None:
    date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else None
    update_entry(
        args.page_id,
        title=args.title,
        date=date,
        rank=args.rank,
        source=args.source,
        summary=args.summary,
        link=args.link,
        category=args.category,
    )
    print(f"수정됨: id={args.page_id}")


def cmd_delete(args: argparse.Namespace) -> None:
    delete_entry(args.page_id)
    print(f"삭제(보관)됨: id={args.page_id}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_sync = sub.add_parser("sync", help="네이버 뉴스 주요 기사를 요약해 노션에 저장")
    p_sync.add_argument("--query", help="검색 키워드 (기본: NAVER_NEWS_QUERY 또는 '증시')")
    p_sync.add_argument("--count", type=int, default=10, help="저장할 기사 수 (기본 10)")
    p_sync.add_argument("--date", help="기준 날짜 YYYY-MM-DD (기본: 오늘, KST)")
    p_sync.set_defaults(func=cmd_sync)

    p_create = sub.add_parser("create", help="기사 직접 생성")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--date", help="YYYY-MM-DD (기본: 오늘)")
    p_create.add_argument("--rank", type=int)
    p_create.add_argument("--source")
    p_create.add_argument("--summary")
    p_create.add_argument("--link")
    p_create.add_argument("--category")
    p_create.set_defaults(func=cmd_create)

    p_list = sub.add_parser("list", help="저장된 기사 조회")
    p_list.add_argument("--date", help="YYYY-MM-DD로 필터")
    p_list.set_defaults(func=cmd_list)

    p_get = sub.add_parser("get", help="단일 기사 조회")
    p_get.add_argument("page_id")
    p_get.set_defaults(func=cmd_get)

    p_update = sub.add_parser("update", help="기존 기사 수정")
    p_update.add_argument("page_id")
    p_update.add_argument("--title")
    p_update.add_argument("--date", help="YYYY-MM-DD")
    p_update.add_argument("--rank", type=int)
    p_update.add_argument("--source")
    p_update.add_argument("--summary")
    p_update.add_argument("--link")
    p_update.add_argument("--category")
    p_update.set_defaults(func=cmd_update)

    p_delete = sub.add_parser("delete", help="기사 삭제(보관 처리)")
    p_delete.add_argument("page_id")
    p_delete.set_defaults(func=cmd_delete)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ConfigError as e:
        print(f"설정 오류: {e}", file=sys.stderr)
        return 1
    except requests.HTTPError as e:
        print(f"API 오류: {e.response.status_code} {e.response.text}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
