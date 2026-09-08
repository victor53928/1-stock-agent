---
name: naver-news-notion
description: "네이버 뉴스 주요 기사를 노션 데이터베이스에 CRUD/쿼리하는 CLI(`scripts/naver_news_notion.py`) 사용법. 매일 아침 6시 GitHub Actions로 상위 10개 기사를 요약해 자동 저장한다. '네이버 뉴스 노션에 저장', '뉴스 동기화', '노션 뉴스 DB 조회/수정/삭제' 같은 요청에 사용한다."
---

# 네이버 뉴스 → 노션 동기화 CLI

`scripts/naver_news_notion.py`는 네이버 뉴스 검색 API(오픈API)에서 기사를 가져와
노션 데이터베이스에 생성/조회/수정/삭제(CRUD)하는 단일 CLI다. GitHub Actions
워크플로(`.github/workflows/naver-news-notion.yml`)가 매일 06:00 KST에
`sync` 서브커맨드를 실행해 그날 주요 기사 10개를 요약해 저장한다.

## 데이터베이스

- 노션 데이터베이스: "네이버 뉴스 요약" (속성: 제목/날짜/순위/언론사/요약/링크/카테고리)
- ID는 `.env`의 `NOTION_DATABASE_ID`에 저장되어 있다 (커밋되지 않음, `.env.example` 참고).

## 최초 설정 (사람이 직접 해야 하는 단계)

이 스킬/CLI는 Claude의 노션 커넥터가 아니라 **독립 실행형 REST 호출**을 쓰므로,
사람이 아래를 준비해야 실제로 동작한다:

1. https://www.notion.so/my-integrations 에서 내부 통합(Internal Integration)을
   만들고 토큰을 발급받아 `.env`의 `NOTION_TOKEN`에 넣는다.
2. 위에서 만든 "네이버 뉴스 요약" 데이터베이스 페이지에서 `···` → "연결 추가"로
   그 통합을 공유한다 (공유하지 않으면 401/404가 난다).
3. https://developers.naver.com/apps/#/register 에서 애플리케이션을 등록해
   `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET`을 발급받아 `.env`에 채운다.
4. GitHub Actions로 매일 자동 실행하려면, 저장소 Settings → Secrets에
   `NOTION_TOKEN`, `NOTION_DATABASE_ID`, `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`
   (선택: `NAVER_NEWS_QUERY`)을 동일한 이름으로 등록한다.

## 사용법

```bash
pip install -r requirements.txt

# 오늘 기준 주요 기사 10개 요약 저장 (매일 06:00 KST GitHub Actions가 실행하는 것과 동일)
python scripts/naver_news_notion.py sync --count 10

# 특정 날짜/키워드로 동기화
python scripts/naver_news_notion.py sync --date 2026-09-08 --query "코스피"

# 조회 (쿼리)
python scripts/naver_news_notion.py list --date 2026-09-08

# 단일 기사 상세
python scripts/naver_news_notion.py get <page_id>

# 직접 생성
python scripts/naver_news_notion.py create --title "제목" --summary "요약" --link "https://..." --source "언론사"

# 수정
python scripts/naver_news_notion.py update <page_id> --summary "수정된 요약"

# 삭제 (노션 특성상 보관 처리 = archived: true)
python scripts/naver_news_notion.py delete <page_id>
```

## 핵심 동작

- `sync`는 네이버 뉴스 검색 API를 `sort=date`로 호출해 최신순으로 받은 뒤,
  기준 날짜(KST)에 발행된 기사를 우선 정렬해 상위 N개를 뽑는다
  (`pick_top_articles`). 네이버 오픈API에는 "헤드라인/랭킹" 전용 엔드포인트가
  없으므로 검색 키워드(`NAVER_NEWS_QUERY`, 기본 "증시")를 대리 신호로 쓴다 —
  범위를 바꾸고 싶으면 `--query`로 다른 키워드를 넘긴다.
- "요약"은 네이버 API가 내려주는 `description` 스니펫에서 `<b>` 하이라이트
  태그 등 HTML을 제거한 값이다 (`strip_html`). 별도 LLM 호출 없이 동작한다.
- 같은 기사를 재실행 시 중복 저장하지 않도록, 생성 전에 `링크` 속성으로
  기존 항목을 쿼리해 존재하면 건너뛴다 (`query_entries(link=...)`).
- 노션 API 버전은 `2022-06-28`(단일 데이터 소스 데이터베이스 기준)을 쓴다.
  데이터베이스에 데이터 소스를 추가로 붙이는 등 구조를 바꾸면 이 가정이
  깨질 수 있으니, CLI의 `database_id` 기반 CRUD를 그대로 유지해야 한다.

## 자주 나는 오류

- `설정 오류: 환경 변수 ...이 설정되어 있지 않습니다` → `.env`에 해당 값이 비어있음.
- `API 오류: 401 ...` → `NOTION_TOKEN`이 없거나, 통합을 데이터베이스에 공유하지 않음.
- `API 오류: 404 ...` (네이버) → `NAVER_CLIENT_ID`/`SECRET`이 잘못됨.
