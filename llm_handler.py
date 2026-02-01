import os
import json
from datetime import date
from groq import Groq

# REMOVED: client = Groq(...) from here. 
# We don't want it to run immediately!

def get_intent_and_entities(user_message):
    # ADDED: Initialize the client INSIDE the function
    # This ensures secrets are loaded before we try to connect
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("⚠️ Error: GROQ_API_KEY is missing.")
            return {"intent": "find_centres", "limit": 5}
            
        client = Groq(api_key=api_key)
        
        today_str = date.today().strftime("%Y-%m-%d")
        
        prompt = f"""
        You are a strict entity extractor.
        Current Date: {today_str}
        
        Task: Extract INTENT, DATE, TIME, TARGET_NAME, and LIMIT.
        
        Rules:
        1. INTENT: "check_slots", "find_centres" (for general search), "get_address", "count_academies".
        2. TARGET_NAME: The specific name of the academy (e.g. "YMCA", "Black Dragon"). 
           *** CRITICAL: DO NOT extract generic location words like "near me", "nearby", "closest", "around here", "center", "academy" as the target_name. ***
           If the user says "academies near me", target_name must be null.
        3. LIMIT: Integer only. 
        
        User Query: "{user_message}"
        
        Return JSON only:
        {{
          "intent": "string",
          "date": "YYYY-MM-DD" or null,
          "time": "HH:MM" or null,
          "limit": integer or null,
          "target_name": "string" or null
        }}
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