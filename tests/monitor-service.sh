#!/bin/bash
# =============================================================================
# Bus Tracker Pi - Service Monitoring Script
# =============================================================================
# This script provides real-time monitoring and health checks for the
# bus-tracker-pi service running on Raspberry Pi.
#
# Usage:
#   ./monitor-service.sh [dashboard|health|restart|info]
#
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

SERVICE_NAME="bus-tracker-pi"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
}

print_box() {
    local title="$1"
    local content="$2"
    echo -e "${BLUE}┌─ $title${NC}"
    echo -e "$content"
    echo -e "${BLUE}└────────────────────────────────────────────────────────────────${NC}"
}

get_service_status() {
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}● RUNNING${NC}"
        return 0
    else
        echo -e "${RED}● STOPPED${NC}"
        return 1
    fi
}

get_uptime() {
    local status
    status=$(systemctl show "$SERVICE_NAME" -p ActiveEnterTimestamp --value)
    if [[ -n "$status" && "$status" != "n/a" ]]; then
        local start_time=$(date -d "$status" +%s)
        local current_time=$(date +%s)
        local uptime_seconds=$((current_time - start_time))
        
        local days=$((uptime_seconds / 86400))
        local hours=$(((uptime_seconds % 86400) / 3600))
        local minutes=$(((uptime_seconds % 3600) / 60))
        
        if [[ $days -gt 0 ]]; then
            echo "${days}d ${hours}h ${minutes}m"
        elif [[ $hours -gt 0 ]]; then
            echo "${hours}h ${minutes}m"
        else
            echo "${minutes}m"
        fi
    else
        echo "Not running"
    fi
}

get_memory_usage() {
    local pid=$(systemctl show "$SERVICE_NAME" -p MainPID --value)
    if [[ -n "$pid" && "$pid" != "0" ]]; then
        ps -p "$pid" -o rss= | awk '{printf "%.1f MB", $1/1024}'
    else
        echo "N/A"
    fi
}

get_cpu_usage() {
    local pid=$(systemctl show "$SERVICE_NAME" -p MainPID --value)
    if [[ -n "$pid" && "$pid" != "0" ]]; then
        ps -p "$pid" -o %cpu= | awk '{printf "%.1f%%", $1}'
    else
        echo "N/A"
    fi
}

get_restart_count() {
    journalctl -u "$SERVICE_NAME" --since "24 hours ago" | grep -c "Started Bus Tracker" || echo "0"
}

get_error_count() {
    journalctl -u "$SERVICE_NAME" --since "1 hour ago" -p err | grep -c "ERROR" || echo "0"
}

check_network() {
    if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
        echo -e "${GREEN}✓ Online${NC}"
    else
        echo -e "${RED}✗ Offline${NC}"
    fi
}

check_gpio() {
    if python3 -c "import RPi.GPIO" 2>/dev/null; then
        echo -e "${GREEN}✓ Available${NC}"
    else
        echo -e "${YELLOW}⚠ Not available${NC}"
    fi
}

check_backend() {
    if [[ -f "${SCRIPT_DIR}/.env" ]]; then
        source "${SCRIPT_DIR}/.env"
        if [[ -n "$BACKEND_URL" ]]; then
            if curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${BACKEND_URL}/docs" | grep -q "200\|404"; then
                echo -e "${GREEN}✓ Reachable${NC} ($BACKEND_URL)"
            else
                echo -e "${RED}✗ Unreachable${NC} ($BACKEND_URL)"
            fi
        else
            echo -e "${YELLOW}⚠ Not configured${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ .env not found${NC}"
    fi
}

# =============================================================================
# Dashboard Function
# =============================================================================

show_dashboard() {
    clear
    print_header "BUS TRACKER PI - SERVICE DASHBOARD"
    echo ""
    
    # Service Status
    echo -e "${BLUE}📊 Service Status${NC}"
    echo "─────────────────────────────────────────────────────────────────"
    printf "%-20s %s\n" "Status:" "$(get_service_status)"
    printf "%-20s %s\n" "Uptime:" "$(get_uptime)"
    printf "%-20s %s\n" "Memory Usage:" "$(get_memory_usage)"
    printf "%-20s %s\n" "CPU Usage:" "$(get_cpu_usage)"
    printf "%-20s %s\n" "Restarts (24h):" "$(get_restart_count)"
    printf "%-20s %s\n" "Errors (1h):" "$(get_error_count)"
    echo ""
    
    # System Health
    echo -e "${BLUE}🔧 System Health${NC}"
    echo "─────────────────────────────────────────────────────────────────"
    printf "%-20s %s\n" "Network:" "$(check_network)"
    printf "%-20s %s\n" "GPIO:" "$(check_gpio)"
    printf "%-20s %s\n" "Backend:" "$(check_backend)"
    echo ""
    
    # Recent Activity
    echo -e "${BLUE}📝 Recent Activity (last 5 entries)${NC}"
    echo "─────────────────────────────────────────────────────────────────"
    journalctl -u "$SERVICE_NAME" -n 5 --no-pager -o short-precise | sed 's/^/  /'
    echo ""
    
    # Quick Actions
    echo -e "${BLUE}⚡ Quick Actions${NC}"
    echo "─────────────────────────────────────────────────────────────────"
    echo "  sudo systemctl restart $SERVICE_NAME    # Restart service"
    echo "  sudo systemctl stop $SERVICE_NAME       # Stop service"
    echo "  journalctl -u $SERVICE_NAME -f          # Follow logs"
    echo "  ./monitor-service.sh health             # Detailed health check"
    echo ""
    
    print_header "Last Updated: $(date '+%Y-%m-%d %H:%M:%S')"
}

