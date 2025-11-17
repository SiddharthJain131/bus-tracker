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
from typing import Dict, Optional, Tuple
import getpass
from dotenv import load_dotenv

# ============================================================
# CONFIGURATION AND MODULE LOADING
# ============================================================

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "pi_device_config.json"
RFID_MAPPING_FILE = SCRIPT_DIR / "rfid_student_mapping.json"
ENV_CONFIG_FILE = SCRIPT_DIR / ".env"

# Load environment variables
load_dotenv(SCRIPT_DIR / ".env")

# Determine which backend module to use
PI_MODE = os.getenv("PI_MODE", "simulated").lower()
DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

# Import appropriate backend module
if PI_MODE == "hardware":
    try:
        import pi_hardware as pi_backend
        print(f"\n[OK] Loaded HARDWARE backend module")
    except ImportError as e:
        print(f"\n[ERROR] Failed to load pi_hardware module: {e}")
        print(f"Falling back to simulated mode")
        import pi_simulated as pi_backend
        PI_MODE = "simulated"
else:
    import pi_simulated as pi_backend
    print(f"\n[OK] Loaded SIMULATED backend module")

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
    """Load device configuration from environment (.env). Returns None when missing."""
    # dotenv already loaded at top of the file
    backend_url = os.getenv("BACKEND_URL")
    device_id = os.getenv("DEVICE_ID")
    device_name = os.getenv("DEVICE_NAME")
    bus_number = os.getenv("BUS_NUMBER")
    api_key = os.getenv("API_KEY")
    registered_at = os.getenv("REGISTERED_AT")

    if device_id and api_key and backend_url:
        return {
            "backend_url": backend_url,
            "device_id": device_id,
            "device_name": device_name or "",
            "bus_number": bus_number or "",
            "api_key": api_key,
            "registered_at": registered_at or ""
        }

    return None

def save_config(config: Dict):
    """Save device configuration into .env (overwrites or creates)."""
    try:
        lines = []
        # preserve existing keys from other .env entries if present
        existing = {}
        if ENV_CONFIG_FILE.exists():
            try:
                with open(ENV_CONFIG_FILE, "r", encoding="utf-8") as f:
                    for ln in f:
                        ln = ln.rstrip("\n")
                        if "=" in ln and not ln.lstrip().startswith("#"):
                            k, v = ln.split("=", 1)
                            existing[k.strip()] = v
            except Exception:
                existing = {}

        # update values we care about
        existing["BACKEND_URL"] = config.get("backend_url", existing.get("BACKEND_URL", ""))
        existing["DEVICE_ID"] = config.get("device_id", existing.get("DEVICE_ID", ""))
        existing["DEVICE_NAME"] = config.get("device_name", existing.get("DEVICE_NAME", ""))
        existing["BUS_NUMBER"] = config.get("bus_number", existing.get("BUS_NUMBER", ""))
        existing["API_KEY"] = config.get("api_key", existing.get("API_KEY", ""))
        existing["REGISTERED_AT"] = config.get("registered_at", existing.get("REGISTERED_AT", ""))

        # write back .env (simple, deterministic ordering)
        with open(ENV_CONFIG_FILE, "w", encoding="utf-8") as f:
            for k, v in existing.items():
                f.write(f"{k}={v}\n")

        print(f"{Colors.GREEN}[OK] Configuration saved to .env{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error saving config to .env: {e}{Colors.RESET}")
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
            print(f"{Colors.GREEN}[OK] RFID mapping cache updated{Colors.RESET}")
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
        print(f"{Colors.GREEN}[OK] Local embedding cache updated for {rfid_tag}{Colors.RESET}")
    else:
        print(f"{Colors.RED}[ERROR] RFID tag {rfid_tag} not found in mapping{Colors.RESET}")

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
        print(f"\n{Colors.BLUE}-> Logging in as admin...{Colors.RESET}")
        login_response = requests.post(
            f"{backend_url}/api/auth/login",
            json={"email": admin_email, "password": admin_password}
        )
        
        if login_response.status_code != 200:
            print(f"{Colors.RED}[ERROR] Login failed: {login_response.text}{Colors.RESET}")
            return None
        
        session_cookie = login_response.cookies.get('session_token')
        if not session_cookie:
            print(f"{Colors.RED}[ERROR] No session token received{Colors.RESET}")
            return None
        
        print(f"{Colors.GREEN}[OK] Admin authenticated{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Login error: {e}{Colors.RESET}")
        return None
    
    # Step 2: Register device
    try:
        print(f"{Colors.BLUE}-> Registering device...{Colors.RESET}")
        register_response = requests.post(
            f"{backend_url}/api/device/register",
            json={"bus_number": bus_number, "device_name": device_name},
            cookies={"session_token": session_cookie}
        )
        
        if register_response.status_code != 200:
            print(f"{Colors.RED}[ERROR] Registration failed: {register_response.text}{Colors.RESET}")
            return None
        
        device_data = register_response.json()
        print(f"{Colors.GREEN}[OK] Device registered successfully!{Colors.RESET}")
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
        print(f"{Colors.RED}[ERROR] Registration error: {e}{Colors.RESET}")
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

