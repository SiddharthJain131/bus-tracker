#!/usr/bin/env python3
"""
Script to generate face embeddings for all students and store them in the seed backup file.
Run this before starting the backend to ensure all students have embeddings in the seed data.
"""

import json
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
import asyncio
import base64
import numpy as np
from deepface import DeepFace
import cv2

ROOT_DIR = Path(__file__).parent
BACKUP_DIR = ROOT_DIR / 'backups'
PHOTO_DIR = ROOT_DIR / 'photos'


async def generate_face_embedding(image_path):
    """Generate face embedding from image using DeepFace."""
    try:
        if not image_path.exists():
            return {"success": False, "embedding": None, "message": "Photo file not found"}
        
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            return {"success": False, "embedding": None, "message": "Could not read image file"}
        
        # Generate embedding using DeepFace
        embedding_objs = DeepFace.represent(
            img_path=img,
            model_name="Facenet",
            enforce_detection=True,
            detector_backend="opencv"
        )
        
        if not embedding_objs or len(embedding_objs) == 0:
            return {"success": False, "embedding": None, "message": "No face detected in image"}
        
        if len(embedding_objs) > 1:
            print(f"    ⚠️  Multiple faces detected ({len(embedding_objs)}), using first face")
        
        # Get the first face's embedding
        embedding_vector = embedding_objs[0]['embedding']
        
        # Convert to base64 for storage
        embedding_array = np.array(embedding_vector, dtype=np.float32)
        embedding_bytes = embedding_array.tobytes()
        embedding_b64 = base64.b64encode(embedding_bytes).decode('utf-8')
        
        return {
            "success": True,
            "embedding": embedding_b64,
            "message": f"Successfully generated embedding (dimension: {len(embedding_vector)})"
        }
        
    except ValueError as e:
        error_msg = str(e)
        if "Face could not be detected" in error_msg or "no face" in error_msg.lower():
            return {"success": False, "embedding": None, "message": "No face detected in image"}
        return {"success": False, "embedding": None, "message": f"Face detection error: {error_msg}"}
    except Exception as e:
        return {"success": False, "embedding": None, "message": f"Error: {str(e)}"}


def find_latest_seed_file():
    """Find the latest seed backup file."""
    seed_files = list(BACKUP_DIR.glob('seed_backup_*.json'))
    if not seed_files:
        print("❌ No seed backup files found")
        sys.exit(1)
    
    latest = max(seed_files, key=lambda p: p.stat().st_mtime)
    return latest


async def main():
    print("🔄 Starting embedding generation for seed file...")
    print("=" * 60)
    
    # Find latest seed file
    seed_file = find_latest_seed_file()
    print(f"📁 Using seed file: {seed_file.name}")
    
    # Create backup of current seed file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = seed_file.parent / f"{seed_file.stem}_backup_{timestamp}.json"
    shutil.copy2(seed_file, backup_file)
    print(f"💾 Backup created: {backup_file.name}")
    
    # Load seed data
    with open(seed_file, 'r') as f:
        seed_data = json.load(f)
    
    students = seed_data.get('collections', {}).get('students', [])
    print(f"👥 Found {len(students)} students in seed file")
    print("=" * 60)
    
    # Process each student
    successful = 0
    failed = 0
    skipped = 0
    
    for idx, student in enumerate(students, 1):
        student_id = student.get('student_id')
        student_name = student.get('name', 'Unknown')
        photo_url = student.get('photo', '')
        
        print(f"\n[{idx}/{len(students)}] {student_name} ({student_id})")
        
        # Check if already has embedding
        if student.get('embedding'):
            print(f"    ⏭️  Already has embedding, skipping")
            skipped += 1
            continue
        
        # Check if has photo
        if not photo_url:
            print(f"    ⚠️  No photo URL, storing null")
            student['embedding'] = None
            failed += 1
            continue
        
        # Convert photo URL to file path
        if photo_url.startswith('/api/photos/'):
            photo_path = PHOTO_DIR / photo_url.replace('/api/photos/', '')
        elif photo_url.startswith('/photos/'):
            photo_path = PHOTO_DIR / photo_url.replace('/photos/', '')
        else:
            photo_path = PHOTO_DIR / photo_url
        
        # Generate embedding
        result = await generate_face_embedding(photo_path)
        
        if result['success']:
            student['embedding'] = result['embedding']
            print(f"    ✅ {result['message']}")
            successful += 1
        else:
            student['embedding'] = None
            print(f"    ❌ {result['message']}")
            failed += 1
    
    # Save updated seed data
    with open(seed_file, 'w') as f:
        json.dump(seed_data, f, indent=2)
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⏭️  Skipped: {skipped}")
    print(f"   📝 Total: {len(students)}")
    print("=" * 60)
    print(f"💾 Updated seed file: {seed_file.name}")
    print(f"🔙 Backup available: {backup_file.name}")
    print("✨ Done!")


if __name__ == '__main__':
    asyncio.run(main())
