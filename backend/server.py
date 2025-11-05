from fastapi import FastAPI, APIRouter, HTTPException, Depends, Cookie, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import secrets
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Session storage (in-memory for simplicity)
sessions = {}

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    role: str  # parent, teacher, admin
    name: str
    student_ids: Optional[List[str]] = []  # for parents and teachers

class UserLogin(BaseModel):
    email: str
    password: str

class Student(BaseModel):
    model_config = ConfigDict(extra="ignore")
    student_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    parent_id: str
    photo_ref: Optional[str] = None
    bus_id: str

class Attendance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    attendance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    date: str  # YYYY-MM-DD
    trip: str  # AM or PM
    status: str  # gray, yellow, green, red, blue
    confidence: Optional[float] = None
    last_update: str

class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    tag_id: str
    verified: bool
    confidence: float
    lat: float
    lon: float
    timestamp: str

class BusLocation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    bus_id: str
    lat: float
    lon: float
    timestamp: str

class ScanEventRequest(BaseModel):
    student_id: str
    tag_id: str
    verified: bool
    confidence: float
    lat: float
    lon: float

class UpdateLocationRequest(BaseModel):
    bus_id: str
    lat: float
    lon: float

class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    timestamp: str
    read: bool = False
    type: str  # mismatch, missed_boarding

class Holiday(BaseModel):
    model_config = ConfigDict(extra="ignore")
    holiday_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str  # YYYY-MM-DD
    name: str

# Auth helper
async def get_current_user(session_token: Optional[str] = Cookie(None)):
    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sessions[session_token]

