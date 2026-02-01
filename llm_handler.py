import os
import json
from datetime import date
from groq import Groq

def get_intent_and_entities(user_message):
    try:
        # 1. Secure Connection
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("⚠️ Error: GROQ_API_KEY is missing.")
            return {"intent": "find_centres", "limit": 5}
            
        client = Groq(api_key=api_key)
        
        # 2. Context for the AI
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        current_year = today.year
        
        # 3. THE UPGRADED PROMPT
        prompt = f"""
        You are a smart API that extracts INTENT and ENTITIES.
        
        CONTEXT:
        - Current Date: {today_str}
        - Current Year: {current_year}
        
        --- STEP 1: DETERMINE INTENT ---
        - "count_academies": If user asks "how many", "total", "stats", "count".
        - "check_slots": If user mentions "slot", "booking", "available", or a specific date.
        - "get_address": If user asks for "address", "where is".
        - "find_centres": Default for "near me", "list academies", "closest".

        --- STEP 2: EXTRACT ENTITIES ---
        - DATE: Must be YYYY-MM-DD format.
          * Convert "24th April" -> "{current_year}-04-24"
          * Convert "Today" -> "{today_str}"
          * If no date is found, return null.
        - TARGET_NAME: Specific academy names only. "Near me" is NOT a name.
        - LIMIT: Integer only.
        
        --- FEW-SHOT EXAMPLES (Do exactly this!) ---
        Query: "How many academies total?"
        JSON: {{ "intent": "count_academies", "date": null, "target_name": null, "limit": null }}
        
        Query: "slots for 24th April"
        JSON: {{ "intent": "check_slots", "date": "{current_year}-04-24", "target_name": null, "limit": null }}

        Query: "academies near me"
        JSON: {{ "intent": "find_centres", "date": null, "target_name": null, "limit": 5 }}

        --- YOUR TASK ---
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
        # Safe fallback
        return {"intent": "find_centres", "limit": 5}