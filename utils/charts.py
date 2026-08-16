"""증시 대시보드 공용 차트 헬퍼."""

import altair as alt
import pandas as pd

UP_COLOR = "#26a69a"
DOWN_COLOR = "#ef5350"

PERIOD_DAYS = {"6개월": 182, "1년": 365, "3년": 365 * 3}

HORIZON_DAYS = {
    "1개월": 30,
    "3개월": 90,
    "6개월": 180,
    "1년": 365,
    "3년": 365 * 3,
    "5년": 365 * 5,
}


def sparkline(data: pd.DataFrame, height: int = 60) -> alt.Chart:
    """Date/Value 시계열로 축·눈금 없는 추이선과 최근값 포인트를 그린다."""
    first, last = data["Value"].iloc[0], data["Value"].iloc[-1]
    color = UP_COLOR if last >= first else DOWN_COLOR

    line = (
        alt.Chart(data)
        .mark_line(strokeWidth=2, color=color)
        .encode(
            alt.X("Date:T", axis=None),
            alt.Y("Value:Q", axis=None, scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip("Date:T", title="날짜"),
                alt.Tooltip("Value:Q", title="값", format=",.2f"),
            ],
        )
    )
    point = (
        alt.Chart(data.tail(1))
        .mark_circle(size=30, color=color)
        .encode(
            alt.X("Date:T", axis=None),
            alt.Y("Value:Q", axis=None, scale=alt.Scale(zero=False)),
        )
    )
    return (line + point).properties(height=height)


def period_chart(data: pd.DataFrame, height: int = 220) -> alt.Chart:
    """Date/Value 시계열 구간을 축과 함께 그린다."""
    first, last = data["Value"].iloc[0], data["Value"].iloc[-1]
    color = UP_COLOR if last >= first else DOWN_COLOR

    return (
        alt.Chart(data)
        .mark_line(strokeWidth=1.5, color=color)
        .encode(
            alt.X("Date:T", title=None),
            alt.Y("Value:Q", title=None, scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip("Date:T", title="날짜"),
                alt.Tooltip("Value:Q", title="값", format=",.2f"),
            ],
        )
        .properties(height=height)
    )


def volume_chart(data: pd.DataFrame, height: int = 120) -> alt.Chart:
    """Date/Volume 시계열을 막대 차트로 그린다."""
    return (
        alt.Chart(data)
        .mark_bar(color="#78909c")
        .encode(
            alt.X("Date:T", title=None),
            alt.Y("Volume:Q", title="거래량"),
            tooltip=[
                alt.Tooltip("Date:T", title="날짜"),
                alt.Tooltip("Volume:Q", title="거래량", format=","),
            ],
        )
        .properties(height=height)
    )


def slice_period(data: pd.DataFrame, days: int) -> pd.DataFrame:
    """전체 시계열에서 최근 N일 구간만 잘라낸다."""
    cutoff = data["Date"].iloc[-1] - pd.Timedelta(days=days)
    return data[data["Date"] >= cutoff]


def calc_period_changes(data: pd.DataFrame) -> dict[str, tuple[float, float] | None]:
    """6개월/1년/3년 전 대비 (등락률(%), 기준가)를 계산한다. 해당 시점 데이터가 없으면 None."""
    last_value = data["Value"].iloc[-1]
    last_date = data["Date"].iloc[-1]

    changes: dict[str, tuple[float, float] | None] = {}
    for label, days in PERIOD_DAYS.items():
        past = data[data["Date"] <= last_date - pd.Timedelta(days=days)]
        if past.empty or not past["Value"].iloc[-1]:
            changes[label] = None
        else:
            past_value = past["Value"].iloc[-1]
            changes[label] = ((last_value - past_value) / past_value * 100, past_value)
    return changes
