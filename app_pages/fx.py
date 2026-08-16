"""환율 정보: 원화 및 주요 통화 간 환율."""

from datetime import datetime, timedelta

import streamlit_shadcn_ui as ui

import streamlit as st
from utils.charts import HORIZON_DAYS, period_chart, sparkline
from utils.data import load_series

FX_SYMBOLS = {
    "달러/원 (USD/KRW)": ("USD/KRW", 1, "원"),
    "엔/원 (100엔 기준)": ("JPY/KRW", 100, "원"),
    "유로/원 (EUR/KRW)": ("EUR/KRW", 1, "원"),
    "위안/원 (CNY/KRW)": ("CNY/KRW", 1, "원"),
    "달러/엔 (USD/JPY)": ("USD/JPY", 1, "엔"),
    "달러/유로 (USD/EUR)": ("USD/EUR", 1, "유로"),
    "달러/위안 (USD/CNY)": ("USD/CNY", 1, "위안"),
    "달러/루블 (USD/RUB)": ("USD/RUB", 1, "루블"),
}

st.caption("주요 통화 간 환율의 최근 6개월 추이입니다.")
st.badge("FinanceDataReader", icon=":material/api:", color="gray")

start_date = datetime.now() - timedelta(days=180)
CARD_WIDTH = 220


@st.dialog("환율 상세 시세", width="large")
def show_price_detail(name: str, symbol: str, multiplier: float, unit: str) -> None:
    st.subheader(name)
    horizon = st.pills(
        "조회 기간",
        options=list(HORIZON_DAYS.keys()),
        default="6개월",
        key=f"detail_horizon_{symbol}_{unit}",
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

    data = data.assign(Value=data["Value"] * multiplier)
    st.altair_chart(period_chart(data), width="stretch")


with st.container(horizontal=True):
    for name, (symbol, multiplier, unit) in FX_SYMBOLS.items():
        try:
            data = load_series(symbol, start_date)
        except ValueError as e:
            ui.metric_card(
                name, "N/A", variant="dashboard", key=f"fx_na_{symbol}", width=CARD_WIDTH
            )
            st.error(f"{name}: {e}")
            continue

        data = data.assign(Value=data["Value"] * multiplier)
        values = data["Value"]
        last = values.iloc[-1]
        prev = values.iloc[-2] if len(values) > 1 else last
        change_pct = (last - prev) / prev * 100 if prev else 0.0

        with st.container(width=CARD_WIDTH):
            ui.metric_card(
                name,
                f"{last:,.2f}{unit}",
                delta=f"{change_pct:.2f}%",
                variant="dashboard",
                key=f"fx_{symbol}_{unit}",
                width=CARD_WIDTH,
            )
            st.altair_chart(sparkline(data), width="stretch")
            if st.button(
                "상세보기 ↗", key=f"detail_btn_{symbol}_{unit}", width="stretch"
            ):
                show_price_detail(name, symbol, multiplier, unit)
