import streamlit as st
import httpx
from datetime import date

st.set_page_config(page_title="Agent Travel Planner", layout="wide")
st.title("🧭 Agent Travel Planner (MVP)")

with st.form("prefs"):
    destination = st.text_input("Destination", "Paris")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", value=date.today())
    with col2:
        end_date = st.date_input("End date", value=date.today())
    interests = st.multiselect("Interests", ["food","history","art","nature","shopping"], default=["history","food"])
    pace = st.selectbox("Pace", ["relaxed","balanced","packed"], index=1)
    budget = st.selectbox("Budget", ["low","mid","high"], index=1)
    party = st.number_input("# of travelers", 1, 10, 1)
    mode = st.selectbox("Orchestrator", ["graph","crew"], index=0)
    backend_url = st.text_input("Backend URL", "http://localhost:8000")
    submitted = st.form_submit_button("Generate Plan")

if submitted:
    payload = {
        "destination": destination,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "interests": interests,
        "pace": pace,
        "budget_level": budget,
        "party": int(party),
        "locale": "ko_KR",
    }
    with st.spinner("Planning your trip..."):
        try:
            r = httpx.post(f"{backend_url}/plan", params={"mode": mode}, json=payload, timeout=120.0)
            r.raise_for_status()
            data = r.json()["itinerary"]
        except Exception as e:
            st.error(f"Error: {e}")
        else:
            st.success("Plan generated!")
            st.subheader("Summary")
            st.write(data["summary"])

            for day in data["days"]:
                with st.expander(f"📅 {day['date']}"):
                    st.markdown("**Morning**")
                    for p in day["morning"]:
                        st.write(f"- {p['name']} ({p['category']}) — {p.get('description','')}")
                    st.markdown("**Afternoon**")
                    for p in day["afternoon"]:
                        st.write(f"- {p['name']} ({p['category']}) — {p.get('description','')}")
                    st.markdown("**Evening**")
                    for p in day["evening"]:
                        st.write(f"- {p['name']} ({p['category']}) — {p.get('description','')}")
                    if day["transfers"]:
                        st.markdown("**Transfers**")
                        for t in day["transfers"]:
                            st.write(f"{t['from_place']} → {t['to_place']} • {t['distance_km']} km • ~{t['travel_min']} min")

            st.subheader("Local Tips")
            tips = data["tips"]
            for k in ["etiquette","packing","safety"]:
                if tips.get(k):
                    st.markdown(f"**{k.title()}**")
                    for item in tips[k]:
                        st.write("- ", item)
