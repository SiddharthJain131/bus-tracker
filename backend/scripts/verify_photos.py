#!/usr/bin/env python3
"""
Quick verification script to check photo structure integrity
"""

import os
from pathlib import Path
from PIL import Image

PHOTOS_DIR = Path("/app/backend/photos")

def verify_photos():
    print("=" * 70)
    print("PHOTO STRUCTURE VERIFICATION")
    print("=" * 70)
    print()
    
    stats = {
        'admins': 0,
        'teachers': 0,
        'parents': 0,
        'students': 0,
        'attendance': 0,
        'corrupted': 0
    }
    
    # Check admins
    admin_dir = PHOTOS_DIR / 'admins'
    if admin_dir.exists():
        for photo in admin_dir.glob('*.jpg'):
            try:
                img = Image.open(photo)
                img.verify()
                stats['admins'] += 1
            except Exception as e:
                print(f"✗ Corrupted admin photo: {photo.name}")
                stats['corrupted'] += 1
    
    # Check teachers
    teacher_dir = PHOTOS_DIR / 'teachers'
    if teacher_dir.exists():
        for photo in teacher_dir.glob('*.jpg'):
            try:
                img = Image.open(photo)
                img.verify()
                stats['teachers'] += 1
            except Exception as e:
                print(f"✗ Corrupted teacher photo: {photo.name}")
                stats['corrupted'] += 1
    
    # Check parents
    parent_dir = PHOTOS_DIR / 'parents'
    if parent_dir.exists():
        for photo in parent_dir.glob('*.jpg'):
            try:
                img = Image.open(photo)
                img.verify()
                stats['parents'] += 1
            except Exception as e:
                print(f"✗ Corrupted parent photo: {photo.name}")
                stats['corrupted'] += 1
    
    # Check students
    student_dir = PHOTOS_DIR / 'students'
    if student_dir.exists():
        for student_folder in student_dir.iterdir():
            if student_folder.is_dir():
                # Check profile
                profile = student_folder / 'profile.jpg'
                if profile.exists():
                    try:
                        img = Image.open(profile)
                        img.verify()
                        stats['students'] += 1
                    except Exception as e:
                        print(f"✗ Corrupted student profile: {student_folder.name}")
                        stats['corrupted'] += 1
                
                # Check attendance photos
                attendance_dir = student_folder / 'attendance'
                if attendance_dir.exists():
                    for photo in attendance_dir.glob('*.jpg'):
                        try:
                            img = Image.open(photo)
                            img.verify()
                            stats['attendance'] += 1
                        except Exception as e:
                            print(f"✗ Corrupted attendance photo: {photo.name}")
                            stats['corrupted'] += 1
    
    # Print summary
    print("Summary:")
    print(f"  Admins:     {stats['admins']} photos")
    print(f"  Teachers:   {stats['teachers']} photos")
    print(f"  Parents:    {stats['parents']} photos")
    print(f"  Students:   {stats['students']} profiles")
    print(f"  Attendance: {stats['attendance']} photos")
    print(f"  Corrupted:  {stats['corrupted']} files")
    print()
    
    total = sum([stats[k] for k in ['admins', 'teachers', 'parents', 'students', 'attendance']])
    print(f"Total valid photos: {total}")
    
    if stats['corrupted'] == 0:
        print("✅ All photos are valid!")
    else:
        print(f"⚠️  {stats['corrupted']} corrupted files found")
    
    print("=" * 70)
    
    return stats['corrupted'] == 0

if __name__ == "__main__":
    success = verify_photos()
    exit(0 if success else 1)
