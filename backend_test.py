import requests
import sys
from datetime import datetime
import json
import random

class SchoolBusTrackerAPITester:
    def __init__(self, base_url="https://dashtest-auto.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.current_user = None
        self.test_results = []
        self.critical_failures = []
        self.student_ids = []
        self.bus_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, critical=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params)
            elif method == 'POST':
                response = self.session.post(url, json=data, params=params)
            elif method == 'PUT':
                response = self.session.put(url, json=data)
            elif method == 'DELETE':
                response = self.session.delete(url)

            success = response.status_code == expected_status
            
            result = {
                'name': name,
                'method': method,
                'endpoint': endpoint,
                'expected_status': expected_status,
                'actual_status': response.status_code,
                'success': success,
                'critical': critical
            }
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    result['response'] = response_data
                    self.test_results.append(result)
                    return True, response_data
                except:
                    result['response'] = {}
                    self.test_results.append(result)
                    return True, {}
            else:
                self.tests_failed += 1
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Response: {error_data}")
                    result['error'] = error_data
                except:
                    error_text = response.text
                    print(f"   Response: {error_text}")
                    result['error'] = error_text
                
                if critical:
                    self.critical_failures.append(result)
                
                self.test_results.append(result)
                return False, {}

        except Exception as e:
            self.tests_failed += 1
            error_msg = str(e)
            print(f"❌ Failed - Error: {error_msg}")
            
            result = {
                'name': name,
                'method': method,
                'endpoint': endpoint,
                'expected_status': expected_status,
                'actual_status': 'ERROR',
                'success': False,
                'critical': critical,
                'error': error_msg
            }
            
            if critical:
                self.critical_failures.append(result)
            
            self.test_results.append(result)
            return False, {}

    def test_login(self, email, password):
        """Test login functionality"""
        success, response = self.run_test(
            f"Login as {email}",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password},
            critical=True
        )
        if success:
            self.current_user = response
            print(f"   Logged in as: {response.get('name')} ({response.get('role')})")
            return True
        return False

    def test_logout(self):
        """Test logout functionality"""
        success, _ = self.run_test(
            "Logout",
            "POST", 
            "auth/logout",
            200,
            critical=True
        )
        if success:
            self.current_user = None
        return success

    def test_get_me(self):
        """Test get current user"""
        return self.run_test(
            "Get current user",
            "GET",
            "auth/me", 
            200,
            critical=True
        )

    def test_invalid_login(self):
        """Test invalid credentials"""
        success, _ = self.run_test(
            "Invalid login credentials",
            "POST",
            "auth/login",
            401,
            data={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        return success

    def test_scan_event(self, student_id=None, verified=True):
        """Test scan event endpoint"""
        if not student_id and self.student_ids:
            student_id = self.student_ids[0]
        elif not student_id:
            student_id = "test-student-id"
            
        scan_data = {
            "student_id": student_id,
            "tag_id": f"RFID-{random.randint(1000, 9999)}",
            "verified": verified,
            "confidence": 0.95 if verified else 0.65,
            "lat": 37.7749 + random.uniform(-0.01, 0.01),
            "lon": -122.4194 + random.uniform(-0.01, 0.01)
        }
        return self.run_test(
            f"Create scan event (verified={verified})",
            "POST",
            "scan_event",
            200,
            data=scan_data,
            critical=True
        )

    def test_update_location(self, bus_id=None):
        """Test bus location update"""
        if not bus_id and self.bus_ids:
            bus_id = self.bus_ids[0]
        elif not bus_id:
            bus_id = "BUS-001"
            
        location_data = {
            "bus_id": bus_id,
            "lat": 37.7749 + random.uniform(-0.01, 0.01),
            "lon": -122.4194 + random.uniform(-0.01, 0.01)
        }
        return self.run_test(
            "Update bus location",
            "POST",
            "update_location",
            200,
            data=location_data,
            critical=True
        )

    def test_get_bus_location(self, bus_id=None):
        """Test get bus location"""
        if not bus_id and self.bus_ids:
            bus_id = self.bus_ids[0]
        elif not bus_id:
            bus_id = "BUS-001"
            
        return self.run_test(
            "Get bus location",
            "GET",
            "get_bus_location",
            200,
            params={"bus_id": bus_id},
            critical=True
        )

    def test_get_attendance(self, student_id=None):
        """Test get attendance"""
        if not student_id and self.student_ids:
            student_id = self.student_ids[0]
        elif not student_id:
            student_id = "test-student-id"
            
        return self.run_test(
            "Get attendance",
            "GET",
            "get_attendance",
            200,
            params={"student_id": student_id, "month": "2025-01"},
            critical=True
        )

    def test_get_notifications(self):
        """Test get notifications"""
        return self.run_test(
            "Get notifications",
            "GET",
            "get_notifications",
            200,
            critical=True
        )

    def test_admin_endpoints(self):
        """Test admin-specific endpoints"""
        results = []
        
        # Get all students (admin view)
        success, students_data = self.run_test("Admin - Get all students", "GET", "students", 200, critical=True)
        results.append(success)
        if success and students_data:
            self.student_ids = [s['student_id'] for s in students_data[:3]]
        
        # Get users
        success, _ = self.run_test("Admin - Get users", "GET", "users", 200, critical=True)
        results.append(success)
        
        # Get holidays
        success, _ = self.run_test("Admin - Get holidays", "GET", "admin/holidays", 200, critical=True)
        results.append(success)
        
        # Get buses
        success, buses_data = self.run_test("Admin - Get buses", "GET", "buses", 200, critical=True)
        results.append(success)
        if success and buses_data:
            self.bus_ids = [b['bus_id'] for b in buses_data[:2]]
        
        # Get routes
        success, _ = self.run_test("Admin - Get routes", "GET", "routes", 200)
        results.append(success)
        
        # Get stops
        success, _ = self.run_test("Admin - Get stops", "GET", "stops", 200)
        results.append(success)
        
        # Get email logs
        success, _ = self.run_test("Admin - Get email logs", "GET", "email_logs", 200)
        results.append(success)
        
        return all(results)

    def test_teacher_endpoints(self):
        """Test teacher-specific endpoints"""
        success, students_data = self.run_test(
            "Teacher - Get assigned students",
            "GET",
            "teacher/students",
            200,
            critical=True
        )
        
        if success and students_data:
            print(f"   Teacher has {len(students_data)} assigned students")
            for student in students_data[:2]:
                print(f"   - {student.get('name')}: AM={student.get('am_status')}, PM={student.get('pm_status')}")
        
        return success

    def test_parent_endpoints(self):
        """Test parent-specific endpoints"""
        success, students_data = self.run_test(
            "Parent - Get children",
            "GET",
            "parent/students",
            200,
            critical=True
        )
        
        if success and students_data:
            print(f"   Parent has {len(students_data)} children")
            for student in students_data:
                print(f"   - {student.get('name')} (Bus: {student.get('bus_id', 'N/A')})")
        
        return success

    def test_role_based_access_control(self):
        """Test role-based access control"""
        results = []
        
        # Parent trying to access admin endpoint (should fail)
        success, _ = self.run_test(
            "Parent accessing admin endpoint (should fail)",
            "GET",
            "users",
            403
        )
        results.append(success)
        
        # Parent trying to access teacher endpoint (should fail)
        success, _ = self.run_test(
            "Parent accessing teacher endpoint (should fail)",
            "GET",
            "teacher/students",
            403
        )
        results.append(success)
        
        return all(results)

    def test_demo_endpoints(self):
        """Test demo simulation endpoints"""
        results = []
        
        # Simulate scan
        success, scan_result = self.run_test("Demo - Simulate scan", "POST", "demo/simulate_scan", 200)
        results.append(success)
        if success and scan_result:
            print(f"   Simulated scan for: {scan_result.get('student_name')} (verified: {scan_result.get('verified')})")
        
        # Simulate bus movement
        bus_id = self.bus_ids[0] if self.bus_ids else "BUS-001"
        success, _ = self.run_test(
            "Demo - Simulate bus movement", 
            "POST", 
            "demo/simulate_bus_movement",
            200,
            params={"bus_id": bus_id}
        )
        results.append(success)
        
        return all(results)

    def test_student_crud(self):
        """Test student CRUD operations (admin only)"""
        results = []
        
        if not self.student_ids:
            print("   No student IDs available for testing")
            return False
        
        student_id = self.student_ids[0]
        
        # Get specific student
        success, student_data = self.run_test(
            f"Get student details",
            "GET",
            f"students/{student_id}",
            200,
            critical=True
        )
        results.append(success)
        
        if success and student_data:
            print(f"   Student: {student_data.get('name')} - Parent: {student_data.get('parent_name')} - Teacher: {student_data.get('teacher_name')}")
        
        # Update student (admin can update)
        update_data = {
            "remarks": f"Updated by test at {datetime.now().isoformat()}"
        }
        success, _ = self.run_test(
            "Update student (admin)",
            "PUT",
            f"students/{student_id}",
            200,
            data=update_data
        )
        results.append(success)
        
        return all(results)

def main():
    print("🚌 School Bus Tracker API Testing")
    print("=" * 50)
    
    tester = SchoolBusTrackerAPITester()
    
    # Test credentials from the review request
    test_accounts = [
        ("parent@school.com", "password", "parent"),
        ("teacher@school.com", "password", "teacher"), 
        ("admin@school.com", "password", "admin")
    ]
    
    all_tests_passed = True
    
    for email, password, role in test_accounts:
        print(f"\n🔐 Testing {role.upper()} role ({email})")
        print("-" * 40)
        
        # Test login
        if not tester.test_login(email, password):
            print(f"❌ Login failed for {role}")
            all_tests_passed = False
            continue
            
        # Test get me
        success, user_data = tester.test_get_me()
        if not success:
            print(f"❌ Get user info failed for {role}")
            all_tests_passed = False
            continue
            
        # Role-specific tests
        if role == "admin":
            if not tester.test_admin_endpoints():
                print(f"❌ Admin endpoints failed")
                all_tests_passed = False
        elif role == "teacher":
            if not tester.test_teacher_endpoints():
                print(f"❌ Teacher endpoints failed")
                all_tests_passed = False
        elif role == "parent":
            if not tester.test_parent_endpoints():
                print(f"❌ Parent endpoints failed")
                all_tests_passed = False
        
        # Test logout
        if not tester.test_logout():
            print(f"❌ Logout failed for {role}")
            all_tests_passed = False
    
    # Test core functionality (without auth for some endpoints)
    print(f"\n🔧 Testing Core Functionality")
    print("-" * 40)
    
    # Login as admin for core tests
    if tester.test_login("admin@school.com", "password"):
        
        # Test scan event
        success, _ = tester.test_scan_event()
        if not success:
            all_tests_passed = False
            
        # Test location update
        success, _ = tester.test_update_location()
        if not success:
            all_tests_passed = False
            
        # Test get bus location
        success, _ = tester.test_get_bus_location()
        if not success:
            all_tests_passed = False
            
        # Test get attendance
        success, _ = tester.test_get_attendance()
        if not success:
            all_tests_passed = False
            
        # Test notifications
        success, _ = tester.test_get_notifications()
        if not success:
            all_tests_passed = False
            
        # Test demo endpoints
        if not tester.test_demo_endpoints():
            all_tests_passed = False
    
    # Print final results
    print(f"\n📊 Final Results")
    print("=" * 50)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    if all_tests_passed and success_rate >= 90:
        print("✅ All critical tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())