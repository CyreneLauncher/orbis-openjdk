#!/usr/bin/env python3
"""Save edits in a prepared JDK as its patch and update the source lock."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import LOCK, ROOT, prepare, run, sha

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('version', choices=['17', '21', '25'])
args = parser.parse_args()
source = prepare(args.version, None)
old_hash = sha(LOCK)
lock = json.loads(LOCK.read_text())
spec = lock['versions'][args.version]
# These are the only source paths exported; caches and binaries never enter the patch.
run(['git', 'add', '--', 'src', 'make', 'test'], source)
patch = run(['git', 'diff', '--binary', spec['base'], '--', 'src', 'make', 'test'], source, True)
path = ROOT / spec['patches'][0]['file']
path.write_text(patch)
spec['patches'][0]['sha256'] = sha(path)
tree = run(['git', 'write-tree', '--missing-ok'], source, True).strip()
for name in spec['expected_source_tree']:
    spec['expected_source_tree'][name] = run(['git', 'rev-parse', tree + ':' + name], source, True).strip()
LOCK.write_text(json.dumps(lock, indent=2) + '\n')
for version in lock['versions']:
    marker = ROOT / 'work' / ('jdk' + version + 'u') / '.orbis-prepared.json'
    if marker.exists():
        identity = json.loads(marker.read_text())
        if identity['lock_sha256'] == old_hash:
            identity['lock_sha256'] = sha(LOCK)
            marker.write_text(json.dumps(identity, indent=2) + '\n')
print('Saved ' + str(path) + '; review and commit the patch and versions.lock.json together')
