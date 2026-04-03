#!/bin/bash
# scripts/sync-scripts.sh
# 将 apiclaw/scripts/apiclaw.py 同步到所有 amazon-* skill 目录
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$REPO_ROOT/apiclaw/scripts/apiclaw.py"

if [[ ! -f "$SOURCE" ]]; then
  echo "ERROR: 真源文件不存在: $SOURCE"
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
    # 副本不存在，直接复制
    cp "$SOURCE" "$target"
    echo "  SYNC $skill_name"
    ((changed++))
  elif diff -q "$SOURCE" "$target" &>/dev/null; then
    echo "  OK   $skill_name"
  else
    # 副本存在但与真源不同，检查是否包含 AUTO-SYNCED 标记
    if grep -q "AUTO-SYNCED" "$target"; then
      # 有标记说明是合法副本，直接覆盖更新
      cp "$SOURCE" "$target"
      echo "  SYNC $skill_name"
      ((changed++))
    else
      echo "  CONFLICT $skill_name — scripts/apiclaw.py 与真源不一致且不含 AUTO-SYNCED 标记"
      echo "           请勿手动编辑副本，改动应提交到 apiclaw/scripts/apiclaw.py"
      ((conflict++))
    fi
  fi
done

echo ""
if [[ $conflict -gt 0 ]]; then
  echo "错误: $conflict 个 skill 存在手动编辑的副本，同步中止。"
  exit 1
fi
echo "完成: $total 个 skill，$changed 个已更新。"
