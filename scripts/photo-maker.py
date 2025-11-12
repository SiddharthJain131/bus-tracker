"""
Download 18+ AI-generated placeholder faces for Bus Tracker testing.
Images come from https://thispersondoesnotexist.com/ (safe, synthetic).
"""

import os
import requests
from pathlib import Path
from time import sleep

# === Configuration ===
OUTPUT_DIR = Path(__file__).parent.parent / "backend/photos"
COUNT = 30                      # number of photos to download
BASE_URL = "https://thispersondoesnotexist.com/"
FILENAME_TEMPLATE = "STU{:03d}.jpg"
DELAY_SEC = 2                   # polite delay between requests

# === Ensure directory exists ===
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"📸 Downloading {COUNT} test student photos...")
for i in range(1, COUNT + 1):
    filename = os.path.join(OUTPUT_DIR, FILENAME_TEMPLATE.format(i))
    try:
        response = requests.get(BASE_URL, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"✅ Saved {filename}")
        else:
            print(f"⚠️  Failed ({response.status_code}) for {filename}")
    except Exception as e:
        print(f"❌ Error for {filename}: {e}")
    sleep(DELAY_SEC)

print("\nAll done! Photos stored in:", OUTPUT_DIR)
print("You can now map these to your student records.")
