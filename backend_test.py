import requests
import sys
from datetime import datetime
import json
import random

class SchoolBusTrackerAPITester:
    def __init__(self, base_url="https://bustracker-setup.preview.emergentagent.com"):
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

    def test_enhanced_admin_dashboard(self):
        """Test Enhanced Admin Dashboard specific requirements"""
        results = []
        
        print(f"\n🎯 Testing Enhanced Admin Dashboard APIs...")
        
        # 1. Data Retrieval for Admin Dashboard
        print(f"   Testing data retrieval with enriched data...")
        
        # Get students with enriched data (parent_name, teacher_name, bus_number)
        success, students_data = self.run_test(
            "Admin Dashboard - Get students with enriched data", 
            "GET", "students", 200, critical=True
        )
        results.append(success)
        if success and students_data:
            # Verify enrichment fields are present
            for student in students_data[:2]:
                if 'parent_name' in student and 'teacher_name' in student and 'bus_number' in student:
                    print(f"   ✅ Student enrichment: {student['name']} - Parent: {student['parent_name']}, Teacher: {student['teacher_name']}, Bus: {student['bus_number']}")
                else:
                    print(f"   ❌ Missing enrichment fields for student: {student.get('name', 'Unknown')}")
                    results.append(False)
        
        # Get users without password_hash
        success, users_data = self.run_test(
            "Admin Dashboard - Get users (no password_hash)", 
            "GET", "users", 200, critical=True
        )
        results.append(success)
        if success and users_data:
            # Verify password_hash is excluded
            for user in users_data[:2]:
                if 'password_hash' not in user:
                    print(f"   ✅ User data secure: {user['name']} - no password_hash exposed")
                else:
                    print(f"   ❌ Security issue: password_hash exposed for {user.get('name', 'Unknown')}")
                    results.append(False)
        
        # Get buses with route_name enrichment
        success, buses_data = self.run_test(
            "Admin Dashboard - Get buses with route enrichment", 
            "GET", "buses", 200, critical=True
        )
        results.append(success)
        if success and buses_data:
            for bus in buses_data[:2]:
                if 'route_name' in bus:
                    print(f"   ✅ Bus enrichment: {bus['bus_number']} - Route: {bus['route_name']}")
                else:
                    print(f"   ❌ Missing route_name for bus: {bus.get('bus_number', 'Unknown')}")
                    results.append(False)
        
        # 2. Test detailed views for modals
        if self.student_ids:
            student_id = self.student_ids[0]
            success, student_detail = self.run_test(
                "Admin Dashboard - Get student detail for View modal", 
                "GET", f"students/{student_id}", 200, critical=True
            )
            results.append(success)
            if success and student_detail:
                required_fields = ['name', 'parent_name', 'parent_email', 'teacher_name', 'bus_number']
                missing_fields = [field for field in required_fields if field not in student_detail]
                if not missing_fields:
                    print(f"   ✅ Student detail complete for modal: {student_detail['name']}")
                else:
                    print(f"   ❌ Student detail missing fields: {missing_fields}")
                    results.append(False)
        
        if self.bus_ids:
            bus_id = self.bus_ids[0]
            success, bus_detail = self.run_test(
                "Admin Dashboard - Get bus detail for View modal", 
                "GET", f"buses/{bus_id}", 200, critical=True
            )
            results.append(success)
            if success and bus_detail:
                if 'route_data' in bus_detail:
                    print(f"   ✅ Bus detail with route data: {bus_detail['bus_number']}")
                else:
                    print(f"   ❌ Bus detail missing route_data for modal")
                    results.append(False)
        
        # 3. Test route details for map visualization
        success, routes_data = self.run_test("Admin Dashboard - Get routes", "GET", "routes", 200)
        results.append(success)
        if success and routes_data and routes_data:
            route_id = routes_data[0]['route_id']
            success, route_detail = self.run_test(
                "Admin Dashboard - Get route with stops for map", 
                "GET", f"routes/{route_id}", 200, critical=True
            )
            results.append(success)
            if success and route_detail:
                if 'stops' in route_detail and 'map_path' in route_detail:
                    print(f"   ✅ Route detail with stops and map_path: {route_detail['route_name']}")
                else:
                    print(f"   ❌ Route detail missing stops or map_path for visualization")
                    results.append(False)
        
        return all(results)

    def test_admin_edit_operations(self):
        """Test admin edit operations with email notifications"""
        results = []
        
        print(f"\n✏️  Testing Admin Edit Operations...")
        
        if not self.student_ids:
            print("   ❌ No student IDs available for edit testing")
            return False
        
        student_id = self.student_ids[0]
        
        # Get original student data
        success, original_student = self.run_test(
            "Get original student data", 
            "GET", f"students/{student_id}", 200
        )
        if not success:
            return False
        
        # Update student info (should trigger email notification)
        update_data = {
            "remarks": f"Updated by Enhanced Admin Dashboard test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        success, _ = self.run_test(
            "Admin - Update student (should trigger email)", 
            "PUT", f"students/{student_id}", 200, 
            data=update_data, critical=True
        )
        results.append(success)
        
        if success:
            print(f"   ✅ Student update successful - email notification should be sent to parent")
            
            # Check email logs to verify notification was sent
            success, email_logs = self.run_test(
                "Check email logs for student update notification", 
                "GET", "email_logs", 200
            )
            if success and email_logs:
                recent_emails = [log for log in email_logs if log.get('student_id') == student_id]
                if recent_emails:
                    print(f"   ✅ Email notification logged: {recent_emails[0]['subject']}")
                else:
                    print(f"   ⚠️  No email log found for student update (may be expected)")
        
        # Test user update
        success, users_data = self.run_test("Get users for edit test", "GET", "users", 200)
        if success and users_data:
            # Find a non-admin user to update
            non_admin_user = next((u for u in users_data if u['role'] != 'admin'), None)
            if non_admin_user:
                user_id = non_admin_user['user_id']
                update_data = {
                    "phone": f"555-TEST-{random.randint(1000, 9999)}"
                }
                success, _ = self.run_test(
                    "Admin - Update user info", 
                    "PUT", f"users/{user_id}", 200, 
                    data=update_data, critical=True
                )
                results.append(success)
                
                # Test restriction: admin cannot edit another admin
                admin_user = next((u for u in users_data if u['role'] == 'admin' and u['user_id'] != self.current_user['user_id']), None)
                if admin_user:
                    success, _ = self.run_test(
                        "Admin - Try to edit another admin (should fail)", 
                        "PUT", f"users/{admin_user['user_id']}", 403, 
                        data={"phone": "should-fail"}
                    )
                    results.append(success)
                    if success:
                        print(f"   ✅ Admin edit restriction working - cannot edit other admins")
        
        return all(results)

    def test_admin_dashboard_stats(self):
        """Test stats verification for admin dashboard"""
        results = []
        
        print(f"\n📊 Testing Admin Dashboard Stats...")
        
        # Count total students
        success, students_data = self.run_test("Get all students for count", "GET", "students", 200, critical=True)
        results.append(success)
        if success and students_data:
            student_count = len(students_data)
            print(f"   ✅ Total students: {student_count}")
        
        # Count teachers from users
        success, users_data = self.run_test("Get all users for teacher count", "GET", "users", 200, critical=True)
        results.append(success)
        if success and users_data:
            teacher_count = len([u for u in users_data if u['role'] == 'teacher'])
            print(f"   ✅ Total teachers: {teacher_count}")
        
        # Count total buses
        success, buses_data = self.run_test("Get all buses for count", "GET", "buses", 200, critical=True)
        results.append(success)
        if success and buses_data:
            bus_count = len(buses_data)
            print(f"   ✅ Total buses: {bus_count}")
        
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

    def test_attendance_flow(self):
        """Test complete attendance flow"""
        results = []
        
        if not self.student_ids:
            print("   No student IDs available for attendance testing")
            return False
        
        student_id = self.student_ids[0]
        
        # Test verified scan (should create yellow status)
        success, _ = self.test_scan_event(student_id, verified=True)
        results.append(success)
        
        # Test unverified scan (should create notification)
        success, _ = self.test_scan_event(student_id, verified=False)
        results.append(success)
        
        # Check notifications were created
        success, notifications = self.run_test(
            "Check notifications after unverified scan",
            "GET",
            "get_notifications",
            200
        )
        results.append(success)
        
        if success and notifications:
            mismatch_notifications = [n for n in notifications if n.get('type') == 'mismatch']
            print(f"   Found {len(mismatch_notifications)} identity mismatch notifications")
        
        # Get attendance to verify status
        success, attendance_data = self.test_get_attendance(student_id)
        results.append(success)
        
        return all(results)

    def test_admin_dashboard_enhancements(self):
        """Test new Admin Dashboard enhancements - roll_number field and user creation"""
        results = []
        
        print(f"\n🎯 Testing Admin Dashboard Enhancements...")
        
        # 1. Test Student Creation with Roll Number
        print(f"   Testing Student Creation with Roll Number...")
        
        # First, get existing bus and parent IDs for test data
        success, buses_data = self.run_test("Get buses for student creation", "GET", "buses", 200)
        if not success or not buses_data:
            print("   ❌ Cannot get buses for student creation test")
            return False
        
        success, users_data = self.run_test("Get users for parent ID", "GET", "users", 200)
        if not success or not users_data:
            print("   ❌ Cannot get users for student creation test")
            return False
        
        # Find a parent user
        parent_user = next((u for u in users_data if u['role'] == 'parent'), None)
        if not parent_user:
            print("   ❌ No parent user found for student creation test")
            return False
        
        bus_id = buses_data[0]['bus_id']
        parent_id = parent_user['user_id']
        
        # Test 1: Create student with roll_number in Grade 5 - A
        student_data_1 = {
            "name": "Test Student Alpha",
            "roll_number": "001",
            "class_name": "Grade 5",
            "section": "A",
            "parent_id": parent_id,
            "bus_id": bus_id,
            "phone": "+1-555-TEST1",
            "emergency_contact": "+1-555-EMRG1",
            "remarks": "Test student for roll number validation"
        }
        
        success, created_student_1 = self.run_test(
            "Create student with roll_number 001 in Grade 5-A",
            "POST",
            "students",
            200,
            data=student_data_1,
            critical=True
        )
        results.append(success)
        
        if success and created_student_1:
            print(f"   ✅ Student created: {created_student_1['name']} - Roll: {created_student_1['roll_number']}")
            test_student_id_1 = created_student_1['student_id']
        else:
            print("   ❌ Failed to create first test student")
            return False
        
        # Test 2: Create another student with same roll_number in different class (should succeed)
        student_data_2 = {
            "name": "Test Student Beta",
            "roll_number": "001",  # Same roll number
            "class_name": "Grade 6",  # Different class
            "section": "B",  # Different section
            "parent_id": parent_id,
            "bus_id": bus_id,
            "phone": "+1-555-TEST2",
            "emergency_contact": "+1-555-EMRG2",
            "remarks": "Test student for roll number uniqueness across classes"
        }
        
        success, created_student_2 = self.run_test(
            "Create student with same roll_number 001 in Grade 6-B (should succeed)",
            "POST",
            "students",
            200,
            data=student_data_2,
            critical=True
        )
        results.append(success)
        
        if success and created_student_2:
            print(f"   ✅ Student created in different class: {created_student_2['name']} - Roll: {created_student_2['roll_number']}")
            test_student_id_2 = created_student_2['student_id']
        else:
            print("   ❌ Failed to create student with same roll number in different class")
        
        # Test 3: Try to create student with same roll_number in same class+section (should fail)
        student_data_3 = {
            "name": "Test Student Gamma",
            "roll_number": "001",  # Same roll number
            "class_name": "Grade 5",  # Same class
            "section": "A",  # Same section
            "parent_id": parent_id,
            "bus_id": bus_id,
            "phone": "+1-555-TEST3"
        }
        
        success, _ = self.run_test(
            "Try to create student with duplicate roll_number in same class+section (should fail)",
            "POST",
            "students",
            400,  # Should fail with 400
            data=student_data_3,
            critical=True
        )
        results.append(success)
        
        if success:
            print(f"   ✅ Roll number uniqueness validation working - duplicate in same class rejected")
        else:
            print("   ❌ Roll number uniqueness validation failed - duplicate was allowed")
        
        # Test 4: Verify GET /api/students includes roll_number field
        success, all_students = self.run_test(
            "Verify GET /api/students includes roll_number field",
            "GET",
            "students",
            200,
            critical=True
        )
        results.append(success)
        
        if success and all_students:
            # Check if roll_number field is present in response
            students_with_roll = [s for s in all_students if 'roll_number' in s]
            if len(students_with_roll) == len(all_students):
                print(f"   ✅ All {len(all_students)} students have roll_number field (including null values)")
            else:
                print(f"   ❌ Some students missing roll_number field: {len(students_with_roll)}/{len(all_students)}")
                results.append(False)
            
            # Verify our test students are in the list with correct roll numbers
            test_students = [s for s in all_students if s['name'].startswith('Test Student')]
            for student in test_students:
                if student.get('roll_number'):
                    print(f"   ✅ Found test student: {student['name']} - Roll: {student['roll_number']} - Class: {student['class_name']}-{student['section']}")
        
        # 2. Test User Creation Endpoint
        print(f"\n   Testing User Creation Endpoint...")
        
        # Test 5: Create parent user
        import time
        timestamp = int(time.time())
        parent_data = {
            "name": "Test Parent",
            "email": f"testparent{timestamp}@test.com",
            "password": "test123",
            "role": "parent",
            "phone": "+1-555-PARENT",
            "address": "123 Test Street, Test City"
        }
        
        success, created_parent = self.run_test(
            "Create parent user",
            "POST",
            "users",
            200,
            data=parent_data,
            critical=True
        )
        results.append(success)
        
        if success and created_parent:
            print(f"   ✅ Parent user created: {created_parent['name']} - {created_parent['email']}")
            # Verify password_hash is not in response
            if 'password_hash' not in created_parent:
                print(f"   ✅ Password hash properly excluded from response")
            else:
                print(f"   ❌ Security issue: password_hash exposed in response")
                results.append(False)
            test_parent_id = created_parent['user_id']
        else:
            print("   ❌ Failed to create parent user")
        
        # Test 6: Create teacher user with assigned_class and assigned_section
        teacher_data = {
            "name": "Test Teacher",
            "email": f"testteacher{timestamp}@test.com", 
            "password": "test123",
            "role": "teacher",
            "phone": "+1-555-TEACHER",
            "assigned_class": "Grade 1",
            "assigned_section": "A",
            "address": "456 Teacher Lane, Education City"
        }
        
        success, created_teacher = self.run_test(
            "Create teacher user with assigned class/section",
            "POST",
            "users",
            200,
            data=teacher_data,
            critical=True
        )
        results.append(success)
        
        if success and created_teacher:
            print(f"   ✅ Teacher user created: {created_teacher['name']} - Class: {created_teacher.get('assigned_class')}-{created_teacher.get('assigned_section')}")
            if created_teacher.get('assigned_class') == "Grade 1" and created_teacher.get('assigned_section') == "A":
                print(f"   ✅ Teacher assignment fields properly saved")
            else:
                print(f"   ❌ Teacher assignment fields not saved correctly")
                results.append(False)
            test_teacher_id = created_teacher['user_id']
        else:
            print("   ❌ Failed to create teacher user")
        
        # Test 7: Create admin user
        admin_data = {
            "name": "Test Admin",
            "email": f"testadmin{timestamp}@test.com",
            "password": "test123", 
            "role": "admin",
            "phone": "+1-555-ADMIN",
            "address": "789 Admin Boulevard, Management City"
        }
        
        success, created_admin = self.run_test(
            "Create admin user",
            "POST",
            "users",
            200,
            data=admin_data,
            critical=True
        )
        results.append(success)
        
        if success and created_admin:
            print(f"   ✅ Admin user created: {created_admin['name']} - {created_admin['email']}")
            test_admin_id = created_admin['user_id']
        else:
            print("   ❌ Failed to create admin user")
        
        # Test 8: Test email uniqueness validation
        duplicate_email_data = {
            "name": "Duplicate Email User",
            "email": f"testparent{timestamp}@test.com",  # Same email as parent created above
            "password": "test123",
            "role": "parent"
        }
        
        success, _ = self.run_test(
            "Try to create user with duplicate email (should fail)",
            "POST",
            "users",
            400,  # Should fail with 400
            data=duplicate_email_data,
            critical=True
        )
        results.append(success)
        
        if success:
            print(f"   ✅ Email uniqueness validation working - duplicate email rejected")
        else:
            print("   ❌ Email uniqueness validation failed - duplicate email was allowed")
        
        # Test 9: Verify password hashing is working by trying to login with created user
        print(f"\n   Testing password hashing by attempting login...")
        
        # Logout current admin session
        self.test_logout()
        
        # Try to login with newly created parent
        login_success = self.test_login(f"testparent{timestamp}@test.com", "test123")
        if login_success:
            print(f"   ✅ Password hashing working - can login with created parent user")
            self.test_logout()
        else:
            print(f"   ❌ Password hashing issue - cannot login with created parent user")
            results.append(False)
        
        # Login back as admin for cleanup
        self.test_login("admin@school.com", "password")
        
        # Cleanup: Delete test users and students
        print(f"\n   Cleaning up test data...")
        
        # Delete test students
        if 'test_student_id_1' in locals():
            self.run_test("Cleanup - Delete test student 1", "DELETE", f"students/{test_student_id_1}", 200)
        if 'test_student_id_2' in locals():
            self.run_test("Cleanup - Delete test student 2", "DELETE", f"students/{test_student_id_2}", 200)
        
        # Note: We don't delete test users as there's no DELETE /api/users endpoint
        # This is expected behavior - users would be managed through admin interface
        
        print(f"   ✅ Test cleanup completed")
        
        return all(results)

    def test_admin_crud_operations(self):
        """Test all CRUD operations for Admin Dashboard as per review request"""
        results = []
        
        print(f"\n🎯 Testing Admin Dashboard CRUD Operations (Review Request)...")
        
        # ===== 1. STUDENTS CRUD =====
        print(f"\n   === STUDENTS CRUD ===")
        
        # Create a test student first
        success, users_data = self.run_test("Get users for test student", "GET", "users", 200)
        if not success or not users_data:
            print("   ❌ Cannot get users for student CRUD test")
            return False
        
        parent_user = next((u for u in users_data if u['role'] == 'parent'), None)
        if not parent_user:
            print("   ❌ No parent user found for student CRUD test")
            return False
        
        success, buses_data = self.run_test("Get buses for test student", "GET", "buses", 200)
        if not success or not buses_data:
            print("   ❌ Cannot get buses for student CRUD test")
            return False
        
        import time
        timestamp = int(time.time())
        test_student_data = {
            "name": f"CRUD Test Student {timestamp}",
            "roll_number": f"CRUD{timestamp}",
            "class_name": "Grade 10",
            "section": "Z",
            "parent_id": parent_user['user_id'],
            "bus_id": buses_data[0]['bus_id'],
            "phone": "+1-555-CRUD-TEST",
            "emergency_contact": "+1-555-CRUD-EMRG",
            "remarks": "Test student for CRUD operations"
        }
        
        success, created_student = self.run_test(
            "Create test student for deletion",
            "POST",
            "students",
            200,
            data=test_student_data,
            critical=True
        )
        results.append(success)
        
        if not success or not created_student:
            print("   ❌ Failed to create test student")
            return False
        
        test_student_id = created_student['student_id']
        print(f"   ✅ Test student created: {created_student['name']} (ID: {test_student_id})")
        
        # Test: DELETE student as admin (should succeed)
        success, _ = self.run_test(
            "DELETE /api/students/{student_id} - Admin deletes student",
            "DELETE",
            f"students/{test_student_id}",
            200,
            critical=True
        )
        results.append(success)
        if success:
            print(f"   ✅ Admin successfully deleted student")
        
        # Verify student is deleted
        success, _ = self.run_test(
            "Verify student is deleted (should return 404)",
            "GET",
            f"students/{test_student_id}",
            404
        )
        results.append(success)
        if success:
            print(f"   ✅ Student deletion verified")
        
        # Logout admin and login as teacher to test 403
        self.test_logout()
        
        # Create another test student for teacher 403 test
        self.test_login("admin@school.com", "password")
        success, created_student2 = self.run_test(
            "Create another test student for 403 test",
            "POST",
            "students",
            200,
            data={**test_student_data, "name": f"CRUD Test Student 2 {timestamp}", "roll_number": f"CRUD2{timestamp}"}
        )
        if success and created_student2:
            test_student_id_2 = created_student2['student_id']
            self.test_logout()
            
            # Login as teacher and try to delete (should fail with 403)
            if self.test_login("teacher@school.com", "password"):
                success, _ = self.run_test(
                    "DELETE /api/students/{student_id} - Teacher tries to delete (should fail 403)",
                    "DELETE",
                    f"students/{test_student_id_2}",
                    403,
                    critical=True
                )
                results.append(success)
                if success:
                    print(f"   ✅ Admin-only access verified - teacher got 403")
                self.test_logout()
            
            # Cleanup: Delete the second test student as admin
            self.test_login("admin@school.com", "password")
            self.run_test("Cleanup test student 2", "DELETE", f"students/{test_student_id_2}", 200)
        
        # ===== 2. USERS CRUD =====
        print(f"\n   === USERS CRUD ===")
        
        # Create a test parent user for deletion
        test_parent_data = {
            "name": f"CRUD Test Parent {timestamp}",
            "email": f"crudparent{timestamp}@test.com",
            "password": "test123",
            "role": "parent",
            "phone": "+1-555-CRUD-PARENT",
            "address": "123 CRUD Test Street"
        }
        
        success, created_parent = self.run_test(
            "Create test parent user for deletion",
            "POST",
            "users",
            200,
            data=test_parent_data,
            critical=True
        )
        results.append(success)
        
        if not success or not created_parent:
            print("   ❌ Failed to create test parent")
            return False
        
        test_parent_id = created_parent['user_id']
        print(f"   ✅ Test parent created: {created_parent['name']} (ID: {test_parent_id})")
        
        # Create a student linked to this parent to test cascading
        test_student_for_cascade = {
            "name": f"Cascade Test Student {timestamp}",
            "roll_number": f"CASCADE{timestamp}",
            "class_name": "Grade 11",
            "section": "Y",
            "parent_id": test_parent_id,
            "bus_id": buses_data[0]['bus_id'],
            "phone": "+1-555-CASCADE",
            "emergency_contact": "+1-555-CASCADE-EMRG"
        }
        
        success, created_cascade_student = self.run_test(
            "Create student linked to test parent",
            "POST",
            "students",
            200,
            data=test_student_for_cascade,
            critical=True
        )
        results.append(success)
        
        if not success or not created_cascade_student:
            print("   ❌ Failed to create cascade test student")
            return False
        
        cascade_student_id = created_cascade_student['student_id']
        print(f"   ✅ Cascade test student created: {created_cascade_student['name']} (ID: {cascade_student_id})")
        
        # Test: DELETE parent user (should succeed and cascade)
        success, _ = self.run_test(
            "DELETE /api/users/{user_id} - Delete parent user",
            "DELETE",
            f"users/{test_parent_id}",
            200,
            critical=True
        )
        results.append(success)
        if success:
            print(f"   ✅ Parent user successfully deleted")
        
        # Verify cascading: student.parent_id should be null
        success, cascade_student_data = self.run_test(
            "Verify cascading - student.parent_id should be null",
            "GET",
            f"students/{cascade_student_id}",
            200,
            critical=True
        )
        results.append(success)
        if success and cascade_student_data:
            if cascade_student_data.get('parent_id') is None:
                print(f"   ✅ Cascading verified - student.parent_id is null after parent deletion")
            else:
                print(f"   ❌ Cascading failed - student.parent_id is still: {cascade_student_data.get('parent_id')}")
                results.append(False)
        
        # Cleanup cascade test student
        self.run_test("Cleanup cascade test student", "DELETE", f"students/{cascade_student_id}", 200)
        
        # Test: Try to delete admin (should fail with 403)
        success, all_users = self.run_test("Get all users to find another admin", "GET", "users", 200)
        if success and all_users:
            # Find another admin (not current user)
            other_admin = next((u for u in all_users if u['role'] == 'admin' and u['user_id'] != self.current_user['user_id']), None)
            
            if other_admin:
                success, _ = self.run_test(
                    "DELETE /api/users/{user_id} - Try to delete another admin (should fail 403)",
                    "DELETE",
                    f"users/{other_admin['user_id']}",
                    403,
                    critical=True
                )
                results.append(success)
                if success:
                    print(f"   ✅ Admin deletion protection verified - cannot delete another admin")
            else:
                print(f"   ⚠️  No other admin found to test deletion protection")
        
        # Test: Try to delete self (should fail with 403)
        success, _ = self.run_test(
            "DELETE /api/users/{user_id} - Try to delete self (should fail 403)",
            "DELETE",
            f"users/{self.current_user['user_id']}",
            403,
            critical=True
        )
        results.append(success)
        if success:
            print(f"   ✅ Self-deletion protection verified - cannot delete own account")
        
        # ===== 3. BUSES CRUD =====
        print(f"\n   === BUSES CRUD ===")
        
        # Get routes for bus creation
        success, routes_data = self.run_test("Get routes for bus creation", "GET", "routes", 200)
        route_id = routes_data[0]['route_id'] if success and routes_data else None
        
        # Test: POST /api/buses - Create a new bus
        test_bus_data = {
            "bus_number": f"TEST-BUS-{timestamp}",
            "driver_name": "Test Driver",
            "driver_phone": "+1-555-TEST-DRIVER",
            "route_id": route_id,
            "capacity": 40,
            "remarks": "Test bus for CRUD operations"
        }
        
        success, created_bus = self.run_test(
            "POST /api/buses - Create a new bus",
            "POST",
            "buses",
            200,
            data=test_bus_data,
            critical=True
        )
        results.append(success)
        
        if not success or not created_bus:
            print("   ❌ Failed to create test bus")
            return False
        
        test_bus_id = created_bus['bus_id']
        print(f"   ✅ Test bus created: {created_bus['bus_number']} (ID: {test_bus_id})")
        
        # Test: PUT /api/buses/{bus_id} - Update bus details
        updated_bus_data = {
            **test_bus_data,
            "bus_id": test_bus_id,
            "driver_name": "Updated Test Driver",
            "capacity": 45,
            "remarks": "Updated test bus"
        }
        
        success, _ = self.run_test(
            "PUT /api/buses/{bus_id} - Update bus details",
            "PUT",
            f"buses/{test_bus_id}",
            200,
            data=updated_bus_data,
            critical=True
        )
        results.append(success)
        if success:
            print(f"   ✅ Bus successfully updated")
        
        # Verify update
        success, updated_bus = self.run_test(
            "Verify bus update",
            "GET",
            f"buses/{test_bus_id}",
            200
        )
        if success and updated_bus:
            if updated_bus.get('driver_name') == "Updated Test Driver" and updated_bus.get('capacity') == 45:
                print(f"   ✅ Bus update verified - driver: {updated_bus['driver_name']}, capacity: {updated_bus['capacity']}")
            else:
                print(f"   ❌ Bus update verification failed")
                results.append(False)
        
        # Test: DELETE /api/buses/{bus_id} - Delete a bus
        success, _ = self.run_test(
            "DELETE /api/buses/{bus_id} - Delete a bus",
            "DELETE",
            f"buses/{test_bus_id}",
            200,
            critical=True
        )
        results.append(success)
        if success:
            print(f"   ✅ Bus successfully deleted")
        
        # Verify deletion
        success, _ = self.run_test(
            "Verify bus deletion (should return 404)",
            "GET",
            f"buses/{test_bus_id}",
            404
        )
        results.append(success)
        if success:
            print(f"   ✅ Bus deletion verified")
        
        # ===== 4. ROUTES CRUD =====
        print(f"\n   === ROUTES CRUD ===")
        
        # Test: POST /api/stops - Create stops
        test_stop_1_data = {
            "stop_name": f"CRUD Test Stop 1 {timestamp}",
            "lat": 37.7749,
            "lon": -122.4194,
            "order_index": 1
        }
        
        success, created_stop_1 = self.run_test(
            "POST /api/stops - Create stop 1",
            "POST",
            "stops",
            200,
            data=test_stop_1_data,
            critical=True
        )
        results.append(success)
        
        if not success or not created_stop_1:
            print("   ❌ Failed to create test stop 1")
            return False
        
        test_stop_1_id = created_stop_1['stop_id']
        print(f"   ✅ Test stop 1 created: {created_stop_1['stop_name']} (ID: {test_stop_1_id})")
        
        test_stop_2_data = {
            "stop_name": f"CRUD Test Stop 2 {timestamp}",
            "lat": 37.7849,
            "lon": -122.4294,
            "order_index": 2
        }
        
        success, created_stop_2 = self.run_test(
            "POST /api/stops - Create stop 2",
            "POST",
            "stops",
            200,
            data=test_stop_2_data,
            critical=True
        )
        results.append(success)
        
        if not success or not created_stop_2:
            print("   ❌ Failed to create test stop 2")
            return False
        
        test_stop_2_id = created_stop_2['stop_id']
        print(f"   ✅ Test stop 2 created: {created_stop_2['stop_name']} (ID: {test_stop_2_id})")
        
        # Test: POST /api/routes - Create a new route
        test_route_data = {
            "route_name": f"CRUD Test Route {timestamp}",
            "stop_ids": [test_stop_1_id, test_stop_2_id],
            "map_path": [
                {"lat": 37.7749, "lon": -122.4194},
                {"lat": 37.7849, "lon": -122.4294}
            ],
            "remarks": "Test route for CRUD operations"
        }
        
        success, created_route = self.run_test(
            "POST /api/routes - Create a new route",
            "POST",
            "routes",
            200,
            data=test_route_data,
            critical=True
        )
        results.append(success)
        
        if not success or not created_route:
            print("   ❌ Failed to create test route")
            return False
        
        test_route_id = created_route['route_id']
        print(f"   ✅ Test route created: {created_route['route_name']} (ID: {test_route_id})")
        
        # Test: PUT /api/routes/{route_id} - Update route
        updated_route_data = {
            **test_route_data,
            "route_id": test_route_id,
            "route_name": f"Updated CRUD Test Route {timestamp}",
            "remarks": "Updated test route"
        }
        
        success, _ = self.run_test(
            "PUT /api/routes/{route_id} - Update route",
            "PUT",
            f"routes/{test_route_id}",
            200,
            data=updated_route_data,
            critical=True
        )
        results.append(success)
        if success:
            print(f"   ✅ Route successfully updated")
        
        # Verify update
        success, updated_route = self.run_test(
            "Verify route update",
            "GET",
            f"routes/{test_route_id}",
            200
        )
        if success and updated_route:
            if updated_route.get('route_name') == f"Updated CRUD Test Route {timestamp}":
                print(f"   ✅ Route update verified - name: {updated_route['route_name']}")
            else:
                print(f"   ❌ Route update verification failed")
                results.append(False)
        
        # Test: DELETE /api/routes/{route_id} - Delete a route
        success, _ = self.run_test(
            "DELETE /api/routes/{route_id} - Delete a route",
            "DELETE",
            f"routes/{test_route_id}",
            200,
            critical=True
        )
        results.append(success)
        if success:
            print(f"   ✅ Route successfully deleted")
        
        # Verify deletion
        success, _ = self.run_test(
            "Verify route deletion (should return 404)",
            "GET",
            f"routes/{test_route_id}",
            404
        )
        results.append(success)
        if success:
            print(f"   ✅ Route deletion verified")
        
        # Cleanup stops
        self.run_test("Cleanup test stop 1", "DELETE", f"stops/{test_stop_1_id}", 200)
        self.run_test("Cleanup test stop 2", "DELETE", f"stops/{test_stop_2_id}", 200)
        
        print(f"\n   ✅ All CRUD operations test completed")
        
        return all(results)

    def test_missing_endpoints(self):
        """Test for missing endpoints mentioned in review"""
        # Test for /api/get_embeddings (mentioned as missing in review)
        success, _ = self.run_test(
            "Check missing get_embeddings endpoint",
            "GET",
            "get_embeddings",
            404  # Expected to be missing
        )
        return success

    def generate_report(self):
        """Generate comprehensive test report"""
        print(f"\n📋 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        # Summary
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Critical failures
        if self.critical_failures:
            print(f"\n❌ CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"   • {failure['name']}: {failure.get('error', 'Status ' + str(failure['actual_status']))}")
        
        # Passed tests summary
        passed_tests = [t for t in self.test_results if t['success']]
        if passed_tests:
            print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
            for test in passed_tests:
                if test.get('critical'):
                    print(f"   • {test['name']} (CRITICAL)")
                else:
                    print(f"   • {test['name']}")
        
        # Failed tests summary
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                error_info = test.get('error', f"Status {test['actual_status']}")
                if test.get('critical'):
                    print(f"   • {test['name']} (CRITICAL): {error_info}")
                else:
                    print(f"   • {test['name']}: {error_info}")
        
        # API Coverage
        tested_endpoints = set()
        for test in self.test_results:
            tested_endpoints.add(test['endpoint'])
        
        print(f"\n📊 API COVERAGE:")
        print(f"   Endpoints tested: {len(tested_endpoints)}")
        print(f"   Expected endpoints: 22+ (from review request)")
        
        return success_rate >= 80 and len(self.critical_failures) == 0

def main():
    print("🚌 IoT RFID School Bus Tracker - Comprehensive Backend Testing")
    print("=" * 70)
    
    tester = SchoolBusTrackerAPITester()
    
    # Test credentials from seed data
    test_accounts = [
        ("parent@school.com", "password", "parent"),
        ("teacher@school.com", "password", "teacher"), 
        ("admin@school.com", "password", "admin")
    ]
    
    # Phase 1: Authentication Tests
    print(f"\n🔐 PHASE 1: AUTHENTICATION TESTING")
    print("-" * 50)
    
    # Test invalid credentials first
    tester.test_invalid_login()
    
    auth_success = True
    for email, password, role in test_accounts:
        print(f"\n   Testing {role.upper()} authentication...")
        
        # Test login
        if not tester.test_login(email, password):
            print(f"   ❌ Login failed for {role}")
            auth_success = False
            continue
            
        # Test get me
        success, user_data = tester.test_get_me()
        if not success:
            print(f"   ❌ Get user info failed for {role}")
            auth_success = False
            continue
            
        # Test logout
        if not tester.test_logout():
            print(f"   ❌ Logout failed for {role}")
            auth_success = False
    
    if not auth_success:
        print("❌ Authentication tests failed - cannot proceed with role-based testing")
        return 1
    
    # Phase 2: Role-Based Endpoint Testing
    print(f"\n👥 PHASE 2: ROLE-BASED ENDPOINT TESTING")
    print("-" * 50)
    
    # Test Admin role
    print(f"\n   Testing ADMIN role capabilities...")
    if tester.test_login("admin@school.com", "password"):
        admin_success = tester.test_admin_endpoints()
        
        # Test Enhanced Admin Dashboard specific features
        enhanced_admin_success = tester.test_enhanced_admin_dashboard()
        edit_operations_success = tester.test_admin_edit_operations()
        stats_success = tester.test_admin_dashboard_stats()
        
        # Test Admin Dashboard Enhancements (roll_number and user creation)
        enhancements_success = tester.test_admin_dashboard_enhancements()
        
        tester.test_student_crud()
        tester.test_logout()
        
        if not (admin_success and enhanced_admin_success and edit_operations_success and stats_success and enhancements_success):
            print("   ❌ Admin endpoints or Enhanced Dashboard features failed")
    
    # Test Teacher role
    print(f"\n   Testing TEACHER role capabilities...")
    if tester.test_login("teacher@school.com", "password"):
        teacher_success = tester.test_teacher_endpoints()
        tester.test_logout()
        
        if not teacher_success:
            print("   ❌ Teacher endpoints failed")
    
    # Test Parent role
    print(f"\n   Testing PARENT role capabilities...")
    if tester.test_login("parent@school.com", "password"):
        parent_success = tester.test_parent_endpoints()
        
        # Test role-based access control
        print(f"\n   Testing role-based access control...")
        tester.test_role_based_access_control()
        
        tester.test_logout()
        
        if not parent_success:
            print("   ❌ Parent endpoints failed")
    
    # Phase 3: Core IoT Functionality Testing
    print(f"\n🔧 PHASE 3: CORE IoT FUNCTIONALITY TESTING")
    print("-" * 50)
    
    # Login as admin for core tests
    if tester.test_login("admin@school.com", "password"):
        
        print(f"\n   Testing core IoT APIs...")
        
        # Test bus location updates
        tester.test_update_location()
        tester.test_get_bus_location()
        
        # Test attendance flow
        print(f"\n   Testing attendance flow...")
        tester.test_attendance_flow()
        
        # Test notifications
        tester.test_get_notifications()
        
        # Test demo endpoints
        print(f"\n   Testing demo simulation...")
        tester.test_demo_endpoints()
        
        tester.test_logout()
    
    # Phase 4: Edge Cases and Missing Endpoints
    print(f"\n⚠️  PHASE 4: EDGE CASES & MISSING ENDPOINTS")
    print("-" * 50)
    
    tester.test_missing_endpoints()
    
    # Generate final report
    overall_success = tester.generate_report()
    
    if overall_success:
        print(f"\n🎉 OVERALL RESULT: SUCCESS")
        print("   All critical backend APIs are working correctly!")
        return 0
    else:
        print(f"\n💥 OVERALL RESULT: ISSUES FOUND")
        print("   Critical issues detected that need attention!")
        return 1

if __name__ == "__main__":
    sys.exit(main())