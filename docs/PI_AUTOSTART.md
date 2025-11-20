# Bus Tracker Pi - Auto-Start Configuration Guide

## Overview

This guide covers the automatic startup configuration for the Bus Tracker Raspberry Pi scanner service. The service starts automatically on boot, restarts on failure, and provides comprehensive logging and monitoring capabilities.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Service Management](#service-management)
4. [Monitoring](#monitoring)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Configuration](#advanced-configuration)
7. [Log Management](#log-management)

---

## Quick Start

### One-Command Installation

```bash
cd /app/tests
sudo ./install-service.sh install
```

This single command will:
- ✅ Install the systemd service
- ✅ Enable auto-start on boot
- ✅ Start the service immediately
- ✅ Configure logging
- ✅ Set up automatic restart on failure

### Verify Installation

```bash
sudo systemctl status bus-tracker-pi
```

---

## Installation

### Prerequisites

Before installing, ensure:

1. **Environment configured**: `.env` file exists in `/app/tests/`
2. **Dependencies installed**: Run `pip3 install -r pi_requirements.txt`
3. **Hardware connected**: RFID reader, LEDs, etc.
4. **Network available**: Internet connection for backend communication

### Step-by-Step Installation

#### 1. Prepare Environment File

Create or verify `/app/tests/.env`:

```bash
nano /app/tests/.env
```

Required contents:
```env
BACKEND_URL=http://your-backend-url.com:8001
DEVICE_ID=your-device-id-here
DEVICE_NAME=Pi-Bus-001
BUS_NUMBER=BUS-001
API_KEY=your-64-char-api-key-here
REGISTERED_AT=2025-01-01T00:00:00Z
PI_MODE=hardware
```

#### 2. Install Python Dependencies

```bash
cd /app/tests
pip3 install -r pi_requirements.txt
```

#### 3. Test Script Manually (Optional)

Before installing the service, test the script manually:

```bash
cd /app/tests
export PI_MODE=hardware
python3 pi_server.py
```

Press Ctrl+C to stop after verifying it works.

#### 4. Install Service

```bash
cd /app/tests
sudo ./install-service.sh install
```

Expected output:
```
=====================================================================
INSTALLING BUS TRACKER PI SERVICE
=====================================================================
→ Running pre-installation checks...
✓ .env file found
✓ Service file found
✓ Log directory created
→ Installing service file...
✓ Service file installed to /etc/systemd/system/bus-tracker-pi.service
→ Reloading systemd daemon...
✓ Systemd daemon reloaded
→ Enabling service to start on boot...
✓ Service enabled
→ Starting service...
✓ Service is running

=====================================================================
INSTALLATION COMPLETE
=====================================================================
```

#### 5. Verify Service is Running

```bash
sudo systemctl status bus-tracker-pi
```

Should show:
```
● bus-tracker-pi.service - Bus Tracker Raspberry Pi Boarding Scanner
   Loaded: loaded (/etc/systemd/system/bus-tracker-pi.service; enabled)
   Active: active (running) since ...
```

---

## Service Management

### Basic Commands

| Command | Description |
|---------|-------------|
| `sudo systemctl start bus-tracker-pi` | Start the service |
| `sudo systemctl stop bus-tracker-pi` | Stop the service |
| `sudo systemctl restart bus-tracker-pi` | Restart the service |
| `sudo systemctl status bus-tracker-pi` | Check service status |
| `sudo systemctl enable bus-tracker-pi` | Enable auto-start on boot |
| `sudo systemctl disable bus-tracker-pi` | Disable auto-start on boot |

### Using Helper Scripts

#### Installation Script

```bash
# Install service
sudo ./install-service.sh install

# Uninstall service
sudo ./install-service.sh uninstall

# Show status
./install-service.sh status

# View logs
./install-service.sh logs

# Test configuration
./install-service.sh test
```

#### Monitoring Script

```bash
# Show dashboard
./monitor-service.sh dashboard

# Health check
./monitor-service.sh health

# Restart service
sudo ./monitor-service.sh restart

# Show info
./monitor-service.sh info

# Continuous monitoring (updates every 5s)
./monitor-service.sh watch
```

---

## Monitoring

### Real-Time Dashboard

View live service status:

```bash
./monitor-service.sh dashboard
```

Output:
```
═══════════════════════════════════════════════════════════════════
BUS TRACKER PI - SERVICE DASHBOARD
═══════════════════════════════════════════════════════════════════

📊 Service Status
─────────────────────────────────────────────────────────────────
Status:              ● RUNNING
Uptime:              2h 15m
Memory Usage:        145.2 MB
CPU Usage:           3.5%
Restarts (24h):      0
Errors (1h):         0

🔧 System Health
─────────────────────────────────────────────────────────────────
Network:             ✓ Online
GPIO:                ✓ Available
Backend:             ✓ Reachable (http://backend:8001)

📝 Recent Activity (last 5 entries)
─────────────────────────────────────────────────────────────────
  Nov 17 14:30:15 [OK] Location updated: BUS-001
  Nov 17 14:30:05 [OK] RFID scanned: RFID-123456
  Nov 17 14:30:00 [OK] Student verified
```

### Health Check

Run comprehensive diagnostics:

```bash
./monitor-service.sh health
```

Checks:
- ✅ Service running and enabled
- ✅ Environment file properly configured
- ✅ Python script syntax valid
- ✅ Network connectivity
- ✅ Backend reachability
- ✅ GPIO availability
- ✅ Recent error count

### View Logs

#### Live Log Monitoring

```bash
journalctl -u bus-tracker-pi -f
```

#### Recent Logs

```bash
# Last 50 lines
journalctl -u bus-tracker-pi -n 50

# Last hour
journalctl -u bus-tracker-pi --since "1 hour ago"

# Today's logs
journalctl -u bus-tracker-pi --since today

# Error logs only
journalctl -u bus-tracker-pi -p err
```

#### Export Logs

```bash
# Export to file
journalctl -u bus-tracker-pi --since "24 hours ago" > /tmp/pi-logs.txt

# Export in JSON format
journalctl -u bus-tracker-pi -o json > /tmp/pi-logs.json
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Service Won't Start

**Symptom**: `sudo systemctl start bus-tracker-pi` fails

**Diagnosis**:
```bash
sudo systemctl status bus-tracker-pi
journalctl -u bus-tracker-pi -n 50
```

**Common Causes**:

1. **Missing .env file**
   ```bash
   # Create .env file
   nano /app/tests/.env
   # Add required variables
   ```

2. **Python dependencies missing**
   ```bash
   pip3 install -r /app/tests/pi_requirements.txt
   ```

3. **Permission issues**
   ```bash
   sudo chown -R pi:pi /app/tests
   chmod +x /app/tests/pi_server.py
   ```

4. **Port already in use**
   ```bash
   # Check if another instance is running
   ps aux | grep pi_server
   # Kill if needed
   sudo pkill -f pi_server
   ```

#### Issue 2: Service Keeps Restarting

**Symptom**: Service status shows multiple restarts

**Diagnosis**:
```bash
./monitor-service.sh health
journalctl -u bus-tracker-pi -p err -n 100
```

**Common Causes**:

1. **Backend unreachable**
   - Check `BACKEND_URL` in `.env`
   - Verify network connection: `ping 8.8.8.8`
   - Test backend: `curl http://your-backend:8001/docs`

2. **Invalid API key**
   - Verify `API_KEY` in `.env`
   - Re-register device if needed

3. **Hardware errors (RFID, camera)**
   - Check hardware connections
   - Review GPIO initialization in logs

#### Issue 3: Service Not Starting on Boot

**Symptom**: Service is inactive after reboot

**Check if enabled**:
```bash
systemctl is-enabled bus-tracker-pi
```

**Enable if disabled**:
```bash
sudo systemctl enable bus-tracker-pi
```

**Test boot sequence**:
```bash
# Reboot and check
sudo reboot
# After reboot:
sudo systemctl status bus-tracker-pi
```

#### Issue 4: GPS Always Null

**Symptom**: Location updates show null coordinates

**Causes**:
1. **ADB device disconnected**
   ```bash
   adb devices
   adb connect <DEVICE_IP>:5555
   ```

2. **GPS disabled on Android**
   - Enable Location on Android device
   - Grant location permissions

3. **Hardware GPS not working**
   - Check GPS module connections
   - Verify GPS library: `pip3 show gpsd-py3`

#### Issue 5: High CPU or Memory Usage

**Diagnosis**:
```bash
./monitor-service.sh dashboard
# Check Memory Usage and CPU Usage
```

**Solutions**:
1. **Memory limit exceeded**
   - Edit service file: `sudo nano /etc/systemd/system/bus-tracker-pi.service`
   - Increase `MemoryLimit=512M` to `MemoryLimit=1G`
   - Reload: `sudo systemctl daemon-reload`
   - Restart: `sudo systemctl restart bus-tracker-pi`

2. **CPU overload**
   - Check for infinite loops in logs
   - Verify scan intervals are reasonable
   - Consider reducing face detection frequency

---

## Advanced Configuration

### Service File Customization

Edit service file:
```bash
sudo nano /etc/systemd/system/bus-tracker-pi.service
```

#### Key Configuration Options

**Restart Policy**:
```ini
[Service]
# Restart behavior
Restart=always              # always, on-failure, on-abnormal, on-abort, never
RestartSec=10              # Wait 10 seconds before restart

# Restart limits
StartLimitInterval=300     # 5 minutes
StartLimitBurst=5          # Max 5 restarts in interval
StartLimitAction=reboot    # Action after limit: reboot, none
```

**Resource Limits**:
```ini
[Service]
MemoryLimit=512M           # Maximum memory
CPUQuota=80%              # Maximum CPU usage
```

**Environment Variables**:
```ini
[Service]
Environment="LOG_LEVEL=DEBUG"
Environment="SCAN_INTERVAL=5"
```

**After editing, reload and restart**:
```bash
sudo systemctl daemon-reload
sudo systemctl restart bus-tracker-pi
```

### Network Dependencies

If backend is on same network, add dependency:

```ini
[Unit]
After=network-online.target bluetooth.target
Requires=network-online.target

# Wait for specific service
After=backend.service
```

### Custom Startup Delays

Add delay before starting:

```ini
[Service]
ExecStartPre=/bin/sleep 30
```

Or use systemd timers for scheduled startup.

---

## Log Management

### Log Rotation

Install logrotate configuration:

```bash
sudo cp bus-tracker-pi-logrotate /etc/logrotate.d/bus-tracker-pi
sudo chmod 644 /etc/logrotate.d/bus-tracker-pi
```

Configuration:
- **Daily rotation**
- **Keep 7 days** of logs
- **Compress** old logs
- **Monthly archive** of compressed logs

### Test Log Rotation

```bash
sudo logrotate -f /etc/logrotate.d/bus-tracker-pi
```

### Log Size Management

Check journal size:
```bash
journalctl --disk-usage
```

Limit journal size:
```bash
sudo nano /etc/systemd/journald.conf
```

Add:
```ini
[Journal]
SystemMaxUse=200M
SystemMaxFileSize=50M
```

Restart journald:
```bash
sudo systemctl restart systemd-journald
```

### Export and Archive Logs

```bash
# Create log archive
journalctl -u bus-tracker-pi --since "7 days ago" > /tmp/pi-logs-$(date +%Y%m%d).txt

# Compress archive
gzip /tmp/pi-logs-$(date +%Y%m%d).txt

# Move to archive location
sudo mkdir -p /var/log/bus-tracker/archive
sudo mv /tmp/pi-logs-*.txt.gz /var/log/bus-tracker/archive/
```

---

## Service Behavior

### Startup Sequence

1. **System Boot**
2. **Network initialization** (wait for network-online.target)
3. **Load environment** from `/app/tests/.env`
4. **Initialize hardware** (GPIO, RFID, Camera)
5. **Connect to backend** and verify authentication
6. **Start location updater** thread
7. **Enter main scanning loop**

### Restart Logic

**Automatic restart triggers**:
- Process crash or exception
- Segmentation fault
- Out of memory (within limits)
- Exit code != 0

**Restart behavior**:
1. Wait 10 seconds
2. Restart process
3. After 5 restarts in 5 minutes → reboot Pi

**Manual restart**:
```bash
sudo systemctl restart bus-tracker-pi
```

### Graceful Shutdown

On stop command:
1. Send SIGTERM to process
2. Process handles Ctrl+C (KeyboardInterrupt)
3. Cleanup hardware (GPIO, camera)
4. Wait up to 30 seconds for graceful exit
5. Force kill if not exited

---

## Integration with Existing Services

### Supervisor Compatibility

The systemd service is independent of supervisor:
- **Backend/Frontend**: Managed by supervisor (development)
- **Pi Scanner**: Managed by systemd (production on Pi)

### Backend Coordination

Ensure backend is accessible:
```bash
# Test backend connection
curl http://your-backend:8001/docs

# Test API with device key
curl -H "X-API-Key: YOUR_KEY" http://your-backend:8001/api/device/list
```

---

## Uninstallation

### Remove Service

```bash
sudo ./install-service.sh uninstall
```

This will:
- Stop the service
- Disable auto-start
- Remove service file
- Reload systemd

**Note**: Logs are preserved in `/var/log/bus-tracker/`

### Complete Cleanup

Remove all traces:
```bash
# Uninstall service
sudo ./install-service.sh uninstall

# Remove logs
sudo rm -rf /var/log/bus-tracker

# Remove logrotate config
sudo rm /etc/logrotate.d/bus-tracker-pi

# Remove environment (optional)
rm /app/tests/.env
```

---

## Best Practices

### 1. Regular Monitoring

Schedule weekly health checks:
```bash
# Add to crontab
crontab -e

# Run health check every Sunday at 2 AM
0 2 * * 0 /app/tests/monitor-service.sh health > /var/log/bus-tracker/health-$(date +\%Y\%m\%d).log
```

### 2. Backup Configuration

```bash
# Backup .env file
cp /app/tests/.env /app/tests/.env.backup-$(date +%Y%m%d)

# Backup service file
sudo cp /etc/systemd/system/bus-tracker-pi.service /root/bus-tracker-pi.service.backup
```

### 3. Update Procedure

When updating pi_server.py:

```bash
# Stop service
sudo systemctl stop bus-tracker-pi

# Update code
cd /app
git pull origin main

# Test manually
cd /app/tests
python3 pi_server.py
# Ctrl+C after verification

# Restart service
sudo systemctl start bus-tracker-pi

# Verify
./monitor-service.sh dashboard
```

### 4. Security

- **Protect API key**: Secure `.env` file permissions
  ```bash
  chmod 600 /app/tests/.env
  ```

- **Limit service permissions**: Service runs as `pi` user (non-root)

- **Monitor logs**: Check for unauthorized access attempts

### 5. Maintenance Schedule

| Frequency | Task |
|-----------|------|
| Daily | Check service status |
| Weekly | Review error logs |
| Monthly | Health check and log rotation |
| Quarterly | Backup configuration |
| Yearly | Update dependencies |

---

## Quick Reference

### Essential Commands

```bash
# Service management
sudo systemctl start bus-tracker-pi
sudo systemctl stop bus-tracker-pi
sudo systemctl restart bus-tracker-pi
sudo systemctl status bus-tracker-pi

# Logs
journalctl -u bus-tracker-pi -f                    # Follow live
journalctl -u bus-tracker-pi -n 50                 # Last 50 lines
journalctl -u bus-tracker-pi --since "1 hour ago"  # Last hour

# Monitoring
./monitor-service.sh dashboard    # Real-time dashboard
./monitor-service.sh health       # Health check
./monitor-service.sh watch        # Continuous monitoring

# Installation
sudo ./install-service.sh install      # Install
sudo ./install-service.sh uninstall    # Uninstall
./install-service.sh status            # Status
```

---

## Support and Documentation

### Related Documentation

- [README_PI_HARDWARE.md](./README_PI_HARDWARE.md) - Hardware setup guide
- [IMPLEMENTATION_SUMMARY.md](/app/IMPLEMENTATION_SUMMARY.md) - Implementation details
- [API_TEST_DEVICE.md](/app/docs/API_TEST_DEVICE.md) - Device API documentation

### Troubleshooting Resources

1. **System logs**: `journalctl -u bus-tracker-pi`
2. **Service status**: `systemctl status bus-tracker-pi`
3. **Health check**: `./monitor-service.sh health`
4. **Backend docs**: `http://your-backend:8001/docs`

---

**Last Updated**: November 17, 2025
**Version**: 1.0
**Raspberry Pi OS**: Debian 11/12 (Bullseye/Bookworm)
