import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any

def create_timeline_chart(days: List[Dict[str, Any]]) -> go.Figure:
    """일정 타임라인 차트 생성"""
    
    # 시간대별 데이터 준비
    timeline_data = []
    
    for i, day in enumerate(days):
        date = day.get('date', f'Day {i+1}')
        
        # 오전 (9:00-12:00)
        if day.get('morning'):
            for place in day['morning']:
                timeline_data.append({
                    'date': date,
                    'time': '09:00',
                    'activity': place['name'],
                    'category': place.get('category', 'poi'),
                    'duration': place.get('est_stay_min', 60),
                    'period': '오전'
                })
        
        # 점심 (12:00-13:00)
        if day.get('lunch'):
            timeline_data.append({
                'date': date,
                'time': '12:00',
                'activity': day['lunch'],
                'category': 'meal',
                'duration': 60,
                'period': '점심'
            })
        
        # 오후 (13:00-18:00)
        if day.get('afternoon'):
            for place in day['afternoon']:
                timeline_data.append({
                    'date': date,
                    'time': '13:00',
                    'activity': place['name'],
                    'category': place.get('category', 'poi'),
                    'duration': place.get('est_stay_min', 60),
                    'period': '오후'
                })
        
        # 저녁 (18:00-19:00)
        if day.get('dinner'):
            timeline_data.append({
                'date': date,
                'time': '18:00',
                'activity': day['dinner'],
                'category': 'meal',
                'duration': 60,
                'period': '저녁'
            })
        
        # 밤 (19:00-22:00)
        if day.get('evening'):
            for place in day['evening']:
                timeline_data.append({
                    'date': date,
                    'time': '19:00',
                    'activity': place['name'],
                    'category': place.get('category', 'poi'),
                    'duration': place.get('est_stay_min', 60),
                    'period': '밤'
                })
    
    if not timeline_data:
        return None
    
    # Plotly 차트 생성
    df = pd.DataFrame(timeline_data)
    
    # 카테고리별 색상 매핑
    color_map = {
        'museum': '#1f77b4',
        'landmark': '#ff7f0e',
        'park': '#2ca02c',
        'restaurant': '#d62728',
        'cafe': '#9467bd',
        'shopping': '#8c564b',
        'entertainment': '#e377c2',
        'culture': '#7f7f7f',
        'nature': '#bcbd22',
        'history': '#17becf',
        'art': '#ff9896',
        'architecture': '#98df8a',
        'religion': '#ffbb78',
        'sports': '#f7b6d2',
        'nightlife': '#c5b0d5',
        'meal': '#ff9896',
        'poi': '#aec7e8'
    }
    
    fig = px.timeline(
        df, 
        x_start='time', 
        y='date',
        color='category',
        hover_data=['activity', 'duration', 'period'],
        color_discrete_map=color_map,
        title="🗓️ 여행 일정 타임라인"
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        xaxis_title="시간",
        yaxis_title="날짜"
    )
    
    return fig

def create_category_distribution_chart(days: List[Dict[str, Any]]) -> go.Figure:
    """카테고리별 분포 차트 생성"""
    
    category_counts = {}
    
    for day in days:
        for period in ['morning', 'afternoon', 'evening']:
            if day.get(period):
                for place in day[period]:
                    category = place.get('category', 'poi')
                    category_counts[category] = category_counts.get(category, 0) + 1
    
    if not category_counts:
        return None
    
    # 카테고리명을 한국어로 변환
    category_labels = {
        'museum': '박물관',
        'landmark': '랜드마크',
        'park': '공원',
        'restaurant': '레스토랑',
        'cafe': '카페',
        'shopping': '쇼핑',
        'entertainment': '엔터테인먼트',
        'culture': '문화',
        'nature': '자연',
        'history': '역사',
        'art': '예술',
        'architecture': '건축',
        'religion': '종교',
        'sports': '스포츠',
        'nightlife': '나이트라이프',
        'poi': '기타'
    }
    
    labels = [category_labels.get(cat, cat) for cat in category_counts.keys()]
    values = list(category_counts.values())
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        textinfo='label+percent',
        insidetextorientation='radial'
    )])
    
    fig.update_layout(
        title="📊 방문 장소 카테고리 분포",
        height=400,
        showlegend=True
    )
    
    return fig

