#!/usr/bin/env python3
"""
Hardware Backend Module for Pi Scanner
=======================================

This module provides real hardware implementations for Raspberry Pi.
Exposes identical function signatures as pi_simulated.py.
"""

import sys
import numpy as np
from typing import Optional, Dict
from pathlib import Path
import time

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def initialize() -> bool:
    """Initialize hardware components"""
    print(f"{Colors.CYAN}→ Initializing HARDWARE mode{Colors.RESET}")
    
    # Initialize RFID reader
    if not init_rfid_reader():
        return False
    
    # Initialize camera
    if not init_camera():
        return False
    
    # Check DeepFace
    try:
        import deepface
        print(f"{Colors.GREEN}✓ DeepFace available{Colors.RESET}")
    except ImportError:
        print(f"{Colors.YELLOW}⚠ DeepFace not installed{Colors.RESET}")
        if not install_deepface():
            return False
    
    return True

def install_deepface() -> bool:
    """Install DeepFace and dependencies"""
    print(f"{Colors.YELLOW}Installing DeepFace...{Colors.RESET}")
    try:
        import subprocess
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "deepface", "tf-keras", "tensorflow", "--quiet"
        ])
        print(f"{Colors.GREEN}✓ DeepFace installed{Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}✗ Failed to install DeepFace: {e}{Colors.RESET}")
        return False

def init_rfid_reader() -> bool:
    """Initialize RFID reader hardware"""
    global rfid_reader
    try:
        # Try to import RFID library (MFRC522 for RC522 module)
        try:
            import RPi.GPIO as GPIO
            from mfrc522 import SimpleMFRC522
            
            rfid_reader = SimpleMFRC522()
            print(f"{Colors.GREEN}✓ RFID reader initialized{Colors.RESET}")
            return True
            
        except ImportError:
            print(f"{Colors.YELLOW}⚠ RFID library not found{Colors.RESET}")
            print(f"{Colors.YELLOW}  Install: pip install mfrc522 RPi.GPIO{Colors.RESET}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}✗ RFID initialization failed: {e}{Colors.RESET}")
        return False

def init_camera() -> bool:
    """Initialize Pi camera"""
    global camera
    try:
        # Try to import picamera2 (newer) or picamera (legacy)
        try:
            from picamera2 import Picamera2
            camera = Picamera2()
            camera.configure(camera.create_still_configuration())
            print(f"{Colors.GREEN}✓ Camera initialized (picamera2){Colors.RESET}")
            return True
            
        except ImportError:
            try:
                import picamera
                camera = picamera.PiCamera()
                print(f"{Colors.GREEN}✓ Camera initialized (picamera){Colors.RESET}")
                return True
            except ImportError:
                print(f"{Colors.YELLOW}⚠ Camera library not found{Colors.RESET}")
                print(f"{Colors.YELLOW}  Install: pip install picamera2 or pip install picamera{Colors.RESET}")
                return False
                
    except Exception as e:
        print(f"{Colors.RED}✗ Camera initialization failed: {e}{Colors.RESET}")
        return False

def read_rfid() -> Optional[str]:
    """Read RFID tag from hardware reader"""
    try:
        print(f"\n{Colors.CYAN}→ [HW] Waiting for RFID scan...{Colors.RESET}")
        
        # Read from RFID reader
        id, text = rfid_reader.read()
        
        if id:
            rfid_tag = f"RFID-{id}"
            print(f"{Colors.GREEN}✓ RFID scanned: {rfid_tag}{Colors.RESET}")
            return rfid_tag
        else:
            print(f"{Colors.RED}✗ No RFID detected{Colors.RESET}")
            return None
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Scan interrupted{Colors.RESET}")
        return None
    except Exception as e:
        print(f"{Colors.RED}✗ RFID read error: {e}{Colors.RESET}")
        return None

def capture_student_photo(config: Dict, student_id: str, script_dir: Path) -> Optional[str]:
    """
    Capture photo using Pi camera.
    Takes a photo and saves it locally.
    """
    print(f"{Colors.BLUE}→ [HW] Capturing photo with camera...{Colors.RESET}")
    
    try:
        # Create temp directory
        temp_dir = script_dir / "temp_photos"
        temp_dir.mkdir(exist_ok=True)
        
        photo_path = temp_dir / f"{student_id}_captured.jpg"
        
        # Capture photo based on camera type
        try:
            # Try picamera2 first
            from picamera2 import Picamera2
            camera.start()
            time.sleep(2)  # Let camera warm up
            camera.capture_file(str(photo_path))
            camera.stop()
            
        except (ImportError, NameError):
            # Fallback to legacy picamera
            import picamera
            camera.start_preview()
            time.sleep(2)  # Camera warm-up
            camera.capture(str(photo_path))
            camera.stop_preview()
        
        print(f"{Colors.GREEN}   ✓ Photo captured{Colors.RESET}")
        return str(photo_path)
        
    except Exception as e:
        print(f"{Colors.RED}   ✗ Capture error: {e}{Colors.RESET}")
        return None

def generate_face_embedding(photo_path: str) -> Optional[np.ndarray]:
    """Generate face embedding using DeepFace"""
    try:
        from deepface import DeepFace
        
        print(f"{Colors.BLUE}→ [HW] Generating face embedding...{Colors.RESET}")
        
        embedding_objs = DeepFace.represent(
            img_path=str(photo_path),
            model_name='Facenet',
            enforce_detection=False
        )
        
        if embedding_objs and len(embedding_objs) > 0:
            embedding = embedding_objs[0]['embedding']
            print(f"{Colors.GREEN}   ✓ Embedding generated{Colors.RESET}")
            return np.array(embedding)
        else:
            print(f"{Colors.RED}   ✗ No face detected{Colors.RESET}")
            return None
            
    except Exception as e:
        print(f"{Colors.RED}   ✗ Error: {e}{Colors.RESET}")
        return None

def send_packet(config: Dict, payload: Dict) -> bool:
    """Send data packet to backend (scan event)"""
    try:
        import requests
        
        print(f"{Colors.BLUE}→ [HW] Sending packet to backend...{Colors.RESET}")
        
        url = f"{config['backend_url']}/api/scan_event"
        headers = {"X-API-Key": config['api_key']}
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"{Colors.GREEN}   ✓ Packet sent successfully{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}   ✗ Failed: {response.text}{Colors.RESET}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}   ✗ Error: {e}{Colors.RESET}")
        return False

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
        
        print(f"{Colors.CYAN}→ [HW] Hardware cleanup complete{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.YELLOW}⚠ Cleanup warning: {e}{Colors.RESET}")
