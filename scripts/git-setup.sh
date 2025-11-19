#!/bin/bash
# === Append ALL Emergent changes as ONE commit ON TOP OF MAIN ===

USERNAME="Siddharth Jain"
USEREMAIL="your_email@example.com"
GITHUB_REPO="https://github.com/SiddharthJain131/bus-tracker.git"
BRANCH="main"

echo "🚀 Applying Emergent changes onto main as ONE clean commit..."
cd /app || exit 1

# Ensure HOME exists (Emergent containers usually need this)
if [ -z "$HOME" ]; then
  export HOME="/home/app"
  mkdir -p "$HOME"
  echo "🏠 HOME was missing — set to $HOME"
fi

# Configure identity
git config --global user.name "$USERNAME"
git config --global user.email "$USEREMAIL"
git config --global init.defaultBranch "$BRANCH"

# Initialize repo if missing
if [ ! -d ".git" ]; then
  echo "📁 No .git directory found — initializing fresh repo..."
  git init
else
  echo "ℹ️ Existing .git detected."
fi

# Set remote to GitHub
git remote remove origin 2>/dev/null
git remote add origin "$GITHUB_REPO"
echo "🔗 Remote set to $GITHUB_REPO"

# Fetch real main from GitHub
echo "📥 Fetching origin/main..."
git fetch origin main

# Reset working branch to remote main
echo "🌿 Switching to main..."
git checkout -B "$BRANCH" origin/main

# Stage all Emergent modifications
echo "📦 Staging Emergent changes..."
git add -A

# Create ONE appended commit
echo "📝 Creating single consolidated commit..."
git commit -m "Emergent changes (single consolidated commit) - $(date +'%Y-%m-%d %H:%M')" \
  || echo "ℹ️ No changes to commit."

# Push normally (DO NOT FORCE)
echo "🚀 Pushing commit to GitHub main (no force push)..."
git push origin "$BRANCH"

echo ""
echo "✅ DONE!"
echo "Main history preserved — Emergent changes added as ONE new commit."
echo "➡  $GITHUB_REPO"