def fetch_student_embedding_from_api(config: Dict, rfid_tag: str, rfid_mapping: Dict[str, Dict], quiet: bool = False) -> Optional[str]:
    """
    Fetch student's embedding from backend using RFID (tag_id) only.
    - Calls /api/students/embedding-by-rfid?rfid=<rfid>
    - If backend returns student_id and embedding, save/update local rfid_mapping and persist.
    - Returns embedding base64 string or None.
     """
    try:
        url_endpoint = f"/api/students/embedding-by-rfid?rfid={rfid_tag}"
        success, data = api_request(config, url_endpoint, method="GET")
        if not success:
            if not quiet:
                print(f"{Colors.RED}   [ERROR] Failed to fetch embedding by RFID: {data.get('error') or data}{Colors.RESET}")
            return None
 
        student_id = data.get("student_id")
        embedding_b64 = data.get("embedding") or ""
 
        if not student_id:
            if not quiet:
                print(f"{Colors.YELLOW}   [WARN] Backend returned no student_id for RFID {rfid_tag}{Colors.RESET}")
            return None
 
        # Update or create local mapping entry and save embedding if present
        if rfid_tag in rfid_mapping:
            # ensure student_id consistent
            if rfid_mapping[rfid_tag].get("student_id") != student_id:
                rfid_mapping[rfid_tag]["student_id"] = student_id
        else:
            # create minimal mapping entry
            rfid_mapping[rfid_tag] = {
                "rfid": rfid_tag,
                "student_id": student_id,
                "name": "",        # unknown here
                "embedding": ""
            }
 
        if embedding_b64:
            rfid_mapping[rfid_tag]["embedding"] = embedding_b64
            save_rfid_mapping(rfid_mapping)
            if not quiet:
                print(f"{Colors.GREEN}   [OK] Embedding saved for RFID {rfid_tag} (student {student_id}){Colors.RESET}")
            return embedding_b64
 
         # embedding missing on server
        if not quiet:
            print(f"{Colors.YELLOW}   [WARN] No embedding available for student {student_id}{Colors.RESET}")
        # persist mapping change (student_id) even if embedding empty
        save_rfid_mapping(rfid_mapping)
        return None
 
    except Exception as e:
        if not quiet:
            print(f"{Colors.RED}   [ERROR] Exception fetching embedding by RFID: {e}{Colors.RESET}")
        return None

def decode_embedding(embedding_b64: str) -> Optional[np.ndarray]:
    """Decode base64 embedding string to numpy array"""
    try:
        embedding_bytes = base64.b64decode(embedding_b64)
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
        return embedding
    except Exception as e:
        print(f"{Colors.RED}   [ERROR] Error decoding embedding: {e}{Colors.RESET}")
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

