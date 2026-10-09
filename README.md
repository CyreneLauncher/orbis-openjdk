# Orbis OpenJDK builds

One build repository for the existing PS4 OpenJDK 17, 21 and 25 ports. It stores pinned upstream revisions, the PS4 changes and export tools. Full JDK sources and binaries are generated locally under ignored `work/` and `output/` directories.

This reorganizes the working ports without rewriting their VM code. The upstream baseline is the FreeBSD-capable `battleblow/jdk17u`, `jdk21u` and `jdk25u` fork at the exact commits in `versions.lock.json`, rather than claiming the patches apply to arbitrary OpenJDK releases. Original port commit IDs are also recorded.

## What is a patch?

A patch is a text file describing changes to source files: which lines to add, remove or replace. It is not compiled code and does not replace the JDK source. The preparation command downloads the full source, checks out the pinned revision and applies the version's patch. You then have ordinary editable Java and C++ files under `work/jdk17u`, `work/jdk21u` or `work/jdk25u`.

The initial patches reproduce the current ports' entire `src/`, `make/` and `test/` trees exactly. Preparation verifies their Git tree hashes. Export files are verified separately using SHA256. Historical migration logs, duplicate research patches and application builds are excluded.

## Layout

- `patches/17`, `patches/21`, `patches/25`: version-specific PS4 source changes.
- `common/orbis-export`: 67 byte-identical export/support files shared across all versions.
- `versions/17`, `versions/21`, `versions/25`: export files that actually differ.
- `versions.lock.json`: exact baseline, original port revisions, input hashes and expected source trees.
- `build.py`: preparation, configuration, compilation, runtime export and checks.

The existing port is substantial, but primarily additive: approximately 9,800–10,000 added lines are new platform files; approximately 3,500 added lines and 160–180 removed lines change existing source/build files per JDK. Consolidation itself adds no changes to those sources. Each version keeps its own patch so API differences remain explicit.

## Requirements

Use a Linux x86_64 build host with Python 3, Git, GNU Make, Bash, autoconf, zip/unzip and the normal OpenJDK Linux build dependencies. Supply the existing PS4 payload SDK and PS4Toolchain, including the port's compatible libc/headers. A generic stock compiler or stock system libc is insufficient. SDK/toolchain paths are parameters, not fetched silently. Each JDK needs a matching host boot JDK (17, 21 or 25).

The PS4 SDK/toolchain is a separate prerequisite; this repository does not contain proprietary SDK files or large compiler binaries. A completed build records the libc hash and boot-JDK version in its provenance report.

## Prepare the source

Fetch sources from the configured upstream:

```sh
python3 build.py prepare all
```

For this workspace, use the existing local repositories to avoid downloading them again:

```sh
python3 build.py prepare all --seed ..
```

Preparation refuses to overwrite an existing checkout with different inputs. It never resets your original JDK repositories. Existing matching prepared trees are reused, including local development edits.

## Build and export

Run each version with its matching host JDK; replace paths for your machine:

```sh
python3 build.py build 17 --boot-jdk /usr/lib/jvm/java-17-openjdk-amd64 --sdk /path/to/ps4-payload-sdk --toolchain /path/to/PS4Toolchain
python3 build.py build 21 --boot-jdk /path/to/host-jdk21 --sdk /path/to/ps4-payload-sdk --toolchain /path/to/PS4Toolchain
python3 build.py build 25 --boot-jdk /path/to/host-jdk25 --sdk /path/to/ps4-payload-sdk --toolchain /path/to/PS4Toolchain
```

`build` configures the PS4 target, runs the actual OpenJDK `images` build, relinks/signs the native modules, creates the desktop runtime image, runs package/binary checks, and copies the audited runtime to `output/jdk17`, `output/jdk21` or `output/jdk25`. It stops on any failed step. It does not package or upload the launcher.

For separate stages:

```sh
python3 build.py configure 25 --boot-jdk /path/to/host-jdk25
python3 build.py check all
python3 build.py export 25 --boot-jdk /path/to/host-jdk25
```

`check` runs host/source checks. Export/artifact checks require compiled modules. Host checks and package checks do not prove the runtime works on a PS4; launch testing is still required. Existing output directories are preserved rather than silently overwritten.

## Development

Edit the prepared source normally, build it and test it on the console. The builder allows local source edits and records their diff hash. Save those edits back into the small build repository:

```sh
python3 tools/save_patch.py 25
```

This stages only `src/`, `make/` and `test/` in the prepared checkout, writes the version's source patch, and updates its hash and expected tree IDs. Review and commit the patch and lock together. New source files are included; build outputs are excluded. Keep unrelated upstream changes out of the patch.

Edit common export files only when the same change is appropriate for all three versions. Keep differences under the respective version directory. Update the corresponding input hashes after review. A changed lock requires preparing a fresh working tree; preserve development edits first.

The launcher remains in the independent `orbis-launcher` repository and continues to select the appropriate runtime for each Minecraft version. Accounts are a launcher concern; JDK builds do not create users.

## Licensing

The upstream JDK source and its patches retain the OpenJDK GPLv2 license with the Classpath Exception where applicable. Refer to each downloaded source tree's `LICENSE` and `ADDITIONAL_LICENSE_INFO`. Export/support files retain their original notices and licenses. Bundled third-party font notices remain alongside their files.

The repository follows the fetch/patch/build/package organization used by [Amethyst's OpenJDK build project](https://github.com/AngelAuraMC/angelauramc-openjdk-build); it does not import Android/iOS patches into the PS4 runtime.

When `--seed` points at a partial clone, preparation borrows that repository's object cache and checks out the build sources and port tests, avoiding unrelated missing upstream test blobs. Retain that seed repository while using the prepared tree. Preparing from the upstream URL produces an independent snapshot. The complete tree hashes are still verified in either case.

One test-tool adjustment in this repository makes JDK 17's stat ABI check use the checked-in JNI headers rather than requiring a separately built fastdebug image. It does not change JDK source or exported runtime behavior.
