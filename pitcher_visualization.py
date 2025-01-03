import pandas as pd
import streamlit as st
from plotnine import (
    ggplot, aes, geom_point, scale_fill_manual, labs, coord_cartesian,
    scale_x_continuous, scale_y_continuous, geom_vline, geom_hline,
    theme, element_text, element_blank, theme_void, annotate, lims  
)
import matplotlib.font_manager as fm
import io  


# 폰트 설정
font_path = "fonts/현대하모니 L.ttF"
font_prop = fm.FontProperties(fname=font_path)

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

@st.cache_data
def load_data():
    # 데이터 URL
    data_url1 = "https://github.com/JUNG-PFe/pitcher-visualization/raw/refs/heads/main/24_merged_data_%EC%88%98%EC%A0%95.xlsx"
    data_url2 = "https://github.com/JUNG-PFe/pitcher-visualization/raw/refs/heads/main/23_merged_data_%EC%88%98%EC%A0%95.xlsx"
    
    # 각 데이터를 로드
    df1 = pd.read_excel(data_url1)
    df2 = pd.read_excel(data_url2)
    
    # 날짜 형식 통일
    df1['Date'] = pd.to_datetime(df1['Date'])
    df2['Date'] = pd.to_datetime(df2['Date'])
    
    # 두 데이터를 병합
    combined_df = pd.concat([df1, df2], ignore_index=True)
    return combined_df

# 데이터 로드
df = load_data()

# 앱 제목
st.title("23-24 호크아이 투수 데이터 필터링 및 분석 앱")

# 세션 상태 초기화
if "filter_applied" not in st.session_state:
    st.session_state.filter_applied = False

# 데이터 필터링 섹션
st.subheader("데이터 필터링")

# 날짜 필터
st.subheader("연도 및 달 필터")
unique_years = sorted(df['Date'].dt.year.unique())  # 고유한 연도 추출
selected_year = st.selectbox("연도 선택", unique_years)

