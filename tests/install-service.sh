#!/bin/bash
# =============================================================================
# Bus Tracker Pi - Service Installation Script
# =============================================================================
# This script installs the bus-tracker-pi systemd service and configures
# automatic startup on boot with proper logging and restart capabilities.
#
# Usage:
#   ./install-service.sh [install|uninstall|status|logs]
#
# =============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="bus-tracker-pi"
SERVICE_FILE="bus-tracker-pi.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_FILE}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
LOG_DIR="/var/log/bus-tracker"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo -e "${CYAN}=====================================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}=====================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}→ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error ".env file not found at: $ENV_FILE"
        print_info "Please create .env file with required configuration:"
        echo ""
        echo "BACKEND_URL=http://your-backend-url.com:8001"
        echo "DEVICE_ID=your-device-id"
        echo "DEVICE_NAME=Pi-Bus-001"
        echo "BUS_NUMBER=BUS-001"
        echo "API_KEY=your-api-key"
        echo "PI_MODE=hardware"
        exit 1
    fi
    print_success ".env file found"
}

check_service_file() {
    if [[ ! -f "${SCRIPT_DIR}/${SERVICE_FILE}" ]]; then
        print_error "Service file not found: ${SCRIPT_DIR}/${SERVICE_FILE}"
        exit 1
    fi
    print_success "Service file found"
}

check_python_deps() {
    print_info "Checking Python dependencies..."
    
    # Check if pi_requirements.txt exists
    if [[ -f "${SCRIPT_DIR}/pi_requirements.txt" ]]; then
        # Check if main dependencies are installed
        python3 -c "import RPi.GPIO" 2>/dev/null || {
            print_warning "RPi.GPIO not installed"
            read -p "Install Pi dependencies now? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                pip3 install -r "${SCRIPT_DIR}/pi_requirements.txt"
            fi
        }
    fi
}

create_log_directory() {
    if [[ ! -d "$LOG_DIR" ]]; then
        print_info "Creating log directory: $LOG_DIR"
        mkdir -p "$LOG_DIR"
        chown pi:pi "$LOG_DIR"
        chmod 755 "$LOG_DIR"
        print_success "Log directory created"
    else
        print_success "Log directory exists"
    fi
}

# =============================================================================
# Installation Functions
# =============================================================================

install_service() {
    print_header "INSTALLING BUS TRACKER PI SERVICE"
    
    # Pre-installation checks
    print_info "Running pre-installation checks..."
    check_env_file
    check_service_file
    check_python_deps
    create_log_directory
    
    # Stop service if already running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_info "Stopping existing service..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # Copy service file
    print_info "Installing service file..."
    cp "${SCRIPT_DIR}/${SERVICE_FILE}" "$SERVICE_PATH"
    chmod 644 "$SERVICE_PATH"
    print_success "Service file installed to $SERVICE_PATH"
    
    # Reload systemd
    print_info "Reloading systemd daemon..."
    systemctl daemon-reload
    print_success "Systemd daemon reloaded"
    
    # Enable service
    print_info "Enabling service to start on boot..."
    systemctl enable "$SERVICE_NAME"
    print_success "Service enabled"
    
    # Start service
    print_info "Starting service..."
    systemctl start "$SERVICE_NAME"
    sleep 2
    
    # Check status
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service is running"
        echo ""
        print_header "INSTALLATION COMPLETE"
        echo ""
        echo -e "${GREEN}The Bus Tracker Pi service has been successfully installed!${NC}"
        echo ""
        echo -e "${CYAN}Service Management Commands:${NC}"
        echo "  sudo systemctl status $SERVICE_NAME      # Check status"
        echo "  sudo systemctl restart $SERVICE_NAME     # Restart service"
        echo "  sudo systemctl stop $SERVICE_NAME        # Stop service"
        echo "  journalctl -u $SERVICE_NAME -f           # View live logs"
        echo "  journalctl -u $SERVICE_NAME -n 100       # View last 100 log lines"
        echo ""
        echo -e "${CYAN}View current status:${NC}"
        systemctl status "$SERVICE_NAME" --no-pager
    else
        print_error "Service failed to start"
        echo ""
        echo -e "${YELLOW}View logs with: journalctl -u $SERVICE_NAME -n 50${NC}"
        exit 1
    fi
}

uninstall_service() {
    print_header "UNINSTALLING BUS TRACKER PI SERVICE"
    
    # Stop service
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_info "Stopping service..."
        systemctl stop "$SERVICE_NAME"
        print_success "Service stopped"
    fi
    
    # Disable service
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        print_info "Disabling service..."
        systemctl disable "$SERVICE_NAME"
        print_success "Service disabled"
    fi
    
    # Remove service file
    if [[ -f "$SERVICE_PATH" ]]; then
        print_info "Removing service file..."
        rm "$SERVICE_PATH"
        print_success "Service file removed"
    fi
    
    # Reload systemd
    print_info "Reloading systemd daemon..."
    systemctl daemon-reload
    print_success "Systemd daemon reloaded"
    
    print_header "UNINSTALLATION COMPLETE"
    print_success "Bus Tracker Pi service has been uninstalled"
    print_warning "Note: Log files in $LOG_DIR were preserved"
}

show_status() {
    print_header "BUS TRACKER PI SERVICE STATUS"
    echo ""
    systemctl status "$SERVICE_NAME" --no-pager
    echo ""
    print_header "RECENT LOGS (last 20 lines)"
    echo ""
    journalctl -u "$SERVICE_NAME" -n 20 --no-pager
}

show_logs() {
    print_header "BUS TRACKER PI SERVICE LOGS"
    echo ""
    echo -e "${CYAN}Following live logs... (Ctrl+C to exit)${NC}"
    echo ""
    journalctl -u "$SERVICE_NAME" -f
}

test_service() {
    print_header "TESTING SERVICE CONFIGURATION"
    
    # Check if service file exists
    if [[ -f "$SERVICE_PATH" ]]; then
        print_success "Service file exists: $SERVICE_PATH"
    else
        print_error "Service file not found: $SERVICE_PATH"
        return 1
    fi
    
    # Check if service is loaded
    if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
        print_success "Service is loaded in systemd"
    else
        print_error "Service not loaded in systemd"
        return 1
    fi
    
    # Check if service is enabled
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        print_success "Service is enabled (will start on boot)"
    else
        print_warning "Service is not enabled (won't start on boot)"
    fi
    
    # Check if service is active
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service is currently running"
    else
        print_warning "Service is not running"
    fi
    
    # Check environment file
    check_env_file
    
    # Check Python script
    if [[ -f "${SCRIPT_DIR}/pi_server.py" ]]; then
        print_success "pi_server.py script found"
    else
        print_error "pi_server.py script not found"
        return 1
    fi
    
    echo ""
    print_success "All checks passed!"
}

# =============================================================================
# Main Script
# =============================================================================

main() {
    local command="${1:-install}"
    
    case "$command" in
        install)
            check_root
            install_service
            ;;
        uninstall)
            check_root
            uninstall_service
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        test)
            test_service
            ;;
        *)
            echo "Usage: $0 [install|uninstall|status|logs|test]"
            echo ""
            echo "Commands:"
            echo "  install    - Install and start the service"
            echo "  uninstall  - Stop and remove the service"
            echo "  status     - Show service status and recent logs"
            echo "  logs       - Follow live service logs"
            echo "  test       - Test service configuration"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
