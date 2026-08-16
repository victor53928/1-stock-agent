---
name: streamlit-shadcn-extras
description: "이 프로젝트(증시 대시보드)에서 streamlit-shadcn-ui 또는 streamlit-extras 컴포넌트를 사용할 때 참고한다. shadcn 스타일 버튼/카드/배지/탭/메트릭카드, extras의 metric_cards 스타일링·dataframe_explorer 필터·grid 레이아웃·chart_container·mention·colored_header 등을 적용하거나, '샤드씨엔', 'shadcn', 'extras 라이브러리 써줘' 같은 요청이 있을 때 사용한다. 기본은 developing-with-streamlit 스킬의 네이티브 우선 원칙을 따르고, 이 스킬은 그 원칙만으로 부족할 때만 보조로 쓴다."
---

# streamlit-shadcn-ui / streamlit-extras 활용 가이드

이 프로젝트(`app.py` + `app_pages/*.py` 멀티페이지 증시 대시보드)에 설치되어 있는
`streamlit-shadcn-ui`(v2 API)와 `streamlit-extras`를 어떻게, 언제 쓸지 정리한 프로젝트
전용 스킬이다. **먼저 `developing-with-streamlit` 스킬의 네이티브 우선 원칙을 따른다** —
`st.metric`, `st.container(border=True)`, `st.badge`, `st.dataframe` 등 네이티브 위젯으로
충분하면 그것을 쓰고, 이 스킬은 네이티브로는 안 되거나 사용자가 명시적으로 shadcn/extras를
요청했을 때만 보조로 사용한다.

## 설치 버전 (2026-08-15 기준)

- `streamlit-shadcn-ui` 1.1.0 (v2 API, `import streamlit_shadcn_ui as ui`)
- `streamlit-extras` 1.6.0
- 둘 다 `streamlit>=1.60`을 요구해서, `streamlit-shadcn-ui` 설치 시 프로젝트의 Streamlit이
  1.59.2 → 1.61.1로 자동 업그레이드된 적이 있다. 두 라이브러리 중 하나를 업그레이드하기 전엔
  `python -m pip show streamlit streamlit-shadcn-ui streamlit-extras`로 버전을 먼저 확인하고,
  적용 후 반드시 앱을 재시작해서 8개 페이지가 전부 에러 없이 뜨는지 확인한다(과거에 서버가
  구버전 `utils/data.py`를 캐싱해 `ImportError`가 난 적이 있음 — 새 함수/컴포넌트 추가 후
  안 뜨면 `streamlit run app.py`를 재시작부터 시도).

## 언제 이 스킬을 쓰는가

- 사용자가 "shadcn 스타일로", "shadcn-ui 컴포넌트 써줘", "extras 라이브러리 활용해줘"처럼
  명시적으로 요청했을 때.
- 네이티브 Streamlit에 없는 기능이 필요할 때: 데이터프레임에 검색/필터 UI
  (`dataframe_explorer`), 차트/표/내보내기를 탭으로 묶기(`chart_container`), 카드형 배지
  (`ui.badge`), 라디어스가 큰 shadcn풍 카드(`ui.card`, `ui.metric_card`).
- 이미 네이티브로 구현된 기능(카드 그림자, 배지, 캔들스틱 차트 등)을 **shadcn 룩앤필로
  바꿔달라**는 요청을 받았을 때만 기존 네이티브 구현을 대체한다. 요청 없이 먼저 바꾸지 않는다.

## streamlit-shadcn-ui (v2) 컴포넌트 레퍼런스

모든 컴포넌트는 `import streamlit_shadcn_ui as ui` 후 `ui.<name>(...)`로 호출한다.
커스텀 iframe 기반 컴포넌트라서 같은 페이지에 여러 개 반복 렌더링할 때는 `key=`를
고유하게 지정해야 상태 충돌이 없다 (특히 `ui.button`, `ui.tabs`).

