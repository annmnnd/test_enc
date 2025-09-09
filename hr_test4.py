
# hr_kpi_app.py
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# ─────────────────────────────────────────────
# 0) 기본 설정 (페이지/폰트/스타일)
# ─────────────────────────────────────────────
st.set_page_config(page_title="퇴직율 KPI 시각화", layout="centered")
sns.set(style="whitegrid")

# 한글 폰트 (윈도우: 맑은 고딕). 그래프에서 한글이 □로 깨질 때 사용.
try:
    plt.rcParams['font.family'] = "Malgun Gothic"
    plt.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지
except Exception:
    pass

st.title("퇴직율 KPI 대시보드")
st.caption("막대그래프 / 박스플롯 / 히트맵")

# ─────────────────────────────────────────────
# 1) 데이터 로드
# ─────────────────────────────────────────────
@st.cache_data
def load_df(file) -> pd.DataFrame:
    if file is None:
        # 기본 경로 (원하면 파일명 바꿔도 됨)
        return pd.read_csv("HR Data.csv", encoding="utf-8")
    return pd.read_csv(file, encoding="utf-8")

up = st.file_uploader("HR CSV 업로드 (.csv)", type=["csv"])
try:
    df = load_df(up)
except Exception as e:
    st.error(f"데이터를 불러오지 못했어요: {e}")
    st.stop()

# ─────────────────────────────────────────────
# 2) 전처리: '퇴직' 숫자열 만들기
#    - '퇴직여부'(Yes/No) 있으면 1/0으로 매핑
# ─────────────────────────────────────────────
if "퇴직" not in df.columns:
    if "퇴직여부" in df.columns:
        df["퇴직"] = df["퇴직여부"].map({"Yes": 1, "No": 0})
    else:
        st.error("'퇴직' 또는 '퇴직여부' 열이 필요합니다.")
        st.stop()

# 숫자형 강제
df["퇴직"] = pd.to_numeric(df["퇴직"], errors="coerce")

# 사이드바 옵션
with st.sidebar:
    show_heat = st.checkbox("히트맵(상관관계) 보기", value=True)

# ─────────────────────────────────────────────
# 3) KPI #1: 업무환경만족도 → 퇴직율 (막대그래프)
# ─────────────────────────────────────────────
st.subheader("😀 KPI #1 — 업무환경만족도 대비 퇴직율 (막대그래프)")

if "업무환경만족도" in df.columns:
    df["업무환경만족도"] = pd.to_numeric(df["업무환경만족도"], errors="coerce")
    d1 = df[["업무환경만족도", "퇴직"]].dropna()

    if d1.empty:
        st.warning("업무환경만족도/퇴직 데이터가 비어 있습니다.")
    else:
        g1 = (
            d1.groupby("업무환경만족도")["퇴직"]
              .mean()
              .reset_index()
              .rename(columns={"퇴직": "rate"})
              .sort_values("업무환경만족도")
        )
        g1["pct"] = (g1["rate"] * 100).round(1)

        fig1, ax1 = plt.subplots(figsize=(7.5, 3.8))
        sns.barplot(data=g1, x="업무환경만족도", y="pct", ax=ax1)
        ax1.set_xlabel("업무환경만족도")
        ax1.set_ylabel("퇴직율(%)")
        ax1.set_title("만족도별 퇴직율(%)")
        # 막대 라벨
        for p in ax1.patches:
            height = p.get_height()
            ax1.annotate(f"{height:.1f}%", (p.get_x() + p.get_width()/2, height),
                         ha='center', va='bottom', fontsize=9, xytext=(0, 2), textcoords='offset points')
        st.pyplot(fig1, clear_figure=True)
else:
    st.info("컬럼 '업무환경만족도'가 없습니다.")

# ─────────────────────────────────────────────
# 4) KPI #2: 근속연수 → 퇴직 (박스플롯)
#     - x축: 퇴직(0=재직, 1=퇴직)
#     - y축: 근속연수
# ─────────────────────────────────────────────
st.subheader("📈 KPI #2 — 근속연수 분포 (퇴직 vs 재직, 박스플롯)")

if "근속연수" in df.columns:
    df["근속연수"] = pd.to_numeric(df["근속연수"], errors="coerce")
    d2 = df[["근속연수", "퇴직"]].dropna()

    if d2.empty:
        st.warning("근속연수/퇴직 데이터가 비어 있습니다.")
    else:
        fig2, ax2 = plt.subplots(figsize=(7.5, 3.8))
        sns.boxplot(data=d2, x="퇴직", y="근속연수", ax=ax2)
        ax2.set_xlabel("퇴직(0=재직, 1=퇴직)")
        ax2.set_ylabel("근속연수(년)")
        ax2.set_title("퇴직여부별 근속연수 분포 (Boxplot)")
        st.pyplot(fig2, clear_figure=True)
else:
    st.info("컬럼 '근속연수'가 없습니다.")

# ─────────────────────────────────────────────
# 5) KPI #3: 전공 → 퇴직율 (가로 막대그래프, 상위 N개)
# ─────────────────────────────────────────────
st.subheader("🎓 KPI #3 — 전공별 퇴직율 (가로 막대그래프)")

if "전공" in df.columns:
    d3 = df[["전공", "퇴직"]].dropna()
    if d3.empty:
        st.warning("전공/퇴직 데이터가 비어 있습니다.")
    else:
        g3 = (
            d3.groupby("전공")["퇴직"]
              .mean()
              .reset_index()
              .rename(columns={"퇴직": "rate"})
        )
        g3["pct"] = (g3["rate"] * 100).round(1)
        g3 = g3.sort_values("pct", ascending=False).head(20)

        fig3, ax3 = plt.subplots(figsize=(8.5, max(3.5, 0.35*len(g3))))
        sns.barplot(data=g3, y="전공", x="pct", ax=ax3)
        ax3.set_xlabel("퇴직율(%)")
        ax3.set_ylabel("전공")
        ax3.set_title(f"전공별 퇴직율 상위 {len(g3)}개")
        # 라벨
        for p in ax3.patches:
            width = p.get_width()
            y = p.get_y() + p.get_height()/2
            ax3.annotate(f"{width:.1f}%", (width, y),
                         ha='left', va='center', fontsize=9, xytext=(3, 0), textcoords='offset points')
        st.pyplot(fig3, clear_figure=True)
else:
    st.info("컬럼 '전공'이 없습니다.")

# ─────────────────────────────────────────────
# 6) (선택) 히트맵: 수치형 변수 ↔ 퇴직 상관관계
# ─────────────────────────────────────────────
if show_heat:
    st.subheader("🧪 상관관계 히트맵 — 수치형 변수 vs 퇴직")
    # 수치형만 추출
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # 너무 많으면 핵심 후보만 남기기 (있을 때만)
    prefer = ["퇴직", "업무환경만족도", "근속연수", "급여증가분백분율", "스톡옵션정도", "집과의거리", "현재역할년수", "마지막승진년수"]
    cols = [c for c in prefer if c in num_cols]
    if len(cols) < 2:
        cols = num_cols[:8]  # 최소 구성
    use = df[cols].dropna()
    if use.empty:
        st.info("히트맵을 그릴 수치형 데이터가 부족합니다.")
    else:
        corr = use.corr(numeric_only=True)
        fig4, ax4 = plt.subplots(figsize=(1.2*len(cols), 0.9*len(cols)))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax4)
        ax4.set_title("상관관계 히트맵 (수치형 변수)")
        st.pyplot(fig4, clear_figure=True)


