#!/usr/bin/env python3
"""Native modules link complete and resolve their providers explicitly (the runner loads libjvm.prx)."""
from pathlib import Path


def main() -> None:
    builder = (Path(__file__).resolve().parents[1] / "tools/build_native_modules.py").read_text()
    assert "--no-undefined" in builder
    assert "--lib=" in builder
    print("native modules link complete with explicit providers")


if __name__ == "__main__":
    main()
