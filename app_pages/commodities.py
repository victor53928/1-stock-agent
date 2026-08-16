"""원자재 선물 가격을 최대한 폭넓게 비교한다."""

from datetime import datetime, timedelta

import streamlit_shadcn_ui as ui

import streamlit as st
from utils.charts import PERIOD_DAYS, calc_period_changes, period_chart, slice_period
from utils.data import load_series

COMMODITY_SYMBOLS = {
    "금": "GC=F",
    "은": "SI=F",
    "백금": "PL=F",
    "팔라듐": "PA=F",
    "구리": "HG=F",
    "WTI 원유": "CL=F",
    "브렌트유": "BZ=F",
    "천연가스": "NG=F",
    "옥수수": "ZC=F",
    "밀": "ZW=F",
    "대두": "ZS=F",
    "귀리": "ZO=F",
    "커피": "KC=F",
    "설탕": "SB=F",
    "면화": "CT=F",
    "코코아": "CC=F",
    "생우": "LE=F",
    "비육돈": "HE=F",
}

st.caption(
    "주요 원자재 선물 가격(USD)입니다. 6개월/1년/3년 전 대비 등락률과 해당 기간 추이 차트를 함께 표시합니다."
)
st.badge("FinanceDataReader", icon=":material/api:", color="gray")

start_date = datetime.now() - timedelta(days=PERIOD_DAYS["3년"] + 14)

for name, symbol in COMMODITY_SYMBOLS.items():
    try:
        data = load_series(symbol, start_date)
    except ValueError as e:
        st.error(f"{name}: {e}")
        continue

    last = data["Value"].iloc[-1]
    changes = calc_period_changes(data)

    with st.container(border=True, key=f"commodity_card_{symbol}"):
        cols = st.columns(1 + len(PERIOD_DAYS))
        with cols[0]:
            ui.metric_card(
                name,
                f"${last:,.2f}",
                variant="dashboard",
                key=f"commodity_price_{symbol}",
            )
        for col, label in zip(cols[1:], PERIOD_DAYS):
            result = changes[label]
            with col:
                if result is None:
                    ui.metric_card(
                        f"{label}비", "N/A", variant="dashboard", key=f"commodity_{label}_{symbol}"
                    )
                else:
                    pct, ref_price = result
                    ui.metric_card(
                        f"{label}비",
                        f"${ref_price:,.2f}",
                        delta=f"{pct:+.2f}%",
                        variant="dashboard",
                        key=f"commodity_{label}_{symbol}",
                    )

        tabs = st.tabs(list(PERIOD_DAYS.keys()))
        for tab, (label, days) in zip(tabs, PERIOD_DAYS.items()):
            with tab:
                windowed = slice_period(data, days)
                if windowed.empty:
                    st.info("해당 기간 데이터가 없습니다.")
                else:
                    st.altair_chart(period_chart(windowed), width="stretch")
