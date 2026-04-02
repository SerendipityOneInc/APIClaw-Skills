#!/bin/bash
# Sync shared files from apiclaw/ to all skill directories
# Run before every PR
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/apiclaw"
SKILLS=(
  amazon-analysis
  amazon-blue-ocean-finder
  amazon-competitor-intelligence-monitor
  amazon-daily-market-radar
  amazon-listing-audit-pro
  amazon-market-entry-analyzer
  amazon-opportunity-discoverer
  amazon-pricing-command-center
  amazon-review-intelligence-extractor
  amazon-market-trend-scanner
)
for skill in "${SKILLS[@]}"; do
  echo "Syncing to ${skill}..."
  mkdir -p "${SCRIPT_DIR}/${skill}/scripts" "${SCRIPT_DIR}/${skill}/references"
  cp "${SOURCE_DIR}/scripts/apiclaw.py" "${SCRIPT_DIR}/${skill}/scripts/apiclaw.py"
  cp "${SOURCE_DIR}/references/reference.md" "${SCRIPT_DIR}/${skill}/references/reference.md"
done
echo "Done! All skills synced."
