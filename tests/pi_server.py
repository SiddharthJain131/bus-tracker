#!/usr/bin/env python3
"""
Raspberry Pi Boarding Scanner - Main Controller - REFACTORED
============================================================

This is the main controller script that orchestrates the boarding process.
Hardware/simulation logic is delegated to interchangeable backend modules.

IMPROVEMENTS:
- Fixed configuration key inconsistencies (bus_number vs bus)
- Added proper timeout handling for all operations
- Improved error recovery and retry logic
- Added proper resource cleanup
- Fixed threading safety issues
- Improved logging and error messages
- Added exponential backoff for API retries
- Better state management
"""

import os
import sys
import json
import base64
import tempfile
import threading
import time
import signal
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple
import getpass

import requests
import numpy as np
from dotenv import load_dotenv

# ============================================================
# CONFIGURATION AND MODULE LOADING
# ============================================================

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "pi_device_config.json"
RFID_MAPPING_FILE = SCRIPT_DIR / "rfid_student_mapping.json"
ENV_CONFIG_FILE = SCRIPT_DIR / ".env"

# Load environment variables
load_dotenv(ENV_CONFIG_FILE)

# Determine which backend module to use
PI_MODE = os.getenv("PI_MODE", "simulated").lower()
DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

# Global shutdown flag
shutdown_flag = threading.Event()

# Import appropriate backend module
if PI_MODE == "hardware":
    try:
        import pi_hardware_auto as pi_backend
        print(f"\n[OK] Loaded HARDWARE backend module")
    except ImportError as e:
        print(f"\n[ERROR] Failed to load pi_hardware_auto: {e}")
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
# SIGNAL HANDLING
# ============================================================

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n{Colors.YELLOW}Received shutdown signal, cleaning up...{Colors.RESET}")
    shutdown_flag.set()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ============================================================
# CONFIGURATION MANAGEMENT
# ============================================================

def load_config() -> Optional[Dict]:
    """Load device configuration from environment (.env). Returns None when missing."""
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
            "bus_number": bus_number or "",  # Consistent key name
            "api_key": api_key,
            "registered_at": registered_at or ""
        }

    return None

