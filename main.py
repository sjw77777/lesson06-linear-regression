                       관측일수=("평균기온", "count"),
        )
        .reset_index()
    )
    yearly = yearly[yearly["관측일수"] >= 300].sort_values("연도")
    return yearly


try:
    yearly = load_yearly_data()
except Exception as e:
    st.error("기온 데이터를 불러오지 못했습니다. 인터넷 연결이나 데이터 주소를 확인해 주세요.")
    st.exception(e)
    st.stop()

if len(yearly) < 2:
    st.error("회귀 직선을 만들 수 있는 연도 데이터가 충분하지 않습니다.")
    st.stop()

# 전체 기간의 선형 회귀
x_all = yearly["연도"].to_numpy(dtype=float)
y_all = yearly["연평균기온"].to_numpy(dtype=float)
slope_all, intercept_all = np.polyfit(x_all, y_all, 1)
correlation = float(np.corrcoef(x_all, y_all)[0, 1])
start_year = int(yearly["연도"].min())
end_year = int(yearly["연도"].max())
predicted_all = slope_all * x_all + intercept_all

# 최근 20년: 마지막 관측 연도 기준으로 20년 범위에 포함되는 연도
recent_start = end_year - 19
recent = yearly[yearly["연도"] >= recent_start]
if len(recent) >= 2:
    x_recent = recent["연도"].to_numpy(dtype=float)
    y_recent = recent["연평균기온"].to_numpy(dtype=float)
    slope_recent, intercept_recent = np.polyfit(x_recent, y_recent, 1)
else:
    slope_recent, intercept_recent = np.nan, np.nan

# 연간 기울기(℃/년)를 100년당 변화량(℃/100년)으로 환산
rise_100_all = slope_all * 100
rise_100_recent = slope_recent * 100 if np.isfinite(slope_recent) else np.nan

st.markdown("## 100년에 기온이 얼마나 오를까?")
st.caption("기울기에 100을 곱해 100년당 기온 변화량으로 표시합니다. 양수는 상승, 음수는 하강을 뜻합니다.")
m1, m2 = st.columns(2)
with m1:
    st.metric("전체 기간", f"{rise_100_all:+.2f}℃ / 100년")
    st.caption(f"{start_year}~{end_year}년 · {len(yearly)}개 연도")
with m2:
    if np.isfinite(rise_100_recent):
        st.metric("최근 20년", f"{rise_100_recent:+.2f}℃ / 100년")
        st.caption(f"{int(recent['연도'].min())}~{int(recent['연도'].max())}년 · {len(recent)}개 연도")
    else:
        st.metric("최근 20년", "계산 불가")
        st.caption("회귀 분석에 필요한 연도 데이터가 부족합니다.")

if np.isfinite(rise_100_recent):
    difference = rise_100_recent - rise_100_all
    if difference > 0:
        st.write(f"최근 20년의 기울기가 전체 기간보다 100년당 {difference:.2f}℃ 더 큽니다.")
    elif difference < 0:
        st.write(f"최근 20년의 기울기가 전체 기간보다 100년당 {abs(difference):.2f}℃ 더 작습니다.")
    else:
        st.write("최근 20년과 전체 기간의 기울기가 같습니다.")

c1, c2, c3 = st.columns(3)
c1.metric("회귀에 사용한 연도 수", f"{len(yearly):,}년")
c2.metric("시작 연도", f"{start_year}년")
c3.metric("끝 연도", f"{end_year}년")

st.markdown("### 연도별 평균기온과 회귀 직선")
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=yearly["연도"], y=yearly["연평균기온"],
        mode="markers", name="연평균기온",
        customdata=yearly[["관측일수"]].to_numpy(),
        hovertemplate="연도: %{x}년<br>연평균기온: %{y:.2f}℃<br>관측일수: %{customdata[0]}일<extra></extra>",
    )
)
fig.add_trace(
    go.Scatter(
        x=yearly["연도"], y=predicted_all,
        mode="lines", name="전체 기간 회귀 직선",
        hovertemplate="연도: %{x}년<br>추정값: %{y:.2f}℃<extra></extra>",
    )
)
if len(recent) >= 2:
    recent_line_x = np.arange(int(recent["연도"].min()), int(recent["연도"].max()) + 1)
    recent_line_y = slope_recent * recent_line_x + intercept_recent
    fig.add_trace(
        go.Scatter(
            x=recent_line_x, y=recent_line_y,
            mode="lines", name="최근 20년 회귀 직선",
            line=dict(dash="dash"),
            hovertemplate="연도: %{x}년<br>최근 20년 추정값: %{y:.2f}℃<extra></extra>",
        )
    )
fig.update_layout(
    xaxis_title="연도", yaxis_title="연평균기온 (℃)",
    hovermode="x unified", legend_title_text="구분",
    margin=dict(l=20, r=20, t=30, b=20),
)
st.plotly_chart(fig, use_container_width=True)

st.metric("상관계수 (연도와 연평균기온, 전체 기간)", f"{correlation:.3f}")
if correlation > 0:
    st.write("상관계수가 양수이므로, 전체 분석 기간에는 연도가 최근일수록 연평균기온이 높아지는 선형 경향이 나타납니다.")
elif correlation < 0:
    st.write("상관계수가 음수이므로, 전체 분석 기간에는 연도가 최근일수록 연평균기온이 낮아지는 선형 경향이 나타납니다.")
else:
    st.write("상관계수가 0이므로 전체 기간에서 연도와 연평균기온 사이의 선형 상관관계가 나타나지 않습니다.")

st.markdown("### 예상 기온 확인")
selected_year = st.slider(
    "예상 기온을 확인할 연도",
    min_value=1900, max_value=2100, value=2026, step=1,
)
estimated_temp = slope_all * selected_year + intercept_all
st.markdown(
    f"""
    <div style="text-align:center; padding:1.2rem; border-radius:0.8rem;
                background-color:rgba(128,128,128,0.10);">
        <div style="font-size:1.1rem">{selected_year}년 예상 연평균기온</div>
        <div style="font-size:3.2rem; font-weight:700">{estimated_temp:.2f}℃</div>
    </div>
    """,
    unsafe_allow_html=True,
