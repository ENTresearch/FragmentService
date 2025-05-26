#!/bin/bash

SCRIPT_DIR=$(dirname "$(realpath "$BASH_SOURCE")")

if [ $# -ne 4 ]; then
  echo "Usage: $0 <SUPABASE_JWT_SECRET> <SUPABASE_URL> <SUPABASE_KEY> <ENV_DIRECTORY_PATH>"
  exit 1
fi

ENV_DIRECTORY_PATH=$4
TARGET_DIR="${ENV_DIRECTORY_PATH%/}"
API_KEY_SECRET=$(sh "$SCRIPT_DIR/generate_keys.sh" $1 $2 $3 $4)

EXPIRY_DAYS=3650

NOW=$(date +%s)
EXPIRATION=$(($NOW + $EXPIRY_DAYS*24*3600))

generate_jwt() {
  local role=$1
  local payload="{\"iss\": \"Fragment Service\", \"role\": \"$role\", \"ref\": \"app\", \"iat\": $NOW, \"exp\": $EXPIRATION}"
  
  node -e "const jwt = require('jsonwebtoken'); const payload = $payload; console.log(jwt.sign(payload, '$API_KEY_SECRET'))"
}

USER_API_KEY=$(generate_jwt "user")
ADMIN_API_KEY=$(generate_jwt "admin")

cat > "${TARGET_DIR}/.env.deploy" <<EOF
USER_API_KEY = "$USER_API_KEY"
ADMIN_API_KEY = "$ADMIN_API_KEY"
EOF