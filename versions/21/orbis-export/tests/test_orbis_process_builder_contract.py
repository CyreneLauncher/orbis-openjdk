#!/usr/bin/env python3
"""Keep Orbis ProcessBuilder initialization distinct from process support."""

from pathlib import Path


root = Path(__file__).resolve().parents[2]
java = (root / "src/java.base/unix/classes/java/lang/ProcessImpl.java").read_text(
    encoding="utf-8"
)
native = (root / "src/java.base/unix/native/libjava/ProcessImpl_md.c").read_text(
    encoding="utf-8"
)

platform = (root / "src/java.base/share/classes/jdk/internal/util/OperatingSystem.java").read_text()
assert '"orbis".equals(PlatformProps.CURRENT_OS_STRING)' in platform
assert "return BSD;" in platform
assert "switch (OperatingSystem.current())" in java
assert '"Process creation is not supported on Orbis"' in native
print("Orbis ProcessBuilder initialization contract: PASS")
