#!/usr/bin/env python3
"""Check the Orbis access fallback used by Files.createDirectories."""

from pathlib import Path


source = Path("../src/java.base/unix/native/libnio/fs/UnixNativeDispatcher.c").read_text()
access = source.split("Java_sun_nio_fs_UnixNativeDispatcher_access0", 1)[1].split("\nJNIEXPORT", 1)[0]
assert "orbis_stat_path(env, path, &buf)" in access
assert "orbis_access_allowed(&buf, amode)" in access
assert "return orbis_normalize_missing_errno(errno);" in access
assert "return EACCES" in access or "? 0 : EACCES" in access
assert "JNIEXPORT jint JNICALL\nJava_sun_nio_fs_UnixNativeDispatcher_access0" in source
assert "Java_sun_nio_fs_UnixNativeDispatcher_exists0" not in source
print("Orbis JDK 21 errno-returning NIO access contract passed")
