from fastapi.testclient import TestClient
from travel_agent.backend.main import app

client = TestClient(app)

def test_plan_smoke():
    payload = {
        "destination": "Paris",
        "start_date": "2025-10-01",
        "end_date": "2025-10-02",
        "interests": ["history","food"],
        "pace": "balanced",
        "budget_level": "mid",
        "party": 2,
        "locale": "ko_KR"
    }
    r = client.post("/plan", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "itinerary" in data
    assert len(data["itinerary"]["days"]) >= 1
