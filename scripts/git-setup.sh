#!/bin/bash
# === Squash local commits into ONE commit above origin/main ===

USERNAME="Siddharth Jain"
USEREMAIL="your_email@example.com"
GITHUB_REPO="https://github.com/SiddharthJain131/bus-tracker.git"
BRANCH="main"    # Your working branch

echo "🚀 Squashing all local commits into ONE commit above origin/main..."

cd /app || exit 1

# --- Ensure HOME exists ---
if [ -z "$HOME" ]; then
  export HOME="/home/app"
  mkdir -p "$HOME"
  echo "🏠 HOME was missing — set to $HOME"
fi

# --- Configure Git User ---
git config --global user.name "$USERNAME"
git config --global user.email "$USEREMAIL"

# --- Ensure remote is present ---
git remote remove origin 2>/dev/null
git remote add origin "$GITHUB_REPO"

echo "📥 Fetching origin/main..."
git fetch origin main

echo "🌿 Checking out branch $BRANCH..."
git checkout "$BRANCH" || git checkout -b "$BRANCH"

# ---- GET THE BASE COMMIT ----
# This gives the EXACT commit where your branch last matched origin/main
BASE=$(git merge-base HEAD origin/main)

echo "🔍 Base commit where branch diverged from origin/main:"
echo "$BASE"

# ---- SQUASH EVERYTHING ABOVE BASE ----
echo "🧹 Soft resetting to base commit..."
git reset --soft "$BASE"

echo "📝 Creating ONE single clean commit..."
git add -A
git commit -m "Single consolidated commit on top of main - $(date +'%Y-%m-%d %H:%M')"

echo "🚀 Pushing (force is needed because commit history changed)..."
git push origin "$BRANCH" -f

echo ""
echo "✅ DONE!"
echo "All commits above origin/main were squashed into ONE clean commit."
