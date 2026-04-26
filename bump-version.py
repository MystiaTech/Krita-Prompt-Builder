#!/usr/bin/env python3
"""Semantic version bumper for Krita Prompt Builder.

Usage:
    python bump-version.py major    # 1.0.0 → 2.0.0
    python bump-version.py minor    # 1.0.0 → 1.1.0
    python bump-version.py patch    # 1.0.0 → 1.0.1
"""

import sys
import re
from pathlib import Path

VERSION_FILE = Path(__file__).parent / "VERSION"


def read_version():
    """Read current version from VERSION file."""
    with open(VERSION_FILE) as f:
        return f.read().strip()


def bump_version(current, bump_type):
    """Bump version based on type (major, minor, patch)."""
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", current)
    if not match:
        raise ValueError(f"Invalid version format: {current}")

    major, minor, patch = map(int, match.groups())

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Unknown bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"


def write_version(version):
    """Write new version to VERSION file."""
    with open(VERSION_FILE, "w") as f:
        f.write(version + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    bump_type = sys.argv[1].lower()
    if bump_type not in ("major", "minor", "patch"):
        print(f"Error: bump type must be 'major', 'minor', or 'patch', got '{bump_type}'")
        sys.exit(1)

    current = read_version()
    new = bump_version(current, bump_type)
    write_version(new)

    print(f"Bumped version: {current} → {new}")
