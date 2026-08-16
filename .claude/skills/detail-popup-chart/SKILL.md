---
name: detail-popup-chart
description: "이 프로젝트(증시 대시보드)에서 카드/블록을 클릭했을 때 기간 선택(1개월~5년) 가능한 확대 시세 차트를 팝업(모달)으로 띄우는 패턴. '상세보기 팝업', '카드 클릭하면 차트 보여줘', '기간별 시세 팝업' 같은 요청에 사용한다. 새 의존성 없이 Streamlit 네이티브 st.dialog만 사용한다."
---

# 상세보기 팝업 (st.dialog) 구현 패턴

이 프로젝트는 순수 Python/Streamlit이며 `package.json`/Node 빌드 파이프라인이
**없다**. "React 모달 라이브러리"류의 요청이 와도 npm 패키지를 설치하는 게 아니라,
Streamlit 1.31+ 네이티브 `st.dialog`로 구현한다 (`app_pages/etf.py`에 2026-08-16
적용, 검증 완료). 새 의존성이 전혀 필요 없고, `st.tabs`/`st.altair_chart` 등 어떤
네이티브 위젯도 모달 안에 그대로 넣을 수 있다.

## 언제 이 스킬을 쓰는가

- 카드형 UI(예: `ui.metric_card` 그리드)를 클릭하면 상세 차트/정보를 팝업으로
  보여달라는 요청.
- 기간 프리셋(1개월/3개월/6개월/1년/3년/5년 등)을 골라 차트를 다시 그리는 UI가
  필요할 때.
- "React 모달", "팝업 라이브러리 설치" 같은 요청이 와도, 이 프로젝트엔 JS 빌드
  도구가 없으므로 먼저 `st.dialog`로 될지 사용자에게 확인하고 이 패턴을 쓴다.
  (커스텀 React 컴포넌트를 새로 빌드하는 건 훨씬 무거운 대안이라 사용자가 명시적으로
  원할 때만 고려한다.)

## 핵심 제약

- `streamlit_shadcn_ui`의 `ui.metric_card`/`ui.card`는 클릭 이벤트나 반환값이
  없는 **순수 표시용** 컴포넌트다. 카드 자체를 클릭 가능하게 만들 수 없으므로,
  카드 바로 아래에 `st.button("상세보기 ↗", key=f"detail_btn_{symbol}", width="stretch")`을
  붙이고 그 버튼 클릭을 트리거로 쓴다.
- `st.dialog` 데코레이터는 **모듈 레벨에서 한 번만** 정의한다. 반복문 안에서 매번
  새로 정의하지 않는다 — 인자(`name`, `symbol`)를 받아 내부에서 분기하면 충분하다.
- `st.dialog(title, width=...)`의 `width`는 `"small" | "medium" | "large"` 리터럴만
  허용한다(`"stretch"` 같은 다른 위젯의 width 값과 다름 — 문서 없이 넘기면 타입 에러).
- 팝업 안에서 기간 선택은 `st.tabs`보다 `st.pills`를 추천한다. `st.tabs`는 모든 탭의
  본문 코드를 매 런마다 실행해서 期간마다 API 호출이 발생하지만, `st.pills`는 선택된
  기간 하나만 로드하면 되므로 더 가볍다. 이 앱은 이미 `app_pages/home.py`의 사이드바
  기간 선택에 `st.pills`를 쓰고 있어 컨벤션도 일치한다.
- 기간 프리셋 상수는 `utils/charts.py`의 `HORIZON_DAYS`
  (`{"1개월": 30, "3개월": 90, "6개월": 180, "1년": 365, "3년": 365*3, "5년": 365*5}`)를
  **재사용**한다 — `home.py`와 `etf.py`가 이미 이 상수를 공유한다. 새 페이지에서
  기간 프리셋이 필요하면 로컬에 새로 정의하지 말고 여기서 import한다.
- 확대 차트는 미니 스파크라인(`utils.charts.sparkline`, 축 없음)이 아니라
  `utils.charts.period_chart`(축·툴팁 있는 버전)를 쓴다.

## 구현 스니펫 (`app_pages/etf.py` 기준)

```python
from utils.charts import HORIZON_DAYS, period_chart, sparkline
from utils.data import load_series

@st.dialog("ETF 상세 시세", width="large")
def show_price_detail(name: str, symbol: str) -> None:
    st.subheader(name)
    horizon = st.pills(
        "조회 기간",
        options=list(HORIZON_DAYS.keys()),
        default="6개월",
        key=f"detail_horizon_{symbol}",  # 심볼별로 고유해야 팝업 간 상태가 안 꼬임
    )
    if horizon is None:
        st.info("조회 기간을 선택하세요.", icon=":material/info:")
        return

    detail_start = datetime.now() - timedelta(days=HORIZON_DAYS[horizon])
    try:
        data = load_series(symbol, detail_start)
    except ValueError as e:
        st.error(f"{name}: {e}")
        return

    st.altair_chart(period_chart(data), width="stretch")


# 카드 렌더링 루프 안:
with st.container(width=CARD_WIDTH):
    ui.metric_card(name, f"{last:,.2f}", ..., key=f"etf_{symbol}", width=CARD_WIDTH)
    st.altair_chart(sparkline(data), width="stretch")
    if st.button("상세보기 ↗", key=f"detail_btn_{symbol}", width="stretch"):
        show_price_detail(name, symbol)
```

`load_series`는 `@st.cache_data(ttl="1h")`로 이미 캐시되므로, 같은 종목의 같은
기간을 다시 열어도 재요청하지 않는다.

## 체크리스트

1. 카드 그리드 루프 안에서 심볼별 `key`를 버튼에도 고유하게 부여했는지 확인
   (`detail_btn_{symbol}`, 팝업 내부 위젯도 `detail_horizon_{symbol}`).
2. `st.dialog`가 모듈 레벨에 한 번만 정의됐는지 확인 (루프 안에서 재정의 금지).
3. `HORIZON_DAYS`/`period_chart`를 `utils/charts.py`에서 import했는지, 로컬에
   중복 정의하지 않았는지 확인.
4. 브라우저에서 실제로 버튼을 클릭해 모달이 뜨는지, 기간 탭을 바꿨을 때 차트가
   갱신되는지 확인한다(`streamlit run app.py` 후 클릭 → 스크린샷).
