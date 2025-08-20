import logging
import traceback
from typing import Dict, Any, Optional, Union
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class TravelAgentError(Exception):
    """Travel Agent AI 시스템의 기본 예외 클래스"""
    
    def __init__(
        self,
        message: str,
        error_code: str = None,
        status_code: int = 500,
        details: Dict[str, Any] = None,
        user_message: str = None
    ):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.status_code = status_code
        self.details = details or {}
        self.user_message = user_message or message
        self.timestamp = datetime.now()
        self.error_id = str(uuid.uuid4())
        
        super().__init__(self.message)

class ValidationError(TravelAgentError):
    """데이터 검증 오류"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field, **details} if details else {"field": field}
        )

class APIKeyError(TravelAgentError):
    """API 키 관련 오류"""
    
    def __init__(self, service: str, message: str = None):
        super().__init__(
            message=message or f"{service} API 키가 설정되지 않았습니다",
            error_code="API_KEY_ERROR",
            status_code=400,
            details={"service": service}
        )

class ExternalAPIError(TravelAgentError):
    """외부 API 호출 오류"""
    
    def __init__(self, service: str, message: str, status_code: int = None):
        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            status_code=status_code or 502,
            details={"service": service}
        )

class RateLimitError(TravelAgentError):
    """API 호출 제한 오류"""
    
    def __init__(self, service: str, retry_after: int = None):
        super().__init__(
            message=f"{service} API 호출 제한에 도달했습니다",
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details={"service": service, "retry_after": retry_after}
        )

class TimeoutError(TravelAgentError):
    """API 호출 시간 초과 오류"""
    
    def __init__(self, service: str, timeout: int = None):
        super().__init__(
            message=f"{service} API 호출 시간이 초과되었습니다",
            error_code="TIMEOUT_ERROR",
            status_code=408,
            details={"service": service, "timeout": timeout}
        )

class ResourceNotFoundError(TravelAgentError):
    """리소스를 찾을 수 없음 오류"""
    
    def __init__(self, resource_type: str, resource_id: str = None):
        super().__init__(
            message=f"{resource_type}을(를) 찾을 수 없습니다",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )

class ConfigurationError(TravelAgentError):
    """설정 오류"""
    
    def __init__(self, config_key: str, message: str = None):
        super().__init__(
            message=message or f"설정 오류: {config_key}",
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details={"config_key": config_key}
        )

def create_error_response(
    error: TravelAgentError,
    request: Request = None,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """에러 응답 생성"""
    
    error_response = {
        "error": True,
        "error_code": error.error_code,
        "message": error.user_message,
        "status_code": error.status_code,
        "timestamp": error.timestamp.isoformat(),
        "error_id": error.error_id,
        "details": error.details
    }
    
    # 요청 정보 추가
    if request:
        error_response["request"] = {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None
        }
    
    # 개발 환경에서만 스택 트레이스 포함
    if include_traceback:
        error_response["traceback"] = traceback.format_exc()
    
    return error_response

def log_error(error: TravelAgentError, request: Request = None, context: Dict[str, Any] = None):
    """에러 로깅"""
    
    log_data = {
        "error_id": error.error_id,
        "error_code": error.error_code,
        "message": error.message,
        "status_code": error.status_code,
        "timestamp": error.timestamp.isoformat(),
        "details": error.details
    }
    
    if request:
        log_data["request"] = {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None,
            "headers": dict(request.headers)
        }
    
    if context:
        log_data["context"] = context
    
    # 에러 수준에 따른 로깅
    if error.status_code >= 500:
        logger.error(f"서버 오류 발생: {log_data}", exc_info=True)
    elif error.status_code >= 400:
        logger.warning(f"클라이언트 오류 발생: {log_data}")
    else:
        logger.info(f"정보성 오류: {log_data}")

def handle_external_api_error(
    service: str,
    error: Exception,
    fallback_data: Any = None,
    user_message: str = None
) -> Union[Any, ExternalAPIError]:
    """외부 API 오류 처리"""
    
    error_message = str(error)
    
    # 오류 유형별 처리
    if "rate limit" in error_message.lower() or "quota" in error_message.lower():
        raise RateLimitError(service)
    elif "timeout" in error_message.lower() or "timed out" in error_message.lower():
        raise TimeoutError(service)
    elif "not found" in error_message.lower() or "404" in error_message:
        raise ResourceNotFoundError(f"{service} 데이터")
    elif "unauthorized" in error_message.lower() or "401" in error_message:
        raise APIKeyError(service, f"{service} API 키가 유효하지 않습니다")
    elif "forbidden" in error_message.lower() or "403" in error_message:
        raise APIKeyError(service, f"{service} API 접근이 거부되었습니다")
    else:
        raise ExternalAPIError(service, f"{service} API 호출 중 오류가 발생했습니다: {error_message}")
    
    # 폴백 데이터가 있는 경우 반환 (현재는 도달하지 않음)
    return fallback_data

def create_fallback_response(
    original_error: Exception,
    fallback_data: Any,
    message: str = None
) -> Dict[str, Any]:
    """폴백 응답 생성"""
    
    return {
        "success": True,
        "message": message or "일부 데이터를 가져올 수 없어 기본 정보로 대체되었습니다",
        "data": fallback_data,
        "warnings": [
            f"원본 오류: {str(original_error)}",
            "폴백 데이터가 사용되었습니다"
        ],
        "timestamp": datetime.now().isoformat()
    }

def validate_api_keys(required_keys: Dict[str, str]) -> Dict[str, bool]:
    """필요한 API 키들의 상태 확인"""
    
    import os
    
    key_status = {}
    missing_keys = []
    
    for key_name, env_var in required_keys.items():
        key_value = os.getenv(env_var)
        key_status[key_name] = bool(key_value)
        
        if not key_value:
            missing_keys.append(key_name)
    
    if missing_keys:
        logger.warning(f"누락된 API 키: {missing_keys}")
    
    return key_status

def check_api_health(api_keys: Dict[str, bool]) -> Dict[str, Any]:
    """API 상태 확인"""
    
    health_status = {
        "overall": "healthy",
        "services": {},
        "warnings": [],
        "errors": []
    }
    
    for service, has_key in api_keys.items():
        if has_key:
            health_status["services"][service] = "available"
        else:
            health_status["services"][service] = "unavailable"
            health_status["warnings"].append(f"{service} API 키가 설정되지 않음")
    
    # 전체 상태 결정
    if health_status["errors"]:
        health_status["overall"] = "error"
    elif health_status["warnings"]:
        health_status["overall"] = "warning"
    
    return health_status

def create_user_friendly_message(error: Exception) -> str:
    """사용자 친화적인 에러 메시지 생성"""
    
    if isinstance(error, TravelAgentError):
        return error.user_message
    
    error_message = str(error).lower()
    
    # 일반적인 에러 메시지 변환
    if "timeout" in error_message:
        return "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
    elif "connection" in error_message:
        return "서버 연결에 실패했습니다. 인터넷 연결을 확인해주세요."
    elif "not found" in error_message:
        return "요청한 정보를 찾을 수 없습니다."
    elif "unauthorized" in error_message:
        return "인증이 필요합니다. API 키를 확인해주세요."
    elif "rate limit" in error_message:
        return "API 호출 제한에 도달했습니다. 잠시 후 다시 시도해주세요."
    else:
        return "예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

def format_error_for_logging(error: Exception, context: Dict[str, Any] = None) -> str:
    """로깅을 위한 에러 포맷팅"""
    
    error_info = {
        "type": type(error).__name__,
        "message": str(error),
        "timestamp": datetime.now().isoformat()
    }
    
    if context:
        error_info["context"] = context
    
    if hasattr(error, 'error_code'):
        error_info["error_code"] = error.error_code
    
    if hasattr(error, 'status_code'):
        error_info["status_code"] = error.status_code
    
    return str(error_info)
