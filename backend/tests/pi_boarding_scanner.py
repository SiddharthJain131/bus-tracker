#!/usr/bin/env python3
"""
Raspberry Pi Boarding Scanner
==============================

This script runs on a Raspberry Pi equipped with an RFID reader and camera.
It handles:
1. Device registration with the backend
2. Boarding IN: RFID scan → fetch student photo → generate embedding → verify → send event
3. Boarding OUT: RFID scan → send event

The script automatically determines all API endpoints, authentication, and data flow
based on the backend's current configuration.
"""

import os
import sys
import json
import base64
import requests
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
import getpass

# ============================================================
# CONFIGURATION FILES
# ============================================================

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "pi_device_config.json"
RFID_MAPPING_FILE = SCRIPT_DIR / "rfid_student_mapping.json"

# Default backend URL (can be overridden in config)
DEFAULT_BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")

# ============================================================
# COLOR CODES FOR TERMINAL OUTPUT
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
# CONFIGURATION MANAGEMENT
# ============================================================

def load_config() -> Optional[Dict]:
    """Load device configuration from local file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"{Colors.RED}Error loading config: {e}{Colors.RESET}")
    return None

def save_config(config: Dict):
    """Save device configuration to local file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"{Colors.GREEN}✓ Configuration saved successfully{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error saving config: {e}{Colors.RESET}")
        raise

def load_rfid_mapping() -> Dict[str, Dict]:
    """Load RFID to student mapping from local file"""
    if RFID_MAPPING_FILE.exists():
        try:
            with open(RFID_MAPPING_FILE, 'r') as f:
                students = json.load(f)
                # Create mapping: rfid -> student_info
                return {s['rfid']: s for s in students}
        except Exception as e:
            print(f"{Colors.RED}Error loading RFID mapping: {e}{Colors.RESET}")
    return {}

# ============================================================
# DEVICE REGISTRATION
# ============================================================

def register_device(backend_url: str, bus_number: str, device_name: str) -> Optional[Dict]:
    """
    Register this Pi device with the backend.
    Requires admin authentication.
    Returns device config including API key.
    """
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}DEVICE REGISTRATION{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW}This device needs to be registered with the backend.{Colors.RESET}")
    print(f"{Colors.YELLOW}Please provide admin credentials to register.{Colors.RESET}\n")
    
    # Get admin credentials
    admin_email = input(f"{Colors.CYAN}Admin Email: {Colors.RESET}")
    admin_password = getpass.getpass(f"{Colors.CYAN}Admin Password: {Colors.RESET}")
    
    # Step 1: Login as admin
    try:
        print(f"\n{Colors.BLUE}→ Logging in as admin...{Colors.RESET}")
        login_response = requests.post(
            f"{backend_url}/api/auth/login",
            json={"email": admin_email, "password": admin_password}
        )
        
        if login_response.status_code != 200:
            print(f"{Colors.RED}✗ Login failed: {login_response.text}{Colors.RESET}")
            return None
        
        # Extract session cookie
        session_cookie = login_response.cookies.get('session_token')
        if not session_cookie:
            print(f"{Colors.RED}✗ No session token received{Colors.RESET}")
            return None
        
        print(f"{Colors.GREEN}✓ Admin authenticated{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.RED}✗ Login error: {e}{Colors.RESET}")
        return None
    
    # Step 2: Register device
    try:
        print(f"{Colors.BLUE}→ Registering device...{Colors.RESET}")
        register_response = requests.post(
            f"{backend_url}/api/device/register",
            json={
                "bus_number": bus_number,
                "device_name": device_name
            },
            cookies={"session_token": session_cookie}
        )
        
        if register_response.status_code != 200:
            print(f"{Colors.RED}✗ Registration failed: {register_response.text}{Colors.RESET}")
            return None
        
        device_data = register_response.json()
        print(f"{Colors.GREEN}✓ Device registered successfully!{Colors.RESET}")
        print(f"{Colors.GREEN}  Device ID: {device_data['device_id']}{Colors.RESET}")
        print(f"{Colors.GREEN}  Bus: {device_data.get('bus_number', bus_number)}{Colors.RESET}")
        
        return {
            "backend_url": backend_url,
            "device_id": device_data['device_id'],
            "device_name": device_name,
            "bus_number": bus_number,
            "api_key": device_data['api_key'],
            "registered_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        print(f"{Colors.RED}✗ Registration error: {e}{Colors.RESET}")
        return None

# ============================================================
# DEEPFACE SETUP & EMBEDDING GENERATION
# ============================================================

def check_deepface_installed() -> bool:
    """Check if DeepFace is installed"""
    try:
        import deepface
        return True
    except ImportError:
        return False

def install_deepface():
    """Install DeepFace and dependencies"""
    print(f"{Colors.YELLOW}Installing DeepFace for face recognition...{Colors.RESET}")
    try:
        import subprocess
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "deepface", "tf-keras", "tensorflow", "--quiet"
        ])
        print(f"{Colors.GREEN}✓ DeepFace installed successfully{Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}✗ Failed to install DeepFace: {e}{Colors.RESET}")
        return False

