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

#include <sal/config.h>

#include <osl/diagnose.h>
#include <comphelper/lok.hxx>
#include <vcl/settings.hxx>
#include <unotools/viewoptions.hxx>
#include <cuihyperdlg.hxx>
#include <hlinettp.hxx>
#include <hlmailtp.hxx>
#include <hldoctp.hxx>
#include <hldocntp.hxx>
#include <bitmaps.hlst>
#include <svx/svxids.hrc>
#include <dialmgr.hxx>
#include <strings.hrc>
#include <vector>

using ::com::sun::star::uno::Reference;
using ::com::sun::star::frame::XFrame;


//#                                                                      #
//# Childwindow-Wrapper-Class                                            #
//#                                                                      #


SvxHlinkCtrl::SvxHlinkCtrl( sal_uInt16 _nId, SfxBindings & rBindings, SvxHpLinkDlg* pDlg )
    : SfxControllerItem ( _nId, rBindings )
    , aRdOnlyForwarder  ( SID_READONLY_MODE, *this )
{
    pParent = pDlg;
}

void SvxHlinkCtrl::dispose()
{
    aRdOnlyForwarder.dispose();
    ::SfxControllerItem::dispose();
}

void SvxHlinkCtrl::StateChanged( sal_uInt16 nSID, SfxItemState eState,
                                 const SfxPoolItem* pState )
{
    if ( eState == SfxItemState::DEFAULT && !pParent->IsDisposed() )
    {
        switch ( nSID )
        {
            case SID_HYPERLINK_GETLINK :
            {
                pParent->SetPage( static_cast<const SvxHyperlinkItem*>(pState) );
            }
            break;
            case SID_READONLY_MODE :
            {
                pParent->SetReadOnlyMode( static_cast<const SfxBoolItem*>(pState)->GetValue() );
            }
            break;
        }
    }
}

//#                                                                      #
//# Hyperlink - Dialog                                                   #
//#                                                                      #

SvxHpLinkDlg::SvxHpLinkDlg (vcl::Window* pParent, SfxBindings* pBindings)
:   IconChoiceDialog( pParent, "HyperlinkDialog", "cui/ui/hyperlinkdialog.ui" ),
    maCtrl          ( SID_HYPERLINK_GETLINK, *pBindings, this ),
    mpBindings      ( pBindings ),
    mbIsHTMLDoc     ( false )
{
    mbGrabFocus = true;
    // insert pages
    OUString aStrTitle;
    SvxIconChoiceCtrlEntry *pEntry;

    aStrTitle = CuiResId( RID_SVXSTR_HYPERDLG_HLINETTP );
    pEntry = AddTabPage ( HyperLinkPageType::Internet, aStrTitle, Image(StockImage::Yes, RID_SVXBMP_HLINETTP), SvxHyperlinkInternetTp::Create );
    pEntry->SetQuickHelpText( CuiResId( RID_SVXSTR_HYPERDLG_HLINETTP_HELP ) );
    aStrTitle = CuiResId( RID_SVXSTR_HYPERDLG_HLMAILTP );
    pEntry = AddTabPage ( HyperLinkPageType::Mail, aStrTitle, Image(StockImage::Yes, RID_SVXBMP_HLMAILTP), SvxHyperlinkMailTp::Create );
    pEntry->SetQuickHelpText( CuiResId( RID_SVXSTR_HYPERDLG_HLMAILTP_HELP ) );
    if (!comphelper::LibreOfficeKit::isActive())
    {
        aStrTitle = CuiResId( RID_SVXSTR_HYPERDLG_HLDOCTP );
        pEntry = AddTabPage ( HyperLinkPageType::Document, aStrTitle, Image(StockImage::Yes, RID_SVXBMP_HLDOCTP), SvxHyperlinkDocTp::Create );
        pEntry->SetQuickHelpText( CuiResId( RID_SVXSTR_HYPERDLG_HLDOCTP_HELP ) );
        aStrTitle = CuiResId( RID_SVXSTR_HYPERDLG_HLDOCNTP );
        pEntry = AddTabPage ( HyperLinkPageType::NewDocument, aStrTitle, Image(StockImage::Yes, RID_SVXBMP_HLDOCNTP), SvxHyperlinkNewDocTp::Create );
        pEntry->SetQuickHelpText( CuiResId( RID_SVXSTR_HYPERDLG_HLDOCNTP_HELP ) );
    }

    // set OK/Cancel - button
    GetCancelButton().SetText ( CuiResId(RID_SVXSTR_HYPDLG_CLOSEBUT) );

    // create itemset for tabpages
    mpItemSet = std::make_unique<SfxItemSet>( SfxGetpApp()->GetPool(), svl::Items<SID_HYPERLINK_GETLINK,
                               SID_HYPERLINK_SETLINK>{} );

    SvxHyperlinkItem aItem(SID_HYPERLINK_GETLINK);
    mpItemSet->Put(aItem);

    SetInputSet (mpItemSet.get());

    //loop through the pages and get their max bounds and lock that down
    ShowPage(HyperLinkPageType::NewDocument);
    VclBox *pBox = get_content_area();
    Size aMaxPrefSize(pBox->get_preferred_size());
    ShowPage(HyperLinkPageType::Document);
    Size aSize(pBox->get_preferred_size());
    aMaxPrefSize.setWidth( std::max(aMaxPrefSize.Width(), aSize.Width()) );
    aMaxPrefSize.setHeight( std::max(aMaxPrefSize.Height(), aSize.Height()) );
    ShowPage(HyperLinkPageType::Mail);
    aSize = pBox->get_preferred_size();
    aMaxPrefSize.setWidth( std::max(aMaxPrefSize.Width(), aSize.Width()) );
    aMaxPrefSize.setHeight( std::max(aMaxPrefSize.Height(), aSize.Height()) );
    ShowPage(HyperLinkPageType::Internet);
    aSize = pBox->get_preferred_size();
    aMaxPrefSize.setWidth( std::max(aMaxPrefSize.Width(), aSize.Width()) );
    aMaxPrefSize.setHeight( std::max(aMaxPrefSize.Height(), aSize.Height()) );
    pBox->set_width_request(aMaxPrefSize.Width());
    pBox->set_height_request(aMaxPrefSize.Height());

    SetCurPageId(HyperLinkPageType::Internet);

    // Init Dialog
    Start();

    pBindings->Update( SID_READONLY_MODE );

    GetOKButton().SetClickHdl    ( LINK ( this, SvxHpLinkDlg, ClickOkHdl_Impl ) );
    GetApplyButton().SetClickHdl ( LINK ( this, SvxHpLinkDlg, ClickApplyHdl_Impl ) );
    GetCancelButton().SetClickHdl( LINK ( this, SvxHpLinkDlg, ClickCloseHdl_Impl ) );
}

