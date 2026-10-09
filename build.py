#!/usr/bin/env python3
"""Fetch pinned sources, apply the existing PS4 port, build and audit a runtime."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
LOCK = ROOT / 'versions.lock.json'
CONF = 'orbis-x86_64-server-release'


def run(args, cwd=None, capture=False):
    return subprocess.run([str(a) for a in args], cwd=cwd, check=True,
                          text=True, stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.STDOUT if capture else None).stdout


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs(version):
    spec = json.loads(LOCK.read_text())['versions'][version]
    for item in [*spec['patches'], *spec['export_files'].values()]:
        if sha(ROOT / item['file']) != item['sha256']:
            raise RuntimeError('Changed locked input: ' + item['file'])
    return spec


def prepare(version, seed):
    spec = inputs(version)
    source = ROOT / 'work' / ('jdk' + version + 'u')
    marker = source / '.orbis-prepared.json'
    identity = {'version': version, 'lock_sha256': sha(LOCK)}
    if source.exists():
        if not marker.exists() or json.loads(marker.read_text()) != identity:
            raise RuntimeError('Existing source tree belongs to different inputs; preserve your edits and use a fresh work directory')
        return source
    source.parent.mkdir(parents=True, exist_ok=True)
    run(['git', 'init', '--quiet', source])
    run(['git', 'remote', 'add', 'origin', spec['url']], source)
    # Fetch only the pinned snapshot. Copying a partial clone's entire history can require
    # unavailable historical blobs even when all files for this snapshot are cached.
    if seed and run(['git', 'config', '--default', 'false', '--get', 'remote.origin.promisor'], seed, True).strip() == 'true':
        objects = Path(run(['git', 'rev-parse', '--path-format=absolute', '--git-path', 'objects'], seed, True).strip())
        (source / '.git/objects/info/alternates').write_text(str(objects) + '\n')
        run(['git', 'config', 'core.sparseCheckout', 'true'], source)
        (source / '.git/info/sparse-checkout').write_text(
            '/*\n!/*/\n/src/\n/make/\n/bin/\n/doc/\n/test/orbis/\n/test/hotspot/gtest/metaspace/test_metaspace_misc.cpp\n')
        print('Using partial-clone cache from ' + str(seed) + '; retain this source repository', flush=True)
    else:
        run(['git', 'fetch', '--quiet', '--depth=1', '--no-tags', seed or 'origin', spec['base']], source)
    run(['git', 'checkout', '--quiet', '--detach', spec['base']], source)
    for patch in spec['patches']:
        run(['git', 'apply', '--check', '--index', '--whitespace=nowarn', ROOT / patch['file']], source)
        run(['git', 'apply', '--index', '--whitespace=nowarn', ROOT / patch['file']], source)
    tree = run(['git', 'write-tree', '--missing-ok'], source, True).strip()
    for name, expected in spec['expected_source_tree'].items():
        actual = run(['git', 'rev-parse', tree + ':' + name], source, True).strip()
        if actual != expected:
            raise RuntimeError('Reconstructed source differs from the accepted port: ' + name)
    for name, item in spec['export_files'].items():
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / item['file'], target)
    marker.write_text(json.dumps(identity, indent=2) + '\n')
    print('Prepared JDK ' + version + ': source trees match the existing port exactly', flush=True)
    return source


def configure(source, version, boot, sdk, toolchain, jobs):
    features = ('cds,compiler2,serialgc,services,vm-structs,epsilongc,-g1gc,-jfr,-jni-check,'
                '-jvmci,-jvmti,management,nmt,parallelgc,-shenandoahgc,-zgc' if version == '17' else
                'cds,compiler1,compiler2,serialgc,parallelgc,epsilongc,services,vm-structs,management,'
                '-g1gc,-jfr,-jni-check,-jvmci,-jvmti,-shenandoahgc,-zgc')
    args = ['bash', 'configure', '--openjdk-target=x86_64-unknown-orbis',
            '--with-toolchain-type=clang', '--with-toolchain-path=' + str(sdk / 'bin'),
            '--with-sysroot=' + str(toolchain),
            '--with-extra-cflags=--target=x86_64-pc-freebsd12-elf -isystem ' + str(toolchain / 'include')
            + ' -isystem ' + str(sdk / 'target/include') + ' -B' + str(toolchain / 'lib') + ' -nostdlib',
            '--with-extra-cxxflags=--target=x86_64-pc-freebsd12-elf -isystem ' + str(toolchain / 'include/c++/v1')
            + ' -isystem ' + str(toolchain / 'include') + ' -isystem ' + str(sdk / 'target/include')
            + ' -B' + str(toolchain / 'lib') + ' -nostdlib -nostdlib++',
            '--with-extra-ldflags=--target=x86_64-pc-freebsd12-elf -L' + str(toolchain / 'lib')
            + ' -B' + str(toolchain / 'lib') + ' -nostdlib',
            '--with-jvm-variants=server', '--with-jvm-features=' + features,
            '--with-debug-level=release', '--disable-warnings-as-errors',
            '--enable-headless-only', '--with-freetype=bundled', '--with-zlib=bundled',
            '--with-boot-jdk=' + str(boot), '--with-build-jdk=' + str(boot),
            '--disable-javac-server', '--with-conf-name=' + CONF, '--with-jobs=' + str(jobs)]
    if version == '25':
        args.append('--with-native-debug-symbols=internal')
    for path in [boot / 'bin/java', sdk / 'bin/clang', toolchain / 'include']:
        if not path.exists():
            raise RuntimeError('Missing build prerequisite: ' + str(path))
    run(args, source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'configure', 'build', 'check', 'export'])
    parser.add_argument('version', choices=['17', '21', '25', 'all'])
    parser.add_argument('--seed', type=Path, help='existing local source repository; with all, its parent directory')
    parser.add_argument('--boot-jdk', type=Path, help='matching host JDK; required for configure/build/export')
    parser.add_argument('--sdk', type=Path, default=Path('/home/wonder/ps4-payload-sdk'))
    parser.add_argument('--toolchain', type=Path, default=Path('/home/wonder/PS4Toolchain'))
    parser.add_argument('--jobs', type=int, default=min(os.cpu_count() or 1, 8))
    args = parser.parse_args()
    if args.version == 'all' and args.action not in ['prepare', 'check']:
        parser.error('Build/export each version with its matching --boot-jdk')
    if args.action in ['configure', 'build', 'export'] and not args.boot_jdk:
        parser.error('This action needs a matching host --boot-jdk')
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    sdk, toolchain = args.sdk.resolve(), args.toolchain.resolve()
    versions = ['17', '21', '25'] if args.version == 'all' else [args.version]
    for version in versions:
        seed = args.seed / ('jdk' + version + 'u') if args.seed and args.version == 'all' else args.seed
        source = prepare(version, seed.resolve() if seed else None)
        if args.action == 'prepare':
            continue
        boot = args.boot_jdk.resolve() if args.boot_jdk else None
        if args.action in ['configure', 'build']:
            configure(source, version, boot, sdk, toolchain, args.jobs)
        if args.action == 'configure':
            continue
        common = ['SDK=' + str(sdk), 'TOOLCHAIN=' + str(toolchain)]
        if args.action == 'check':
            run(['make', '-C', source / 'orbis-export', 'check', *common])
            continue
        if args.action == 'build':
            run(['make', 'CONF=' + CONF, 'JOBS=' + str(args.jobs), 'images'], source)
        run(['make', '-C', source / 'orbis-export', 'jdk-export', 'DESKTOP=1', 'JDK_CONF=' + CONF,
             'BOOT_JDK=' + str(boot), *common])
        run(['make', '-C', source / 'orbis-export', 'check-artifacts', 'DESKTOP=1', 'JDK_CONF=' + CONF,
             'BOOT_JDK=' + str(boot), *common])
        export = source / 'orbis-export' / ('build-jdk-' + CONF + '-desktop/export')
        destination = ROOT / 'output' / ('jdk' + version)
        if destination.exists():
            raise RuntimeError('Output already exists; preserve it before producing a replacement: ' + str(destination))
        destination.parent.mkdir(exist_ok=True)
        shutil.copytree(export, destination)
        report = {'version': version, 'source': inputs(version), 'lock_sha256': sha(LOCK),
                  'boot_java': run([boot / 'bin/java', '-version'], capture=True),
                  'libc_sha256': sha(toolchain / 'lib/libc.a'),
                  'source_diff_sha256': hashlib.sha256(run(['git', 'diff', '--binary', inputs(version)['base'], '--', 'src', 'make', 'test'], source, True).encode()).hexdigest()}
        report['output_files'] = {p.relative_to(destination).as_posix(): sha(p) for p in sorted(destination.rglob('*')) if p.is_file()}
        (destination / 'build-provenance.json').write_text(json.dumps(report, indent=2) + '\n')
        print('Built and audited runtime: ' + str(destination), flush=True)


if __name__ == '__main__':
    main()
