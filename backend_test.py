#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Device API Key System
Bus Tracker - Raspberry Pi Authentication Testing

This script tests the new Device API Key System implementation for secure
Raspberry Pi device authentication and API access.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://user-photo-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class DeviceAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_cookies = None
        self.teacher_cookies = None
        self.api_key = None
        self.device_id = None
        self.bus_id = None
        self.student_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, details="", expected="", actual=""):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and expected:
            print(f"    Expected: {expected}")
            print(f"    Actual: {actual}")
        print()

    def admin_login(self):
        """Login as admin to get session cookies"""
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "email": "admin@school.com",
                "password": "password"
            })
            
            if response.status_code == 200:
                self.admin_cookies = self.session.cookies
                data = response.json()
                self.log_result("Admin Login", True, f"Logged in as {data.get('name')} ({data.get('role')})")
                return True
            else:
                self.log_result("Admin Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_result("Admin Login", False, f"Exception: {str(e)}")
            return False

    def teacher_login(self):
        """Login as teacher for non-admin access tests"""
        try:
            teacher_session = requests.Session()
            response = teacher_session.post(f"{API_BASE}/auth/login", json={
                "email": "teacher@school.com",
                "password": "password"
            })
            
            if response.status_code == 200:
                self.teacher_cookies = teacher_session.cookies
                data = response.json()
                self.log_result("Teacher Login", True, f"Logged in as {data.get('name')} ({data.get('role')})")
                return teacher_session
            else:
                self.log_result("Teacher Login", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_result("Teacher Login", False, f"Exception: {str(e)}")
            return None

    def get_seed_data(self):
        """Get bus and student IDs from seed data"""
        try:
            # Get buses
            response = self.session.get(f"{API_BASE}/buses")
            if response.status_code == 200:
                buses = response.json()
                if buses:
                    self.bus_id = buses[0]['bus_id']  # Use first bus (BUS-001)
                    self.log_result("Get Seed Bus Data", True, f"Using bus_id: {self.bus_id}")
                else:
                    self.log_result("Get Seed Bus Data", False, "No buses found in seed data")
                    return False
            else:
                self.log_result("Get Seed Bus Data", False, f"Status: {response.status_code}")
                return False

            # Get students
            response = self.session.get(f"{API_BASE}/students")
            if response.status_code == 200:
                students = response.json()
                if students:
                    self.student_id = students[0]['student_id']  # Use first student
                    self.log_result("Get Seed Student Data", True, f"Using student_id: {self.student_id}")
                else:
                    self.log_result("Get Seed Student Data", False, "No students found in seed data")
                    return False
            else:
                self.log_result("Get Seed Student Data", False, f"Status: {response.status_code}")
                return False
                
            return True
        except Exception as e:
            self.log_result("Get Seed Data", False, f"Exception: {str(e)}")
            return False

    def test_device_registration_admin(self):
        """SCENARIO A.1 - Register Device (Admin)"""
        try:
            payload = {
                "bus_id": self.bus_id,
                "device_name": "Raspberry Pi - Bus 001"
            }
            
            response = self.session.post(f"{API_BASE}/device/register", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['device_id', 'bus_id', 'bus_number', 'device_name', 'api_key', 'warning']
                
                if all(field in data for field in required_fields):
                    self.api_key = data['api_key']
                    self.device_id = data['device_id']
                    
                    # Verify API key is 64 characters
                    if len(self.api_key) == 64:
                        self.log_result("A.1 - Register Device (Admin)", True, 
                                      f"Device registered successfully. API key length: {len(self.api_key)} chars")
                        return True
                    else:
                        self.log_result("A.1 - Register Device (Admin)", False, 
                                      f"API key length incorrect: {len(self.api_key)} (expected 64)")
                        return False
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("A.1 - Register Device (Admin)", False, 
                                  f"Missing fields: {missing}")
                    return False
            else:
                self.log_result("A.1 - Register Device (Admin)", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_result("A.1 - Register Device (Admin)", False, f"Exception: {str(e)}")
            return False

    def test_duplicate_device_prevention(self):
        """SCENARIO A.2 - Duplicate Device Prevention"""
        try:
            payload = {
                "bus_id": self.bus_id,
                "device_name": "Another Raspberry Pi"
            }
            
            response = self.session.post(f"{API_BASE}/device/register", json=payload)
            
            if response.status_code == 400:
                self.log_result("A.2 - Duplicate Device Prevention", True, 
                              "Correctly prevented duplicate device registration")
                return True
            else:
                self.log_result("A.2 - Duplicate Device Prevention", False, 
                              f"Expected 400, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("A.2 - Duplicate Device Prevention", False, f"Exception: {str(e)}")
            return False

    def test_non_admin_device_registration(self):
        """SCENARIO A.3 - Non-Admin Access"""
        try:
            teacher_session = self.teacher_login()
            if not teacher_session:
                return False
                
            payload = {
                "bus_id": self.bus_id,
                "device_name": "Unauthorized Device"
            }
            
            response = teacher_session.post(f"{API_BASE}/device/register", json=payload)
            
            if response.status_code == 403:
                self.log_result("A.3 - Non-Admin Access", True, 
                              "Correctly denied non-admin device registration")
                return True
            else:
                self.log_result("A.3 - Non-Admin Access", False, 
                              f"Expected 403, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("A.3 - Non-Admin Access", False, f"Exception: {str(e)}")
            return False

    def test_list_devices_admin(self):
        """SCENARIO A.4 - List Devices (Admin)"""
        try:
            response = self.session.get(f"{API_BASE}/device/list")
            
            if response.status_code == 200:
                devices = response.json()
                if isinstance(devices, list) and len(devices) > 0:
                    device = devices[0]
                    # Verify key_hash is not included
                    if 'key_hash' not in device and 'bus_number' in device:
                        self.log_result("A.4 - List Devices (Admin)", True, 
                                      f"Retrieved {len(devices)} device(s) without key_hash")
                        return True
                    else:
                        self.log_result("A.4 - List Devices (Admin)", False, 
                                      "key_hash field present or bus_number missing")
                        return False
                else:
                    self.log_result("A.4 - List Devices (Admin)", False, 
                                  "No devices returned or invalid format")
                    return False
            else:
                self.log_result("A.4 - List Devices (Admin)", False, 
                              f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("A.4 - List Devices (Admin)", False, f"Exception: {str(e)}")
            return False

    def test_list_devices_non_admin(self):
        """SCENARIO A.5 - List Devices (Non-Admin)"""
        try:
            teacher_session = self.teacher_login()
            if not teacher_session:
                return False
                
            response = teacher_session.get(f"{API_BASE}/device/list")
            
            if response.status_code == 403:
                self.log_result("A.5 - List Devices (Non-Admin)", True, 
                              "Correctly denied non-admin device list access")
                return True
            else:
                self.log_result("A.5 - List Devices (Non-Admin)", False, 
                              f"Expected 403, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("A.5 - List Devices (Non-Admin)", False, f"Exception: {str(e)}")
            return False

    def test_scan_event_valid_key_yellow(self):
        """SCENARIO B.1 - Scan Event with Valid API Key (Yellow Status)"""
        try:
            headers = {"X-API-Key": self.api_key}
            payload = {
                "student_id": self.student_id,
                "tag_id": "RFID-TEST-001",
                "verified": True,
                "confidence": 0.95,
                "lat": 40.7128,
                "lon": -74.0060,
                "scan_type": "yellow"
            }
            
            response = requests.post(f"{API_BASE}/scan_event", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' and data.get('attendance_status') == 'yellow':
                    self.log_result("B.1 - Scan Event Valid Key (Yellow)", True, 
                                  f"Yellow scan recorded successfully: {data.get('event_id')}")
                    return True
                else:
                    self.log_result("B.1 - Scan Event Valid Key (Yellow)", False, 
                                  f"Unexpected response: {data}")
                    return False
            else:
                self.log_result("B.1 - Scan Event Valid Key (Yellow)", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_result("B.1 - Scan Event Valid Key (Yellow)", False, f"Exception: {str(e)}")
            return False

    def test_scan_event_valid_key_green(self):
        """SCENARIO B.2 - Scan Event with Valid API Key (Green Status)"""
        try:
            headers = {"X-API-Key": self.api_key}
            payload = {
                "student_id": self.student_id,
                "tag_id": "RFID-TEST-002",
                "verified": True,
                "confidence": 0.92,
                "lat": 40.7128,
                "lon": -74.0060,
                "scan_type": "green"
            }
            
            response = requests.post(f"{API_BASE}/scan_event", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' and data.get('attendance_status') == 'green':
                    self.log_result("B.2 - Scan Event Valid Key (Green)", True, 
                                  f"Green scan recorded successfully: {data.get('event_id')}")
                    return True
                else:
                    self.log_result("B.2 - Scan Event Valid Key (Green)", False, 
                                  f"Unexpected response: {data}")
                    return False
            else:
                self.log_result("B.2 - Scan Event Valid Key (Green)", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_result("B.2 - Scan Event Valid Key (Green)", False, f"Exception: {str(e)}")
            return False

    def test_scan_event_no_key(self):
        """SCENARIO B.3 - Scan Event without API Key"""
        try:
            payload = {
                "student_id": self.student_id,
                "tag_id": "RFID-TEST-003",
                "verified": True,
                "confidence": 0.90,
                "lat": 40.7128,
                "lon": -74.0060,
                "scan_type": "yellow"
            }
            
            response = requests.post(f"{API_BASE}/scan_event", json=payload)
            
            if response.status_code in [403, 422]:
                self.log_result("B.3 - Scan Event No Key", True, 
                              f"Correctly rejected request without API key (Status: {response.status_code})")
                return True
            else:
                self.log_result("B.3 - Scan Event No Key", False, 
                              f"Expected 403/422, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("B.3 - Scan Event No Key", False, f"Exception: {str(e)}")
            return False

    def test_scan_event_invalid_key(self):
        """SCENARIO B.4 - Scan Event with Invalid API Key"""
        try:
            headers = {"X-API-Key": "invalid_fake_key_12345"}
            payload = {
                "student_id": self.student_id,
                "tag_id": "RFID-TEST-004",
                "verified": True,
                "confidence": 0.88,
                "lat": 40.7128,
                "lon": -74.0060,
                "scan_type": "yellow"
            }
            
            response = requests.post(f"{API_BASE}/scan_event", json=payload, headers=headers)
            
            if response.status_code == 403:
                self.log_result("B.4 - Scan Event Invalid Key", True, 
                              "Correctly rejected invalid API key")
                return True
            else:
                self.log_result("B.4 - Scan Event Invalid Key", False, 
                              f"Expected 403, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("B.4 - Scan Event Invalid Key", False, f"Exception: {str(e)}")
            return False

    def test_update_location_valid_key(self):
        """SCENARIO C.1 - Update Location with Valid API Key"""
        try:
            headers = {"X-API-Key": self.api_key}
            payload = {
                "bus_id": self.bus_id,
                "lat": 40.7589,
                "lon": -73.9851
            }
            
            response = requests.post(f"{API_BASE}/update_location", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' and 'timestamp' in data:
                    self.log_result("C.1 - Update Location Valid Key", True, 
                                  f"Location updated successfully at {data.get('timestamp')}")
                    return True
                else:
                    self.log_result("C.1 - Update Location Valid Key", False, 
                                  f"Unexpected response: {data}")
                    return False
            else:
                self.log_result("C.1 - Update Location Valid Key", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_result("C.1 - Update Location Valid Key", False, f"Exception: {str(e)}")
            return False

    def test_update_location_wrong_bus(self):
        """SCENARIO C.2 - Update Location for Wrong Bus"""
        try:
            # Get a different bus_id
            response = self.session.get(f"{API_BASE}/buses")
            buses = response.json()
            different_bus_id = None
            for bus in buses:
                if bus['bus_id'] != self.bus_id:
                    different_bus_id = bus['bus_id']
                    break
            
            if not different_bus_id:
                self.log_result("C.2 - Update Location Wrong Bus", False, 
                              "Could not find different bus for test")
                return False
            
            headers = {"X-API-Key": self.api_key}
            payload = {
                "bus_id": different_bus_id,
                "lat": 40.7589,
                "lon": -73.9851
            }
            
            response = requests.post(f"{API_BASE}/update_location", json=payload, headers=headers)
            
            if response.status_code == 403:
                self.log_result("C.2 - Update Location Wrong Bus", True, 
                              "Correctly rejected unauthorized bus access")
                return True
            else:
                self.log_result("C.2 - Update Location Wrong Bus", False, 
                              f"Expected 403, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("C.2 - Update Location Wrong Bus", False, f"Exception: {str(e)}")
            return False

    def test_update_location_no_key(self):
        """SCENARIO C.3 - Update Location without API Key"""
        try:
            payload = {
                "bus_id": self.bus_id,
                "lat": 40.7589,
                "lon": -73.9851
            }
            
            response = requests.post(f"{API_BASE}/update_location", json=payload)
            
            if response.status_code in [403, 422]:
                self.log_result("C.3 - Update Location No Key", True, 
                              f"Correctly rejected request without API key (Status: {response.status_code})")
                return True
            else:
                self.log_result("C.3 - Update Location No Key", False, 
                              f"Expected 403/422, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("C.3 - Update Location No Key", False, f"Exception: {str(e)}")
            return False

    def test_get_bus_location_valid_key(self):
        """SCENARIO D.1 - Get Bus Location with Valid API Key"""
        try:
            headers = {"X-API-Key": self.api_key}
            
            response = requests.get(f"{API_BASE}/get_bus_location?bus_id={self.bus_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['bus_id', 'lat', 'lon', 'timestamp']
                if all(field in data for field in required_fields):
                    self.log_result("D.1 - Get Bus Location Valid Key", True, 
                                  f"Bus location retrieved: lat={data.get('lat')}, lon={data.get('lon')}")
                    return True
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("D.1 - Get Bus Location Valid Key", False, 
                                  f"Missing fields: {missing}")
                    return False
            else:
                self.log_result("D.1 - Get Bus Location Valid Key", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_result("D.1 - Get Bus Location Valid Key", False, f"Exception: {str(e)}")
            return False

    def test_get_bus_location_no_key(self):
        """SCENARIO D.2 - Get Bus Location without API Key"""
        try:
            response = requests.get(f"{API_BASE}/get_bus_location?bus_id={self.bus_id}")
            
            if response.status_code in [403, 422]:
                self.log_result("D.2 - Get Bus Location No Key", True, 
                              f"Correctly rejected request without API key (Status: {response.status_code})")
                return True
            else:
                self.log_result("D.2 - Get Bus Location No Key", False, 
                              f"Expected 403/422, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("D.2 - Get Bus Location No Key", False, f"Exception: {str(e)}")
            return False

    def test_get_student_embedding_valid_key(self):
        """SCENARIO E.1 - Get Student Embedding with Valid API Key"""
        try:
            headers = {"X-API-Key": self.api_key}
            
            response = requests.get(f"{API_BASE}/students/{self.student_id}/embedding", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['student_id', 'name', 'embedding', 'has_embedding']
                if all(field in data for field in required_fields):
                    self.log_result("E.1 - Get Student Embedding Valid Key", True, 
                                  f"Student embedding data retrieved: has_embedding={data.get('has_embedding')}")
                    return True
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("E.1 - Get Student Embedding Valid Key", False, 
                                  f"Missing fields: {missing}")
                    return False
            else:
                self.log_result("E.1 - Get Student Embedding Valid Key", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_result("E.1 - Get Student Embedding Valid Key", False, f"Exception: {str(e)}")
            return False

    def test_get_student_embedding_no_key(self):
        """SCENARIO E.2 - Get Student Embedding without API Key"""
        try:
            response = requests.get(f"{API_BASE}/students/{self.student_id}/embedding")
            
            if response.status_code in [403, 422]:
                self.log_result("E.2 - Get Student Embedding No Key", True, 
                              f"Correctly rejected request without API key (Status: {response.status_code})")
                return True
            else:
                self.log_result("E.2 - Get Student Embedding No Key", False, 
                              f"Expected 403/422, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("E.2 - Get Student Embedding No Key", False, f"Exception: {str(e)}")
            return False

    def test_get_student_photo_valid_key(self):
        """SCENARIO E.3 - Get Student Photo with Valid API Key"""
        try:
            headers = {"X-API-Key": self.api_key}
            
            response = requests.get(f"{API_BASE}/students/{self.student_id}/photo", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['student_id', 'name', 'photo_url', 'has_photo']
                if all(field in data for field in required_fields):
                    self.log_result("E.3 - Get Student Photo Valid Key", True, 
                                  f"Student photo data retrieved: has_photo={data.get('has_photo')}")
                    return True
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("E.3 - Get Student Photo Valid Key", False, 
                                  f"Missing fields: {missing}")
                    return False
            else:
                self.log_result("E.3 - Get Student Photo Valid Key", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_result("E.3 - Get Student Photo Valid Key", False, f"Exception: {str(e)}")
            return False

    def test_get_student_photo_no_key(self):
        """SCENARIO E.4 - Get Student Photo without API Key"""
        try:
            response = requests.get(f"{API_BASE}/students/{self.student_id}/photo")
            
            if response.status_code in [403, 422]:
                self.log_result("E.4 - Get Student Photo No Key", True, 
                              f"Correctly rejected request without API key (Status: {response.status_code})")
                return True
            else:
                self.log_result("E.4 - Get Student Photo No Key", False, 
                              f"Expected 403/422, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("E.4 - Get Student Photo No Key", False, f"Exception: {str(e)}")
            return False

    def test_get_nonexistent_student_data(self):
        """SCENARIO E.5 - Get Non-existent Student Data"""
        try:
            headers = {"X-API-Key": self.api_key}
            
            response = requests.get(f"{API_BASE}/students/invalid-student-id-999/embedding", headers=headers)
            
            if response.status_code == 404:
                self.log_result("E.5 - Get Non-existent Student Data", True, 
                              "Correctly returned 404 for non-existent student")
                return True
            else:
                self.log_result("E.5 - Get Non-existent Student Data", False, 
                              f"Expected 404, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("E.5 - Get Non-existent Student Data", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all Device API Key System tests"""
        print("=" * 80)
        print("🔐 DEVICE API KEY SYSTEM - COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print()

        # Setup phase
        print("📋 SETUP PHASE")
        print("-" * 40)
        
        if not self.admin_login():
            print("❌ Cannot proceed without admin login")
            return False
            
        if not self.get_seed_data():
            print("❌ Cannot proceed without seed data")
            return False
        
        print()
        
        # Test scenarios
        test_methods = [
            # SCENARIO A: Device Registration & Management
            ("SCENARIO A: Device Registration & Management", [
                self.test_device_registration_admin,
                self.test_duplicate_device_prevention,
                self.test_non_admin_device_registration,
                self.test_list_devices_admin,
                self.test_list_devices_non_admin
            ]),
            
            # SCENARIO B: Device Authentication - Scan Event
            ("SCENARIO B: Device Authentication - Scan Event", [
                self.test_scan_event_valid_key_yellow,
                self.test_scan_event_valid_key_green,
                self.test_scan_event_no_key,
                self.test_scan_event_invalid_key
            ]),
            
            # SCENARIO C: Device Authentication - Location Updates
            ("SCENARIO C: Device Authentication - Location Updates", [
                self.test_update_location_valid_key,
                self.test_update_location_wrong_bus,
                self.test_update_location_no_key
            ]),
            
            # SCENARIO D: Device Authentication - Get Bus Location
            ("SCENARIO D: Device Authentication - Get Bus Location", [
                self.test_get_bus_location_valid_key,
                self.test_get_bus_location_no_key
            ]),
            
            # SCENARIO E: Student Data Endpoints
            ("SCENARIO E: Student Data Endpoints (Embedding & Photo)", [
                self.test_get_student_embedding_valid_key,
                self.test_get_student_embedding_no_key,
                self.test_get_student_photo_valid_key,
                self.test_get_student_photo_no_key,
                self.test_get_nonexistent_student_data
            ])
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for scenario_name, test_list in test_methods:
            print(f"🧪 {scenario_name}")
            print("-" * 60)
            
            for test_method in test_list:
                total_tests += 1
                if test_method():
                    passed_tests += 1
            
            print()
        
        # Summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.api_key:
            print(f"\n🔑 Generated API Key: {self.api_key}")
            print("⚠️  Store this key securely - it cannot be retrieved later!")
        
        print()
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("❌ FAILED TESTS DETAILS:")
            print("-" * 40)
            for test in failed_tests:
                print(f"• {test['test']}: {test['details']}")
            print()
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    tester = DeviceAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 ALL TESTS PASSED! Device API Key System is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please review the results above.")
        sys.exit(1)

if __name__ == "__main__":
    main()