# =============================================================================
# Health Check Function
# =============================================================================

health_check() {
    print_header "BUS TRACKER PI - COMPREHENSIVE HEALTH CHECK"
    echo ""
    
    local issues=0
    
    # Check 1: Service Running
    echo -e "${CYAN}[1/8]${NC} Checking service status..."
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "  ${GREEN}✓ Service is running${NC}"
    else
        echo -e "  ${RED}✗ Service is not running${NC}"
        issues=$((issues + 1))
    fi
    echo ""
    
    # Check 2: Service Enabled
    echo -e "${CYAN}[2/8]${NC} Checking service auto-start..."
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        echo -e "  ${GREEN}✓ Service is enabled (will start on boot)${NC}"
    else
        echo -e "  ${YELLOW}⚠ Service is not enabled${NC}"
        issues=$((issues + 1))
    fi
    echo ""
    
    # Check 3: Environment File
    echo -e "${CYAN}[3/8]${NC} Checking environment configuration..."
    if [[ -f "${SCRIPT_DIR}/.env" ]]; then
        echo -e "  ${GREEN}✓ .env file exists${NC}"
        
        # Check required variables
        source "${SCRIPT_DIR}/.env"
        [[ -n "$BACKEND_URL" ]] && echo -e "    ${GREEN}✓${NC} BACKEND_URL set" || { echo -e "    ${RED}✗${NC} BACKEND_URL missing"; issues=$((issues + 1)); }
        [[ -n "$DEVICE_ID" ]] && echo -e "    ${GREEN}✓${NC} DEVICE_ID set" || { echo -e "    ${YELLOW}⚠${NC} DEVICE_ID missing"; }
        [[ -n "$API_KEY" ]] && echo -e "    ${GREEN}✓${NC} API_KEY set" || { echo -e "    ${RED}✗${NC} API_KEY missing"; issues=$((issues + 1)); }
    else
        echo -e "  ${RED}✗ .env file not found${NC}"
        issues=$((issues + 1))
    fi
    echo ""
    
    # Check 4: Python Script
    echo -e "${CYAN}[4/8]${NC} Checking pi_server.py script..."
    if [[ -f "${SCRIPT_DIR}/pi_server.py" ]]; then
        echo -e "  ${GREEN}✓ pi_server.py exists${NC}"
        if python3 -m py_compile "${SCRIPT_DIR}/pi_server.py" 2>/dev/null; then
            echo -e "  ${GREEN}✓ Syntax is valid${NC}"
        else
            echo -e "  ${RED}✗ Syntax errors detected${NC}"
            issues=$((issues + 1))
        fi
    else
        echo -e "  ${RED}✗ pi_server.py not found${NC}"
        issues=$((issues + 1))
    fi
    echo ""
    
    # Check 5: Network Connectivity
    echo -e "${CYAN}[5/8]${NC} Checking network connectivity..."
    if ping -c 2 -W 3 8.8.8.8 &> /dev/null; then
        echo -e "  ${GREEN}✓ Internet connection available${NC}"
    else
        echo -e "  ${RED}✗ No internet connection${NC}"
        issues=$((issues + 1))
    fi
    echo ""
    
    # Check 6: Backend Reachability
    echo -e "${CYAN}[6/8]${NC} Checking backend server..."
    if [[ -n "$BACKEND_URL" ]]; then
        if curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${BACKEND_URL}/docs" | grep -q "200\|404"; then
            echo -e "  ${GREEN}✓ Backend is reachable${NC}"
            echo -e "    URL: $BACKEND_URL"
        else
            echo -e "  ${RED}✗ Backend is unreachable${NC}"
            echo -e "    URL: $BACKEND_URL"
            issues=$((issues + 1))
        fi
    else
        echo -e "  ${YELLOW}⚠ Backend URL not configured${NC}"
    fi
    echo ""
    
    # Check 7: GPIO Availability
    echo -e "${CYAN}[7/8]${NC} Checking GPIO hardware..."
    if python3 -c "import RPi.GPIO" 2>/dev/null; then
        echo -e "  ${GREEN}✓ RPi.GPIO module available${NC}"
    else
        echo -e "  ${YELLOW}⚠ RPi.GPIO not available (LEDs won't work)${NC}"
        echo -e "    Install with: pip3 install RPi.GPIO"
    fi
    echo ""
    
    # Check 8: Recent Errors
    echo -e "${CYAN}[8/8]${NC} Checking recent error logs..."
    local error_count=$(journalctl -u "$SERVICE_NAME" --since "1 hour ago" -p err | grep -c "." || echo "0")
    if [[ $error_count -eq 0 ]]; then
        echo -e "  ${GREEN}✓ No errors in the last hour${NC}"
    else
        echo -e "  ${YELLOW}⚠ Found $error_count error(s) in the last hour${NC}"
        echo -e "    View with: journalctl -u $SERVICE_NAME -p err -n 20"
    fi
    echo ""
    
    # Summary
    print_header "HEALTH CHECK SUMMARY"
    if [[ $issues -eq 0 ]]; then
        echo -e "${GREEN}✓ All critical checks passed!${NC}"
        echo ""
        echo -e "${GREEN}The service is healthy and running properly.${NC}"
    else
        echo -e "${RED}✗ Found $issues issue(s) that need attention${NC}"
        echo ""
        echo -e "${YELLOW}Please review the issues above and fix them.${NC}"
    fi
    echo ""
}

