#!/usr/bin/env python3
"""
Populate Missing Photos Script
Downloads photos for existing attendance records that are missing them.
"""

import json
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

# Constants
BACKEND_DIR = Path(__file__).parent
BACKUPS_DIR = BACKEND_DIR / "backups"
ATTENDANCE_BACKUP_DIR = BACKUPS_DIR / "attendance"
PHOTOS_DIR = BACKEND_DIR / "photos" / "students"
ATTENDANCE_BACKUP_FILE = ATTENDANCE_BACKUP_DIR / "attendance_backup_20251114_0532.json"

# Photo generation settings
PHOTO_SOURCE_URL = "https://thispersondoesnotexist.com/"
RETRY_DELAY = 2  # seconds between photo downloads

def download_photo(save_path: Path) -> bool:
    """Download a photo from thispersondoesnotexist.com"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(PHOTO_SOURCE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        print(f"   ⚠️  Failed: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("  📸 POPULATE MISSING PHOTOS FOR EXISTING ATTENDANCE RECORDS")
    print("="*70)
    
    # Load attendance backup
    print("\n📖 Loading attendance backup...")
    with open(ATTENDANCE_BACKUP_FILE, 'r') as f:
        backup_data = json.load(f)
    
    records = backup_data['collections']['attendance']
    print(f"   ✅ Found {len(records)} attendance records")
    
    # Find records without photos
    records_without_photos = [r for r in records if not r.get('scan_photo')]
    print(f"   ℹ️  Records without photos: {len(records_without_photos)}")
    
    if not records_without_photos:
        print("\n✅ All records already have photos!")
        return
    
    # Process records
    print(f"\n📸 Downloading photos for {len(records_without_photos)} records...")
    photo_count = 0
    
    for i, record in enumerate(records_without_photos, 1):
        student_id = record['student_id']
        date = record['date']
        trip = record['trip']
        status = record['status']
        
        # Create photo filename
        photo_filename = f"{date}_{trip}_{status}.jpg"
        attendance_dir = PHOTOS_DIR / student_id / "attendance"
        photo_path = attendance_dir / photo_filename
        
        # Check if photo already exists
        if photo_path.exists():
            photo_url = f"/photos/students/{student_id}/attendance/{photo_filename}"
            record['scan_photo'] = photo_url
            if not record.get('scan_timestamp'):
                record['scan_timestamp'] = record['last_update']
            continue
        
        # Download photo
        print(f"   [{i}/{len(records_without_photos)}] {date} {trip} ({status})...")
        success = download_photo(photo_path)
        
        if success:
            photo_count += 1
            photo_url = f"/photos/students/{student_id}/attendance/{photo_filename}"
            record['scan_photo'] = photo_url
            if not record.get('scan_timestamp'):
                record['scan_timestamp'] = record['last_update']
            
            # Small delay to avoid rate limiting
            if i < len(records_without_photos):
                time.sleep(RETRY_DELAY)
    
    print(f"\n   ✅ Downloaded {photo_count} new photos")
    
    # Update backup
    print("\n💾 Updating attendance backup...")
    backup_data['timestamp'] = datetime.now(timezone.utc).isoformat()
    
    with open(ATTENDANCE_BACKUP_FILE, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"   ✅ Attendance backup updated")
    
    print("\n" + "="*70)
    print("  ✅ MISSING PHOTOS POPULATION COMPLETED")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"   • Photos downloaded: {photo_count}")
    print(f"   • Total records: {len(records)}")
    print(f"   • Records with photos: {len([r for r in records if r.get('scan_photo')])}")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
