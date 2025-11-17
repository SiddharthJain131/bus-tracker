#!/usr/bin/env python3
"""
Hardware Backend Module for Pi Scanner
=======================================

This module provides real hardware implementations for Raspberry Pi.
Integrates RFID scanning, camera capture via ADB, face detection, and GPS location.
Exposes identical function signatures as pi_simulated.py.
"""

import sys
import numpy as np
from typing import Optional, Dict, Tuple
from pathlib import Path
import time
import subprocess
import os
import re
import cv2
from datetime import datetime

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

# Global hardware handles
rfid_reader = None
camera = None
detector = None

# --- ADB Configuration ---
DEVICE_IP = "172.17.72.186"
DEVICE_ID = f"{DEVICE_IP}:5555"
PHOTO_AGE_LIMIT = 20
MAX_RETRIES = 5
SLEEP_TIME = 5
DROIDCAM_PORT = "4747"

# --- GPIO Configuration ---
LED_SCAN = 22
BIN0 = 23
BIN1 = 24
BIN2 = 25
BINARY_PINS = [BIN0, BIN1, BIN2]


def initialize() -> bool:
    """
    Initialize hardware components with graceful degradation.
    Returns True if critical components initialized successfully.
    Non-critical failures (like GPIO LEDs) will warn but not fail.
    """
    print(f"{Colors.CYAN}-> Initializing HARDWARE mode{Colors.RESET}")
    
    critical_failures = []
    
    # Initialize GPIO for LEDs (non-critical - for visual feedback only)
    if not init_gpio():
        print(f"{Colors.YELLOW}[WARN] Continuing without GPIO LED controls{Colors.RESET}")
    
    # Initialize RFID reader (CRITICAL)
    if not init_rfid_reader():
        critical_failures.append("RFID reader")
    
    # Initialize camera (CRITICAL)
    if not init_camera():
        critical_failures.append("Camera")
    
    # Initialize face detector (CRITICAL)
    if not init_face_detector():
        critical_failures.append("Face detector")
    
    # Check DeepFace (CRITICAL)
    try:
        import deepface
        print(f"{Colors.GREEN}[OK] DeepFace available{Colors.RESET}")
    except ImportError:
        print(f"{Colors.YELLOW}[WARN] DeepFace not installed, attempting installation...{Colors.RESET}")
        if not install_deepface():
            critical_failures.append("DeepFace")
    
    # Report initialization status
    if critical_failures:
        print(f"\n{Colors.RED}[ERROR] Critical component failures:{Colors.RESET}")
        for component in critical_failures:
            print(f"  ❌ {component}")
        print(f"{Colors.RED}Cannot proceed without these components.{Colors.RESET}")
        return False
    
    print(f"\n{Colors.GREEN}[OK] All critical hardware components initialized{Colors.RESET}")
    return True


def init_gpio() -> bool:
    """Initialize GPIO pins for LEDs and binary counter display"""
    try:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LED_SCAN, GPIO.OUT)
        for pin in BINARY_PINS:
            GPIO.setup(pin, GPIO.OUT)
        default_gpio_state()
        print(f"{Colors.GREEN}[OK] GPIO initialized{Colors.RESET}")
        return True
    except ImportError:
        print(f"{Colors.YELLOW}[WARN] RPi.GPIO not installed - LED controls disabled{Colors.RESET}")
        print(f"{Colors.YELLOW}  Install: pip install RPi.GPIO{Colors.RESET}")
        return False
    except RuntimeError as e:
        # This happens when not running on actual Raspberry Pi hardware
        print(f"{Colors.YELLOW}[WARN] GPIO not available (not running on Pi hardware): {e}{Colors.RESET}")
        return False
    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] GPIO initialization failed: {e}{Colors.RESET}")
        return False


def default_gpio_state():
    """Turn off all LEDs"""
    try:
        import RPi.GPIO as GPIO
        GPIO.output(LED_SCAN, GPIO.LOW)
        for pin in BINARY_PINS:
            GPIO.output(pin, GPIO.LOW)
    except:
        pass


