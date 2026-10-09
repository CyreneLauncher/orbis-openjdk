#!/bin/bash
# Configures the Orbis (PS4) cross build of this JDK 25 port; then: make CONF=orbis-x86_64-server-release images
set -eu
cd "$(dirname "$0")/.."
boot_jdk=${BOOT_JDK:-"$PWD/.boot-jdks/jdk-25"}
bash configure \
 --openjdk-target=x86_64-unknown-orbis \
 --with-toolchain-type=clang \
 --with-toolchain-path=/home/wonder/ps4-payload-sdk/bin \
 --with-sysroot=/home/wonder/PS4Toolchain \
 --with-extra-cflags='--target=x86_64-pc-freebsd12-elf -isystem /home/wonder/PS4Toolchain/include -isystem /home/wonder/ps4-payload-sdk/target/include -B/home/wonder/PS4Toolchain/lib -nostdlib' \
 --with-extra-cxxflags='--target=x86_64-pc-freebsd12-elf -isystem /home/wonder/PS4Toolchain/include/c++/v1 -isystem /home/wonder/PS4Toolchain/include -isystem /home/wonder/ps4-payload-sdk/target/include -B/home/wonder/PS4Toolchain/lib -nostdlib -nostdlib++' \
 --with-extra-ldflags='--target=x86_64-pc-freebsd12-elf -L/home/wonder/PS4Toolchain/lib -B/home/wonder/PS4Toolchain/lib -nostdlib' \
 --with-jvm-variants=server \
 --with-jvm-features=cds,compiler1,compiler2,serialgc,parallelgc,epsilongc,services,vm-structs,management,-g1gc,-jfr,-jni-check,-jvmci,-jvmti,-shenandoahgc,-zgc \
 --with-debug-level=release --disable-warnings-as-errors \
 --with-native-debug-symbols=internal \
 --enable-headless-only --with-freetype=bundled --with-zlib=bundled \
 --with-boot-jdk="$boot_jdk" --with-build-jdk="$boot_jdk" \
 --disable-javac-server --with-conf-name=orbis-x86_64-server-release
