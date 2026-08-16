"""채권: 미국·한국의 단기·장기 금리를 한눈에 비교한다."""

from datetime import datetime, timedelta

import streamlit_shadcn_ui as ui

import streamlit as st
from utils.charts import sparkline
from utils.data import load_series

BOND_SYMBOLS = {
    "미국 3개월 (단기)": "^IRX",
    "미국 2년 (단기)": "FRED:DGS2",
    "미국 10년 (장기)": "^TNX",
    "미국 30년 (장기)": "^TYX",
    "한국 콜금리 3개월 (단기)": "FRED:IR3TIB01KRM156N",
    "한국 국고채 10년 (장기)": "FRED:IRLTLT01KRM156N",
}

st.caption(
    "단위는 연 수익률(%)입니다. 한국 금리는 월별, 미국 금리는 일별로 갱신됩니다. "
    "최근 6개월 추이입니다."
)
with st.container(horizontal=True):
    st.badge("Yahoo Finance", icon=":material/api:", color="gray")
    st.badge("FRED", icon=":material/api:", color="gray")

start_date = datetime.now() - timedelta(days=180)
CARD_WIDTH = 220

with st.container(horizontal=True):
    for name, symbol in BOND_SYMBOLS.items():
        try:
            data = load_series(symbol, start_date)
        except ValueError as e:
            ui.metric_card(
                name, "N/A", variant="dashboard", key=f"bond_na_{symbol}", width=CARD_WIDTH
            )
            st.error(f"{name}: {e}")
            continue

        last = data["Value"].iloc[-1]
        prev = data["Value"].iloc[-2] if len(data) > 1 else last
        delta = last - prev

        with st.container(width=CARD_WIDTH):
            ui.metric_card(
                name,
                f"{last:.2f}%",
                delta=f"{delta:+.2f}%p",
                variant="dashboard",
                key=f"bond_{symbol}",
                width=CARD_WIDTH,
            )
            st.altair_chart(sparkline(data), width="stretch")
