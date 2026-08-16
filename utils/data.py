"""증시 대시보드 공용 데이터 로더."""

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

import FinanceDataReader as fdr
import pandas as pd

import streamlit as st


@st.cache_data(ttl="12h", show_spinner="종목 목록을 불러오는 중...")
def load_listing(market: str) -> pd.DataFrame:
    """시장별 종목 코드/이름 목록을 불러온다."""
    if market == "한국":
        listing = fdr.StockListing("KRX")[["Code", "Name"]].rename(
            columns={"Code": "Symbol"}
        )
    else:
        listing = fdr.StockListing("S&P500")[["Symbol", "Name"]]
    return listing.dropna().reset_index(drop=True)


@st.cache_data(ttl="1h", show_spinner="시세 데이터를 불러오는 중...")
def load_prices(symbol: str, start: datetime) -> pd.DataFrame:
    """종목의 OHLCV 시세를 불러온다."""
    data = fdr.DataReader(symbol, start)
    if data is None or data.empty:
        raise ValueError(f"'{symbol}' 데이터를 찾을 수 없습니다.")
    data.index.name = "Date"
    return data.reset_index()


@st.cache_data(ttl="1h", show_spinner="데이터를 불러오는 중...")
def load_series(symbol: str, start: datetime) -> pd.DataFrame:
    """지수/채권/원자재 등 단일 지표의 Date, Value 시계열을 불러온다."""
    data = fdr.DataReader(symbol, start)
    if data is None or data.empty:
        raise ValueError(f"'{symbol}' 데이터를 찾을 수 없습니다.")
    data.index.name = "Date"
    data = data.reset_index()
    value_col = "Close" if "Close" in data.columns else data.columns[-1]
    return data[["Date", value_col]].rename(columns={value_col: "Value"})


@st.cache_data(ttl="1h", show_spinner="ETF 시가총액을 불러오는 중...")
def load_etf_marcap() -> pd.DataFrame:
    """국내 상장 ETF 전종목의 시가총액(억원)을 불러온다."""
    data = fdr.StockListing("ETF/KR")
    return data[["Symbol", "MarCap"]].set_index("Symbol")


@st.cache_data(ttl="10m", show_spinner="시장 전체 시세를 불러오는 중...")
def load_krx_snapshot() -> pd.DataFrame:
    """KRX 전종목의 당일 시세 스냅샷과 회전율(거래대금/시가총액)을 불러온다."""
    data = fdr.StockListing("KRX")
    data = data[(data["Marcap"] > 0) & (data["Volume"] > 0)].copy()
    data["Turnover"] = data["Amount"] / data["Marcap"] * 100
    return data


@st.cache_data(ttl="30m", show_spinner="주요 뉴스를 불러오는 중...")
def load_news(query: str, hl: str, gl: str, ceid: str, limit: int = 8) -> list[dict]:
    """Google 뉴스 RSS에서 헤드라인을 불러온다."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=10) as response:
        raw = response.read()
    root = ET.fromstring(raw)

    items = []
    for item in root.findall(".//item")[:limit]:
        source_el = item.find("source")
        items.append(
            {
                "title": item.findtext("title") or "",
                "link": item.findtext("link") or "",
                "source": source_el.text if source_el is not None else "",
                "published": item.findtext("pubDate") or "",
            }
        )
    return items
