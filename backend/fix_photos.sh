#!/bin/bash
#
# Quick Photo Fix Script
# ======================
# One-command solution to restore and relink all student photos
#
# Usage: ./fix_photos.sh

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          Student Photo Restoration & Relink System            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

echo "Step 1: Checking for orphaned photos..."
python3 migrate_orphaned_photos.py --list
echo ""

read -p "Found orphaned photos. Migrate them? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Step 2: Migrating orphaned photos..."
    python3 migrate_orphaned_photos.py --migrate
    echo ""
fi

echo "Step 3: Running full restoration and verification..."
python3 restore_student_photos.py
echo ""

echo "Step 4: Final verification..."
python3 restore_student_photos.py --verify-only
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ Process Complete!                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "All student photos have been restored and relinked."
echo "Check the output above for any warnings or issues."
