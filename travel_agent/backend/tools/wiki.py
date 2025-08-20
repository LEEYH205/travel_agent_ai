from __future__ import annotations
import httpx
import asyncio
from typing import Dict, List, Optional, Any
import logging
import re
from urllib.parse import quote

# 로깅 설정
logger = logging.getLogger(__name__)

class WikipediaService:
    """Wikipedia API를 사용한 여행지 정보 수집 서비스"""
    
    def __init__(self):
        self.base_url = "https://en.wikipedia.org/api/rest_v1"
        self.timeout = 15
        
        # 한국어 위키백과 지원
        self.ko_base_url = "https://ko.wikipedia.org/api/rest_v1"
        
        # 여행 관련 키워드
        self.travel_keywords = [
            "관광", "여행", "명소", "박물관", "성당", "궁전", "공원", "광장",
            "역사", "문화", "예술", "건축", "자연", "풍경", "축제", "음식",
            "shopping", "restaurant", "museum", "cathedral", "palace", "park",
            "square", "history", "culture", "art", "architecture", "nature",
            "landscape", "festival", "food", "cuisine"
        ]
    
    async def get_destination_info(self, destination: str, lang: str = "ko") -> Dict[str, Any]:
        """여행지의 종합 정보 수집"""
        try:
            # 한국어 우선, 영어 차선
            if lang == "ko":
                info = await self._get_ko_wikipedia_info(destination)
                if not info or not info.get("summary"):
                    logger.info(f"한국어 정보를 찾을 수 없어 영어 정보를 검색합니다: {destination}")
                    info = await self._get_en_wikipedia_info(destination)
            else:
                info = await self._get_en_wikipedia_info(destination)
                if not info or not info.get("summary"):
                    logger.info(f"영어 정보를 찾을 수 없어 한국어 정보를 검색합니다: {destination}")
                    info = await self._get_ko_wikipedia_info(destination)
            
            if info:
                # 추가 정보 수집
                enhanced_info = await self._enhance_destination_info(destination, info)
                return enhanced_info
            
            # 정보를 찾을 수 없는 경우 기본 정보 반환
            return self._get_basic_destination_info(destination)
            
        except Exception as e:
            logger.error(f"여행지 정보 수집 중 오류: {e}")
            return self._get_basic_destination_info(destination)
    
    async def _get_ko_wikipedia_info(self, destination: str) -> Optional[Dict[str, Any]]:
        """한국어 위키백과에서 정보 수집"""
        try:
            # 1. 페이지 요약 정보
            summary_url = f"{self.ko_base_url}/page/summary/{quote(destination)}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(summary_url)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_wikipedia_summary(data, "ko")
            
            return None
            
        except Exception as e:
            logger.error(f"한국어 위키백과 정보 수집 오류: {e}")
            return None
    
    async def _get_en_wikipedia_info(self, destination: str) -> Optional[Dict[str, Any]]:
        """영어 위키백과에서 정보 수집"""
        try:
            # 1. 페이지 요약 정보
            summary_url = f"{self.base_url}/page/summary/{quote(destination)}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(summary_url)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_wikipedia_summary(data, "en")
            
            return None
            
        except Exception as e:
            logger.error(f"영어 위키백과 정보 수집 오류: {e}")
            return None
    
    def _parse_wikipedia_summary(self, data: Dict[str, Any], lang: str) -> Dict[str, Any]:
        """위키백과 요약 정보 파싱"""
        try:
            return {
                "title": data.get("title", ""),
                "summary": data.get("extract", ""),
                "language": lang,
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "thumbnail": data.get("thumbnail", {}).get("source", ""),
                "coordinates": data.get("coordinates", {}),
                "page_id": data.get("pageid"),
                "categories": self._extract_categories(data.get("extract", "")),
                "type": self._determine_destination_type(data.get("extract", ""))
            }
        except Exception as e:
            logger.error(f"위키백과 요약 파싱 오류: {e}")
            return {}
    
    async def _enhance_destination_info(self, destination: str, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """기본 정보를 바탕으로 추가 정보 수집"""
        try:
            enhanced_info = basic_info.copy()
            
            # 1. 여행 관련 정보 추출
            travel_info = self._extract_travel_info(basic_info.get("summary", ""))
            enhanced_info["travel_info"] = travel_info
            
            # 2. 주요 명소 추출
            attractions = self._extract_attractions(basic_info.get("summary", ""))
            enhanced_info["attractions"] = attractions
            
            # 3. 문화 및 역사 정보 추출
            cultural_info = self._extract_cultural_info(basic_info.get("summary", ""))
            enhanced_info["cultural_info"] = cultural_info
            
            # 4. 실용 정보 추출
            practical_info = self._extract_practical_info(basic_info.get("summary", ""))
            enhanced_info["practical_info"] = practical_info
            
            # 5. 여행 팁 생성
            travel_tips = self._generate_travel_tips(destination, enhanced_info)
            enhanced_info["travel_tips"] = travel_tips
            
            return enhanced_info
            
        except Exception as e:
            logger.error(f"여행지 정보 강화 중 오류: {e}")
            return basic_info
    
    def _extract_categories(self, text: str) -> List[str]:
        """텍스트에서 카테고리 정보 추출"""
        categories = []
        
        # 일반적인 카테고리 키워드
        category_keywords = [
            "도시", "국가", "지역", "주", "도", "시", "군", "구",
            "city", "country", "region", "state", "province", "district"
        ]
        
        for keyword in category_keywords:
            if keyword in text:
                categories.append(keyword)
        
        return categories
    
    def _determine_destination_type(self, text: str) -> str:
        """목적지 유형 판단"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["도시", "city", "metropolis"]):
            return "도시"
        elif any(word in text_lower for word in ["국가", "country", "nation"]):
            return "국가"
        elif any(word in text_lower for word in ["지역", "region", "area"]):
            return "지역"
        elif any(word in text_lower for word in ["섬", "island"]):
            return "섬"
        elif any(word in text_lower for word in ["산", "mountain", "peak"]):
            return "산"
        else:
            return "기타"
    
    def _extract_travel_info(self, text: str) -> Dict[str, Any]:
        """여행 관련 정보 추출"""
        travel_info = {
            "best_time": "",
            "climate": "",
            "accessibility": "",
            "safety": ""
        }
        
        # 최적 여행 시기 추출
        time_patterns = [
            r"(\d{1,2}월|봄|여름|가을|겨울).*?(여행|방문|관광)",
            r"(spring|summer|autumn|winter).*?(visit|travel|tour)",
            r"(\d{1,2}월).*?(최적|좋은|적합한)"
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                travel_info["best_time"] = match.group(1)
                break
        
        # 기후 정보 추출
        climate_patterns = [
            r"(온화한|따뜻한|시원한|건조한|습한).*?(기후|날씨)",
            r"(mild|warm|cool|dry|humid).*?(climate|weather)"
        ]
        
        for pattern in climate_patterns:
            match = re.search(pattern, text)
            if match:
                travel_info["climate"] = match.group(1)
                break
        
        return travel_info
    
    def _extract_attractions(self, text: str) -> List[str]:
        """주요 명소 추출"""
        attractions = []
        
        # 명소 관련 키워드
        attraction_keywords = [
            "박물관", "성당", "궁전", "공원", "광장", "탑", "다리", "성",
            "museum", "cathedral", "palace", "park", "square", "tower", "bridge", "castle"
        ]
        
        for keyword in attraction_keywords:
            if keyword in text:
                attractions.append(keyword)
        
        return attractions[:5]  # 최대 5개
    
    def _extract_cultural_info(self, text: str) -> Dict[str, Any]:
        """문화 및 역사 정보 추출"""
        cultural_info = {
            "history": "",
            "culture": "",
            "traditions": "",
            "festivals": ""
        }
        
        # 역사 정보
        if any(word in text for word in ["역사", "history", "ancient", "medieval"]):
            cultural_info["history"] = "풍부한 역사적 배경을 가지고 있습니다."
        
        # 문화 정보
        if any(word in text for word in ["문화", "culture", "artistic", "cultural"]):
            cultural_info["culture"] = "다양한 문화적 요소를 제공합니다."
        
        # 전통
        if any(word in text for word in ["전통", "tradition", "traditional"]):
            cultural_info["traditions"] = "오랜 전통을 유지하고 있습니다."
        
        # 축제
        if any(word in text for word in ["축제", "festival", "celebration"]):
            cultural_info["festivals"] = "다양한 축제와 행사가 열립니다."
        
        return cultural_info
    
    def _extract_practical_info(self, text: str) -> Dict[str, Any]:
        """실용 정보 추출"""
        practical_info = {
            "transportation": "",
            "accommodation": "",
            "cuisine": "",
            "shopping": ""
        }
        
        # 교통
        if any(word in text for word in ["지하철", "버스", "기차", "subway", "bus", "train"]):
            practical_info["transportation"] = "대중교통이 잘 발달되어 있습니다."
        
        # 숙박
        if any(word in text for word in ["호텔", "숙박", "hotel", "accommodation"]):
            practical_info["accommodation"] = "다양한 숙박 옵션을 제공합니다."
        
        # 음식
        if any(word in text for word in ["음식", "요리", "cuisine", "food"]):
            practical_info["cuisine"] = "독특한 지역 음식을 경험할 수 있습니다."
        
        # 쇼핑
        if any(word in text for word in ["쇼핑", "상점", "shopping", "market"]):
            practical_info["shopping"] = "다양한 쇼핑 기회를 제공합니다."
        
        return practical_info
    
    def _generate_travel_tips(self, destination: str, info: Dict[str, Any]) -> List[str]:
        """여행 팁 생성"""
        tips = []
        
        # 기본 팁
        tips.append(f"{destination} 방문 전 기본 정보를 확인하세요.")
        
        # 언어 관련 팁
        if info.get("language") == "ko":
            tips.append("한국어 정보가 제공되어 한국인 여행객에게 유용합니다.")
        else:
            tips.append("영어 정보가 제공되어 국제 여행객에게 적합합니다.")
        
        # 문화 관련 팁
        if info.get("cultural_info", {}).get("history"):
            tips.append("역사적 배경을 미리 알아보면 더욱 흥미로운 여행이 될 것입니다.")
        
        if info.get("cultural_info", {}).get("festivals"):
            tips.append("축제 시기를 확인하여 특별한 경험을 계획해보세요.")
        
        # 실용 팁
        if info.get("practical_info", {}).get("transportation"):
            tips.append("대중교통을 활용하여 효율적으로 이동하세요.")
        
        if info.get("practical_info", {}).get("cuisine"):
            tips.append("현지 음식을 맛보는 것을 잊지 마세요.")
        
        return tips
    
    def _get_basic_destination_info(self, destination: str) -> Dict[str, Any]:
        """기본 여행지 정보 (정보를 찾을 수 없는 경우)"""
        return {
            "title": destination,
            "summary": f"{destination}에 대한 정보를 찾을 수 없습니다. 직접 방문하여 탐험해보세요!",
            "language": "ko",
            "url": "",
            "thumbnail": "",
            "coordinates": {},
            "page_id": None,
            "categories": ["여행지"],
            "type": "기타",
            "travel_info": {
                "best_time": "연중 언제든지",
                "climate": "정보 없음",
                "accessibility": "정보 없음",
                "safety": "일반적인 여행 주의사항 준수"
            },
            "attractions": ["현지 탐험"],
            "cultural_info": {
                "history": "직접 탐험하여 발견해보세요",
                "culture": "현지 문화를 체험해보세요",
                "traditions": "현지 전통을 알아보세요",
                "festivals": "현지 축제를 확인해보세요"
            },
            "practical_info": {
                "transportation": "현지 교통편을 확인해보세요",
                "accommodation": "숙박 시설을 미리 예약하세요",
                "cuisine": "현지 음식을 맛보세요",
                "shopping": "현지 특산품을 구매해보세요"
            },
            "travel_tips": [
                f"{destination} 방문 전 기본 정보를 확인하세요.",
                "현지 문화와 관습을 존중하세요.",
                "안전한 여행을 위해 주의사항을 준수하세요."
            ]
        }

# 전역 WikipediaService 인스턴스
wiki_service = WikipediaService()

# 기존 함수와의 호환성을 위한 래퍼
async def get_wikipedia_summary(title: str, lang: str = "ko") -> str | None:
    """기존 코드와의 호환성을 위한 함수"""
    info = await wiki_service.get_destination_info(title, lang)
    return info.get("summary") if info else None

async def get_destination_info(destination: str, lang: str = "ko") -> Dict[str, Any]:
    """여행지 종합 정보 조회"""
    return await wiki_service.get_destination_info(destination, lang)
