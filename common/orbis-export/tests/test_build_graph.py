#!/usr/bin/env python3
"""The export graph converts a completed JDK build; CLI changes update settings without stale reuse."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / 'Makefile'


def run_make(*arguments, cwd=ROOT):
    return subprocess.run(['make', '-f', str(MAKEFILE), *arguments], cwd=cwd,
                          text=True, capture_output=True, check=True)


with tempfile.TemporaryDirectory() as temporary:
    export = Path(temporary) / 'jdk'
    source = Path(temporary) / 'src/java.base/bsd/native/libnet/bsd_close.c'
    source.parent.mkdir(parents=True)
    source.touch()
    arguments = [f'EXPORT_BUILD={export}', f'REPO_ROOT={temporary}']
    path = export / 'settings'
    run_make(str(path), *arguments, 'RUNTIME_MODULES=first')
    first = path.stat().st_mtime_ns
    run_make(str(path), *arguments, 'RUNTIME_MODULES=first')
    assert path.stat().st_mtime_ns == first
    run_make(str(path), *arguments, 'RUNTIME_MODULES=second')
    assert path.stat().st_mtime_ns != first
    assert 'second' in path.read_text()
    release = run_make('-n', 'jdk-export', *arguments,
                       'JDK_CONF=orbis-x86_64-server-release').stdout
    debug = run_make('-n', 'jdk-export', *arguments,
                     'JDK_CONF=orbis-x86_64-server-fastdebug').stdout
    assert '/build/orbis-x86_64-server-release/jdk' in release
    assert '/build/orbis-x86_64-server-fastdebug/jdk' in debug
    assert '--profile' not in release and '--jimage' in release
    assert '--strip-debug' not in release, 'JDK classes must keep SourceFile/LineNumberTable'
    # The application (runner eboot, app.jar, PKG) is built in the Orbis launcher project.
    for forbidden in ('launcher.c', 'app.jar', 'pkg_build', 'eboot'):
        assert forbidden not in release, forbidden

print('Export dependency boundary and changed settings tracking passed')