def generate_embedding(image_path: str) -> Optional[np.ndarray]:
    """Generate face embedding using DeepFace Facenet model"""
    try:
        from deepface import DeepFace
        
        embedding_objs = DeepFace.represent(
            img_path=str(image_path),
            model_name='Facenet',
            enforce_detection=False
        )
        
        if embedding_objs and len(embedding_objs) > 0:
            embedding = embedding_objs[0]['embedding']
            return np.array(embedding)
        else:
            return None
            
    except Exception as e:
        print(f"{Colors.RED}   Error generating embedding: {e}{Colors.RESET}")
        return None

def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Calculate cosine similarity between two embeddings"""
    try:
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)
        
    except Exception as e:
        print(f"{Colors.RED}   Error calculating similarity: {e}{Colors.RESET}")
        return 0.0

# ============================================================
# BACKEND API COMMUNICATION
# ============================================================

def api_request(config: Dict, endpoint: str, method: str = "GET", data: Dict = None) -> Tuple[bool, Optional[Dict]]:
    """Make authenticated API request to backend"""
    url = f"{config['backend_url']}{endpoint}"
    headers = {"X-API-Key": config['api_key']}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            return False, {"error": f"Unsupported method: {method}"}
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {"status_code": response.status_code, "error": response.text}
            
    except Exception as e:
        return False, {"error": str(e)}

def fetch_student_photo(config: Dict, student_id: str) -> Optional[str]:
    """Fetch student photo from backend and save locally"""
    success, data = api_request(config, f"/api/students/{student_id}/photo")
    
    if not success:
        print(f"{Colors.RED}   ✗ Failed to fetch photo: {data.get('error')}{Colors.RESET}")
        return None
    
    photo_url = data.get('photo_url')
    if not photo_url:
        print(f"{Colors.RED}   ✗ No photo available for student{Colors.RESET}")
        return None
    
    # Download photo
    try:
        full_url = f"{config['backend_url']}{photo_url}"
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        
        # Save to local temp directory
        temp_dir = SCRIPT_DIR / "temp_photos"
        temp_dir.mkdir(exist_ok=True)
        
        photo_path = temp_dir / f"{student_id}_profile.jpg"
        with open(photo_path, 'wb') as f:
            f.write(response.content)
        
        return str(photo_path)
        
    except Exception as e:
        print(f"{Colors.RED}   ✗ Error downloading photo: {e}{Colors.RESET}")
        return None

def fetch_student_embedding(config: Dict, student_id: str) -> Optional[np.ndarray]:
    """Fetch student's stored face embedding from backend"""
    success, data = api_request(config, f"/api/students/{student_id}/embedding")
    
    if not success:
        print(f"{Colors.RED}   ✗ Failed to fetch embedding: {data.get('error')}{Colors.RESET}")
        return None
    
    embedding_b64 = data.get('embedding')
    if not embedding_b64:
        return None
    
    try:
        # Decode base64 embedding
        embedding_bytes = base64.b64decode(embedding_b64)
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
        return embedding
    except Exception as e:
        print(f"{Colors.RED}   ✗ Error decoding embedding: {e}{Colors.RESET}")
        return None

def send_scan_event(config: Dict, student_id: str, rfid_tag: str, verified: bool, 
                   confidence: float, photo_url: Optional[str] = None) -> bool:
    """Send scan event to backend"""
    # Use GPS coordinates from config or default
    gps = config.get('gps', {'lat': 37.7749, 'lon': -122.4194})
    
    data = {
        "student_id": student_id,
        "tag_id": rfid_tag,
        "verified": verified,
        "confidence": confidence,
        "lat": gps['lat'],
        "lon": gps['lon']
    }
    
    if photo_url:
        data['photo_url'] = photo_url
    
    success, response = api_request(config, "/api/scan_event", method="POST", data=data)
    
    if success:
        status = response.get('status', 'unknown')
        return True
    else:
        print(f"{Colors.RED}   ✗ Failed to send scan event: {response.get('error')}{Colors.RESET}")
        return False

# ============================================================
# RFID SCANNING (Hardware/Simulation)
# ============================================================

def read_rfid_tag(simulation_mode: bool = True) -> Optional[str]:
    """
    Read RFID tag from hardware or simulation.
    In simulation mode, user inputs the RFID manually.
    In hardware mode, this would interface with the actual RFID reader.
    """
    if simulation_mode:
        rfid = input(f"\n{Colors.CYAN}Enter RFID tag (or 'q' to quit): {Colors.RESET}").strip()
        if rfid.lower() == 'q':
            return None
        return rfid
    else:
        # TODO: Implement actual RFID reader interface
        # Example: Use serial port to read from RC522 RFID module
        pass

