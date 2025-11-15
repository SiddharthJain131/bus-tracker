from fastapi import FastAPI, APIRouter, HTTPException, Depends, Cookie, Response, UploadFile, File, Header
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
import subprocess
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import secrets
import random
import shutil
import hashlib

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
    is_elevated_admin: bool = False

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    assigned_class: Optional[str] = None
    assigned_section: Optional[str] = None
    address: Optional[str] = None
    is_elevated_admin: Optional[bool] = None

class UserCreate(BaseModel):
    email: str
    password: str
    role: str  # parent, teacher, admin
    name: str
    phone: Optional[str] = None
    photo: Optional[str] = None
    assigned_class: Optional[str] = None
    assigned_section: Optional[str] = None
    address: Optional[str] = None
    is_elevated_admin: bool = False

class UserLogin(BaseModel):
    email: str
    password: str

class Student(BaseModel):
    model_config = ConfigDict(extra="ignore")
    student_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    roll_number: str  # Required for uniqueness constraint
    tag_id: str  # RFID tag identifier for Pi scanning (unique per student)
    phone: Optional[str] = None
    photo: Optional[str] = None
    embedding: Optional[str] = None  # Face embedding data (base64 encoded)
    class_name: str  # Required for uniqueness constraint
    section: str  # Required for uniqueness constraint
    parent_id: str
    teacher_id: Optional[str] = None
    bus_number: str
    stop_id: Optional[str] = None
    emergency_contact: Optional[str] = None
    remarks: Optional[str] = None

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    roll_number: Optional[str] = None
    tag_id: Optional[str] = None
    phone: Optional[str] = None
    class_name: Optional[str] = None
    section: Optional[str] = None
    parent_id: Optional[str] = None
    teacher_id: Optional[str] = None
    bus_number: Optional[str] = None
    stop_id: Optional[str] = None
    emergency_contact: Optional[str] = None
    remarks: Optional[str] = None

class Bus(BaseModel):
    model_config = ConfigDict(extra="ignore")
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
    morning_expected_time: Optional[str] = None  # HH:MM format
    evening_expected_time: Optional[str] = None  # HH:MM format

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
    scan_photo: Optional[str] = None  # Photo URL captured during scan
    scan_timestamp: Optional[str] = None  # ISO format timestamp of scan

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
    bus_number: str
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
    photo_url: Optional[str] = None  # Optional photo URL captured during scan
    # Note: scan_type removed - status determined automatically by backend

class UpdateLocationRequest(BaseModel):
    bus_number: str
    lat: float
    lon: float

class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: Optional[str] = None
    timestamp: str
    read: bool = False
    type: str  # mismatch, missed_boarding, update

class Holiday(BaseModel):
    model_config = ConfigDict(extra="ignore")
    holiday_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str  # YYYY-MM-DD
    name: str
    description: str = ""  # Optional description field

class DeviceKey(BaseModel):
    model_config = ConfigDict(extra="ignore")
    device_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bus_number: str  # Links device to bus (1:1 relationship)
    device_name: str
    key_hash: str  # Hashed API key (using bcrypt)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class DeviceKeyCreate(BaseModel):
    bus_number: str
    device_name: str

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

# Helper function to convert photo path to URL
def get_photo_url(photo_path: Optional[str]) -> Optional[str]:
    """
    Convert backend photo path to accessible URL.
    Example: "backend/photos/admins/abc123.jpg" -> "/api/photos/admins/abc123.jpg"
    
    Note: Uses /api/photos prefix to match Kubernetes ingress routing rules
    that redirect /api/* requests to backend port 8001.
    """
    if not photo_path:
        return None
    # Remove 'backend/' prefix if present
    if photo_path.startswith('backend/'):
        photo_path = photo_path[8:]  # Remove 'backend/'
    # Ensure path starts with /api/photos/
    if not photo_path.startswith('/api/photos/'):
        if photo_path.startswith('photos/'):
            photo_path = '/api/' + photo_path
        elif photo_path.startswith('/photos/'):
            photo_path = '/api' + photo_path
        else:
            photo_path = '/api/photos/' + photo_path
    return photo_path

# Device API Key verification helper
async def verify_device_key(x_api_key: str = Header(...)):
    """
    Dependency to verify device API key from X-API-Key header.
    Validates against hashed keys stored in device_keys collection.
    """
    if not x_api_key:
        raise HTTPException(status_code=403, detail="Missing X-API-Key header")
    
    # Hash the provided key to compare with stored hash
    # Get all device keys and check each one
    device_keys = await db.device_keys.find({}, {"_id": 0}).to_list(1000)
    
    for device_key in device_keys:
        # Verify the key using bcrypt
        if bcrypt.checkpw(x_api_key.encode('utf-8'), device_key['key_hash'].encode('utf-8')):
            return device_key  # Return the device info if valid
    
    # If no match found, raise 403
    raise HTTPException(status_code=403, detail="Invalid or expired API key")

