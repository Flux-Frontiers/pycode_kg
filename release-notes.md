# Release Notes — v0.21.2

> Released: 2026-07-29

A hook-correctness release. `pycodekg install-hooks` was generating a pre-commit hook
that rebuilt the knowledge graph *before* running quality checks. That ordering is not
merely wasteful — it put freshly-written snapshot files inside the window where
`pre-commit` stashes and restores unstaged changes, and it corrupted two commits in
practice. If you use the generated hook, re-run `pycodekg install-hooks --force`.

## What changed

**Quality checks now run before the KG build.** The generated hook previously did:
build index → stage snapshots → `pre-commit run`. Because `pre-commit run` stashes
unstaged changes and restores them afterwards, the build's rewritten
`snapshots/manifest.json` landed squarely inside that stash window.

Two distinct failures came out of that, both observed rather than theorised. In one
repository the stash restore failed with *"patch does not apply"* and aborted the
commit — after every hook had reported success, so nothing surfaced the problem except
checking `git show HEAD` afterwards and finding the commit absent. In another, a staged
deletion of a tracked snapshot slipped into the commit by the same route, silently
removing a file from history. Running the build after `pre-commit run` has fully
finished keeps KG artifacts entirely outside the stash cycle.

The secondary benefit is cheaper but constant: a full index rebuild costs 60–90 seconds,
and there is no longer any reason to pay it for a commit that ruff, ty or pytest is
about to reject.

`TREE_HASH` moved along with the build. It used to be captured first, deliberately,
"before any tool modifies files" — but a hook that rewrites files exits non-zero, so the
build is never reached in that case. Capturing it after the checks pass keys the
snapshot to the content actually being committed, which is strictly more accurate.

**Ignore rules cover nested stores.** The `.gitignore` shipped in this repository
matched only a root-level `.pycodekg/`, so artifacts inside a nested store were ignored
by nothing at all, and `*.db` files were missed entirely. Patterns are now
`**/`-prefixed. `snapshots/` remains tracked at every depth — that distinction matters,
and a blanket `**/.pycodekg/` would silently discard snapshot history.

## Upgrading

Existing hooks are **not** updated automatically. The hook is a generated file in
`.git/hooks/`, which is local to each clone and does not travel with the package. After
upgrading, re-run:

```bash
pycodekg install-hooks --force
```

Take care in repositories whose hook drives more than one KG tool — AgentKG and
FileTreeKG install a combined hook that invokes both `pycodekg` and `dockg`. Each
installer writes a whole hook file rather than a fragment, so running this there would
overwrite the combined hook and silently drop the other half.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