| 컴포넌트 | 시그니처(핵심) | variant / size 옵션 | 비고 |
|---|---|---|---|
| `ui.button` | `button(label, *, key=None, variant="default", size="default", disabled=False, on_click=None, width="content") -> bool` | variant: default·destructive·outline·secondary·ghost·link / size: default·xs·sm·lg·icon·icon-xs·icon-sm·icon-lg | 클릭 시 `True` 반환. `st.form` 안에서 트리거로 못 씀(라이브러리에서 `fail_if_trigger_in_form`으로 막음) |
| `ui.badge` | `badge(text, *, key=None, variant="default", width="content") -> None` | variant: default·secondary·destructive·outline·ghost·link | 값 반환 없음(순수 표시용). 여러 개는 `ui.badges([(text, variant), ...])` |
| `ui.card` | `card(title=None, content=None, description=None, *, footer=None, key=None, size="default", width="stretch") -> None` | size: default·sm | 상태 없는 정적 카드. 텍스트만 표시(차트/위젯 못 넣음) |
| `ui.metric_card` | `metric_card(label, value, *, description=None, delta=None, variant="default", key=None, size="default", width="stretch") -> None` | variant: default·dashboard / size: default·sm | `variant="dashboard"`가 이 프로젝트의 `st.metric(border=True)` KPI 카드를 대체하기 가장 적합 |
| `ui.tabs` | `tabs(options, *, value=None, format_func=str, key=None, label="Tabs", orientation="horizontal", variant="default", ...) -> T` | orientation: horizontal·vertical | 선택된 값을 반환(콜백 아님). `st.tabs`와 달리 선택 상태를 코드에서 바로 읽을 수 있음 |
| `ui.alert` | `alert(title, description=None, *, key=None, variant="default", width="stretch") -> None` | variant: default·destructive | 에러/경고 표시. `st.error`/`st.warning` 대체용 |
| `ui.progress` | `progress(value=0, *, key=None, label=None, show_value=False, width="stretch") -> None` | - | 0~100 스케일 |
| `ui.table` | `table(data, columns=None, *, key=None, caption=None, max_height=None, width="stretch") -> None` | - | `st.dataframe`보다 표현은 예쁘지만 정렬/필터/컬럼설정(`column_config`)이 없음. 인터랙티브 데이터 탐색이 필요하면 `st.dataframe` 유지 |
| `ui.calendar`, `ui.date_picker` | 날짜 선택 | - | 이 프로젝트는 기간을 `st.pills`(1개월~5년 프리셋)로 처리 중이라 임의 날짜 선택이 필요할 때만 고려 |

### 예시: KPI 카드를 shadcn 스타일로 바꾸기

**적용 완료 (2026-08-15):** 8개 페이지 전체의 KPI/지수/채권/섹터/환율/원자재 카드가 이미
`ui.metric_card(..., variant="dashboard")`로 전환되어 있다. 네이티브 `st.metric`은 이 앱에
더 이상 없으므로 `app.py`의 CARD_SELECTORS에서도 `[data-testid="stMetric"]` 규칙을 뺐다.
예시(`app_pages/home.py`의 KPI 블록):

```python
import streamlit_shadcn_ui as ui

with st.container(horizontal=True):
    ui.metric_card("현재가", fmt_price(last_close), delta=f"{change_pct:.2f}%", variant="dashboard", key=f"kpi_price_{symbol}")
    ui.metric_card("기간 최고", fmt_price(period_high), variant="dashboard", key=f"kpi_high_{symbol}")
    ui.metric_card("기간 최저", fmt_price(period_low), variant="dashboard", key=f"kpi_low_{symbol}")
    ui.metric_card("거래량", f"{last_volume:,.0f}", variant="dashboard", key=f"kpi_volume_{symbol}")
```

**트레이드오프**: `ui.metric_card`는 네이티브 `st.metric`의 `chart_data`(카드 안 스파크라인)를
지원하지 않는다. 이 앱은 shadcn 룩앤필 통일을 위해 스파크라인을 포기하기로 사용자와 합의했다
(2026-08-15). 스파크라인이 다시 필요하면 `ui.metric_card` 대신 네이티브 `st.metric`으로
되돌리거나, 카드 아래 별도 mini Altair 라인차트를 추가해야 한다.

shadcn 카드는 자체 스타일 시스템을 쓰므로 `app.py`의 CSS(`st.html` 블록)로는 꾸밀 수 없다
— 색/모양은 `variant`/`size` 인자로만 조정한다. 반복 루프에서 여러 개 렌더링할 때는
`key=f"prefix_{symbol}"`처럼 종목/심볼 기반으로 고유 키를 꼭 지정한다(안 그러면 라벨이
같은 카드가 여럿일 때 상태가 꼬일 수 있음).

## streamlit-extras 레퍼런스

