from fastapi import FastAPI, APIRouter, HTTPException, Depends, Cookie, Response, UploadFile, File
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
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Session storage (in-memory for simplicity)
sessions = {}

# Photo storage directory
PHOTO_DIR = ROOT_DIR / 'photos'
PHOTO_DIR.mkdir(exist_ok=True)

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Extended Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    role: str  # parent, teacher, admin
    name: str
    phone: Optional[str] = None
    photo: Optional[str] = None
    assigned_class: Optional[str] = None
    assigned_section: Optional[str] = None
    address: Optional[str] = None
    student_ids: Optional[List[str]] = []

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    assigned_class: Optional[str] = None
    assigned_section: Optional[str] = None
    address: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Student(BaseModel):
    model_config = ConfigDict(extra="ignore")
    student_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    roll_number: Optional[str] = None
    phone: Optional[str] = None
    photo: Optional[str] = None
    class_name: Optional[str] = None
    section: Optional[str] = None
    parent_id: str
    teacher_id: Optional[str] = None
    bus_id: str
    stop_id: Optional[str] = None
    emergency_contact: Optional[str] = None
    remarks: Optional[str] = None

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    roll_number: Optional[str] = None
    phone: Optional[str] = None
    class_name: Optional[str] = None
    section: Optional[str] = None
    parent_id: Optional[str] = None
    teacher_id: Optional[str] = None
    bus_id: Optional[str] = None
    stop_id: Optional[str] = None
    emergency_contact: Optional[str] = None
    remarks: Optional[str] = None

class Bus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    bus_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bus_number: str
    driver_name: str
    driver_phone: str
    route_id: Optional[str] = None
    capacity: int
    remarks: Optional[str] = None

class Route(BaseModel):
    model_config = ConfigDict(extra="ignore")
    route_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    route_name: str
    stop_ids: List[str] = []
    map_path: List[dict] = []  # [{"lat": float, "lon": float}]
    remarks: Optional[str] = None

class Stop(BaseModel):
    model_config = ConfigDict(extra="ignore")
    stop_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stop_name: str
    lat: float
    lon: float
    order_index: int

class EmailLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    email_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recipient_email: str
    recipient_name: str
    subject: str
    body: str
    timestamp: str
    student_id: Optional[str] = None
    user_id: Optional[str] = None

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
    type: str  # mismatch, missed_boarding, update

class Holiday(BaseModel):
    model_config = ConfigDict(extra="ignore")
    holiday_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str  # YYYY-MM-DD
    name: str

# Helper: Send mock email and log
async def send_email_notification(recipient_email: str, recipient_name: str, subject: str, body: str, student_id: Optional[str] = None, user_id: Optional[str] = None):
    email_log = EmailLog(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        subject=subject,
        body=body,
        timestamp=datetime.now(timezone.utc).isoformat(),
        student_id=student_id,
        user_id=user_id
    )
    await db.email_logs.insert_one(email_log.model_dump())
    logging.info(f"EMAIL SENT TO: {recipient_email}\nSUBJECT: {subject}\nBODY: {body}")
    return email_log

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
        "phone": user.get('phone'),
        "photo": user.get('photo'),
        "assigned_class": user.get('assigned_class'),
        "assigned_section": user.get('assigned_section'),
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
        "phone": current_user.get('phone'),
        "photo": current_user.get('photo'),
        "address": current_user.get('address'),
        "assigned_class": current_user.get('assigned_class'),
        "assigned_section": current_user.get('assigned_section'),
        "student_ids": current_user.get('student_ids', [])
    }

