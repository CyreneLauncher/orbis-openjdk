#!/usr/bin/env python3
"""Contract tests for the JDK's side of the one-shot HotSpot mapping trace.

The runner (Orbis launcher project) arms the trace; HotSpot writes it, and the loader adapter
routes its lines to the dedicated log.
"""

from pathlib import Path

root = Path(__file__).resolve().parents[1]
runtime = (root.parent / "src/hotspot/os/orbis/os_orbis.cpp").read_text()
native = (root / "tools/native_dlfcn.c").read_text()

assert '"/data/orbis-jdk/runner/vmmap-probe.txt"' in runtime
assert '"/data/orbis-jdk/logs/orbis-vmmap.log"' in native
assert 'strncmp(text, "orbis-vmmap ",' in native
assert '::unlink(marker_path)' in runtime
assert 'getenv("ORBIS_VM_MAP_TRACE")' not in runtime
assert "size < 64 * 1024" in runtime
assert "success ? 1024 : 256" in runtime
assert "trace-limit-reached" in runtime
assert "size < 1024 * 1024" not in runtime
assert "caller=0x%" in runtime
trace_body = runtime[runtime.index("void orbis_vm_map_trace("):runtime.index("// NOTE: Bsd kernel")]
assert 'success && strncmp(operation, "commit-", 7) == 0' in trace_body
assert 'op=commit-successes-suppressed count=%u' in trace_body
assert "commit_success_events" in trace_body

print("HotSpot mapping trace writer and dedicated log contract passed")
