import sqlite3
import logging
import random
from pathlib import Path
from datetime import datetime, timedelta
import bcrypt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseSeeder:
    def __init__(self):
        self.db_path = Path(__file__).resolve().parent / "attendance.db"

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;") 
        
        tables = ['attendance_log', 'registrations', 'lecture_schedule', 'courses', 'students']
        for table in tables:
            self.cursor.execute(f"DELETE FROM {table}")
            self.cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        logger.info("🧹 Cleaned old database completely.")

    def _close(self):
        self.conn.commit()
        self.conn.close()

    def hash_pw(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def seed_students(self):
        """إضافة 60 طالب لتغطية الكورسات"""
        first_names = ["Ahmed", "Mohamed", "Sarah", "Nour", "Youssef", "Mariam", "Omar", "Hana", "Karim", "Laila", "Islam", "Mahmoud", "Tarek", "Ziad", "Rana"]
        last_names = ["Ali", "Ibrahim", "Hassan", "Kamal", "Adel", "Samir", "Nabil", "Fawzy", "Radwan", "Moussa", "Saeed", "Zaki"]
        
        students = []
        students.append(('1', 'Islam Mohamed', 'em8756070@gmail.com'))
        
        for i in range(59):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            fullname = f"{fname} {lname}"
            student_id = str(2024001 + i)
            email = f"student{i}@uni.edu"
            students.append((student_id, fullname, email))
            
        self.cursor.executemany('INSERT INTO students VALUES (?, ?, ?)', students)
        self.students_ids = [s[0] for s in students] 
        logger.info(f"✅ Seeded {len(students)} Students.")

    def seed_courses(self):
        """إضافة 6 مواد دراسية"""
        pass_1234 = self.hash_pw("1234")
        
        self.courses_list = [
            ('CS101', 'Intro to AI', 'Dr. Smith', pass_1234),
            ('MATH2', 'Linear Algebra', 'Dr. Magdy', pass_1234),
            ('IS300', 'Database Systems', 'Dr. Hoda', pass_1234),
            ('ENG101', 'Technical Writing', 'Dr. Rania', pass_1234),
            ('PHY102', 'Physics II', 'Dr. Albert', pass_1234),
            ('CS202', 'Data Structures', 'Dr. Khaled', pass_1234)
        ]
        self.cursor.executemany('INSERT INTO courses VALUES (?, ?, ?, ?)', self.courses_list)
        logger.info(f"✅ Seeded {len(self.courses_list)} Courses.")

    def seed_registrations(self):
        registrations = []
        
        for student_id in self.students_ids:
            num_courses = random.randint(4, 6) 
            my_courses = random.sample(self.courses_list, num_courses)
            
            for course in my_courses:
                if student_id == '1' and course[0] == 'CS101': continue 
                registrations.append((student_id, course[0]))
        
        registrations.append(('1', 'CS101'))
        registrations.append(('1', 'MATH2'))

        self.cursor.executemany('INSERT OR IGNORE INTO registrations (student_id, course_code) VALUES (?, ?)', registrations)
        logger.info(f"✅ Seeded {len(registrations)} Registrations (Avg ~50 students per course).")

    def seed_schedule(self):

        today_date = datetime.now()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        today_name = today_date.strftime("%A")
        
        self.schedule_map = {
            'CS101': today_name, 
            'MATH2': days[(days.index(today_name) + 1) % 7],
            'IS300': days[(days.index(today_name) + 2) % 7],
            'ENG101': days[(days.index(today_name) + 3) % 7],
            'PHY102': days[(days.index(today_name) + 4) % 7],
            'CS202': days[(days.index(today_name) + 5) % 7],
        }

        schedule_data = []
        for code, day in self.schedule_map.items():
            schedule_data.append((code, 'Hall_1', day, '00:00', '23:59')) 

        self.cursor.executemany('''INSERT INTO lecture_schedule (course_code, room_number, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?, ?)''', schedule_data)
        logger.info(f"✅ Schedule Updated (CS101 is Active Today: {today_name}).")

    def seed_history(self):

        logger.info("⏳ Simulating 12-week semester data...")
        
        attendance_log = []
        total_weeks = 12
        start_date = datetime.now() - timedelta(weeks=total_weeks)

        for course_code, day_name in self.schedule_map.items():
            self.cursor.execute("SELECT student_id FROM registrations WHERE course_code = ?", (course_code,))
            enrolled_students = [row[0] for row in self.cursor.fetchall()]
            
            course_dates = []
            current_check = start_date
            while len(course_dates) < total_weeks:
                if current_check.strftime("%A") == day_name:
                    course_dates.append(current_check)
                current_check += timedelta(days=1)
                
                if current_check > datetime.now(): break

            for student_id in enrolled_students:
                rand_profile = random.random()
                
                if rand_profile < 0.15: 
                    sessions_to_attend = random.sample(course_dates, k=random.randint(5, 8))
                elif rand_profile < 0.30:
                    sessions_to_attend = random.sample(course_dates, k=10) if len(course_dates) >= 10 else course_dates
                else:
                    k = len(course_dates) if random.random() > 0.3 else len(course_dates) - 1
                    sessions_to_attend = random.sample(course_dates, k=max(0, k))

                for session_date in sessions_to_attend:
                    entry_time = session_date.replace(hour=random.randint(9, 10), minute=random.randint(0, 59), second=0)
                    time_str = entry_time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    attendance_log.append((student_id, course_code, time_str, 'Present', 'Auto'))

        self.cursor.executemany('INSERT INTO attendance_log (student_id, course_code, timestamp, status, method) VALUES (?, ?, ?, ?, ?)', attendance_log)
        logger.info(f"✅ Generated {len(attendance_log)} attendance records across 12 weeks.")

    def run(self):
        self._connect()
        self.seed_students()
        self.seed_courses()
        self.seed_registrations()
        self.seed_schedule()
        self.seed_history()
        self._close()
        logger.info("🚀 Database Fully Seeded! Ready for Dashboard Demo.")

if __name__ == "__main__":
    DatabaseSeeder().run()