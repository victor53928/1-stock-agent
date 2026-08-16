"""개별종목: 종목 검색, 캔들스틱 차트, 시장 지수 개요."""

from datetime import datetime, timedelta

import altair as alt
import streamlit_shadcn_ui as ui

import streamlit as st
from streamlit_extras.chart_container import chart_container
from utils.charts import HORIZON_DAYS
from utils.data import load_listing, load_prices, load_series

DEFAULT_SYMBOL = {"한국": "005930", "미국": "AAPL"}
INDEX_SYMBOL = {"한국": "KS11", "미국": "US500"}
INDEX_NAME = {"한국": "코스피", "미국": "S&P 500"}

with st.sidebar:
    st.subheader("조회 조건")

    market = st.segmented_control(
        "시장", ["한국", "미국"], default="한국", key="market"
    )

    listing = load_listing(market)
    symbols = listing["Symbol"].tolist()
    name_by_symbol = dict(zip(listing["Symbol"], listing["Name"]))

    default_symbol = DEFAULT_SYMBOL[market]
    default_index = symbols.index(default_symbol) if default_symbol in symbols else 0

    symbol = st.selectbox(
        "종목 검색",
        options=symbols,
        index=default_index,
        format_func=lambda s: f"{s} — {name_by_symbol.get(s, '')}",
        accept_new_options=True,
        placeholder="종목 코드 또는 이름 입력 (예: 005930, AAPL)",
        key=f"symbol_{market}",
    )

    horizon = st.pills(
        "조회 기간",
        options=list(HORIZON_DAYS.keys()),
        default="6개월",
        key="horizon",
    )

st.badge("FinanceDataReader", icon=":material/api:", color="gray")

if horizon is None:
    st.info("조회 기간을 선택하세요.", icon=":material/info:")
    st.stop()

start_date = datetime.now() - timedelta(days=HORIZON_DAYS[horizon])

try:
    index_df = load_series(INDEX_SYMBOL[market], start_date)
except ValueError as e:
    st.error(str(e))
    st.stop()

index_last = index_df["Value"].iloc[-1]
index_prev = index_df["Value"].iloc[-2] if len(index_df) > 1 else index_last
index_change_pct = (index_last - index_prev) / index_prev * 100 if index_prev else 0.0

index_cols = st.columns([2, 1])
with index_cols[0]:
    with st.container(border=True, key="index_chart_card"):
        st.markdown(f"**{INDEX_NAME[market]} 추이 ({horizon})**")
        index_line = (
            alt.Chart(index_df)
            .mark_line()
            .encode(
                alt.X("Date:T", title=None),
                alt.Y("Value:Q", title="지수", scale=alt.Scale(zero=False)),
                tooltip=["Date:T", "Value:Q"],
            )
            .properties(height=200)
        )
        st.altair_chart(index_line, width="stretch")
with index_cols[1]:
    ui.metric_card(
        f"현재 {INDEX_NAME[market]}",
        f"{index_last:,.2f}",
        delta=f"{index_change_pct:.2f}%",
        variant="dashboard",
        key=f"index_metric_{market}",
    )

st.space("medium")

if not symbol:
    st.info("종목을 선택하거나 코드를 입력하세요.", icon=":material/info:")
    st.stop()

try:
    df = load_prices(symbol, start_date)
except ValueError as e:
    st.error(str(e))
    st.stop()

name = name_by_symbol.get(symbol, symbol)
is_krw = market == "한국"

last_close = df["Close"].iloc[-1]
prev_close = df["Close"].iloc[-2] if len(df) > 1 else last_close
change_pct = (last_close - prev_close) / prev_close * 100 if prev_close else 0.0
period_high = df["High"].max()
period_low = df["Low"].min()
last_volume = df["Volume"].iloc[-1]


def fmt_price(value: float) -> str:
    return f"{value:,.0f}원" if is_krw else f"${value:,.2f}"


st.subheader(f"{name} ({symbol})")

with st.container(horizontal=True):
    ui.metric_card(
        "현재가",
        fmt_price(last_close),
        delta=f"{change_pct:.2f}%",
        variant="dashboard",
        key=f"kpi_price_{symbol}",
    )
    ui.metric_card(
        "기간 최고", fmt_price(period_high), variant="dashboard", key=f"kpi_high_{symbol}"
    )
    ui.metric_card(
        "기간 최저", fmt_price(period_low), variant="dashboard", key=f"kpi_low_{symbol}"
    )
    ui.metric_card(
        "거래량", f"{last_volume:,.0f}", variant="dashboard", key=f"kpi_volume_{symbol}"
    )

st.space("medium")

color = alt.condition(
    "datum.Open <= datum.Close", alt.value("#26a69a"), alt.value("#ef5350")
)
base = alt.Chart(df).encode(alt.X("Date:T", title=None), color=color)
candlestick = (
    base.mark_rule().encode(
        alt.Y("Low:Q", title="가격", scale=alt.Scale(zero=False)),
        alt.Y2("High:Q"),
        tooltip=["Date:T", "Open:Q", "High:Q", "Low:Q", "Close:Q"],
    )
    + base.mark_bar().encode(alt.Y("Open:Q"), alt.Y2("Close:Q"))
).properties(height=420)

st.markdown("**가격**")
with chart_container(df):
    st.altair_chart(candlestick, width="stretch")

volume_chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        alt.X("Date:T", title=None),
        alt.Y("Volume:Q", title="거래량"),
        color=color,
        tooltip=["Date:T", "Volume:Q"],
    )
    .properties(height=150)
)

with st.container(border=True, key="volume_chart_card"):
    st.markdown("**거래량**")
    st.altair_chart(volume_chart, width="stretch")