unique_months = ["전체"] + list(range(1, 13))  # 월 목록 (1~12월 + "전체")
selected_month = st.selectbox("월 선택", unique_months)

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
    
    if selected_year:
        filtered_df = filtered_df[filtered_df['Date'].dt.year == selected_year]
    if selected_month != "전체":
        filtered_df = filtered_df[filtered_df['Date'].dt.month == selected_month]

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

    # 기본 분석
    if not filtered_df.empty:
        st.subheader("기본 분석 값")
        analysis = filtered_df.groupby('구종').agg(
            투구수=('구종', 'count'),
            투구_비율=('구종', lambda x: round((x.count() / len(filtered_df)) * 100, 1)),
            스트라이크_비율=('심판콜', lambda x: round((x[x != 'B'].count() / x.count()) * 100, 1) if x.count() > 0 else 0),
            구속_평균=('RelSpeed', lambda x: round(x.mean(), 0)),
            구속_최고=('RelSpeed', lambda x: round(x.max(), 0)),
            회전수=('SpinRate', lambda x: round(x.mean(), 0)),
            회전효율=('회전효율', lambda x: round(x.mean(), 0)),
            Tilt=('Tilt', lambda x: x.mode().iloc[0] if not x.mode().empty else None),
            수직무브_평균=('InducedVertBreak', lambda x: round(x.mean(), 1)),
            수평무브_평균=('HorzBreak', lambda x: round(x.mean(), 1)),
            타구속도=('ExitSpeed', lambda x: round(x.mean(), 0)),
            높이=('RelHeight', lambda x: round(x.mean() * 100, 0)),
            사이드=('RelSide', lambda x: round(x.mean() * 100, 0)),
            익스텐션=('Extension', lambda x: round(x.mean() * 100, 0))
        ).reset_index()

        cols_order = list(cols.keys())
        analysis['구종'] = pd.Categorical(analysis['구종'], categories=cols_order, ordered=True)
        analysis = analysis.sort_values('구종')

        column_order = ['구종', '투구수', '투구_비율', '스트라이크_비율', '구속_평균', '구속_최고',
                        '회전수', '회전효율', 'Tilt', '수직무브_평균', '수평무브_평균','타구속도',
                        '높이', '사이드', '익스텐션']
        analysis = analysis[column_order]
        st.dataframe(analysis)

    # 구종별 플레이트 위치 시각화
    st.subheader("구종별 플레이트 위치")
    if not filtered_df.empty:
        unique_kinds = filtered_df['구종'].dropna().unique().tolist()
        valid_colors = {key: cols[key] for key in unique_kinds if key in cols}

        ggpoint = (
            ggplot(filtered_df, aes(x='PlateLocSide*100', y='PlateLocHeight*100'))
            + geom_point(aes(fill='구종'), shape='o', size=5)
            + scale_fill_manual(values=valid_colors)
            + annotate("rect", xmin=-23, xmax=23, ymin=46, ymax=105, alpha=0.2)
            + annotate("segment", x=-23, xend=23, y=85, yend=85, linetype='dashed')
            + annotate("segment", x=-23, xend=23, y=65, yend=65, linetype='dashed')
            + annotate("segment", x=-7.666, xend=-7.666, y=46, yend=105, linetype='dashed')
            + annotate("segment", x=7.666, xend=7.666, y=46, yend=105, linetype='dashed')
            + coord_cartesian(xlim=(-70, 70), ylim=(-10, 150))
            + theme_void()
            + theme(
                text=element_text(family=font_prop.get_name(), size=10),
                axis_title_x=element_blank(),
                axis_text_x=element_blank(),
                axis_ticks_x=element_blank(),
                axis_title_y=element_blank(),
                axis_text_y=element_blank(),
                axis_ticks_y=element_blank(),
                legend_title=element_text(family=font_prop.get_name(), size=10),  # 범례 제목에 폰트 적용
                legend_text=element_text(family=font_prop.get_name(), size=8),    # 범례 텍스트에 폰트 적용
                legend_position="right",  # 범례를 오른쪽에 배치,
                figure_size=(6, 7)
                )
        )
        fig = ggpoint.draw()
        st.pyplot(fig)

    # 구종별 수직/수평 무브먼트
    st.subheader("구종별 수평/수직 무브먼트")
    if not filtered_df.empty:
        unique_kinds = filtered_df['구종'].dropna().unique().tolist()
        ggpoint = (
            ggplot(filtered_df, aes(x='HorzBreak', y='InducedVertBreak', fill='구종'))
            + geom_point(shape='o', size=4)
            + scale_fill_manual(values=cols, breaks=unique_kinds)
            + labs(x='수평 무브먼트 (cm)', y='수직 무브먼트 (cm)')
            + coord_cartesian(xlim=(-70, 70), ylim=(-70, 70))
            + scale_x_continuous(breaks=range(-70, 71, 10))
            + scale_y_continuous(breaks=range(-70, 71, 10))
            + geom_vline(xintercept=0, linetype='dashed', size=1, color='darkgrey')
            + geom_hline(yintercept=0, linetype='dashed', size=1, color='darkgrey')
            + theme(
                text=element_text(family=font_prop.get_name(), size=10),
                axis_title=element_text(family=font_prop.get_name(), size=12),
                axis_text=element_text(family=font_prop.get_name(), size=10),
                legend_title=element_text(family=font_prop.get_name(), size=10),
                legend_text=element_text(family=font_prop.get_name(), size=8),
                panel_grid_minor=element_blank(),
                figure_size=(8, 7.5)
            )
        )
        fig = ggpoint.draw()
        st.pyplot(fig)

    # 데이터 다운로드
    st.subheader("결과 다운로드")
    output = io.BytesIO()

    # 'XlsxWriter'를 사용하여 Excel 파일 생성
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Filtered Data')
        writer.close()  # 'save()' 대신 'close()' 사용

    # 파일 포인터를 처음으로 되돌림
    output.seek(0)

    # Streamlit에서 다운로드 버튼 생성
    st.download_button(
        label="필터링된 데이터 다운로드 (Excel)",
        data=output,
        file_name='filtered_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    if filtered_df.empty:
        st.info("필터를 설정한 후 검색 버튼을 눌러주세요.")