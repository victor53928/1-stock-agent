#!/usr/bin/env python3
"""얀덱스(Яндекс) 뉴스 기준 러시아 주요 기사를 노션 데이터베이스에 CRUD/쿼리하는 CLI.

환경 변수 (.env):
    NOTION_TOKEN            노션 내부 통합(Internal Integration) 토큰
    YANDEX_NOTION_DATABASE_ID  대상 데이터베이스 ID
    YANDEX_NEWS_RSS_URL     얀덱스 뉴스 RSS 주소 (기본값: 얀덱스 메인 헤드라인)

얀덱스 뉴스는 네이버와 달리 발급받는 API 키가 필요 없는 공개 RSS 피드를 쓴다
(기존 Google 뉴스 RSS 연동과 동일한 방식, utils/data.py의 load_news 참고).

서브커맨드:
    sync    얀덱스 뉴스 주요 기사 상위 N개를 요약해 노션에 저장 (매일 실행용)
    create  기사를 하나 직접 생성
    list    저장된 기사를 날짜 등으로 조회
    get     단일 기사 상세 조회
    update  기존 기사 수정
    delete  기사 삭제(보관 처리)

노션 CRUD/쿼리 자체는 scripts/notion_news_crud.py를 공유한다.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from notion_news_crud import (
    ConfigError,
    create_entry,
    delete_entry,
    format_entry_row,
    get_entry,
    query_entries,
    require_env,
    update_entry,
)

DEFAULT_RSS_URL = "https://news.yandex.ru/index.rss"
MSK = timezone(timedelta(hours=3))


def database_id() -> str:
    return require_env("YANDEX_NOTION_DATABASE_ID")


# --------------------------------------------------------------------------
# 얀덱스 뉴스
# --------------------------------------------------------------------------


def strip_html(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def fetch_yandex_news(rss_url: str | None = None) -> list[dict[str, Any]]:
    """얀덱스 뉴스 RSS 피드에서 기사 목록을 가져온다 (API 키 불필요)."""
    url = rss_url or os.environ.get("YANDEX_NEWS_RSS_URL", DEFAULT_RSS_URL)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        raw = response.read()
    root = ET.fromstring(raw)

    items = []
    for item in root.findall(".//item"):
        source_el = item.find("source")
        category_el = item.find("category")
        items.append(
            {
                "title": item.findtext("title") or "",
                "link": item.findtext("link") or "",
                "description": item.findtext("description") or "",
                "pubDate": item.findtext("pubDate") or "",
                "source": source_el.text if source_el is not None else "",
                "category": category_el.text if category_el is not None else "",
            }
        )
    return items


def parse_pub_date(raw: str) -> datetime:
    # 예: "Tue, 08 Sep 2026 12:00:00 +0300"
    return datetime.strptime(raw, "%a, %d %b %Y %H:%M:%S %z")


def pick_top_articles(items: list[dict[str, Any]], target_date: datetime.date, count: int) -> list[dict[str, Any]]:
    """target_date(모스크바 기준)에 발행된 기사를 우선으로 상위 count개를 고른다."""
    same_day = []
    others = []
    for item in items:
        try:
            pub = parse_pub_date(item["pubDate"]).astimezone(MSK)
        except (KeyError, ValueError):
            continue
        item["_pub_dt"] = pub
        (same_day if pub.date() == target_date else others).append(item)
    ordered = same_day + others
    return ordered[:count]


# --------------------------------------------------------------------------
# 서브커맨드
# --------------------------------------------------------------------------


def cmd_sync(args: argparse.Namespace) -> None:
    target_date = datetime.now(MSK).date() if not args.date else datetime.strptime(args.date, "%Y-%m-%d").date()

    items = fetch_yandex_news(args.rss_url)
    top_items = pick_top_articles(items, target_date, args.count)

    if not top_items:
        print("얀덱스 뉴스 결과가 없습니다.")
        return

    db_id = database_id()
    created, skipped = 0, 0
    for rank, item in enumerate(top_items, start=1):
        link = item["link"]
        if not link or query_entries(db_id, link=link):
            skipped += 1
            continue
        title = strip_html(item["title"])
        summary = strip_html(item["description"])
        pub_dt = item.get("_pub_dt") or datetime.now(MSK)
        create_entry(
            db_id,
            title=title,
            date=pub_dt,
            rank=rank,
            source=item["source"] or "Яндекс.Новости",
            summary=summary,
            link=link,
            category=item["category"] or "러시아",
        )
        created += 1

    print(f"완료: {target_date} 기준 {created}건 생성, {skipped}건 중복/누락 스킵")


def cmd_create(args: argparse.Namespace) -> None:
    date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now(MSK)
    entry = create_entry(
        database_id(),
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
    results = query_entries(database_id(), date=args.date)
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

    p_sync = sub.add_parser("sync", help="얀덱스 뉴스 주요 기사를 요약해 노션에 저장")
    p_sync.add_argument("--rss-url", help="얀덱스 뉴스 RSS 주소 (기본: YANDEX_NEWS_RSS_URL)")
    p_sync.add_argument("--count", type=int, default=10, help="저장할 기사 수 (기본 10)")
    p_sync.add_argument("--date", help="기준 날짜 YYYY-MM-DD (기본: 오늘, MSK)")
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
    except ET.ParseError as e:
        print(f"RSS 파싱 오류: {e}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"네트워크 오류: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
