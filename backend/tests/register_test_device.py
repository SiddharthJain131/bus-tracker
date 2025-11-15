#!/usr/bin/env python3
"""
Register a test device for Pi script testing
"""

import json
import requests
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "pi_device_config.json"

def register_device():
    """Register device with admin credentials"""
    
    backend_url = "http://localhost:8001"
    bus_number = "BUS-001"
    device_name = "pi-test-device"
    
    # Admin credentials from seed data
    admin_email = "admin@school.com"
    admin_password = "password"
    
    # Step 1: Login as admin
    print("→ Logging in as admin...")
    login_response = requests.post(
        f"{backend_url}/api/auth/login",
        json={"email": admin_email, "password": admin_password}
    )
    
    if login_response.status_code != 200:
        print(f"✗ Login failed: {login_response.text}")
        return False
    
    session_cookie = login_response.cookies.get('session_token')
    if not session_cookie:
        print("✗ No session token received")
        return False
    
    print("✓ Admin authenticated")
    
    # Step 2: Register device
    print("→ Registering device...")
    register_response = requests.post(
        f"{backend_url}/api/device/register",
        json={"bus_number": bus_number, "device_name": device_name},
        cookies={"session_token": session_cookie}
    )
    
    if register_response.status_code != 200:
        print(f"✗ Registration failed: {register_response.text}")
        return False
    
    device_data = register_response.json()
    print("✓ Device registered successfully!")
    print(f"  Device ID: {device_data['device_id']}")
    print(f"  Bus: {device_data.get('bus_number', bus_number)}")
    print(f"  API Key: {device_data['api_key']}")
    
    # Step 3: Save config
    config = {
        "backend_url": backend_url,
        "device_id": device_data['device_id'],
        "device_name": device_name,
        "bus_number": bus_number,
        "api_key": device_data['api_key'],
        "registered_at": datetime.now(timezone.utc).isoformat()
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Configuration saved to {CONFIG_FILE}")
    
    return True

if __name__ == "__main__":
    success = register_device()
    exit(0 if success else 1)
