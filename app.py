"""한국/미국 증시 대시보드 진입점: 개별종목, 채권, 국가별 지수, 원자재 페이지를 연결한다."""

import streamlit as st

st.set_page_config(
    page_title="증시 대시보드",
    page_icon=":material/candlestick_chart:",
    layout="wide",
)

page = st.navigation(
    [
        st.Page(
            "app_pages/home.py", title="개별종목", icon=":material/candlestick_chart:"
        ),
        st.Page("app_pages/bonds.py", title="채권", icon=":material/account_balance:"),
        st.Page("app_pages/indices.py", title="국가별 지수", icon=":material/public:"),
        st.Page("app_pages/sectors.py", title="섹터별 지수", icon=":material/category:"),
        st.Page("app_pages/etf.py", title="테마 ETF", icon=":material/pie_chart:"),
        st.Page("app_pages/fx.py", title="환율", icon=":material/currency_exchange:"),
        st.Page(
            "app_pages/commodities.py", title="원자재", icon=":material/propane_tank:"
        ),
        st.Page(
            "app_pages/movers.py", title="거래량 급등", icon=":material/local_fire_department:"
        ),
        st.Page("app_pages/news.py", title="주요뉴스", icon=":material/newspaper:"),
    ]
)

CARD_SELECTORS = [
    ".st-key-index_chart_card",
    ".st-key-volume_chart_card",
    ".st-key-movers_chart_card",
    ".st-key-movers_table_card",
]

base_rule = ", ".join(CARD_SELECTORS)
hover_rule = ", ".join(f"{s}:hover" for s in CARD_SELECTORS)

st.html(f"""
<style>
{base_rule} {{
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
    transition: box-shadow 0.15s ease, transform 0.15s ease;
}}
{hover_rule} {{
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.22);
    transform: translateY(-2px);
}}
</style>
""")

st.header(f"{page.icon} {page.title}", divider="blue")

page.run()
