#!/bin/bash
# scripts/sync-scripts.sh
# Sync apiclaw/scripts/apiclaw.py to all amazon-* skill directories
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$REPO_ROOT/apiclaw/scripts/apiclaw.py"

if [[ ! -f "$SOURCE" ]]; then
  echo "ERROR: Canonical source file does not exist: $SOURCE"
  exit 1
fi

changed=0
total=0
conflict=0

for skill_dir in "$REPO_ROOT"/amazon-*/; do
  skill_name=$(basename "$skill_dir")
  target="$skill_dir/scripts/apiclaw.py"
  ((total++))

  mkdir -p "$skill_dir/scripts"

  if [[ ! -f "$target" ]]; then
    # Copy directly when the target does not exist
    cp "$SOURCE" "$target"
    echo "  SYNC $skill_name"
    ((changed++))
  elif diff -q "$SOURCE" "$target" &>/dev/null; then
    echo "  OK   $skill_name"
  else
    # If the target differs, only overwrite files that are marked as managed copies.
    # The canonical-source banner (added in #47) is the marker we look for.
    if grep -q "Canonical source - do not edit copies" "$target"; then
      # The marker indicates a managed copy, so it is safe to overwrite
      cp "$SOURCE" "$target"
      echo "  SYNC $skill_name"
      ((changed++))
    else
      echo "  CONFLICT $skill_name - scripts/apiclaw.py differs from the canonical source and has no managed-copy marker"
      echo "           Do not edit copies directly; submit changes to apiclaw/scripts/apiclaw.py"
      ((conflict++))
    fi
  fi
done

echo ""
if [[ $conflict -gt 0 ]]; then
  echo "ERROR: $conflict skill copies appear to have been edited manually; sync aborted."
  exit 1
fi
echo "Done: $total skills processed, $changed updated."
