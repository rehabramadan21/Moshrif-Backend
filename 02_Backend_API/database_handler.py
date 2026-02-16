import sqlite3
import pandas as pd
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseHandler:
    def __init__(self):
        # تحديد مسار قاعدة البيانات بدقة
        self.BASE_DIR = Path(__file__).resolve().parent.parent
        self.DB_PATH = self.BASE_DIR / "03_Database" / "attendance.db"

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.DB_PATH)

    def mark_attendance(self, student_id: str, course_code: str) -> Dict[str, str]:
            """
            Marks a student as present IF they are registered.
            Returns student email on success for notification.
            """
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%Y-%m-%d %H:%M:%S")

            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    # 1. Validation: Check if student exists AND Get Email
                    cursor.execute("SELECT name, email FROM students WHERE student_id = ?", (student_id,))
                    student = cursor.fetchone()
                    
                    if not student:
                        logger.warning(f"Attempt to mark unknown ID: {student_id}")
                        return {"status": "error", "message": "Student ID not found"}

                    student_name = student[0]
                    student_email = student[1]

                    # 2. Validation: Check Registration
                    cursor.execute("""
                        SELECT id FROM registrations 
                        WHERE student_id = ? AND course_code = ?
                    """, (student_id, course_code))
                    
                    if not cursor.fetchone():
                        logger.warning(f"⛔ Student {student_name} is NOT registered for {course_code}")
                        return {"status": "error", "message": f"Not Registered for {course_code}"}

                    # 3. Validation: Duplicate Check
                    cursor.execute("""
                        SELECT id FROM attendance_log 
                        WHERE student_id = ? AND course_code = ? AND date(timestamp) = ?
                    """, (student_id, course_code, date_str))
                    
                    if cursor.fetchone():
                        return {"status": "warning", "message": f"Already marked: {student_name}"}

                    # 4. Insert Attendance Record
                    cursor.execute("""
                        INSERT INTO attendance_log (student_id, course_code, timestamp, status, method) 
                        VALUES (?, ?, ?, 'Present', 'Camera')
                    """, (student_id, course_code, time_str))
                    
                    conn.commit()
                    logger.info(f"✅ Attendance marked for {student_name}")
                    
                    return {
                        "status": "success", 
                        "message": f"Welcome {student_name}", 
                        "email": student_email,
                        "student_name": student_name
                    }

            except sqlite3.Error as e:
                logger.error(f"❌ Database Error: {e}")
                return {"status": "error", "message": "Internal Database Error"}

    def get_live_data(self) -> List[Dict[str, Any]]:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        query = '''
            SELECT s.name, s.student_id, c.course_name, a.timestamp, a.status
            FROM attendance_log a
            JOIN students s ON a.student_id = s.student_id
            LEFT JOIN courses c ON a.course_code = c.course_code
            WHERE date(a.timestamp) = ?
            ORDER BY a.timestamp DESC
        '''
        # Removed "AND a.method = 'Camera'" so manual entries also show up in live feed
        
        try:
            with self._get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=(date_str,))
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%H:%M:%S')
                return df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error fetching live data: {e}")
            return []