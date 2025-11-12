"""
Integrated Scheduled Seeder with Smart Backup
Automatically runs backup + seeding cycles at configurable intervals
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add backend directory to path for imports
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / '.env')

# Import backup and seed functions
from backup_seed_data import create_backup, client as backup_client
from seed_data import seed_data, client as seed_client

# Configuration from environment
AUTO_SEED_ENABLE = os.environ.get('AUTO_SEED_ENABLE', 'false').lower() == 'true'
SEED_INTERVAL_HOURS = int(os.environ.get('SEED_INTERVAL_HOURS', '24'))
BACKUP_LIMIT = int(os.environ.get('BACKUP_LIMIT', '3'))

# Logging directory
LOGS_DIR = ROOT_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)


def log_message(message: str, level: str = "INFO"):
    """Print and log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    
    # Append to log file
    try:
        log_file = LOGS_DIR / 'seeder.log'
        with open(log_file, 'a') as f:
            f.write(log_line + '\n')
    except Exception as e:
        print(f"Warning: Failed to write to log file: {e}")


async def run_backup_and_seed_cycle():
    """Execute one complete backup + seed cycle"""
    cycle_start = datetime.now()
    log_message("=" * 60)
    log_message("🔁 Starting Backup & Seed Cycle")
    log_message("=" * 60)
    
    try:
        # Step 1: Run backup with rotation
        log_message("🔁 Running backup rotation", "INFO")
        try:
            backup_filename = await create_backup()
            log_message(f"📦 Backup created: {backup_filename}", "SUCCESS")
        except Exception as e:
            log_message(f"Backup failed: {e}", "ERROR")
            log_message("⚠️  Continuing with seeding despite backup failure...", "WARNING")
        
        # Step 2: Run seeding (will auto-restore from latest backup)
        log_message("\n🌱 Starting seeding process", "INFO")
        try:
            await seed_data()
            log_message("✅ Seeding completed successfully", "SUCCESS")
        except Exception as e:
            log_message(f"Seeding failed: {e}", "ERROR")
            raise
        
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        log_message("=" * 60)
        log_message(f"✅ Cycle completed in {cycle_duration:.2f} seconds")
        log_message("=" * 60)
        
        return True
        
    except Exception as e:
        log_message(f"Cycle failed with error: {e}", "ERROR")
        return False


async def scheduled_seeder_loop():
    """Main loop that runs backup + seed cycles at intervals"""
    log_message("\n" + "=" * 60)
    log_message("🚀 SCHEDULED SEEDER SERVICE STARTED")
    log_message("=" * 60)
    log_message(f"Configuration:")
    log_message(f"   • Auto-Seed Enabled: {AUTO_SEED_ENABLE}")
    log_message(f"   • Interval: {SEED_INTERVAL_HOURS} hour(s)")
    log_message(f"   • Backup Limit: {BACKUP_LIMIT} file(s)")
    
    if not AUTO_SEED_ENABLE:
        log_message("\n⚠️  AUTO_SEED_ENABLE is false - service will not run", "WARNING")
        log_message("   To enable, set AUTO_SEED_ENABLE=true in .env")
        return
    
    cycle_count = 0
    
    while True:
        try:
            cycle_count += 1
            log_message(f"\n🔄 Cycle #{cycle_count} started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            success = await run_backup_and_seed_cycle()
            
            if success:
                log_message(f"✅ Cycle #{cycle_count} completed successfully")
            else:
                log_message(f"⚠️  Cycle #{cycle_count} completed with errors", "WARNING")
            
            # Calculate next run time
            interval_seconds = SEED_INTERVAL_HOURS * 3600
            next_run = datetime.now().timestamp() + interval_seconds
            next_run_str = datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S')
            
            log_message(f"\n⏰ Next cycle scheduled for: {next_run_str} (in {SEED_INTERVAL_HOURS} hour(s))")
            log_message("   Press Ctrl+C to stop the service")
            
            # Sleep until next cycle
            await asyncio.sleep(interval_seconds)
            
        except KeyboardInterrupt:
            log_message("\n🛑 Service stopped by user (Ctrl+C)", "INFO")
            break
        except Exception as e:
            log_message(f"Unexpected error in loop: {e}", "ERROR")
            log_message("⏰ Retrying in 5 minutes...", "INFO")
            await asyncio.sleep(300)  # Wait 5 minutes before retrying


async def run_manual_cycle():
    """Run a single backup + seed cycle (for manual triggering)"""
    log_message("\n🔧 MANUAL CYCLE TRIGGERED")
    success = await run_backup_and_seed_cycle()
    
    if success:
        log_message("\n✅ Manual cycle completed successfully")
    else:
        log_message("\n❌ Manual cycle failed", "ERROR")
    
    return success


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scheduled Seeder with Smart Backup')
    parser.add_argument(
        '--manual',
        action='store_true',
        help='Run a single cycle manually instead of starting the scheduler'
    )
    
    args = parser.parse_args()
    
    try:
        if args.manual:
            # Manual mode: run once and exit
            await run_manual_cycle()
        else:
            # Scheduled mode: run continuously
            await scheduled_seeder_loop()
    finally:
        # Clean up connections
        backup_client.close()
        seed_client.close()
        log_message("\n👋 Connections closed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Seeder service stopped")
