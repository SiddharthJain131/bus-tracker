#!/usr/bin/env python3
"""
Raspberry Pi Boarding Scanner - Main Controller
================================================

This is the main controller script that orchestrates the boarding process.
Hardware/simulation logic is delegated to interchangeable backend modules.

The script imports either pi_hardware.py or pi_simulated.py based on PI_MODE
environment variable. Both modules expose identical function signatures.
"""

import os
import sys
import json
import base64
import requests
import numpy as np
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
import getpass
from dotenv import load_dotenv

# ============================================================
# CONFIGURATION AND MODULE LOADING
# ============================================================

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "pi_device_config.json"
RFID_MAPPING_FILE = SCRIPT_DIR / "rfid_student_mapping.json"

# Load environment variables
load_dotenv(SCRIPT_DIR / ".env")

# Determine which backend module to use
PI_MODE = os.getenv("PI_MODE", "simulated").lower()
DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

# Import appropriate backend module
if PI_MODE == "hardware":
    try:
        import pi_hardware as pi_backend
        print(f"\n✓ Loaded HARDWARE backend module")
    except ImportError as e:
        print(f"\n✗ Failed to load pi_hardware module: {e}")
        print(f"Falling back to simulated mode")
        import pi_simulated as pi_backend
        PI_MODE = "simulated"
else:
    import pi_simulated as pi_backend
    print(f"\n✓ Loaded SIMULATED backend module")

# Verification failure tracking (per student)
verification_failures = {}

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
    """Load RFID to student mapping from local file with error handling"""
    if RFID_MAPPING_FILE.exists():
        try:
            with open(RFID_MAPPING_FILE, 'r') as f:
                students = json.load(f)
                return {s['rfid']: s for s in students}
        except json.JSONDecodeError as e:
            print(f"{Colors.RED}Error: RFID mapping file is corrupted: {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}Creating backup and starting fresh...{Colors.RESET}")
            backup_path = RFID_MAPPING_FILE.with_suffix('.json.bak')
            if RFID_MAPPING_FILE.exists():
                RFID_MAPPING_FILE.rename(backup_path)
            return {}
        except Exception as e:
            print(f"{Colors.RED}Error loading RFID mapping: {e}{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}Warning: RFID mapping file not found{Colors.RESET}")
    return {}

def save_rfid_mapping(rfid_mapping: Dict[str, Dict]):
    """Save updated RFID mapping to local file atomically"""
    try:
        students_list = list(rfid_mapping.values())
        
        # Use atomic write: write to temp file then rename
        temp_fd, temp_path = tempfile.mkstemp(dir=SCRIPT_DIR, suffix='.json.tmp')
        try:
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(students_list, f, indent=2)
            
            # Atomic rename
            os.replace(temp_path, RFID_MAPPING_FILE)
            print(f"{Colors.GREEN}✓ RFID mapping cache updated{Colors.RESET}")
        except:
            # Clean up temp file if something went wrong
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
            
    except Exception as e:
        print(f"{Colors.RED}Error saving RFID mapping: {e}{Colors.RESET}")

def update_local_embedding_cache(rfid_mapping: Dict[str, Dict], rfid_tag: str, embedding_b64: str):
    """Update the local embedding cache for a specific RFID tag"""
    if rfid_tag in rfid_mapping:
        rfid_mapping[rfid_tag]['embedding'] = embedding_b64
        save_rfid_mapping(rfid_mapping)
        print(f"{Colors.GREEN}✓ Local embedding cache updated for {rfid_tag}{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ RFID tag {rfid_tag} not found in mapping{Colors.RESET}")

# ============================================================
# DEVICE REGISTRATION
# ============================================================

def register_device(backend_url: str, bus_number: str, device_name: str) -> Optional[Dict]:
    """Register this Pi device with the backend"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}DEVICE REGISTRATION{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW}This device needs to be registered with the backend.{Colors.RESET}")
    print(f"{Colors.YELLOW}Please provide admin credentials to register.{Colors.RESET}\n")
    
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
            json={"bus_number": bus_number, "device_name": device_name},
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
# BACKEND API COMMUNICATION
# ============================================================

def api_request(config: Dict, endpoint: str, method: str = "GET", data: Dict = None) -> tuple:
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

def fetch_student_embedding_from_api(config: Dict, student_id: str) -> Optional[str]:
    """Fetch student's stored face embedding from backend API"""
    success, data = api_request(config, f"/api/students/{student_id}/embedding")
    
    if not success:
        print(f"{Colors.RED}   ✗ Failed to fetch embedding from API: {data.get('error')}{Colors.RESET}")
        return None
    
    embedding_b64 = data.get('embedding')
    if not embedding_b64:
        print(f"{Colors.YELLOW}   ⚠ No embedding available in backend{Colors.RESET}")
        return None
    
    return embedding_b64

