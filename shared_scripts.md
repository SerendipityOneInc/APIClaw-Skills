# 共享脚本改造方案：单一真源 + CI 自动分发

## 背景

APIClaw-Skills 仓库包含 9 个 Amazon 相关 skill，每个 skill 的 `scripts/apiclaw.py` 将统一为完全相同的文件。目前各 skill 独立维护各自的副本，维护成本高、容易不一致。

`npx skills add` 安装 skill 时，会将每个 skill 目录独立复制到用户本地（如 `.claude/skills/skill-name/`），不会携带 skill 目录外的文件。因此安装后的 skill 必须是自包含的。

本方案在仓库中保留唯一真源，通过 CI 自动分发到各 skill 目录，确保：
- 开发者只维护一份 `apiclaw.py`
- 安装用户无感知，每个 skill 安装后自包含可用
- CI 保障所有副本与真源严格一致

## 改造后的仓库结构

```
APIClaw-Skills/
├── shared/
│   └── scripts/
│       └── apiclaw.py                  ← 唯一真源
│
├── amazon-analysis/
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
│       └── apiclaw.py                  ← CI 自动从 shared/ 复制，禁止手动编辑
│
├── amazon-blue-ocean-finder/
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
│       └── apiclaw.py                  ← CI 自动从 shared/ 复制
│
├── amazon-competitor-war-room/
│   └── ...（同上）
├── amazon-daily-market-radar/
│   └── ...
├── amazon-listing-audit-pro/
│   └── ...
├── amazon-market-entry-analyzer/
│   └── ...
├── amazon-opportunity-discoverer/
│   └── ...
├── amazon-pricing-command-center/
│   └── ...
├── amazon-review-intelligence-extractor/
│   └── ...
│
├── apiclaw/                             ← API 参考 skill，无 scripts，不参与同步
│   ├── SKILL.md
│   └── references/
│
├── scripts/
│   └── sync-scripts.sh                 ← 同步脚本（CI 和本地均可使用）
│
└── .github/
    └── workflows/
        ├── markdown-link-check.yml
        └── shared-files-distribution.yml
```

## 实施步骤

### 第一步：将统一版本的 apiclaw.py 放入 `apiclaw/scripts/`

```bash
mkdir -p apiclaw/scripts
# 将最终统一版本的 apiclaw.py 放入真源位置
cp amazon-market-entry-analyzer/scripts/apiclaw.py apiclaw/scripts/apiclaw.py
```

### 第二步：创建同步脚本 `scripts/sync-scripts.sh`

```bash
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

for skill_dir in "$REPO_ROOT"/amazon-*/; do
  skill_name=$(basename "$skill_dir")
  target="$skill_dir/scripts/apiclaw.py"
  ((total++))

  mkdir -p "$skill_dir/scripts"

  if [[ -f "$target" ]] && diff -q "$SOURCE" "$target" &>/dev/null; then
    echo "  OK  $skill_name"
  else
    cp "$SOURCE" "$target"
    echo "  SYNC $skill_name"
    ((changed++))
  fi
done

echo ""
echo "完成: $total 个 skill，$changed 个已更新。"
```

```bash
chmod +x scripts/sync-scripts.sh
```

### 第三步：新增 CI 配置 `.github/workflows/shared-files-distribution.yml`

