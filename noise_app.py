import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import os

# 페이지 설정
st.set_page_config(
    page_title="주변 소음 진동 배출 시설 확인",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS로 친환경 테마 적용 (초록색/파란색)
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #e8f5e9 0%, #e1f5fe 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #e8f5e9 0%, #e1f5fe 100%);
    }
    h1, h2, h3 {
        color: #1b5e20;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    </style>
""", unsafe_allow_html=True)

# 데이터 로드 함수
@st.cache_data
def load_noise_data():
    csv_path = "전국소음진동배출시설표준데이터.csv"
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='cp949')

    # 위도, 경도 컬럼 확인 및 정리
    if '위도' in df.columns and '경도' in df.columns:
        df = df.dropna(subset=['위도', '경도'])
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        df = df.dropna(subset=['위도', '경도'])

    return df

# 주소를 좌표로 변환
def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="noise_app")
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        return None, None
    except GeocoderTimedOut:
        st.error("주소 변환 시간 초과. 다시 시도해주세요.")
        return None, None
    except Exception as e:
        st.error(f"주소 변환 오류: {e}")
        return None, None

# 근처 소음 시설 찾기 (거리 기반)
def find_nearby_facilities(lat, lon, df, radius_km=5):
    from math import radians, cos, sin, asin, sqrt

    def haversine(lat1, lon1, lat2, lon2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km

    df['거리_km'] = df.apply(lambda row: haversine(lat, lon, row['위도'], row['경도']), axis=1)
    nearby = df[df['거리_km'] <= radius_km].sort_values('거리_km')
    return nearby

# UI 구성
st.title("🌍 주변 환경 소음 진동 배출 시설 확인")
st.markdown("*주소 또는 원하는 장소를 검색하여 근처의 소음 배출 시설을 확인하세요*")
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 주소/장소 검색")
    address_input = st.text_input("주소 또는 장소를 입력하세요 (예: 서울시 강남구 테헤란로, 서울역, 명동)", "")

with col2:
    st.subheader("⚙️ 검색 범위")
    radius = st.slider("반경 (km)", min_value=1, max_value=20, value=5)

# 데이터 로드
df = load_noise_data()

# 세션 상태 초기화
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'search_address' not in st.session_state:
    st.session_state.search_address = None

if st.button("🔍 확인하기", use_container_width=True, key="search_btn"):
    if address_input:
        with st.spinner("주소를 검색 중입니다..."):
            lat, lon = get_coordinates(address_input)

            if lat and lon:
                st.success(f"✅ 주소 변환 성공: ({lat:.4f}, {lon:.4f})")

                # 근처 시설 찾기
                nearby_facilities = find_nearby_facilities(lat, lon, df, radius_km=radius)

                # 세션에 결과 저장
                st.session_state.search_results = {
                    'lat': lat,
                    'lon': lon,
                    'nearby_facilities': nearby_facilities,
                    'radius': radius,
                    'address': address_input
                }
                st.rerun()
            else:
                st.error("❌ 주소를 찾을 수 없습니다. 다른 주소를 시도해주세요.")
    else:
        st.warning("⚠️ 주소를 입력해주세요.")

# 저장된 결과 표시 (세션 유지)
if st.session_state.search_results:
    results = st.session_state.search_results
    lat = results['lat']
    lon = results['lon']
    nearby_facilities = results['nearby_facilities']
    radius = results['radius']

    st.subheader(f"🗺️ 지도 (반경 {radius}km)")

    m = folium.Map(
        location=[lat, lon],
        zoom_start=12,
        tiles="CartoDB positron",
        background_color='#e8f5e9'
    )

    # 검색 위치 표시
    folium.Marker(
        location=[lat, lon],
        popup="📍 검색 위치",
        icon=folium.Icon(color='blue', icon='home'),
        tooltip="입력한 주소/장소"
    ).add_to(m)

    # 주변 시설 표시
    for idx, row in nearby_facilities.iterrows():
        folium.CircleMarker(
            location=[row['위도'], row['경도']],
            radius=8,
            popup=f"<b>{row.get('시설명', '시설')}</b><br>거리: {row['거리_km']:.2f}km",
            color='#4CAF50',
            fill=True,
            fillColor='#81C784',
            fillOpacity=0.7,
            weight=2,
            tooltip=f"{row.get('시설명', '시설')} - {row['거리_km']:.2f}km"
        ).add_to(m)

    # 반경 원 그리기
    folium.Circle(
        location=[lat, lon],
        radius=radius * 1000,
        color='#2196F3',
        fill=True,
        fillColor='#64B5F6',
        fillOpacity=0.2,
        weight=2,
        popup=f"검색 반경: {radius}km"
    ).add_to(m)

    st_folium(m, width=1200, height=600)

    # 심각도 평가 (먼저 계산)
    facility_count = len(nearby_facilities)
    if facility_count >= 10:
        severity = "🔴 높음"
        severity_desc = "주변에 많은 소음 배출 시설이 있습니다"
        severity_color = "#d32f2f"
    elif facility_count >= 5:
        severity = "🟡 중간"
        severity_desc = "주변에 소음 배출 시설이 있습니다"
        severity_color = "#f57c00"
    else:
        severity = "🟢 낮음"
        severity_desc = "주변에 소음 배출 시설이 적습니다"
        severity_color = "#388e3c"

    # 결과 요약 표시
    st.markdown("---")

    # 검색한 위치 정보
    st.subheader(f"📍 검색 장소: {address_input}")
    st.caption(f"좌표: ({lat:.4f}, {lon:.4f}) | 검색 반경: {radius}km")

    # 큰 숫자로 시설 개수 표시
    col_metric, col_severity = st.columns([2, 1])
    with col_metric:
        st.metric("🏭 주변 소음 배출 시설 개수", f"{facility_count}개", delta="")
    with col_severity:
        st.markdown(f"<div style='text-align: center; padding: 20px; background-color: {severity_color}20; border-radius: 10px; border: 2px solid {severity_color};'>" +
                   f"<h2 style='color: {severity_color}; margin: 0;'>{severity}</h2>" +
                   f"<p style='color: {severity_color}; margin: 5px 0 0 0;'>{severity_desc}</p>" +
                   f"</div>", unsafe_allow_html=True)

    st.markdown("---")

    if len(nearby_facilities) > 0:
        # 시설 목록
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("#### 🏭 주변 소음 배출 시설 목록")

            display_cols = ['시설명', '시도명', '시군구명', '거리_km']
            display_df = nearby_facilities[display_cols].copy()
            display_df['거리_km'] = display_df['거리_km'].apply(lambda x: f"{x:.2f}km")
            display_df = display_df.rename(columns={'시설명': '시설명', '시도명': '시도', '시군구명': '시군구', '거리_km': '거리'})

            st.dataframe(display_df, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("#### 📈 거리별 분포")

            # 거리별 시설 개수 그래프
            distance_bins = pd.cut(nearby_facilities['거리_km'], bins=5)
            distance_counts = nearby_facilities.groupby(distance_bins).size()

            fig = px.bar(
                x=distance_counts.index.astype(str),
                y=distance_counts.values,
                labels={'x': '거리 (km)', 'y': '시설 개수'},
                color_discrete_sequence=['#4CAF50']
            )
            fig.update_layout(
                showlegend=False,
                height=400,
                xaxis_title="거리 범위",
                yaxis_title="시설 개수",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

        # 상세 정보 박스
        st.markdown(f"<div style='background-color: {severity_color}20; padding: 15px; border-radius: 10px; border-left: 5px solid {severity_color};'>" +
                   f"<h3 style='color: {severity_color};'>{severity}</h3>" +
                   f"<p style='color: #333;'>{severity_desc}</p>" +
                   f"<p style='color: #666; font-size: 14px;'>반경 {radius}km 내에 총 <b>{facility_count}개</b>의 소음 진동 배출 시설이 있습니다.</p>" +
                   f"</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background-color: #c8e6c920; padding: 15px; border-radius: 10px; border-left: 5px solid #388e3c;'>" +
                   f"<h3 style='color: #388e3c;'>✨ 축하합니다!</h3>" +
                   f"<p style='color: #333;'>반경 {radius}km 내에 등록된 소음 배출 시설이 없습니다.</p>" +
                   f"</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
### 📖 사용 가이드
- **주소/장소 입력**: 한글 주소, 영문 주소, 건물명(예: 서울역, 명동), 지역명 모두 가능합니다
- **검색 반경**: 원하는 반경을 선택해서 검색할 수 있습니다
- **지도 클릭**: 지도의 각 시설을 클릭하면 자세한 정보를 볼 수 있습니다
- **그래프**: 거리별로 시설의 분포를 한눈에 확인할 수 있습니다
""")

st.markdown("🌱 친환경적이고 살기 좋은 주거 환경을 위해 소음 정보를 확인하세요!")
