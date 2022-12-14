/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * This file incorporates work covered by the following license notice:
 *
 *   Licensed to the Apache Software Foundation (ASF) under one or more
 *   contributor license agreements. See the NOTICE file distributed
 *   with this work for additional information regarding copyright
 *   ownership. The ASF licenses this file to you under the Apache
 *   License, Version 2.0 (the "License"); you may not use this file
 *   except in compliance with the License. You may obtain a copy of
 *   the License at http://www.apache.org/licenses/LICENSE-2.0 .
 */

#ifndef INCLUDED_CUI_SOURCE_OPTIONS_OPTUPDT_HXX
#define INCLUDED_CUI_SOURCE_OPTIONS_OPTUPDT_HXX

#include <sfx2/tabdlg.hxx>
#include <vcl/button.hxx>
#include <vcl/fixed.hxx>
#include <com/sun/star/container/XNameReplace.hpp>
#include <com/sun/star/configuration/XReadWriteAccess.hpp>

// class SvxPathTabPage --------------------------------------------------

class SvxOnlineUpdateTabPage : public SfxTabPage
{
private:
    VclPtr<CheckBox>           m_pAutoCheckCheckBox;
    VclPtr<RadioButton>        m_pEveryDayButton;
    VclPtr<RadioButton>        m_pEveryWeekButton;
    VclPtr<RadioButton>        m_pEveryMonthButton;
    VclPtr<PushButton>         m_pCheckNowButton;
    VclPtr<CheckBox>           m_pAutoDownloadCheckBox;
    VclPtr<FixedText>          m_pDestPathLabel;
    VclPtr<FixedText>          m_pDestPath;
    VclPtr<PushButton>         m_pChangePathButton;
    VclPtr<FixedText>          m_pLastChecked;
    VclPtr<CheckBox>           m_pExtrasCheckBox;
    VclPtr<FixedText>          m_pUserAgentLabel;
    OUString       m_aNeverChecked;
    OUString       m_aLastCheckedTemplate;

    DECL_LINK(FileDialogHdl_Impl, Button*, void);
    DECL_LINK(CheckNowHdl_Impl, Button*, void);
    DECL_LINK(AutoCheckHdl_Impl, Button*, void);
    DECL_LINK(ExtrasCheckHdl_Impl, Button*, void);

    css::uno::Reference< css::container::XNameReplace > m_xUpdateAccess;
    css::uno::Reference<css::configuration::XReadWriteAccess> m_xReadWriteAccess;

    void                    UpdateLastCheckedText();
    void                    UpdateUserAgent();

public:
    SvxOnlineUpdateTabPage( vcl::Window* pParent, const SfxItemSet& rSet );
    virtual ~SvxOnlineUpdateTabPage() override;
    virtual void dispose() override;

    static VclPtr<SfxTabPage>      Create( TabPageParent pParent, const SfxItemSet* rSet );

    virtual bool            FillItemSet( SfxItemSet* rSet ) override;
    virtual void            Reset( const SfxItemSet* rSet ) override;
    virtual void            FillUserData() override;
};


#endif

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