def verify_student_identity(config: Dict, rfid_tag: str, student_info: Dict, rfid_mapping: Dict[str, Dict]) -> Tuple[bool, float, Optional[str]]:
    """
    Performs Steps 1-5: 
    - Fetch/load embedding
    - Capture photo
    - Generate embedding
    - Compare
    - Retry if needed

    Returns: (verified, confidence, photo_path)
    """
    student_id = student_info['student_id']
    local_embedding_b64 = student_info.get('embedding')
    
    # Step 1: Check local cache
    if not local_embedding_b64:
        print(f"{Colors.YELLOW}[WARN] No local embedding cached{Colors.RESET}")
        print(f"{Colors.BLUE}-> Fetching embedding from API...{Colors.RESET}")
        
        api_embedding_b64 = fetch_student_embedding_from_api(config, rfid_tag, rfid_mapping)
        if not api_embedding_b64:
            print(f"{Colors.RED}[ERROR] No embedding available{Colors.RESET}")
            return False, 0.0, None
        
        print(f"{Colors.GREEN}[OK] Embedding fetched{Colors.RESET}")
        update_local_embedding_cache(rfid_mapping, rfid_tag, api_embedding_b64)
        local_embedding_b64 = api_embedding_b64
    else:
        print(f"{Colors.GREEN}[OK] Using cached embedding{Colors.RESET}")

    # Decode stored embedding
    stored_embedding = decode_embedding(local_embedding_b64)
    if stored_embedding is None:
        print(f"{Colors.RED}[ERROR] Failed to decode embedding{Colors.RESET}")
        return False, 0.0, None
    
    # Step 2: Capture photo
    photo_path = pi_backend.capture_student_photo(config, student_id, SCRIPT_DIR)
    if not photo_path:
        print(f"{Colors.RED}[ERROR] No photo captured{Colors.RESET}")
        return False, 0.0, None

    # Step 3: Generate embedding
    current_embedding = pi_backend.generate_face_embedding(photo_path)
    if current_embedding is None:
        print(f"{Colors.YELLOW}[WARN] Failed to generate embedding{Colors.RESET}")
        return False, 0.0, photo_path

    # Step 4: Compare embeddings
    print(f"{Colors.BLUE}-> Comparing embeddings...{Colors.RESET}")
    confidence = cosine_similarity(current_embedding, stored_embedding)
    verified = confidence >= 0.7

    if verified:
        print(f"{Colors.GREEN}[OK] VERIFIED - Similarity: {confidence:.2%}{Colors.RESET}")
        return True, confidence, photo_path

    print(f"{Colors.RED}[ERROR] NOT VERIFIED - Similarity: {confidence:.2%}{Colors.RESET}")

    # Step 5: Retry logic
    print(f"\n{Colors.YELLOW}[WARN] Fetching fresh embedding for retry...{Colors.RESET}")
    fresh_b64 = fetch_student_embedding_from_api(config, rfid_tag, rfid_mapping)
    if not fresh_b64:
        return False, confidence, photo_path

    update_local_embedding_cache(rfid_mapping, rfid_tag, fresh_b64)
    fresh_embedding = decode_embedding(fresh_b64)
    if fresh_embedding is None:
        return False, confidence, photo_path

    print(f"{Colors.CYAN}Retrying verification (up to 3 attempts)...{Colors.RESET}")
    for attempt in range(1, 4):
        print(f"{Colors.CYAN}-> Retry attempt {attempt}/3{Colors.RESET}")

        retry_photo = pi_backend.capture_student_photo(config, student_id, SCRIPT_DIR)
        if not retry_photo:
            continue

        retry_emb = pi_backend.generate_face_embedding(retry_photo)
        if retry_emb is None:
            continue

        retry_similarity = cosine_similarity(retry_emb, fresh_embedding)
        if retry_similarity >= 0.6:
            print(f"{Colors.GREEN}[OK] VERIFIED on retry - Similarity: {retry_similarity:.2%}{Colors.RESET}")
            return True, float(retry_similarity), retry_photo

        print(f"{Colors.RED}[ERROR] Still not verified - Similarity: {retry_similarity:.2%}{Colors.RESET}")

    print(f"{Colors.RED}[ERROR] Failed after 3 retries{Colors.RESET}")
    return False, confidence, photo_path

def process_boarding(config: Dict, rfid_tag: str, student_info: Dict, rfid_mapping: Dict[str, Dict]) -> bool:
    """
    Handles BOTH Boarding IN and Boarding OUT.
    - IN requires identity verification (photo + embeddings)
    - OUT does NOT require verification
    """

    student_id = student_info['student_id']
    present = student_info.get('present', 0)  # 0 = IN, 1 = OUT

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}BOARDING {'IN' if present == 0 else 'OUT'}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}Student ID: {student_id}{Colors.RESET}")
    print(f"{Colors.CYAN}RFID Tag: {rfid_tag}{Colors.RESET}\n")

    # ----------------------------
    # BOARDING IN (present == 0)
    # ----------------------------
    if present == 0:
        verified, confidence, photo_path = verify_student_identity(
            config, rfid_tag, student_info, rfid_mapping
        )

        if not verified:
            print(f"{Colors.RED}[ERROR] Boarding IN failed{Colors.RESET}")

    # ----------------------------
    # BOARDING OUT (present == 1)
    # ----------------------------
    else:
        verified = True
        confidence = 1.0
        photo_path = None

    # ----------------------------
    # Send scan event
    # ----------------------------
    print(f"\n{Colors.BLUE}-> Sending scan event...{Colors.RESET}")
    present ^= verified  # Toggle present status if photo captured
    payload = {
        "student_id": student_id,
        "tag_id": rfid_tag,
        "verified": verified,
        "confidence": confidence,
        "lat": config.get('gps', {}).get('lat', 37.7749),
        "lon": config.get('gps', {}).get('lon', -122.4194),
        "photo": base64.b64encode(open(photo_path, "rb").read()).decode("utf-8")
                 if photo_path and os.path.exists(photo_path) else None,
        "present": present
    }

    student_info['present'] = present
    save_rfid_mapping(rfid_mapping)
    sent = pi_backend.send_packet(config, payload)
    status = 'RED' if not verified else ('YELLOW' if present == 1 else 'GREEN')
    if sent:
        print(f"{Colors.BLUE}[OK] Scan event sent successfully{Colors.RESET}")
        print(f"{Colors.CYAN}[INFO] Status: {getattr(Colors, status, Colors.RESET)}{status}{Colors.RESET}")

        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)

    return sent


