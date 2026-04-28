# Contributing to APIClaw Skills

Thanks for your interest in contributing! We keep things simple.

## Ways to Contribute

- 🐛 **Report bugs** — [Open a bug report](https://github.com/SerendipityOneInc/APIClaw-Skills/issues/new?template=bug_report.md)
- 💡 **Suggest features** — [Open a feature request](https://github.com/SerendipityOneInc/APIClaw-Skills/issues/new?template=feature_request.md)
- 📝 **Improve docs** — Fix typos, clarify instructions, add examples
- 🔧 **Improve skills** — Enhance SKILL.md files, add scenarios, improve the CLI

## Getting Started

1. Fork the repo
2. Create a branch: `git checkout -b my-feature`
3. Make your changes
4. Test your changes (see below)
5. Commit: `git commit -m "feat: add new search scenario"`
6. Push: `git push origin my-feature`
7. Open a Pull Request

## Local Branch Hygiene

To avoid divergence from `origin/main` (e.g. if your previous branch was
squash-merged, your local SHA differs from the merged SHA on `main`):

```bash
# Always start from a fresh main
git checkout main
git fetch origin
git reset --hard origin/main   # safe — discards stale local commits whose
                               # content has already been merged on origin
git checkout -b feat/my-thing
```

## Shared CLI Script — `apiclaw.py`

The canonical script lives at `apiclaw/scripts/apiclaw.py`. Each `amazon-*`
skill has a synced copy at `<skill>/scripts/apiclaw.py`. **Never edit copies
directly** — sync is enforced at three layers:

1. **Local pre-commit hook** — auto-syncs copies when canonical is staged.
   Install once per clone: `bash scripts/install-hooks.sh`
2. **`scripts/sync-scripts.sh`** — mirrors canonical → copies. Refuses to
   overwrite copies that differ without the canonical-source banner
   (`# Canonical source - do not edit copies under amazon-* skill directories directly`).
3. **CI check** (`.github/workflows/shared-files-distribution.yml`) — every
   PR touching `scripts/**` or `*scripts/apiclaw.py` runs a strict diff;
   mismatched copies fail the PR.

See the file header of `apiclaw/scripts/apiclaw.py` for full details.

## Testing Your Changes

### For Skill files (SKILL.md, references/)

- Ensure markdown renders correctly on GitHub
- Check that all links work
- Verify examples are accurate

### For CLI (apiclaw.py)

```bash
# Set your API key
export APICLAW_API_KEY='hms_live_xxx'

# Test basic commands
python amazon-analysis/scripts/apiclaw.py products --keyword "test" --mode beginner
python amazon-analysis/scripts/apiclaw.py categories --keyword "electronics"
```

## Commit Convention

We use conventional commits:

- `feat:` — New feature or scenario
- `fix:` — Bug fix
- `docs:` — Documentation only
- `refactor:` — Code restructuring
- `chore:` — Maintenance tasks

## Code Style

- **Python**: Follow PEP 8, stdlib only (no pip dependencies)
- **Markdown**: Use ATX-style headers (`#`), fenced code blocks with language tags

## Questions?

- Join our [Discord](https://discord.gg/YfDFU9BDp5)
- [Open an Issue](https://github.com/SerendipityOneInc/APIClaw-Skills/issues)

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
