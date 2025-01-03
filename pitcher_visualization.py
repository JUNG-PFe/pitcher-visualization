import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from plotnine import (
    ggplot, aes, geom_point, scale_fill_manual, annotate, lims,
    theme_void, theme, element_blank
)
import plotly.express as px
# 데이터 캐싱을 위한 함수
@st.cache_data
def load_data():
    data_url = "https://github.com/JUNG-PFe/pitcher-visualization/raw/refs/heads/main/24_merged_data_%EC%88%98%EC%A0%95.xlsx"
    df = pd.read_excel(data_url)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

# 데이터 로드
df = load_data()

# Streamlit 앱 시작
st.title("투수 데이터 필터링 및 분석 앱")

# 데이터 컬러 설정
cols = {
    "직구": "#4C569B",
    "투심": "#B590C3",
    "커터": "#45B0D8",
    "슬라": "firebrick",
    "스위퍼": "#00FF00",
    "체인": "#FBE25E",
    "포크": "MediumSeaGreen",
    "커브": "orange",
    "너클": "black"
}

# 세션 상태 초기화
if "filter_applied" not in st.session_state:
    st.session_state.filter_applied = False

# 데이터 필터링 섹션
st.subheader("데이터 필터링")

# 날짜 필터
date_range = st.date_input("날짜 범위 선택", [])

# 투수 이름 필터
search_query = st.text_input("투수 이름 검색", "").strip()
if search_query:
    suggestions = [name for name in sorted(df['투수'].unique()) if search_query.lower() in name.lower()]
else:
    suggestions = sorted(df['투수'].unique())

if suggestions:
    pitcher_name = st.selectbox("투수 이름 선택", suggestions)
else:
    pitcher_name = None

# 타자 유형 필터
batter_type = st.selectbox("타자 유형 선택", ["전체", "우타", "좌타"])

# 구종 필터
pitch_type = st.multiselect("구종 선택", df['구종'].unique())

# 주자 상황 필터
runner_status = st.selectbox("주자 상황 선택", ["전체", "주자무", "나머지"])

# 검색 버튼
if st.button("검색 실행"):
    st.session_state.filter_applied = True

# 필터 적용 로직
if st.session_state.filter_applied:
    filtered_df = df.copy()

    # 날짜 필터 적용
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[(filtered_df['Date'] >= pd.Timestamp(start_date)) & (filtered_df['Date'] <= pd.Timestamp(end_date))]

    # 투수 이름 필터 적용
    if pitcher_name:
        filtered_df = filtered_df[filtered_df['투수'] == pitcher_name]

    # 타자 유형 필터 적용
    if batter_type == "우타":
        filtered_df = filtered_df[filtered_df['타자유형'] == "우타"]
    elif batter_type == "좌타":
        filtered_df = filtered_df[filtered_df['타자유형'] == "좌타"]

    # 구종 필터 적용
    if pitch_type:
        filtered_df = filtered_df[filtered_df['구종'].isin(pitch_type)]

    # 주자 상황 필터 적용
    if runner_status == "주자무":
        filtered_df = filtered_df[filtered_df['주자'] == "주자무"]
    elif runner_status == "나머지":
        filtered_df = filtered_df[filtered_df['주자'] != "주자무"]

    # 필터링 결과 출력
    st.write("필터링된 데이터:")
    st.dataframe(filtered_df)

    # 기본 분석
    if not filtered_df.empty:
        st.subheader("기본 분석 값")
        analysis = filtered_df.groupby('구종').agg(
            투구수=('구종', 'count'),
            투구_비율=('구종',  lambda x: round((x.count() / len(filtered_df)) * 100, 1)),
            스트라이크_비율=('심판콜', lambda x: round((x[x != 'B'].count() / x.count()) * 100, 1) if x.count() > 0 else 0),
            구속_평균=('RelSpeed', lambda x: round(x.mean(), 0)),
            구속_최고=('RelSpeed', lambda x: round(x.max(), 0)),
            회전수=('SpinRate', lambda x: round(x.mean(), 0)),
            회전효율=('회전효율', lambda x: round(x.mean(), 0)),
            Tilt=('Tilt', lambda x: x.mode().iloc[0] if not x.mode().empty else None),
            수직무브_평균=('InducedVertBreak', lambda x: round(x.mean(), 1)),
            수평무브_평균=('HorzBreak', lambda x: round(x.mean(), 1)),
            높이=('RelHeight', lambda x: round(x.mean() * 100, 0)),
            사이드=('RelSide', lambda x: round(x.mean() * 100, 0)),
            익스텐션=('Extension', lambda x: round(x.mean() * 100, 0))
        ).reset_index()
        st.dataframe(analysis)

    # 구종별 플레이트 위치 시각화
    st.subheader("구종별 플레이트 위치")
    if not filtered_df.empty:
        ggpoint = (
            ggplot(filtered_df, aes(x='PlateLocSide*100', y='PlateLocHeight*100'))
            + geom_point(aes(fill='구종'), shape='o', size=5)
            + scale_fill_manual(values=cols, breaks=filtered_df['구종'].unique())
            + annotate("rect", xmin=-23, xmax=23, ymin=46, ymax=105, alpha=0.2)
            + annotate("segment", x=-23, xend=23, y=85, yend=85, linetype='dashed')
            + annotate("segment", x=-23, xend=23, y=65, yend=65, linetype='dashed')
            + annotate("segment", x=-7.666, xend=-7.666, y=46, yend=105, linetype='dashed')
            + annotate("segment", x=7.666, xend=7.666, y=46, yend=105, linetype='dashed')
            + lims(x=(-70, 70), y=(-10, 150))
            + theme_void()
            + theme(
                axis_title_x=element_blank(),
                axis_text_x=element_blank(),
                axis_ticks_x=element_blank(),
                axis_title_y=element_blank(),
                axis_text_y=element_blank(),
                axis_ticks_y=element_blank(),
                legend_title=element_blank(),
                legend_position='none',
                figure_size=(4, 5)
            )
        )
        fig = ggpoint.draw()
        st.pyplot(fig)

    # 시각화

    st.subheader("구종별 수평/수직 무브먼트")
    fig = px.scatter(
        filtered_df,
        x="HorzBreak",
        y="InducedVertBreak",
        color="구종",
        hover_data=["투수", "구속"],
        title="구종별 수평/수직 무브먼트",
        labels={"HorzBreak": "수평 무브먼트 (cm)", "InducedVertBreak": "수직 무브먼트 (cm)"}
    )

    fig.update_layout(
        xaxis=dict(range=[-70, 70], linecolor="black", linewidth=2, mirror=True),
        yaxis=dict(range=[-70, 70], linecolor="black", linewidth=2, mirror=True)
    )
    fig.add_shape(type="line", x0=0, y0=-70, x1=0, y1=70, line=dict(color="black", width=2))
    fig.add_shape(type="line", x0=-70, y0=0, x1=70, y1=0, line=dict(color="black", width=2))
    st.plotly_chart(fig)

    # 데이터 다운로드
    st.subheader("결과 다운로드")
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="필터링된 데이터 다운로드 (CSV)",
        data=csv,
        file_name='filtered_data.csv',
        mime='text/csv'
    )
else:
    st.info("필터를 설정한 후 검색 버튼을 눌러주세요.")