# ============================================================
# BOARDING WORKFLOWS
# ============================================================

def process_boarding_in(config: Dict, rfid_tag: str, student_info: Dict) -> bool:
    """
    Process a Boarding IN scan:
    1. Fetch student's stored photo from backend
    2. Generate embedding from the photo
    3. Compare with backend's stored embedding
    4. Send scan event with verification result
    """
    student_id = student_info['student_id']
    student_name = student_info.get('name', 'Unknown')
    
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}BOARDING IN: {student_name}{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}Student ID: {student_id}{Colors.RESET}")
    print(f"{Colors.CYAN}RFID Tag: {rfid_tag}{Colors.RESET}\n")
    
    # Step 1: Fetch student photo
    print(f"{Colors.BLUE}→ Fetching student photo from backend...{Colors.RESET}")
    photo_path = fetch_student_photo(config, student_id)
    
    if not photo_path:
        print(f"{Colors.YELLOW}⚠ No photo available, sending unverified scan{Colors.RESET}")
        send_scan_event(config, student_id, rfid_tag, verified=False, confidence=0.0)
        return False
    
    print(f"{Colors.GREEN}✓ Photo downloaded{Colors.RESET}")
    
    # Step 2: Generate embedding from photo
    print(f"{Colors.BLUE}→ Generating face embedding...{Colors.RESET}")
    current_embedding = generate_embedding(photo_path)
    
    if current_embedding is None:
        print(f"{Colors.YELLOW}⚠ Failed to generate embedding, sending unverified scan{Colors.RESET}")
        send_scan_event(config, student_id, rfid_tag, verified=False, confidence=0.0)
        return False
    
    print(f"{Colors.GREEN}✓ Embedding generated{Colors.RESET}")
    
    # Step 3: Fetch stored embedding from backend
    print(f"{Colors.BLUE}→ Fetching stored embedding from backend...{Colors.RESET}")
    stored_embedding = fetch_student_embedding(config, student_id)
    
    if stored_embedding is None:
        print(f"{Colors.YELLOW}⚠ No stored embedding available{Colors.RESET}")
        # Send event with lower confidence
        send_scan_event(config, student_id, rfid_tag, verified=True, confidence=0.5)
        return True
    
    print(f"{Colors.GREEN}✓ Stored embedding fetched{Colors.RESET}")
    
    # Step 4: Compare embeddings
    print(f"{Colors.BLUE}→ Comparing face embeddings...{Colors.RESET}")
    similarity = cosine_similarity(current_embedding, stored_embedding)
    
    # Determine if verified (threshold = 0.6)
    verified = similarity >= 0.6
    confidence = float(similarity)
    
    if verified:
        print(f"{Colors.GREEN}✓ VERIFIED - Similarity: {similarity:.2%}{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ NOT VERIFIED - Similarity: {similarity:.2%} (threshold: 60%){Colors.RESET}")
    
    # Step 5: Send scan event
    print(f"{Colors.BLUE}→ Sending scan event to backend...{Colors.RESET}")
    success = send_scan_event(config, student_id, rfid_tag, verified, confidence)
    
    if success:
        print(f"{Colors.GREEN}✓ Scan event sent successfully{Colors.RESET}")
        print(f"{Colors.GREEN}  Status: YELLOW (Boarding IN){Colors.RESET}")
    
    return success

def process_boarding_out(config: Dict, rfid_tag: str, student_info: Dict) -> bool:
    """
    Process a Boarding OUT scan:
    1. Send scan event (no photo verification needed)
    2. Backend will automatically mark as GREEN (destination reached)
    """
    student_id = student_info['student_id']
    student_name = student_info.get('name', 'Unknown')
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}BOARDING OUT: {student_name}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}Student ID: {student_id}{Colors.RESET}")
    print(f"{Colors.CYAN}RFID Tag: {rfid_tag}{Colors.RESET}\n")
    
    # Send scan event (second scan, will be marked GREEN by backend)
    print(f"{Colors.BLUE}→ Sending scan event to backend...{Colors.RESET}")
    success = send_scan_event(config, student_id, rfid_tag, verified=True, confidence=1.0)
    
    if success:
        print(f"{Colors.GREEN}✓ Scan event sent successfully{Colors.RESET}")
        print(f"{Colors.GREEN}  Status: GREEN (Boarding OUT - Destination Reached){Colors.RESET}")
    
    return success

# ============================================================
# MAIN SCANNER LOOP
# ============================================================

