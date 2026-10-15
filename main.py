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

x = yearly["연도"].to_numpy(dtype=float)
y = yearly["연평균기온"].to_numpy(dtype=float)
slope, intercept = np.polyfit(x, y, 1)
correlation = float(np.corrcoef(x, y)[0, 1])
start_year = int(yearly["연도"].min())
end_year = int(yearly["연도"].max())
predicted_line = slope * x + intercept

c1, c2, c3 = st.columns(3)
c1.metric("회귀에 사용한 연도 수", f"{len(yearly):,}년")
c2.metric("시작 연도", f"{start_year}년")
c3.metric("끝 연도", f"{end_year}년")

st.markdown("### 연도별 평균기온과 회귀 직선")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=yearly["연도"], y=yearly["연평균기온"],
    mode="markers", name="연평균기온",
    customdata=yearly[["관측일수"]].to_numpy(),
    hovertemplate="연도: %{x}년<br>연평균기온: %{y:.2f}℃<br>관측일수: %{customdata[0]}일<extra></extra>"
))
fig.add_trace(go.Scatter(
    x=yearly["연도"], y=predicted_line,
    mode="lines", name="선형 회귀 직선",
    hovertemplate="연도: %{x}년<br>회귀 추정값: %{y:.2f}℃<extra></extra>"
))
fig.update_layout(
    xaxis_title="연도", yaxis_title="연평균기온 (℃)",
    hovermode="x unified", legend_title_text="구분",
    margin=dict(l=20, r=20, t=30, b=20)
)
st.plotly_chart(fig, use_container_width=True)

st.metric("상관계수 (연도와 연평균기온)", f"{correlation:.3f}")
if correlation > 0:
    st.write("상관계수가 양수이므로, 분석 기간에는 연도가 최근일수록 연평균기온이 높아지는 경향이 나타납니다.")
elif correlation < 0:
    st.write("상관계수가 음수이므로, 분석 기간에는 연도가 최근일수록 연평균기온이 낮아지는 경향이 나타납니다.")
else:
    st.write("상관계수가 0에 가까워 연도와 연평균기온 사이의 선형 관계가 약합니다.")

st.markdown("### 예상 기온 확인")
selected_year = st.slider("예상 기온을 확인할 연도", min_value=1900, max_value=2100, value=2026, step=1)
estimated_temp = slope * selected_year + intercept
st.markdown(
    f"<div style='text-align:center;padding:1.2rem;border-radius:0.8rem;background-color:rgba(128,128,128,0.10);'>"
    f"<div style='font-size:1.1rem'>{selected_year}년 예상 연평균기온</div>"
    f"<div style='font-size:3.2rem;font-weight:700'>{estimated_temp:.2f}℃</div>"
    f"</div>",
    unsafe_allow_html=True
)

st.warning("이 값은 과거 연평균기온의 선형 추세를 연장한 통계적 추정치입니다. 실제 미래 기온을 정확히 예측하는 값은 아니며, 기후 변화의 복잡한 요인을 반영하지 않습니다.")
with st.expander("분석에 사용한 연도별 데이터 보기"):
    st.dataframe(yearly.rename(columns={"연도": "연도", "연평균기온": "연평균기온(℃)", "관측일수": "관측일수"}), use_container_width=True)
