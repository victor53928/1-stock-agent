"""주요뉴스: 한국·미국 증시 관련 최신 헤드라인."""

from email.utils import parsedate_to_datetime

import streamlit as st
from utils.data import load_news

NEWS_SOURCES = {
    "한국 증시": {"query": "코스피 증시", "hl": "ko", "gl": "KR", "ceid": "KR:ko"},
    "미국 증시": {
        "query": "S&P 500 stock market",
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    },
}


def fmt_published(raw: str) -> str:
    try:
        return parsedate_to_datetime(raw).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        return raw


st.caption("Google 뉴스 헤드라인을 기준으로 30분마다 갱신됩니다.")
st.badge("Google 뉴스", icon=":material/api:", color="gray")

tabs = st.tabs(list(NEWS_SOURCES.keys()))

for tab, (label, params) in zip(tabs, NEWS_SOURCES.items()):
    with tab:
        try:
            articles = load_news(
                params["query"], params["hl"], params["gl"], params["ceid"]
            )
        except Exception as e:
            st.error(f"뉴스를 불러오지 못했습니다: {e}")
            continue

        if not articles:
            st.info("표시할 뉴스가 없습니다.", icon=":material/info:")
            continue

        for article in articles:
            with st.container(border=True):
                st.markdown(f"**[{article['title']}]({article['link']})**")
                with st.container(horizontal=True, gap="small"):
                    if article["source"]:
                        st.badge(article["source"], color="blue")
                    st.caption(fmt_published(article["published"]))
