"""국가별 주요 증시 지수를 비교한다."""

from datetime import datetime, timedelta

import streamlit_shadcn_ui as ui

import streamlit as st
from utils.charts import HORIZON_DAYS, period_chart, sparkline
from utils.data import load_series

INDEX_SYMBOLS = {
    "한국 코스피": "KS11",
    "한국 코스닥": "KQ11",
    "미국 다우존스": "DJI",
    "미국 나스닥": "IXIC",
    "미국 S&P 500": "US500",
    "미국 러셀2000": "RUT",
    "미국 필라델피아반도체": "^SOX",
    "일본 니케이225": "N225",
    "홍콩 항셍": "HSI",
    "중국 상해종합": "SSEC",
    "영국 FTSE100": "FTSE",
    "프랑스 CAC40": "FCHI",
    "독일 DAX": "GDAXI",
    "인도 SENSEX": "^BSESN",
    "대만 가권지수": "^TWII",
    "유럽 유로스톡스50": "^STOXX50E",
}

st.caption("국가별 대표 증시 지수의 최근 6개월 추이입니다.")
st.badge("FinanceDataReader", icon=":material/api:", color="gray")

start_date = datetime.now() - timedelta(days=180)
CARD_WIDTH = 220


@st.dialog("지수 상세 시세", width="large")
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


with st.container(horizontal=True):
    for name, symbol in INDEX_SYMBOLS.items():
        try:
            data = load_series(symbol, start_date)
        except ValueError as e:
            ui.metric_card(
                name, "N/A", variant="dashboard", key=f"index_na_{symbol}", width=CARD_WIDTH
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
                key=f"index_{symbol}",
                width=CARD_WIDTH,
            )
            st.altair_chart(sparkline(data), width="stretch")
            if st.button(
                "상세보기 ↗", key=f"detail_btn_{symbol}", width="stretch"
            ):
                show_price_detail(name, symbol)
