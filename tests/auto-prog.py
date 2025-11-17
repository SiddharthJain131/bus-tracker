import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import subprocess
import time
import os
import sys
import csv
from datetime import datetime
import re

LOG_FILE = "rfid_log.csv"

# --- RFID GPIO Configuration ---
LED_SCAN = 22
BIN0 = 23
BIN1 = 24
BIN2 = 25
BINARY_PINS = [BIN0, BIN1, BIN2]

# --- ADB Configuration ---
DEVICE_IP = "172.17.72.186"
#DEVICE_IP = "192.0.0.4"
DEVICE_ID = f"{DEVICE_IP}:5555"
PHOTO_AGE_LIMIT = 20
MAX_RETRIES = 5
SLEEP_TIME = 5
DEST_FOLDER = "./photos"

# --- Global Variables ---
stored_uids = []
counter = 0
reader = SimpleMFRC522()

def setup_gpio():
    """Initializes GPIO pins for RFID and LEDs."""
    GPIO.cleanup()
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_SCAN, GPIO.OUT)
    for pin in BINARY_PINS:
        GPIO.setup(pin, GPIO.OUT)
    default_state()
    print("RFID Binary Counter Scanner Ready!")

def default_state():
    """Turns off all LEDs."""
    GPIO.output(LED_SCAN, GPIO.LOW)
    for pin in BINARY_PINS:
        GPIO.output(pin, GPIO.LOW)

def display_binary(value):
    """Displays a 3-bit number on the binary LEDs."""
    for i in range(len(BINARY_PINS)):
        if (value >> i) & 1:
            GPIO.output(BINARY_PINS[i], GPIO.HIGH)
        else:
            GPIO.output(BINARY_PINS[i], GPIO.LOW)

def adb_connect(ip):
    """Connect to ADB device over network."""
    print(f"Connecting to ADB device {ip}...")
    subprocess.run(["adb", "connect", f"{ip}:5555"], check=True)
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
    if f"{ip}:5555" not in result.stdout or "device" not in result.stdout.split(f"{ip}:5555")[-1]:
        input(f"ADB device {ip} not found or offline!")
        exit(1)
    print("ADB device connected!")

def adb(cmd):
    """Run an ADB command and return its output."""
    full_cmd = ["adb", "-s", DEVICE_ID] + cmd
    result = subprocess.run(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.stderr:
        print(f"ADB error: {result.stderr.strip()}")
    return result.stdout.strip()

def take_photo():
    """Trigger Android camera shutter."""
    print("Triggering Android camera...")
    adb(["shell", "input", "keyevent", "27"])
    time.sleep(2)

def get_recent_photo():
    """Get newest photo file name."""
    output = adb(["shell", "ls", "-t", "/storage/emulated/0/DCIM/Camera/"])
    if not output:
        return None
    return output.splitlines()[0].strip()

def get_file_age(file_path):
    """Calculate file age in seconds."""
    curr_time = int(time.time())
    file_mod_time = int(adb(["shell", "stat", "-c", "%Y", file_path]))
    return curr_time - file_mod_time

def pull_recent_photo():
    """Take photo and pull it from device if recent enough."""
    os.makedirs(DEST_FOLDER, exist_ok=True)
    retry_count = 0

    while retry_count < MAX_RETRIES:
        take_photo()
        recent_file = get_recent_photo()
        if not recent_file:
            print("No photo found on device.")
            retry_count += 1
            time.sleep(SLEEP_TIME)
            continue

        file_path = f"/storage/emulated/0/DCIM/Camera/{recent_file}"
        age = get_file_age(file_path)
        print(f"File: {recent_file}, Age: {age} seconds")

        if age < PHOTO_AGE_LIMIT:
            print("Recent photo detected, pulling...")
            adb(["pull", file_path, DEST_FOLDER])
            adb(["shell", "rm", file_path])
            return True, recent_file

        print(f"No recent photo, retrying in {SLEEP_TIME} seconds...")
        retry_count += 1
        time.sleep(SLEEP_TIME)

    print(f"No photo less than {PHOTO_AGE_LIMIT} seconds old found after {MAX_RETRIES} retries.")
    return False, None

def get_latest_location_via_adb():
    try:
        # Run adb shell dumpsys location command
        result = subprocess.run(
            ['adb', 'shell', 'dumpsys', 'location'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        output = result.stdout
        
        # Find all lines containing "last location=Location" but not "null"
        locations = re.findall(r'last location=Location\[([^\]]+)\]', output)
        valid_locations = [loc for loc in locations if 'null' not in loc]
        
        if not valid_locations:
            return None, None
        
        # Take the last (latest) valid location
        latest_loc = valid_locations[-1]
        
        # Regex to extract latitude and longitude from location string
        match = re.search(r'([-\d.]+),([-\d.]+)', latest_loc)
        
        if match:
            latitude = float(match.group(1))
            longitude = float(match.group(2))
            return latitude, longitude
        else:
            return None, None
    
    except subprocess.CalledProcessError as e:
        print("ADB command failed:", e)
        return None, None
    
def log_scan_event(uid, action, counter_value, photo_name=""):
    """Log an RFID scan event with optional photo name and current location."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    latitude, longitude = get_latest_location_via_adb()
    
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, uid, action, counter_value, photo_name, latitude, longitude])
        
def log_system_event(event):
    """Log system-level events like START or END."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, "SYSTEM", event, ""])
        
def main():
    """Main program loop."""
    global counter
    
    # Initialize systems
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "UID", "Action", "Count", "Photo"])
    setup_gpio()
    adb_connect(DEVICE_IP)
    log_system_event("START")
    print("---------------------------------")
    print("System ready. Waiting for RFID scans...")
    
    try:
        while True:
            # Turn on scan LED
            GPIO.output(LED_SCAN, GPIO.HIGH)
            
            # Wait for RFID card (blocking call)
            uid, text = reader.read()
            
            # Turn off scan LED
            GPIO.output(LED_SCAN, GPIO.LOW)
            
            print(f"Card Scanned: {uid}")
            photo = None
            if uid in stored_uids:
                stored_uids.remove(uid)
                counter -= 1
                action = "OUT"
                print("Card removed.")
            else:
                stored_uids.append(uid)
                counter += 1
                action = "IN"
                print("Card added. Taking photo...")

                success, photo = pull_recent_photo()
                if success:
                    print("Photo captured and saved successfully.")
                else:
                    print("Photo capture failed.")
            
            # Ensure counter doesn't go below zero
            if counter < 0:
                counter = 0
            
            # Log the event
            log_scan_event(uid, action, counter, photo)
            print(f"Total cards: {counter}")
            display_binary(counter)
            print("\nReady for next scan...")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        err_msg = f"Runtime error: {str(e)}"
        input(err_msg)
    finally:
        log_system_event("END")
        GPIO.cleanup()

if __name__ == "__main__":
    main()
    
