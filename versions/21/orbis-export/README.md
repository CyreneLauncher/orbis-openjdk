# Orbis runtime export

Turns this JDK port's completed build into the runtime the Orbis launcher's runner loads
(the sibling `../orbis-launcher`, which builds the PS4 application itself):

- `tools/build_native_modules.py` relinks each JDK native library as a SELF module with the Orbis
  runtime objects (`orbis_runtime.c`, `native_dlfcn.c`, `orbis_initializers.c`, TLS support) and
  audits its imports against `orbis_native_policy.json`;
- `make jdk-export` adds a jlink image of the runtime modules and assembles the upload tree
  (`tools/export_jdk.py`), validated by `tools/check_native_package.py`.

```sh
make -C orbis-export jdk-export JDK_CONF=orbis-x86_64-server-release DESKTOP=1
make -C orbis-export check
make -C orbis-export check-artifacts JDK_CONF=orbis-x86_64-server-release DESKTOP=1
```

The export lands in `build-jdk-<configuration>[-desktop]/export/`; upload its contents to
`/data/orbis-jdk/jdk21/release-desktop/`. JDK 21 is the launcher's optional runner: when it is
there, the launcher offers Minecraft 1.20.5 to 1.21.4 and starts those versions on it, while JDK 17
stays the default. The runner and the launcher recognise a runtime by its `release` file and
`lib/server/libjvm.prx`.

Configure and build the JDK first (`docs/orbis-migration/tools/configure-orbis.sh`, then
`make CONF=orbis-x86_64-server-release images`); the jlink target platform is `linux-amd64`
(`MODULE_TARGET_PLATFORM`), as the host JDK 21's jlink knows no Orbis platform.
