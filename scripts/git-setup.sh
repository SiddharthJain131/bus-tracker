#!/bin/bash
# === School Bus Tracker Git Setup Script (Squash Everything Into One Commit) ===

USERNAME="Siddharth Jain"
USEREMAIL="your_email@example.com"
GITHUB_REPO="https://github.com/SiddharthJain131/bus-tracker.git"

echo "🚀 Starting Git setup for Bus Tracker (Single Commit Mode)..."
cd /app || exit 1

# Ensure HOME exists
[ -z "$HOME" ] && export HOME=~

# Configure Git identity
git config --global user.name "$USERNAME"
git config --global user.email "$USEREMAIL"
git config --global init.defaultBranch main

# Initialize repo if missing
if [ ! -d ".git" ]; then
  git init
  echo "✅ Initialized new git repository."
else
  echo "ℹ️ Git repository already exists."
fi

# Set remote
git remote remove origin 2>/dev/null
git remote add origin "$GITHUB_REPO"

# Fetch remote branch if exists
git fetch origin main 2>/dev/null

echo "🧹 Clearing commit history to consolidate changes..."
# Reset to an empty state but keep files
git reset --soft $(git commit-tree HEAD^{tree} -m "TEMP_EMPTY_COMMIT")

echo "📦 Staging all project files..."
git add .

echo "📝 Creating SINGLE consolidated commit..."
git commit -m "Consolidated commit - $(date +'%Y-%m-%d %H:%M')"

echo "🚀 Pushing consolidated commit to GitHub (force push)..."
git push origin main --force

echo ""
echo "✅ Done! Remote 'main' now contains ONE clean consolidated commit."
