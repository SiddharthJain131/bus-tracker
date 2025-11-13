#!/usr/bin/env python3
"""
Profile Photo Display Testing - Bus Tracker Application
Testing photo serving via FastAPI StaticFiles for all user roles

This script tests the profile photo display functionality including:
- Photo URL conversion from database paths to accessible URLs
- Static file serving for all user roles (admin, teacher, parent)
- Login and /auth/me endpoints returning correct photo URLs
- Photo file accessibility via HTTP requests
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://unused-cleanup.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class PhotoDisplayTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.test_users = [
            {"email": "admin@school.com", "password": "password", "role": "admin", "name": "James Anderson"},
            {"email": "admin2@school.com", "password": "password", "role": "admin", "name": "Patricia Williams"},
            {"email": "teacher@school.com", "password": "password", "role": "teacher", "name": "Mary Johnson"},
            {"email": "teacher2@school.com", "password": "password", "role": "teacher", "name": "Robert Smith"},
            {"email": "parent@school.com", "password": "password", "role": "parent", "name": "John Parent"}
        ]
        
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

    def test_user_login_photo_url(self, user_data):
        """Test login endpoint returns correct photo URL format"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if user data is correct
                if data.get('name') != user_data['name'] or data.get('role') != user_data['role']:
                    self.log_result(f"Login {user_data['role']} - {user_data['email']}", False, 
                                  f"User data mismatch. Expected: {user_data['name']} ({user_data['role']}), Got: {data.get('name')} ({data.get('role')})")
                    return None
                
                photo_url = data.get('photo')
                
                # Check photo URL format
                if photo_url:
                    if photo_url.startswith('/photos/'):
                        expected_role_folder = f"/photos/{user_data['role']}s/"  # admins, teachers, parents
                        if photo_url.startswith(expected_role_folder):
                            self.log_result(f"Login {user_data['role']} - {user_data['email']}", True, 
                                          f"Photo URL format correct: {photo_url}")
                            return {"session": response.cookies, "photo_url": photo_url, "user_data": data}
                        else:
                            self.log_result(f"Login {user_data['role']} - {user_data['email']}", False, 
                                          f"Photo URL wrong role folder. Expected: {expected_role_folder}, Got: {photo_url}")
                            return None
                    else:
                        self.log_result(f"Login {user_data['role']} - {user_data['email']}", False, 
                                      f"Photo URL wrong format. Expected: /photos/..., Got: {photo_url}")
                        return None
                else:
                    # Photo URL is null - this is acceptable
                    self.log_result(f"Login {user_data['role']} - {user_data['email']}", True, 
                                  f"Photo URL is null (no photo assigned)")
                    return {"session": response.cookies, "photo_url": None, "user_data": data}
            else:
                self.log_result(f"Login {user_data['role']} - {user_data['email']}", False, 
                              f"Login failed. Status: {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            self.log_result(f"Login {user_data['role']} - {user_data['email']}", False, f"Exception: {str(e)}")
            return None

    def test_auth_me_photo_url(self, user_data, session_cookies):
        """Test /auth/me endpoint returns consistent photo URL"""
        try:
            response = requests.get(f"{API_BASE}/auth/me", cookies=session_cookies)
            
            if response.status_code == 200:
                data = response.json()
                photo_url = data.get('photo')
                
                # Check photo URL format (same logic as login)
                if photo_url:
                    if photo_url.startswith('/photos/'):
                        expected_role_folder = f"/photos/{user_data['role']}s/"  # admins, teachers, parents
                        if photo_url.startswith(expected_role_folder):
                            self.log_result(f"/auth/me {user_data['role']} - {user_data['email']}", True, 
                                          f"Photo URL format correct: {photo_url}")
                            return photo_url
                        else:
                            self.log_result(f"/auth/me {user_data['role']} - {user_data['email']}", False, 
                                          f"Photo URL wrong role folder. Expected: {expected_role_folder}, Got: {photo_url}")
                            return None
                    else:
                        self.log_result(f"/auth/me {user_data['role']} - {user_data['email']}", False, 
                                      f"Photo URL wrong format. Expected: /photos/..., Got: {photo_url}")
                        return None
                else:
                    # Photo URL is null - this is acceptable
                    self.log_result(f"/auth/me {user_data['role']} - {user_data['email']}", True, 
                                  f"Photo URL is null (no photo assigned)")
                    return None
            else:
                self.log_result(f"/auth/me {user_data['role']} - {user_data['email']}", False, 
                              f"Request failed. Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_result(f"/auth/me {user_data['role']} - {user_data['email']}", False, f"Exception: {str(e)}")
            return None

    def test_photo_file_accessibility(self, user_data, photo_url):
        """Test that photo file is accessible via HTTP request"""
        if not photo_url:
            self.log_result(f"Photo Access {user_data['role']} - {user_data['email']}", True, 
                          "No photo URL to test (user has no photo)")
            return True
            
        try:
            # Test via direct backend access (localhost:8001) since external routing has issues
            backend_direct_url = f"http://localhost:8001{photo_url}"
            response = requests.get(backend_direct_url)
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get('content-type', '')
                if content_type.startswith('image/'):
                    self.log_result(f"Photo Access {user_data['role']} - {user_data['email']}", True, 
                                  f"Photo accessible with correct content-type: {content_type}")
                    return True
                else:
                    self.log_result(f"Photo Access {user_data['role']} - {user_data['email']}", False, 
                                  f"Wrong content-type. Expected: image/*, Got: {content_type}")
                    return False
            elif response.status_code == 404:
                self.log_result(f"Photo Access {user_data['role']} - {user_data['email']}", False, 
                              f"Photo file not found (404): {backend_direct_url}")
                return False
            else:
                self.log_result(f"Photo Access {user_data['role']} - {user_data['email']}", False, 
                              f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result(f"Photo Access {user_data['role']} - {user_data['email']}", False, f"Exception: {str(e)}")
            return False

    def test_photo_url_consistency(self, user_data, login_photo_url, me_photo_url):
        """Test that login and /auth/me return consistent photo URLs"""
        try:
            if login_photo_url == me_photo_url:
                self.log_result(f"Photo URL Consistency {user_data['role']} - {user_data['email']}", True, 
                              f"URLs consistent: {login_photo_url}")
                return True
            else:
                self.log_result(f"Photo URL Consistency {user_data['role']} - {user_data['email']}", False, 
                              f"URLs inconsistent. Login: {login_photo_url}, /auth/me: {me_photo_url}")
                return False
        except Exception as e:
            self.log_result(f"Photo URL Consistency {user_data['role']} - {user_data['email']}", False, f"Exception: {str(e)}")
            return False

    def test_static_file_serving_direct(self):
        """Test direct access to known photo files and non-existent files"""
        try:
            # Test known photo paths via direct backend access
            test_paths = [
                "/photos/admins/55b426f6-d039-4c7b-9b20-a4c09af39eec.jpg",  # Known admin photo
                "/photos/admins/fcdbb6fa-732a-4214-bf2a-d623ca5e6253.jpg",  # Known admin2 photo
                "/photos/teachers/6d0e882e-5161-4a95-a6ff-3f45f5ac3265.jpg",  # Known teacher photo
                "/photos/parents/f8bdc585-52a8-4d0f-8808-6a0393ecba61.jpg",  # Known parent photo
                "/photos/nonexistent/fake-photo.jpg"  # Non-existent photo (should return 404)
            ]
            
            for photo_path in test_paths:
                # Use direct backend access
                backend_url = f"http://localhost:8001{photo_path}"
                response = requests.get(backend_url)
                
                if photo_path.endswith("fake-photo.jpg"):
                    # This should return 404
                    if response.status_code == 404:
                        self.log_result(f"Direct Photo Access - Non-existent", True, 
                                      f"Correctly returned 404 for non-existent photo")
                    else:
                        self.log_result(f"Direct Photo Access - Non-existent", False, 
                                      f"Expected 404, got {response.status_code}")
                else:
                    # These should exist and return proper content-type
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        if content_type.startswith('image/'):
                            self.log_result(f"Direct Photo Access - {photo_path.split('/')[-1]}", True, 
                                          f"Photo exists with correct content-type: {content_type}")
                        else:
                            self.log_result(f"Direct Photo Access - {photo_path.split('/')[-1]}", False, 
                                          f"Wrong content-type: {content_type}")
                    elif response.status_code == 404:
                        self.log_result(f"Direct Photo Access - {photo_path.split('/')[-1]}", False, 
                                      f"Photo not found (404)")
                    else:
                        self.log_result(f"Direct Photo Access - {photo_path.split('/')[-1]}", False, 
                                      f"Unexpected status: {response.status_code}")
            
            return True
        except Exception as e:
            self.log_result("Direct Photo Access Tests", False, f"Exception: {str(e)}")
            return False

    def test_photo_url_conversion_logic(self):
        """Test the photo URL conversion logic by examining actual database vs API responses"""
        try:
            # Login as admin to get access to user data
            admin_response = requests.post(f"{API_BASE}/auth/login", json={
                "email": "admin@school.com",
                "password": "password"
            })
            
            if admin_response.status_code != 200:
                self.log_result("Photo URL Conversion Logic", False, "Could not login as admin")
                return False
            
            admin_cookies = admin_response.cookies
            
            # Get users data to check photo path conversion
            users_response = requests.get(f"{API_BASE}/users", cookies=admin_cookies)
            
            if users_response.status_code == 200:
                users = users_response.json()
                conversion_tests_passed = 0
                conversion_tests_total = 0
                
                for user in users:
                    if user.get('photo'):  # Only test users with photos
                        conversion_tests_total += 1
                        
                        # Login as this user to see the converted photo URL
                        user_login_response = requests.post(f"{API_BASE}/auth/login", json={
                            "email": user['email'],
                            "password": "password"  # Assuming all test users have same password
                        })
                        
                        if user_login_response.status_code == 200:
                            user_data = user_login_response.json()
                            api_photo_url = user_data.get('photo')
                            
                            # Check conversion logic
                            db_photo_path = user.get('photo', '')
                            
                            if db_photo_path.startswith('backend/'):
                                expected_url = '/' + db_photo_path[8:]  # Remove 'backend/' prefix
                            else:
                                expected_url = '/' + db_photo_path if not db_photo_path.startswith('/') else db_photo_path
                            
                            if api_photo_url == expected_url:
                                conversion_tests_passed += 1
                                self.log_result(f"Photo URL Conversion - {user['email']}", True, 
                                              f"Correct conversion: {db_photo_path} -> {api_photo_url}")
                            else:
                                self.log_result(f"Photo URL Conversion - {user['email']}", False, 
                                              f"Wrong conversion: {db_photo_path} -> {api_photo_url} (expected: {expected_url})")
                
                if conversion_tests_total > 0:
                    success_rate = (conversion_tests_passed / conversion_tests_total) * 100
                    self.log_result("Photo URL Conversion Logic Summary", conversion_tests_passed == conversion_tests_total, 
                                  f"Conversion tests: {conversion_tests_passed}/{conversion_tests_total} passed ({success_rate:.1f}%)")
                else:
                    self.log_result("Photo URL Conversion Logic Summary", True, 
                                  "No users with photos found to test conversion logic")
                
                return conversion_tests_passed == conversion_tests_total
            else:
                self.log_result("Photo URL Conversion Logic", False, f"Could not get users data: {users_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Photo URL Conversion Logic", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all profile photo display tests"""
        print("=" * 80)
        print("📸 PROFILE PHOTO DISPLAY TESTING - BUS TRACKER APPLICATION")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print()

        total_tests = 0
        passed_tests = 0
        
        # Test 1: Static File Serving Direct Access
        print("🧪 SCENARIO 1: Static File Serving Direct Access")
        print("-" * 60)
        total_tests += 1
        if self.test_static_file_serving_direct():
            passed_tests += 1
        print()
        
        # Test 2: Photo URL Conversion Logic
        print("🧪 SCENARIO 2: Photo URL Conversion Logic")
        print("-" * 60)
        total_tests += 1
        if self.test_photo_url_conversion_logic():
            passed_tests += 1
        print()
        
        # Test 3-7: User Role Photo Display Tests
        for user_data in self.test_users:
            print(f"🧪 SCENARIO: {user_data['role'].upper()} PHOTO DISPLAY - {user_data['email']}")
            print("-" * 60)
            
            # Test login photo URL
            total_tests += 1
            login_result = self.test_user_login_photo_url(user_data)
            if login_result:
                passed_tests += 1
                
                # Test /auth/me photo URL
                total_tests += 1
                me_photo_url = self.test_auth_me_photo_url(user_data, login_result['session'])
                if me_photo_url is not None or login_result['photo_url'] is None:
                    passed_tests += 1
                
                # Test photo URL consistency
                total_tests += 1
                if self.test_photo_url_consistency(user_data, login_result['photo_url'], me_photo_url):
                    passed_tests += 1
                
                # Test photo file accessibility
                total_tests += 1
                if self.test_photo_file_accessibility(user_data, login_result['photo_url']):
                    passed_tests += 1
            else:
                # If login failed, skip other tests for this user
                total_tests += 3  # Add the skipped tests to total
            
            print()
        
        # Summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("❌ FAILED TESTS DETAILS:")
            print("-" * 40)
            for test in failed_tests:
                print(f"• {test['test']}: {test['details']}")
            print()
        else:
            print("🎉 ALL TESTS PASSED!")
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    tester = PhotoDisplayTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 ALL PROFILE PHOTO DISPLAY TESTS PASSED!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please review the results above.")
        sys.exit(1)

if __name__ == "__main__":
    main()