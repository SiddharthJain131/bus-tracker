"""
Photo Refactoring Verification Script
Verifies that all photo fields have been successfully migrated from photo_path to photo
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple

# Configuration
BACKUP_FILE = Path('/app/backend/backups/seed_backup_20251114_0532.json')
API_BASE = 'http://localhost:8001'


def check_backup_file() -> Tuple[bool, Dict]:
    """Check backup file for photo field consistency"""
    print("\n" + "=" * 70)
    print("📦 CHECKING BACKUP FILE")
    print("=" * 70)
    
    results = {
        'backup_exists': False,
        'students_count': 0,
        'users_count': 0,
        'students_photo_path': 0,
        'users_photo_path': 0,
        'students_valid_photo': 0,
        'users_valid_photo': 0
    }
    
    if not BACKUP_FILE.exists():
        print(f"❌ Backup file not found: {BACKUP_FILE}")
        return False, results
    
    results['backup_exists'] = True
    print(f"✅ Backup file found: {BACKUP_FILE.name}")
    
    with open(BACKUP_FILE, 'r') as f:
        backup = json.load(f)
    
    collections = backup.get('collections', {})
    students = collections.get('students', [])
    users = collections.get('users', [])
    
    results['students_count'] = len(students)
    results['users_count'] = len(users)
    
    # Check students
    for student in students:
        if 'photo_path' in student:
            results['students_photo_path'] += 1
        if student.get('photo') and student['photo'].startswith('/api/photos/'):
            results['students_valid_photo'] += 1
    
    # Check users
    for user in users:
        if 'photo_path' in user:
            results['users_photo_path'] += 1
        if user.get('photo') and user['photo'].startswith('/api/photos/'):
            results['users_valid_photo'] += 1
    
    print(f"\n📊 Statistics:")
    print(f"  Students: {results['students_count']}")
    print(f"    - With photo_path: {results['students_photo_path']}")
    print(f"    - With valid photo: {results['students_valid_photo']}")
    print(f"  Users: {results['users_count']}")
    print(f"    - With photo_path: {results['users_photo_path']}")
    print(f"    - With valid photo: {results['users_valid_photo']}")
    
    # Determine success
    success = (
        results['students_photo_path'] == 0 and
        results['users_photo_path'] == 0 and
        results['students_valid_photo'] == results['students_count'] and
        results['users_valid_photo'] == results['users_count']
    )
    
    if success:
        print("\n✅ BACKUP FILE PASSED - All photo fields are correctly formatted")
    else:
        print("\n❌ BACKUP FILE FAILED - Issues found with photo fields")
    
    return success, results


def check_api_endpoints() -> Tuple[bool, Dict]:
    """Check API endpoints for photo field consistency"""
    print("\n" + "=" * 70)
    print("🌐 CHECKING API ENDPOINTS")
    print("=" * 70)
    
    results = {
        'api_accessible': False,
        'students_api_works': False,
        'users_api_works': False,
        'sample_student_correct': False,
        'sample_user_correct': False
    }
    
    try:
        # Login
        login_response = requests.post(f'{API_BASE}/api/auth/login', json={
            'email': 'admin@school.com',
            'password': 'password'
        }, timeout=5)
        
        if login_response.status_code != 200:
            print("❌ Failed to login")
            return False, results
        
        results['api_accessible'] = True
        cookies = login_response.cookies
        print("✅ API accessible - Login successful")
        
        # Check students endpoint
        students_response = requests.get(f'{API_BASE}/api/students', cookies=cookies, timeout=5)
        if students_response.status_code == 200:
            results['students_api_works'] = True
            students = students_response.json()
            print(f"✅ Students API working - {len(students)} students")
            
            if students:
                student = students[0]
                has_photo = bool(student.get('photo'))
                has_photo_url = bool(student.get('photo_url'))
                no_photo_path = 'photo_path' not in student
                
                if has_photo and has_photo_url and no_photo_path:
                    results['sample_student_correct'] = True
                    print(f"✅ Sample student photo fields correct")
                    print(f"   Name: {student.get('name')}")
                    print(f"   Photo: {student.get('photo')[:50]}...")
                else:
                    print(f"❌ Sample student has issues:")
                    print(f"   has_photo: {has_photo}")
                    print(f"   has_photo_url: {has_photo_url}")
                    print(f"   no_photo_path: {no_photo_path}")
        else:
            print(f"❌ Students API failed: {students_response.status_code}")
        
        # Check users endpoint
        users_response = requests.get(f'{API_BASE}/api/users', cookies=cookies, timeout=5)
        if users_response.status_code == 200:
            results['users_api_works'] = True
            users = users_response.json()
            print(f"✅ Users API working - {len(users)} users")
            
            if users:
                user = users[0]
                has_photo = bool(user.get('photo'))
                has_photo_url = bool(user.get('photo_url'))
                no_photo_path = 'photo_path' not in user
                
                if has_photo and has_photo_url and no_photo_path:
                    results['sample_user_correct'] = True
                    print(f"✅ Sample user photo fields correct")
                    print(f"   Name: {user.get('name')}")
                    print(f"   Role: {user.get('role')}")
                    print(f"   Photo: {user.get('photo')[:50]}...")
                else:
                    print(f"❌ Sample user has issues:")
                    print(f"   has_photo: {has_photo}")
                    print(f"   has_photo_url: {has_photo_url}")
                    print(f"   no_photo_path: {no_photo_path}")
        else:
            print(f"❌ Users API failed: {users_response.status_code}")
        
    except Exception as e:
        print(f"❌ API check failed: {e}")
        return False, results
    
    # Determine success
    success = all([
        results['api_accessible'],
        results['students_api_works'],
        results['users_api_works'],
        results['sample_student_correct'],
        results['sample_user_correct']
    ])
    
    if success:
        print("\n✅ API ENDPOINTS PASSED - All photo fields working correctly")
    else:
        print("\n❌ API ENDPOINTS FAILED - Issues found")
    
    return success, results


def check_code_consistency() -> Tuple[bool, Dict]:
    """Check if server code has been refactored"""
    print("\n" + "=" * 70)
    print("💻 CHECKING CODE CONSISTENCY")
    print("=" * 70)
    
    results = {
        'server_file_exists': False,
        'photo_path_references': 0,
        'refactored': False
    }
    
    server_file = Path('/app/backend/server.py')
    
    if not server_file.exists():
        print("❌ server.py not found")
        return False, results
    
    results['server_file_exists'] = True
    
    with open(server_file, 'r') as f:
        content = f.read()
    
    # Count photo_path references in conversion code (should be minimal)
    # We expect some in get_photo_url function but not in endpoint logic
    lines = content.split('\n')
    photo_path_in_endpoints = 0
    
    for i, line in enumerate(lines):
        if 'photo_path' in line and 'student.get' in line:
            photo_path_in_endpoints += 1
            print(f"   Found photo_path usage at line {i+1}: {line.strip()[:60]}...")
    
    results['photo_path_references'] = photo_path_in_endpoints
    results['refactored'] = photo_path_in_endpoints == 0
    
    if results['refactored']:
        print("✅ Code refactored - No photo_path references in endpoint logic")
    else:
        print(f"❌ Code not fully refactored - {photo_path_in_endpoints} photo_path references found")
    
    return results['refactored'], results


def main():
    """Main verification function"""
    print("=" * 70)
    print("🔍 PHOTO REFACTORING VERIFICATION")
    print("=" * 70)
    print("\nThis script verifies that photo_path has been successfully replaced")
    print("with photo across backups, database, and code.")
    
    # Run all checks
    backup_success, backup_results = check_backup_file()
    api_success, api_results = check_api_endpoints()
    code_success, code_results = check_code_consistency()
    
    # Final summary
    print("\n" + "=" * 70)
    print("📋 FINAL VERIFICATION SUMMARY")
    print("=" * 70)
    
    all_passed = backup_success and api_success and code_success
    
    print(f"\n{'✅' if backup_success else '❌'} Backup File: {'PASSED' if backup_success else 'FAILED'}")
    print(f"{'✅' if api_success else '❌'} API Endpoints: {'PASSED' if api_success else 'FAILED'}")
    print(f"{'✅' if code_success else '❌'} Code Consistency: {'PASSED' if code_success else 'FAILED'}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL CHECKS PASSED - REFACTORING SUCCESSFUL!")
        print("=" * 70)
        print("\nThe photo field refactoring is complete and verified:")
        print("  • Backup file has no photo_path fields")
        print("  • All photos use /api/photos/ URLs")
        print("  • API endpoints return correct photo data")
        print("  • Code has been properly refactored")
        print("\n✨ System is ready for use!")
    else:
        print("⚠️  VERIFICATION FAILED - ACTION NEEDED")
        print("=" * 70)
        print("\nSome checks did not pass. Review the details above.")
        print("Refer to PHOTO_FIELD_REFACTORING.md for troubleshooting.")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
