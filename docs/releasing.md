# Release process

AI Context Kit uses a tag-gated Trusted Publishing workflow. Do not create a version tag until every prerequisite below is complete.

## One-time repository setup

1. Create a protected GitHub Environment named `pypi`.
2. In PyPI, configure a Trusted Publisher for repository `sorenjing/ai-context-kit`, workflow `release.yml`, environment `pypi`.
3. Confirm the repository default branch and package ownership before the first upload.

## Version release checklist

1. Update `src/ai_context_kit/__init__.py` and the changelog to the same semantic version.
2. Run `.venv/Scripts/python.exe -m pytest -q` on Windows or the equivalent virtual-environment command on Unix.
3. Remove old `dist/`, then run `python -m build`.
4. Create a clean temporary virtual environment and install the wheel from `dist/`.
5. Run `aictx --version`, `aictx --help`, and a temporary-workspace `aictx init --dry-run` smoke test.
6. Confirm `git status --short` is empty and CI is green on all supported operating systems.
7. Create an annotated tag matching the package version, for example `v0.1.0`, and push only that tag.
8. Verify the release workflow build job before approving the `pypi` environment deployment.
9. After upload, install from PyPI in a new environment and verify the version again.

## Failure boundary

If build or wheel smoke tests fail, do not create or push a tag. If Trusted Publishing fails before upload, fix the repository or publisher configuration and rerun the workflow. PyPI releases are immutable; a bad uploaded version must be replaced by a new patch version rather than overwritten.

