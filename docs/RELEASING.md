# Releasing labelscope

Trusted publishing to PyPI runs automatically from `.github/workflows/publish.yml`
whenever a GitHub Release is published. Humans only do the version bump and the
tag + release.

## One-time setup

1. On PyPI, create the project `labelscope` and register a trusted publisher:
   - Owner: `Xpertik`
   - Repository: `labelscope`
   - Workflow: `publish.yml`
   - Environment: `pypi`
2. Reference: <https://docs.pypi.org/trusted-publishers/>.

## Cutting a release

1. Update `__version__` in `labelscope/__init__.py` and `version` in `pyproject.toml`.
2. Update `CHANGELOG.md` (if present) with the new section.
3. Commit on `main`: `chore(release): vX.Y.Z`.
4. Tag: `git tag vX.Y.Z && git push origin vX.Y.Z`.
5. On GitHub, draft a release from the tag, paste the changelog section, publish.
6. The `Publish to PyPI` workflow builds sdist + wheel and uploads via OIDC.

## Verify

- CI green on `main`.
- `pip install labelscope==X.Y.Z` in a clean venv.
- `labelscope --help` prints, `labelscope render examples/epl1-55x34.txt -o /tmp/x.png` works.
