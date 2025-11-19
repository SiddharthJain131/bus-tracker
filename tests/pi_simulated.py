#!/usr/bin/env python3
"""
Simulated Backend Module for Pi Scanner - REFACTORED
====================================================

This module provides simulated implementations for development and testing.
Exposes identical function signatures as pi_hardware_mod.py.

IMPROVEMENTS:
- Added missing functions (get_gps, start_camera_thread, stop_camera_thread, get_latest_face)
- Made paths configurable via environment variables
- Added proper error handling for all operations
- Added timeout handling
- Improved logging and error messages
"""

import sys
import os
import time
import threading
from pathlib import Path
from typing import Optional, Dict

import requests
import numpy as np


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'


# ============================================================
# CONFIGURATION
# ============================================================

# Simulated GPS coordinates (default to San Francisco)
DEFAULT_LAT = float(os.getenv("SIM_GPS_LAT", "37.7749"))
DEFAULT_LON = float(os.getenv("SIM_GPS_LON", "-122.4194"))

# Photo storage path (relative to backend)
PHOTO_BASE_PATH = os.getenv("PHOTO_BASE_PATH", "../backend/photos/students")

# Simulated camera thread state (matches hardware module)
camera_thread_running = False
camera_thread = None
camera_frame_lock = threading.Lock()
latest_full_frame = None


# ============================================================
# INITIALIZATION
# ============================================================

def initialize() -> bool:
    """Initialize simulated backend"""
    print(f"{Colors.CYAN}-> Initializing SIMULATED mode{Colors.RESET}")
    
    # Check DeepFace installation
    try:
        import deepface  # noqa: F401
        print(f"{Colors.GREEN}[OK] DeepFace available{Colors.RESET}")
        return True
    except ImportError:
        print(f"{Colors.YELLOW}[WARN] DeepFace not installed{Colors.RESET}")
        print(f"{Colors.YELLOW}  Install with: pip install deepface tf-keras tensorflow{Colors.RESET}")
        print(f"{Colors.YELLOW}  Continuing without face recognition (API testing mode only){Colors.RESET}")
        return True


def install_deepface() -> bool:
    """Install DeepFace and dependencies"""
    print(f"{Colors.YELLOW}Installing DeepFace...{Colors.RESET}")
    
    try:
        import subprocess
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "deepface", "tf-keras", "tensorflow", "--quiet"],
            timeout=300
        )
        print(f"{Colors.GREEN}[OK] DeepFace installed{Colors.RESET}")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}[ERROR] DeepFace installation timed out{Colors.RESET}")
        return False
        
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Failed to install DeepFace: {e}{Colors.RESET}")
        return False


# ============================================================
# CAMERA THREAD SIMULATION (for API compatibility)
# ============================================================

def camera_thread_loop() -> None:
    """
    Simulated camera thread.
    In simulation mode, we don't have a real camera feed, so this just maintains
    the thread lifecycle for API compatibility.
    """
    global camera_thread_running
    
    print(f"{Colors.CYAN}[SIM] Camera thread started (simulated mode){Colors.RESET}")
    
    while camera_thread_running:
        time.sleep(1.0)
    
    # Clear frame on stop
    global latest_full_frame
    with camera_frame_lock:
        latest_full_frame = None
    
    print(f"{Colors.CYAN}[SIM] Camera thread stopped{Colors.RESET}")


def start_camera_thread() -> bool:
    """Start simulated camera thread for API compatibility"""
    global camera_thread_running, camera_thread
    
    if camera_thread_running:
        return True
    
    camera_thread_running = True
    camera_thread = threading.Thread(target=camera_thread_loop, daemon=True, name="SimCameraThread")
    camera_thread.start()
    
    print(f"{Colors.GREEN}[OK] Simulated camera thread started{Colors.RESET}")
    return True


def stop_camera_thread() -> None:
    """Stop simulated camera thread"""
    global camera_thread_running
    
    if not camera_thread_running:
        return
    
    camera_thread_running = False
    
    if camera_thread is not None and camera_thread.is_alive():
        camera_thread.join(timeout=2.0)
    
    print(f"{Colors.CYAN}[SIM] Camera thread stopped{Colors.RESET}")


def get_latest_frame_from_thread() -> Optional[np.ndarray]:
    """
    Get the latest full frame from the camera thread.
    In simulated mode, always returns None (no live camera feed).
    """
    return None


def get_latest_face(student_id: str, script_dir: Path) -> Optional[str]:
    """
    Simulated version - returns None as we don't have a real camera thread.
    This ensures the system falls back to capture_student_photo.
    
    Matches hardware module signature for compatibility.
    """
    return None


# ============================================================
# RFID SIMULATION
# ============================================================

def read_rfid() -> Optional[str]:
    """Read RFID tag via user input (simulation)"""
    try:
        rfid = input(f"\n{Colors.CYAN}[SIM] Enter RFID tag (or 'q' to quit): {Colors.RESET}").strip()
        
        if rfid.lower() == 'q':
            return None
        
        if not rfid:
            print(f"{Colors.YELLOW}[WARN] Empty RFID tag{Colors.RESET}")
            return read_rfid()  # Try again
        
        return rfid
        
    except (KeyboardInterrupt, EOFError):
        print(f"\n{Colors.YELLOW}[SIM] Input interrupted{Colors.RESET}")
        return None


