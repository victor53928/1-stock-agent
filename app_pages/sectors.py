"""섹터별 지수: 한국·미국 대표 섹터 ETF로 업종 흐름을 비교한다."""

from datetime import datetime, timedelta

import streamlit_shadcn_ui as ui

import streamlit as st
from utils.charts import HORIZON_DAYS, period_chart, sparkline
from utils.data import load_series

KR_SECTOR_SYMBOLS = {
    "반도체 (KODEX)": "091160",
    "은행 (KODEX)": "091170",
    "자동차 (KODEX)": "091180",
    "필수소비재 (KODEX)": "266410",
    "헬스케어 (KODEX)": "266420",
    "2차전지산업 (KODEX)": "305720",
    "건설 (KODEX)": "117700",
    "증권 (KODEX)": "102970",
    "화장품 (TIGER)": "228790",
}

US_SECTOR_SYMBOLS = {
    "기술 (XLK)": "XLK",
    "금융 (XLF)": "XLF",
    "에너지 (XLE)": "XLE",
    "헬스케어 (XLV)": "XLV",
    "자유소비재 (XLY)": "XLY",
    "필수소비재 (XLP)": "XLP",
    "산업재 (XLI)": "XLI",
    "소재 (XLB)": "XLB",
    "유틸리티 (XLU)": "XLU",
    "부동산 (XLRE)": "XLRE",
    "커뮤니케이션 (XLC)": "XLC",
}

start_date = datetime.now() - timedelta(days=180)
CARD_WIDTH = 220


@st.dialog("섹터 ETF 상세 시세", width="large")
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


def render_sector_grid(symbols: dict[str, str]) -> None:
    with st.container(horizontal=True):
        for name, symbol in symbols.items():
            try:
                data = load_series(symbol, start_date)
            except ValueError as e:
                ui.metric_card(
                    name,
                    "N/A",
                    variant="dashboard",
                    key=f"sector_na_{symbol}",
                    width=CARD_WIDTH,
                )
                st.error(f"{name}: {e}")
                continue

            last = data["Value"].iloc[-1]
            prev = data["Value"].iloc[-2] if len(data) > 1 else last
            change_pct = (last - prev) / prev * 100 if prev else 0.0

            with st.container(width=CARD_WIDTH):
                ui.metric_card(
                    name,
                    f"{last:,.2f}",
                    delta=f"{change_pct:.2f}%",
                    variant="dashboard",
                    key=f"sector_{symbol}",
                    width=CARD_WIDTH,
                )
                st.altair_chart(sparkline(data), width="stretch")
                if st.button(
                    "상세보기 ↗", key=f"detail_btn_{symbol}", width="stretch"
                ):
                    show_price_detail(name, symbol)


st.caption("업종 대표 ETF 가격 기준, 최근 6개월 추이입니다.")
st.badge("FinanceDataReader", icon=":material/api:", color="gray")

st.subheader("한국 섹터")
render_sector_grid(KR_SECTOR_SYMBOLS)

st.space("medium")

st.subheader("미국 섹터 (S&P 섹터 SPDR ETF)")
render_sector_grid(US_SECTOR_SYMBOLS)
