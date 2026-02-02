import os
import json
from datetime import date
from groq import Groq
import streamlit as st  # Imported to show errors on screen

def get_intent_and_entities(user_message):
    try:
        # 1. Check API Key
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            st.error("CRITICAL ERROR: GROQ_API_KEY is missing from Secrets!")
            return {"intent": "find_centres", "limit": 5}
            
        # 2. Connect to Groq
        client = Groq(api_key=api_key)
        
        # 3. Context
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        current_year = today.year
        
        # 4. Strict Prompt
        prompt = f"""
        You are a smart API. Extract JSON data.
        CONTEXT: Current Date: {today_str}, Year: {current_year}
        
        RULES:
        - "count_academies": If user asks "how many", "total", "stats".
        - "check_slots": If user asks for "slots" or a specific date.
        - "get_address": If user asks for "address".
        - "find_centres": Default/Fallback.
        
        DATE RULES:
        - Convert "24th April" to "{current_year}-04-24".
        - Convert "Today" to "{today_str}".
        
        QUERY: "{user_message}"
        
        Return JSON object only.
        """
        
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
        
    except Exception as e:
        # THIS IS THE FIX: Print the actual error to the screen!
        st.error(f"⚠️ AI BRAIN FAILURE: {str(e)}")
        return {"intent": "find_centres", "limit": 5}