# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

$(eval $(call gb_Package_Package,macro_userconfig,$(SRCDIR)/extras/source/userconfig))

$(eval $(call gb_Package_add_files_with_dir,macro_userconfig,$(LIBO_SHARE_FOLDER)/userconfig,\
	user/extensions/bundled/extensions.pmap \
	user/extensions/bundled/registry/com.sun.star.comp.deployment.bundle.PackageRegistryBackend/backenddb.xml \
	user/extensions/bundled/registry/com.sun.star.comp.deployment.component.PackageRegistryBackend/backenddb.xml \
	user/extensions/bundled/registry/com.sun.star.comp.deployment.component.PackageRegistryBackend/common_.rdb \
	user/extensions/bundled/registry/com.sun.star.comp.deployment.component.PackageRegistryBackend/common.rdb \
	user/extensions/bundled/registry/com.sun.star.comp.deployment.component.PackageRegistryBackend/unorc \
	user/extensions/bundled/registry/com.sun.star.comp.deployment.configuration.PackageRegistryBackend/backenddb.xml \
	user/extensions/bundled/registry/com.sun.star.comp.deployment.configuration.PackageRegistryBackend/configmgr.ini \
	user/extensions/bundled/registry/com.sun.star.comp.deployment.script.PackageRegistryBackend/backenddb.xml \
))

# vim: set noet sw=4 ts=4:
