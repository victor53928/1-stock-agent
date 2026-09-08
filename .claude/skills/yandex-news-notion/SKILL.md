---
name: yandex-news-notion
description: "얀덱스(Яндекс) 뉴스 기준 러시아 주요 기사를 노션 데이터베이스에 CRUD/쿼리하는 CLI(`scripts/yandex_news_notion.py`) 사용법. 매일 낮 12시 GitHub Actions로 상위 10개 기사를 요약해 자동 저장한다. '얀덱스 뉴스 노션에 저장', '러시아 뉴스 동기화', '노션 얀덱스 뉴스 DB 조회/수정/삭제' 같은 요청에 사용한다."
---

# 얀덱스 뉴스 → 노션 동기화 CLI

`scripts/yandex_news_notion.py`는 얀덱스 뉴스 공개 RSS 피드에서 러시아 주요
기사를 가져와 노션 데이터베이스에 생성/조회/수정/삭제(CRUD)하는 CLI다.
GitHub Actions 워크플로(`.github/workflows/yandex-news-notion.yml`)가 매일
12:00 KST(정오)에 `sync` 서브커맨드를 실행해 그날 주요 기사 10개를 요약해
저장한다. 노션 CRUD/쿼리 자체는 `naver-news-notion` 스킬과 함께
`scripts/notion_news_crud.py`를 공유한다.

**시각 해석**: 사용자가 "매일 아침 12시"로 요청했는데 "아침"과 "12시"가
문자적으로는 상충한다(정오 vs 자정). 이 구현은 **낮 12시(정오, KST)**로
해석했다 — 자정을 원한다면 워크플로의 cron을 `0 15 * * *`(전날 UTC 15:00 =
자정 KST)로 바꿔야 한다.

## 데이터베이스

- 노션 데이터베이스: "얀덱스 뉴스 요약" (속성: 제목/날짜/순위/언론사/요약/링크/카테고리,
  네이버용 DB와 동일한 스키마이지만 별도 데이터베이스)
- ID는 `.env`의 `YANDEX_NOTION_DATABASE_ID`에 저장되어 있다 (커밋되지 않음).

## 최초 설정 (사람이 직접 해야 하는 단계)

1. `naver-news-notion`과 같은 노션 통합을 재사용하면 된다 (`NOTION_TOKEN`).
   아직 없다면 https://www.notion.so/my-integrations 에서 만든다.
2. "얀덱스 뉴스 요약" 데이터베이스 페이지에서 `···` → "연결 추가"로 그
   통합을 공유한다 (공유하지 않으면 401/404가 난다).
3. 얀덱스 뉴스는 **API 키가 필요 없는 공개 RSS**(`YANDEX_NEWS_RSS_URL`,
   기본값 `https://news.yandex.ru/index.rss`)를 쓰므로 추가 발급 절차가 없다.
   다만 이 저장소를 개발한 샌드박스 환경에서는 조직 프록시 정책이
   `news.yandex.ru`를 차단(`403`)해 실제 호출을 직접 검증하지 못했다 —
   GitHub Actions 등 일반 인터넷 접근이 가능한 환경에서 먼저
   `python scripts/yandex_news_notion.py sync --count 1`로 한 번
   테스트해볼 것을 권장한다. 피드가 막혀 있다면 `--rss-url`/`YANDEX_NEWS_RSS_URL`을
   다른 얀덱스 뉴스 RSS 카테고리 주소로 바꿔본다.
4. GitHub Actions로 매일 자동 실행하려면, 저장소 Settings → Secrets에
   `NOTION_TOKEN`, `YANDEX_NOTION_DATABASE_ID` (선택: `YANDEX_NEWS_RSS_URL`)을
   등록한다.

## 사용법

```bash
pip install -r requirements.txt

# 오늘 기준 주요 기사 10개 요약 저장 (매일 12:00 KST GitHub Actions가 실행하는 것과 동일)
python scripts/yandex_news_notion.py sync --count 10

# 특정 날짜/다른 RSS로 동기화
python scripts/yandex_news_notion.py sync --date 2026-09-08 --rss-url https://news.yandex.ru/world.rss

# 조회 (쿼리)
python scripts/yandex_news_notion.py list --date 2026-09-08

# 단일 기사 상세
python scripts/yandex_news_notion.py get <page_id>

# 직접 생성
python scripts/yandex_news_notion.py create --title "제목" --summary "요약" --link "https://..." --source "언론사"

# 수정
python scripts/yandex_news_notion.py update <page_id> --summary "수정된 요약"

# 삭제 (노션 특성상 보관 처리 = archived: true)
python scripts/yandex_news_notion.py delete <page_id>
```

## 핵심 동작

- `sync`는 얀덱스 메인 헤드라인 RSS(`index.rss`)를 그대로 쓴다 — 이미
  러시아어 서비스의 대표 헤드라인이라 "러시아 주요 기사"라는 요구와 맞는다.
  네이버처럼 검색 키워드가 아니라 피드 자체가 상위 기사 목록이다.
- 기준 날짜(모스크바 시간, UTC+3)에 발행된 기사를 우선 정렬해 상위 N개를
  뽑는다 (`pick_top_articles`, `naver_news_notion.py`와 동일한 패턴).
- "요약"은 RSS `description` 필드에서 HTML 태그를 제거한 값이다
  (`strip_html`). 원문이 러시아어이므로 요약도 러시아어 그대로 저장된다 —
  한국어 번역 요약이 필요하면 번역/LLM 호출 단계를 추가해야 한다(현재는
  구현하지 않음).
- 같은 기사를 재실행 시 중복 저장하지 않도록, 생성 전에 `링크` 속성으로
  기존 항목을 쿼리해 존재하면 건너뛴다.

## 자주 나는 오류

- `설정 오류: 환경 변수 ...이 설정되어 있지 않습니다` → `.env`에 해당 값이 비어있음.
- `API 오류: 401 ...` → `NOTION_TOKEN`이 없거나, 통합을 데이터베이스에 공유하지 않음.
- `네트워크 오류: ...403...` 또는 RSS 파싱 오류 → 실행 환경에서
  `news.yandex.ru`가 차단되었거나 피드 구조/주소가 바뀐 경우. `--rss-url`로
  대체 피드를 시도한다.