# Auth endpoints
@api_router.post("/auth/login")
async def login(user_login: UserLogin, response: Response):
    logging.info(f"Login attempt for email: {user_login.email}")
    user = await db.users.find_one({"email": user_login.email}, {"_id": 0})
    if not user:
        logging.warning(f"User not found: {user_login.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    logging.info(f"User found: {user['name']} ({user['role']})")
    
    try:
        password_valid = bcrypt.checkpw(user_login.password.encode('utf-8'), user['password_hash'].encode('utf-8'))
        logging.info(f"Password verification result: {password_valid}")
        if not password_valid:
            logging.warning(f"Invalid password for user: {user_login.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        logging.error(f"Password verification error: {e}")
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
        "photo": get_photo_url(user.get('photo')),
        "assigned_class": user.get('assigned_class'),
        "assigned_section": user.get('assigned_section'),
        "student_ids": user.get('student_ids', []),
        "is_elevated_admin": user.get('is_elevated_admin', False)
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
        "photo": get_photo_url(current_user.get('photo')),
        "address": current_user.get('address'),
        "assigned_class": current_user.get('assigned_class'),
        "assigned_section": current_user.get('assigned_section'),
        "student_ids": current_user.get('student_ids', []),
        "is_elevated_admin": current_user.get('is_elevated_admin', False)
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
        
        return {"photo_url": f"/api/photos/{file_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Update user's own photo
@api_router.put("/users/me/photo")
async def update_my_photo(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Allow any authenticated user to update their own profile photo
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            raise HTTPException(status_code=400, detail="Invalid image format. Use jpg, jpeg, png, gif, or webp")
        
        # Determine photo directory based on role
        role_dirs = {
            'admin': 'admins',
            'teacher': 'teachers',
            'parent': 'parents'
        }
        role_dir = role_dirs.get(current_user['role'])
        if not role_dir:
            raise HTTPException(status_code=400, detail="Invalid user role")
        
        # Create role directory if it doesn't exist
        role_path = PHOTO_DIR / role_dir
        role_path.mkdir(parents=True, exist_ok=True)
        
        # Save with user_id as filename
        file_name = f"{current_user['user_id']}.{file_ext}"
        file_path = role_path / file_name
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update database
        photo = f"/api/photos/{role_dir}/{file_name}"
        await db.users.update_one(
            {"user_id": current_user['user_id']},
            {"$set": {"photo": photo}}
        )
        
        return {"success": True, "photo_url": photo, "message": "Photo updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating user photo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin: Update student photo
@api_router.put("/students/{student_id}/photo")
async def update_student_photo(student_id: str, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Admin-only endpoint to update a student's profile photo
    """
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can update student photos")
    
    try:
        # Validate student exists
        student = await db.students.find_one({"student_id": student_id})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            raise HTTPException(status_code=400, detail="Invalid image format. Use jpg, jpeg, png, gif, or webp")
        
        # Create student directory if it doesn't exist
        student_dir = PHOTO_DIR / 'students' / student_id
        student_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as profile.jpg
        file_name = f"profile.{file_ext}"
        file_path = student_dir / file_name
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update database
        photo = f"/api/photos/students/{student_id}/profile.{file_ext}"
        await db.students.update_one(
            {"student_id": student_id},
            {"$set": {"photo": photo}}
        )
        
        return {"success": True, "photo_url": photo, "message": "Student photo updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating student photo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Device API Key Management
@api_router.post("/device/register")
async def register_device(device_create: DeviceKeyCreate, current_user: dict = Depends(get_current_user)):
    """
    Admin-only endpoint to register a new device and generate an API key.
    The API key is displayed only once and must be stored securely by the admin.
    """
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can register devices")
    
    # Check if bus exists
    bus = await db.buses.find_one({"bus_number": device_create.bus_number}, {"_id": 0})
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    
    # Check if device already exists for this bus
    existing_device = await db.device_keys.find_one({"bus_number": device_create.bus_number}, {"_id": 0})
    if existing_device:
        raise HTTPException(status_code=400, detail=f"Device already registered for bus {bus['bus_number']}")
    
    # Generate secure API key (64 characters)
    api_key = secrets.token_hex(32)
    
    # Hash the API key using bcrypt
    key_hash = bcrypt.hashpw(api_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create device key record
    device_key = DeviceKey(
        bus_number=device_create.bus_number,
        device_name=device_create.device_name,
        key_hash=key_hash
    )
    
    await db.device_keys.insert_one(device_key.model_dump())
    
    logging.info(f"Device registered: {device_create.device_name} for bus {bus['bus_number']}")
    
    # Return the API key ONCE - it cannot be retrieved later
    return {
        "message": "Device registered successfully",
        "device_id": device_key.device_id,
        "bus_number": device_create.bus_number,
        "device_name": device_create.device_name,
        "api_key": api_key,  # ONLY TIME THIS IS SHOWN
        "warning": "Store this API key securely. It cannot be retrieved later.",
        "created_at": device_key.created_at
    }

@api_router.get("/device/list")
async def list_devices(current_user: dict = Depends(get_current_user)):
    """
    Admin-only endpoint to list all registered devices (without API keys).
    """
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can list devices")
    
    devices = await db.device_keys.find({}, {"_id": 0, "key_hash": 0}).to_list(1000)
    
    # bus_number is already in device records, no need for enrichment
    return devices

# Device-Only Endpoints (require X-API-Key header)
@api_router.get("/students/{student_id}/embedding")
async def get_student_embedding(student_id: str, device: dict = Depends(verify_device_key)):
    """
    Device-only endpoint to retrieve student face embedding data.
    Used by Raspberry Pi for local face verification.
    """
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    embedding = student.get('embedding', '')
    
    return {
        "student_id": student_id,
        "name": student['name'],
        "embedding": embedding,
        "has_embedding": bool(embedding)
    }

@api_router.get("/students/{student_id}/photo")
async def get_student_photo(student_id: str, device: dict = Depends(verify_device_key)):
    """
    Device-only endpoint to retrieve student photo.
    Used by Raspberry Pi as fallback when embedding is not available.
    """
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    photo_url = student.get('photo', '')
    
    return {
        "student_id": student_id,
        "name": student['name'],
        "photo_url": photo_url,
        "has_photo": bool(photo_url)
    }

# Core APIs
@api_router.post("/scan_event")
async def scan_event(request: ScanEventRequest, device: dict = Depends(verify_device_key)):
    """
    Device-only endpoint for recording RFID scan events.
    Requires X-API-Key header authentication.
    Automatically determines status (YELLOW/GREEN) based on:
    - Time of day (morning < 12:00 PM, evening >= 12:00 PM)
    - Scan sequence (first scan = IN/YELLOW, second scan = GREEN)
    - Direction logic (morning: pickup->school, evening: school->home)
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    current_time = datetime.now(timezone.utc)
    
    # Record the scan event
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
    
    today = current_time.strftime("%Y-%m-%d")
    hour = current_time.hour
    
    # Determine trip direction based on time of day
    # Morning: before 12:00 PM (first scan at pickup = IN/YELLOW, second at school = GREEN)
    # Evening: at or after 12:00 PM (first scan at school = IN/YELLOW, second at home = OUT/GREEN)
    is_morning = hour < 12
    trip = "AM" if is_morning else "PM"
    
    existing = await db.attendance.find_one({
        "student_id": request.student_id,
        "date": today,
        "trip": trip
    })
    
    if request.verified:
        # Determine status based on scan sequence
        if existing:
            # This is the second scan
            # Morning: student reached school (GREEN)
            # Evening: student reached home (GREEN)
            status = "green"
            
            update_data = {
                "status": status, 
                "confidence": request.confidence, 
                "last_update": timestamp
            }
            
            # Add photo and scan timestamp if provided
            if request.photo_url:
                update_data["scan_photo"] = request.photo_url
                update_data["scan_timestamp"] = timestamp
            
            await db.attendance.update_one(
                {"student_id": request.student_id, "date": today, "trip": trip},
                {"$set": update_data}
            )
        else:
            # This is the first scan
            # Morning: student boarded at pickup stop (IN/YELLOW)
            # Evening: student boarded at school (IN/YELLOW)
            status = "yellow"
            
            attendance = Attendance(
                student_id=request.student_id,
                date=today,
                trip=trip,
                status=status,
                confidence=request.confidence,
                last_update=timestamp,
                scan_photo=request.photo_url,
                scan_timestamp=timestamp if request.photo_url else None
            )
            await db.attendance.insert_one(attendance.model_dump())
        
        direction = "morning" if is_morning else "evening"
        scan_sequence = "second" if existing else "first"
        logging.info(f"Scan event recorded: Student {request.student_id}, Direction: {direction}, Sequence: {scan_sequence}, Status: {status}, Device: {device['device_name']}")
    else:
        # Identity mismatch - create notification for parent
        student = await db.students.find_one({"student_id": request.student_id}, {"_id": 0})
        if student:
            notification = Notification(
                user_id=student['parent_id'],
                title="Identity Mismatch Detected",
                message=f"Identity mismatch detected for {student['name']} (Confidence: {request.confidence:.0%})",
                timestamp=timestamp,
                type="mismatch"
            )
            await db.notifications.insert_one(notification.model_dump())
        status = "not_recorded"
    
    return {"status": "success", "event_id": event.event_id, "attendance_status": status}

@api_router.post("/update_location")
async def update_location(request: UpdateLocationRequest, device: dict = Depends(verify_device_key)):
    """
    Device-only endpoint for updating bus GPS location.
    Requires X-API-Key header authentication.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Verify that the device is authorized for this bus
    if device['bus_number'] != request.bus_number:
        raise HTTPException(status_code=403, detail="Device not authorized for this bus")
    
    location = BusLocation(
        bus_number=request.bus_number,
        lat=request.lat,
        lon=request.lon,
        timestamp=timestamp
    )
    
    await db.bus_locations.update_one(
        {"bus_number": request.bus_number},
        {"$set": location.model_dump()},
        upsert=True
    )
    
    logging.info(f"Location updated for bus {request.bus_number} by device {device['device_name']}")
    
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
            "pm_confidence": pm_record['confidence'] if pm_record else None,
            "am_scan_photo": am_record.get('scan_photo') if am_record else None,
            "am_scan_timestamp": am_record.get('scan_timestamp') if am_record else None,
            "pm_scan_photo": pm_record.get('scan_photo') if pm_record else None,
            "pm_scan_timestamp": pm_record.get('scan_timestamp') if pm_record else None
        })
    
    total_days = last_day * 2
    present_count = sum(1 for r in attendance_records if r['status'] in ['yellow', 'green'])
    
    return {
        "grid": grid,
        "summary": f"{present_count} / {total_days} sessions"
    }

@api_router.get("/get_bus_location")
async def get_bus_location(bus_number: str, device: dict = Depends(verify_device_key)):
    """
    Device-only endpoint for retrieving bus GPS location.
    Requires X-API-Key header authentication.
    """
    location = await db.bus_locations.find_one({"bus_number": bus_number}, {"_id": 0})
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
        
        # bus_number is already in student record, no need to fetch
        if not student.get('bus_number'):
            student['bus_number'] = 'N/A'
        
        # Enrich with stop name and times
        if student.get('stop_id'):
            stop = await db.stops.find_one({"stop_id": student['stop_id']}, {"_id": 0})
            if stop:
                student['stop_name'] = stop['stop_name']
                student['morning_expected_time'] = stop.get('morning_expected_time', 'N/A')
                student['evening_expected_time'] = stop.get('evening_expected_time', 'N/A')
            else:
                student['stop_name'] = 'N/A'
                student['morning_expected_time'] = 'N/A'
                student['evening_expected_time'] = 'N/A'
        else:
            student['stop_name'] = 'N/A'
            student['morning_expected_time'] = 'N/A'
            student['evening_expected_time'] = 'N/A'
        
        # Convert photo to accessible URL (photo field already contains the URL)
        if student.get('photo'):
            student['photo_url'] = student['photo']
        else:
            student['photo_url'] = None
    
    return students

@api_router.get("/students/class-sections")
async def get_class_sections():
    """Get all unique class-section combinations for autocomplete"""
    try:
        # Get distinct combinations of class_name and section from students collection
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "class_name": "$class_name",
                        "section": "$section"
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "class_name": "$_id.class_name",
                    "section": "$_id.section"
                }
            },
            {
                "$sort": {"class_name": 1, "section": 1}
            }
        ]
        
        combinations = await db.students.aggregate(pipeline).to_list(length=None)
        
        # Format as "5A" style
        formatted = []
        for combo in combinations:
            if combo.get('class_name') and combo.get('section'):
                # Extract just the number from class_name (e.g., "Grade 5" -> "5")
                class_num = combo['class_name'].replace('Grade', '').replace('Class', '').strip()
                formatted.append(f"{class_num}{combo['section']}")
        
        return formatted
    except Exception as e:
        print(f"Error fetching class-sections: {str(e)}")
        return []

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
    
    # bus_number is already in student record, no need to fetch
    if not student.get('bus_number'):
        student['bus_number'] = 'N/A'
    
    # Still need to fetch route_id from bus if needed
    if student.get('bus_number'):
        bus = await db.buses.find_one({"bus_number": student['bus_number']}, {"_id": 0})
        student['route_id'] = bus.get('route_id') if bus else None
    else:
        student['route_id'] = None
    
    # Enrich with stop name and times
    if student.get('stop_id'):
        stop = await db.stops.find_one({"stop_id": student['stop_id']}, {"_id": 0})
        if stop:
            student['stop_name'] = stop['stop_name']
            student['morning_expected_time'] = stop.get('morning_expected_time', 'N/A')
            student['evening_expected_time'] = stop.get('evening_expected_time', 'N/A')
        else:
            student['stop_name'] = 'N/A'
            student['morning_expected_time'] = 'N/A'
            student['evening_expected_time'] = 'N/A'
    else:
        student['stop_name'] = 'N/A'
        student['morning_expected_time'] = 'N/A'
        student['evening_expected_time'] = 'N/A'
    
    # Convert photo to accessible URL (photo field already contains the URL)
    if student.get('photo'):
        student['photo_url'] = student['photo']
    else:
        student['photo_url'] = None
    
    return student

@api_router.post("/students")
async def create_student(student: Student, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate roll_number uniqueness per class+section
    if student.roll_number and student.class_name and student.section:
        existing = await db.students.find_one({
            "roll_number": student.roll_number,
            "class_name": student.class_name,
            "section": student.section
        })
        if existing:
            raise HTTPException(status_code=400, detail=f"Roll number {student.roll_number} already exists in {student.class_name} - {student.section}")
    
    # Check bus capacity before creating student
    capacity_warning = None
    if student.bus_id:
        bus = await db.buses.find_one({"bus_id": student.bus_id}, {"_id": 0})
        if bus:
            current_count = await db.students.count_documents({"bus_id": student.bus_id})
            bus_capacity = bus.get('capacity', 0)
            new_count = current_count + 1
            
            if new_count > bus_capacity:
                capacity_warning = f"Warning: Bus {bus['bus_number']} capacity ({bus_capacity}) will be exceeded. Current: {current_count}, After: {new_count}"
                print(f"⚠️ CAPACITY WARNING: {capacity_warning}")
    
    await db.students.insert_one(student.model_dump())
    
    # Update parent's student_ids array (supports multiple students per parent)
    if student.parent_id:
        await db.users.update_one(
            {"user_id": student.parent_id},
            {"$addToSet": {"student_ids": student.student_id}}
        )
    
    # Update teacher's student_ids array if teacher is assigned
    if student.teacher_id:
        await db.users.update_one(
            {"user_id": student.teacher_id},
            {"$addToSet": {"student_ids": student.student_id}}
        )
    
    # Return student with capacity warning if applicable
    response = student.model_dump()
    if capacity_warning:
        response['capacity_warning'] = capacity_warning
    
    return response

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
    
    # Validate roll_number uniqueness if any of the composite key fields are being updated
    if 'roll_number' in update_data or 'class_name' in update_data or 'section' in update_data:
        # Get the final values (updated or existing)
        final_roll_number = update_data.get('roll_number', old_student.get('roll_number'))
        final_class_name = update_data.get('class_name', old_student.get('class_name'))
        final_section = update_data.get('section', old_student.get('section'))
        
        # Check if another student has this combination
        existing = await db.students.find_one({
            "roll_number": final_roll_number,
            "class_name": final_class_name,
            "section": final_section,
            "student_id": {"$ne": student_id}  # Exclude current student
        })
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"A student with this roll number already exists in class {final_class_name}{final_section}."
            )
    
    # Check bus capacity if bus is being changed
    capacity_warning = None
    if 'bus_id' in update_data and update_data['bus_id'] != old_student.get('bus_id'):
        new_bus_id = update_data['bus_id']
        bus = await db.buses.find_one({"bus_id": new_bus_id}, {"_id": 0})
        if bus:
            # Count students currently on this bus (excluding current student)
            current_count = await db.students.count_documents({
                "bus_id": new_bus_id,
                "student_id": {"$ne": student_id}
            })
            bus_capacity = bus.get('capacity', 0)
            new_count = current_count + 1
            
            if new_count > bus_capacity:
                capacity_warning = f"Warning: Bus {bus['bus_number']} capacity ({bus_capacity}) will be exceeded. Current: {current_count}, After: {new_count}"
                print(f"⚠️ CAPACITY WARNING: {capacity_warning}")
    
    # Handle parent change - update both old and new parent's student_ids
    if 'parent_id' in update_data and update_data['parent_id'] != old_student.get('parent_id'):
        old_parent_id = old_student.get('parent_id')
        new_parent_id = update_data['parent_id']
        
        # Remove from old parent's student_ids
        if old_parent_id:
            await db.users.update_one(
                {"user_id": old_parent_id},
                {"$pull": {"student_ids": student_id}}
            )
        
        # Add to new parent's student_ids (supports multiple students per parent)
        if new_parent_id:
            await db.users.update_one(
                {"user_id": new_parent_id},
                {"$addToSet": {"student_ids": student_id}}
            )
    
    await db.students.update_one(
        {"student_id": student_id},
        {"$set": update_data}
    )
    
    # Send email notification to parent if admin updated
    if current_user['role'] == 'admin':
        # Get current parent (after update)
        updated_student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
        parent = await db.users.find_one({"user_id": updated_student['parent_id']}, {"_id": 0})
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
    
    # Return response with capacity warning if applicable
    response = {"status": "updated"}
    if capacity_warning:
        response['capacity_warning'] = capacity_warning
    
    return response

@api_router.delete("/students/{student_id}")
async def delete_student(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if student exists
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check for dependent attendance records
    attendance_count = await db.attendance.count_documents({"student_id": student_id})
    if attendance_count > 0:
        raise HTTPException(
            status_code=409, 
            detail=f"Cannot delete student. {attendance_count} attendance record(s) exist. Please delete attendance records first or archive the student."
        )
    
    # Check for dependent notifications
    notification_count = await db.notifications.count_documents({"student_id": student_id})
    if notification_count > 0:
        # Soft warning - we can cascade delete notifications
        await db.notifications.delete_many({"student_id": student_id})
    
    await db.students.delete_one({"student_id": student_id})
    return {
        "status": "deleted",
        "student_id": student_id,
        "cascaded_notifications": notification_count
    }

# User APIs
@api_router.get("/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    
    # Convert photo to accessible URL (photo field already contains the URL)
    for user in users:
        if user.get('photo'):
            user['photo_url'] = user['photo']
        else:
            user['photo_url'] = None
    
    return users

@api_router.post("/users")
async def create_user(user_data: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Hash the password using bcrypt (consistent with login)
    password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create user object
    user = User(
        user_id=str(uuid.uuid4()),
        email=user_data.email,
        password_hash=password_hash,
        role=user_data.role,
        name=user_data.name,
        phone=user_data.phone,
        photo=user_data.photo,
        assigned_class=user_data.assigned_class,
        assigned_section=user_data.assigned_section,
        address=user_data.address,
        student_ids=[]
    )
    
    await db.users.insert_one(user.model_dump())
    
    # Return user without password_hash
    user_dict = user.model_dump()
    user_dict.pop('password_hash')
    return user_dict

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, updates: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get target user
    target_user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check elevated admin permissions
    is_elevated = current_user.get('is_elevated_admin', False)
    is_editing_self = user_id == current_user['user_id']
    
    # Cannot edit another admin unless you are elevated admin
    if target_user['role'] == 'admin' and not is_editing_self and not is_elevated:
        raise HTTPException(status_code=403, detail="Only elevated admins can edit other admins")
    
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

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Cannot delete yourself
    if user_id == current_user['user_id']:
        raise HTTPException(status_code=403, detail="Cannot delete your own account")
    
    # Check if user exists
    target_user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check elevated admin permissions
    is_elevated = current_user.get('is_elevated_admin', False)
    
    # Cannot delete another admin unless you are elevated admin
    if target_user['role'] == 'admin' and not is_elevated:
        raise HTTPException(status_code=403, detail="Only elevated admins can delete other admins")
    
    # Count dependent records before deletion
    affected_students = 0
    affected_notifications = 0
    
    # If user is a parent or teacher, check and update student references
    if target_user['role'] == 'parent':
        affected_students = await db.students.count_documents({"parent_id": user_id})
        if affected_students > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete parent. {affected_students} student(s) are linked to this parent. Please reassign or delete students first."
            )
    elif target_user['role'] == 'teacher':
        affected_students = await db.students.count_documents({"teacher_id": user_id})
        if affected_students > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete teacher. {affected_students} student(s) are assigned to this teacher. Please reassign students first."
            )
    
    # Cascade delete notifications for this user
    affected_notifications = await db.notifications.count_documents({"user_id": user_id})
    if affected_notifications > 0:
        await db.notifications.delete_many({"user_id": user_id})
    
    # Delete the user
    await db.users.delete_one({"user_id": user_id})
    
    return {
        "status": "deleted",
        "user_id": user_id,
        "role": target_user['role'],
        "cascaded_notifications": affected_notifications
    }


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

@api_router.get("/buses/{bus_id}/stops")
async def get_bus_stops(bus_id: str):
    """Get all stops for a specific bus via its route"""
    # Get bus
    bus = await db.buses.find_one({"bus_id": bus_id}, {"_id": 0})
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    
    # Check if bus has a route
    if not bus.get('route_id'):
        return []  # Return empty list if no route assigned
    
    # Get route with stops
    route = await db.routes.find_one({"route_id": bus['route_id']}, {"_id": 0})
    if not route:
        return []
    
    # Fetch all stops for this route
    stops = []
    for stop_id in route.get('stop_ids', []):
        stop = await db.stops.find_one({"stop_id": stop_id}, {"_id": 0})
        if stop:
            stops.append(stop)
    
    # Sort by order_index if available
    stops = sorted(stops, key=lambda x: x.get('order_index', 0))
    
    return stops


@api_router.get("/parents/all")
async def get_all_parents(current_user: dict = Depends(get_current_user)):
    """Get all parent users - supports many students per parent"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get all parents sorted by name
        all_parents = await db.users.find(
            {"role": "parent"}, 
            {"_id": 0, "password_hash": 0}
        ).sort("name", 1).to_list(length=None)
        
        return all_parents
    except Exception as e:
        print(f"Error fetching parents: {str(e)}")
        return []


@api_router.get("/parents/unlinked")
async def get_unlinked_parents(current_user: dict = Depends(get_current_user)):
    """Get all parent users who are not linked to any student (legacy endpoint)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get all parents
        all_parents = await db.users.find({"role": "parent"}, {"_id": 0}).to_list(length=None)
        
        # Filter parents who have no students linked (empty or no student_ids array)
        unlinked_parents = [
            parent for parent in all_parents 
            if not parent.get('student_ids') or len(parent.get('student_ids', [])) == 0
        ]
        
        return unlinked_parents
    except Exception as e:
        print(f"Error fetching unlinked parents: {str(e)}")
        return []


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
    
    # Check if bus exists
    bus = await db.buses.find_one({"bus_id": bus_id}, {"_id": 0})
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    
    # Check for students assigned to this bus
    student_count = await db.students.count_documents({"bus_id": bus_id})
    if student_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete bus. {student_count} student(s) are assigned to this bus. Please reassign students first."
        )
    
    await db.buses.delete_one({"bus_id": bus_id})
    return {"status": "deleted", "bus_id": bus_id}

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
    
    # Check if route exists
    route = await db.routes.find_one({"route_id": route_id}, {"_id": 0})
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Check for buses using this route
    bus_count = await db.buses.count_documents({"route_id": route_id})
    if bus_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete route. {bus_count} bus(es) are using this route. Please reassign buses first."
        )
    
    # Cascade delete: Remove stops that are only used by this route
    stop_ids = route.get('stop_ids', [])
    for stop_id in stop_ids:
        # Check if stop is used by other routes
        other_routes = await db.routes.count_documents({
            "route_id": {"$ne": route_id},
            "stop_ids": stop_id
        })
        # Check if stop is used by students
        students_using_stop = await db.students.count_documents({"stop_id": stop_id})
        
        # Only delete stop if not used elsewhere
        if other_routes == 0 and students_using_stop == 0:
            await db.stops.delete_one({"stop_id": stop_id})
    
    await db.routes.delete_one({"route_id": route_id})
    return {
        "status": "deleted", 
        "route_id": route_id,
        "cascaded_stops": len([s for s in stop_ids])
    }

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

@api_router.put("/stops/{stop_id}")
async def update_stop(stop_id: str, stop: Stop, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.stops.update_one(
        {"stop_id": stop_id},
        {"$set": stop.model_dump()}
    )
    return stop

@api_router.delete("/stops/{stop_id}")
async def delete_stop(stop_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if stop exists
    stop = await db.stops.find_one({"stop_id": stop_id}, {"_id": 0})
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    
    # Check for students assigned to this stop
    student_count = await db.students.count_documents({"stop_id": stop_id})
    if student_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete stop. {student_count} student(s) are assigned to this stop. Please reassign students first."
        )
    
    # Check for routes using this stop
    route_count = await db.routes.count_documents({"stop_ids": stop_id})
    if route_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete stop. {route_count} route(s) include this stop. Please remove stop from routes first."
        )
    
    await db.stops.delete_one({"stop_id": stop_id})
    return {"status": "deleted", "stop_id": stop_id}

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

@api_router.put("/admin/holidays/{holiday_id}")
async def update_holiday(holiday_id: str, holiday: Holiday, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if holiday exists
    existing = await db.holidays.find_one({"holiday_id": holiday_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    # Update holiday
    update_data = {
        "name": holiday.name,
        "date": holiday.date,
        "description": holiday.description
    }
    await db.holidays.update_one({"holiday_id": holiday_id}, {"$set": update_data})
    
    # Return updated holiday
    updated_holiday = await db.holidays.find_one({"holiday_id": holiday_id}, {"_id": 0})
    return updated_holiday

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
        
        # Add scan photos and timestamps for clickable status badges
        student['am_scan_photo'] = am_attendance.get('scan_photo') if am_attendance else None
        student['am_scan_timestamp'] = am_attendance.get('scan_timestamp') if am_attendance else None
        student['pm_scan_photo'] = pm_attendance.get('scan_photo') if pm_attendance else None
        student['pm_scan_timestamp'] = pm_attendance.get('scan_timestamp') if pm_attendance else None
        
        # Add bus info
        # bus_number is already in student record, no need to fetch
        if not student.get('bus_number'):
            student['bus_number'] = 'N/A'
        
        # Add parent info
        if student.get('parent_id'):
            parent = await db.users.find_one({"user_id": student['parent_id']}, {"_id": 0})
            student['parent_name'] = parent['name'] if parent else 'N/A'
        else:
            student['parent_name'] = 'N/A'
        
        # Add stop name and times
        if student.get('stop_id'):
            stop = await db.stops.find_one({"stop_id": student['stop_id']}, {"_id": 0})
            if stop:
                student['stop_name'] = stop['stop_name']
                student['morning_expected_time'] = stop.get('morning_expected_time', 'N/A')
                student['evening_expected_time'] = stop.get('evening_expected_time', 'N/A')
            else:
                student['stop_name'] = 'N/A'
                student['morning_expected_time'] = 'N/A'
                student['evening_expected_time'] = 'N/A'
        else:
            student['stop_name'] = 'N/A'
            student['morning_expected_time'] = 'N/A'
            student['evening_expected_time'] = 'N/A'
    
    return students

# Parent endpoint
@api_router.get("/parent/students")
async def get_parent_students(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'parent':
        raise HTTPException(status_code=403, detail="Access denied")
    
    student_ids = current_user.get('student_ids', [])
    students = await db.students.find({"student_id": {"$in": student_ids}}, {"_id": 0}).to_list(1000)
    
    # Enrich with stop name and times, bus info, teacher info
    for student in students:
        # Add teacher info
        if student.get('teacher_id'):
            teacher = await db.users.find_one({"user_id": student['teacher_id']}, {"_id": 0})
            student['teacher_name'] = teacher['name'] if teacher else 'N/A'
        else:
            student['teacher_name'] = 'N/A'
        
        # Add bus info
        # bus_number is already in student record, no need to fetch
        if not student.get('bus_number'):
            student['bus_number'] = 'N/A'
        
        # Add stop name and times
        if student.get('stop_id'):
            stop = await db.stops.find_one({"stop_id": student['stop_id']}, {"_id": 0})
            if stop:
                student['stop_name'] = stop['stop_name']
                student['morning_expected_time'] = stop.get('morning_expected_time', 'N/A')
                student['evening_expected_time'] = stop.get('evening_expected_time', 'N/A')
            else:
                student['stop_name'] = 'N/A'
                student['morning_expected_time'] = 'N/A'
                student['evening_expected_time'] = 'N/A'
        else:
            student['stop_name'] = 'N/A'
            student['morning_expected_time'] = 'N/A'
            student['evening_expected_time'] = 'N/A'
        
        # Convert photo to accessible URL (photo field already contains the URL)
        if student.get('photo'):
            student['photo_url'] = student['photo']
        else:
            student['photo_url'] = None
    
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
    
    # Generate photo URL for the scan (matches new naming convention: YYYY-MM-DD_{AM|PM}.jpg)
    # No status suffix (_green or _yellow) - the same photo is used for both IN and OUT scans
    current_time = datetime.now(timezone.utc)
    today = current_time.strftime("%Y-%m-%d")
    trip = "AM" if current_time.hour < 12 else "PM"
    photo_url = f"/api/photos/students/{student['student_id']}/attendance/{today}_{trip}.jpg"
    
    request = ScanEventRequest(
        student_id=student['student_id'],
        tag_id=f"RFID-{random.randint(1000, 9999)}",
        verified=verified,
        confidence=confidence,
        lat=lat,
        lon=lon,
        photo_url=photo_url
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

# Mount static files for photos under /api prefix to match Kubernetes ingress routing
app.mount("/api/photos", StaticFiles(directory=str(PHOTO_DIR)), name="photos")

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

# Background task functions
async def start_attendance_monitor():
    """Start the attendance monitoring daemon in background"""
    RED_STATUS_THRESHOLD = int(os.environ.get('RED_STATUS_THRESHOLD', '10'))
    CHECK_INTERVAL = 60  # Check every 60 seconds
    
    logging.info("=" * 60)
    logging.info("🚨 ATTENDANCE MONITOR STARTED")
    logging.info(f"Configuration: Threshold={RED_STATUS_THRESHOLD}min, Interval={CHECK_INTERVAL}s")
    logging.info("=" * 60)
    
    while True:
        try:
            await check_missed_scans()
            await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            logging.error(f"Attendance monitor error: {e}")
            await asyncio.sleep(CHECK_INTERVAL)


async def check_missed_scans():
    """Check for students who should have been scanned but weren't"""
    current_time = datetime.now(timezone.utc)
    current_hour = current_time.hour
    today = current_time.strftime("%Y-%m-%d")
    
    is_morning = current_hour < 12
    trip = "AM" if is_morning else "PM"
    
    RED_STATUS_THRESHOLD = int(os.environ.get('RED_STATUS_THRESHOLD', '10'))
    
    # Get all students with assigned stops
    students_cursor = db.students.find({"stop_id": {"$exists": True, "$ne": None}})
    
    marked_red_count = 0
    
    async for student in students_cursor:
        try:
            student_id = student['student_id']
            stop_id = student.get('stop_id')
            
            if not stop_id:
                continue
            
            # Get stop with expected times
            stop = await db.stops.find_one({"stop_id": stop_id}, {"_id": 0})
            if not stop:
                continue
            
            # Get expected time for current direction
            expected_time_str = stop.get('morning_expected_time') if is_morning else stop.get('evening_expected_time')
            if not expected_time_str:
                continue
            
            # Parse expected time (HH:MM format)
            try:
                hour, minute = map(int, expected_time_str.split(':'))
                expected_datetime = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                threshold_datetime = expected_datetime + timedelta(minutes=RED_STATUS_THRESHOLD)
            except:
                continue
            
            # Check if we're past the threshold
            if current_time < threshold_datetime:
                continue
            
            # Check attendance record
            attendance = await db.attendance.find_one({
                "student_id": student_id,
                "date": today,
                "trip": trip
            })
            
            if not attendance:
                # No scan - mark as RED
                red_attendance = Attendance(
                    student_id=student_id,
                    date=today,
                    trip=trip,
                    status="red",
                    confidence=0.0,
                    last_update=current_time.isoformat()
                )
                await db.attendance.insert_one(red_attendance.model_dump())
                marked_red_count += 1
                logging.warning(f"Marked RED: Student {student_id} - No scan for {trip} (expected {expected_time_str})")
            
            elif attendance.get('status') == 'yellow':
                # Incomplete journey - check duration
                last_update = attendance.get('last_update')
                if last_update:
                    last_update_time = datetime.fromisoformat(last_update)
                    yellow_duration = (current_time - last_update_time).total_seconds() / 60
                    
                    if yellow_duration > RED_STATUS_THRESHOLD:
                        await db.attendance.update_one(
                            {"student_id": student_id, "date": today, "trip": trip},
                            {"$set": {"status": "red", "last_update": current_time.isoformat()}}
                        )
                        marked_red_count += 1
                        logging.warning(f"Marked RED: Student {student_id} - Incomplete journey ({yellow_duration:.1f}min yellow)")
        
        except Exception as e:
            logging.error(f"Error checking student {student.get('student_id')}: {e}")
            continue
    
    if marked_red_count > 0:
        logging.info(f"Scan check: {marked_red_count} students marked RED")


async def start_backup_scheduler():
    """Schedule regular backups for both main and attendance data"""
    BACKUP_INTERVAL_HOURS = int(os.environ.get('SEED_INTERVAL_HOURS', '1'))
    BACKUP_INTERVAL_SECONDS = BACKUP_INTERVAL_HOURS * 3600
    
    logging.info("=" * 60)
    logging.info("💾 BACKUP SCHEDULER STARTED")
    logging.info(f"Configuration: Interval={BACKUP_INTERVAL_HOURS}h")
    logging.info("=" * 60)
    
    while True:
        try:
            await asyncio.sleep(BACKUP_INTERVAL_SECONDS)
            
            # Run main backup
            logging.info("Running scheduled main backup...")
            import subprocess
            subprocess.run(["python", "backup_seed_data.py"], cwd="/app/backend")
            
            # Run attendance backup
            logging.info("Running scheduled attendance backup...")
            subprocess.run(["python", "backup_attendance_data.py"], cwd="/app/backend")
            
            logging.info("✅ Scheduled backups completed")
        except Exception as e:
            logging.error(f"Backup scheduler error: {e}")
            await asyncio.sleep(300)  # Retry in 5 minutes on error


@app.on_event("startup")
async def startup_db_seed():
    """Auto-seed database on first startup if collections are empty and start attendance monitor"""
    try:
        # Create compound unique index for student uniqueness (class, section, roll_number)
        try:
            await db.students.create_index(
                [("class_name", 1), ("section", 1), ("roll_number", 1)],
                unique=True,
                name="unique_class_section_roll"
            )
            print("✅ Compound unique index created: (class_name, section, roll_number)")
        except Exception as idx_error:
            print(f"ℹ️  Index already exists or creation skipped: {str(idx_error)}")
        
        
        print("🪴 Auto-seeding database with initial demo data...")
        from seed_data import seed_data
        await seed_data()
        print("✅ Full auto-seeding completed successfully!")
        
        # Start attendance monitor as background task
        asyncio.create_task(start_attendance_monitor())
        print("🚨 Attendance monitor started in background")
        
        # Start backup scheduler as background task
        asyncio.create_task(start_backup_scheduler())
        print("💾 Backup scheduler started in background")
        
    except Exception as e:
        print(f"⚠️ Auto-seeding skipped due to error: {str(e)}")
        print("   You can manually run seeding with: cd /app/backend && python seed_data.py")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