```yaml
name: Shared Files Distribution

on:
  push:
    branches: [main]
    paths:
      - 'apiclaw/scripts/apiclaw.py'
      - 'scripts/**'
      - 'amazon-*/scripts/apiclaw.py'
  pull_request:
    branches: [main]
    paths:
      - 'apiclaw/scripts/apiclaw.py'
      - 'scripts/**'
      - 'amazon-*/scripts/apiclaw.py'
  workflow_dispatch:

permissions:
  contents: read

jobs:
  sync-and-test:
    name: Sync Scripts & Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      # 校验所有副本与真源一致
      - name: Verify scripts are in sync
        run: |
          shopt -s nullglob
          found=0
          for skill_dir in amazon-*/; do
            found=1
            target="${skill_dir}scripts/apiclaw.py"
            if [[ ! -f "$target" ]]; then
              echo "::error::缺少副本文件: $target"
              echo "请运行: bash scripts/sync-scripts.sh"
              exit 1
            fi
            if ! diff -q apiclaw/scripts/apiclaw.py "$target" &>/dev/null; then
              echo "::error::$target 与 apiclaw/scripts/apiclaw.py 不一致！"
              echo "请运行: bash scripts/sync-scripts.sh"
              exit 1
            fi
          done
          if [[ "$found" -eq 0 ]]; then
            echo "::error::未找到任何 amazon-* skill 目录，无法执行同步校验。"
            exit 1
          fi

      # CLI 冒烟测试（用真源验证）
      - name: CLI smoke test
        run: python apiclaw/scripts/apiclaw.py --help
```

### 第四步：在各 skill 的 apiclaw.py 头部添加注释标记

在 `apiclaw/scripts/apiclaw.py` 文件顶部加入提示，防止有人直接编辑副本：

```python
#!/usr/bin/env python3
# ============================================================
# AUTO-SYNCED — 请勿直接编辑此文件
# 真源位置: apiclaw/scripts/apiclaw.py
# 同步方式: pre-commit hook 自动复制 或 bash scripts/sync-scripts.sh
# ============================================================
```

## 日常工作流

### 修改 apiclaw.py

```bash
# 1. 编辑唯一真源
vim apiclaw/scripts/apiclaw.py

# 2. 本地同步（可选，CI 也会做）
bash scripts/sync-scripts.sh

# 3. 提交
git add apiclaw/scripts/apiclaw.py
git add '*/scripts/apiclaw.py'
git commit -m "feat: apiclaw.py 增加 xxx 功能"
git push
```

### 提交 PR

- CI 自动校验各 skill 下的 `apiclaw.py` 是否与 `apiclaw/scripts/apiclaw.py` 一致
- 如果不一致，PR check 失败，提示开发者运行 `bash scripts/sync-scripts.sh`

### 新增一个 skill

```bash
# 1. 创建 skill 目录
mkdir -p amazon-new-skill/{references,scripts}

# 2. 编写 SKILL.md 和 references
vim amazon-new-skill/SKILL.md

# 3. 同步脚本自动覆盖（匹配 amazon-* 模式）
bash scripts/sync-scripts.sh

# 4. 提交
git add amazon-new-skill/
git commit -m "feat: 新增 amazon-new-skill"
```

## 对现有流程的影响

| 方面 | 改造前 | 改造后 |
|------|--------|--------|
| apiclaw.py 维护 | 9 份独立副本，手动同步 | 只改 `apiclaw/scripts/apiclaw.py` |
| `npx skills add` 安装 | 正常 | 正常，无任何变化 |
| 单个 skill 安装 | 自包含 | 自包含，无变化 |
| CI | 冒烟测试 + 链接检查 | + 自动同步 + 一致性校验 |
| 新增 skill | 手动复制 apiclaw.py | `sync-scripts.sh` 自动处理 |

## 注意事项

1. **`apiclaw/` skill 不参与同步**：它是纯 API 参考文档，没有 scripts 目录，同步脚本通过 `amazon-*` 通配符自动排除。

2. **首次改造时需要统一 apiclaw.py**：当前各 skill 的 apiclaw.py 内容不同（各有特有的复合命令）。统一版本需要先合并所有复合命令到一个文件中，再执行本方案。

3. **同步依赖本地 hook 或手动执行脚本**：当前 CI 只负责校验，不会自动 commit 副本；如果改了真源，需本地运行 `bash scripts/sync-scripts.sh`，或依赖 pre-commit hook 自动同步。
   ```bash
   git commit -m "chore: sync apiclaw.py from shared/ [skip ci]"
   ```
