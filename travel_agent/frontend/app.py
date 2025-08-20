import streamlit as st
import httpx
from datetime import date, timedelta
import json
import os

# 시각화 컴포넌트 import
try:
    from .components import (
        display_itinerary_summary,
        display_visualizations,
        create_weather_widget,
        create_interactive_map,
        create_packing_list,
        create_budget_estimator
    )
except ImportError:
    # 상대 import가 실패할 경우 절대 import 시도
    try:
        from travel_agent.frontend.components import (
            display_itinerary_summary,
            display_visualizations,
            create_weather_widget,
            create_interactive_map,
            create_packing_list,
            create_budget_estimator
        )
    except ImportError:
        # 컴포넌트를 찾을 수 없는 경우 기본 함수들 정의
        def display_itinerary_summary(data): pass
        def display_visualizations(data): pass
        def create_weather_widget(weather_data): pass
        def create_interactive_map(days): pass
        def create_packing_list(tips, weather_data=None): pass
        def create_budget_estimator(days, budget_level): pass

# 피드백 시스템 import
try:
    from .feedback import TravelFeedbackSystem
except ImportError:
    try:
        from travel_agent.frontend.feedback import TravelFeedbackSystem
    except ImportError:
        # 피드백 시스템을 찾을 수 없는 경우 기본 클래스 정의
        class TravelFeedbackSystem:
            def create_feedback_form(self, data): pass
            def display_feedback_history(self): pass

