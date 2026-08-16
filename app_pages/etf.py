"""테마 ETF: 섹터별 대표 ETF와 엔터테인먼트(K-POP·콘텐츠) ETF 시세·시가총액을 비교한다."""

from datetime import datetime, timedelta

import streamlit_shadcn_ui as ui

import streamlit as st
from utils.charts import HORIZON_DAYS, period_chart, sparkline
from utils.data import load_etf_marcap, load_series

SECTOR_ETF_GROUPS = {
    "반도체": {
        "반도체 (KODEX)": "091160",
        "반도체TOP10 (TIGER)": "396500",
        "K-반도체 (HANARO Fn)": "395270",
    },
    "2차전지": {
        "2차전지TOP10 (TIGER)": "364980",
        "2차전지TOP10 (RISE)": "465330",
    },
    "IT/테크": {
        "IT (KODEX)": "266370",
        "200 IT (TIGER)": "139260",
        "메타버스 (RISE)": "401170",
    },
    "금융": {
        "은행 (KODEX)": "091170",
        "은행 (TIGER)": "091220",
    },
    "소비재/뷰티": {
        "경기소비재 (KODEX)": "266390",
        "K-뷰티 (HANARO)": "479850",
    },
    "에너지/화학": {
        "200 에너지화학 (TIGER)": "139250",
    },
    "채권": {
        "종합채권AA- (KODEX)": "273130",
        "국고채10년 (KIWOOM)": "148070",
    },
    "원자재/금": {
        "KRX금현물 (ACE)": "411060",
        "구리선물H (KODEX)": "138910",
    },
}

ENT_ETF_SYMBOLS = {
    "미디어컨텐츠 (TIGER)": "228810",
    "엔터테인먼트 (RISE)": "388280",
    "K콘텐츠 (KODEX)": "266360",
    "K-POP&미디어 (HANARO Fn)": "395290",
    "KPOP포커스 (ACE)": "475050",
}

start_date = datetime.now() - timedelta(days=180)
CARD_WIDTH = 220


@st.dialog("ETF 상세 시세", width="large")
def show_price_detail(name: str, symbol: str) -> None:
    st.subheader(name)
    horizon = st.pills(
        "조회 기간",
        options=list(HORIZON_DAYS.keys()),
        default="6개월",
        key=f"detail_horizon_{symbol}",
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


def render_etf_grid(symbols: dict[str, str]) -> None:
    marcap = load_etf_marcap()

    with st.container(horizontal=True):
        for name, symbol in symbols.items():
            try:
                data = load_series(symbol, start_date)
            except ValueError as e:
                ui.metric_card(
                    name,
                    "N/A",
                    variant="dashboard",
                    key=f"etf_na_{symbol}",
                    width=CARD_WIDTH,
                )
                st.error(f"{name}: {e}")
                continue

            last = data["Value"].iloc[-1]
            prev = data["Value"].iloc[-2] if len(data) > 1 else last
            change_pct = (last - prev) / prev * 100 if prev else 0.0

            if symbol in marcap.index:
                description = f"시가총액 {marcap.loc[symbol, 'MarCap']:,.0f}억원"
            else:
                description = "시가총액 N/A"

            with st.container(width=CARD_WIDTH):
                ui.metric_card(
                    name,
                    f"{last:,.2f}",
                    description=description,
                    delta=f"{change_pct:.2f}%",
                    variant="dashboard",
                    key=f"etf_{symbol}",
                    width=CARD_WIDTH,
                )
                st.altair_chart(sparkline(data), width="stretch")
                if st.button(
                    "상세보기 ↗",
                    key=f"detail_btn_{symbol}",
                    width="stretch",
                ):
                    show_price_detail(name, symbol)


st.caption("섹터·테마 대표 ETF 가격 기준, 최근 6개월 추이입니다.")
st.badge("FinanceDataReader", icon=":material/api:", color="gray")

for section, symbols in SECTOR_ETF_GROUPS.items():
    st.subheader(section)
    render_etf_grid(symbols)
    st.space("medium")

st.subheader("엔터테인먼트 (K-POP·콘텐츠)")
render_etf_grid(ENT_ETF_SYMBOLS)
