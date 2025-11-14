"""
Attendance Monitor Daemon
Continuously monitors current day attendance records and marks as RED
when scans don't occur within the threshold time relative to expected stop arrival times.
"""

import asyncio
import os
import logging
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/backend/logs/attendance_monitor.log'),
        logging.StreamHandler()
    ]
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Configuration
RED_STATUS_THRESHOLD = int(os.environ.get('RED_STATUS_THRESHOLD', '10'))  # minutes
CHECK_INTERVAL = 60  # Check every 60 seconds


def parse_time(time_str: str) -> datetime.time:
    """Parse HH:MM format time string to time object"""
    if not time_str:
        return None
    try:
        hour, minute = map(int, time_str.split(':'))
        return datetime.now(timezone.utc).replace(hour=hour, minute=minute, second=0, microsecond=0).time()
    except Exception as e:
        logging.error(f"Failed to parse time {time_str}: {e}")
        return None


async def check_missed_scans():
    """
    Check for students who should have been scanned but weren't.
    Mark their attendance as RED if threshold exceeded.
    """
    current_time = datetime.now(timezone.utc)
    current_hour = current_time.hour
    today = current_time.strftime("%Y-%m-%d")
    
    # Determine current trip direction
    is_morning = current_hour < 12
    trip = "AM" if is_morning else "PM"
    
    logging.info(f"Checking missed scans for {today} {trip} trip (is_morning={is_morning})")
    
    # Get all students with their assigned routes and stops
    students_cursor = db.students.find({
        "stop_id": {"$exists": True, "$ne": None}
    })
    
    checked_count = 0
    marked_red_count = 0
    
    async for student in students_cursor:
        try:
            student_id = student['student_id']
            stop_id = student.get('stop_id')
            
            if not stop_id:
                continue
            
            # Get stop details with expected times
            stop = await db.stops.find_one({"stop_id": stop_id}, {"_id": 0})
            if not stop:
                continue
            
            # Get expected time based on trip direction
            expected_time_str = stop.get('morning_expected_time') if is_morning else stop.get('evening_expected_time')
            if not expected_time_str:
                # No expected time configured for this stop/direction, skip
                continue
            
            # Parse expected time
            expected_time = parse_time(expected_time_str)
            if not expected_time:
                continue
            
            # Calculate threshold time (expected time + threshold minutes)
            expected_datetime = datetime.combine(current_time.date(), expected_time)
            threshold_datetime = expected_datetime + timedelta(minutes=RED_STATUS_THRESHOLD)
            
            # Check if we're past the threshold
            if current_time < threshold_datetime:
                # Still within acceptable time window, skip
                continue
            
            checked_count += 1
            
            # Check if student has attendance record for today's trip
            attendance = await db.attendance.find_one({
                "student_id": student_id,
                "date": today,
                "trip": trip
            })
            
            if not attendance:
                # No scan at all - mark as RED
                # Create RED status attendance record
                from server import Attendance
                red_attendance = Attendance(
                    student_id=student_id,
                    date=today,
                    trip=trip,
                    status="red",
                    confidence=0.0,
                    last_update=current_time.isoformat()
                )
                await db.attendance.insert_one(red_attendance.model_dump())
                marked_red_count += 1
                logging.warning(f"Marked RED: Student {student_id} - No scan for {trip} trip (expected at {expected_time_str}, threshold passed at {threshold_datetime.strftime('%H:%M')})")
            
            elif attendance.get('status') == 'yellow':
                # Student scanned once but never completed second scan
                # Check if enough time has passed since first scan
                last_update = attendance.get('last_update')
                if last_update:
                    last_update_time = datetime.fromisoformat(last_update)
                    # If student has been "yellow" for longer than threshold, mark as RED
                    yellow_duration = (current_time - last_update_time).total_seconds() / 60  # minutes
                    
                    if yellow_duration > RED_STATUS_THRESHOLD:
                        await db.attendance.update_one(
                            {"student_id": student_id, "date": today, "trip": trip},
                            {"$set": {"status": "red", "last_update": current_time.isoformat()}}
                        )
                        marked_red_count += 1
                        logging.warning(f"Marked RED: Student {student_id} - Incomplete journey, yellow status for {yellow_duration:.1f} minutes (threshold: {RED_STATUS_THRESHOLD} min)")
            
            # If status is already 'green' or 'red', no action needed
            
        except Exception as e:
            logging.error(f"Error checking student {student.get('student_id')}: {e}")
            continue
    
    if marked_red_count > 0:
        logging.info(f"Scan check complete: {checked_count} students checked, {marked_red_count} marked RED")
    else:
        logging.debug(f"Scan check complete: {checked_count} students checked, no RED marks needed")


async def monitor_attendance():
    """Main monitoring loop"""
    logging.info("=" * 60)
    logging.info("🚨 ATTENDANCE MONITOR STARTED")
    logging.info("=" * 60)
    logging.info(f"Configuration:")
    logging.info(f"  • RED Status Threshold: {RED_STATUS_THRESHOLD} minutes")
    logging.info(f"  • Check Interval: {CHECK_INTERVAL} seconds")
    logging.info("=" * 60)
    
    while True:
        try:
            await check_missed_scans()
            await asyncio.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logging.info("\n🛑 Monitor stopped by user")
            break
        except Exception as e:
            logging.error(f"Monitor error: {e}")
            logging.info(f"Retrying in {CHECK_INTERVAL} seconds...")
            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        asyncio.run(monitor_attendance())
    except KeyboardInterrupt:
        logging.info("Monitor shutdown complete")
    finally:
        client.close()
