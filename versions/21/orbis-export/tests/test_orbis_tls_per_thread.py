#!/usr/bin/env python3
"""Every native module whose thread-locals go beyond musl's locale pointer links the per-thread TLS
(orbis_prx_tls.c: its thread table and image bounds), not orbis_tls.c's one block shared by all threads.
JDK 21's libjvm keeps WorkerThread::_worker_id thread-local; shared, every Parallel GC worker used
the same promotion manager and the heap was corrupted on the PS4."""
from pathlib import Path
import subprocess
import sys

paths = [Path(p) for p in sys.argv[1:]]
assert paths, 'pass the native modules (build-jdk-*/native/*.so)'
checked = 0
for path in paths:
    table = subprocess.run(['llvm-readelf', '-s', str(path)], check=True, text=True,
                           stdout=subprocess.PIPE).stdout
    tls = {line.split()[7] for line in table.splitlines()
           if len(line.split()) >= 8 and line.split()[3] == 'TLS'}
    if not tls - {'__musl_current_locale'}:
        continue
    checked += 1
    names = {line.split()[-1] for line in table.splitlines() if line.split()}
    assert {'orbis_prx_tls_slots', '__orbis_tls_image_start', '__orbis_tls_image_end'} <= names, \
        f'{path.name} has thread-locals {sorted(tls)} but links the shared TLS block'
    assert 'orbis_tls_block' not in names, f'{path.name} links both TLS implementations'
print(f'Per-thread TLS in every module that needs it ({checked} checked)')
