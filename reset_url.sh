#!/bin/bash

echo "🔧 Updating Bus Tracker backend URLs..."

NEW_URL="https://bus-tracker-update.preview.emergentagent.com/"
echo "Using URL: $NEW_URL"

# FRONTEND UPDATE
FE_ENV="frontend/.env"

if [ -f "$FE_ENV" ]; then
  echo "🌐 Updating REACT_APP_BACKEND_URL in frontend/.env..."
  sed -i "s|^REACT_APP_BACKEND_URL=.*|REACT_APP_BACKEND_URL=${NEW_URL}|g" "$FE_ENV"
else
  echo "⚠️ frontend/.env not found."
fi

# BACKEND UPDATE
BE_ENV="backend/.env"

if [ -f "$BE_ENV" ]; then
  echo "🛠 Updating BACKEND_BASE_URL in backend/.env..."
  sed -i "s|^BACKEND_BASE_URL=.*|BACKEND_BASE_URL=\"${NEW_URL}/\"|g" "$BE_ENV"
else
  echo "⚠️ backend/.env not found."
fi

echo "✅ URLs updated successfully!"
