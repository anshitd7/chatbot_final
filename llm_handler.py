import os
import json
from datetime import date
from groq import Groq

def get_intent_and_entities(user_message):
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return {"intent": "find_centres", "limit": 5}
            
        client = Groq(api_key=api_key)
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        current_year = today.year
        
        # --- STRICTER PROMPT ---
        prompt = f"""
        You are a smart API that extracts Intent and Entities from sports queries.
        
        CONTEXT:
        - Current Date: {today_str}
        - Current Year: {current_year}
        
        --- 1. DETERMINE INTENT ---
        - "count_academies": If user asks "how many", "total", "stats", "count".
        - "check_slots": If user mentions "slot", "booking", "available", or a specific date/time.
        - "get_address": If user asks for "address", "where is", "location of [Specific Name]".
        - "find_centres": Default for "near me", "list academies", "closest".

        --- 2. EXTRACT ENTITIES ---
        - DATE: Must be YYYY-MM-DD. 
          * Convert "24th April" -> "{current_year}-04-24"
          * Convert "tomorrow" -> (Calculate based on {today_str})
          * If year is missing, use {current_year}.
        - TARGET_NAME: Specific academy name only (e.g. "Black Dragon"). "Near me" is NOT a name.
        - TIME: HH:MM format (24hr).
        
        --- FEW-SHOT EXAMPLES (Follow These!) ---
        Query: "How many academies total?"
        JSON: {{ "intent": "count_academies", "date": null, "target_name": null, "limit": null }}
        
        Query: "slot available on 24th april 2024?"
        JSON: {{ "intent": "check_slots", "date": "2024-04-24", "target_name": null, "limit": null }}

        Query: "academies near me"
        JSON: {{ "intent": "find_centres", "date": null, "target_name": null, "limit": 5 }}

        --- YOUR TASK ---
        User Query: "{user_message}"
        
        Return the JSON object only.
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