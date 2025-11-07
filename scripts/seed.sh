#!/bin/bash

# Seed Data Script for Bus Tracker System
# This script runs the database seeding process

echo "=================================================="
echo "🌱 BUS TRACKER - DATABASE SEEDING SCRIPT"
echo "=================================================="
echo ""

# Check if MongoDB is running
if ! pgrep -x "mongod" > /dev/null; then
    echo "⚠️  MongoDB is not running. Starting MongoDB..."
    sudo systemctl start mongod
    sleep 3
fi

# Navigate to backend directory
cd "$(dirname "$0")/../backend" || exit 1

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Run seed script
echo "🌱 Running seed data script..."
echo ""
python seed_data.py

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!"
    echo "=================================================="
    echo ""
    echo "📌 Next Steps:"
    echo "   1. Start the application: sudo supervisorctl restart all"
    echo "   2. Access frontend: http://localhost:3000"
    echo "   3. Use demo credentials from the output above"
    echo ""
else
    echo ""
    echo "❌ SEEDING FAILED! Check error messages above."
    exit 1
fi
