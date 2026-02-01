import os
import json
from datetime import date
from groq import Groq

def get_intent_and_entities(user_message):
    try:
        # 1. Connect to Groq (Cloud API)
        # We do this INSIDE the function to prevent crashes if secrets aren't loaded yet
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("⚠️ Error: GROQ_API_KEY is missing.")
            return {"intent": "find_centres", "limit": 5}
            
        client = Groq(api_key=api_key)
        
        # 2. Get Context
        today = date.today()
        today_str = today.strftime("%Y-%m-%d") # e.g. "2024-04-24"
        current_year = today.year
        
        # 3. The "Brain" Instructions (Prompt)
        prompt = f"""
        You are a smart API that extracts JSON data from sports queries.
        
        CONTEXT:
        - Current Date: {today_str}
        - Current Year: {current_year}
        
        --- RULES ---
        1. INTENT: 
           - "count_academies" -> If user asks "how many", "total", "stats".
           - "check_slots" -> If user asks for "slots", "booking", "available", or mentions a specific date.
           - "get_address" -> If user asks for "address", "location".
           - "find_centres" -> Default for "near me", "nearby", "list".

        2. DATE HANDLING (CRITICAL):
           - Convert words like "Today", "Tomorrow" to YYYY-MM-DD.
           - Convert "24th April" or "24/04" to "{current_year}-04-24".
           - If the user says "24th April 2024", return "2024-04-24".
           - Return null if no date is mentioned.

        3. TARGET_NAME:
           - Extract specific names (e.g. "YMCA", "Black Dragon").
           - IGNORE generic words like "near me", "academy".

        --- EXAMPLES ---
        Query: "How many academies total?"
        JSON: {{ "intent": "count_academies", "date": null, "target_name": null, "limit": null }}

        Query: "slots for 24th April?"
        JSON: {{ "intent": "check_slots", "date": "{current_year}-04-24", "target_name": null, "limit": null }}
        
        Query: "academies near me"
        JSON: {{ "intent": "find_centres", "date": null, "target_name": null, "limit": 5 }}

        --- USER QUERY ---
        "{user_message}"
        
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
        # Fallback to Discovery if AI fails
        return {"intent": "find_centres", "limit": 5}