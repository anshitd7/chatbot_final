from datetime import datetime, timedelta
from db_config import get_db_connection

def is_overlapping(start_A, end_A, start_B, end_B):
    return start_A < end_B and end_A > start_B

def get_available_slots(academy_name, date_str):
    """
    Checks the 'academy_master' table for existing bookings to calculate free slots.
    """
    conn = get_db_connection()
    bookings = []
    
    try:
        with conn.cursor(dictionary=True) as cursor:
            # Check for bookings matching the Name and Date
            # We use academy_name because IDs might vary in the master table
            query = """
            SELECT slot_start, slot_end
            FROM academy_master
            WHERE academy_name = %s
              AND DATE(slot_start) = %s
            """
            cursor.execute(query, (academy_name, date_str))
            bookings = cursor.fetchall()
            
    finally:
        conn.close()

    # --- Standard Logic to Calculate Free Slots (06:00 to 23:59) ---
    available_slots = []
    current_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Check 18 hours: 6 AM to 11 PM
    for hour in range(6, 24): 
        slot_start = current_date_obj.replace(hour=hour, minute=0, second=0)
        slot_end = slot_start + timedelta(hours=1)
        
        is_blocked = False
        
        for b in bookings:
            # Handle string vs datetime objects safely
            b_start = b['slot_start'] if isinstance(b['slot_start'], datetime) else datetime.strptime(str(b['slot_start']), "%Y-%m-%d %H:%M:%S")
            b_end = b['slot_end'] if isinstance(b['slot_end'], datetime) else datetime.strptime(str(b['slot_end']), "%Y-%m-%d %H:%M:%S")
            
            if is_overlapping(slot_start, slot_end, b_start, b_end):
                is_blocked = True
                break 
        
        if not is_blocked:
            available_slots.append({
                "raw_start": slot_start,
                "display": slot_start.strftime("%I:%M %p")
            })
            
    return available_slots