#!/usr/bin/env python3
"""Socket available() on Orbis asks with FreeBSD's FIONREAD and never fails.

The SDK header's FIONREAD is Linux's 0x541B, which libkernel refuses with EACCES; available()
then threw, BufferedInputStream asks it between reads, and every HTTP body longer than one read
failed (Minecraft's skins, left as empty cache files)."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[2]
candidates = [root / 'src/java.base/unix/native/libnet/net_util_md.c',
              root / 'src/java.base/unix/native/libnio/ch/Net.c']
checked = 0
for path in candidates:
    text = path.read_text()
    for name in ('NET_SocketAvailable(int s, int *pbytes)', 'Java_sun_nio_ch_Net_available('):
        start = text.find(name)
        if start < 0:
            continue
        body = text[start:text.index('\n}\n', start)]
        if 'FIONREAD' not in body and 'NET_SocketAvailable' in body:
            continue  # forwards to NET_SocketAvailable, checked there
        orbis = re.search(r'#if defined\(ORBIS\)(.*?)#else', body, re.S)
        assert orbis, f'{path.name}: {name} has no Orbis branch'
        branch = orbis.group(1)
        assert '0x4004667fUL' in branch, f'{path.name}: {name} must use FreeBSD FIONREAD'
        assert 'IOS_THROWN' not in branch and 'return -1' not in branch, \
            f'{path.name}: {name} must report 0 instead of failing'
        checked += 1
assert checked == 1, f'expected one Orbis available() implementation, found {checked}'
print('Socket available() uses FreeBSD FIONREAD and never fails')
