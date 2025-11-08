#!/bin/bash
# === School Bus Tracker Git Setup Script (Simplified) ===
# Usage: bash setup_git.sh

# --- CONFIGURE YOUR DETAILS HERE ---
USERNAME="Siddharth Jain"
USEREMAIL="your_email@example.com"
GITHUB_REPO="https://github.com/SiddharthJain131/bus-tracker.git"

# --- DO NOT EDIT BELOW UNLESS NEEDED ---
echo "🚀 Starting Git setup for Bus Tracker..."
cd /app
# Fix HOME if not defined
if [ -z "$HOME" ]; then
  export HOME=~
fi

# Configure git identity
git config --global user.name "$USERNAME"
git config --global user.email "$USEREMAIL"
git config --global init.defaultBranch main

# Initialize repo if not present
if [ ! -d ".git" ]; then
  git init
  echo "✅ Initialized new git repository."
else
  echo "ℹ️  Git repository already exists."
fi

# Set remote (replace if already set)
git remote remove origin 2>/dev/null
git remote add origin "$GITHUB_REPO"

# Fetch latest updates from GitHub (pull first)
echo "📥 Pulling latest changes from GitHub..."
git fetch origin main 2>/dev/null
git pull origin main --allow-unrelated-histories || echo "No remote history yet."

# Stage & commit local files
echo "📦 Adding all files..."
git add .
git commit -m "Sync local project with remote - $(date +'%Y-%m-%d %H:%M')" || echo "No new changes to commit."

# Push to GitHub
echo "🚀 Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ All done!"
echo "Repo synced at: $GITHUB_REPO"
echo "Now visible at: https://github.com/SiddharthJain131/bus-tracker"