def display_binary(value: int):
    """Display a 3-bit number on the binary LEDs"""
    try:
        import RPi.GPIO as GPIO
        for i in range(len(BINARY_PINS)):
            if (value >> i) & 1:
                GPIO.output(BINARY_PINS[i], GPIO.HIGH)
            else:
                GPIO.output(BINARY_PINS[i], GPIO.LOW)
    except:
        pass


def install_deepface() -> bool:
    """Install DeepFace and dependencies"""
    print(f"{Colors.YELLOW}Installing DeepFace...{Colors.RESET}")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "deepface", "tf-keras", "tensorflow", "--quiet"
        ])
        print(f"{Colors.GREEN}[OK] DeepFace installed{Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Failed to install DeepFace: {e}{Colors.RESET}")
        return False


def init_rfid_reader() -> bool:
    """Initialize RFID reader hardware"""
    global rfid_reader
    try:
        import RPi.GPIO as GPIO
        from mfrc522 import SimpleMFRC522
        
        rfid_reader = SimpleMFRC522()
        print(f"{Colors.GREEN}[OK] RFID reader initialized{Colors.RESET}")
        return True
        
    except ImportError:
        print(f"{Colors.YELLOW}[WARN] RFID library not found{Colors.RESET}")
        print(f"{Colors.YELLOW}  Install: pip install mfrc522 RPi.GPIO{Colors.RESET}")
        return False
        
    except Exception as e:
        print(f"{Colors.RED}[ERROR] RFID initialization failed: {e}{Colors.RESET}")
        return False


def init_camera() -> bool:
    """Initialize camera via ADB connection"""
    global camera
    try:
        print(f"{Colors.CYAN}-> Connecting to ADB device {DEVICE_IP}...{Colors.RESET}")
        subprocess.run(["adb", "connect", f"{DEVICE_IP}:5555"], check=True)
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
        
        if f"{DEVICE_IP}:5555" not in result.stdout or "device" not in result.stdout.split(f"{DEVICE_IP}:5555")[-1]:
            print(f"{Colors.RED}[ERROR] ADB device not found or offline{Colors.RESET}")
            return False
        
        camera = "adb_connected"
        print(f"{Colors.GREEN}[OK] Camera initialized (ADB){Colors.RESET}")
        return True
        
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Camera initialization failed: {e}{Colors.RESET}")
        return False


def init_face_detector() -> bool:
    """Initialize UltraLight face detector"""
    global detector
    try:
        from ultralight import UltraLightDetector
        detector = UltraLightDetector()
        print(f"{Colors.GREEN}[OK] Face detector initialized{Colors.RESET}")
        return True
    except ImportError:
        print(f"{Colors.YELLOW}[WARN] ultralight not installed{Colors.RESET}")
        print(f"{Colors.YELLOW}  Install: pip install ultralight{Colors.RESET}")
        return False
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Face detector initialization failed: {e}{Colors.RESET}")
        return False


