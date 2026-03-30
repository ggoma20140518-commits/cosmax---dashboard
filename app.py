import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="안정성 테스트 대시보드", layout="wide")
st.title("🧪 화장품 시제품 안정성 테스트 대시보드")

# ── 파일 업로드 ──
uploaded = st.file_uploader("엑셀 파일을 업로드하세요 (.xlsx)", type=["xlsx"])

if uploaded is None:
    st.info("엑셀 파일을 업로드하면 대시보드가 표시됩니다.")
    st.stop()

# ── 데이터 로드 ──
xls = pd.ExcelFile(uploaded)
df_product = pd.read_excel(xls, sheet_name="시제품정보")
df_test = pd.read_excel(xls, sheet_name="안정성테스트결과")

# 시제품정보 병합
df = df_test.merge(df_product, on="시제품코드", how="left")

# ── 사이드바 필터 ──
st.sidebar.header("필터")
sel_product = st.sidebar.multiselect("제품유형", df["제품유형"].unique(), default=df["제품유형"].unique())
sel_condition = st.sidebar.multiselect("테스트조건", df["테스트조건"].unique(), default=df["테스트조건"].unique())
sel_result = st.sidebar.multiselect("판정결과", df["판정결과"].unique(), default=df["판정결과"].unique())

mask = (
    df["제품유형"].isin(sel_product)
    & df["테스트조건"].isin(sel_condition)
    & df["판정결과"].isin(sel_result)
)
df_filtered = df[mask]

# ── KPI 카드 ──
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
col1.metric("총 테스트 건수", f"{len(df_filtered)}건")
col2.metric("적합률", f"{(df_filtered['판정결과'] == '적합').mean() * 100:.1f}%")
col3.metric("평균 pH", f"{df_filtered['pH'].mean():.2f}")
col4.metric("평균 점도(cP)", f"{df_filtered['점도_cP'].mean():,.0f}")

# ── 차트 영역 ──
st.markdown("---")

# Row 1: 판정결과 분포 & 테스트조건별 판정결과
r1c1, r1c2 = st.columns(2)

with r1c1:
    st.subheader("판정결과 분포")
    result_counts = df_filtered["판정결과"].value_counts().reset_index()
    result_counts.columns = ["판정결과", "건수"]
    color_map = {"적합": "#2ecc71", "경미변화": "#f39c12", "재검토": "#e74c3c"}
    fig = px.pie(result_counts, names="판정결과", values="건수", color="판정결과",
                 color_discrete_map=color_map, hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with r1c2:
    st.subheader("테스트조건별 판정결과")
    ct = df_filtered.groupby(["테스트조건", "판정결과"]).size().reset_index(name="건수")
    fig = px.bar(ct, x="테스트조건", y="건수", color="판정결과",
                 color_discrete_map=color_map, barmode="group")
    st.plotly_chart(fig, use_container_width=True)

# Row 2: pH & 점도 분석
r2c1, r2c2 = st.columns(2)

with r2c1:
    st.subheader("보관온도별 pH 분포")
    fig = px.box(df_filtered, x="보관온도", y="pH", color="테스트조건",
                 labels={"보관온도": "보관온도(°C)"})
    st.plotly_chart(fig, use_container_width=True)

with r2c2:
    st.subheader("보관기간별 점도 변화")
    fig = px.scatter(df_filtered, x="보관기간_주", y="점도_cP", color="테스트조건",
                     size="색상변화등급", hover_data=["시제품코드", "판정결과"],
                     labels={"보관기간_주": "보관기간(주)", "점도_cP": "점도(cP)"})
    st.plotly_chart(fig, use_container_width=True)

# Row 3: 제품유형별 분석 & 향/분리 현상
r3c1, r3c2 = st.columns(2)

with r3c1:
    st.subheader("제품유형별 적합률")
    type_stats = df_filtered.groupby("제품유형").apply(
        lambda g: (g["판정결과"] == "적합").mean() * 100
    ).reset_index(name="적합률(%)")
    fig = px.bar(type_stats, x="제품유형", y="적합률(%)", color="적합률(%)",
                 color_continuous_scale="RdYlGn", range_color=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

with r3c2:
    st.subheader("향변화 / 분리현상 발생 비율")
    issue_data = pd.DataFrame({
        "항목": ["향변화", "분리현상"],
        "발생률(%)": [
            (df_filtered["향변화여부"] == "y").mean() * 100,
            (df_filtered["분리현상여부"] == "y").mean() * 100,
        ]
    })
    fig = px.bar(issue_data, x="항목", y="발생률(%)", color="항목",
                 color_discrete_sequence=["#e67e22", "#9b59b6"])
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# Row 4: 담당팀별 업무 횟수
r4c1, r4c2 = st.columns(2)

with r4c1:
    st.subheader("담당팀별 테스트 수행 건수")
    team_counts = df_filtered.groupby("담당팀").size().reset_index(name="건수").sort_values("건수", ascending=True)
    fig = px.bar(team_counts, x="건수", y="담당팀", orientation="h",
                 color="건수", color_continuous_scale="Blues")
    st.plotly_chart(fig, use_container_width=True)

with r4c2:
    st.subheader("담당팀별 판정결과 비교")
    team_result = df_filtered.groupby(["담당팀", "판정결과"]).size().reset_index(name="건수")
    fig = px.bar(team_result, x="담당팀", y="건수", color="판정결과",
                 color_discrete_map=color_map, barmode="stack")
    st.plotly_chart(fig, use_container_width=True)

# ── 색상변화등급 히트맵 ──
st.markdown("---")
st.subheader("보관온도 × 보관기간 색상변화등급 히트맵")
heatmap_data = df_filtered.pivot_table(
    values="색상변화등급", index="보관온도", columns="보관기간_주", aggfunc="mean"
)
fig = px.imshow(heatmap_data, text_auto=".1f", color_continuous_scale="YlOrRd",
                labels={"x": "보관기간(주)", "y": "보관온도(°C)", "color": "색상변화등급"})
st.plotly_chart(fig, use_container_width=True)

# ── 데이터 테이블 ──
st.markdown("---")
st.subheader("원본 데이터")
tab1, tab2 = st.tabs(["안정성테스트결과", "시제품정보"])
with tab1:
    st.dataframe(df_filtered, use_container_width=True)
with tab2:
    st.dataframe(df_product, use_container_width=True)
