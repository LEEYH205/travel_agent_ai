from __future__ import annotations
from ..schemas import DayPlan

def validate_plans(days: list[DayPlan]) -> list[str]:
    issues = []
    seen = set()
    for d in days:
        for p in d.morning + d.afternoon + d.evening:
            if p.name in seen:
                issues.append(f"Duplicate place: {p.name} on {d.date}")
            seen.add(p.name)
        total_walk = sum(t.travel_min for t in d.transfers)
        if total_walk > 120:
            issues.append(f"Long walking time ({total_walk} min) on {d.date}")
    return issues
