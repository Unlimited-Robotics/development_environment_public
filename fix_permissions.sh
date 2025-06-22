#!/bin/bash

set -e

# Check if robot alias was provided
if [ -z "$1" ]; then
  echo "❌ Usage: ./fix_permissions.sh <robot_alias>"
  echo "   Example: ./fix_permissions.sh GARY013_VPN"
  exit 1
fi

ROBOT_ALIAS="$1"

echo "🔧 Connecting to $ROBOT_ALIAS to fix permissions..."

ssh -t "$ROBOT_ALIAS" "
  cd ~/dev_workspaces &&
  USER_FOLDER=\"devel\" &&
  echo '📁 Using user folder: \$USER_FOLDER' &&
  sudo chown -R gary:gary \"\$USER_FOLDER\" &&
  echo '✅ Permissions fixed for \$USER_FOLDER'
"
