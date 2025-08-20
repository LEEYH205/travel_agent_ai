import asyncio
import json
import hashlib
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
from functools import wraps
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class CacheManager:
    """캐시 관리자"""
    
    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 100):
        self.cache_dir = Path(cache_dir)
        self.max_size_mb = max_size_mb
        self.cache_dir.mkdir(exist_ok=True)
        
        # 메모리 캐시 (빠른 접근용)
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.memory_cache_size = 0
        self.max_memory_items = 1000
        
        # 캐시 통계
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0
        }
    
    def _generate_cache_key(self, *args, **kwargs) -> str:
        """캐시 키 생성"""
        # 인자들을 문자열로 변환하여 해시 생성
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """캐시 파일 경로 반환"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_data: Dict[str, Any]) -> bool:
        """캐시 유효성 검사"""
        if "expires_at" not in cache_data:
            return False
        
        expires_at = datetime.fromisoformat(cache_data["expires_at"])
        return datetime.now() < expires_at
    
    def _cleanup_expired_cache(self):
        """만료된 캐시 정리"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    if not self._is_cache_valid(cache_data):
                        cache_file.unlink()
                        logger.debug(f"만료된 캐시 파일 삭제: {cache_file}")
                        
                except (json.JSONDecodeError, KeyError):
                    # 손상된 캐시 파일 삭제
                    cache_file.unlink()
                    logger.warning(f"손상된 캐시 파일 삭제: {cache_file}")
                    
        except Exception as e:
            logger.error(f"캐시 정리 중 오류: {e}")
    
    def _check_cache_size(self):
        """캐시 크기 확인 및 정리"""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
            total_size_mb = total_size / (1024 * 1024)
            
            if total_size_mb > self.max_size_mb:
                # 가장 오래된 캐시 파일들부터 삭제
                cache_files = []
                for cache_file in self.cache_dir.glob("*.json"):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        created_at = datetime.fromisoformat(cache_data.get("created_at", "1970-01-01T00:00:00"))
                        cache_files.append((cache_file, created_at))
                        
                    except (json.JSONDecodeError, KeyError):
                        cache_file.unlink()
                        continue
                
                # 생성 시간순으로 정렬하여 오래된 것부터 삭제
                cache_files.sort(key=lambda x: x[1])
                
                for cache_file, _ in cache_files:
                    if total_size_mb <= self.max_size_mb * 0.8:  # 80%까지 줄임
                        break
                    
                    cache_file.unlink()
                    total_size_mb -= cache_file.stat().st_size / (1024 * 1024)
                    self.stats["evictions"] += 1
                    
                logger.info(f"캐시 크기 정리 완료: {total_size_mb:.2f}MB")
                
        except Exception as e:
            logger.error(f"캐시 크기 확인 중 오류: {e}")
    
    async def get(self, cache_key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        self.stats["total_requests"] += 1
        
        # 메모리 캐시에서 먼저 확인
        if cache_key in self.memory_cache:
            cache_data = self.memory_cache[cache_key]
            if self._is_cache_valid(cache_data):
                self.stats["hits"] += 1
                logger.debug(f"메모리 캐시 히트: {cache_key}")
                return cache_data["data"]
            else:
                # 만료된 메모리 캐시 제거
                del self.memory_cache[cache_key]
                self.memory_cache_size -= 1
        
        # 파일 캐시에서 확인
        cache_file = self._get_cache_file_path(cache_key)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if self._is_cache_valid(cache_data):
                    # 메모리 캐시에 추가
                    self._add_to_memory_cache(cache_key, cache_data)
                    self.stats["hits"] += 1
                    logger.debug(f"파일 캐시 히트: {cache_key}")
                    return cache_data["data"]
                else:
                    # 만료된 파일 캐시 삭제
                    cache_file.unlink()
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"캐시 파일 읽기 오류: {cache_key}, {e}")
                cache_file.unlink()
        
        self.stats["misses"] += 1
        logger.debug(f"캐시 미스: {cache_key}")
        return None
    
    def _add_to_memory_cache(self, cache_key: str, cache_data: Dict[str, Any]):
        """메모리 캐시에 데이터 추가"""
        # 메모리 캐시 크기 제한 확인
        if len(self.memory_cache) >= self.max_memory_items:
            # 가장 오래된 항목 제거
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k].get("created_at", "1970-01-01T00:00:00"))
            del self.memory_cache[oldest_key]
            self.memory_cache_size -= 1
        
        self.memory_cache[cache_key] = cache_data
        self.memory_cache_size += 1
    
    async def set(self, cache_key: str, data: Any, ttl_seconds: int = 3600):
        """캐시에 데이터 저장"""
        try:
            now = datetime.now()
            expires_at = now + timedelta(seconds=ttl_seconds)
            
            cache_data = {
                "data": data,
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "ttl_seconds": ttl_seconds
            }
            
            # 메모리 캐시에 저장
            self._add_to_memory_cache(cache_key, cache_data)
            
            # 파일 캐시에 저장
            cache_file = self._get_cache_file_path(cache_key)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"캐시 저장 완료: {cache_key}, TTL: {ttl_seconds}초")
            
            # 주기적으로 캐시 정리
            if self.stats["total_requests"] % 100 == 0:
                self._cleanup_expired_cache()
                self._check_cache_size()
                
        except Exception as e:
            logger.error(f"캐시 저장 중 오류: {cache_key}, {e}")
    
    async def delete(self, cache_key: str):
        """캐시에서 데이터 삭제"""
        try:
            # 메모리 캐시에서 제거
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
                self.memory_cache_size -= 1
            
            # 파일 캐시에서 제거
            cache_file = self._get_cache_file_path(cache_key)
            if cache_file.exists():
                cache_file.unlink()
            
            logger.debug(f"캐시 삭제 완료: {cache_key}")
            
        except Exception as e:
            logger.error(f"캐시 삭제 중 오류: {cache_key}, {e}")
    
    async def clear(self):
        """모든 캐시 정리"""
        try:
            # 메모리 캐시 정리
            self.memory_cache.clear()
            self.memory_cache_size = 0
            
            # 파일 캐시 정리
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            
            logger.info("모든 캐시 정리 완료")
            
        except Exception as e:
            logger.error(f"캐시 정리 중 오류: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        hit_rate = (self.stats["hits"] / max(self.stats["total_requests"], 1)) * 100
        
        return {
            **self.stats,
            "hit_rate_percent": round(hit_rate, 2),
            "memory_cache_size": self.memory_cache_size,
            "memory_cache_items": len(self.memory_cache),
            "file_cache_size_mb": sum(f.stat().st_size for f in self.cache_dir.glob("*.json")) / (1024 * 1024)
        }

# 전역 캐시 매니저 인스턴스
cache_manager = CacheManager()

def cache_result(ttl_seconds: int = 3600, key_prefix: str = ""):
    """함수 결과를 캐시하는 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{key_prefix}:{func.__name__}:{cache_manager._generate_cache_key(*args, **kwargs)}"
            
            # 캐시에서 결과 확인
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 함수 실행
            result = await func(*args, **kwargs)
            
            # 결과를 캐시에 저장
            await cache_manager.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator

def cache_sync_result(ttl_seconds: int = 3600, key_prefix: str = ""):
    """동기 함수 결과를 캐시하는 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{key_prefix}:{func.__name__}:{cache_manager._generate_cache_key(*args, **kwargs)}"
            
            # 캐시에서 결과 확인 (동기적으로)
            try:
                cache_file = cache_manager._get_cache_file_path(cache_key)
                if cache_file.exists():
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    if cache_manager._is_cache_valid(cache_data):
                        cache_manager.stats["hits"] += 1
                        return cache_data["data"]
            except Exception:
                pass
            
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 결과를 캐시에 저장 (비동기적으로)
            asyncio.create_task(cache_manager.set(cache_key, result, ttl_seconds))
            
            return result
        
        return wrapper
    return decorator

class APICache:
    """API별 캐싱 전략"""
    
    def __init__(self):
        self.cache_manager = cache_manager
        
        # API별 TTL 설정
        self.ttl_config = {
            "weather": 1800,      # 30분 (날씨는 자주 변함)
            "places": 86400,      # 24시간 (장소 정보는 자주 변하지 않음)
            "directions": 3600,   # 1시간 (교통 상황은 자주 변함)
            "wiki": 604800,       # 7일 (위키 정보는 자주 변하지 않음)
            "itinerary": 3600,    # 1시간 (일정은 사용자별로 다름)
        }
    
    async def get_cached_weather(self, destination: str, date: str) -> Optional[Dict[str, Any]]:
        """캐시된 날씨 정보 조회"""
        cache_key = f"weather:{destination}:{date}"
        return await self.cache_manager.get(cache_key)
    
    async def cache_weather(self, destination: str, date: str, weather_data: Dict[str, Any]):
        """날씨 정보 캐시"""
        cache_key = f"weather:{destination}:{date}"
        await self.cache_manager.set(cache_key, weather_data, self.ttl_config["weather"])
    
    async def get_cached_places(self, destination: str, interests: List[str]) -> Optional[List[Dict[str, Any]]]:
        """캐시된 장소 정보 조회"""
        interests_str = ",".join(sorted(interests))
        cache_key = f"places:{destination}:{interests_str}"
        return await self.cache_manager.get(cache_key)
    
    async def cache_places(self, destination: str, interests: List[str], places_data: List[Dict[str, Any]]):
        """장소 정보 캐시"""
        interests_str = ",".join(sorted(interests))
        cache_key = f"places:{destination}:{interests_str}"
        await self.cache_manager.set(cache_key, places_data, self.ttl_config["places"])
    
    async def get_cached_directions(self, origin: str, destination: str, mode: str) -> Optional[Dict[str, Any]]:
        """캐시된 경로 정보 조회"""
        cache_key = f"directions:{origin}:{destination}:{mode}"
        return await self.cache_manager.get(cache_key)
    
    async def cache_directions(self, origin: str, destination: str, mode: str, directions_data: Dict[str, Any]):
        """경로 정보 캐시"""
        cache_key = f"directions:{origin}:{destination}:{mode}"
        await self.cache_manager.set(cache_key, directions_data, self.ttl_config["directions"])
    
    async def get_cached_wiki(self, destination: str, language: str) -> Optional[Dict[str, Any]]:
        """캐시된 위키 정보 조회"""
        cache_key = f"wiki:{destination}:{language}"
        return await self.cache_manager.get(cache_key)
    
    async def cache_wiki(self, destination: str, language: str, wiki_data: Dict[str, Any]):
        """위키 정보 캐시"""
        cache_key = f"wiki:{destination}:{language}"
        await self.cache_manager.set(cache_key, wiki_data, self.ttl_config["wiki"])
    
    async def get_cached_itinerary(self, preferences_hash: str) -> Optional[Dict[str, Any]]:
        """캐시된 여행 일정 조회"""
        cache_key = f"itinerary:{preferences_hash}"
        return await self.cache_manager.get(cache_key)
    
    async def cache_itinerary(self, preferences_hash: str, itinerary_data: Dict[str, Any]):
        """여행 일정 캐시"""
        cache_key = f"itinerary:{preferences_hash}"
        await self.cache_manager.set(cache_key, itinerary_data, self.ttl_config["itinerary"])
    
    def generate_preferences_hash(self, preferences: Dict[str, Any]) -> str:
        """사용자 선호도 해시 생성"""
        # 민감하지 않은 정보만 포함하여 해시 생성
        key_data = {
            "destination": preferences.get("destination"),
            "interests": sorted(preferences.get("interests", [])),
            "pace": preferences.get("pace"),
            "budget_level": preferences.get("budget_level"),
            "party": preferences.get("party")
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()

# 전역 API 캐시 인스턴스
api_cache = APICache()
