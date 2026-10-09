#!/usr/bin/env bash
# Supply BOOT_JDK17, BOOT_JDK21 and BOOT_JDK25; remaining arguments go to build.py.
set -euo pipefail
build_root=$(cd -- "$(dirname -- "$0")/.." && pwd)
for version in 17 21 25; do
    boot_variable="BOOT_JDK${version}"
    boot_directory=${!boot_variable:-}
    if [[ -z "$boot_directory" ]]; then
        echo "Set $boot_variable to the matching host JDK directory" >&2
        exit 1
    fi
    python3 "$build_root/build.py" build "$version" --boot-jdk "$boot_directory" "$@"
done