def main():
    """Main scanner loop"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}RASPBERRY PI BOARDING SCANNER{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    # Check for existing configuration
    config = load_config()
    
    if not config:
        print(f"{Colors.YELLOW}No device configuration found. Starting registration...{Colors.RESET}\n")
        
        # Prompt for registration details
        backend_url = input(f"{Colors.CYAN}Backend URL [{DEFAULT_BACKEND_URL}]: {Colors.RESET}").strip() or DEFAULT_BACKEND_URL
        bus_id = input(f"{Colors.CYAN}Bus ID: {Colors.RESET}").strip()
        device_name = input(f"{Colors.CYAN}Device Name (e.g., 'Pi-Bus-001'): {Colors.RESET}").strip()
        
        if not bus_id or not device_name:
            print(f"{Colors.RED}Bus ID and Device Name are required!{Colors.RESET}")
            sys.exit(1)
        
        # Register device
        config = register_device(backend_url, bus_id, device_name)
        
        if not config:
            print(f"{Colors.RED}Failed to register device. Exiting.{Colors.RESET}")
            sys.exit(1)
        
        # Save configuration
        save_config(config)
    
    else:
        print(f"{Colors.GREEN}✓ Device configuration loaded{Colors.RESET}")
        print(f"{Colors.CYAN}  Device: {config['device_name']}{Colors.RESET}")
        print(f"{Colors.CYAN}  Backend: {config['backend_url']}{Colors.RESET}")
    
    # Check DeepFace installation
    if not check_deepface_installed():
        print(f"\n{Colors.YELLOW}DeepFace not installed.{Colors.RESET}")
        if not install_deepface():
            print(f"{Colors.RED}Cannot proceed without DeepFace. Exiting.{Colors.RESET}")
            sys.exit(1)
    
    # Load RFID mapping
    rfid_mapping = load_rfid_mapping()
    if not rfid_mapping:
        print(f"\n{Colors.YELLOW}⚠ Warning: No RFID mapping file found.{Colors.RESET}")
        print(f"{Colors.YELLOW}  Create '{RFID_MAPPING_FILE}' with student RFID mappings.{Colors.RESET}")
        print(f"{Colors.YELLOW}  Example format:{Colors.RESET}")
        print(f"{Colors.YELLOW}  [{Colors.RESET}")
        print(f"{Colors.YELLOW}    {{'rfid': 'RFID-1001', 'student_id': 'abc-123', 'name': 'John Doe'}},{Colors.RESET}")
        print(f"{Colors.YELLOW}    {{'rfid': 'RFID-1002', 'student_id': 'def-456', 'name': 'Jane Smith'}}{Colors.RESET}")
        print(f"{Colors.YELLOW}  ]{Colors.RESET}\n")
    else:
        print(f"{Colors.GREEN}✓ RFID mapping loaded ({len(rfid_mapping)} students){Colors.RESET}")
    
    # Main scanning loop
    print(f"\n{Colors.BOLD}{Colors.GREEN}Scanner ready! Waiting for RFID scans...{Colors.RESET}\n")
    print(f"{Colors.CYAN}Scan modes:{Colors.RESET}")
    print(f"{Colors.CYAN}  1. Boarding IN (first scan) - Yellow status{Colors.RESET}")
    print(f"{Colors.CYAN}  2. Boarding OUT (second scan) - Green status{Colors.RESET}\n")
    
    while True:
        try:
            # Read RFID tag (simulation mode for testing)
            rfid_tag = read_rfid_tag(simulation_mode=True)
            
            if not rfid_tag:
                print(f"\n{Colors.YELLOW}Exiting scanner...{Colors.RESET}")
                break
            
            # Lookup student from RFID mapping
            student_info = rfid_mapping.get(rfid_tag)
            
            if not student_info:
                print(f"{Colors.RED}✗ Unknown RFID tag: {rfid_tag}{Colors.RESET}")
                print(f"{Colors.RED}  This tag is not in the mapping file.{Colors.RESET}")
                continue
            
            # Determine scan type
            print(f"\n{Colors.CYAN}Scan type:{Colors.RESET}")
            print(f"{Colors.CYAN}  1. Boarding IN (pickup/school entry){Colors.RESET}")
            print(f"{Colors.CYAN}  2. Boarding OUT (school exit/home){Colors.RESET}")
            scan_type = input(f"{Colors.CYAN}Select scan type [1/2]: {Colors.RESET}").strip()
            
            if scan_type == '1':
                process_boarding_in(config, rfid_tag, student_info)
            elif scan_type == '2':
                process_boarding_out(config, rfid_tag, student_info)
            else:
                print(f"{Colors.RED}Invalid scan type{Colors.RESET}")
            
            print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}\n")
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Scanner interrupted. Exiting...{Colors.RESET}")
            break
        except Exception as e:
            print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
            continue

if __name__ == "__main__":
    main()
