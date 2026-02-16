import sqlite3
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "attendance.db")

def create_schema():
    print(f"[INFO] Creating Database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Students (Removed Department)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT
        )
    ''')

    # 2. Courses (Removed Hall Number - rely on Schedule instead)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            course_code TEXT PRIMARY KEY,
            course_name TEXT NOT NULL,
            instructor TEXT,
            password TEXT DEFAULT '1234'
        )
    ''')

    # 3. Schedule
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lecture_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT,
            room_number TEXT,
            day_of_week TEXT,
            start_time TEXT,
            end_time TEXT,
            FOREIGN KEY (course_code) REFERENCES courses(course_code)
        )
    ''')

    # 4. Registrations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            course_code TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_code) REFERENCES courses(course_code),
            UNIQUE(student_id, course_code)
        )
    ''')

    # 5. Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            course_code TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Present',
            method TEXT DEFAULT 'Camera', 
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_code) REFERENCES courses(course_code)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Schema Updated (Cleaned Version)!")

if __name__ == "__main__":
    create_schema()