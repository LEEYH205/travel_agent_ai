#!/usr/bin/env python3
"""
Travel Agent AI - Hugging Face Spaces 배포용 메인 앱
이 파일은 Hugging Face Spaces에서 자동으로 인식됩니다.
"""

import os
import sys

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 백엔드 앱 import
from travel_agent.backend.main import app

# Hugging Face Spaces에서 실행할 때 필요한 설정
if __name__ == "__main__":
    import uvicorn
    
    # 환경 변수에서 포트 가져오기 (Hugging Face Spaces에서 설정)
    port = int(os.environ.get("PORT", 7860))
    
    # 호스트를 0.0.0.0으로 설정하여 외부 접근 허용
    uvicorn.run(
        "travel_agent.backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=False  # 프로덕션에서는 reload 비활성화
    )