SvxHpLinkDlg::~SvxHpLinkDlg ()
{
    disposeOnce();
}

void SvxHpLinkDlg::dispose()
{
    // delete config item, so the base class (IconChoiceDialog) can not load it on the next start
    SvtViewOptions aViewOpt( EViewType::TabDialog, OUString::number(SID_HYPERLINK_DIALOG) );
    aViewOpt.Delete();

    mpItemSet.reset();

    maCtrl.dispose();

    IconChoiceDialog::dispose();
}

/*************************************************************************
|*
|* Close Dialog-Window
|*
|************************************************************************/

bool SvxHpLinkDlg::Close()
{
    GetDispatcher()->Execute( SID_HYPERLINK_DIALOG,
                              SfxCallMode::ASYNCHRON |
                              SfxCallMode::RECORD);
    return true;
}

void SvxHpLinkDlg::Apply()
{
    SfxItemSet aItemSet( SfxGetpApp()->GetPool(), svl::Items<SID_HYPERLINK_GETLINK,
                         SID_HYPERLINK_SETLINK>{} );

    SvxHyperlinkTabPageBase* pCurrentPage = static_cast<SvxHyperlinkTabPageBase*>(
                                                GetTabPage( GetCurPageId() ) );

    if ( pCurrentPage->AskApply() )
    {
        pCurrentPage->FillItemSet( &aItemSet );

        const SvxHyperlinkItem *aItem = aItemSet.GetItem(SID_HYPERLINK_SETLINK);
        if ( !aItem->GetURL().isEmpty() )
            GetDispatcher()->ExecuteList(SID_HYPERLINK_SETLINK,
                    SfxCallMode::ASYNCHRON | SfxCallMode::RECORD, { aItem });

        static_cast<SvxHyperlinkTabPageBase*>( GetTabPage( GetCurPageId() ) )->DoApply();
    }
}

/*************************************************************************
|*
|* When extra window is visible and its never moved by user, then move that
|* window, too.
|*
|************************************************************************/

