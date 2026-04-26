# Semantic Versioning Guide

This project uses **Semantic Versioning** (MAJOR.MINOR.PATCH) for releases.

## Version Format

- `MAJOR` - Breaking changes or major features
- `MINOR` - Backwards-compatible features
- `PATCH` - Bug fixes and minor improvements

Example: `1.2.3`
- 1 = MAJOR version
- 2 = MINOR version  
- 3 = PATCH version

## Current Version

The current version is stored in the `VERSION` file at the repository root.

```bash
cat VERSION
```

## Creating a New Release

### Option 1: Using GitHub Actions (Recommended)

1. Go to **Actions → Auto Create Version Tag**
2. Click **Run workflow**
3. Select bump type: **major**, **minor**, or **patch**
4. Click **Run workflow**

The workflow will:
- Bump the version in the `VERSION` file
- Commit the version change
- Create a git tag (e.g., `v1.0.1`)
- Create a GitHub release
- Trigger the release ZIP build

### Option 2: Manual Bumping

```bash
# Bump patch version (1.0.0 → 1.0.1)
python bump-version.py patch

# Bump minor version (1.0.0 → 1.1.0)
python bump-version.py minor

# Bump major version (1.0.0 → 2.0.0)
python bump-version.py major
```

Then commit and push:
```bash
git add VERSION
git commit -m "Bump version to $(cat VERSION)"
git tag -a v$(cat VERSION) -m "Release v$(cat VERSION)"
git push origin main
git push origin v$(cat VERSION)
```

## Release Workflow

When you create a version tag (e.g., `v1.0.1`):

1. The **Auto Create Version Tag** workflow bumps the version file
2. A git tag is created automatically
3. A GitHub release is created
4. The **Create Release ZIP** workflow triggers and builds `krita-prompt-builder.zip`
5. The ZIP is attached to the GitHub release

## Checking Tags

```bash
# List all version tags
git tag -l "v*"

# Show details of a specific tag
git show v1.0.0

# Show the commit for a tag
git rev-list -n 1 v1.0.0
```
