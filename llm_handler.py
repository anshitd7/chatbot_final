import os
import json
from datetime import date
from groq import Groq

def get_intent_and_entities(user_message):
    try:
        # Check if key exists before connecting
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("⚠️ Error: GROQ_API_KEY is missing from secrets.")
            return {"intent": "find_centres", "limit": 5}
            
        # Connect to Groq now
        client = Groq(api_key=api_key)
        
        today_str = date.today().strftime("%Y-%m-%d")
        
        # --- IMPROVED PROMPT WITH EXAMPLES ---
        prompt = f"""
        You are a strict entity extractor API. 
        Current Date: {today_str}
        
        Task: Extract INTENT, DATE, TIME, TARGET_NAME, and LIMIT from the User Query.
        
        --- RULES ---
        1. INTENT: "check_slots", "find_centres", "get_address", "count_academies".
        2. DATE: Must be in "YYYY-MM-DD" format. 
           - Convert "today", "tomorrow", "next friday" to actual dates based on Current Date.
           - Convert "24th April", "April 24", "24/04" to "2024-04-24" (Use current year 2024 unless specified).
           - If no date is found, return null.
        3. TARGET_NAME: Specific academy names only (e.g. "YMCA"). Generic words like "near me" = null.
        
        --- EXAMPLES ---
        Query: "slots for 24th april?"
        Result: {{ "intent": "check_slots", "date": "2024-04-24", "target_name": null, "limit": null, "time": null }}
        
        Query: "academies near me"
        Result: {{ "intent": "find_centres", "date": null, "target_name": null, "limit": 5, "time": null }}

        --- ACTUAL QUERY ---
        User Query: "{user_message}"
        
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
        print(f"LLM Error: {e}")
        return {"intent": "find_centres", "limit": 5}