from __future__ import annotations
from ..schemas import Tips

def get_local_tips(locale: str = "ko_KR") -> Tips:
    return Tips(
        etiquette=["현지 식당의 예약 문화를 존중하세요.", "종교 시설 방문 시 복장 규정을 확인하세요."],
        packing=["편한 신발", "보조 배터리", "현지용 유심/ESIM"],
        safety=["소매치기 주의", "늦은 밤 외진 골목 피하기"]
    )
