```python
# main.py — 연평균기온에 직선을 맞추고 예측한다
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"

st.set_page_config(page_title="기온 예측기", page_icon="🌡️", layout="wide")
st.title("🌡️ 기온 예측기")


@st.cache_data
def load_yearly():
    df = pd.read_csv(DATA_URL, encoding="utf-8")
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")
    df = df.dropna(subset=["날짜", "평균기온"])

    df["연도"] = df["날짜"].dt.year
    df = df[df["연도"] <= 2025]

    grouped = (
        df.groupby("연도")["평균기온"]
        .agg(["mean", "count"])
        .reset_index()
    )

    # 관측일이 300일 이상인 연도만 사용
    valid = grouped["count"] >= 300

    return grouped[valid].rename(
        columns={"mean": "연평균기온"}
    )


yearly = load_yearly()

if len(yearly) < 2:
    st.error("회귀 분석에 필요한 데이터가 부족합니다.")
    st.stop()

# 전체 기간의 회귀 직선
a, b = np.polyfit(
    yearly["연도"],
    yearly["연평균기온"],
    1
)

# 기울기를 100년당 기온 변화량으로 환산
rise_all = a * 100

# 최근 20년 데이터
end_year = int(yearly["연도"].max())
start_recent = end_year - 19

recent = yearly[
    yearly["연도"] >= start_recent
]

if len(recent) >= 2:
    a_recent, b_recent = np.polyfit(
        recent["연도"],
        recent["연평균기온"],
        1
    )
    rise_recent = a_recent * 100
else:
    rise_recent = np.nan

# 기울기 비교를 화면 상단에 나란히 표시
st.header("100년에 기온이 얼마나 오를까?")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="전체 기간의 기온 변화",
        value=f"{rise_all:+.2f}℃ / 100년"
    )
    st.caption(
        f"{int(yearly['연도'].min())}~{end_year}년"
        f" · {len(yearly)}개 연도"
    )

with col2:
    if np.isfinite(rise_recent):
        st.metric(
            label="최근 20년의 기온 변화",
            value=f"{rise_recent:+.2f}℃ / 100년"
        )
        st.caption(
            f"{int(recent['연도'].min())}~"
            f"{int(recent['연도'].max())}년"
            f" · {len(recent)}개 연도"
        )
    else:
        st.metric("최근 20년의 기온 변화", "계산 불가")

# 두 기울기의 차이 설명
if np.isfinite(rise_recent):
    difference = rise_recent - rise_all

    if difference > 0:
        st.info(
            f"최근 20년의 기울기가 전체 기간보다 "
            f"100년당 {difference:.2f}℃ 더 큽니다."
        )
    elif difference < 0:
        st.info(
            f"최근 20년의 기울기가 전체 기간보다 "
            f"100년당 {abs(difference):.2f}℃ 더 작습니다."
        )
    else:
        st.info("두 기간의 기울기가 같습니다.")

# 전체 기간과 최근 20년의 회귀 직선을 비교
fig = px.scatter(
    yearly,
    x="연도",
    y="연평균기온",
    opacity=0.6,
    title="연도별 평균기온과 회귀 직선"
)

fig.add_scatter(
    x=yearly["연도"],
    y=a * yearly["연도"] + b,
    mode="lines",
    name="전체 기간 회귀 직선"
)

if len(recent) >= 2:
    recent_line_x = np.arange(
        int(recent["연도"].min()),
        int(recent["연도"].max()) + 1
    )

    recent_line_y = (
        a_recent * recent_line_x + b_recent
    )

    fig.add_scatter(
        x=recent_line_x,
        y=recent_line_y,
        mode="lines",
        name="최근 20년 회귀 직선",
        line=dict(dash="dash")
    )

fig.update_layout(
    xaxis_title="연도",
    yaxis_title="연평균기온 (℃)"
)

st.plotly_chart(fig, use_container_width=True)

# 분석에 사용한 기간과 상관계수
st.caption(
    f"직선을 만든 해: {len(yearly)}개 "
    f"({int(yearly['연도'].min())}~{end_year}년)"
)

correlation = yearly["연도"].corr(
    yearly["연평균기온"]
)

st.metric(
    "연도와 연평균기온의 상관계수",
    f"{correlation:.3f}"
)

# 연도별 예상 기온
year = st.slider(
    "예상 기온을 확인할 연도",
    min_value=1900,
    max_value=2100,
    value=2045
)

predicted_temp = a * year + b

st.metric(
    f"{year}년 예상 연평균기온",
    f"{predicted_temp:.1f}℃"
)

if year < yearly["연도"].min() or year > yearly["연도"].max():
    st.info(
        "학습 범위 밖의 외삽값입니다. "
        "실제 미래 기온을 보장하지 않습니다."
    )

st.caption(
    "100년당 기온 변화량은 회귀 직선의 기울기에 "
    "100을 곱해 계산한 통계적 추세입니다."
)
```
