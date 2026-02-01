import streamlit as st
import requests
import geocoder 

# --- CONFIGURATION ---
# 🔴 REPLACE THIS with your actual Railway App URL after deployment
# Example: "https://web-production-1234.up.railway.app/chat"
API_URL = "strong-communication-production-b242.up.railway.app"

st.set_page_config(page_title="TIDA Sports", page_icon="🎾", layout="centered")

# Initialize Session State
if "user_lat" not in st.session_state:
    st.session_state.user_lat = 30.7570
if "user_lng" not in st.session_state:
    st.session_state.user_lng = 76.7800

st.markdown("""
<style>
    .stChatMessage { padding: 1rem; border-radius: 10px; margin-bottom: 10px; }
    .stButton button { border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

# --- HELPER: ROBUST GEOLOCATION ---
def get_current_location():
    """Tries ipapi first (fast), falls back to geocoder (robust)"""
    # Priority 1: ipapi.co
    try:
        response = requests.get('https://ipapi.co/json/', timeout=3)
        if response.status_code == 200:
            data = response.json()
            return data.get('latitude'), data.get('longitude'), data.get('city')
    except:
        pass 

    # Priority 2: Geocoder Library (Fallback)
    try:
        g = geocoder.ip('me')
        if g.latlng:
            return g.latlng[0], g.latlng[1], g.city
    except Exception:
        pass 
        
    return None, None, None

# --- SIDEBAR ---
with st.sidebar:
    st.header("📍 Your Location")
    
    if st.button("📍 Use My Current Location"):
        with st.spinner("Locating..."):
            lat, lng, city = get_current_location()
            
            if lat and lng:
                st.session_state.user_lat = float(lat)
                st.session_state.user_lng = float(lng)
                st.success(f"📍 Found you in {city}!")
            else:
                st.error("⚠️ Could not detect location. Please enter coordinates manually.")

    lat = st.number_input("Latitude", key="user_lat", format="%.4f")
    lng = st.number_input("Longitude", key="user_lng", format="%.4f")
    
    st.divider()
    st.info(f"Connected to:\n{API_URL}")

# --- MAIN CHAT ---
st.title("🎾 TIDA Sports Assistant")
st.markdown("Welcome! I can help you find slots, check availability, and locate academies.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! 👋 How can I help you play today?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def ask_bot(prompt_text):
    st.session_state.messages.append({"role": "user", "content": prompt_text})
    with st.chat_message("user"):
        st.markdown(prompt_text)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                payload = {
                    "message": prompt_text, 
                    "latitude": st.session_state.user_lat, 
                    "longitude": st.session_state.user_lng
                }
                # Keep 60s timeout for cloud latency
                resp = requests.post(API_URL, json=payload, timeout=60) 
                
                if resp.status_code == 200:
                    reply = resp.json().get("reply")
                else:
                    reply = f"⚠️ Server Error: {resp.status_code}"
            except requests.exceptions.ConnectionError:
                reply = "⚠️ Connection Failed. Please make sure the backend is running."
            except requests.exceptions.ReadTimeout:
                reply = "⚠️ The AI took too long to respond. Please try again."
            except Exception as e:
                reply = f"⚠️ Error: {str(e)}"
            
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

st.write("") 
cols = st.columns(3)
if cols[0].button("📅 Slots for Today"):
    ask_bot("Check slots for today")
if cols[1].button("📍 Academies Near Me"):
    ask_bot("Find academies near me")
if cols[2].button("📊 Stats"):
    ask_bot("How many academies total?")

if user_input := st.chat_input("Type your question..."):
    ask_bot(user_input)