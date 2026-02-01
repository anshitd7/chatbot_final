import streamlit as st
import geocoder 
from services.center_service import find_nearby_centres, find_centre_by_name, get_total_academy_count
from services.slot_service import get_available_slots
from llm_handler import get_intent_and_entities
from datetime import datetime, timedelta

st.set_page_config(page_title="TIDA Sports", page_icon="🎾", layout="centered")

# Initialize Session State
if "user_lat" not in st.session_state:
    st.session_state.user_lat = 30.7570
if "user_lng" not in st.session_state:
    st.session_state.user_lng = 76.7800
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! 👋 How can I help you play today?"}
    ]

# --- HELPER: FORMAT TIME RANGES ---
def format_time_ranges(slots):
    if not slots: return "No slots"
    sorted_slots = sorted(slots, key=lambda x: x['raw_start'])
    if not sorted_slots: return ""
    ranges = []
    range_start = sorted_slots[0]['raw_start']
    last_slot_start = sorted_slots[0]['raw_start']
    for i in range(1, len(sorted_slots)):
        current = sorted_slots[i]['raw_start']
        if (current - last_slot_start).total_seconds() == 3600:
            last_slot_start = current 
        else:
            range_end = last_slot_start + timedelta(hours=1)
            ranges.append(f"{range_start.strftime('%I:%M %p')} - {range_end.strftime('%I:%M %p')}")
            range_start = current
            last_slot_start = current
    range_end = last_slot_start + timedelta(hours=1)
    ranges.append(f"{range_start.strftime('%I:%M %p')} - {range_end.strftime('%I:%M %p')}")
    return ", ".join(ranges)

# --- DIRECT LOGIC HANDLER (No API needed) ---
def process_user_message(message, lat, lng):
    ai_data = get_intent_and_entities(message)
    intent = ai_data.get("intent")
    req_date = ai_data.get("date")
    req_time = ai_data.get("time") 
    target_name = ai_data.get("target_name")
    req_limit = ai_data.get("limit")
    limit = int(req_limit) if req_limit else 5

    # CASE: Stats
    if intent == "count_academies":
        return f"📊 **System Status**\nActive Academies: **{get_total_academy_count()}**"

    # CASE: Address
    if intent == "get_address" or (target_name and "address" in message.lower()):
        if target_name and target_name.lower() in ['near me', 'nearby', 'closest']:
            target_name = None
        search_name = target_name if target_name else message
        result = find_centre_by_name(search_name)
        if result:
            return f"📍 **{result['post_title']}**\n{result['address']}"
        return "❌ Academy not found. Try asking for 'academies near me'."

    # CASE: Check Slots
    if intent == "check_slots" or req_date or "slot" in message.lower():
        if not req_date:
            return "📅 **Date Needed**\nPlease specify a date (e.g., Today, Tomorrow)."

        pretty_date = datetime.strptime(req_date, "%Y-%m-%d").strftime("%A, %d %b")

        if target_name:
            academy = find_centre_by_name(target_name)
            if not academy:
                return f"❌ Academy '**{target_name}**' not found."
            
            free_slots = get_available_slots(academy['post_title'], req_date)
            now = datetime.now()
            if req_date == now.strftime("%Y-%m-%d"):
                free_slots = [s for s in free_slots if s['raw_start'] > now]

            if not free_slots:
                return f"❌ **{academy['post_title']}** is fully booked on {pretty_date}."

            if req_time:
                req_dt = datetime.strptime(f"{req_date} {req_time}", "%Y-%m-%d %H:%M")
                match = next((s for s in free_slots if s['raw_start'].hour == req_dt.hour), None)
                if match:
                    return f"✅ **Available**\n{academy['post_title']} has a slot at **{match['display']}**."
                else:
                    return f"❌ **Booked**\n{req_time} is taken at {academy['post_title']}."
            else:
                 time_str = format_time_ranges(free_slots)
                 return f"✅ **{academy['post_title']}**\n**Open:** {time_str}"

        else:
            # Broad Search
            centres = find_nearby_centres(lat, lng, radius=60, limit=limit)
            if not centres:
                return "🚫 No academies found within 60km."

            report_blocks = [f"### 🗓️ Availability for {pretty_date}\n"]
            any_found = False

            for c in centres:
                free_slots = get_available_slots(c['post_title'], req_date)
                now = datetime.now()
                if req_date == now.strftime("%Y-%m-%d"):
                    free_slots = [s for s in free_slots if s['raw_start'] > now]

                if free_slots:
                    any_found = True
                    dist = round(c['distance'], 1)
                    if len(free_slots) >= 18:
                        report_blocks.append(f"🟢 **{c['post_title']}** ({dist} km)\n   • Entire day available")
                    else:
                        range_str = format_time_ranges(free_slots)
                        report_blocks.append(f"🟡 **{c['post_title']}** ({dist} km)\n   • {range_str}")

            if not any_found:
                 return f"⚠️ Fully booked nearby for {pretty_date}."
            return "\n\n".join(report_blocks)

    # CASE: General Discovery
    centres = find_nearby_centres(lat, lng, radius=60, limit=limit)
    if not centres:
        return "No academies found nearby."
    
    header = f"Here are the **{len(centres)}** closest academies:\n\n"
    list_items = [f"📍 **{c['post_title']}**\n   {c['address']} ({round(c['distance'], 1)} km)" for c in centres]
    return header + "\n\n".join(list_items)

# --- SIDEBAR & LOCATION ---
with st.sidebar:
    st.header("📍 Your Location")
    if st.button("📍 Use My Current Location"):
        try:
            g = geocoder.ip('me')
            if g.latlng:
                st.session_state.user_lat = float(g.latlng[0])
                st.session_state.user_lng = float(g.latlng[1])
                st.success(f"Found: {g.city}")
        except:
            st.error("Location failed.")
            
    st.number_input("Lat", key="user_lat", format="%.4f")
    st.number_input("Lng", key="user_lng", format="%.4f")

# --- CHAT UI ---
st.title("🎾 TIDA Sports Assistant")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def ask_bot(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # CALL FUNCTION DIRECTLY - NO API REQUEST
            reply = process_user_message(prompt, st.session_state.user_lat, st.session_state.user_lng)
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

if user_input := st.chat_input("Type your question..."):
    ask_bot(user_input)