#!/usr/bin/env bash
# One-time bootstrap for the new remote host luck@192.168.111.172.
# Run this ONCE interactively from the repo root on the Windows machine (Git Bash);
# it will prompt for luck's password exactly one time.
#
# It installs the local public key into luck's authorized_keys and creates
# ~/spz/Fast-Amortized-Bootstrapping (the current project's task directory).
#
# No secrets are stored in this file: it only reads the local public key.

set -euo pipefail

PUBKEY_FILE="$HOME/.ssh/codex_luck_192_168_111_172.pub"
PROJECT_DIR="Fast-Amortized-Bootstrapping"

if [[ ! -f "$PUBKEY_FILE" ]]; then
  echo "ERROR: public key not found: $PUBKEY_FILE" >&2
  echo "Generate it first:" >&2
  echo "  ssh-keygen -t ed25519 -f \"\${PUBKEY_FILE%.pub}\" -N \"\" -C codex-luck-192.168.111.172" >&2
  exit 1
fi

echo ">> Installing public key and creating ~/${PROJECT_DIR} task dir (enter luck's password when prompted)..."
cat "$PUBKEY_FILE" | ssh luck@192.168.111.172 "
set -e
mkdir -p ~/.ssh ~/spz/${PROJECT_DIR}
chmod 700 ~/.ssh
grep -qF '$(cat "$PUBKEY_FILE")' ~/.ssh/authorized_keys 2>/dev/null || cat >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
echo BOOTSTRAP_OK
"

echo ">> Verifying non-interactive login..."
ssh -o BatchMode=yes spz "echo SSH_OK && hostname && whoami && ls -ld ~/spz/${PROJECT_DIR}"