def decode_embedding(embedding_b64: str) -> Optional[np.ndarray]:
    """Decode base64 embedding string to numpy array"""
    try:
        embedding_bytes = base64.b64decode(embedding_b64)
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
        return embedding
    except Exception as e:
        print(f"{Colors.RED}   ✗ Error decoding embedding: {e}{Colors.RESET}")
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
# BOARDING WORKFLOWS
# ============================================================

def process_boarding_in(config: Dict, rfid_tag: str, student_info: Dict, rfid_mapping: Dict[str, Dict]) -> bool:
    """
    Process a Boarding IN scan using backend module functions.
    All hardware/simulation operations are delegated to pi_backend module.
    """
    global verification_failures
    
    student_id = student_info['student_id']
    
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}BOARDING IN{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}Student ID: {student_id}{Colors.RESET}")
    print(f"{Colors.CYAN}RFID Tag: {rfid_tag}{Colors.RESET}\n")
    
    # Initialize failure tracking
    if student_id not in verification_failures:
        verification_failures[student_id] = 0
    
    # Step 1: Check local embedding cache
    local_embedding_b64 = student_info.get('embedding')
    
    if not local_embedding_b64:
        print(f"{Colors.YELLOW}⚠ No local embedding cached{Colors.RESET}")
        print(f"{Colors.BLUE}→ Fetching embedding from API...{Colors.RESET}")
        
        api_embedding_b64 = fetch_student_embedding_from_api(config, student_id)
        
        if api_embedding_b64:
            print(f"{Colors.GREEN}✓ Embedding fetched from API{Colors.RESET}")
            update_local_embedding_cache(rfid_mapping, rfid_tag, api_embedding_b64)
            local_embedding_b64 = api_embedding_b64
        else:
            print(f"{Colors.YELLOW}⚠ No embedding available, sending unverified scan{Colors.RESET}")
            payload = {
                "student_id": student_id,
                "tag_id": rfid_tag,
                "verified": False,
                "confidence": 0.0,
                "lat": config.get('gps', {}).get('lat', 37.7749),
                "lon": config.get('gps', {}).get('lon', -122.4194)
            }
            pi_backend.send_packet(config, payload)
            return False
    else:
        print(f"{Colors.GREEN}✓ Using cached local embedding{Colors.RESET}")
    
    # Decode embedding
    stored_embedding = decode_embedding(local_embedding_b64)
    if stored_embedding is None:
        print(f"{Colors.RED}✗ Failed to decode embedding{Colors.RESET}")
        return False
    
    # Step 2: Capture photo (via backend module)
    photo_path = pi_backend.capture_student_photo(config, student_id, SCRIPT_DIR)
    if not photo_path:
        print(f"{Colors.YELLOW}⚠ No photo captured, sending unverified scan{Colors.RESET}")
        payload = {
            "student_id": student_id,
            "tag_id": rfid_tag,
            "verified": False,
            "confidence": 0.0,
            "lat": config.get('gps', {}).get('lat', 37.7749),
            "lon": config.get('gps', {}).get('lon', -122.4194)
        }
        pi_backend.send_packet(config, payload)
        return False
    
    # Step 3: Generate embedding (via backend module)
    current_embedding = pi_backend.generate_face_embedding(photo_path)
    if current_embedding is None:
        print(f"{Colors.YELLOW}⚠ Failed to generate embedding{Colors.RESET}")
        return False
    
    # Step 4: Compare embeddings
    print(f"{Colors.BLUE}→ Comparing face embeddings...{Colors.RESET}")
    similarity = cosine_similarity(current_embedding, stored_embedding)
    
    verified = similarity >= 0.6
    confidence = float(similarity)
    
    if verified:
        print(f"{Colors.GREEN}✓ VERIFIED - Similarity: {similarity:.2%}{Colors.RESET}")
        verification_failures[student_id] = 0
    else:
        print(f"{Colors.RED}✗ NOT VERIFIED - Similarity: {similarity:.2%}{Colors.RESET}")
        verification_failures[student_id] += 1
        current_failures = verification_failures[student_id]
        print(f"{Colors.YELLOW}   Consecutive failures: {current_failures}{Colors.RESET}")
        
        # Step 5: Retry logic after 2 failures
        if current_failures >= 2:
            print(f"\n{Colors.YELLOW}⚠ Two consecutive failures detected{Colors.RESET}")
            print(f"{Colors.BLUE}→ Fetching fresh embedding from API...{Colors.RESET}")
            
            fresh_embedding_b64 = fetch_student_embedding_from_api(config, student_id)
            
            if fresh_embedding_b64:
                print(f"{Colors.GREEN}✓ Fresh embedding fetched{Colors.RESET}")
                update_local_embedding_cache(rfid_mapping, rfid_tag, fresh_embedding_b64)
                
                fresh_embedding = decode_embedding(fresh_embedding_b64)
                
                if fresh_embedding is not None:
                    print(f"\n{Colors.CYAN}Retrying verification (up to 3 attempts)...{Colors.RESET}")
                    
                    for retry_num in range(1, 4):
                        print(f"\n{Colors.CYAN}→ Retry attempt {retry_num}/3{Colors.RESET}")
                        
                        retry_photo_path = pi_backend.capture_student_photo(config, student_id, SCRIPT_DIR)
                        if not retry_photo_path:
                            continue
                        
                        retry_embedding = pi_backend.generate_face_embedding(retry_photo_path)
                        if retry_embedding is None:
                            continue
                        
                        print(f"{Colors.BLUE}→ Comparing embeddings...{Colors.RESET}")
                        retry_similarity = cosine_similarity(retry_embedding, fresh_embedding)
                        retry_verified = retry_similarity >= 0.6
                        
                        if retry_verified:
                            print(f"{Colors.GREEN}✓ VERIFIED on retry - Similarity: {retry_similarity:.2%}{Colors.RESET}")
                            verified = True
                            confidence = float(retry_similarity)
                            verification_failures[student_id] = 0
                            break
                        else:
                            print(f"{Colors.RED}✗ Still not verified - Similarity: {retry_similarity:.2%}{Colors.RESET}")
                    
                    if not verified:
                        print(f"\n{Colors.RED}✗ Failed after 3 retries{Colors.RESET}")
                        verification_failures[student_id] = 0
    
    # Step 6: Send scan event (via backend module)
    print(f"\n{Colors.BLUE}→ Sending scan event...{Colors.RESET}")
    payload = {
        "student_id": student_id,
        "tag_id": rfid_tag,
        "verified": verified,
        "confidence": confidence,
        "lat": config.get('gps', {}).get('lat', 37.7749),
        "lon": config.get('gps', {}).get('lon', -122.4194)
    }
    
    success = pi_backend.send_packet(config, payload)
    
    if success:
        print(f"{Colors.GREEN}✓ Scan event sent successfully{Colors.RESET}")
        print(f"{Colors.GREEN}  Status: YELLOW (Boarding IN){Colors.RESET}")
    
    return success