| 유틸리티 | import | 시그니처(핵심) | 이 프로젝트에서의 용도 |
|---|---|---|---|
| `style_metric_cards` | `from streamlit_extras.metric_cards import style_metric_cards` | `style_metric_cards(background_color=None, border_size_px=1, border_color=None, border_radius_px=5, border_left_color="#9AD8E1", box_shadow=True)` | 네이티브 `st.metric` 카드용 스타일링. **현재 이 앱엔 네이티브 metric이 없어서(전부 `ui.metric_card`로 전환됨) 해당 없음** — 나중에 shadcn을 다시 걷어내고 네이티브로 되돌릴 때 참고 |
| `dataframe_explorer` | `from streamlit_extras.dataframe_explorer import dataframe_explorer` | `dataframe_explorer(df, case=True) -> pd.DataFrame` | **적용됨**: `app_pages/movers.py` "상세 데이터" 테이블에 `filtered = dataframe_explorer(display, case=False)` 후 필터링된 결과에 등락률 색상 스타일(`.style.map`)을 다시 씌워서 표시 |
| `grid` | `from streamlit_extras.grid import grid` | `grid(*spec, gap="small", vertical_align="top") -> GridDeltaGenerator` | **미적용**: `GridDeltaGenerator.__getattr__`이 셀의 네이티브 메서드(`.metric`, `.dataframe` 등)만 프록시하고 `with` 컨텍스트 진입을 공식 지원하지 않아서, `ui.metric_card`처럼 셀 안에서 별도 함수를 호출해야 하는 컴포넌트와는 안 맞는다. bonds/indices/sectors/fx/commodities는 그래서 `st.container(horizontal=True)` 반복 패턴을 유지했다. 순수 네이티브 요소(`st.metric`, `st.dataframe` 등)만 나열할 때만 고려할 것 |
| `chart_container` | `from streamlit_extras.chart_container import chart_container` | `chart_container(data, tabs=(":material/show_chart: Chart", ":material/table: Dataframe", ":material/download: Export"), export_formats=["CSV","Parquet"])` (컨텍스트 매니저, `with` 블록 안에서 직접 차트를 그리면 나머지 탭은 자동 생성) | **적용됨**: `app_pages/home.py`의 캔들스틱 차트를 `with chart_container(df): st.altair_chart(candlestick, ...)`로 감싸서, 기존에 따로 있던 `st.expander("원본 데이터")`를 없애고 Chart/Dataframe/Export 탭 하나로 통합 |
| `mention` | `from streamlit_extras.mention import mention` | `mention(label, url, icon="🔗", write=True) -> str \| None` | 데이터 출처 링크 표시(예: `mention("FinanceDataReader", "https://github.com/FinanceData/FinanceDataReader")`). 지금은 `st.badge`(회색, 클릭 불가)로 출처만 표시 중인데, 클릭 가능한 링크가 필요하면 이걸로 교체 |
| `stoggle` | `from streamlit_extras.stoggle import stoggle` | `stoggle(summary, content)` | 간단 접기/펼치기. `st.expander`로 이미 충분해서 이 프로젝트에서는 우선순위 낮음 |
| `add_vertical_space` | `from streamlit_extras.add_vertical_space import add_vertical_space` | `add_vertical_space(num_lines=1)` | 네이티브 `st.space("small"/"medium"/"large")`로 이미 대체 가능 — **쓰지 말 것** |

### 쓰지 말아야 할 것 (검증 결과 이 프로젝트엔 부적합)

- **`streamlit_extras.stylable_container`** — 라이브러리 자체가 deprecated 표시했고,
  "Use the `key` parameter with `st.container` to target containers with CSS instead"라고
  안내함. 이미 `app.py`에서 `st.container(key=...)` + `st.html(<style>)` 패턴으로 구현되어
  있으니 그대로 유지한다.
- **`streamlit_extras.badges`** — `type`이 `"pypi"`, `"github"`, `"streamlit"`, `"twitter"`,
  `"buymeacoffee"` 중 하나로 고정되어 있어서 "뉴스 출처 배지", "FinanceDataReader 배지"처럼
  임의 텍스트 배지를 만들 수 없다. 네이티브 `st.badge(label, icon=None, color=...)`
  (Streamlit 1.61+)를 대신 쓴다 — 이미 전 페이지에 적용되어 있음.
- **`streamlit_extras.colored_header`** — 라이브러리 자체가 deprecated 표시했고, "Use the
  `divider` parameter in `st.header`, `st.title`, or `st.subheader` instead"라고 안내함.
  `app.py`에서는 `st.header(f"{page.icon} {page.title}", divider="blue")`로 대체 적용함
  (`st.title`에는 `divider` 파라미터가 없어서 `st.header`로 바꿈).

## 체크리스트 (shadcn/extras 컴포넌트 추가할 때)

1. 네이티브 위젯으로 안 되는지 먼저 확인한다(`developing-with-streamlit` 스킬 우선).
2. `python -m pip show streamlit-shadcn-ui streamlit-extras streamlit`로 버전 확인 —
   설치/업그레이드가 Streamlit 버전을 바꿨다면 8개 페이지를 재시작 후 훑어본다.
3. `ui.button`/`ui.tabs`처럼 상태를 갖는 컴포넌트는 페이지 내에서 `key=`를 고유하게 준다
   (멀티페이지 앱이라 사이드바 위젯 `key`와도 겹치지 않게 주의).
4. 브라우저(`http://localhost:8501`)에서 실제 렌더링과 콘솔 에러(`read_console_messages`,
   `onlyErrors: true`)까지 확인한 뒤 완료로 보고한다.