# Auth endpoints
@api_router.post("/auth/login")
async def login(user_login: UserLogin, response: Response):
    user = await db.users.find_one({"email": user_login.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not bcrypt.checkpw(user_login.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = user
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )
    
    return {
        "user_id": user['user_id'],
        "email": user['email'],
        "role": user['role'],
        "name": user['name'],
        "student_ids": user.get('student_ids', [])
    }

@api_router.post("/auth/logout")
async def logout(response: Response, session_token: Optional[str] = Cookie(None)):
    if session_token in sessions:
        del sessions[session_token]
    response.delete_cookie("session_token")
    return {"message": "Logged out"}

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user['user_id'],
        "email": current_user['email'],
        "role": current_user['role'],
        "name": current_user['name'],
        "student_ids": current_user.get('student_ids', [])
    }

# Core APIs
@api_router.post("/scan_event")
async def scan_event(request: ScanEventRequest):
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Create event record
    event = Event(
        student_id=request.student_id,
        tag_id=request.tag_id,
        verified=request.verified,
        confidence=request.confidence,
        lat=request.lat,
        lon=request.lon,
        timestamp=timestamp
    )
    await db.events.insert_one(event.model_dump())
    
    # Update attendance status
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    hour = datetime.now(timezone.utc).hour
    trip = "AM" if hour < 12 else "PM"
    
    # Check if attendance exists
    existing = await db.attendance.find_one({
        "student_id": request.student_id,
        "date": today,
        "trip": trip
    })
    
    if request.verified:
        status = "yellow"  # On Board
        
        if existing:
            await db.attendance.update_one(
                {"student_id": request.student_id, "date": today, "trip": trip},
                {"$set": {"status": status, "confidence": request.confidence, "last_update": timestamp}}
            )
        else:
            attendance = Attendance(
                student_id=request.student_id,
                date=today,
                trip=trip,
                status=status,
                confidence=request.confidence,
                last_update=timestamp
            )
            await db.attendance.insert_one(attendance.model_dump())
    else:
        # Create notification for mismatch
        student = await db.students.find_one({"student_id": request.student_id}, {"_id": 0})
        if student:
            notification = Notification(
                user_id=student['parent_id'],
                message=f"Identity mismatch detected for {student['name']} (Confidence: {request.confidence:.0%})",
                timestamp=timestamp,
                type="mismatch"
            )
            await db.notifications.insert_one(notification.model_dump())
    
    return {"status": "success", "event_id": event.event_id}

@api_router.post("/update_location")
async def update_location(request: UpdateLocationRequest):
    timestamp = datetime.now(timezone.utc).isoformat()
    
    location = BusLocation(
        bus_id=request.bus_id,
        lat=request.lat,
        lon=request.lon,
        timestamp=timestamp
    )
    
    # Upsert bus location
    await db.bus_locations.update_one(
        {"bus_id": request.bus_id},
        {"$set": location.model_dump()},
        upsert=True
    )
    
    return {"status": "success", "timestamp": timestamp}

@api_router.get("/get_attendance")
async def get_attendance(student_id: str, month: str, current_user: dict = Depends(get_current_user)):
    # month format: YYYY-MM
    
    # Check permissions
    if current_user['role'] == 'parent':
        if student_id not in current_user.get('student_ids', []):
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all attendance for the month
    year, month_num = month.split('-')
    start_date = f"{year}-{month_num}-01"
    
    # Calculate end date
    import calendar
    last_day = calendar.monthrange(int(year), int(month_num))[1]
    end_date = f"{year}-{month_num}-{last_day:02d}"
    
    attendance_records = await db.attendance.find({
        "student_id": student_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(1000)
    
    # Get holidays
    holidays = await db.holidays.find({
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(100)
    
    holiday_dates = {h['date'] for h in holidays}
    
    # Build grid data
    grid = []
    for day in range(1, last_day + 1):
        date = f"{year}-{month_num}-{day:02d}"
        
        am_record = next((r for r in attendance_records if r['date'] == date and r['trip'] == 'AM'), None)
        pm_record = next((r for r in attendance_records if r['date'] == date and r['trip'] == 'PM'), None)
        
        # Check if holiday
        if date in holiday_dates:
            am_status = "blue"
            pm_status = "blue"
        else:
            am_status = am_record['status'] if am_record else "gray"
            pm_status = pm_record['status'] if pm_record else "gray"
        
        grid.append({
            "date": date,
            "day": day,
            "am_status": am_status,
            "pm_status": pm_status,
            "am_confidence": am_record['confidence'] if am_record else None,
            "pm_confidence": pm_record['confidence'] if pm_record else None
        })
    
    # Calculate summary
    total_days = last_day * 2  # AM + PM
    present_count = sum(1 for r in attendance_records if r['status'] in ['yellow', 'green'])
    
    return {
        "grid": grid,
        "summary": f"{present_count} / {total_days} sessions"
    }

@api_router.get("/get_bus_location")
async def get_bus_location(bus_id: str):
    location = await db.bus_locations.find_one({"bus_id": bus_id}, {"_id": 0})
    if not location:
        raise HTTPException(status_code=404, detail="Bus location not found")
    return location

@api_router.get("/get_notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    notifications = await db.notifications.find(
        {"user_id": current_user['user_id']},
        {"_id": 0}
    ).sort("timestamp", -1).limit(50).to_list(50)
    
    return notifications

@api_router.post("/mark_notification_read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    await db.notifications.update_one(
        {"notification_id": notification_id, "user_id": current_user['user_id']},
        {"$set": {"read": True}}
    )
    return {"status": "success"}

# Admin CRUD operations
@api_router.get("/admin/students")
async def get_students(current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    students = await db.students.find({}, {"_id": 0}).to_list(1000)
    return students

@api_router.post("/admin/students")
async def create_student(student: Student, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.students.insert_one(student.model_dump())
    return student

@api_router.put("/admin/students/{student_id}")
async def update_student(student_id: str, student: Student, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.students.update_one(
        {"student_id": student_id},
        {"$set": student.model_dump()}
    )
    return student

@api_router.delete("/admin/students/{student_id}")
async def delete_student(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.students.delete_one({"student_id": student_id})
    return {"status": "deleted"}

@api_router.get("/admin/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api_router.post("/admin/holidays")
async def create_holiday(holiday: Holiday, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.holidays.insert_one(holiday.model_dump())
    return holiday

@api_router.get("/admin/holidays")
async def get_holidays(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    holidays = await db.holidays.find({}, {"_id": 0}).to_list(1000)
    return holidays

@api_router.delete("/admin/holidays/{holiday_id}")
async def delete_holiday(holiday_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.holidays.delete_one({"holiday_id": holiday_id})
    return {"status": "deleted"}

# Teacher endpoints
@api_router.get("/teacher/students")
async def get_teacher_students(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'teacher':
        raise HTTPException(status_code=403, detail="Access denied")
    
    student_ids = current_user.get('student_ids', [])
    students = await db.students.find({"student_id": {"$in": student_ids}}, {"_id": 0}).to_list(1000)
    
    # Get today's attendance for each student
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for student in students:
        am_attendance = await db.attendance.find_one({
            "student_id": student['student_id'],
            "date": today,
            "trip": "AM"
        }, {"_id": 0})
        pm_attendance = await db.attendance.find_one({
            "student_id": student['student_id'],
            "date": today,
            "trip": "PM"
        }, {"_id": 0})
        
        student['am_status'] = am_attendance['status'] if am_attendance else 'gray'
        student['pm_status'] = pm_attendance['status'] if pm_attendance else 'gray'
    
    return students

# Parent endpoint
@api_router.get("/parent/students")
async def get_parent_students(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'parent':
        raise HTTPException(status_code=403, detail="Access denied")
    
    student_ids = current_user.get('student_ids', [])
    students = await db.students.find({"student_id": {"$in": student_ids}}, {"_id": 0}).to_list(1000)
    return students

# Mock/Demo endpoints
@api_router.post("/demo/simulate_scan")
async def simulate_scan():
    """Simulate a random RFID scan event"""
    # Get random student
    students = await db.students.find({}, {"_id": 0}).to_list(1000)
    if not students:
        raise HTTPException(status_code=404, detail="No students found")
    
    student = random.choice(students)
    
    # Random verification result
    verified = random.choice([True, True, True, False])  # 75% verified
    confidence = random.uniform(0.85, 0.99) if verified else random.uniform(0.40, 0.70)
    
    # Random coordinates (simulating bus route)
    lat = 37.7749 + random.uniform(-0.05, 0.05)
    lon = -122.4194 + random.uniform(-0.05, 0.05)
    
    request = ScanEventRequest(
        student_id=student['student_id'],
        tag_id=f"RFID-{random.randint(1000, 9999)}",
        verified=verified,
        confidence=confidence,
        lat=lat,
        lon=lon
    )
    
    result = await scan_event(request)
    return {**result, "student_name": student['name'], "verified": verified}

@api_router.post("/demo/simulate_bus_movement")
async def simulate_bus_movement(bus_id: str):
    """Simulate bus movement along a route"""
    # Get current location or start new
    current = await db.bus_locations.find_one({"bus_id": bus_id}, {"_id": 0})
    
    if current:
        # Move slightly
        lat = current['lat'] + random.uniform(-0.001, 0.001)
        lon = current['lon'] + random.uniform(-0.001, 0.001)
    else:
        # Start position
        lat = 37.7749
        lon = -122.4194
    
    request = UpdateLocationRequest(
        bus_id=bus_id,
        lat=lat,
        lon=lon
    )
    
    return await update_location(request)

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