def process_boarding_out(config: Dict, rfid_tag: str, student_info: Dict) -> bool:
    """Process a Boarding OUT scan"""
    student_id = student_info['student_id']
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}BOARDING OUT{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}Student ID: {student_id}{Colors.RESET}")
    print(f"{Colors.CYAN}RFID Tag: {rfid_tag}{Colors.RESET}\n")
    
    print(f"{Colors.BLUE}→ Sending scan event...{Colors.RESET}")
    payload = {
        "student_id": student_id,
        "tag_id": rfid_tag,
        "verified": True,
        "confidence": 1.0,
        "lat": config.get('gps', {}).get('lat', 37.7749),
        "lon": config.get('gps', {}).get('lon', -122.4194)
    }
    
    success = pi_backend.send_packet(config, payload)
    
    if success:
        print(f"{Colors.GREEN}✓ Scan event sent successfully{Colors.RESET}")
        print(f"{Colors.GREEN}  Status: GREEN (Boarding OUT){Colors.RESET}")
    
    return success

# ============================================================
# MAIN SCANNER LOOP
# ============================================================

def main():
    """Main scanner loop"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}RASPBERRY PI BOARDING SCANNER{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}Mode: {PI_MODE.upper()}{Colors.RESET}\n")
    
    # Initialize backend module
    if not pi_backend.initialize():
        print(f"{Colors.RED}Failed to initialize backend module. Exiting.{Colors.RESET}")
        sys.exit(1)
    
    # Check for existing configuration
    config = load_config()
    
    if not config:
        print(f"\n{Colors.YELLOW}No device configuration found. Starting registration...{Colors.RESET}\n")
        
        backend_url = input(f"{Colors.CYAN}Backend URL [{DEFAULT_BACKEND_URL}]: {Colors.RESET}").strip() or DEFAULT_BACKEND_URL
        bus_number = input(f"{Colors.CYAN}Bus Number (e.g., 'BUS-001'): {Colors.RESET}").strip()
        device_name = input(f"{Colors.CYAN}Device Name (e.g., 'Pi-Bus-001'): {Colors.RESET}").strip()
        
        if not bus_number or not device_name:
            print(f"{Colors.RED}Bus Number and Device Name are required!{Colors.RESET}")
            sys.exit(1)
        
        config = register_device(backend_url, bus_number, device_name)
        
        if not config:
            print(f"{Colors.RED}Failed to register device. Exiting.{Colors.RESET}")
            sys.exit(1)
        
        save_config(config)
    else:
        print(f"\n{Colors.GREEN}✓ Device configuration loaded{Colors.RESET}")
        print(f"{Colors.CYAN}  Device: {config['device_name']}{Colors.RESET}")
        print(f"{Colors.CYAN}  Backend: {config['backend_url']}{Colors.RESET}")
    
    # Load RFID mapping
    rfid_mapping = load_rfid_mapping()
    if not rfid_mapping:
        print(f"\n{Colors.YELLOW}⚠ Warning: No RFID mapping file found{Colors.RESET}")
        print(f"{Colors.YELLOW}  Create '{RFID_MAPPING_FILE}' with mappings.{Colors.RESET}\n")
    else:
        print(f"\n{Colors.GREEN}✓ RFID mapping loaded ({len(rfid_mapping)} students){Colors.RESET}")
        cached_count = sum(1 for s in rfid_mapping.values() if s.get('embedding'))
        print(f"{Colors.CYAN}  Cached embeddings: {cached_count}/{len(rfid_mapping)}{Colors.RESET}")
    
    # Main scanning loop
    print(f"\n{Colors.BOLD}{Colors.GREEN}Scanner ready!{Colors.RESET}\n")
    print(f"{Colors.CYAN}Scan modes:{Colors.RESET}")
    print(f"{Colors.CYAN}  1. Boarding IN - Yellow status{Colors.RESET}")
    print(f"{Colors.CYAN}  2. Boarding OUT - Green status{Colors.RESET}\n")
    
    try:
        while True:
            try:
                # Read RFID tag (via backend module)
                rfid_tag = pi_backend.read_rfid()
                
                if not rfid_tag:
                    print(f"\n{Colors.YELLOW}Exiting scanner...{Colors.RESET}")
                    break
                
                # Lookup student
                student_info = rfid_mapping.get(rfid_tag)
                
                if not student_info:
                    print(f"{Colors.RED}✗ Unknown RFID: {rfid_tag}{Colors.RESET}")
                    continue
                
                if 'student_id' not in student_info:
                    print(f"{Colors.RED}✗ Invalid entry: missing student_id{Colors.RESET}")
                    continue
                
                # Determine scan type
                print(f"\n{Colors.CYAN}Scan type:{Colors.RESET}")
                print(f"{Colors.CYAN}  1. Boarding IN{Colors.RESET}")
                print(f"{Colors.CYAN}  2. Boarding OUT{Colors.RESET}")
                scan_type = input(f"{Colors.CYAN}Select [1/2]: {Colors.RESET}").strip()
                
                if scan_type == '1':
                    process_boarding_in(config, rfid_tag, student_info, rfid_mapping)
                elif scan_type == '2':
                    process_boarding_out(config, rfid_tag, student_info)
                else:
                    print(f"{Colors.RED}Invalid scan type{Colors.RESET}")
                
                print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}\n")
                
            except Exception as e:
                print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
                import traceback
                traceback.print_exc()
                continue
                
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Scanner interrupted.{Colors.RESET}")
    finally:
        pi_backend.cleanup()
        print(f"{Colors.CYAN}Exiting...{Colors.RESET}\n")

if __name__ == "__main__":
    main()
