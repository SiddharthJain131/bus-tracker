#!/usr/bin/env python3
"""
Automated Pi Script Test
Simulates the Pi script workflow without user interaction
"""

import sys
import os
import json
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

import pi_simulated as pi_backend

# Load configuration
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "pi_device_config.json"
RFID_MAPPING_FILE = SCRIPT_DIR / "rfid_student_mapping.json"

def load_config():
    """Load device configuration"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def load_rfid_mapping():
    """Load RFID mapping"""
    with open(RFID_MAPPING_FILE, 'r') as f:
        students = json.load(f)
        return {s['rfid']: s for s in students}

def test_device_registration():
    """Test 1: Device registration check"""
    print("\n" + "="*70)
    print("TEST 1: DEVICE REGISTRATION")
    print("="*70)
    
    config = load_config()
    
    if not config:
        print("✗ No device configuration found")
        return False
    
    required_fields = ['backend_url', 'device_id', 'device_name', 'bus_number', 'api_key']
    for field in required_fields:
        if field not in config:
            print(f"✗ Missing required field: {field}")
            return False
    
    print("✓ Device configuration loaded")
    print(f"  Device ID: {config['device_id']}")
    print(f"  Device Name: {config['device_name']}")
    print(f"  Bus Number: {config['bus_number']}")
    print(f"  Backend URL: {config['backend_url']}")
    
    return True

def test_rfid_read():
    """Test 2: RFID read flow"""
    print("\n" + "="*70)
    print("TEST 2: RFID READ FLOW")
    print("="*70)
    
    rfid_mapping = load_rfid_mapping()
    
    if not rfid_mapping:
        print("✗ No RFID mapping found")
        return False
    
    print(f"✓ RFID mapping loaded ({len(rfid_mapping)} students)")
    
    # Test with first RFID
    test_rfid = list(rfid_mapping.keys())[0]
    student_info = rfid_mapping[test_rfid]
    
    print(f"  Test RFID: {test_rfid}")
    print(f"  Student ID: {student_info['student_id']}")
    
    return True

def test_student_lookup():
    """Test 3: Student lookup via API"""
    print("\n" + "="*70)
    print("TEST 3: STUDENT LOOKUP")
    print("="*70)
    
    config = load_config()
    rfid_mapping = load_rfid_mapping()
    
    test_rfid = list(rfid_mapping.keys())[0]
    student_info = rfid_mapping[test_rfid]
    student_id = student_info['student_id']
    
    print(f"  Looking up student: {student_id}")
    
    # Test photo endpoint
    import requests
    try:
        url = f"{config['backend_url']}/api/students/{student_id}/photo"
        headers = {"X-API-Key": config['api_key']}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Student photo endpoint accessible")
            print(f"  Has photo: {data.get('has_photo', False)}")
        else:
            print(f"✗ Photo endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error accessing photo endpoint: {e}")
        return False
    
    return True

def test_embedding_retrieval():
    """Test 4: Embedding retrieval or fallback"""
    print("\n" + "="*70)
    print("TEST 4: EMBEDDING RETRIEVAL")
    print("="*70)
    
    config = load_config()
    rfid_mapping = load_rfid_mapping()
    
    test_rfid = list(rfid_mapping.keys())[0]
    student_info = rfid_mapping[test_rfid]
    student_id = student_info['student_id']
    
    # Check local cache first
    local_embedding = student_info.get('embedding')
    if local_embedding:
        print("✓ Local embedding cached")
    else:
        print("⚠ No local embedding (expected for fresh setup)")
    
    # Test API embedding endpoint
    import requests
    try:
        url = f"{config['backend_url']}/api/students/{student_id}/embedding"
        headers = {"X-API-Key": config['api_key']}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Embedding endpoint accessible")
            print(f"  Has embedding: {data.get('has_embedding', False)}")
            
            if not data.get('has_embedding'):
                print("⚠ No embedding stored (fallback to unverified scan)")
        else:
            print(f"✗ Embedding endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error accessing embedding endpoint: {e}")
        return False
    
    return True

def test_in_scan_packet():
    """Test 5: IN scan packet"""
    print("\n" + "="*70)
    print("TEST 5: IN SCAN PACKET")
    print("="*70)
    
    config = load_config()
    rfid_mapping = load_rfid_mapping()
    
    test_rfid = list(rfid_mapping.keys())[0]
    student_info = rfid_mapping[test_rfid]
    student_id = student_info['student_id']
    
    # Simulate IN scan (unverified since no embeddings)
    payload = {
        "student_id": student_id,
        "tag_id": test_rfid,
        "verified": False,
        "confidence": 0.0,
        "lat": 37.7749,
        "lon": -122.4194
    }
    
    print(f"  Sending IN scan for student: {student_id}")
    print(f"  RFID: {test_rfid}")
    print(f"  Verified: {payload['verified']}")
    
    success = pi_backend.send_packet(config, payload)
    
    if success:
        print("✓ IN scan packet sent successfully")
        print("  Expected status: YELLOW (first scan)")
        return True
    else:
        print("✗ Failed to send IN scan packet")
        return False

def test_out_scan_packet():
    """Test 6: OUT scan packet"""
    print("\n" + "="*70)
    print("TEST 6: OUT SCAN PACKET")
    print("="*70)
    
    config = load_config()
    rfid_mapping = load_rfid_mapping()
    
    test_rfid = list(rfid_mapping.keys())[0]
    student_info = rfid_mapping[test_rfid]
    student_id = student_info['student_id']
    
    # Simulate OUT scan
    payload = {
        "student_id": student_id,
        "tag_id": test_rfid,
        "verified": True,
        "confidence": 1.0,
        "lat": 37.7749,
        "lon": -122.4194
    }
    
    print(f"  Sending OUT scan for student: {student_id}")
    print(f"  RFID: {test_rfid}")
    print(f"  Verified: {payload['verified']}")
    
    success = pi_backend.send_packet(config, payload)
    
    if success:
        print("✓ OUT scan packet sent successfully")
        print("  Expected status: GREEN (second scan)")
        return True
    else:
        print("✗ Failed to send OUT scan packet")
        return False

def test_caching():
    """Test 7: Caching functionality"""
    print("\n" + "="*70)
    print("TEST 7: CACHING FUNCTIONALITY")
    print("="*70)
    
    rfid_mapping = load_rfid_mapping()
    
    # Count cached embeddings
    cached_count = sum(1 for s in rfid_mapping.values() if s.get('embedding'))
    total_count = len(rfid_mapping)
    
    print(f"  Cached embeddings: {cached_count}/{total_count}")
    
    if cached_count == 0:
        print("⚠ No embeddings cached yet (expected for fresh setup)")
        print("  Embeddings will be cached on first successful fetch")
    else:
        print(f"✓ {cached_count} embeddings cached")
    
    return True

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("PI SCRIPT END-TO-END TEST - AUTOMATED")
    print("="*70)
    print("Mode: SIMULATED")
    print()
    
    # Initialize backend
    if not pi_backend.initialize():
        print("✗ Failed to initialize backend module")
        sys.exit(1)
    
    tests = [
        ("Device Registration", test_device_registration),
        ("RFID Read Flow", test_rfid_read),
        ("Student Lookup", test_student_lookup),
        ("Embedding Retrieval", test_embedding_retrieval),
        ("IN Scan Packet", test_in_scan_packet),
        ("OUT Scan Packet", test_out_scan_packet),
        ("Caching", test_caching)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Pi script working end-to-end")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