# Photo upload
@api_router.post("/upload_photo")
async def upload_photo(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    try:
        file_ext = file.filename.split('.')[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = PHOTO_DIR / file_name
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"photo_url": f"/photos/{file_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Core APIs
@api_router.post("/scan_event")
async def scan_event(request: ScanEventRequest):
    timestamp = datetime.now(timezone.utc).isoformat()
    
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
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    hour = datetime.now(timezone.utc).hour
    trip = "AM" if hour < 12 else "PM"
    
    existing = await db.attendance.find_one({
        "student_id": request.student_id,
        "date": today,
        "trip": trip
    })
    
    if request.verified:
        status = "yellow"
        
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
    
    await db.bus_locations.update_one(
        {"bus_id": request.bus_id},
        {"$set": location.model_dump()},
        upsert=True
    )
    
    return {"status": "success", "timestamp": timestamp}

@api_router.get("/get_attendance")
async def get_attendance(student_id: str, month: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] == 'parent':
        if student_id not in current_user.get('student_ids', []):
            raise HTTPException(status_code=403, detail="Access denied")
    
    year, month_num = month.split('-')
    start_date = f"{year}-{month_num}-01"
    
    import calendar
    last_day = calendar.monthrange(int(year), int(month_num))[1]
    end_date = f"{year}-{month_num}-{last_day:02d}"
    
    attendance_records = await db.attendance.find({
        "student_id": student_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(1000)
    
    holidays = await db.holidays.find({
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(100)
    
    holiday_dates = {h['date'] for h in holidays}
    
    grid = []
    for day in range(1, last_day + 1):
        date = f"{year}-{month_num}-{day:02d}"
        
        am_record = next((r for r in attendance_records if r['date'] == date and r['trip'] == 'AM'), None)
        pm_record = next((r for r in attendance_records if r['date'] == date and r['trip'] == 'PM'), None)
        
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
    
    total_days = last_day * 2
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

# Student APIs
@api_router.get("/students")
async def get_students(current_user: dict = Depends(get_current_user)):
    if current_user['role'] == 'parent':
        student_ids = current_user.get('student_ids', [])
        students = await db.students.find({"student_id": {"$in": student_ids}}, {"_id": 0}).to_list(1000)
    elif current_user['role'] == 'teacher':
        student_ids = current_user.get('student_ids', [])
        students = await db.students.find({"student_id": {"$in": student_ids}}, {"_id": 0}).to_list(1000)
    else:
        students = await db.students.find({}, {"_id": 0}).to_list(1000)
    
    # Enrich with teacher and parent names
    for student in students:
        if student.get('teacher_id'):
            teacher = await db.users.find_one({"user_id": student['teacher_id']}, {"_id": 0})
            student['teacher_name'] = teacher['name'] if teacher else 'N/A'
        else:
            student['teacher_name'] = 'N/A'
        
        parent = await db.users.find_one({"user_id": student['parent_id']}, {"_id": 0})
        student['parent_name'] = parent['name'] if parent else 'N/A'
        
        if student.get('bus_id'):
            bus = await db.buses.find_one({"bus_id": student['bus_id']}, {"_id": 0})
            student['bus_number'] = bus['bus_number'] if bus else 'N/A'
        else:
            student['bus_number'] = 'N/A'
    
    return students

@api_router.get("/students/{student_id}")
async def get_student(student_id: str, current_user: dict = Depends(get_current_user)):
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Enrich
    if student.get('teacher_id'):
        teacher = await db.users.find_one({"user_id": student['teacher_id']}, {"_id": 0})
        student['teacher_name'] = teacher['name'] if teacher else 'N/A'
    else:
        student['teacher_name'] = 'N/A'
    
    parent = await db.users.find_one({"user_id": student['parent_id']}, {"_id": 0})
    student['parent_name'] = parent['name'] if parent else 'N/A'
    student['parent_email'] = parent['email'] if parent else 'N/A'
    
    if student.get('bus_id'):
        bus = await db.buses.find_one({"bus_id": student['bus_id']}, {"_id": 0})
        student['bus_number'] = bus['bus_number'] if bus else 'N/A'
        student['route_id'] = bus.get('route_id') if bus else None
    else:
        student['bus_number'] = 'N/A'
        student['route_id'] = None
    
    return student

@api_router.post("/students")
async def create_student(student: Student, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.students.insert_one(student.model_dump())
    return student

@api_router.put("/students/{student_id}")
async def update_student(student_id: str, updates: StudentUpdate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get old student data
    old_student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not old_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update student
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    await db.students.update_one(
        {"student_id": student_id},
        {"$set": update_data}
    )
    
    # Send email notification to parent if admin updated
    if current_user['role'] == 'admin':
        parent = await db.users.find_one({"user_id": old_student['parent_id']}, {"_id": 0})
        if parent:
            changed_fields = []
            for key, value in update_data.items():
                if old_student.get(key) != value:
                    changed_fields.append(f"{key}: {old_student.get(key)} → {value}")
            
            if changed_fields:
                subject = "Student Record Updated"
                body = f"Dear {parent['name']},\n\nThe following details have been updated for {old_student['name']}:\n\n" + "\n".join(changed_fields) + "\n\nRegards,\nSchool Administration"
                await send_email_notification(
                    recipient_email=parent['email'],
                    recipient_name=parent['name'],
                    subject=subject,
                    body=body,
                    student_id=student_id
                )
    
    return {"status": "updated"}

@api_router.delete("/students/{student_id}")
async def delete_student(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.students.delete_one({"student_id": student_id})
    return {"status": "deleted"}

# User APIs
@api_router.get("/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, updates: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Cannot edit another admin
    target_user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user['role'] == 'admin' and user_id != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Cannot edit another admin")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    
    # Update session if current user
    if user_id == current_user['user_id']:
        for session_token, session_user in sessions.items():
            if session_user['user_id'] == user_id:
                session_user.update(update_data)
    
    return {"status": "updated"}

# Bus APIs
@api_router.get("/buses")
async def get_buses(current_user: dict = Depends(get_current_user)):
    buses = await db.buses.find({}, {"_id": 0}).to_list(1000)
    
    # Enrich with route info
    for bus in buses:
        if bus.get('route_id'):
            route = await db.routes.find_one({"route_id": bus['route_id']}, {"_id": 0})
            bus['route_name'] = route['route_name'] if route else 'N/A'
        else:
            bus['route_name'] = 'N/A'
    
    return buses

@api_router.get("/buses/{bus_id}")
async def get_bus(bus_id: str):
    bus = await db.buses.find_one({"bus_id": bus_id}, {"_id": 0})
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    
    if bus.get('route_id'):
        route = await db.routes.find_one({"route_id": bus['route_id']}, {"_id": 0})
        bus['route_data'] = route if route else None
    
    return bus

@api_router.post("/buses")
async def create_bus(bus: Bus, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.buses.insert_one(bus.model_dump())
    return bus

@api_router.put("/buses/{bus_id}")
async def update_bus(bus_id: str, bus: Bus, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.buses.update_one(
        {"bus_id": bus_id},
        {"$set": bus.model_dump()}
    )
    return bus

@api_router.delete("/buses/{bus_id}")
async def delete_bus(bus_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.buses.delete_one({"bus_id": bus_id})
    return {"status": "deleted"}

# Route APIs
@api_router.get("/routes")
async def get_routes():
    routes = await db.routes.find({}, {"_id": 0}).to_list(1000)
    return routes

@api_router.get("/routes/{route_id}")
async def get_route(route_id: str):
    route = await db.routes.find_one({"route_id": route_id}, {"_id": 0})
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Get stops details
    stops = []
    for stop_id in route.get('stop_ids', []):
        stop = await db.stops.find_one({"stop_id": stop_id}, {"_id": 0})
        if stop:
            stops.append(stop)
    
    route['stops'] = sorted(stops, key=lambda x: x['order_index'])
    return route

@api_router.post("/routes")
async def create_route(route: Route, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.routes.insert_one(route.model_dump())
    return route

@api_router.put("/routes/{route_id}")
async def update_route(route_id: str, route: Route, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.routes.update_one(
        {"route_id": route_id},
        {"$set": route.model_dump()}
    )
    return route

@api_router.delete("/routes/{route_id}")
async def delete_route(route_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.routes.delete_one({"route_id": route_id})
    return {"status": "deleted"}

# Stop APIs
@api_router.get("/stops")
async def get_stops():
    stops = await db.stops.find({}, {"_id": 0}).to_list(1000)
    return stops

@api_router.post("/stops")
async def create_stop(stop: Stop, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.stops.insert_one(stop.model_dump())
    return stop

@api_router.delete("/stops/{stop_id}")
async def delete_stop(stop_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.stops.delete_one({"stop_id": stop_id})
    return {"status": "deleted"}

# Email logs
@api_router.get("/email_logs")
async def get_email_logs(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    logs = await db.email_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(100).to_list(100)
    return logs

# Admin CRUD
@api_router.get("/admin/students")
async def admin_get_students(current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    students = await db.students.find({}, {"_id": 0}).to_list(1000)
    return students

@api_router.get("/admin/holidays")
async def get_holidays(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    holidays = await db.holidays.find({}, {"_id": 0}).to_list(1000)
    return holidays

@api_router.post("/admin/holidays")
async def create_holiday(holiday: Holiday, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.holidays.insert_one(holiday.model_dump())
    return holiday

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
        
        # Add bus info
        if student.get('bus_id'):
            bus = await db.buses.find_one({"bus_id": student['bus_id']}, {"_id": 0})
            student['bus_number'] = bus['bus_number'] if bus else 'N/A'
        else:
            student['bus_number'] = 'N/A'
        
        # Add parent info
        if student.get('parent_id'):
            parent = await db.users.find_one({"user_id": student['parent_id']}, {"_id": 0})
            student['parent_name'] = parent['name'] if parent else 'N/A'
        else:
            student['parent_name'] = 'N/A'
    
    return students

# Parent endpoint
@api_router.get("/parent/students")
async def get_parent_students(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'parent':
        raise HTTPException(status_code=403, detail="Access denied")
    
    student_ids = current_user.get('student_ids', [])
    students = await db.students.find({"student_id": {"$in": student_ids}}, {"_id": 0}).to_list(1000)
    return students

# Demo endpoints
@api_router.post("/demo/simulate_scan")
async def simulate_scan():
    students = await db.students.find({}, {"_id": 0}).to_list(1000)
    if not students:
        raise HTTPException(status_code=404, detail="No students found")
    
    student = random.choice(students)
    verified = random.choice([True, True, True, False])
    confidence = random.uniform(0.85, 0.99) if verified else random.uniform(0.40, 0.70)
    
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
    current = await db.bus_locations.find_one({"bus_id": bus_id}, {"_id": 0})
    
    if current:
        lat = current['lat'] + random.uniform(-0.001, 0.001)
        lon = current['lon'] + random.uniform(-0.001, 0.001)
    else:
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
