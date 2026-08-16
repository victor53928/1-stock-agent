"""거래량 급등 종목: 회전율(거래대금/시가총액)이 높은 한국 종목을 하이라이트한다."""

from datetime import datetime, timedelta

import altair as alt

import streamlit as st
from streamlit_extras.dataframe_explorer import dataframe_explorer
from utils.charts import (
    PERIOD_DAYS,
    calc_period_changes,
    period_chart,
    slice_period,
    volume_chart,
)
from utils.data import load_krx_snapshot, load_prices

TOP_N = 20

st.caption(
    "회전율(당일 거래대금 ÷ 시가총액)이 높은 순으로 정렬한 한국(KRX) 종목입니다. "
    "회전율이 높을수록 시가총액 대비 거래가 활발하다는 뜻으로, 거래량 급등의 대용 지표로 사용합니다."
)
st.badge("KRX", icon=":material/api:", color="gray")

try:
    snapshot = load_krx_snapshot()
except Exception as e:
    st.error(f"시장 데이터를 불러오지 못했습니다: {e}")
    st.stop()

top = snapshot.sort_values("Turnover", ascending=False).head(TOP_N).copy()

color = alt.condition("datum.ChagesRatio >= 0", alt.value("#26a69a"), alt.value("#ef5350"))

with st.container(border=True, key="movers_chart_card"):
    st.markdown(f"**회전율 상위 {TOP_N}종목**")
    chart = (
        alt.Chart(top)
        .mark_bar()
        .encode(
            alt.X("Name:N", sort="-y", title=None),
            alt.Y("Turnover:Q", title="회전율(%)"),
            color=color,
            tooltip=[
                alt.Tooltip("Name:N", title="종목"),
                alt.Tooltip("Close:Q", title="현재가", format=","),
                alt.Tooltip("ChagesRatio:Q", title="등락률(%)", format=".2f"),
                alt.Tooltip("Turnover:Q", title="회전율(%)", format=".2f"),
            ],
        )
        .properties(height=360)
    )
    st.altair_chart(chart, width="stretch")

display = top[
    ["Name", "Code", "Close", "ChagesRatio", "Volume", "Amount", "Turnover"]
].rename(
    columns={
        "Name": "종목명",
        "Code": "코드",
        "Close": "현재가",
        "ChagesRatio": "등락률(%)",
        "Volume": "거래량",
        "Amount": "거래대금",
        "Turnover": "회전율(%)",
    }
)

with st.container(border=True, key="movers_table_card"):
    st.markdown("**상세 데이터** (표 위 필터로 종목명·코드·등락률 등을 검색할 수 있습니다)")
    filtered = dataframe_explorer(display, case=False)
    styled = filtered.style.map(
        lambda v: f"color: {'#26a69a' if v >= 0 else '#ef5350'}", subset=["등락률(%)"]
    )
    st.dataframe(
        styled,
        hide_index=True,
        width="stretch",
        column_config={
            "현재가": st.column_config.NumberColumn(format="%,d원"),
            "등락률(%)": st.column_config.NumberColumn(format="%.2f%%"),
            "거래량": st.column_config.NumberColumn(format="%,d"),
            "거래대금": st.column_config.NumberColumn(format="%,d원"),
            "회전율(%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

st.markdown("**종목별 추이** (펼쳐서 6개월/1년/3년 등락률과 차트를 확인하세요)")

three_years_ago = datetime.now() - timedelta(days=PERIOD_DAYS["3년"] + 14)

for _, row in filtered.iterrows():
    name, code = row["종목명"], row["코드"]
    with st.expander(f"{name} ({code})"):
        try:
            hist = load_prices(code, three_years_ago)
        except ValueError as e:
            st.error(f"{name}: {e}")
            continue

        hist = hist[["Date", "Close", "Volume"]].rename(columns={"Close": "Value"})
        changes = calc_period_changes(hist)

        cols = st.columns(len(PERIOD_DAYS))
        for col, label in zip(cols, PERIOD_DAYS):
            result = changes[label]
            with col:
                if result is None:
                    st.metric(f"{label}비", "N/A")
                else:
                    pct, ref_price = result
                    st.metric(f"{label}비", f"{ref_price:,.0f}원", delta=f"{pct:+.2f}%")

        tabs = st.tabs(list(PERIOD_DAYS.keys()))
        for tab, (label, days) in zip(tabs, PERIOD_DAYS.items()):
            with tab:
                windowed = slice_period(hist, days)
                if windowed.empty:
                    st.info("해당 기간 데이터가 없습니다.")
                else:
                    st.altair_chart(period_chart(windowed), width="stretch")
                    st.altair_chart(volume_chart(windowed), width="stretch")
