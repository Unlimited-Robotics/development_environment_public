#!/bin/bash

set -e

# Check if robot alias was provided
if [ -z "$1" ]; then
  echo "❌ Usage: ./fix_permissions.sh <robot_alias> [user_folder]"
  echo "   Example: ./fix_permissions.sh GARY013_VPN roy"
  echo "   Example: ./fix_permissions.sh GARY013_VPN            # uses default 'devel'"
  exit 1
fi

ROBOT_ALIAS="$1"
USER_FOLDER="$2"  # optional

echo "🔧 Connecting to $ROBOT_ALIAS to fix permissions..."

ssh -t "$ROBOT_ALIAS" "
  cd ~/dev_workspaces &&
  USER_FOLDER=\"${USER_FOLDER:-devel}\" &&
  echo '📁 Using user folder: \$USER_FOLDER' &&
  sudo chown -R gary:gary \"\$USER_FOLDER\" &&
  echo '✅ Permissions fixed for \$USER_FOLDER'
"