def create_daily_activity_chart(days: List[Dict[str, Any]]) -> go.Figure:
    """일별 활동량 차트 생성"""
    
    daily_activities = []
    
    for i, day in enumerate(days):
        date = day.get('date', f'Day {i+1}')
        
        # 하루 총 활동 수 계산
        total_places = (
            len(day.get('morning', [])) +
            len(day.get('afternoon', [])) +
            len(day.get('evening', []))
        )
        
        # 하루 총 체류 시간 계산
        total_time = 0
        for period in ['morning', 'afternoon', 'evening']:
            if day.get(period):
                for place in day[period]:
                    total_time += place.get('est_stay_min', 60)
        
        daily_activities.append({
            'date': date,
            'total_places': total_places,
            'total_time': total_time
        })
    
    if not daily_activities:
        return None
    
    df = pd.DataFrame(daily_activities)
    
    fig = go.Figure()
    
    # 장소 수 차트
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['total_places'],
        name='방문 장소 수',
        marker_color='#1f77b4'
    ))
    
    # 체류 시간 차트 (보조 Y축)
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['total_time'],
        name='총 체류 시간 (분)',
        yaxis='y2',
        line=dict(color='#ff7f0e', width=3)
    ))
    
    fig.update_layout(
        title="📈 일별 활동량",
        xaxis_title="날짜",
        yaxis_title="방문 장소 수",
        yaxis2=dict(
            title="총 체류 시간 (분)",
            overlaying='y',
            side='right'
        ),
        height=400,
        showlegend=True
    )
    
    return fig

def create_transport_summary(days: List[Dict[str, Any]]) -> Dict[str, Any]:
    """교통 정보 요약 생성"""
    
    total_distance = 0
    total_time = 0
    transfer_count = 0
    
    for day in days:
        if day.get('transfers'):
            for transfer in day['transfers']:
                total_distance += transfer.get('distance_km', 0)
                total_time += transfer.get('travel_min', 0)
                transfer_count += 1
    
    return {
        'total_distance': round(total_distance, 1),
        'total_time': total_time,
        'transfer_count': transfer_count,
        'avg_distance': round(total_distance / max(transfer_count, 1), 1),
        'avg_time': round(total_time / max(transfer_count, 1))
    }

def display_itinerary_summary(data: Dict[str, Any]) -> None:
    """여행 일정 요약 표시"""
    
    st.markdown("## 📋 여행 계획 요약")
    
    # 기본 정보
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 목적지", data.get("summary", "").split()[0])
    
    with col2:
        days_count = len(data.get("days", []))
        st.metric("📅 여행 기간", f"{days_count}일")
    
    with col3:
        total_places = sum(
            len(day.get('morning', [])) + 
            len(day.get('afternoon', [])) + 
            len(day.get('evening', []))
            for day in data.get("days", [])
        )
        st.metric("📍 총 방문 장소", f"{total_places}개")
    
    with col4:
        transport_summary = create_transport_summary(data.get("days", []))
        st.metric("🚶 총 이동 거리", f"{transport_summary['total_distance']}km")

def display_visualizations(data: Dict[str, Any]) -> None:
    """시각화 차트들 표시"""
    
    st.markdown("## 📊 여행 계획 시각화")
    
    days = data.get("days", [])
    if not days:
        st.warning("시각화할 일정 데이터가 없습니다.")
        return
    
    # 1. 타임라인 차트
    timeline_fig = create_timeline_chart(days)
    if timeline_fig:
        st.plotly_chart(timeline_fig, use_container_width=True)
    
    # 2. 카테고리 분포 차트
    col1, col2 = st.columns(2)
    
    with col1:
        category_fig = create_category_distribution_chart(days)
        if category_fig:
            st.plotly_chart(category_fig, use_container_width=True)
    
    # 3. 일별 활동량 차트
    with col2:
        activity_fig = create_daily_activity_chart(days)
        if activity_fig:
            st.plotly_chart(activity_fig, use_container_width=True)
    
    # 4. 교통 정보 요약
    transport_summary = create_transport_summary(days)
    
    st.markdown("### 🚶 교통 정보 요약")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 이동 거리", f"{transport_summary['total_distance']}km")
    
    with col2:
        st.metric("총 이동 시간", f"{transport_summary['total_time']}분")
    
    with col3:
        st.metric("이동 횟수", f"{transport_summary['transfer_count']}회")
    
    with col4:
        st.metric("평균 거리", f"{transport_summary['avg_distance']}km")

