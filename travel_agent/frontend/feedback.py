import streamlit as st
import json
from typing import Dict, List, Any
from datetime import datetime

class TravelFeedbackSystem:
    """여행 일정 피드백 및 개선 시스템"""
    
    def __init__(self):
        self.feedback_types = {
            "schedule": "일정 조정",
            "places": "장소 변경",
            "timing": "시간 조정",
            "transport": "교통수단 변경",
            "budget": "예산 조정",
            "other": "기타"
        }
        
        self.improvement_suggestions = {
            "schedule": [
                "하루에 너무 많은 장소를 방문합니다",
                "휴식 시간이 부족합니다",
                "이동 시간이 너무 깁니다",
                "더 여유로운 일정을 원합니다",
                "더 빡빡한 일정을 원합니다"
            ],
            "places": [
                "특정 카테고리의 장소를 더 추가하고 싶습니다",
                "현재 추천된 장소가 마음에 들지 않습니다",
                "더 현지적인 장소를 원합니다",
                "관광지보다는 숨겨진 명소를 원합니다",
                "특정 장소를 제외하고 싶습니다"
            ],
            "timing": [
                "아침 일정을 늦게 시작하고 싶습니다",
                "저녁 일정을 일찍 끝내고 싶습니다",
                "점심 시간을 더 길게 하고 싶습니다",
                "특정 시간대에 방문하고 싶은 장소가 있습니다",
                "일정을 더 유연하게 조정하고 싶습니다"
            ],
            "transport": [
                "도보보다는 대중교통을 더 활용하고 싶습니다",
                "자전거를 이용한 이동을 원합니다",
                "택시나 자동차를 더 활용하고 싶습니다",
                "이동 시간을 단축하고 싶습니다",
                "경로를 최적화하고 싶습니다"
            ],
            "budget": [
                "더 저렴한 옵션을 원합니다",
                "프리미엄 경험을 더 원합니다",
                "무료 관광지를 더 추가하고 싶습니다",
                "식비를 줄이고 싶습니다",
                "쇼핑 예산을 늘리고 싶습니다"
            ]
        }
    
    def create_feedback_form(self, itinerary_data: Dict[str, Any]) -> Dict[str, Any]:
        """피드백 입력 폼 생성"""
        
        st.markdown("## 💬 여행 일정 피드백")
        st.info("생성된 여행 계획에 대한 의견을 들려주세요. 더 나은 일정을 만들기 위해 활용하겠습니다.")
        
        feedback_data = {}
        
        # 1. 전체 만족도
        st.subheader("📊 전체 만족도")
        overall_satisfaction = st.slider(
            "이 여행 계획에 대한 전반적인 만족도는 어떠신가요?",
            min_value=1,
            max_value=5,
            value=3,
            help="1: 매우 불만족, 5: 매우 만족"
        )
        
        satisfaction_labels = {
            1: "매우 불만족 😞",
            2: "불만족 😕", 
            3: "보통 😐",
            4: "만족 😊",
            5: "매우 만족 😍"
        }
        
        st.write(f"**선택된 만족도**: {satisfaction_labels[overall_satisfaction]}")
        feedback_data["overall_satisfaction"] = overall_satisfaction
        
        # 2. 구체적인 피드백
        st.subheader("🔍 구체적인 피드백")
        
        feedback_type = st.selectbox(
            "어떤 부분에 대한 피드백인가요?",
            options=list(self.feedback_types.keys()),
            format_func=lambda x: self.feedback_types[x]
        )
        
        feedback_data["feedback_type"] = feedback_type
        
        # 피드백 유형별 세부 질문
        if feedback_type in self.improvement_suggestions:
            st.write("**개선하고 싶은 부분을 선택하세요:**")
            selected_improvements = st.multiselect(
                "개선 사항",
                options=self.improvement_suggestions[feedback_type],
                help="해당하는 항목들을 모두 선택해주세요"
            )
            feedback_data["improvement_areas"] = selected_improvements
        
        # 3. 자유 텍스트 피드백
        st.subheader("✍️ 자유 의견")
        free_feedback = st.text_area(
            "추가적인 의견이나 요청사항이 있으시면 자유롭게 작성해주세요.",
            height=120,
            placeholder="예: 파리에서 더 많은 미술관을 방문하고 싶습니다. 또는: 이동 시간이 너무 길어서 하루에 방문할 수 있는 장소가 적습니다."
        )
        
        if free_feedback:
            feedback_data["free_feedback"] = free_feedback
        
        # 4. 일정별 세부 피드백
        st.subheader("📅 일정별 피드백")
        
        days = itinerary_data.get("days", [])
        day_feedback = {}
        
        for i, day in enumerate(days):
            with st.expander(f"Day {i+1} ({day.get('date', '')})", expanded=False):
                day_satisfaction = st.slider(
                    f"Day {i+1} 만족도",
                    min_value=1,
                    max_value=5,
                    value=3,
                    key=f"day_{i}_satisfaction"
                )
                
                day_comment = st.text_input(
                    f"Day {i+1} 특별한 의견",
                    placeholder="이 날의 일정에 대한 의견이 있으시면 작성해주세요.",
                    key=f"day_{i}_comment"
                )
                
                day_feedback[f"day_{i+1}"] = {
                    "satisfaction": day_satisfaction,
                    "comment": day_comment if day_comment else None
                }
        
        feedback_data["day_feedback"] = day_feedback
        
        # 5. 장소별 피드백
        st.subheader("📍 장소별 피드백")
        
        all_places = []
        for day in days:
            for period in ['morning', 'afternoon', 'evening']:
                if day.get(period):
                    all_places.extend(day[period])
        
        if all_places:
            st.write("**방문 장소에 대한 의견을 들려주세요:**")
            
            place_feedback = {}
            for place in all_places:
                place_name = place.get('name', 'Unknown')
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"📍 {place_name}")
                with col2:
                    rating = st.selectbox(
                        "평점",
                        options=[1, 2, 3, 4, 5],
                        index=2,
                        key=f"place_{place_name}_rating"
                    )
                
                place_comment = st.text_input(
                    f"{place_name}에 대한 의견",
                    placeholder="이 장소에 대한 의견이나 개선 제안이 있으시면 작성해주세요.",
                    key=f"place_{place_name}_comment"
                )
                
                place_feedback[place_name] = {
                    "rating": rating,
                    "comment": place_comment if place_comment else None,
                    "category": place.get('category', 'poi'),
                    "est_stay_min": place.get('est_stay_min', 60)
                }
            
            feedback_data["place_feedback"] = place_feedback
        
        # 6. 개선 요청
        st.subheader("🔄 개선 요청")
        
        improvement_request = st.text_area(
            "이 여행 계획을 어떻게 개선하고 싶으신가요?",
            height=100,
            placeholder="구체적인 개선 요청사항을 작성해주세요. 예: 더 많은 자연 명소를 추가하고 싶습니다. 또는: 하루에 방문하는 장소 수를 줄이고 싶습니다."
        )
        
        if improvement_request:
            feedback_data["improvement_request"] = improvement_request
        
        # 7. 추가 옵션
        st.subheader("⚙️ 추가 옵션")
        
        col1, col2 = st.columns(2)
        
        with col1:
            include_weather = st.checkbox(
                "날씨 정보를 더 자세히 포함",
                value=False,
                help="날씨에 따른 일정 조정을 더 세밀하게 하고 싶은 경우"
            )
            
            include_local_tips = st.checkbox(
                "현지 정보를 더 자세히 포함",
                value=False,
                help="현지 문화, 주의사항 등을 더 자세히 알고 싶은 경우"
            )
        
        with col2:
            include_alternatives = st.checkbox(
                "대안 장소 제시",
                value=False,
                help="추천된 장소 외에 대안을 제시하고 싶은 경우"
            )
            
            include_budget_breakdown = st.checkbox(
                "상세 예산 분석",
                value=False,
                help="카테고리별 상세한 예산 분석을 원하는 경우"
            )
        
        feedback_data["additional_options"] = {
            "include_weather": include_weather,
            "include_local_tips": include_local_tips,
            "include_alternatives": include_alternatives,
            "include_budget_breakdown": include_budget_breakdown
        }
        
        # 8. 연락처 정보 (선택사항)
        st.subheader("📧 연락처 정보 (선택사항)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input(
                "이메일",
                placeholder="개선된 계획을 받고 싶으시면 이메일을 입력해주세요.",
                help="개선된 여행 계획을 이메일로 받아보실 수 있습니다."
            )
        
        with col2:
            phone = st.text_input(
                "전화번호",
                placeholder="긴급한 문의사항이 있을 경우를 대비해 전화번호를 입력해주세요.",
                help="선택사항입니다."
            )
        
        if email or phone:
            feedback_data["contact_info"] = {
                "email": email if email else None,
                "phone": phone if phone else None
            }
        
        # 9. 피드백 제출
        st.divider()
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_feedback = st.button(
                "📤 피드백 제출",
                type="primary",
                use_container_width=True
            )
        
        if submit_feedback:
            # 피드백 데이터에 메타데이터 추가
            feedback_data["metadata"] = {
                "submitted_at": datetime.now().isoformat(),
                "itinerary_id": itinerary_data.get("summary", ""),
                "feedback_version": "1.0"
            }
            
            # 피드백 저장 및 처리
            self._process_feedback(feedback_data, itinerary_data)
            
            return feedback_data
        
        return None
    
    def _process_feedback(self, feedback_data: Dict[str, Any], itinerary_data: Dict[str, Any]) -> None:
        """피드백 처리 및 저장"""
        
        try:
            # 피드백 요약 표시
            st.success("✅ 피드백이 성공적으로 제출되었습니다!")
            
            # 피드백 요약
            st.markdown("## 📋 피드백 요약")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("전체 만족도", f"{feedback_data['overall_satisfaction']}/5")
                st.metric("피드백 유형", self.feedback_types.get(feedback_data['feedback_type'], '기타'))
                
                if feedback_data.get('improvement_areas'):
                    st.write("**개선 요청 사항:**")
                    for area in feedback_data['improvement_areas']:
                        st.write(f"• {area}")
            
            with col2:
                if feedback_data.get('free_feedback'):
                    st.write("**자유 의견:**")
                    st.info(feedback_data['free_feedback'])
                
                if feedback_data.get('improvement_request'):
                    st.write("**개선 요청:**")
                    st.warning(feedback_data['improvement_request'])
            
            # 피드백 데이터를 세션 상태에 저장
            if 'feedback_history' not in st.session_state:
                st.session_state.feedback_history = []
            
            st.session_state.feedback_history.append({
                'timestamp': datetime.now(),
                'feedback': feedback_data,
                'itinerary': itinerary_data
            })
            
            # 개선된 계획 생성 제안
            st.markdown("## 🚀 개선된 계획 생성")
            
            if st.button("🔄 피드백을 반영한 개선된 계획 생성", type="secondary"):
                self._generate_improved_plan(feedback_data, itinerary_data)
            
        except Exception as e:
            st.error(f"피드백 처리 중 오류가 발생했습니다: {e}")
    
    def _generate_improved_plan(self, feedback_data: Dict[str, Any], original_itinerary: Dict[str, Any]) -> None:
        """피드백을 반영한 개선된 계획 생성"""
        
        st.info("🤖 AI 에이전트들이 피드백을 분석하여 개선된 여행 계획을 생성하고 있습니다...")
        
        # 여기서는 간단한 예시를 보여줍니다
        # 실제 구현에서는 백엔드 API를 호출하여 개선된 계획을 생성합니다
        
        st.markdown("## 📝 개선 제안")
        
        # 만족도 기반 개선 제안
        satisfaction = feedback_data.get('overall_satisfaction', 3)
        
        if satisfaction <= 2:
            st.warning("**낮은 만족도 감지** - 전면적인 일정 재구성이 필요합니다.")
            st.write("• 여행 스타일과 선호도를 다시 파악하겠습니다")
            st.write("• 장소 선택 기준을 재검토하겠습니다")
            st.write("• 일정 밀도를 조정하겠습니다")
        
        elif satisfaction == 3:
            st.info("**보통 만족도** - 부분적인 개선이 필요합니다.")
            st.write("• 주요 불만 사항을 중심으로 개선하겠습니다")
            st.write("• 대안 장소를 제시하겠습니다")
            st.write("• 시간 배분을 최적화하겠습니다")
        
        else:
            st.success("**높은 만족도** - 세부적인 조정으로 완벽하게 만들겠습니다.")
            st.write("• 추가 옵션과 대안을 제시하겠습니다")
            st.write("• 더 상세한 현지 정보를 제공하겠습니다")
            st.write("• 예산 최적화를 진행하겠습니다")
        
        # 피드백 유형별 구체적 개선 방안
        feedback_type = feedback_data.get('feedback_type')
        if feedback_type == 'schedule':
            st.markdown("**📅 일정 개선 방안:**")
            st.write("• 하루 방문 장소 수 조정")
            st.write("• 휴식 시간 추가")
            st.write("• 이동 시간 최적화")
        
        elif feedback_type == 'places':
            st.markdown("**📍 장소 개선 방안:**")
            st.write("• 카테고리별 장소 재선별")
            st.write("• 현지인 추천 장소 추가")
            st.write("• 숨겨진 명소 발굴")
        
        elif feedback_type == 'timing':
            st.markdown("**⏰ 시간 개선 방안:**")
            st.write("• 방문 시간대 조정")
            st.write("• 운영 시간 고려")
            st.write("• 피크 시간대 회피")
        
        # 개선된 계획 생성 버튼
        st.divider()
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎯 개선된 계획 생성하기", type="primary"):
                st.success("개선된 계획을 생성하기 위해 백엔드 API를 호출합니다...")
                # 실제 구현에서는 여기서 백엔드 API 호출
                st.info("이 기능은 백엔드 연동 후 완전히 구현됩니다.")
    
    def display_feedback_history(self) -> None:
        """피드백 히스토리 표시"""
        
        if 'feedback_history' not in st.session_state or not st.session_state.feedback_history:
            st.info("아직 제출된 피드백이 없습니다.")
            return
        
        st.markdown("## 📚 피드백 히스토리")
        
        for i, history_item in enumerate(reversed(st.session_state.feedback_history)):
            with st.expander(f"피드백 #{len(st.session_state.feedback_history) - i} - {history_item['timestamp'].strftime('%Y-%m-%d %H:%M')}", expanded=False):
                
                feedback = history_item['feedback']
                itinerary = history_item['itinerary']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**목적지**: {itinerary.get('summary', '').split()[0]}")
                    st.write(f"**만족도**: {feedback.get('overall_satisfaction', 'N/A')}/5")
                    st.write(f"**피드백 유형**: {self.feedback_types.get(feedback.get('feedback_type', ''), '기타')}")
                
                with col2:
                    if feedback.get('free_feedback'):
                        st.write("**주요 의견**:")
                        st.info(feedback['free_feedback'][:100] + "..." if len(feedback['free_feedback']) > 100 else feedback['free_feedback'])
                
                # 피드백 상세 내용
                if feedback.get('improvement_request'):
                    st.write("**개선 요청**:")
                    st.warning(feedback['improvement_request'])
                
                # 피드백 데이터 다운로드
                feedback_json = json.dumps(feedback, ensure_ascii=False, indent=2)
                st.download_button(
                    label=f"📥 피드백 #{len(st.session_state.feedback_history) - i} 다운로드",
                    data=feedback_json,
                    file_name=f"feedback_{history_item['timestamp'].strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

def create_feedback_widget(itinerary_data: Dict[str, Any]) -> None:
    """피드백 위젯 생성 (간단한 버전)"""
    
    st.markdown("## 💬 간단한 피드백")
    
    # 만족도
    satisfaction = st.slider(
        "이 여행 계획에 대한 만족도는 어떠신가요?",
        min_value=1,
        max_value=5,
        value=3
    )
    
    # 간단한 의견
    comment = st.text_area(
        "의견이나 개선 요청사항이 있으시면 작성해주세요.",
        height=100
    )
    
    # 제출 버튼
    if st.button("📤 피드백 제출", type="secondary"):
        if comment:
            st.success("✅ 피드백이 제출되었습니다!")
            st.info("제출된 피드백을 바탕으로 더 나은 여행 계획을 만들어드리겠습니다.")
        else:
            st.warning("⚠️ 의견을 작성해주세요.")
