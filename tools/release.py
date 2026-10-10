#!/usr/bin/env python3
"""Pack audited runtime exports as release assets that keep file modes and provenance."""
import argparse
import hashlib
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def asset_name(version):
    return 'orbis-jdk' + version + '-x86_64.tar.xz'


def normalized(info):
    info.uid = info.gid = 0
    info.uname = info.gname = ''
    info.mtime = 0
    return info


def pack(version, output, dist):
    runtime = output / ('jdk' + version)
    for name in ('release', 'build-provenance.json', 'lib/server/libjvm.prx'):
        if not (runtime / name).is_file():
            raise ValueError('Incomplete runtime export: ' + str(runtime / name))
    dist.mkdir(parents=True, exist_ok=True)
    archive = dist / asset_name(version)
    if archive.exists():
        raise ValueError('Release asset already exists: ' + str(archive))
    with tarfile.open(archive, 'w:xz', preset=9) as target:
        for path in [runtime, *sorted(runtime.rglob('*'))]:
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise ValueError('Unsupported runtime entry: ' + str(path))
            target.add(path, arcname=path.relative_to(output).as_posix(), recursive=False, filter=normalized)
    print(archive)
    return archive


def checksums(dist):
    assets = sorted(p for p in dist.iterdir() if p.is_file() and p.name != 'SHA256SUMS')
    (dist / 'SHA256SUMS').write_text(''.join(digest(p) + '  ' + p.name + '\n' for p in assets))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['pack', 'checksums'])
    parser.add_argument('versions', nargs='*', choices=['17', '21', '25'])
    parser.add_argument('--output', type=Path, default=ROOT / 'output')
    parser.add_argument('--dist', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    if args.action == 'pack':
        if not args.versions:
            parser.error('Name the runtime versions to pack')
        for version in args.versions:
            pack(version, args.output, args.dist)
    else:
        checksums(args.dist)


if __name__ == '__main__':
    main()
