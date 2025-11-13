#!/bin/bash
# === School Bus Tracker Git Setup Script (Updated for GitHub OAuth) ===

USERNAME="Siddharth Jain"
USEREMAIL="your_email@example.com"
GITHUB_REPO="https://github.com/SiddharthJain131/bus-tracker.git"

echo "🚀 Starting Git setup for Bus Tracker..."
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

# Pull & merge safely
echo "📥 Pulling latest changes from GitHub..."
git fetch origin main 2>/dev/null
git pull origin main --allow-unrelated-histories --no-rebase || echo "No remote history yet."

# Stage & commit
echo "📦 Adding all files..."
git add .
git commit -m "Sync local project with remote - $(date +'%Y-%m-%d %H:%M')" || echo "No new changes to commit."

# Push (using cached or VS Code OAuth credentials)
echo "🚀 Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ All done!"
echo "Repo synced at: $GITHUB_REPO"