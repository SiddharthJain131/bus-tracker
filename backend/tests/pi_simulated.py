#!/usr/bin/env python3
"""
Simulated Backend Module for Pi Scanner
========================================

This module provides simulated implementations for development and testing.
Exposes identical function signatures as pi_hardware.py.
"""

import sys
import requests
import numpy as np
from typing import Optional, Dict
from pathlib import Path

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def initialize() -> bool:
    """Initialize simulated backend"""
    print(f"{Colors.CYAN}→ Initializing SIMULATED mode{Colors.RESET}")
    
    # Check DeepFace installation
    try:
        import deepface
        print(f"{Colors.GREEN}✓ DeepFace available{Colors.RESET}")
        return True
    except ImportError:
        print(f"{Colors.YELLOW}⚠ DeepFace not installed{Colors.RESET}")
        response = input(f"{Colors.CYAN}Install DeepFace? [y/n]: {Colors.RESET}").lower()
        if response == 'y':
            return install_deepface()
        return False

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

def read_rfid() -> Optional[str]:
    """Read RFID tag via user input (simulation)"""
    rfid = input(f"\n{Colors.CYAN}Enter RFID tag (or 'q' to quit): {Colors.RESET}").strip()
    if rfid.lower() == 'q':
        return None
    return rfid

def capture_student_photo(config: Dict, student_id: str, script_dir: Path) -> Optional[str]:
    """
    Simulate photo capture by fetching student's photo from backend.
    In simulation mode, we fetch the stored profile photo.
    """
    print(f"{Colors.BLUE}→ [SIM] Fetching student photo from backend...{Colors.RESET}")
    
    try:
        # Call API to get photo URL
        url = f"{config['backend_url']}/api/students/{student_id}/photo"
        headers = {"X-API-Key": config['api_key']}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"{Colors.RED}   ✗ Failed to fetch photo: {response.text}{Colors.RESET}")
            return None
        
        data = response.json()
        photo_url = data.get('photo_url')
        
        if not photo_url:
            print(f"{Colors.RED}   ✗ No photo available{Colors.RESET}")
            return None
        
        # Download photo
        full_url = f"{config['backend_url']}{photo_url}"
        photo_response = requests.get(full_url, timeout=10)
        photo_response.raise_for_status()
        
        # Save to temp directory
        temp_dir = script_dir / "temp_photos"
        temp_dir.mkdir(exist_ok=True)
        
        photo_path = temp_dir / f"{student_id}_profile.jpg"
        with open(photo_path, 'wb') as f:
            f.write(photo_response.content)
        
        print(f"{Colors.GREEN}   ✓ Photo downloaded{Colors.RESET}")
        return str(photo_path)
        
    except Exception as e:
        print(f"{Colors.RED}   ✗ Error: {e}{Colors.RESET}")
        return None

def generate_face_embedding(photo_path: str) -> Optional[np.ndarray]:
    """Generate face embedding using DeepFace"""
    try:
        from deepface import DeepFace
        
        print(f"{Colors.BLUE}→ [SIM] Generating face embedding...{Colors.RESET}")
        
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
        print(f"{Colors.BLUE}→ [SIM] Sending packet to backend...{Colors.RESET}")
        
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
    """Cleanup simulated resources"""
    print(f"{Colors.CYAN}→ [SIM] Cleanup complete{Colors.RESET}")
