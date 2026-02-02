from db_config import get_db_connection

def find_nearby_centres(lat, lng, radius=60, limit=5): 
    conn = get_db_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            safe_limit = int(limit) if limit else 5
            
            # UPDATED QUERY: Uses GROUP BY to prevent duplicates
            query = """
            SELECT 
                academy_name as post_title,
                MIN(address) as address, 
                latitude,
                longitude,
                (
                    6371 * acos(
                        LEAST(1.0, GREATEST(-1.0,
                            cos(radians(%s)) * cos(radians(latitude)) * cos(radians(longitude) - radians(%s)) + 
                            sin(radians(%s)) * sin(radians(latitude))
                        ))
                    )
                ) AS distance
            FROM academy_master 
            GROUP BY academy_name, latitude, longitude
            HAVING distance < %s
            ORDER BY distance ASC
            LIMIT %s; 
            """
            cursor.execute(query, (lat, lng, lat, radius, safe_limit))
            return cursor.fetchall()
    finally:
        conn.close()

def find_centre_by_name(name_query):
    conn = get_db_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            # Simple lookup in the master table
            query = """
            SELECT DISTINCT academy_name as post_title, address, id
            FROM academy_master
            WHERE academy_name LIKE %s
            LIMIT 1
            """
            cursor.execute(query, (f"%{name_query}%",))
            return cursor.fetchone()
    finally:
        conn.close()

def get_total_academy_count():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(DISTINCT academy_name) FROM academy_master")
            result = cursor.fetchone()
            return result[0] if result else 0
    finally:
        conn.close()