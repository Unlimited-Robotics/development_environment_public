#!/bin/bash

set -e

# Check if both arguments were provided
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "❌ Usage: ./fix_permissions.sh <user_folder> <robot_alias>"
  echo "   Example: ./fix_permissions.sh roy GARY011_LOCAL"
  exit 1
fi

USER_FOLDER="$1"
ROBOT_ALIAS="$2"

echo "🔧 Connecting to $ROBOT_ALIAS to fix permissions for $USER_FOLDER..."

ssh -t "$ROBOT_ALIAS" "
  cd ~/dev_workspaces &&
  echo '📁 Using user folder: $USER_FOLDER' &&
  sudo chown -R gary:gary \"$USER_FOLDER\" &&
  echo '✅ Permissions fixed for $USER_FOLDER'
"
