---
name: publish
description: Step-by-step release workflow for pycode-kg. Use this skill when the user wants to cut a release, bump the version, update the CHANGELOG, or tag a commit for the pycode-kg project. Prefer the generic /release skill for the full, current workflow — this file is kept for the manual/local steps it still covers.
---

# Publish Skill — pycode-kg Release Workflow

**PyPI publishing is automatic.** `.github/workflows/release.yml` runs on
`push: tags: ['v*']` and has a `publish` job (added `394c660`, 2026-08-25)
that pushes the built wheel/sdist to PyPI via OIDC trusted publishing
(`pypa/gh-action-pypi-publish`) once the `release` job's GitHub Release step
completes. **Do not run `poetry publish` manually** — pushing the release
tag is the publish step. A manual `poetry publish` afterward would just fail
(PyPI rejects re-uploading an existing version).

## Prerequisites

- Clean working tree (`git status` shows no uncommitted changes)
- All tests passing (`poetry run pytest`)
- Pre-commit checks passing (`pre-commit run --all-files`)

---

## Release Steps

### 1. Decide the version bump

Follow [Semantic Versioning](https://semver.org/):

| Change | Bump |
|--------|------|
| Bug fixes only | `patch` (0.5.2 → 0.5.3) |
| New features, backward-compatible | `minor` (0.5.2 → 0.6.0) |
| Breaking changes | `major` (0.5.2 → 1.0.0) |

### 2. Update CHANGELOG.md

Move items from `## [Unreleased]` to a new versioned section:

```markdown
## [X.Y.Z] - YYYY-MM-DD
```

Leave `## [Unreleased]` empty at the top for future entries.

### 3. Bump version in pyproject.toml

```bash
poetry version patch   # or minor / major
```

Verify: `grep '^version' pyproject.toml`

### 4. Commit the release

```bash
git add pyproject.toml CHANGELOG.md
PYCODEKG_SKIP_SNAPSHOT=1 git commit -m "chore: release vX.Y.Z"
```

> Use `PYCODEKG_SKIP_SNAPSHOT=1` to prevent the post-commit hook from creating a snapshot on a release commit.

### 5. Tag the release

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

### 6. Push the branch, then the tag

```bash
git push origin main
git push origin vX.Y.Z
```

Pushing the tag triggers `release.yml`: it builds the wheel/sdist, creates
the GitHub Release (using `release-notes.md`), and publishes those same
artifacts to PyPI. Watch it with `gh run watch` — nothing further to run
locally.

---

## After Release

- Update `.claude/skills/pycodekg/SKILL.md` if the install command or version references changed
- Save a snapshot: `pycodekg snapshot save X.Y.Z --repo . --subject repo:pycode-kg` (there is no `--commit` flag; the git tree hash is auto-detected provenance, not the key)

---

## Rollback

If something went wrong after the tag push published to PyPI:

- PyPI releases cannot be deleted (only yanked): `poetry run twine yank pycode-kg X.Y.Z`
- Revert the commit: `git revert HEAD` then `git push`
- Deleting the tag does not undo the PyPI publish — it only removes the git
  ref: `git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z`