def send_bus_location(config: Dict, bus_number: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None, timestamp: Optional[str] = None):
    """
    Send current bus location to backend /api/bus-locations/update.
    - Uses config.bus_number if bus_number not provided.
    - Attempts to use provided lat/lon, falls back to config['gps'] or pi_backend.get_gps() if available.
    """
    try:
        bn = bus_number or config.get("bus_number") or config.get("bus") or ""
        if not bn:
            return False

        # resolve lat/lon
        if lat is None or lon is None:
            # prefer config.gps then backend helper
            g = config.get("gps") or {}
            lat = lat or g.get("lat")
            lon = lon or g.get("lon")
            if (lat is None or lon is None) and hasattr(pi_backend, "get_gps"):
                try:
                    g2 = pi_backend.get_gps()
                    lat = lat or g2.get("lat")
                    lon = lon or g2.get("lon")
                except Exception:
                    pass

        if lat is None or lon is None:
            return False

        payload = {
            "bus_number": bn,
            "lat": float(lat),
            "lon": float(lon),
            "timestamp": timestamp
        }

        # use existing api_request helper (POST)
        success, data = api_request(config, "/api/bus-locations/update", method="POST", json=payload)
        if success:
            print(f"{Colors.GREEN}   [OK] Bus location reported: {bn} @ {lat},{lon}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}   [ERROR] Failed to report bus location: {data}{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.RED}   [ERROR] Exception reporting bus location: {e}{Colors.RESET}")
        return False

# ...existing code...

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
        print(f"\n{Colors.GREEN}[OK] Device configuration loaded{Colors.RESET}")
        print(f"{Colors.CYAN}  Device: {config['device_name']}{Colors.RESET}")
        print(f"{Colors.CYAN}  Backend: {config['backend_url']}{Colors.RESET}")
    
    # Load RFID mapping
    rfid_mapping = load_rfid_mapping()
    if not rfid_mapping:
        print(f"\n{Colors.YELLOW}[WARN] Warning: No RFID mapping file found{Colors.RESET}")
        print(f"{Colors.YELLOW}  Create '{RFID_MAPPING_FILE}' with mappings.{Colors.RESET}\n")
    else:
        print(f"\n{Colors.GREEN}[OK] RFID mapping loaded ({len(rfid_mapping)} students){Colors.RESET}")
        cached_count = sum(1 for s in rfid_mapping.values() if s.get('embedding'))
        print(f"{Colors.CYAN}  Cached embeddings: {cached_count}/{len(rfid_mapping)}{Colors.RESET}")
    
    # Main scanning loop
    print(f"\n{Colors.BOLD}{Colors.GREEN}Scanner ready!{Colors.RESET}\n")
    
    try:
        while True:
            try:
                # Read RFID tag (via backend module)
                rfid_tag = pi_backend.read_rfid()
                
                if not rfid_tag:
                    print(f"\n{Colors.YELLOW}Exiting scanner...{Colors.RESET}")
                    break

                # Lookup student in local mapping
                student_info = rfid_mapping.get(rfid_tag)

                # If mapping missing or missing student_id, try to fetch from backend by RFID
                if not student_info or 'student_id' not in student_info:
                    print(f"{Colors.BLUE}-> Querying backend for RFID {rfid_tag}...{Colors.RESET}")
                    fetch_student_embedding_from_api(config, rfid_tag, rfid_mapping)
                    # reload mapping entry (function saves mapping when possible)
                    student_info = rfid_mapping.get(rfid_tag)

                if not student_info:
                    print(f"{Colors.RED}[ERROR] Unknown RFID after backend lookup: {rfid_tag}{Colors.RESET}")
                    continue

                # Ensure we have student_id
                if 'student_id' not in student_info or not student_info['student_id']:
                    print(f"{Colors.RED}[ERROR] Invalid entry for RFID {rfid_tag}: missing student_id{Colors.RESET}")
                    continue

                process_boarding(config, rfid_tag, student_info, rfid_mapping)
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