# 페이지 설정
st.set_page_config(
    page_title="AI 여행 계획사 - 맞춤형 여행 일정 생성",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 추가
st.markdown("""
<style>
    /* 기본 변수 설정 */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --success-color: #28a745;
        --warning-color: #ffc107;
        --danger-color: #dc3545;
        --info-color: #17a2b8;
        --light-color: #f8f9fa;
        --dark-color: #343a40;
        --border-color: #dee2e6;
        --text-color: #212529;
        --text-muted: #6c757d;
        --shadow: 0 2px 4px rgba(0,0,0,0.1);
        --border-radius: 10px;
        --transition: all 0.3s ease;
    }
    
    /* 다크 모드 지원 */
    @media (prefers-color-scheme: dark) {
        :root {
            --text-color: #f8f9fa;
            --text-muted: #adb5bd;
            --light-color: #343a40;
            --border-color: #495057;
            --shadow: 0 2px 4px rgba(255,255,255,0.1);
        }
    }
    
    /* 반응형 그리드 시스템 */
    .responsive-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    /* 메인 헤더 */
    .main-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        padding: 2rem;
        border-radius: var(--border-radius);
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 100%);
        pointer-events: none;
    }
    
    .main-header h1 {
        font-size: clamp(2rem, 5vw, 3.5rem);
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: clamp(1rem, 2.5vw, 1.25rem);
        opacity: 0.9;
        margin: 0;
    }
    
    /* 폼 컨테이너 */
    .form-container {
        background: var(--light-color);
        padding: clamp(1rem, 3vw, 2rem);
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
        margin-bottom: 2rem;
        box-shadow: var(--shadow);
        transition: var(--transition);
    }
    
    .form-container:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    /* 관심사 태그 */
    .interest-tag {
        background: var(--primary-color);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        display: inline-block;
        transition: var(--transition);
        cursor: pointer;
        user-select: none;
    }
    
    .interest-tag:hover {
        background: var(--secondary-color);
        transform: scale(1.05);
    }
    
    /* 상태 박스들 */
    .success-box, .info-box, .warning-box, .error-box {
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid;
        transition: var(--transition);
    }
    
    .success-box {
        background: #d4edda;
        border-color: var(--success-color);
        color: #155724;
    }
    
    .info-box {
        background: #d1ecf1;
        border-color: var(--info-color);
        color: #0c5460;
    }
    
    .warning-box {
        background: #fff3cd;
        border-color: var(--warning-color);
        color: #856404;
    }
    
    .error-box {
        background: #f8d7da;
        border-color: var(--danger-color);
        color: #721c24;
    }
    
    /* 일정 카드 */
    .day-card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: clamp(1rem, 3vw, 1.5rem);
        margin: 1rem 0;
        box-shadow: var(--shadow);
        transition: var(--transition);
        position: relative;
    }
    
    .day-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    .day-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        border-radius: var(--border-radius) var(--border-radius) 0 0;
    }
    
    /* 장소 아이템 */
    .place-item {
        background: var(--light-color);
        border-left: 4px solid var(--primary-color);
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        transition: var(--transition);
        cursor: pointer;
    }
    
    .place-item:hover {
        background: #e9ecef;
        transform: translateX(5px);
        box-shadow: var(--shadow);
    }
    
    /* 이동 정보 */
    .transfer-info {
        background: #e9ecef;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        border-left: 3px solid var(--info-color);
        transition: var(--transition);
    }
    
    .transfer-info:hover {
        background: #dee2e6;
        transform: translateX(3px);
    }
    
    /* 탭 콘텐츠 */
    .tab-content {
        padding: clamp(0.5rem, 2vw, 1rem) 0;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        border-radius: var(--border-radius);
        transition: var(--transition);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* 입력 필드 스타일 */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        border-radius: var(--border-radius);
        border: 2px solid var(--border-color);
        transition: var(--transition);
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stDateInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* 체크박스 스타일 */
    .stCheckbox > div > div > label {
        cursor: pointer;
        transition: var(--transition);
        padding: 0.5rem;
        border-radius: 5px;
    }
    
    .stCheckbox > div > div > label:hover {
        background: rgba(102, 126, 234, 0.1);
    }
    
    /* 메트릭 카드 */
    .metric-card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        text-align: center;
        box-shadow: var(--shadow);
        transition: var(--transition);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        color: var(--text-muted);
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* 로딩 애니메이션 */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255,255,255,.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* 접근성 개선 */
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }
    
    /* 포커스 표시 */
    *:focus {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
    }
    
    /* 고대비 모드 지원 */
    @media (prefers-contrast: high) {
        .main-header {
            border: 3px solid white;
        }
        
        .day-card {
            border: 2px solid var(--text-color);
        }
        
        .place-item {
            border-left: 6px solid var(--primary-color);
        }
    }
    
    /* 모바일 최적화 */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .form-container {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .day-card {
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .responsive-grid {
            grid-template-columns: 1fr;
            gap: 0.5rem;
        }
        
        .interest-tag {
            padding: 0.4rem 0.8rem;
            font-size: 0.9rem;
        }
    }
    
    /* 태블릿 최적화 */
    @media (min-width: 769px) and (max-width: 1024px) {
        .responsive-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    /* 대형 화면 최적화 */
    @media (min-width: 1025px) {
        .main-header {
            padding: 3rem;
        }
        
        .form-container {
            padding: 2.5rem;
        }
        
        .day-card {
            padding: 2rem;
        }
    }
    
    /* 인쇄 스타일 */
    @media print {
        .main-header,
        .form-container,
        .stButton,
        .stSidebar {
            display: none !important;
        }
        
        .day-card {
            break-inside: avoid;
            border: 1px solid #000;
            box-shadow: none;
        }
        
        .place-item {
            border-left: 2px solid #000;
        }
    }
    
    /* 애니메이션 성능 최적화 */
    .animate-on-scroll {
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.6s ease;
    }
    
    .animate-on-scroll.visible {
        opacity: 1;
        transform: translateY(0);
    }
    
    /* 스크롤바 스타일링 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--light-color);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-color);
    }
    
    /* 선택 텍스트 스타일 */
    ::selection {
        background: var(--primary-color);
        color: white;
    }
    
    ::-moz-selection {
        background: var(--primary-color);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# 메인 헤더
st.markdown("""
<div class="main-header">
    <h1>🧭 AI 여행 계획사</h1>
    <p>AI 에이전트가 협력하여 맞춤형 여행 일정을 생성해드립니다</p>
</div>
""", unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 백엔드 설정
    # 환경변수에서 백엔드 URL 가져오기 (기본값: localhost:8000)
    default_backend = os.getenv("BACKEND_URL", "http://localhost:8000")
    backend_url = st.text_input(
        "백엔드 URL", 
        value=default_backend,
        help="백엔드 서버의 URL을 입력하세요 (환경변수 BACKEND_URL로 설정 가능)"
    )
    
    # 오케스트레이터 모드 선택
    mode = st.selectbox(
        "계획 생성 모드",
        options=[
            ("crew", "🤖 CrewAI 모드 (AI 에이전트 협업)"),
            ("graph", "📊 Graph 모드 (기본 알고리즘)")
        ],
        format_func=lambda x: x[1],
        help="CrewAI 모드는 OpenAI API 키가 필요합니다"
    )
    mode = mode[0]  # 실제 값 추출
    
    # API 키 상태 표시
    st.subheader("🔑 API 상태")
    
    # OpenAI API 키 확인
    openai_key = st.secrets.get("OPENAI_API_KEY", "") if hasattr(st, 'secrets') else ""
    if openai_key:
        st.success("✅ OpenAI API 키 설정됨")
    else:
        st.warning("⚠️ OpenAI API 키 미설정")
    
    # OpenWeather API 키 확인
    weather_key = st.secrets.get("OPENWEATHER_API_KEY", "") if hasattr(st, 'secrets') else ""
    if weather_key:
        st.success("✅ OpenWeather API 키 설정됨")
    else:
        st.warning("⚠️ OpenWeather API 키 미설정")
    
    # Google Maps API 키 확인
    maps_key = st.secrets.get("GOOGLE_MAPS_API_KEY", "") if hasattr(st, 'secrets') else ""
    if maps_key:
        st.success("✅ Google Maps API 키 설정됨")
    else:
        st.warning("⚠️ Google Maps API 키 미설정")
    
    # FourSquare API 키 확인
    foursquare_key = st.secrets.get("FOURSQUARE_API_KEY", "") if hasattr(st, 'secrets') else ""
    if foursquare_key:
        st.success("✅ FourSquare API 키 설정됨")
    else:
        st.warning("⚠️ FourSquare API 키 미설정")
    
    st.divider()
    
    # 도움말
    st.subheader("💡 사용법")
    st.markdown("""
    1. **여행지 입력**: 방문하고 싶은 도시나 지역을 입력하세요
    2. **기간 선택**: 여행 시작일과 종료일을 선택하세요
    3. **관심사 선택**: 여행에서 중점을 두고 싶은 활동을 선택하세요
    4. **여행 스타일**: 여행의 페이스를 선택하세요
    5. **예산 설정**: 예산 수준을 선택하세요
    6. **계획 생성**: '여행 계획 생성' 버튼을 클릭하세요
    """)

# 메인 폼
st.markdown('<div class="form-container">', unsafe_allow_html=True)

with st.form("travel_preferences", clear_on_submit=False):
    st.header("🎯 여행 정보 입력")
    
    # 1단계: 기본 정보
    st.subheader("📍 기본 정보")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        destination = st.text_input(
            "여행지",
            value="파리",
            placeholder="예: 파리, 도쿄, 뉴욕, 로마...",
            help="방문하고 싶은 도시나 지역을 입력하세요"
        )
    
    with col2:
        party = st.number_input(
            "여행 인원",
            min_value=1,
            max_value=20,
            value=2,
            help="함께 여행할 인원 수를 입력하세요"
        )
    
    # 2단계: 여행 기간
    st.subheader("📅 여행 기간")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "시작일",
            value=date.today() + timedelta(days=30),
            min_value=date.today(),
            help="여행 시작일을 선택하세요"
        )
    
    with col2:
        end_date = st.date_input(
            "종료일",
            value=start_date + timedelta(days=3),
            min_value=start_date,
            help="여행 종료일을 선택하세요"
        )
    
    # 여행 일수 계산 및 표시
    if start_date and end_date:
        days_diff = (end_date - start_date).days
        if days_diff > 0:
            st.info(f"📊 총 여행 기간: {days_diff}일")
        elif days_diff == 0:
            st.warning("⚠️ 당일 여행입니다")
        else:
            st.error("❌ 종료일이 시작일보다 빠릅니다")
    
    # 3단계: 여행 관심사
    st.subheader("🎭 여행 관심사")
    
    # 관심사 카테고리별 그룹화
    interest_categories = {
        "문화 & 예술": ["박물관", "미술관", "공연장", "역사", "건축", "종교"],
        "자연 & 야외": ["공원", "산", "바다", "동물원", "식물원", "등산"],
        "엔터테인먼트": ["테마파크", "영화관", "게임센터", "카지노", "스포츠"],
        "미식 & 쇼핑": ["레스토랑", "카페", "시장", "쇼핑센터", "전통시장"],
        "휴식 & 웰빙": ["스파", "요가", "명상", "힐링", "휴양지"]
    }
    
    selected_interests = []
    for category, interests in interest_categories.items():
        st.markdown(f"**{category}**")
        cols = st.columns(3)
        for i, interest in enumerate(interests):
            with cols[i % 3]:
                if st.checkbox(interest, key=f"interest_{interest}"):
                    selected_interests.append(interest)
    
    # 선택된 관심사 표시
    if selected_interests:
        st.markdown("**선택된 관심사:**")
        for interest in selected_interests:
            st.markdown(f'<span class="interest-tag">{interest}</span>', unsafe_allow_html=True)
    
    # 4단계: 여행 스타일
    st.subheader("🚶 여행 스타일")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pace = st.selectbox(
            "여행 페이스",
            options=["relaxed", "balanced", "packed"],
            index=1,
            format_func=lambda x: {
                "relaxed": "😌 여유로운",
                "balanced": "⚖️ 균형잡힌", 
                "packed": "🏃 빡빡한"
            }[x],
            help="하루에 방문할 장소의 수를 결정합니다"
        )
    
    with col2:
        budget_level = st.selectbox(
            "예산 수준",
            options=["low", "mid", "high"],
            index=1,
            format_func=lambda x: {
                "low": "💰 절약형",
                "mid": "💳 보통형",
                "high": "💎 프리미엄"
            }[x],
            help="여행 예산에 맞는 장소를 추천합니다"
        )
    
    with col3:
        transport_mode = st.selectbox(
            "주요 교통수단",
            options=["walking", "transit", "driving"],
            index=0,
            format_func=lambda x: {
                "walking": "🚶 도보",
                "transit": "🚇 대중교통",
                "driving": "🚗 자동차"
            }[x],
            help="장소 간 이동 시 사용할 교통수단입니다"
        )
    
    # 5단계: 추가 옵션
    st.subheader("🔧 추가 옵션")
    
    col1, col2 = st.columns(2)
    
    with col1:
        locale = st.selectbox(
            "언어 설정",
            options=["ko_KR", "en_US", "ja_JP", "zh_CN"],
            index=0,
            format_func=lambda x: {
                "ko_KR": "🇰🇷 한국어",
                "en_US": "🇺🇸 영어",
                "ja_JP": "🇯🇵 일본어",
                "zh_CN": "🇨🇳 중국어"
            }[x]
        )
    
    with col2:
        include_weather = st.checkbox(
            "날씨 정보 포함",
            value=True,
            help="여행 기간의 날씨 정보를 포함하여 일정을 조정합니다"
        )
    
    # 폼 제출 버튼
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submitted = st.form_submit_button(
            "🚀 여행 계획 생성",
            type="primary",
            use_container_width=True
        )

st.markdown('</div>', unsafe_allow_html=True)

# 폼 제출 처리
if submitted:
    # 입력 검증
    if not destination:
        st.error("❌ 여행지를 입력해주세요")
    elif start_date >= end_date:
        st.error("❌ 종료일은 시작일보다 늦어야 합니다")
    elif not selected_interests:
        st.warning("⚠️ 관심사를 하나 이상 선택해주세요")
    else:
        # 페이로드 생성
        payload = {
            "destination": destination,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "interests": selected_interests,
            "pace": pace,
            "budget_level": budget_level,
            "party": int(party),
            "locale": locale,
            "transport_mode": transport_mode,
            "include_weather": include_weather
        }
        
        # 진행 상황 표시
        with st.spinner("🤖 AI 에이전트들이 여행 계획을 세우고 있습니다..."):
            try:
                # 백엔드 API 호출
                r = httpx.post(
                    f"{backend_url}/plan", 
                    params={"mode": mode}, 
                    json=payload, 
                    timeout=180.0
                )
                r.raise_for_status()
                data = r.json()["itinerary"]
                
                # 성공 메시지
                st.success("🎉 여행 계획이 완성되었습니다!")
                
                # 탭으로 결과 표시
                tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                    "📋 요약", "🗓️ 일정", "📊 시각화", "🗺️ 지도", "🎒 준비물", "💰 예산", "💬 피드백"
                ])
                
                with tab1:
                    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
                    
                    # 여행 계획 요약
                    display_itinerary_summary(data)
                    
                    # 여행 요약 상세
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.subheader("📋 여행 요약")
                    st.write(data["summary"])
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # 현지 팁 표시
                    if data.get("tips"):
                        st.subheader("💡 현지 가이드 팁")
                        tips = data["tips"]
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if tips.get("etiquette"):
                                st.markdown("**🎭 문화 및 예의**")
                                for tip in tips["etiquette"]:
                                    st.write(f"• {tip}")
                        
                        with col2:
                            if tips.get("packing"):
                                st.markdown("**🎒 준비물**")
                                for tip in tips["packing"]:
                                    st.write(f"• {tip}")
                        
                        with col3:
                            if tips.get("safety"):
                                st.markdown("**⚠️ 안전 및 주의사항**")
                                for tip in tips["safety"]:
                                    st.write(f"• {tip}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with tab2:
                    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
                    
                    # 일별 일정 표시
                    st.subheader("🗓️ 일별 여행 계획")
                    
                    for i, day in enumerate(data["days"]):
                        with st.expander(f"📅 {day['date']} (Day {i+1})", expanded=True):
                            st.markdown('<div class="day-card">', unsafe_allow_html=True)
                            
                            # 오전 일정
                            if day["morning"]:
                                st.markdown("**🌅 오전**")
                                for place in day["morning"]:
                                    st.markdown(f'<div class="place-item">', unsafe_allow_html=True)
                                    st.write(f"📍 **{place['name']}** ({place['category']})")
                                    if place.get('description'):
                                        st.write(f"   {place['description']}")
                                    if place.get('est_stay_min'):
                                        st.write(f"   ⏱️ 예상 체류시간: {place['est_stay_min']}분")
                                    st.markdown('</div>', unsafe_allow_html=True)
                            
                            # 점심
                            if day.get("lunch"):
                                st.markdown("**🍽️ 점심**")
                                st.info(day["lunch"])
                            
                            # 오후 일정
                            if day["afternoon"]:
                                st.markdown("**🌞 오후**")
                                for place in day["afternoon"]:
                                    st.markdown(f'<div class="place-item">', unsafe_allow_html=True)
                                    st.write(f"📍 **{place['name']}** ({place['category']})")
                                    if place.get('description'):
                                        st.write(f"   {place['description']}")
                                    if place.get('est_stay_min'):
                                        st.write(f"   ⏱️ 예상 체류시간: {place['est_stay_min']}분")
                                    st.markdown('</div>', unsafe_allow_html=True)
                            
                            # 저녁
                            if day.get("dinner"):
                                st.markdown("**🍽️ 저녁**")
                                st.info(day["dinner"])
                            
                            # 저녁 일정
                            if day["evening"]:
                                st.markdown("**🌙 저녁**")
                                for place in day["evening"]:
                                    st.markdown(f'<div class="place-item">', unsafe_allow_html=True)
                                    st.write(f"📍 **{place['name']}** ({place['category']})")
                                    if place.get('description'):
                                        st.write(f"   {place['description']}")
                                    if place.get('est_stay_min'):
                                        st.write(f"   ⏱️ 예상 체류시간: {place['est_stay_min']}분")
                                    st.markdown('</div>', unsafe_allow_html=True)
                            
                            # 이동 정보
                            if day.get("transfers"):
                                st.markdown("**🚶 이동 정보**")
                                for transfer in day["transfers"]:
                                    st.markdown(f'<div class="transfer-info">', unsafe_allow_html=True)
                                    st.write(f"🔄 {transfer['from_place']} → {transfer['to_place']}")
                                    st.write(f"   📏 거리: {transfer['distance_km']}km")
                                    st.write(f"   ⏱️ 시간: {transfer['travel_min']}분")
                                    st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with tab3:
                    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
                    
                    # 시각화 차트들 표시
                    display_visualizations(data)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with tab4:
                    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
                    
                    # 인터랙티브 지도
                    create_interactive_map(data.get("days", []))
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with tab5:
                    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
                    
                    # 준비물 체크리스트
                    create_packing_list(data.get("tips", {}))
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with tab6:
                    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
                    
                    # 예산 추정
                    create_budget_estimator(data.get("days", []), budget_level)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with tab7:
                    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
                    
                    # 피드백 시스템
                    feedback_system = TravelFeedbackSystem()
                    
                    # 피드백 입력 폼
                    feedback_result = feedback_system.create_feedback_form(data)
                    
                    # 피드백 히스토리 표시
                    if st.checkbox("📚 피드백 히스토리 보기", value=False):
                        feedback_system.display_feedback_history()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # JSON 다운로드 버튼
                st.divider()
                st.subheader("💾 여행 계획 다운로드")
                json_str = json.dumps(data, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📥 JSON 파일 다운로드",
                    data=json_str,
                    file_name=f"travel_plan_{destination}_{start_date}.json",
                    mime="application/json"
                )
                
            except httpx.TimeoutException:
                st.error("⏰ 요청 시간이 초과되었습니다. 다시 시도해주세요.")
            except httpx.HTTPStatusError as e:
                st.error(f"❌ 서버 오류: {e.response.status_code}")
                st.error(f"오류 내용: {e.response.text}")
            except Exception as e:
                st.error(f"❌ 예상치 못한 오류가 발생했습니다: {e}")
                st.info("💡 백엔드 서버가 실행 중인지 확인해주세요.")

# 페이지 하단 정보
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🤖 AI 에이전트 기반 여행 계획 시스템</p>
    <p>Powered by CrewAI, OpenAI, and various travel APIs</p>
</div>
""", unsafe_allow_html=True)