# ============================================================
# PHOTO CAPTURE SIMULATION
# ============================================================

def capture_student_photo(config: Dict, student_id: str, script_dir: Path) -> Optional[str]:
    """
    Simulate photo capture by fetching student's photo from backend storage.
    In simulation mode, we use the stored profile photo.
    """
    print(f"{Colors.BLUE}-> [SIM] Fetching student photo from storage...{Colors.RESET}")
    
    try:
        # Construct path to student's profile photo
        script_path = Path(__file__).resolve().parent
        photo_source = script_path / PHOTO_BASE_PATH / student_id / "profile.jpg"
        
        # Check if photo exists
        if not photo_source.exists():
            print(f"{Colors.RED}   [ERROR] Profile photo not found at: {photo_source}{Colors.RESET}")
            print(f"{Colors.YELLOW}   [HINT] Expected path: {photo_source}{Colors.RESET}")
            return None
        
        # Create temp directory
        temp_dir = script_dir / "temp_photos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy photo to temp location
        photo_dest = temp_dir / f"{student_id}_profile.jpg"
        
        with open(photo_source, "rb") as src:
            with open(photo_dest, "wb") as dst:
                dst.write(src.read())
        
        print(f"{Colors.GREEN}   [OK] Photo loaded from storage{Colors.RESET}")
        return str(photo_dest)
        
    except PermissionError as e:
        print(f"{Colors.RED}   [ERROR] Permission denied: {e}{Colors.RESET}")
        return None
        
    except Exception as e:
        print(f"{Colors.RED}   [ERROR] Failed to load photo: {e}{Colors.RESET}")
        return None


# ============================================================
# FACE EMBEDDING
# ============================================================

def generate_face_embedding(photo_path: str) -> Optional[np.ndarray]:
    """Generate face embedding using DeepFace"""
    try:
        from deepface import DeepFace
        
        print(f"{Colors.BLUE}-> [SIM] Generating face embedding...{Colors.RESET}")
        
        # Verify photo exists
        if not Path(photo_path).exists():
            print(f"{Colors.RED}   [ERROR] Photo not found: {photo_path}{Colors.RESET}")
            return None
        
        embedding_objs = DeepFace.represent(
            img_path=str(photo_path),
            model_name='Facenet',
            enforce_detection=False
        )
        
        if embedding_objs and len(embedding_objs) > 0:
            embedding = embedding_objs[0]['embedding']
            print(f"{Colors.GREEN}   [OK] Embedding generated (dim: {len(embedding)}){Colors.RESET}")
            return np.array(embedding, dtype=np.float32)
        else:
            print(f"{Colors.RED}   [ERROR] No face detected in photo{Colors.RESET}")
            return None
            
    except ImportError:
        print(f"{Colors.RED}   [ERROR] DeepFace not installed{Colors.RESET}")
        return None
        
    except Exception as e:
        print(f"{Colors.RED}   [ERROR] Embedding generation failed: {e}{Colors.RESET}")
        return None


# ============================================================
# NETWORK COMMUNICATION
# ============================================================

def send_packet(config: Dict, payload: Dict) -> bool:
    """Send data packet to backend (scan event)"""
    try:
        print(f"{Colors.BLUE}-> [SIM] Sending packet to backend...{Colors.RESET}")
        
        # Add simulated GPS location if not present
        if 'lat' not in payload or payload['lat'] is None:
            payload['lat'] = DEFAULT_LAT
        if 'lon' not in payload or payload['lon'] is None:
            payload['lon'] = DEFAULT_LON
        
        url = f"{config['backend_url']}/api/scan_event"
        headers = {"X-API-Key": config['api_key']}
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print(f"{Colors.GREEN}   [OK] Packet sent successfully{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}   [ERROR] Backend returned {response.status_code}: {response.text}{Colors.RESET}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"{Colors.RED}   [ERROR] Request timed out{Colors.RESET}")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"{Colors.RED}   [ERROR] Connection failed: {e}{Colors.RESET}")
        return False
        
    except Exception as e:
        print(f"{Colors.RED}   [ERROR] Send packet failed: {e}{Colors.RESET}")
        return False


def get_gps() -> Dict[str, Optional[float]]:
    """
    Get simulated GPS location.
    Returns dict with 'lat' and 'lon' keys.
    
    This function is called by pi_server.py for location updates.
    
    Returns:
        Dict with 'lat' and 'lon' keys (float)
        Example: {"lat": 37.7749, "lon": -122.4194}
    """
    return {
        "lat": DEFAULT_LAT,
        "lon": DEFAULT_LON
    }


# ============================================================
# CLEANUP
# ============================================================

def cleanup() -> None:
    """Cleanup simulated resources"""
    stop_camera_thread()
    print(f"{Colors.CYAN}-> [SIM] Cleanup complete{Colors.RESET}")
