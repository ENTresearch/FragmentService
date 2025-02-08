#!/bin/bash

# Argument check
if [ $# -ne 4 ]; then
  echo "Usage: $0 <SUPABASE_JWT_SECRET> <SUPABASE_URL> <SUPABASE_KEY> <ENV_DIRECTORY_PATH>"
  exit 1
fi

SUPABASE_JWT_SECRET=$1
SUPABASE_URL=$2
SUPABASE_KEY=$3
ENV_DIRECTORY_PATH=$4

TARGET_DIR="${ENV_DIRECTORY_PATH%/}"

# Generating random ADMIN_URL
ADMIN_URL="admin-$(shuf -i 10000-99999 -n 1)"

# Generating API_KEY_SECRET (64-byte base64 string)
API_KEY_SECRET=$(node -e "console.log(require('crypto').randomBytes(64).toString('base64'))")

# .env.keys file creation
cat > "${TARGET_DIR}/.env.keys" <<EOF
# Supabase
SUPABASE_JWT_SECRET = "$SUPABASE_JWT_SECRET"
SUPABASE_URL = "$SUPABASE_URL"
SUPABASE_KEY = "$SUPABASE_KEY"

# Python FastAPI Gateway Configuration
ADMIN_URL = "$ADMIN_URL"
API_KEY_SECRET = "$API_KEY_SECRET"
EOF

echo $API_KEY_SECRET