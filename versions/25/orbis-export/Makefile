# Exports this JDK port's completed build as a runtime the Orbis launcher's runner loads
# (the sibling ../orbis-launcher builds the application). Never invokes the upstream JDK build.
PROJECT_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
REPO_ROOT := $(abspath $(PROJECT_DIR)/..)
JDK_CONF ?= orbis-x86_64-server-release
DESKTOP ?= 0
ifneq ($(DESKTOP),0)
ifneq ($(DESKTOP),1)
$(error DESKTOP must be exactly 0 or 1)
endif
endif
DESKTOP_FLAG := $(if $(filter 1,$(DESKTOP)),--desktop)
DESKTOP_FONT_INPUTS := $(wildcard $(PROJECT_DIR)/runtime-data/desktop/fonts/*)
SDK ?= /home/wonder/ps4-payload-sdk
TOOLCHAIN ?= /home/wonder/PS4Toolchain
BOOT_JDK ?= $(REPO_ROOT)/.boot-jdks/jdk-25
JDK_IMAGE ?= $(REPO_ROOT)/build/$(JDK_CONF)/jdk
JMOD ?= $(BOOT_JDK)/bin/jmod
JLINK ?= $(BOOT_JDK)/bin/jlink
JIMAGE ?= $(BOOT_JDK)/bin/jimage
PYTHON ?= python3
PAID ?= 0x3800000000000011
EXPORT_BUILD := $(PROJECT_DIR)/build-jdk-$(JDK_CONF)$(if $(filter 1,$(DESKTOP)),-desktop)
NATIVE := $(EXPORT_BUILD)/native
RUNTIME_VERSION ?= 25.0.4
# JDK 25's jlink, from the host's JDK, knows platforms only by upstream OperatingSystem names and
# uses them for the image layout, which for Orbis is the Unix one (make/autoconf/platform.m4
# records the same for the JDK build's own modules). The runtime still reports and dispatches Orbis.
MODULE_TARGET_PLATFORM ?= linux-amd64
JLINK_COMPRESS ?= 0
RUNTIME_MODULES ?= java.desktop,java.datatransfer,java.prefs,java.base,java.logging,java.xml,java.net.http,java.transaction.xa,java.sql,java.naming,java.security.jgss,java.security.sasl,java.sql.rowset,java.xml.crypto,java.scripting,java.rmi,jdk.charsets,jdk.localedata,jdk.unsupported,jdk.zipfs,java.compiler,jdk.httpserver,jdk.naming.dns,jdk.naming.rmi,jdk.net,jdk.nio.mapmode,jdk.security.auth,jdk.security.jgss,jdk.xml.dom,jdk.dynalink,jdk.crypto.ec,java.management,jdk.management

.PHONY: all jdk-export check check-artifacts clean FORCE
all: jdk-export
FORCE:
$(EXPORT_BUILD)/settings: FORCE
	@mkdir -p $(EXPORT_BUILD)
	@printf '%s\n' '$(DESKTOP)|$(JDK_IMAGE)|$(RUNTIME_MODULES)|$(RUNTIME_VERSION)|$(MODULE_TARGET_PLATFORM)|$(JLINK_COMPRESS)|$(JMOD)|$(JLINK)|$(JIMAGE)|$(SDK)|$(TOOLCHAIN)|$(PAID)' > $@.tmp
	@sha256sum $(PROJECT_DIR)/Makefile >> $@.tmp
	@sha256sum $(PROJECT_DIR)/tools/orbis_native_modules.py $(PROJECT_DIR)/tools/audit_native_providers.py $(DESKTOP_FONT_INPUTS) >> $@.tmp
	@cmp -s $@.tmp $@ && rm $@.tmp || mv $@.tmp $@
$(EXPORT_BUILD)/jvm-link.x: $(TOOLCHAIN)/link.x $(PROJECT_DIR)/tools/prepare_jvm_link.py
	mkdir -p $(dir $@)
	$(PYTHON) $(PROJECT_DIR)/tools/prepare_jvm_link.py $< $@
# Content-compared input inventories detect removals and replacements with older
# mtimes. These recipes run only when export intermediates are requested.
$(EXPORT_BUILD)/native-inputs: FORCE
	@mkdir -p $(EXPORT_BUILD)
	@find $(JDK_IMAGE)/../hotspot/variant-server/libjvm/objs $(JDK_IMAGE)/../support/native $(TOOLCHAIN)/lib/libc.a -type f -printf '%p %T@ %C@ %s %i\n' > $@.unsorted || { rm -f $@.unsorted; exit 1; }
	@LC_ALL=C sort $@.unsorted > $@.tmp
	@rm $@.unsorted
	@cmp -s $@.tmp $@ && rm $@.tmp || mv $@.tmp $@
$(EXPORT_BUILD)/module-inputs: FORCE
	@mkdir -p $(EXPORT_BUILD)
	@find $(JDK_IMAGE)/modules -type f -printf '%p %T@ %C@ %s %i\n' > $@.unsorted || { rm -f $@.unsorted; exit 1; }
	@LC_ALL=C sort $@.unsorted > $@.tmp
	@rm $@.unsorted
	@cmp -s $@.tmp $@ && rm $@.tmp || mv $@.tmp $@
NATIVE_INPUTS := $(if $(filter jdk-export,$(MAKECMDGOALS)),$(shell find $(JDK_IMAGE)/../hotspot/variant-server/libjvm/objs $(JDK_IMAGE)/../support/native $(TOOLCHAIN)/lib/libc.a -type f 2>/dev/null))
$(EXPORT_BUILD)/native.stamp: $(EXPORT_BUILD)/native-inputs $(NATIVE_INPUTS) $(EXPORT_BUILD)/settings $(EXPORT_BUILD)/jvm-link.x $(wildcard $(PROJECT_DIR)/tools/*.c $(PROJECT_DIR)/tools/*.h) $(PROJECT_DIR)/tools/build_native_modules.py $(PROJECT_DIR)/tools/orbis_native_modules.py $(PROJECT_DIR)/tools/audit_native_providers.py $(DESKTOP_FONT_INPUTS) $(PROJECT_DIR)/tools/orbis_native_policy.json $(PROJECT_DIR)/tools/audit_orbis_binaries.py
	cd $(PROJECT_DIR) && $(PYTHON) $(PROJECT_DIR)/tools/build_native_modules.py --sdk $(SDK) --toolchain $(TOOLCHAIN) --jdk $(JDK_IMAGE) --paid $(PAID) --policy $(PROJECT_DIR)/tools/orbis_native_policy.json --output $(NATIVE) --link-script $(EXPORT_BUILD)/jvm-link.x $(DESKTOP_FLAG)
	touch $@
MODULE_INPUTS := $(if $(filter jdk-export,$(MAKECMDGOALS)),$(shell find $(JDK_IMAGE)/modules -type f 2>/dev/null))
$(EXPORT_BUILD)/runtime-jmods.stamp: $(EXPORT_BUILD)/module-inputs $(MODULE_INPUTS) $(EXPORT_BUILD)/settings
	mkdir -p $(EXPORT_BUILD)/jmods
	rm -f $(EXPORT_BUILD)/jmods/*.jmod
	for module in $$(printf '%s' '$(RUNTIME_MODULES)' | tr ',' ' '); do $(JMOD) create --class-path $(JDK_IMAGE)/modules/$$module --module-version $(RUNTIME_VERSION) --target-platform $(MODULE_TARGET_PLATFORM) $(EXPORT_BUILD)/jmods/$$module.jmod || exit; done
	touch $@
# No --strip-debug: it drops SourceFile and LineNumberTable from every JDK class, so JDK stack
# frames have no file name - and Minecraft's crash reporter, which compares frame file names,
# then fails with a NullPointerException and loses the original crash.
$(EXPORT_BUILD)/runtime-image.stamp: $(EXPORT_BUILD)/runtime-jmods.stamp
	rm -rf $(EXPORT_BUILD)/runtime-image
	$(JLINK) --module-path $(EXPORT_BUILD)/jmods --add-modules $(RUNTIME_MODULES) --output $(EXPORT_BUILD)/runtime-image --no-header-files --no-man-pages $(if $(filter 0,$(JLINK_COMPRESS)),,--compress=$(JLINK_COMPRESS))
	touch $@
# Always assemble fresh so changed configuration/legal/data cannot survive stale staging.
jdk-export: $(EXPORT_BUILD)/native.stamp $(EXPORT_BUILD)/runtime-image.stamp
	$(PYTHON) $(PROJECT_DIR)/tools/export_jdk.py --jdk $(JDK_IMAGE) --runtime-image $(EXPORT_BUILD)/runtime-image --native $(NATIVE) --output $(EXPORT_BUILD)/export --jimage $(JIMAGE) $(DESKTOP_FLAG)
	$(PYTHON) $(PROJECT_DIR)/tools/check_native_package.py $(EXPORT_BUILD)/export --jimage $(JIMAGE)
check:
	cd $(PROJECT_DIR) && PYTHONDONTWRITEBYTECODE=1 $(PYTHON) tests/run_checks.py --sdk $(SDK) --toolchain $(TOOLCHAIN)
check-artifacts:
	cd $(PROJECT_DIR) && PYTHONDONTWRITEBYTECODE=1 $(PYTHON) tests/test_audit_orbis_binaries.py --native $(NATIVE)
	cd $(PROJECT_DIR) && $(PYTHON) tests/test_prx_initializers.py $(NATIVE)/*.so
	cd $(PROJECT_DIR) && $(PYTHON) tests/test_orbis_runtime_binary.py $(NATIVE)/*.so
	cd $(PROJECT_DIR) && $(PYTHON) tests/test_orbis_tls_per_thread.py $(NATIVE)/*.so
	cd $(PROJECT_DIR) && $(PYTHON) tests/test_orbis_signal_diagnostic_binary.py $(NATIVE)/libjvm.prx
	cd $(PROJECT_DIR) && RUNTIME_IMAGE=$(EXPORT_BUILD)/runtime-image JIMAGE=$(JIMAGE) RUNTIME_MODULES='$(RUNTIME_MODULES)' $(PYTHON) tests/test_runtime_image_modules.py
clean:
	rm -rf $(PROJECT_DIR)/build-jdk-*

