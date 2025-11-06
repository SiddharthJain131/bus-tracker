import requests
import sys
from datetime import datetime
import json

class TeacherDashboardTester:
    def __init__(self, base_url="https://teacher-bus-tracker.preview.emergentagent.com"):
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

    def test_teacher_authentication(self):
        """Test teacher authentication and profile"""
        print(f"\n🔐 TESTING TEACHER AUTHENTICATION & PROFILE")
        print("-" * 50)
        
        # Test login
        success, response = self.run_test(
            "Teacher Login",
            "POST",
            "auth/login",
            200,
            data={"email": "teacher@school.com", "password": "password"},
            critical=True
        )
        
        if not success:
            return False
            
        self.current_user = response
        print(f"   ✅ Logged in as: {response.get('name')} ({response.get('role')})")
        
        # Verify teacher profile includes required fields
        required_fields = ['user_id', 'email', 'role', 'name', 'phone', 'photo', 'assigned_class', 'assigned_section']
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            print(f"   ❌ Missing profile fields: {missing_fields}")
            return False
        
        if response.get('role') != 'teacher':
            print(f"   ❌ Expected role 'teacher', got '{response.get('role')}'")
            return False
            
        print(f"   ✅ Teacher profile complete:")
        print(f"      - Name: {response.get('name')}")
        print(f"      - Email: {response.get('email')}")
        print(f"      - Phone: {response.get('phone')}")
        print(f"      - Class: {response.get('assigned_class')}")
        print(f"      - Section: {response.get('assigned_section')}")
        
        # Test GET /api/auth/me
        success, me_data = self.run_test(
            "Get Teacher Profile (/api/auth/me)",
            "GET",
            "auth/me",
            200,
            critical=True
        )
        
        if success:
            # Verify same fields are present
            for field in required_fields:
                if field not in me_data:
                    print(f"   ❌ /api/auth/me missing field: {field}")
                    return False
            print(f"   ✅ /api/auth/me returns complete teacher profile")
        
        return success

    def test_enhanced_teacher_students_endpoint(self):
        """Test enhanced /api/teacher/students endpoint"""
        print(f"\n👥 TESTING ENHANCED TEACHER STUDENTS ENDPOINT")
        print("-" * 50)
        
        success, students_data = self.run_test(
            "GET /api/teacher/students (Enhanced)",
            "GET",
            "teacher/students",
            200,
            critical=True
        )
        
        if not success:
            return False
            
        if not students_data:
            print(f"   ❌ No students returned for teacher")
            return False
            
        print(f"   ✅ Teacher has {len(students_data)} assigned students")
        
        # Verify each student has required enriched fields
        required_fields = ['student_id', 'name', 'class_name', 'section', 'parent_name', 'bus_id', 'bus_number', 'am_status', 'pm_status']
        
        for i, student in enumerate(students_data):
            print(f"\n   Student {i+1}: {student.get('name')}")
            
            missing_fields = [field for field in required_fields if field not in student]
            if missing_fields:
                print(f"   ❌ Missing fields: {missing_fields}")
                return False
                
            # Verify enrichment data
            print(f"      - Parent Name: {student.get('parent_name')} (ENHANCED)")
            print(f"      - Bus Number: {student.get('bus_number')} (BUS ENRICHMENT)")
            print(f"      - AM Status: {student.get('am_status')} (TODAY'S ATTENDANCE)")
            print(f"      - PM Status: {student.get('pm_status')} (TODAY'S ATTENDANCE)")
            print(f"      - Class: {student.get('class_name')}")
            print(f"      - Section: {student.get('section')}")
            
            # Verify parent_name is not N/A or empty (newly added enrichment)
            if not student.get('parent_name') or student.get('parent_name') == 'N/A':
                print(f"   ❌ Parent name enrichment missing or N/A")
                return False
                
        print(f"   ✅ All students have complete enriched data including parent_name")
        
        # Test role-based access (should fail for non-teacher)
        # First logout
        self.run_test("Logout", "POST", "auth/logout", 200)
        
        # Login as parent
        parent_login = self.run_test(
            "Parent Login (for access test)",
            "POST", 
            "auth/login",
            200,
            data={"email": "parent@school.com", "password": "password"}
        )
        
        if parent_login[0]:
            # Try to access teacher endpoint (should fail)
            success, _ = self.run_test(
                "Parent accessing teacher endpoint (should fail with 403)",
                "GET",
                "teacher/students", 
                403
            )
            
            if success:
                print(f"   ✅ Role-based access control working - parent cannot access teacher endpoint")
            else:
                print(f"   ❌ Role-based access control failed - parent should not access teacher endpoint")
                return False
                
            # Logout parent and login teacher again
            self.run_test("Logout Parent", "POST", "auth/logout", 200)
            teacher_login = self.run_test(
                "Re-login Teacher",
                "POST",
                "auth/login", 
                200,
                data={"email": "teacher@school.com", "password": "password"}
            )
            
            if not teacher_login[0]:
                return False
                
        return True

    def test_student_details_for_modal(self):
        """Test student details endpoint for View modal"""
        print(f"\n📋 TESTING STUDENT DETAILS FOR VIEW MODAL")
        print("-" * 50)
        
        # First get students to get a student ID
        success, students_data = self.run_test(
            "Get students for detail test",
            "GET",
            "teacher/students",
            200
        )
        
        if not success or not students_data:
            print(f"   ❌ Cannot get students for detail testing")
            return False
            
        student_id = students_data[0]['student_id']
        student_name = students_data[0]['name']
        
        success, student_detail = self.run_test(
            f"GET /api/students/{student_id} (Student Detail for Modal)",
            "GET",
            f"students/{student_id}",
            200,
            critical=True
        )
        
        if not success:
            return False
            
        # Verify all required fields for modal are present
        required_modal_fields = [
            'name', 'student_id', 'class_name', 'section', 'phone',
            'parent_name', 'parent_email', 'bus_number', 'route_id', 'teacher_name'
        ]
        
        missing_fields = [field for field in required_modal_fields if field not in student_detail]
        if missing_fields:
            print(f"   ❌ Student detail missing fields for modal: {missing_fields}")
            return False
            
        print(f"   ✅ Student detail complete for modal: {student_name}")
        print(f"      - Basic Info: {student_detail.get('name')}, ID: {student_detail.get('student_id')}")
        print(f"      - Class/Section: {student_detail.get('class_name')}/{student_detail.get('section')}")
        print(f"      - Phone: {student_detail.get('phone')}")
        print(f"      - Parent: {student_detail.get('parent_name')} ({student_detail.get('parent_email')})")
        print(f"      - Bus: {student_detail.get('bus_number')}")
        print(f"      - Route ID: {student_detail.get('route_id')}")
        print(f"      - Teacher: {student_detail.get('teacher_name')}")
        
        return True

    def test_monthly_attendance_for_stats(self):
        """Test monthly attendance endpoint for stats calculation"""
        print(f"\n📊 TESTING MONTHLY ATTENDANCE FOR STATS")
        print("-" * 50)
        
        # Get students first
        success, students_data = self.run_test(
            "Get students for attendance test",
            "GET", 
            "teacher/students",
            200
        )
        
        if not success or not students_data:
            return False
            
        # Test attendance for multiple students
        attendance_results = []
        for student in students_data[:2]:  # Test first 2 students
            student_id = student['student_id']
            student_name = student['name']
            
            success, attendance_data = self.run_test(
                f"GET /api/get_attendance for {student_name} (2025-01)",
                "GET",
                "get_attendance",
                200,
                params={"student_id": student_id, "month": "2025-01"},
                critical=True
            )
            
            if success and attendance_data:
                grid = attendance_data.get('grid', [])
                summary = attendance_data.get('summary', '')
                
                print(f"   ✅ Attendance data for {student_name}:")
                print(f"      - Grid entries: {len(grid)} days")
                print(f"      - Summary: {summary}")
                
                # Verify grid structure
                if grid:
                    sample_day = grid[0]
                    required_day_fields = ['date', 'day', 'am_status', 'pm_status']
                    missing_day_fields = [field for field in required_day_fields if field not in sample_day]
                    
                    if missing_day_fields:
                        print(f"   ❌ Attendance grid missing fields: {missing_day_fields}")
                        return False
                        
                    print(f"      - Sample day: {sample_day['date']} - AM: {sample_day['am_status']}, PM: {sample_day['pm_status']}")
                    
                # Calculate attendance percentage for stats
                present_sessions = sum(1 for day in grid for status in [day['am_status'], day['pm_status']] if status in ['yellow', 'green'])
                total_sessions = len(grid) * 2
                attendance_percentage = (present_sessions / total_sessions * 100) if total_sessions > 0 else 0
                
                print(f"      - Attendance %: {attendance_percentage:.1f}% ({present_sessions}/{total_sessions} sessions)")
                attendance_results.append(attendance_percentage)
            else:
                return False
                
        # Calculate average attendance for teacher dashboard stats
        if attendance_results:
            avg_attendance = sum(attendance_results) / len(attendance_results)
            print(f"   ✅ Average monthly attendance for teacher's students: {avg_attendance:.1f}%")
            
        return True

    def test_notifications_for_teacher(self):
        """Test notifications endpoint for teacher"""
        print(f"\n🔔 TESTING NOTIFICATIONS FOR TEACHER")
        print("-" * 50)
        
        success, notifications = self.run_test(
            "GET /api/get_notifications (Teacher)",
            "GET",
            "get_notifications",
            200,
            critical=True
        )
        
        if not success:
            return False
            
        print(f"   ✅ Retrieved {len(notifications)} notifications for teacher")
        
        # Verify notification structure
        if notifications:
            sample_notification = notifications[0]
            required_notification_fields = ['notification_id', 'type', 'message', 'timestamp', 'user_id']
            
            missing_fields = [field for field in required_notification_fields if field not in sample_notification]
            if missing_fields:
                print(f"   ❌ Notification missing fields: {missing_fields}")
                return False
                
            print(f"   ✅ Notification structure complete:")
            for notification in notifications[:3]:  # Show first 3
                print(f"      - {notification.get('type')}: {notification.get('message')[:50]}...")
                print(f"        Time: {notification.get('timestamp')}")
        else:
            print(f"   ℹ️  No notifications found (this is normal for new teacher account)")
            
        return True

    def test_route_details_for_map_modal(self):
        """Test route details endpoint for map modal"""
        print(f"\n🗺️  TESTING ROUTE DETAILS FOR MAP MODAL")
        print("-" * 50)
        
        # First get a student to get their route_id
        success, students_data = self.run_test(
            "Get students for route test",
            "GET",
            "teacher/students", 
            200
        )
        
        if not success or not students_data:
            return False
            
        # Find a student with a bus/route
        student_with_route = None
        for student in students_data:
            if student.get('bus_id'):
                # Get student details to get route_id
                success, student_detail = self.run_test(
                    f"Get student detail for route_id",
                    "GET",
                    f"students/{student['student_id']}",
                    200
                )
                if success and student_detail.get('route_id'):
                    student_with_route = student_detail
                    break
                    
        if not student_with_route:
            print(f"   ❌ No student found with route assignment")
            return False
            
        route_id = student_with_route['route_id']
        
        success, route_data = self.run_test(
            f"GET /api/routes/{route_id} (Route Details for Map)",
            "GET",
            f"routes/{route_id}",
            200,
            critical=True
        )
        
        if not success:
            return False
            
        # Verify route data includes all required fields for map visualization
        required_route_fields = ['route_id', 'route_name', 'stops', 'map_path']
        missing_fields = [field for field in required_route_fields if field not in route_data]
        
        if missing_fields:
            print(f"   ❌ Route data missing fields for map: {missing_fields}")
            return False
            
        stops = route_data.get('stops', [])
        map_path = route_data.get('map_path', [])
        
        print(f"   ✅ Route details complete for map modal:")
        print(f"      - Route: {route_data.get('route_name')} (ID: {route_data.get('route_id')})")
        print(f"      - Stops: {len(stops)} stops")
        print(f"      - Map Path: {len(map_path)} coordinates")
        
        # Verify stops have required fields
        if stops:
            sample_stop = stops[0]
            required_stop_fields = ['stop_id', 'stop_name', 'lat', 'lon', 'order_index']
            missing_stop_fields = [field for field in required_stop_fields if field not in sample_stop]
            
            if missing_stop_fields:
                print(f"   ❌ Stop data missing fields: {missing_stop_fields}")
                return False
                
            print(f"      - Sample stop: {sample_stop.get('stop_name')} at ({sample_stop.get('lat')}, {sample_stop.get('lon')})")
            
        # Verify map_path has coordinates
        if map_path:
            sample_coord = map_path[0]
            if 'lat' not in sample_coord or 'lon' not in sample_coord:
                print(f"   ❌ Map path coordinates missing lat/lon")
                return False
                
            print(f"      - Map path starts at: ({sample_coord.get('lat')}, {sample_coord.get('lon')})")
            
        return True

    def generate_report(self):
        """Generate test report"""
        print(f"\n📋 TEACHER DASHBOARD TEST REPORT")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.critical_failures:
            print(f"\n❌ CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"   • {failure['name']}: {failure.get('error', 'Status ' + str(failure['actual_status']))}")
        
        return success_rate >= 90 and len(self.critical_failures) == 0

def main():
    print("🎓 Enhanced Teacher Dashboard Backend API Testing")
    print("=" * 60)
    
    tester = TeacherDashboardTester()
    
    # Run all teacher dashboard tests
    tests = [
        tester.test_teacher_authentication,
        tester.test_enhanced_teacher_students_endpoint,
        tester.test_student_details_for_modal,
        tester.test_monthly_attendance_for_stats,
        tester.test_notifications_for_teacher,
        tester.test_route_details_for_map_modal
    ]
    
    all_passed = True
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            all_passed = False
    
    # Generate final report
    overall_success = tester.generate_report()
    
    if overall_success and all_passed:
        print(f"\n🎉 TEACHER DASHBOARD TESTING: SUCCESS")
        print("   All enhanced Teacher Dashboard backend APIs are working correctly!")
        return 0
    else:
        print(f"\n💥 TEACHER DASHBOARD TESTING: ISSUES FOUND")
        print("   Some Teacher Dashboard features need attention!")
        return 1

if __name__ == "__main__":
    sys.exit(main())