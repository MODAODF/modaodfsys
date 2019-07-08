/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

/*
 This file has been autogenerated by update_pch.sh. It is possible to edit it
 manually (such as when an include file has been moved/renamed/removed). All such
 manual changes will be rewritten by the next run of update_pch.sh (which presumably
 also fixes all possible problems, so it's usually better to use it).

 Generated on 2020-09-21 15:23:13 using:
 ./bin/update_pch sc scui --cutoff=1 --exclude:system --exclude:module --include:local

 If after updating build fails, use the following command to locate conflicting headers:
 ./bin/update_pch_bisect ./sc/inc/pch/precompiled_scui.hxx "make sc.build" --find-conflicts
*/

#if PCH_LEVEL >= 1
#include <memory>
#include <utility>
#include <vector>
#endif // PCH_LEVEL >= 1
#if PCH_LEVEL >= 2
#include <osl/diagnose.h>
#include <osl/thread.h>
#include <osl/time.h>
#include <rtl/math.hxx>
#include <rtl/tencinfo.h>
#include <rtl/ustrbuf.hxx>
#include <sal/config.h>
#include <sal/types.h>
#include <vcl/event.hxx>
#include <vcl/settings.hxx>
#include <vcl/svapp.hxx>
#include <vcl/weld.hxx>
#endif // PCH_LEVEL >= 2
#if PCH_LEVEL >= 3
#include <com/sun/star/sdb/DatabaseContext.hpp>
#include <com/sun/star/sdb/XCompletedConnection.hpp>
#include <com/sun/star/sdb/XQueriesSupplier.hpp>
#include <com/sun/star/sdbcx/XTablesSupplier.hpp>
#include <com/sun/star/sheet/DataImportMode.hpp>
#include <com/sun/star/sheet/DataPilotFieldGroupBy.hpp>
#include <com/sun/star/sheet/DataPilotFieldLayoutMode.hpp>
#include <com/sun/star/sheet/DataPilotFieldReferenceItemType.hpp>
#include <com/sun/star/sheet/DataPilotFieldReferenceType.hpp>
#include <com/sun/star/sheet/DataPilotFieldShowItemsMode.hpp>
#include <com/sun/star/sheet/DataPilotFieldSortMode.hpp>
#include <com/sun/star/task/InteractionHandler.hpp>
#include <com/sun/star/uno/Any.hxx>
#include <com/sun/star/uno/Sequence.hxx>
#include <comphelper/processfactory.hxx>
#include <comphelper/string.hxx>
#include <editeng/editobj.hxx>
#include <editeng/eeitem.hxx>
#include <editeng/flditem.hxx>
#include <editeng/flstitem.hxx>
#include <i18nlangtag/languagetag.hxx>
#include <officecfg/Office/Calc.hxx>
#include <officecfg/Office/Common.hxx>
#include <sfx2/basedlgs.hxx>
#include <sfx2/docfile.hxx>
#include <sfx2/docfilt.hxx>
#include <sfx2/docinsert.hxx>
#include <sfx2/fcontnr.hxx>
#include <sfx2/filedlghelper.hxx>
#include <sfx2/objsh.hxx>
#include <sfx2/sfxdlg.hxx>
#include <sfx2/sfxresid.hxx>
#include <sfx2/tabdlg.hxx>
#include <svl/aeitem.hxx>
#include <svl/cjkoptions.hxx>
#include <svl/eitem.hxx>
#include <svl/intitem.hxx>
#include <svl/sharedstringpool.hxx>
#include <svl/style.hxx>
#include <svl/typedwhich.hxx>
#include <svl/zforlist.hxx>
#include <svtools/collatorres.hxx>
#include <svtools/ctrlbox.hxx>
#include <svtools/ehdl.hxx>
#include <svtools/inettbc.hxx>
#include <svtools/miscopt.hxx>
#include <svtools/restartdialog.hxx>
#include <svtools/sfxecode.hxx>
#include <svtools/unitconv.hxx>
#include <svx/colorbox.hxx>
#include <svx/flagsdef.hxx>
#include <svx/langbox.hxx>
#include <svx/numinf.hxx>
#include <svx/pageitem.hxx>
#include <svx/txencbox.hxx>
#include <tools/color.hxx>
#include <tools/fldunit.hxx>
#include <tools/lineend.hxx>
#include <unicode/uclean.h>
#include <unicode/ucsdet.h>
#include <unotools/collatorwrapper.hxx>
#include <unotools/localedatawrapper.hxx>
#include <unotools/transliterationwrapper.hxx>
#include <unotools/useroptions.hxx>
#endif // PCH_LEVEL >= 3
#if PCH_LEVEL >= 4
#include <appoptio.hxx>
#include <attrdlg.hxx>
#include <attrib.hxx>
#include <autoform.hxx>
#include <calcconfig.hxx>
#include <condformatdlg.hxx>
#include <condformathelper.hxx>
#include <condformatmgr.hxx>
#include <conditio.hxx>
#include <corodlg.hxx>
#include <crdlg.hxx>
#include <csvtablebox.hxx>
#include <dapidata.hxx>
#include <dapitype.hxx>
#include <datafdlg.hxx>
#include <dbdata.hxx>
#include <defaultsoptions.hxx>
#include <delcldlg.hxx>
#include <delcodlg.hxx>
#include <docoptio.hxx>
#include <docsh.hxx>
#include <document.hxx>
#include <dpgroupdlg.hxx>
#include <dpobject.hxx>
#include <dpsave.hxx>
#include <dpsdbtab.hxx>
#include <dputil.hxx>
#include <editfield.hxx>
#include <editutil.hxx>
#include <filldlg.hxx>
#include <filterentries.hxx>
#include <formula/grammar.hxx>
#include <formulaopt.hxx>
#include <global.hxx>
#include <globalnames.hxx>
#include <groupdlg.hxx>
#include <helpids.h>
#include <hfedtdlg.hxx>
#include <imoptdlg.hxx>
#include <impex.hxx>
#include <inscldlg.hxx>
#include <inscodlg.hxx>
#include <instbdlg.hxx>
#include <lbseldlg.hxx>
#include <linkarea.hxx>
#include <miscuno.hxx>
#include <mtrindlg.hxx>
#include <mvtabdlg.hxx>
#include <namecrea.hxx>
#include <namepast.hxx>
#include <opredlin.hxx>
#include <optutil.hxx>
#include <patattr.hxx>
#include <pfiltdlg.hxx>
#include <printopt.hxx>
#include <pvfundlg.hxx>
#include <queryentry.hxx>
#include <rangenam.hxx>
#include <rangeutl.hxx>
#include <scabstdlg.hxx>
#include <scendlg.hxx>
#include <scitems.hxx>
#include <scmod.hxx>
#include <scresid.hxx>
#include <scui_def.hxx>
#include <scuiasciiopt.hxx>
#include <scuiautofmt.hxx>
#include <scuiimoptdlg.hxx>
#include <scuitphfedit.hxx>
#include <shtabdlg.hxx>
#include <sortdlg.hxx>
#include <sortkeydlg.hxx>
#include <strindlg.hxx>
#include <strings.hxx>
#include <styledlg.hxx>
#include <subtdlg.hxx>
#include <tabbgcolordlg.hxx>
#include <tablink.hxx>
#include <tabpages.hxx>
#include <tabvwsh.hxx>
#include <textdlgs.hxx>
#include <textimportoptions.hxx>
#include <tpcalc.hxx>
#include <tpcompatibility.hxx>
#include <tpdefaults.hxx>
#include <tpformula.hxx>
#include <tphf.hxx>
#include <tpprint.hxx>
#include <tpsort.hxx>
#include <tpstat.hxx>
#include <tpsubt.hxx>
#include <tptable.hxx>
#include <tpusrlst.hxx>
#include <tpview.hxx>
#include <uiitems.hxx>
#include <userlist.hxx>
#include <viewdata.hxx>
#include <viewopti.hxx>
#endif // PCH_LEVEL >= 4

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */