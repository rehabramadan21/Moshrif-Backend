import os
import sqlite3
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import bcrypt
from dotenv import load_dotenv
import jwt  # 🔥 تمت إضافة مكتبة JWT

# Import our robust handler
from database_handler import DatabaseHandler

# ==========================================
# ⚙️ 1. Configuration & Setup
# ==========================================
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Moshrif University ERP API", version="6.0 (Rebranded)")
db_handler = DatabaseHandler()

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "03_Database", "attendance.db")

# 🔥 Secrets from .env
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SMTP_EMAIL")
SENDER_PASSWORD = os.getenv("SMTP_PASSWORD")

# 🔥 JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_change_me")
ALGORITHM = "HS256"

# ==========================================
# 🔒 Security Helper Functions
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_password(plain, hashed):
    try: return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except: return False

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# 🔥 دالة التحقق من صحة التوكن (JWT)
def verify_jwt_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization.split(" ")[1]
    try:
        # فك التشفير والتأكد من صحة التوكن
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==========================================
# 📦 Models
# ==========================================
class LoginRequest(BaseModel):
    password: str
    course_code: Optional[str] = None

class AttendanceRequest(BaseModel):
    student_id: str
    room_number: str = "Hall_1"

class AdminAction(BaseModel):
    table: str
    action: str
    data: Dict[str, Any]

class ManualEdit(BaseModel):
    student_id: str
    course_code: str
    status: str
    date: Optional[str] = None 

# ==========================================
# 📧 Email Helper (Professional & Rebranded)
# ==========================================
def send_email_notification(to_email: str, student_name: str, course_name: str, time: str):
    if not to_email or "uni.edu" in to_email: 
        return 

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = f"✅ Attendance Confirmed: {course_name}"

        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; }}
                .header {{ background: #1e1e2f; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; color: #e14eca; font-size: 28px; letter-spacing: 2px; text-transform: uppercase; }}
                .header span {{ color: #ffffff; font-size: 14px; letter-spacing: 1px; opacity: 0.8; display: block; margin-top: 5px; }}
                .content {{ padding: 40px 30px; color: #333; }}
                .greeting {{ font-size: 18px; font-weight: bold; margin-bottom: 20px; color: #1e1e2f; }}
                .message {{ font-size: 16px; line-height: 1.6; color: #555; margin-bottom: 30px; }}
                .details-box {{ background: #f8f9fa; border-left: 5px solid #00f2c3; padding: 20px; border-radius: 4px; margin-bottom: 30px; }}
                .detail-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                .detail-row:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
                .label {{ font-weight: bold; color: #777; font-size: 14px; }}
                .value {{ font-weight: bold; color: #333; font-size: 14px; }}
                .status-badge {{ background: #e6fffa; color: #00f2c3; padding: 5px 12px; border-radius: 15px; font-size: 12px; border: 1px solid #00f2c3; }}
                .footer {{ background: #f4f4f9; padding: 20px; text-align: center; font-size: 12px; color: #888; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>MOSHRiF</h1>
                    <span>Smart Attendance System</span>
                </div>
                <div class="content">
                    <div class="greeting">Hello, {student_name} 👋</div>
                    <div class="message">
                        This is an automated notification to confirm that your attendance has been successfully recorded.
                    </div>
                    
                    <div class="details-box">
                        <div class="detail-row">
                            <span class="label">Course</span>
                            <span class="value">{course_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Time Recorded</span>
                            <span class="value">{time}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Status</span>
                            <span class="status-badge">✅ PRESENT</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Method</span>
                            <span class="value">Facial Recognition</span>
                        </div>
                    </div>
                </div>
                <div class="footer">
                    &copy; {datetime.now().year} Moshrif System. All rights reserved.<br>
                    This is an automated message, please do not reply.
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")

# ==========================================
# 🛠️ Helpers
# ==========================================
def get_current_course(room_number):
    if not os.path.exists(DB_PATH): return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    now = datetime.now()
    day = now.strftime("%A")
    time = now.strftime("%H:%M")
    
    row = cursor.execute("SELECT s.course_code, c.course_name FROM lecture_schedule s JOIN courses c ON s.course_code = c.course_code WHERE s.room_number = ? AND s.day_of_week = ? AND ? BETWEEN s.start_time AND s.end_time", (room_number, day, time)).fetchone()
    conn.close()
    return {"code": row["course_code"], "name": row["course_name"]} if row else None

def get_date_range(filter_type):
    today = datetime.now()
    if filter_type == "Today": start = today.strftime("%Y-%m-%d")
    elif filter_type == "Week": start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    elif filter_type == "Month": start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    else: start = "2023-01-01"
    return start, today.strftime("%Y-%m-%d")

# ==========================================
# 🚀 API Endpoints
# ==========================================

# --- Auth ---
@app.post("/api/admin/login")
def admin_login(req: LoginRequest):
    return {"status": "success"} if req.password == ADMIN_PASSWORD else {"status": "error"}

@app.post("/api/course/login")
def course_login(req: LoginRequest):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT password FROM courses WHERE course_code=?", (req.course_code,)).fetchone()
    conn.close()
    if row and verify_password(req.password, row[0]): return {"status": "success"}
    return {"status": "error"}

# --- Attendance ---
# 🔥 إضافة الحماية هنا باستخدام Depends(verify_jwt_token)
@app.post("/api/attendance/mark")
def mark_attendance(req: AttendanceRequest, background_tasks: BackgroundTasks, token_data: dict = Depends(verify_jwt_token)):
    active_course = get_current_course(req.room_number)
    
    if not active_course: 
        return {"status": "error", "message": "No active lecture found at this time!"}
    
    result = db_handler.mark_attendance(req.student_id, active_course["code"])
    
    if result["status"] == "success" and result.get("email"):
         background_tasks.add_task(send_email_notification, result["email"], result["student_name"], active_course["name"], datetime.now().strftime("%H:%M"))
    return result

@app.get("/api/attendance/live")
def get_live_attendance():
    return db_handler.get_live_data()

# --- Dashboard Stats ---
@app.get("/api/dashboard/stats")
def dashboard_stats(filter: str = "Today"):
    conn = sqlite3.connect(DB_PATH)
    s, e = get_date_range(filter)
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM attendance_log WHERE date(timestamp) BETWEEN '{s}' AND '{e}' AND status='Present'").fetchone()[0]
        active = conn.execute(f"SELECT COUNT(DISTINCT course_code) FROM attendance_log WHERE date(timestamp) BETWEEN '{s}' AND '{e}'").fetchone()[0]
        unique = conn.execute(f"SELECT COUNT(DISTINCT student_id) FROM attendance_log WHERE date(timestamp) BETWEEN '{s}' AND '{e}'").fetchone()[0]
        avg = round(total/active, 1) if active > 0 else 0
        return {"total_attendance": total, "active_courses": active, "unique_students": unique, "avg_attendance": avg}
    except: return {}
    finally: conn.close()

@app.get("/api/dashboard/chart_data")
def dashboard_chart(filter: str = "Today"):
    conn = sqlite3.connect(DB_PATH)
    s, e = get_date_range(filter)
    df = pd.read_sql_query(f"SELECT c.course_code as name, COUNT(a.id) as value FROM courses c LEFT JOIN attendance_log a ON c.course_code = a.course_code AND date(a.timestamp) BETWEEN '{s}' AND '{e}' GROUP BY c.course_code", conn)
    conn.close()
    return df.to_dict(orient="records")

# --- Admin CRUD ---
@app.post("/api/admin/crud")
def admin_crud(req: AdminAction):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        if req.table == "students":
            if req.action == "add": cursor.execute("INSERT INTO students VALUES (?,?,?)", (req.data['id'], req.data['name'], req.data.get('email')))
            elif req.action == "update": cursor.execute("UPDATE students SET name=?, email=? WHERE student_id=?", (req.data['name'], req.data.get('email'), req.data['id']))
            elif req.action == "delete": cursor.execute("DELETE FROM students WHERE student_id=?", (req.data['id'],))
        elif req.table == "courses":
            if req.action == "add": cursor.execute("INSERT INTO courses VALUES (?,?,?,?)", (req.data['code'], req.data['name'], req.data['instructor'], get_password_hash(req.data['password'])))
            elif req.action == "update": cursor.execute("UPDATE courses SET course_name=?, instructor=?, password=? WHERE course_code=?", (req.data['name'], req.data['instructor'], get_password_hash(req.data['password']), req.data['code']))
            elif req.action == "delete": cursor.execute("DELETE FROM courses WHERE course_code=?", (req.data['code'],))
        elif req.table == "schedule":
            if req.action == "add": cursor.execute("INSERT INTO lecture_schedule (course_code, room_number, day_of_week, start_time, end_time) VALUES (?,?,?,?,?)", (req.data['course_code'], req.data['room'], req.data['day'], req.data['start'], req.data['end']))
            elif req.action == "delete": cursor.execute("DELETE FROM lecture_schedule WHERE id=?", (req.data['id'],))
        elif req.table == "registrations":
            if req.action == "add": cursor.execute("INSERT INTO registrations (student_id, course_code) VALUES (?,?)", (req.data['student_id'], req.data['course_code']))
            elif req.action == "delete": cursor.execute("DELETE FROM registrations WHERE id=?", (req.data['id'],))
        conn.commit()
        return {"status": "success"}
    except Exception as e: return {"status": "error", "message": str(e)}
    finally: conn.close()

# --- General Data Fetching ---
@app.get("/api/admin/get/{table}")
def get_data(table: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        if table == "attendance": df = pd.read_sql_query("SELECT a.id, a.student_id, s.name as student_name, a.course_code, c.course_name, a.timestamp, a.status FROM attendance_log a JOIN students s ON a.student_id=s.student_id JOIN courses c ON a.course_code=c.course_code ORDER BY a.timestamp DESC", conn)
        elif table == "registrations": df = pd.read_sql_query("SELECT r.id, r.student_id, s.name as student_name, r.course_code, c.course_name FROM registrations r JOIN students s ON r.student_id=s.student_id JOIN courses c ON r.course_code=c.course_code", conn)
        elif table == "schedule": df = pd.read_sql_query("SELECT s.id, s.course_code, c.course_name, s.room_number, s.day_of_week, s.start_time, s.end_time FROM lecture_schedule s LEFT JOIN courses c ON s.course_code=c.course_code", conn)
        else: df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        return df.to_dict(orient="records")
    except: return []
    finally: conn.close()

# --- Course Details & Reports ---
@app.get("/api/course/{code}/date/{date_str}")
def get_daily_details(code: str, date_str: str):
    conn = sqlite3.connect(DB_PATH)
    try: return pd.read_sql_query("SELECT s.student_id, s.name, CASE WHEN a.id IS NOT NULL THEN 'Present' ELSE 'Absent' END as status FROM students s JOIN registrations r ON s.student_id = r.student_id LEFT JOIN attendance_log a ON s.student_id = a.student_id AND a.course_code = ? AND date(a.timestamp) = ? WHERE r.course_code = ?", conn, params=(code, date_str, code)).to_dict(orient="records")
    except: return []
    finally: conn.close()

@app.get("/api/course/{code}/history")
def get_course_history(code: str):
    conn = sqlite3.connect(DB_PATH)
    total_reg = conn.execute("SELECT COUNT(*) FROM registrations WHERE course_code = ?", (code,)).fetchone()[0] or 1
    return [{"date": r[0], "present": r[1], "absent": total_reg - r[1], "percentage": round((r[1]/total_reg)*100, 1)} for r in conn.execute('SELECT date(timestamp), COUNT(DISTINCT student_id) FROM attendance_log WHERE course_code = ? GROUP BY date(timestamp) ORDER BY date DESC', (code,)).fetchall()]

@app.get("/api/course/{code}/dates")
def get_course_dates(code: str):
    conn = sqlite3.connect(DB_PATH)
    try: dates = [row[0] for row in conn.execute("SELECT DISTINCT date(timestamp) FROM attendance_log WHERE course_code = ? ORDER BY date(timestamp) DESC", (code,)).fetchall()]
    except: dates = []
    finally: conn.close()
    
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in dates: dates.insert(0, today)
    return dates

@app.get("/api/course/{code}/report")
def risk_report(code: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        total_lectures = conn.execute("SELECT COUNT(DISTINCT date(timestamp)) FROM attendance_log WHERE course_code=?", (code,)).fetchone()[0]
        if total_lectures == 0: total_lectures = 1
        
        df = pd.read_sql_query("""
            SELECT s.name, s.student_id, COUNT(a.id) as attended 
            FROM students s 
            JOIN registrations r ON s.student_id = r.student_id 
            LEFT JOIN attendance_log a ON s.student_id = a.student_id AND a.course_code = ? 
            WHERE r.course_code = ? 
            GROUP BY s.student_id
        """, conn, params=(code, code))
        
        report = []
        for _, r in df.iterrows():
            absent = total_lectures - r['attended']
            if absent >= 3: status = "🚫 BARRED"
            elif absent == 2: status = "⚠️ Warning"
            else: status = "Safe ✅"
            
            report.append({
                "name": r['name'], 
                "id": r['student_id'], 
                "attended": r['attended'], 
                "absent": absent, 
                "status": status
            })
        return report
    except Exception as e: 
        logger.error(f"Risk report error: {e}")
        return []
    finally: conn.close()

# --- Manual Edit & Export ---
@app.post("/api/attendance/manual")
def manual_update(req: ManualEdit, background_tasks: BackgroundTasks):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    target_date = req.date if req.date else datetime.now().strftime("%Y-%m-%d")
    is_today = (target_date == datetime.now().strftime("%Y-%m-%d"))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if is_today else f"{target_date} 09:00:00"
    
    try:
        if req.status == "Present":
            check = cursor.execute("SELECT id FROM attendance_log WHERE student_id=? AND course_code=? AND date(timestamp)=?", (req.student_id, req.course_code, target_date)).fetchone()
            if not check:
                cursor.execute("INSERT INTO attendance_log (student_id, course_code, timestamp, status, method) VALUES (?, ?, ?, 'Present', 'Manual')", (req.student_id, req.course_code, timestamp))
                
                s_info = cursor.execute("SELECT name, email FROM students WHERE student_id=?", (req.student_id,)).fetchone()
                c_info = cursor.execute("SELECT course_name FROM courses WHERE course_code=?", (req.course_code,)).fetchone()
                if s_info and s_info[1] and c_info:
                    background_tasks.add_task(send_email_notification, s_info[1], s_info[0], c_info[0], timestamp)
        else: 
            cursor.execute("DELETE FROM attendance_log WHERE student_id=? AND course_code=? AND date(timestamp)=?", (req.student_id, req.course_code, target_date))
        
        conn.commit()
        return {"status": "success"}
    except Exception as e: return {"status": "error", "message": str(e)}
    finally: conn.close()

@app.get("/api/export/course/{code}/{date}")
def export_sheet(code: str, date: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT s.student_id, s.name, CASE WHEN a.id IS NOT NULL THEN 'Present' ELSE 'Absent' END as Status FROM students s JOIN registrations r ON s.student_id=r.student_id LEFT JOIN attendance_log a ON s.student_id=a.student_id AND a.course_code=? AND date(a.timestamp)=? WHERE r.course_code=?", conn, params=(code, date, code))
        file_path = os.path.join(BASE_DIR, f"Attendance_{code}_{date}.xlsx")
        df.to_excel(file_path, index=False)
        return FileResponse(file_path, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=f"Attendance_{code}_{date}.xlsx")
    except: return {"error": "Failed"}
    finally: conn.close()

@app.get("/api/students")
def get_students():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT student_id, name FROM students", conn)
    conn.close()
    return df.to_dict(orient="records")

@app.get("/api/courses")
def get_courses():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM courses", conn)
    conn.close()
    return df.to_dict(orient="records")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)