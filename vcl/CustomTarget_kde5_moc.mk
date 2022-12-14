# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

$(eval $(call gb_CustomTarget_CustomTarget,vcl/unx/kde5))

$(call gb_CustomTarget_get_target,vcl/unx/kde5) : \
	$(call gb_CustomTarget_get_workdir,vcl/unx/kde5)/KDE5FilePicker.moc

$(call gb_CustomTarget_get_workdir,vcl/unx/kde5)/%.moc : \
		$(SRCDIR)/vcl/unx/kde5/%.hxx \
		| $(call gb_CustomTarget_get_workdir,vcl/unx/kde5)/.dir
	$(call gb_Output_announce,$(subst $(WORKDIR)/,,$@),$(true),MOC,1)
	$(MOC5) $< -o $@

# vim: set noet sw=4:
