#!/usr/bin/env python3
"""
Pi Real-Time Scanner - Simulates Raspberry Pi Device with RFID Scanner

This simulator:
1. Registers as a device and gets API key
2. Runs a continuous scanning thread
3. Simulates RFID scans (one student at a time)
4. For each RFID scan:
   - Fetches student info and embedding from backend API
   - Loads and processes student's profile photo
   - Generates embedding using DeepFace
   - Compares embeddings
   - Sends verification result back to API
"""

import os
import sys
import json
import base64
import requests
import numpy as np
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import queue

# ============================================================
# CONFIGURATION
# ============================================================

# Backend URL
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')

# Admin credentials for device registration
ADMIN_EMAIL = "admin@school.com"
ADMIN_PASSWORD = "password"

# Bus configuration
BUS_ID = "3ca09d6a-2650-40e7-a874-5b2879025aff"  # Default bus ID
DEVICE_NAME = "Pi Scanner Test Device"

# Photo directories
PHOTO_BASE_DIR = Path(__file__).parent.parent / "photos" / "students"

# GPS coordinates (simulated)
GPS_LOCATION = {
    "lat": 37.7749,
    "lon": -122.4194
}

# Scanning configuration
SCAN_INTERVAL = 3  # Seconds between scans
SIMILARITY_THRESHOLD = 0.6

# Device state
device_api_key = None
session_cookie = None
scan_queue = queue.Queue()
scanning_active = False

# ============================================================
# COLOR CODES
# ============================================================
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ============================================================
# DEVICE REGISTRATION
# ============================================================

def admin_login() -> Optional[str]:
    """Login as admin and get session cookie"""
    try:
        print(f"{Colors.CYAN}📝 Logging in as admin...{Colors.RESET}")
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            # Get session cookie
            cookies = response.cookies
            session = cookies.get('session')
            if session:
                print(f"{Colors.GREEN}✓ Admin login successful{Colors.RESET}")
                return session
            else:
                print(f"{Colors.RED}✗ No session cookie received{Colors.RESET}")
                return None
        else:
            print(f"{Colors.RED}✗ Login failed: {response.status_code}{Colors.RESET}")
            print(f"  Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"{Colors.RED}✗ Login error: {e}{Colors.RESET}")
        return None

def register_device(session: str) -> Optional[str]:
    """Register device and get API key"""
    try:
        print(f"{Colors.CYAN}🔑 Registering device...{Colors.RESET}")
        
        response = requests.post(
            f"{BACKEND_URL}/api/device/register",
            headers={'Cookie': f'session={session}'},
            json={"bus_id": BUS_ID, "device_name": DEVICE_NAME},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            api_key = data.get('api_key')
            if api_key:
                print(f"{Colors.GREEN}✓ Device registered successfully{Colors.RESET}")
                print(f"  Device ID: {data.get('device_id')}")
                print(f"  API Key: {api_key[:20]}...{api_key[-10:]}")
                return api_key
            else:
                print(f"{Colors.RED}✗ No API key in response{Colors.RESET}")
                return None
        else:
            print(f"{Colors.YELLOW}⚠ Device may already be registered (Status: {response.status_code}){Colors.RESET}")
            # Try to use existing key from config if available
            from simulator_config import DEVICE_API_KEY
            if DEVICE_API_KEY and DEVICE_API_KEY != "your_device_api_key_here":
                print(f"{Colors.YELLOW}  Using existing API key from config{Colors.RESET}")
                return DEVICE_API_KEY
            return None
            
    except Exception as e:
        print(f"{Colors.RED}✗ Registration error: {e}{Colors.RESET}")
        # Try to use existing key from config
        try:
            from simulator_config import DEVICE_API_KEY
            if DEVICE_API_KEY and DEVICE_API_KEY != "your_device_api_key_here":
                print(f"{Colors.YELLOW}  Using existing API key from config{Colors.RESET}")
                return DEVICE_API_KEY
        except:
            pass
        return None

# ============================================================
# DEEPFACE SETUP
# ============================================================

def check_deepface():
    """Check if DeepFace is available"""
    try:
        import deepface
        from deepface import DeepFace
        return True
    except ImportError:
        print(f"{Colors.RED}✗ DeepFace not installed{Colors.RESET}")
        print(f"{Colors.YELLOW}  Installing DeepFace...{Colors.RESET}")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                                 "deepface", "tf-keras", "tensorflow"])
            print(f"{Colors.GREEN}✓ DeepFace installed{Colors.RESET}")
            return True
        except:
            print(f"{Colors.RED}✗ Failed to install DeepFace{Colors.RESET}")
            return False

def generate_embedding(image_path: str) -> Optional[np.ndarray]:
    """Generate face embedding using DeepFace"""
    try:
        from deepface import DeepFace
        
        embedding_objs = DeepFace.represent(
            img_path=str(image_path),
            model_name='Facenet',
            enforce_detection=False
        )
        
        if embedding_objs and len(embedding_objs) > 0:
            return np.array(embedding_objs[0]['embedding'])
        return None
    except Exception as e:
        print(f"{Colors.RED}  Error generating embedding: {e}{Colors.RESET}")
        return None

def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Calculate cosine similarity"""
    try:
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(emb1, emb2) / (norm1 * norm2))
    except:
        return 0.0

# ============================================================
# API INTERACTIONS
# ============================================================

def get_student_by_rfid(rfid: str) -> Optional[Dict]:
    """Get student info by RFID tag"""
    try:
        headers = {'X-API-Key': device_api_key}
        
        # First get all students (in real implementation, backend should have RFID lookup endpoint)
        response = requests.get(
            f"{BACKEND_URL}/api/students",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            students = response.json()
            # Find student by RFID (this would be a direct lookup in real implementation)
            # For now, we'll match by loading from JSON
            return None  # Will use JSON mapping instead
        return None
    except Exception as e:
        print(f"{Colors.RED}  API error: {e}{Colors.RESET}")
        return None

def get_student_embedding(student_id: str) -> Optional[np.ndarray]:
    """Get student embedding from backend"""
    try:
        headers = {'X-API-Key': device_api_key}
        
        response = requests.get(
            f"{BACKEND_URL}/api/students/{student_id}/embedding",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('has_embedding') and data.get('embedding'):
                embedding_data = data['embedding']
                if isinstance(embedding_data, str):
                    try:
                        embedding_bytes = base64.b64decode(embedding_data)
                        return np.frombuffer(embedding_bytes, dtype=np.float32)
                    except:
                        return None
                else:
                    return np.array(embedding_data)
        return None
    except Exception as e:
        print(f"{Colors.RED}  Embedding fetch error: {e}{Colors.RESET}")
        return None

def send_scan_event(student_id: str, rfid: str, verified: bool, 
                   similarity: float, photo_base64: str, scan_type: str = "yellow") -> bool:
    """Send scan event to backend"""
    try:
        headers = {
            'X-API-Key': device_api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            "student_id": student_id,
            "tag_id": rfid,
            "verified": verified,
            "confidence": similarity,
            "scan_type": scan_type,
            "lat": GPS_LOCATION["lat"],
            "lon": GPS_LOCATION["lon"],
            "photo_base64": photo_base64
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/scan_event",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        return response.status_code == 200
    except Exception as e:
        print(f"{Colors.RED}  Scan event error: {e}{Colors.RESET}")
        return False

# ============================================================
# PHOTO MANAGEMENT
# ============================================================

def get_student_photo(student_id: str) -> Optional[Path]:
    """Get student profile photo"""
    student_dir = PHOTO_BASE_DIR / student_id
    
    for ext in ['.jpg', '.jpeg', '.png']:
        photo_path = student_dir / f"profile{ext}"
        if photo_path.exists():
            return photo_path
    
    return None

def photo_to_base64(photo_path: Path) -> Optional[str]:
    """Convert photo to base64"""
    try:
        with open(photo_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except:
        return None

def save_attendance_photo(student_id: str, photo_path: Path, scan_type: str) -> bool:
    """Save to attendance folder"""
    try:
        attendance_dir = PHOTO_BASE_DIR / student_id / "attendance"
        attendance_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        dest = attendance_dir / f"{today}_{scan_type}.jpg"
        
        import shutil
        shutil.copy2(photo_path, dest)
        return True
    except:
        return False

# ============================================================
# RFID SCANNING LOGIC
# ============================================================

def process_rfid_scan(rfid: str, student_name: str, student_id: str, scan_type: str = "AM"):
    """Process a single RFID scan"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}📡 RFID Scan Detected{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"  RFID: {Colors.YELLOW}{rfid}{Colors.RESET}")
    print(f"  Student: {Colors.CYAN}{student_name}{Colors.RESET}")
    print(f"  ID: {student_id}")
    print(f"  Type: {scan_type}")
    
    # Step 1: Load profile photo
    print(f"\n{Colors.BLUE}[1/6] Loading profile photo...{Colors.RESET}")
    photo_path = get_student_photo(student_id)
    
    if not photo_path:
        print(f"{Colors.RED}  ✗ Photo not found{Colors.RESET}")
        return False
    
    print(f"{Colors.GREEN}  ✓ Photo loaded: {photo_path.name}{Colors.RESET}")
    
    # Step 2: Generate local embedding
    print(f"{Colors.BLUE}[2/6] Generating embedding from photo...{Colors.RESET}")
    local_embedding = generate_embedding(photo_path)
    
    if local_embedding is None:
        print(f"{Colors.RED}  ✗ Embedding generation failed{Colors.RESET}")
        return False
    
    print(f"{Colors.GREEN}  ✓ Embedding generated (shape: {local_embedding.shape}){Colors.RESET}")
    
    # Step 3: Fetch backend embedding via API
    print(f"{Colors.BLUE}[3/6] Fetching backend embedding via API...{Colors.RESET}")
    backend_embedding = get_student_embedding(student_id)
    
    verified = True
    similarity = 1.0
    
    if backend_embedding is not None:
        print(f"{Colors.GREEN}  ✓ Backend embedding fetched{Colors.RESET}")
        
        # Step 4: Compare embeddings
        print(f"{Colors.BLUE}[4/6] Comparing embeddings...{Colors.RESET}")
        similarity = cosine_similarity(local_embedding, backend_embedding)
        verified = similarity >= SIMILARITY_THRESHOLD
        
        print(f"{Colors.GREEN}  ✓ Similarity: {similarity:.4f}{Colors.RESET}")
        if verified:
            print(f"{Colors.GREEN}  ✓ Verification: PASSED (>= {SIMILARITY_THRESHOLD}){Colors.RESET}")
        else:
            print(f"{Colors.RED}  ✗ Verification: FAILED (< {SIMILARITY_THRESHOLD}){Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}  ⚠ Backend embedding not found, using local only{Colors.RESET}")
        print(f"{Colors.YELLOW}  → Assuming verified (first time scan){Colors.RESET}")
    
    # Step 5: Convert photo to base64
    print(f"{Colors.BLUE}[5/6] Converting photo to base64...{Colors.RESET}")
    photo_base64 = photo_to_base64(photo_path)
    
    if not photo_base64:
        print(f"{Colors.RED}  ✗ Base64 conversion failed{Colors.RESET}")
        return False
    
    print(f"{Colors.GREEN}  ✓ Photo converted ({len(photo_base64)} chars){Colors.RESET}")
    
    # Step 6: Send scan event to backend
    print(f"{Colors.BLUE}[6/6] Sending scan event to backend...{Colors.RESET}")
    scan_type_code = "yellow" if scan_type == "AM" else "green"
    success = send_scan_event(student_id, rfid, verified, similarity, photo_base64, scan_type_code)
    
    if success:
        print(f"{Colors.GREEN}  ✓ Scan event sent successfully{Colors.RESET}")
        
        # Save to attendance folder
        save_attendance_photo(student_id, photo_path, scan_type)
        print(f"{Colors.GREEN}  ✓ Photo saved to attendance folder{Colors.RESET}")
        
        # Summary
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        if verified:
            print(f"{Colors.BOLD}{Colors.GREEN}✓ SCAN SUCCESSFUL{Colors.RESET}")
        else:
            print(f"{Colors.BOLD}{Colors.RED}⚠ VERIFICATION FAILED{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"  Student: {student_name}")
        print(f"  Similarity: {similarity:.4f}")
        print(f"  Status: {'✓ VERIFIED' if verified else '✗ NOT VERIFIED'}")
        print(f"  Attendance: {scan_type_code.upper()}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
        
        return True
    else:
        print(f"{Colors.RED}  ✗ Failed to send scan event{Colors.RESET}")
        return False

# ============================================================
# SCANNING THREAD
# ============================================================

def load_student_rfid_mapping() -> Dict[str, Dict]:
    """Load RFID to student mapping"""
    try:
        json_file = Path(__file__).parent / "students_boarding.json"
        if json_file.exists():
            with open(json_file, 'r') as f:
                students = json.load(f)
                return {s['rfid']: s for s in students}
        return {}
    except:
        return {}

def scanning_thread():
    """Continuous scanning thread"""
    global scanning_active
    
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}🔄 Scanning thread started{Colors.RESET}")
    print(f"{Colors.YELLOW}Simulating RFID scans every {SCAN_INTERVAL} seconds...{Colors.RESET}\n")
    
    # Load student mapping
    rfid_map = load_student_rfid_mapping()
    student_list = list(rfid_map.values())
    
    if not student_list:
        print(f"{Colors.RED}✗ No students loaded{Colors.RESET}")
        return
    
    scan_index = 0
    scan_type = "AM"  # Start with AM scans
    
    while scanning_active:
        try:
            # Get next student
            student = student_list[scan_index % len(student_list)]
            
            # Process scan
            process_rfid_scan(
                rfid=student['rfid'],
                student_name=student['name'],
                student_id=student['student_id'],
                scan_type=scan_type
            )
            
            # Move to next student
            scan_index += 1
            
            # After all students scanned once in AM, switch to PM
            if scan_index == len(student_list) and scan_type == "AM":
                print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
                print(f"{Colors.CYAN}🔄 All students scanned for AM boarding{Colors.RESET}")
                print(f"{Colors.CYAN}   Switching to PM boarding...{Colors.RESET}")
                print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
                scan_type = "PM"
                scan_index = 0
            
            # Wait before next scan
            if scanning_active:
                time.sleep(SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"{Colors.RED}Scanning error: {e}{Colors.RESET}")
            time.sleep(1)
    
    print(f"\n{Colors.MAGENTA}🛑 Scanning thread stopped{Colors.RESET}")

# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    global device_api_key, session_cookie, scanning_active
    
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}🚌 Pi Real-Time Scanner - Raspberry Pi Simulator{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    # Step 1: Check DeepFace
    print(f"{Colors.YELLOW}Checking dependencies...{Colors.RESET}")
    if not check_deepface():
        print(f"{Colors.RED}✗ Cannot continue without DeepFace{Colors.RESET}")
        return
    print(f"{Colors.GREEN}✓ All dependencies ready{Colors.RESET}\n")
    
    # Step 2: Admin login
    session_cookie = admin_login()
    if not session_cookie:
        print(f"{Colors.RED}✗ Cannot continue without admin session{Colors.RESET}")
        return
    
    # Step 3: Register device
    device_api_key = register_device(session_cookie)
    if not device_api_key:
        print(f"{Colors.RED}✗ Cannot continue without device API key{Colors.RESET}")
        return
    
    print(f"\n{Colors.GREEN}✓ Device ready for scanning{Colors.RESET}")
    print(f"{Colors.CYAN}  Backend: {BACKEND_URL}{Colors.RESET}")
    print(f"{Colors.CYAN}  Bus ID: {BUS_ID}{Colors.RESET}")
    print(f"{Colors.CYAN}  Device: {DEVICE_NAME}{Colors.RESET}\n")
    
    # Step 4: Start scanning thread
    scanning_active = True
    scanner = threading.Thread(target=scanning_thread, daemon=True)
    scanner.start()
    
    # Keep main thread alive
    try:
        print(f"{Colors.YELLOW}Press Ctrl+C to stop scanning...{Colors.RESET}\n")
        while scanning_active:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.CYAN}🛑 Stopping scanner...{Colors.RESET}")
        scanning_active = False
        scanner.join(timeout=2)
        print(f"{Colors.GREEN}✓ Scanner stopped{Colors.RESET}\n")

if __name__ == "__main__":
    main()
