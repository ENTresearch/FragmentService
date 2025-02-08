#!/bin/bash

if ! command -v node &> /dev/null; then
  echo "Node.js is not installed. Installing..."
  sudo apt update
  sudo apt install -y nodejs npm
fi

if ! command -v shuf &> /dev/null; then
  echo "shuf is not installed. Installing..."
  sudo apt install -y coreutils
fi

if ! command -v openssl &> /dev/null; then
  echo "OpenSSL is not installed. Installing..."
  sudo apt install -y openssl
fi

if ! node -e "require('jsonwebtoken')" &> /dev/null; then
  echo "jsonwebtoken is not installed. Installing..."
  #npm init -y
  npm install jsonwebtoken
fi