def adb(cmd: list) -> str:
    """Run an ADB command and return its output"""
    full_cmd = ["adb", "-s", DEVICE_ID] + cmd
    result = subprocess.run(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.stderr:
        print(f"{Colors.YELLOW}ADB stderr: {result.stderr.strip()}{Colors.RESET}")
    return result.stdout.strip()


def take_photo_adb():
    """Trigger Android camera shutter via ADB"""
    print(f"{Colors.BLUE}-> Triggering camera...{Colors.RESET}")
    adb(["shell", "input", "keyevent", "27"])
    time.sleep(2)


def get_recent_photo_adb() -> Optional[str]:
    """Get newest photo file name from Android"""
    output = adb(["shell", "ls", "-t", "/storage/emulated/0/DCIM/Camera/"])
    if not output:
        return None
    return output.splitlines()[0].strip()


def get_file_age_adb(file_path: str) -> int:
    """Calculate file age in seconds"""
    curr_time = int(time.time())
    file_mod_time = int(adb(["shell", "stat", "-c", "%Y", file_path]))
    return curr_time - file_mod_time


def pull_recent_photo_adb(dest_folder: Path) -> Tuple[bool, Optional[str]]:
    """Take photo via ADB and pull it from device if recent enough"""
    dest_folder.mkdir(exist_ok=True)
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        take_photo_adb()
        recent_file = get_recent_photo_adb()
        if not recent_file:
            print(f"{Colors.YELLOW}No photo found on device{Colors.RESET}")
            retry_count += 1
            time.sleep(SLEEP_TIME)
            continue
        
        file_path = f"/storage/emulated/0/DCIM/Camera/{recent_file}"
        age = get_file_age_adb(file_path)
        print(f"File: {recent_file}, Age: {age} seconds")
        
        if age < PHOTO_AGE_LIMIT:
            print(f"{Colors.BLUE}-> Recent photo detected, pulling...{Colors.RESET}")
            adb(["pull", file_path, str(dest_folder)])
            adb(["shell", "rm", file_path])
            return True, recent_file
        
        print(f"{Colors.YELLOW}No recent photo, retrying...{Colors.RESET}")
        retry_count += 1
        time.sleep(SLEEP_TIME)
    
    print(f"{Colors.RED}[ERROR] No photo found after {MAX_RETRIES} retries{Colors.RESET}")
    return False, None


def get_gps_location_adb() -> Tuple[Optional[float], Optional[float]]:
    """Get GPS location from Android device via ADB"""
    try:
        result = subprocess.run(
            ['adb', 'shell', 'dumpsys', 'location'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        output = result.stdout
        locations = re.findall(r'last location=Location\[([^\]]+)\]', output)
        valid_locations = [loc for loc in locations if 'null' not in loc]
        
        if not valid_locations:
            return None, None
        
        latest_loc = valid_locations[-1]
        match = re.search(r'([-\d.]+),([-\d.]+)', latest_loc)
        
        if match:
            latitude = float(match.group(1))
            longitude = float(match.group(2))
            print(f"{Colors.GREEN}[OK] GPS: {latitude}, {longitude}{Colors.RESET}")
            return latitude, longitude
        else:
            return None, None
            
    except subprocess.CalledProcessError as e:
        print(f"{Colors.YELLOW}[WARN] GPS location failed: {e}{Colors.RESET}")
        return None, None


def read_rfid() -> Optional[str]:
    """Read RFID tag from hardware reader"""
    try:
        import RPi.GPIO as GPIO
        print(f"\n{Colors.CYAN}-> [HW] Waiting for RFID scan...{Colors.RESET}")
        
        # Turn on scan LED
        GPIO.output(LED_SCAN, GPIO.HIGH)
        
        # Read from RFID reader (blocking)
        id, text = rfid_reader.read()
        
        # Turn off scan LED
        GPIO.output(LED_SCAN, GPIO.LOW)
        
        if id:
            rfid_tag = f"RFID-{id}"
            print(f"{Colors.GREEN}[OK] RFID scanned: {rfid_tag}{Colors.RESET}")
            return rfid_tag
        else:
            print(f"{Colors.RED}[ERROR] No RFID detected{Colors.RESET}")
            return None
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Scan interrupted{Colors.RESET}")
        return None
    except Exception as e:
        print(f"{Colors.RED}[ERROR] RFID read error: {e}{Colors.RESET}")
        return None


def crop_with_offset(frame, box, offset_ratio=0.3):
    """Crop face with offset for better framing"""
    x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
    height, width = frame.shape[:2]
    
    w = x2 - x1
    h = y2 - y1
    cx = x1 + w // 2
    cy = y1 + h // 2
    
    half_w = int(w * (1 + offset_ratio) / 2)
    half_h = int(h * (1 + offset_ratio) / 2)
    
    x_start = max(cx - half_w, 0)
    y_start = max(cy - half_h, 0)
    x_end = min(cx + half_w, width)
    y_end = min(cy + half_h, height)
    
    return frame[y_start:y_end, x_start:x_end]


def capture_student_photo(config: Dict, student_id: str, script_dir: Path) -> Optional[str]:
    """
    Capture photo using Android camera via ADB or DroidCam.
    Takes a photo, detects face, crops, and saves it locally.
    """
    print(f"{Colors.BLUE}-> [HW] Capturing photo...{Colors.RESET}")
    
    try:
        # Create temp directory
        temp_dir = script_dir / "temp_photos"
        temp_dir.mkdir(exist_ok=True)
        
        # Attempt to pull photo from Android via ADB
        success, photo_filename = pull_recent_photo_adb(temp_dir)
        
        if not success:
            print(f"{Colors.RED}[ERROR] Failed to capture photo{Colors.RESET}")
            return None
        
        photo_path = temp_dir / photo_filename
        
        # Load image and detect face
        frame = cv2.imread(str(photo_path))
        if frame is None:
            print(f"{Colors.RED}[ERROR] Failed to load image{Colors.RESET}")
            return None
        
        # Detect faces
        boxes, scores = detector.detect_one(frame)
        
        if boxes is not None and len(boxes) > 0:
            # Get best face
            boxes_list = boxes.tolist() if isinstance(boxes, np.ndarray) else list(boxes)
            scores_list = scores.tolist() if isinstance(scores, np.ndarray) else list(scores)
            best_idx = scores_list.index(max(scores_list))
            best_box = boxes_list[best_idx]
            
            # Crop face
            cropped_face = crop_with_offset(frame, best_box)
            
            if cropped_face.size > 0:
                # Save cropped face
                final_path = temp_dir / f"{student_id}_captured.jpg"
                cv2.imwrite(str(final_path), cropped_face)
                print(f"{Colors.GREEN}[OK] Photo captured and cropped{Colors.RESET}")
                return str(final_path)
        
        print(f"{Colors.YELLOW}[WARN] No face detected, using original{Colors.RESET}")
        return str(photo_path)
        
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Capture error: {e}{Colors.RESET}")
        return None


def generate_face_embedding(photo_path: str) -> Optional[np.ndarray]:
    """Generate face embedding using DeepFace"""
    try:
        from deepface import DeepFace
        
        print(f"{Colors.BLUE}-> [HW] Generating face embedding...{Colors.RESET}")
        
        embedding_objs = DeepFace.represent(
            img_path=str(photo_path),
            model_name='Facenet',
            enforce_detection=False
        )
        
        if embedding_objs and len(embedding_objs) > 0:
            embedding = embedding_objs[0]['embedding']
            print(f"{Colors.GREEN}[OK] Embedding generated{Colors.RESET}")
            return np.array(embedding)
        else:
            print(f"{Colors.RED}[ERROR] No face detected{Colors.RESET}")
            return None
            
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Error: {e}{Colors.RESET}")
        return None


def send_packet(config: Dict, payload: Dict) -> bool:
    """Send data packet to backend (scan event)"""
    try:
        import requests
        
        print(f"{Colors.BLUE}-> [HW] Sending packet to backend...{Colors.RESET}")
        
        # Add GPS location if available
        lat, lon = get_gps_location_adb()
        if lat is not None and lon is not None:
            payload['latitude'] = lat
            payload['longitude'] = lon
        
        url = f"{config['backend_url']}/api/scan_event"
        headers = {"X-API-Key": config['api_key']}
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"{Colors.GREEN}[OK] Packet sent successfully{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}[ERROR] Failed: {response.text}{Colors.RESET}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Error: {e}{Colors.RESET}")
        return False


def get_gps() -> Optional[Dict[str, Optional[float]]]:
    """
    Get GPS location from Android device via ADB.
    Returns dict with 'lat' and 'lon' keys, or None values if GPS unavailable.
    
    This function is called by pi_server.py for location updates.
    
    Returns:
        Dict with 'lat' and 'lon' keys (float or None)
        Example: {"lat": 37.7749, "lon": -122.4194} or {"lat": None, "lon": None}
    """
    try:
        lat, lon = get_gps_location_adb()
        return {"lat": lat, "lon": lon}
    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] GPS error: {e}{Colors.RESET}")
        return {"lat": None, "lon": None}



def cleanup():
    """Cleanup hardware resources"""
    try:
        # Close camera
        if 'camera' in globals():
            try:
                camera.close()
            except:
                pass
        
        # Cleanup GPIO
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except:
            pass
        
        print(f"{Colors.CYAN}-> [HW] Hardware cleanup complete{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.YELLOW}[WARN] Cleanup warning: {e}{Colors.RESET}")