void SvxHpLinkDlg::Move()
{
    SvxHyperlinkTabPageBase* pCurrentPage = static_cast<SvxHyperlinkTabPageBase*>(
                                              GetTabPage ( GetCurPageId() ) );

    if( pCurrentPage->IsMarkWndVisible () )
    {
        // Pos&Size of this dialog-window
        Point aDlgPos ( GetPosPixel () );
        Size aDlgSize ( GetSizePixel () );

        // Size of Office-Main-Window
        Size aWindowSize( SfxGetpApp()->GetTopWindow()->GetSizePixel() );

        // Size of Extrawindow
        Size aExtraWndSize( pCurrentPage->GetSizeExtraWnd() );

        if( aDlgPos.X()+(1.02*aDlgSize.Width())+aExtraWndSize.Width() > aWindowSize.Width() )
        {
            if( aDlgPos.X() - ( 0.02*aDlgSize.Width() ) - aExtraWndSize.Width() < 0 )
            {
                // Pos Extrawindow anywhere
                pCurrentPage->MoveToExtraWnd( Point( 1, long(1.1*aDlgPos.Y()) ) );
            }
            else
            {
                // Pos Extrawindow on the left side of Dialog
                pCurrentPage->MoveToExtraWnd( aDlgPos -
                                              Point( long(0.02*aDlgSize.Width()), 0 ) -
                                              Point( aExtraWndSize.Width(), 0 ) );
            }
        }
        else
        {
            // Pos Extrawindow on the right side of Dialog
            pCurrentPage->MoveToExtraWnd ( aDlgPos + Point( long(1.02*aDlgSize.Width()), 0 ) );
        }
    }

    Window::Move();
}

/// Click on OK button
IMPL_LINK_NOARG(SvxHpLinkDlg, ClickOkHdl_Impl, Button*, void)
{
    Apply();
    Close();
}

/*************************************************************************
|*
|* Click on Apply-button
|*
|************************************************************************/

IMPL_LINK_NOARG(SvxHpLinkDlg, ClickApplyHdl_Impl, Button*, void)
{
    Apply();
}

/*************************************************************************
|*
|* Click on Close-button
|*
|************************************************************************/

IMPL_LINK_NOARG(SvxHpLinkDlg, ClickCloseHdl_Impl, Button*, void)
{
    Close();
}

/*************************************************************************
|*
|* Set Page
|*
|************************************************************************/

void SvxHpLinkDlg::SetPage ( SvxHyperlinkItem const * pItem )
{
    HyperLinkPageType nPageId = HyperLinkPageType::Internet;

    OUString aStrURL(pItem->GetURL());
    INetURLObject aURL(aStrURL);
    INetProtocol eProtocolTyp = aURL.GetProtocol();

    switch ( eProtocolTyp )
    {
        case INetProtocol::Http :
        case INetProtocol::Ftp :
            nPageId = HyperLinkPageType::Internet;
            break;
        case INetProtocol::File :
            nPageId = HyperLinkPageType::Document;
            break;
        case INetProtocol::Mailto :
            nPageId = HyperLinkPageType::Mail;
            break;
        default :
            if (aStrURL.startsWith("#"))
                nPageId = HyperLinkPageType::Document;
            else
            {
                // not valid
                nPageId = GetCurPageId();
            }
            break;
    }

    ShowPage (nPageId);

    SvxHyperlinkTabPageBase* pCurrentPage = static_cast<SvxHyperlinkTabPageBase*>(GetTabPage( nPageId ));

    mbIsHTMLDoc = (pItem->GetInsertMode() & HLINK_HTMLMODE) != 0;

    IconChoicePage* pPage = GetTabPage (nPageId);
    if(pPage)
    {
        SfxItemSet& aPageSet = const_cast<SfxItemSet&>(pPage->GetItemSet ());
        aPageSet.Put ( *pItem );

        pCurrentPage->Reset( aPageSet );
        if ( mbGrabFocus )
        {
            pCurrentPage->SetInitFocus();   // #92535# grab the focus only once at initialization
            mbGrabFocus = false;
        }
    }
}

/*************************************************************************
|*
|* Enable/Disable ReadOnly mode
|*
|************************************************************************/

void SvxHpLinkDlg::SetReadOnlyMode( bool bRdOnly )
{
    if ( bRdOnly )
        GetOKButton().Disable();
    else
        GetOKButton().Enable();
}

/*************************************************************************
|*
|* late-initialization of newly created pages
|*
|************************************************************************/

void SvxHpLinkDlg::PageCreated( HyperLinkPageType /*nId*/, IconChoicePage& rPage )
{
    SvxHyperlinkTabPageBase& rHyperlinkPage = dynamic_cast< SvxHyperlinkTabPageBase& >( rPage );
    Reference< XFrame > xDocumentFrame;
    if ( mpBindings )
        xDocumentFrame = mpBindings->GetActiveFrame();
    OSL_ENSURE( xDocumentFrame.is(), "SvxHpLinkDlg::PageCreated: macro assignment functionality won't work with a proper frame!" );
    rHyperlinkPage.SetDocumentFrame( xDocumentFrame );
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
