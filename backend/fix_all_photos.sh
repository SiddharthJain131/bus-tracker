#!/bin/bash
#
# Universal Photo Fix Script
# ==========================
# Restores and relinks photos for ALL entities (students, teachers, parents, admins)
# Generates placeholders via thispersondoesnotexist.com for missing photos
#
# Usage: ./fix_all_photos.sh

cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        Universal Photo Restoration & Relink System            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "Restoring photos for all entities..."
echo "(This may take a few minutes as placeholders are generated)"
echo ""

python3 restore_all_photos.py

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ Process Complete!                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
