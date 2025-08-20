from __future__ import annotations
from crewai import Agent
from typing import Dict, Any, List
from ..schemas import Tips, Place

class LocalGuideAgent:
    """현지 문화, 관습, 팁을 제공하는 Agent"""
    
    def __init__(self):
        self.agent = Agent(
            role="Local Guide",
            goal="여행지의 현지 문화, 관습, 실용적인 팁을 제공하여 여행자가 현지인처럼 여행할 수 있도록 돕습니다",
            backstory="""당신은 각 여행지의 현지 가이드입니다. 
            해당 지역의 문화, 관습, 예의, 안전 수칙, 실용적인 정보를 잘 알고 있습니다.
            여행자가 현지 문화를 존중하면서도 편안하게 여행할 수 있도록 
            실용적이고 문화적으로 민감한 조언을 제공합니다.""",
            verbose=True,
            allow_delegation=False
        )
    
    async def get_local_tips(self, destination: str, locale: str = "ko_KR") -> Tips:
        """현지 팁 제공"""
        try:
            # 기본 팁 생성
            basic_tips = self._get_basic_tips(destination, locale)
            
            # AI를 통한 현지 정보 보강
            enhanced_tips = await self._enhance_with_ai(destination, basic_tips)
            
            return enhanced_tips
            
        except Exception as e:
            # 오류 발생 시 기본 팁 반환
            return self._get_fallback_tips(destination, locale)
    
    def _get_basic_tips(self, destination: str, locale: str) -> Tips:
        """기본 현지 팁 생성"""
        # 목적지별 기본 팁
        destination_tips = {
            "파리": {
                "etiquette": [
                    "프랑스어로 인사말 하기 (Bonjour)",
                    "식당에서 팁 문화 이해하기",
                    "예술 작품 감상 시 조용히 하기"
                ],
                "packing": [
                    "편한 걷기 신발",
                    "우산 (비가 자주 옴)",
                    "카페 문화 체험용 여유 시간"
                ],
                "safety": [
                    "소매치기 주의 (관광지 주변)",
                    "지하철에서 소지품 관리",
                    "밤늦게 외진 골목 피하기"
                ]
            },
            "도쿄": {
                "etiquette": [
                    "일본식 인사 (고개 숙이기)",
                    "전철에서 조용히 하기",
                    "신발 벗고 들어가는 곳 구분하기"
                ],
                "packing": [
                    "편한 신발 (많이 걸음)",
                    "보조 배터리",
                    "일본어 기본 인사말"
                ],
                "safety": [
                    "지진 대비 정보 확인",
                    "교통 신호 준수",
                    "야간 안전한 지역 파악"
                ]
            },
            "뉴욕": {
                "etiquette": [
                    "다양한 문화 존중하기",
                    "지하철에서 우선순위석 양보",
                    "팁 문화 이해하기"
                ],
                "packing": [
                    "편한 걷기 신발",
                    "지하철 카드",
                    "계절별 옷차림"
                ],
                "safety": [
                    "밤늦게 외진 곳 피하기",
                    "소지품 관리",
                    "교통 신호 준수"
                ]
            }
        }
        
        # 기본 팁
        default_tips = {
            "etiquette": [
                "현지 문화와 관습을 존중하세요",
                "현지 언어로 기본 인사말 하기",
                "종교 시설 방문 시 복장 규정 확인"
            ],
            "packing": [
                "편한 신발",
                "보조 배터리",
                "현지용 유심/ESIM",
                "기본 의약품"
            ],
            "safety": [
                "소매치기 주의",
                "늦은 밤 외진 골목 피하기",
                "긴급연락처 미리 확인"
            ]
        }
        
        # 목적지별 팁이 있으면 사용, 없으면 기본 팁
        tips = destination_tips.get(destination, default_tips)
        
        return Tips(
            etiquette=tips["etiquette"],
            packing=tips["packing"],
            safety=tips["safety"],
            local_customs=[
                "현지 시간대 확인",
                "현지 통화 환율 파악",
                "현지 교통수단 이용법 학습"
            ],
            emergency_contacts=[
                "현지 경찰: 112 (대부분 국가)",
                "현지 응급실",
                "대사관 연락처"
            ]
        )
    
    async def _enhance_with_ai(self, destination: str, basic_tips: Tips) -> Tips:
        """AI를 통한 현지 정보 보강"""
        try:
            # AI 에이전트를 통한 현지 정보 수집
            # 실제 구현에서는 CrewAI를 통한 정보 수집
            enhanced_tips = basic_tips
            
            # 목적지별 특별한 팁 추가
            if "파리" in destination.lower():
                enhanced_tips.local_customs.extend([
                    "프랑스의 식사 시간 문화 (늦은 점심, 늦은 저녁)",
                    "카페에서 테라스 자리 선점하기",
                    "박물관 무료 입장일 확인"
                ])
            elif "도쿄" in destination.lower():
                enhanced_tips.local_customs.extend([
                    "일본의 정시 문화",
                    "온천 이용 시 예의",
                    "편의점 문화 체험"
                ])
            elif "뉴욕" in destination.lower():
                enhanced_tips.local_customs.extend([
                    "뉴욕의 24시간 문화",
                    "브로드웨이 공연 예매 팁",
                    "다양한 음식 문화 체험"
                ])
            
            return enhanced_tips
            
        except Exception as e:
            # AI 보강 실패 시 기본 팁 반환
            return basic_tips
    
    def _get_fallback_tips(self, destination: str, locale: str) -> Tips:
        """폴백 팁 제공"""
        return Tips(
            etiquette=["현지 문화와 관습을 존중하세요"],
            packing=["편한 신발", "보조 배터리"],
            safety=["소매치기 주의", "늦은 밤 외진 골목 피하기"],
            local_customs=["현지 시간대와 통화 확인"],
            emergency_contacts=["현지 경찰: 112"]
        )
    
    async def get_cultural_context(self, destination: str) -> Dict[str, Any]:
        """문화적 맥락 정보 제공"""
        try:
            cultural_info = {
                "language": self._get_primary_language(destination),
                "currency": self._get_currency(destination),
                "timezone": self._get_timezone(destination),
                "cultural_norms": self._get_cultural_norms(destination)
            }
            return cultural_info
        except Exception as e:
            return {
                "language": "영어",
                "currency": "USD",
                "timezone": "UTC",
                "cultural_norms": ["현지 문화를 존중하세요"]
            }
    
    def _get_primary_language(self, destination: str) -> str:
        """주요 언어 확인"""
        language_map = {
            "파리": "프랑스어",
            "도쿄": "일본어",
            "뉴욕": "영어",
            "베를린": "독일어",
            "로마": "이탈리아어",
            "마드리드": "스페인어"
        }
        return language_map.get(destination, "영어")
    
    def _get_currency(self, destination: str) -> str:
        """통화 확인"""
        currency_map = {
            "파리": "EUR",
            "도쿄": "JPY",
            "뉴욕": "USD",
            "베를린": "EUR",
            "로마": "EUR",
            "마드리드": "EUR"
        }
        return currency_map.get(destination, "USD")
    
    def _get_timezone(self, destination: str) -> str:
        """시간대 확인"""
        timezone_map = {
            "파리": "Europe/Paris",
            "도쿄": "Asia/Tokyo",
            "뉴욕": "America/New_York",
            "베를린": "Europe/Berlin",
            "로마": "Europe/Rome",
            "마드리드": "Europe/Madrid"
        }
        return timezone_map.get(destination, "UTC")
    
    def _get_cultural_norms(self, destination: str) -> List[str]:
        """문화적 규범 확인"""
        norms_map = {
            "파리": [
                "식사 시간을 존중하기",
                "예술 작품 감상 시 조용히 하기",
                "카페 문화 체험하기"
            ],
            "도쿄": [
                "정시 문화 준수하기",
                "공공장소에서 조용히 하기",
                "신발 벗는 문화 이해하기"
            ],
            "뉴욕": [
                "다양한 문화 존중하기",
                "빠른 페이스 적응하기",
                "팁 문화 이해하기"
            ]
        }
        return norms_map.get(destination, ["현지 문화를 존중하세요"])

# 기존 함수 유지 (하위 호환성)
def get_local_tips(locale: str = "ko_KR") -> Tips:
    """기존 함수 유지"""
    return Tips(
        etiquette=["현지 식당의 예약 문화를 존중하세요.", "종교 시설 방문 시 복장 규정을 확인하세요."],
        packing=["편한 신발", "보조 배터리", "현지용 유심/ESIM"],
        safety=["소매치기 주의", "늦은 밤 외진 골목 피하기"]
    )