def save_config(config: Dict) -> None:
    """Save device configuration into .env (overwrites or creates)."""
    try:
        # Preserve existing keys from .env
        existing = {}
        if ENV_CONFIG_FILE.exists():
            try:
                with open(ENV_CONFIG_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            existing[key.strip()] = value.strip()
            except Exception as e:
                print(f"{Colors.YELLOW}[WARN] Error reading existing .env: {e}{Colors.RESET}")
                existing = {}

        # Update values
        existing["BACKEND_URL"] = config.get("backend_url", existing.get("BACKEND_URL", ""))
        existing["DEVICE_ID"] = config.get("device_id", existing.get("DEVICE_ID", ""))
        existing["DEVICE_NAME"] = config.get("device_name", existing.get("DEVICE_NAME", ""))
        existing["BUS_NUMBER"] = config.get("bus_number", existing.get("BUS_NUMBER", ""))
        existing["API_KEY"] = config.get("api_key", existing.get("API_KEY", ""))
        existing["REGISTERED_AT"] = config.get("registered_at", existing.get("REGISTERED_AT", ""))

        # Preserve PI_MODE if it exists
        if "PI_MODE" not in existing:
            existing["PI_MODE"] = os.getenv("PI_MODE", "simulated")

        # Atomic write
        temp_fd, temp_path = tempfile.mkstemp(dir=SCRIPT_DIR, suffix='.env.tmp', text=True)
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                for key, value in existing.items():
                    f.write(f"{key}={value}\n")

            os.replace(temp_path, ENV_CONFIG_FILE)
            print(f"{Colors.GREEN}[OK] Configuration saved to .env{Colors.RESET}")

        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    except Exception as e:
        print(f"{Colors.RED}[ERROR] Failed to save config: {e}{Colors.RESET}")
        raise

def load_rfid_mapping() -> Dict[str, Dict]:
    """Load RFID to student mapping from local file with error handling"""
    if not RFID_MAPPING_FILE.exists():
        print(f"{Colors.YELLOW}[WARN] RFID mapping file not found{Colors.RESET}")
        return {}

    try:
        with open(RFID_MAPPING_FILE, 'r', encoding='utf-8') as f:
            students = json.load(f)
            return {s['rfid']: s for s in students}

    except json.JSONDecodeError as e:
        print(f"{Colors.RED}[ERROR] RFID mapping file is corrupted: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}[INFO] Creating backup and starting fresh...{Colors.RESET}")

        backup_path = RFID_MAPPING_FILE.with_suffix('.json.bak')
        try:
            RFID_MAPPING_FILE.rename(backup_path)
            print(f"{Colors.GREEN}[OK] Backup created: {backup_path}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}[WARN] Could not create backup: {e}{Colors.RESET}")

        return {}

    except Exception as e:
        print(f"{Colors.RED}[ERROR] Failed to load RFID mapping: {e}{Colors.RESET}")
        return {}

def save_rfid_mapping(rfid_mapping: Dict[str, Dict]) -> None:
    """Save updated RFID mapping to local file atomically"""
    try:
        students_list = list(rfid_mapping.values())

        # Atomic write
        temp_fd, temp_path = tempfile.mkstemp(dir=SCRIPT_DIR, suffix='.json.tmp', text=True)
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(students_list, f, indent=2, ensure_ascii=False)

            os.replace(temp_path, RFID_MAPPING_FILE)
            print(f"{Colors.GREEN}[OK] RFID mapping cache updated{Colors.RESET}")

        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    except Exception as e:
        print(f"{Colors.RED}[ERROR] Failed to save RFID mapping: {e}{Colors.RESET}")

def update_local_embedding_cache(rfid_mapping: Dict[str, Dict], rfid_tag: str, embedding_b64: str) -> None:
    """Update the local embedding cache for a specific RFID tag"""
    if rfid_tag not in rfid_mapping:
        print(f"{Colors.YELLOW}[WARN] RFID tag {rfid_tag} not in local mapping{Colors.RESET}")
        return

    rfid_mapping[rfid_tag]['embedding'] = embedding_b64
    save_rfid_mapping(rfid_mapping)
    print(f"{Colors.GREEN}[OK] Local embedding cache updated for {rfid_tag}{Colors.RESET}")

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

    try:
        admin_email = input(f"{Colors.CYAN}Admin Email: {Colors.RESET}").strip()
        admin_password = getpass.getpass(f"{Colors.CYAN}Admin Password: {Colors.RESET}")

        if not admin_email or not admin_password:
            print(f"{Colors.RED}[ERROR] Email and password are required{Colors.RESET}")
            return None

    except (KeyboardInterrupt, EOFError):
        print(f"\n{Colors.YELLOW}[WARN] Registration cancelled{Colors.RESET}")
        return None

    # Step 1: Login as admin
    try:
        print(f"\n{Colors.BLUE}-> Logging in as admin...{Colors.RESET}")

        login_response = requests.post(
            f"{backend_url}/api/auth/login",
            json={"email": admin_email, "password": admin_password},
            timeout=10
        )

        if login_response.status_code != 200:
            print(f"{Colors.RED}[ERROR] Login failed: {login_response.text}{Colors.RESET}")
            return None

        session_cookie = login_response.cookies.get('session_token')
        if not session_cookie:
            print(f"{Colors.RED}[ERROR] No session token received{Colors.RESET}")
            return None

        print(f"{Colors.GREEN}[OK] Admin authenticated{Colors.RESET}")

    except requests.exceptions.Timeout:
        print(f"{Colors.RED}[ERROR] Login request timed out{Colors.RESET}")
        return None

    except Exception as e:
        print(f"{Colors.RED}[ERROR] Login error: {e}{Colors.RESET}")
        return None

    # Step 2: Register device
    try:
        print(f"{Colors.BLUE}-> Registering device...{Colors.RESET}")

        register_response = requests.post(
            f"{backend_url}/api/device/register",
            json={"bus_number": bus_number, "device_name": device_name},
            cookies={"session_token": session_cookie},
            timeout=10
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

    except requests.exceptions.Timeout:
        print(f"{Colors.RED}[ERROR] Registration request timed out{Colors.RESET}")
        return None

    except Exception as e:
        print(f"{Colors.RED}[ERROR] Registration error: {e}{Colors.RESET}")
        return None

# ============================================================
# BACKEND API COMMUNICATION
# ============================================================

def api_request(config: Dict, endpoint: str, method: str = "GET", data: Dict = None, retries: int = 3) -> Tuple[bool, Dict]:
    """Make authenticated API request to backend with retry logic"""
    url = f"{config['backend_url']}{endpoint}"
    headers = {"X-API-Key": config['api_key']}

    for attempt in range(retries):
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
                error_msg = {"status_code": response.status_code, "error": response.text}

                if attempt < retries - 1:
                    print(f"{Colors.YELLOW}[WARN] API request failed (attempt {attempt + 1}/{retries}): {error_msg}{Colors.RESET}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue

                return False, error_msg

        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                print(f"{Colors.YELLOW}[WARN] Request timed out (attempt {attempt + 1}/{retries}){Colors.RESET}")
                time.sleep(2 ** attempt)
                continue
            return False, {"error": "Request timed out"}

        except Exception as e:
            if attempt < retries - 1:
                print(f"{Colors.YELLOW}[WARN] Request failed (attempt {attempt + 1}/{retries}): {e}{Colors.RESET}")
                time.sleep(2 ** attempt)
                continue
            return False, {"error": str(e)}

    return False, {"error": "Max retries exceeded"}

def fetch_student_embedding_from_api(config: Dict, rfid_tag: str, rfid_mapping: Dict[str, Dict], quiet: bool = False) -> Optional[str]:
    """
    Fetch student's embedding from backend using RFID (tag_id) only.
    Returns embedding base64 string or None.
    """
    try:
        url_endpoint = f"/api/students/embedding-by-rfid?rfid={rfid_tag}"
        success, data = api_request(config, url_endpoint, method="GET")

        if not success:
            if not quiet:
                print(f"{Colors.RED}  [ERROR] Failed to fetch embedding by RFID: {data.get('error', data)}{Colors.RESET}")
            return None

        student_id = data.get("student_id")
        embedding_b64 = data.get("embedding") or ""

        if not student_id:
            if not quiet:
                print(f"{Colors.YELLOW}  [WARN] Backend returned no student_id for RFID {rfid_tag}{Colors.RESET}")
            return None

        # Update or create local mapping entry
        if rfid_tag in rfid_mapping:
            if rfid_mapping[rfid_tag].get("student_id") != student_id:
                rfid_mapping[rfid_tag]["student_id"] = student_id
        else:
            rfid_mapping[rfid_tag] = {
                "rfid": rfid_tag,
                "student_id": student_id,
                "name": "",
                "embedding": ""
            }

        if embedding_b64:
            rfid_mapping[rfid_tag]["embedding"] = embedding_b64
            save_rfid_mapping(rfid_mapping)
            if not quiet:
                print(f"{Colors.GREEN}  [OK] Embedding saved for RFID {rfid_tag} (student {student_id}){Colors.RESET}")
            return embedding_b64

        if not quiet:
            print(f"{Colors.YELLOW}  [WARN] No embedding available for student {student_id}{Colors.RESET}")

        save_rfid_mapping(rfid_mapping)
        return None

    except Exception as e:
        if not quiet:
            print(f"{Colors.RED}  [ERROR] Exception fetching embedding: {e}{Colors.RESET}")
        return None

def decode_embedding(embedding_b64: str) -> Optional[np.ndarray]:
    """Decode base64 embedding string to numpy array"""
    try:
        embedding_bytes = base64.b64decode(embedding_b64)
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
        return embedding
    except Exception as e:
        print(f"{Colors.RED}  [ERROR] Error decoding embedding: {e}{Colors.RESET}")
        return None

def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Calculate cosine similarity between two embeddings"""
    try:
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(np.clip(similarity, -1.0, 1.0))

    except Exception as e:
        print(f"{Colors.RED}  [ERROR] Similarity calculation failed: {e}{Colors.RESET}")
        return 0.0

# ============================================================
# VERIFICATION AND BOARDING LOGIC
# ============================================================

def verify_student_identity(config: Dict, rfid_tag: str, student_info: Dict, rfid_mapping: Dict[str, Dict]) -> Tuple[bool, float, Optional[str]]:
    """
    Performs identity verification steps:
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

    # Step 2: Try to get latest face from camera thread
    photo_path = None
    if hasattr(pi_backend, "get_latest_face"):
        photo_path = pi_backend.get_latest_face(student_id, SCRIPT_DIR)

    # Fallback to standard capture
    if not photo_path:
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

    print(f"{Colors.RED}[WARN] LOW CONFIDENCE - Similarity: {confidence:.2%}{Colors.RESET}")

    # Step 5: Retry with fresh embedding
    print(f"\n{Colors.YELLOW}[INFO] Fetching fresh embedding for retry...{Colors.RESET}")
    fresh_b64 = fetch_student_embedding_from_api(config, rfid_tag, rfid_mapping)

    if not fresh_b64:
        return False, confidence, photo_path

    update_local_embedding_cache(rfid_mapping, rfid_tag, fresh_b64)
    fresh_embedding = decode_embedding(fresh_b64)

    if fresh_embedding is None:
        return False, confidence, photo_path

    # Retry verification (up to 3 attempts)
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

            # Clean up old photo
            try:
                if photo_path and Path(photo_path).exists():
                    Path(photo_path).unlink()
            except:
                pass

            return True, float(retry_similarity), retry_photo

        print(f"{Colors.YELLOW}[WARN] Still not verified - Similarity: {retry_similarity:.2%}{Colors.RESET}")

        # Clean up retry photo
        try:
            if retry_photo and Path(retry_photo).exists():
                Path(retry_photo).unlink()
        except:
            pass

    print(f"{Colors.RED}[ERROR] Failed after 3 retries{Colors.RESET}")
    return False, confidence, photo_path

def process_boarding(config: Dict, rfid_tag: str, student_info: Dict, rfid_mapping: Dict[str, Dict]) -> bool:
    """
    Handles BOTH Boarding IN and Boarding OUT.
    - IN requires identity verification (photo + embeddings)
    - OUT does NOT require verification
    """
    student_id = student_info['student_id']
    present = student_info.get('present', 0)  # 0 = boarding IN, 1 = boarding OUT

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}BOARDING {'IN' if present == 0 else 'OUT'}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}Student ID: {student_id}{Colors.RESET}")
    print(f"{Colors.CYAN}RFID Tag: {rfid_tag}{Colors.RESET}\n")

    verified = False
    confidence = 0.0
    photo_path = None

    # Boarding IN requires verification
    if present == 0:
        verified, confidence, photo_path = verify_student_identity(
            config, rfid_tag, student_info, rfid_mapping
        )

        if not verified:
            print(f"{Colors.RED}[ERROR] Boarding IN failed - identity not verified{Colors.RESET}")
    else:
        # Boarding OUT doesn't require verification
        verified = True
        confidence = 1.0
        print(f"{Colors.GREEN}[OK] Boarding OUT - no verification required{Colors.RESET}")

    # Send scan event
    print(f"\n{Colors.BLUE}-> Sending scan event...{Colors.RESET}")

    # Toggle present status if verified
    new_present = present ^ (1 if verified else 0)

    # Prepare payload
    payload = {
        "student_id": student_id,
        "tag_id": rfid_tag,
        "verified": verified,
        "confidence": float(confidence),
        "lat": None,  # Will be populated by backend module if available
        "lon": None,
        "photo": None,
        "present": new_present
    }

    # Add photo if available
    if photo_path and Path(photo_path).exists():
        try:
            with open(photo_path, "rb") as f:
                payload["photo"] = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            print(f"{Colors.YELLOW}[WARN] Could not encode photo: {e}{Colors.RESET}")

    # Update local state
    student_info['present'] = new_present
    save_rfid_mapping(rfid_mapping)

    # Send to backend
    sent = pi_backend.send_packet(config, payload)

    if sent:
        status_color = Colors.RED if not verified else (Colors.YELLOW if new_present == 1 else Colors.GREEN)
        status_text = 'FAILED' if not verified else ('OUT' if new_present == 1 else 'IN')

        print(f"{Colors.GREEN}[OK] Scan event sent successfully{Colors.RESET}")
        print(f"{status_color}[STATUS] {status_text}{Colors.RESET}")

        # Clean up photo
        if photo_path and Path(photo_path).exists():
            try:
                Path(photo_path).unlink()
            except:
                pass
    else:
        print(f"{Colors.RED}[ERROR] Failed to send scan event{Colors.RESET}")

    return sent

# ============================================================
# CONTINUOUS LOCATION UPDATE LOOP
# ============================================================

def continuous_location_updater(config: Dict, stop_event: threading.Event) -> None:
    """
    Background thread that continuously updates bus location every 10 seconds.
    Sends fallback null location if GPS unavailable.
    """
    print(f"{Colors.CYAN}[INFO] Starting continuous location updater...{Colors.RESET}")

    update_interval = 10  # seconds
    consecutive_failures = 0
    max_consecutive_failures = 5

    while not stop_event.is_set():
        try:
            bus_number = config.get("bus_number")

            if not bus_number:
                print(f"{Colors.YELLOW}[WARN] No bus number in config, skipping location update{Colors.RESET}")
                time.sleep(update_interval)
                continue

            # Get GPS location
            lat, lon = None, None

            if hasattr(pi_backend, "get_gps"):
                try:
                    gps_data = pi_backend.get_gps()
                    if gps_data:
                        lat = gps_data.get("lat")
                        lon = gps_data.get("lon")
                except Exception as e:
                    print(f"{Colors.YELLOW}[WARN] Failed to get GPS: {e}{Colors.RESET}")

            # Prepare payload
            timestamp = datetime.now(timezone.utc).isoformat()
            payload = {
                "bus_number": bus_number,
                "lat": float(lat) if lat is not None else None,
                "lon": float(lon) if lon is not None else None,
                "timestamp": timestamp
            }

            # Send location update
            success, response = api_request(config, "/api/bus-locations/update", method="POST", data=payload, retries=2)

            if success:
                consecutive_failures = 0
                if lat is not None and lon is not None:
                    print(f"{Colors.GREEN}[OK] Location updated: {bus_number} @ ({lat:.6f}, {lon:.6f}){Colors.RESET}")
                else:
                    print(f"{Colors.CYAN}[OK] Heartbeat sent: {bus_number} (GPS unavailable){Colors.RESET}")
            else:
                consecutive_failures += 1
                error_msg = response.get("error", "Unknown error")
                print(f"{Colors.RED}[ERROR] Location update failed ({consecutive_failures}/{max_consecutive_failures}): {error_msg}{Colors.RESET}")

                if consecutive_failures >= max_consecutive_failures:
                    print(f"{Colors.YELLOW}[WARN] Too many failures, increasing retry interval to 30s{Colors.RESET}")
                    time.sleep(30)
                    consecutive_failures = 0
                    continue

        except Exception as e:
            consecutive_failures += 1
            print(f"{Colors.RED}[ERROR] Exception in location updater: {e}{Colors.RESET}")

        # Wait before next update
        for _ in range(update_interval):
            if stop_event.is_set():
                break
            time.sleep(1)

    print(f"{Colors.CYAN}[INFO] Location updater stopped{Colors.RESET}")

# ============================================================
# MAIN APPLICATION LOOP
# ============================================================

def main():
    """Main scanner loop"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}RASPBERRY PI BOARDING SCANNER - REFACTORED{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.CYAN}Mode: {PI_MODE.upper()}{Colors.RESET}\n")

    # Initialize backend module
    if not pi_backend.initialize():
        print(f"{Colors.RED}[ERROR] Failed to initialize backend module. Exiting.{Colors.RESET}")
        sys.exit(1)

    # Start camera thread if available
    if hasattr(pi_backend, "start_camera_thread"):
        pi_backend.start_camera_thread()

    # Load configuration
    config = load_config()

    if not config:
        print(f"\n{Colors.YELLOW}No device configuration found. Starting registration...{Colors.RESET}\n")

        backend_url = input(f"{Colors.CYAN}Backend URL [{DEFAULT_BACKEND_URL}]: {Colors.RESET}").strip() or DEFAULT_BACKEND_URL
        bus_number = input(f"{Colors.CYAN}Bus Number (e.g., 'BUS-001'): {Colors.RESET}").strip()
        device_name = input(f"{Colors.CYAN}Device Name (e.g., 'Pi-Bus-001'): {Colors.RESET}").strip()

        if not bus_number or not device_name:
            print(f"{Colors.RED}[ERROR] Bus Number and Device Name are required!{Colors.RESET}")
            sys.exit(1)

        config = register_device(backend_url, bus_number, device_name)

        if not config:
            print(f"{Colors.RED}[ERROR] Failed to register device. Exiting.{Colors.RESET}")
            sys.exit(1)

        save_config(config)
    else:
        print(f"\n{Colors.GREEN}[OK] Device configuration loaded{Colors.RESET}")
        print(f"{Colors.CYAN}  Device: {config['device_name']}{Colors.RESET}")
        print(f"{Colors.CYAN}  Backend: {config['backend_url']}{Colors.RESET}")

    # Load RFID mapping
    rfid_mapping = load_rfid_mapping()

    if not rfid_mapping:
        print(f"\n{Colors.YELLOW}[WARN] No RFID mapping file found{Colors.RESET}")
        print(f"{Colors.YELLOW}  Create '{RFID_MAPPING_FILE}' with mappings.{Colors.RESET}\n")
    else:
        print(f"\n{Colors.GREEN}[OK] RFID mapping loaded ({len(rfid_mapping)} students){Colors.RESET}")
        cached_count = sum(1 for s in rfid_mapping.values() if s.get('embedding'))
        print(f"{Colors.CYAN}  Cached embeddings: {cached_count}/{len(rfid_mapping)}{Colors.RESET}")

    # Start location updater
    location_thread = threading.Thread(
        target=continuous_location_updater,
        args=(config, shutdown_flag),
        daemon=True,
        name="LocationUpdater"
    )
    location_thread.start()
    print(f"{Colors.GREEN}[OK] Location updater started{Colors.RESET}")

    # Main scanning loop
    print(f"\n{Colors.BOLD}{Colors.GREEN}Scanner ready!{Colors.RESET}\n")

    try:
        while not shutdown_flag.is_set():
            try:
                # Read RFID tag
                rfid_tag = pi_backend.read_rfid()

                if not rfid_tag:
                    print(f"\n{Colors.YELLOW}Exiting scanner...{Colors.RESET}")
                    break

                # Lookup student
                student_info = rfid_mapping.get(rfid_tag)

                # Fetch from backend if missing
                if not student_info or 'student_id' not in student_info:
                    print(f"{Colors.BLUE}-> Querying backend for RFID {rfid_tag}...{Colors.RESET}")
                    fetch_student_embedding_from_api(config, rfid_tag, rfid_mapping)
                    student_info = rfid_mapping.get(rfid_tag)

                if not student_info or not student_info.get('student_id'):
                    print(f"{Colors.RED}[ERROR] Unknown RFID: {rfid_tag}{Colors.RESET}")
                    continue

                # Process boarding
                process_boarding(config, rfid_tag, student_info, rfid_mapping)
                print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}\n")

            except Exception as e:
                print(f"\n{Colors.RED}[ERROR] {e}{Colors.RESET}")
                import traceback
                traceback.print_exc()
                continue

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Scanner interrupted.{Colors.RESET}")

    finally:
        # Cleanup
        print(f"\n{Colors.CYAN}Shutting down...{Colors.RESET}")

        # Stop camera thread
        if hasattr(pi_backend, "stop_camera_thread"):
            pi_backend.stop_camera_thread()

        # Stop location updater
        shutdown_flag.set()
        if location_thread.is_alive():
            location_thread.join(timeout=5)

        # Cleanup backend
        pi_backend.cleanup()

        print(f"{Colors.CYAN}Goodbye!{Colors.RESET}\n")

if __name__ == "__main__":
    main()