# =============================================================================
# Restart Function
# =============================================================================

restart_service() {
    print_header "RESTARTING BUS TRACKER PI SERVICE"
    echo ""
    
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${YELLOW}Service is not running. Starting instead...${NC}"
        sudo systemctl start "$SERVICE_NAME"
    else
        echo -e "${BLUE}→ Stopping service...${NC}"
        sudo systemctl stop "$SERVICE_NAME"
        sleep 2
        
        echo -e "${BLUE}→ Starting service...${NC}"
        sudo systemctl start "$SERVICE_NAME"
        sleep 2
    fi
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}✓ Service restarted successfully${NC}"
        echo ""
        sudo systemctl status "$SERVICE_NAME" --no-pager
    else
        echo -e "${RED}✗ Service failed to start${NC}"
        echo ""
        echo "View logs with: journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi
}

# =============================================================================
# Info Function
# =============================================================================

show_info() {
    print_header "BUS TRACKER PI - SERVICE INFORMATION"
    echo ""
    
    echo -e "${CYAN}Service Configuration${NC}"
    echo "─────────────────────────────────────────────────────────────────"
    systemctl show "$SERVICE_NAME" --no-pager | grep -E "^(Id|Description|LoadState|ActiveState|SubState|MainPID|ExecStart|Restart|User|WorkingDirectory)" | sed 's/^/  /'
    echo ""
    
    echo -e "${CYAN}Log Statistics (last 24 hours)${NC}"
    echo "─────────────────────────────────────────────────────────────────"
    local total_lines=$(journalctl -u "$SERVICE_NAME" --since "24 hours ago" | wc -l)
    local error_lines=$(journalctl -u "$SERVICE_NAME" --since "24 hours ago" -p err | wc -l)
    local warning_lines=$(journalctl -u "$SERVICE_NAME" --since "24 hours ago" -p warning | wc -l)
    
    printf "  %-20s %s\n" "Total log entries:" "$total_lines"
    printf "  %-20s %s\n" "Errors:" "$error_lines"
    printf "  %-20s %s\n" "Warnings:" "$warning_lines"
    echo ""
    
    if [[ -f "${SCRIPT_DIR}/.env" ]]; then
        echo -e "${CYAN}Environment Configuration${NC}"
        echo "─────────────────────────────────────────────────────────────────"
        source "${SCRIPT_DIR}/.env"
        printf "  %-20s %s\n" "Backend URL:" "${BACKEND_URL:-Not set}"
        printf "  %-20s %s\n" "Device ID:" "${DEVICE_ID:-Not set}"
        printf "  %-20s %s\n" "Device Name:" "${DEVICE_NAME:-Not set}"
        printf "  %-20s %s\n" "Bus Number:" "${BUS_NUMBER:-Not set}"
        printf "  %-20s %s\n" "PI Mode:" "${PI_MODE:-Not set}"
        echo ""
    fi
}

# =============================================================================
# Main Script
# =============================================================================

main() {
    local command="${1:-dashboard}"
    
    case "$command" in
        dashboard|d)
            show_dashboard
            ;;
        health|h)
            health_check
            ;;
        restart|r)
            restart_service
            ;;
        info|i)
            show_info
            ;;
        watch|w)
            while true; do
                show_dashboard
                sleep 5
            done
            ;;
        *)
            echo "Usage: $0 [dashboard|health|restart|info|watch]"
            echo ""
            echo "Commands:"
            echo "  dashboard (d) - Show real-time service dashboard"
            echo "  health (h)    - Run comprehensive health check"
            echo "  restart (r)   - Restart the service"
            echo "  info (i)      - Show detailed service information"
            echo "  watch (w)     - Continuously monitor (refresh every 5s)"
            exit 1
            ;;
    esac
}

main "$@"