def create_weather_widget(weather_data: List[Dict[str, Any]]) -> None:
    """날씨 위젯 생성"""
    
    if not weather_data:
        return
    
    st.markdown("## 🌤️ 여행 기간 날씨 정보")
    
    # 날씨 정보를 카드 형태로 표시
    cols = st.columns(min(len(weather_data), 7))  # 최대 7일
    
    for i, weather in enumerate(weather_data):
        with cols[i]:
            date = weather.get('date', f'Day {i+1}')
            temp = weather.get('temp_c', 0)
            condition = weather.get('condition', 'unknown')
            summary = weather.get('summary', '')
            
            # 날씨 아이콘
            weather_icons = {
                'clear': '☀️',
                'cloudy': '⛅',
                'rain': '🌧️',
                'snow': '❄️',
                'storm': '⛈️',
                'fog': '🌫️',
                'windy': '💨'
            }
            
            icon = weather_icons.get(condition, '🌤️')
            
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; border: 1px solid #ddd; border-radius: 10px; background: white;">
                <h4>{date}</h4>
                <div style="font-size: 2rem;">{icon}</div>
                <h3>{temp}°C</h3>
                <p style="font-size: 0.8rem;">{summary}</p>
            </div>
            """, unsafe_allow_html=True)

def create_interactive_map(days: List[Dict[str, Any]]) -> None:
    """인터랙티브 지도 생성 (간단한 버전)"""
    
    st.markdown("## 🗺️ 여행 경로 지도")
    
    # 지도 데이터 준비
    map_data = []
    
    for day in days:
        for period in ['morning', 'afternoon', 'evening']:
            if day.get(period):
                for place in day[period]:
                    if place.get('lat') and place.get('lon'):
                        map_data.append({
                            'name': place['name'],
                            'lat': place['lat'],
                            'lon': place['lon'],
                            'category': place.get('category', 'poi'),
                            'description': place.get('description', '')
                        })
    
    if not map_data:
        st.info("지도에 표시할 위치 정보가 없습니다.")
        return
    
    # 간단한 지도 표시 (실제 구현에서는 folium이나 streamlit-folium 사용)
    df = pd.DataFrame(map_data)
    
    st.map(df)
    
    # 위치 정보 테이블
    st.markdown("### 📍 방문 장소 위치 정보")
    
    # 카테고리별로 그룹화
    for category in df['category'].unique():
        category_places = df[df['category'] == category]
        st.markdown(f"**{category}**")
        
        for _, place in category_places.iterrows():
            st.write(f"📍 {place['name']} - 위도: {place['lat']:.4f}, 경도: {place['lon']:.4f}")
            if place['description']:
                st.write(f"   {place['description']}")
        st.write("---")

def create_packing_list(tips: Dict[str, Any], weather_data: List[Dict[str, Any]] = None) -> None:
    """준비물 리스트 생성"""
    
    st.markdown("## 🎒 여행 준비물 체크리스트")
    
    # 기본 준비물
    basic_items = [
        "여권/신분증", "현금/카드", "휴대폰 충전기", "보조 배터리",
        "편한 신발", "여분 옷", "세면도구", "약품"
    ]
    
    # 날씨별 추가 준비물
    weather_items = []
    if weather_data:
        for weather in weather_data:
            condition = weather.get('condition', '')
            if condition == 'rain':
                weather_items.extend(["우산", "우비", "방수 신발"])
            elif condition == 'snow':
                weather_items.extend(["장갑", "목도리", "방한복"])
            elif condition == 'clear':
                weather_items.extend(["선글라스", "자외선 차단제", "모자"])
    
    # 중복 제거
    weather_items = list(set(weather_items))
    
    # 준비물 표시
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📋 기본 준비물**")
        for item in basic_items:
            st.checkbox(item, key=f"basic_{item}")
    
    with col2:
        if weather_items:
            st.markdown("**🌤️ 날씨별 준비물**")
            for item in weather_items:
                st.checkbox(item, key=f"weather_{item}")
        else:
            st.markdown("**🌤️ 날씨별 준비물**")
            st.info("날씨 정보가 없어 기본 준비물만 표시됩니다.")
    
    # 현지 팁에서 추가 준비물
    if tips and tips.get('packing'):
        st.markdown("**💡 현지 가이드 추천 준비물**")
        for item in tips['packing']:
            st.checkbox(item, key=f"local_{item}")

def create_budget_estimator(days: List[Dict[str, Any]], budget_level: str) -> None:
    """예산 추정기 생성"""
    
    st.markdown("## 💰 예산 추정")
    
    # 카테고리별 예상 비용
    cost_estimates = {
        'museum': {'low': 5000, 'mid': 15000, 'high': 30000},
        'landmark': {'low': 0, 'mid': 5000, 'high': 15000},
        'park': {'low': 0, 'mid': 2000, 'high': 5000},
        'restaurant': {'low': 15000, 'mid': 30000, 'high': 60000},
        'cafe': {'low': 5000, 'mid': 10000, 'high': 20000},
        'shopping': {'low': 20000, 'mid': 50000, 'high': 100000},
        'entertainment': {'low': 10000, 'mid': 25000, 'high': 50000},
        'culture': {'low': 8000, 'mid': 20000, 'high': 40000},
        'nature': {'low': 0, 'mid': 3000, 'high': 8000},
        'history': {'low': 5000, 'mid': 15000, 'high': 30000},
        'art': {'low': 8000, 'mid': 20000, 'high': 40000},
        'architecture': {'low': 3000, 'mid': 8000, 'high': 20000},
        'religion': {'low': 0, 'mid': 2000, 'high': 5000},
        'sports': {'low': 10000, 'mid': 25000, 'high': 50000},
        'nightlife': {'low': 20000, 'mid': 40000, 'high': 80000},
        'poi': {'low': 5000, 'mid': 15000, 'high': 30000}
    }
    
    # 총 비용 계산
    total_cost = 0
    category_costs = {}
    
    for day in days:
        for period in ['morning', 'afternoon', 'evening']:
            if day.get(period):
                for place in day[period]:
                    category = place.get('category', 'poi')
                    cost = cost_estimates.get(category, cost_estimates['poi'])[budget_level]
                    
                    total_cost += cost
                    
                    if category not in category_costs:
                        category_costs[category] = 0
                    category_costs[category] += cost
    
    # 비용 표시
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("💰 총 예상 비용", f"{total_cost:,}원")
        
        # 예산 수준별 설명
        budget_descriptions = {
            'low': '절약형: 기본적인 경험 중심',
            'mid': '보통형: 균형잡힌 여행 경험',
            'high': '프리미엄형: 고급스러운 여행 경험'
        }
        
        st.info(f"**예산 수준**: {budget_descriptions.get(budget_level, '')}")
    
    with col2:
        st.markdown("**📊 카테고리별 비용**")
        for category, cost in sorted(category_costs.items(), key=lambda x: x[1], reverse=True):
            if cost > 0:
                st.write(f"• {category}: {cost:,}원")
    
    # 절약 팁
    st.markdown("**💡 절약 팁**")
    if budget_level == 'low':
        st.write("• 무료 관광지를 우선적으로 방문하세요")
        st.write("• 현지 시장에서 식사를 즐기세요")
        st.write("• 대중교통을 적극 활용하세요")
    elif budget_level == 'mid':
        st.write("• 유료 명소와 무료 명소를 조합하세요")
        st.write("• 점심은 현지 맛집, 저녁은 절약하세요")
        st.write("• 할인 정보를 미리 확인하세요")
    else:
        st.write("• 프리미엄 경험을 즐기세요")
        st.write("• 고급 레스토랑에서 현지 요리를 맛보세요")
        st.write("• 가이드 서비스를 활용하세요")
