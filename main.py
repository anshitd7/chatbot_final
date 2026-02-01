from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from llm_handler import get_intent_and_entities
from services.center_service import find_nearby_centres, find_centre_by_name, get_total_academy_count
from services.slot_service import get_available_slots

app = FastAPI()
#
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    latitude: float
    longitude: float

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

@app.post("/chat")
async def chat_handler(req: ChatRequest):
    ai_data = get_intent_and_entities(req.message)
    intent = ai_data.get("intent")
    req_date = ai_data.get("date")
    req_time = ai_data.get("time") 
    target_name = ai_data.get("target_name")
    req_limit = ai_data.get("limit")
    limit = int(req_limit) if req_limit else 5

    if intent == "count_academies":
        count = get_total_academy_count()
        return {"reply": f"📊 **System Status**\nActive Academies: **{count}**"}

    if intent == "get_address" or (target_name and "address" in req.message.lower()):
        if target_name and target_name.lower() in ['near me', 'nearby', 'closest']:
            target_name = None
        search_name = target_name if target_name else req.message
        result = find_centre_by_name(search_name)
        if result:
            return {"reply": f"📍 **{result['post_title']}**\n{result['address']}"}
        return {"reply": "❌ Academy not found. Try asking for 'academies near me'."}

    if intent == "check_slots" or req_date or "slot" in req.message.lower():
        if not req_date:
            return {"reply": "📅 **Date Needed**\nPlease specify a date (e.g., Today, Tomorrow)."}

        pretty_date = datetime.strptime(req_date, "%Y-%m-%d").strftime("%A, %d %b")

        if target_name:
            academy = find_centre_by_name(target_name)
            if not academy:
                return {"reply": f"❌ Academy '**{target_name}**' not found."}
            
            # UPDATED: Passing 'post_title' (Name) instead of ID
            free_slots = get_available_slots(academy['post_title'], req_date)
            
            now = datetime.now()
            if req_date == now.strftime("%Y-%m-%d"):
                free_slots = [s for s in free_slots if s['raw_start'] > now]

            if not free_slots:
                return {"reply": f"❌ **{academy['post_title']}** is fully booked on {pretty_date}."}

            if req_time:
                req_dt = datetime.strptime(f"{req_date} {req_time}", "%Y-%m-%d %H:%M")
                match = next((s for s in free_slots if s['raw_start'].hour == req_dt.hour), None)
                if match:
                    return {"reply": f"✅ **Available**\n{academy['post_title']} has a slot at **{match['display']}**."}
                else:
                    return {"reply": f"❌ **Booked**\n{req_time} is taken at {academy['post_title']}."}
            else:
                 time_str = format_time_ranges(free_slots)
                 return {"reply": f"✅ **{academy['post_title']}**\n**Open:** {time_str}"}

        else:
            centres = find_nearby_centres(req.latitude, req.longitude, radius=60, limit=limit)
            if not centres:
                return {"reply": "🚫 No academies found within 60km."}

            report_blocks = []
            report_blocks.append(f"### 🗓️ Availability for {pretty_date}\n")
            any_found = False

            for c in centres:
                # UPDATED: Passing 'post_title' (Name)
                free_slots = get_available_slots(c['post_title'], req_date)
                
                now = datetime.now()
                if req_date == now.strftime("%Y-%m-%d"):
                    free_slots = [s for s in free_slots if s['raw_start'] > now]

                if free_slots:
                    any_found = True
                    dist = round(c['distance'], 1)
                    if req_time:
                         req_dt = datetime.strptime(f"{req_date} {req_time}", "%Y-%m-%d %H:%M")
                         match = next((s for s in free_slots if s['raw_start'].hour == req_dt.hour), None)
                         if match:
                             report_blocks.append(f"✅ **{c['post_title']}** ({dist} km)\n   • Open at **{match['display']}**")
                    else:
                        if len(free_slots) >= 18:
                            report_blocks.append(f"🟢 **{c['post_title']}** ({dist} km)\n   • Entire day available")
                        else:
                            range_str = format_time_ranges(free_slots)
                            report_blocks.append(f"🟡 **{c['post_title']}** ({dist} km)\n   • {range_str}")

            if not any_found:
                 return {"reply": f"⚠️ Fully booked nearby for {pretty_date}."}
            return {"reply": "\n\n".join(report_blocks)}

    centres = find_nearby_centres(req.latitude, req.longitude, radius=60, limit=limit)
    if not centres:
        return {"reply": "No academies found nearby."}
    
    header = f"Here are the **{len(centres)}** closest academies:\n\n"
    list_items = [f"📍 **{c['post_title']}**\n   {c['address']} ({round(c['distance'], 1)} km)" for c in centres]
    return {"reply": header + "\n\n".join(list_items)}