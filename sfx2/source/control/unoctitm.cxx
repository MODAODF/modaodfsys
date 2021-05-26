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

#include <config_java.h>

#include <rtl/strbuf.hxx>
#include <tools/debug.hxx>
#include <svl/eitem.hxx>
#include <svl/intitem.hxx>
#include <svl/itemset.hxx>
#include <svl/visitem.hxx>
#include <svtools/javacontext.hxx>
#include <svtools/javainteractionhandler.hxx>
#include <svl/itempool.hxx>
#include <tools/urlobj.hxx>
#include <com/sun/star/awt/FontDescriptor.hpp>
#include <com/sun/star/awt/Point.hpp>
#include <com/sun/star/awt/Size.hpp>
#include <com/sun/star/awt/Rectangle.hpp>
#include <com/sun/star/util/URLTransformer.hpp>
#include <com/sun/star/util/XURLTransformer.hpp>
#include <com/sun/star/frame/Desktop.hpp>
#include <com/sun/star/frame/XFrame.hpp>
#include <com/sun/star/frame/status/FontHeight.hpp>
#include <com/sun/star/frame/status/ItemStatus.hpp>
#include <com/sun/star/frame/status/ItemState.hpp>
#include <com/sun/star/frame/status/Template.hpp>
#include <com/sun/star/frame/DispatchResultState.hpp>
#include <com/sun/star/frame/ModuleManager.hpp>
#include <com/sun/star/frame/status/Visibility.hpp>
#include <com/sun/star/drawing/LineCap.hpp>
#include <com/sun/star/drawing/LineJoint.hpp>
#include <com/sun/star/drawing/LineStyle.hpp>
#include <com/sun/star/style/LineSpacing.hpp>
#include <com/sun/star/style/LineSpacingMode.hpp>
#include <com/sun/star/table/BorderLine2.hpp>
#include <com/sun/star/table/BorderLineStyle.hpp>
#include <com/sun/star/table/CellHoriJustify.hpp>
#include <comphelper/processfactory.hxx>
#include <officecfg/Office/Common.hxx>
#include <uno/current_context.hxx>
#include <vcl/svapp.hxx>
#include <vcl/uitest/logger.hxx>
#include <boost/property_tree/json_parser.hpp>

#include <sfx2/app.hxx>
#include <unoctitm.hxx>
#include <sfx2/viewfrm.hxx>
#include <sfx2/frame.hxx>
#include <sfx2/ctrlitem.hxx>
#include <sfx2/sfxuno.hxx>
#include <sfx2/bindings.hxx>
#include <sfx2/dispatch.hxx>
#include <sfx2/sfxsids.hrc>
#include <sfx2/request.hxx>
#include <sfx2/msg.hxx>
#include <sfx2/viewsh.hxx>
#include <slotserv.hxx>
#include <osl/file.hxx>
#include <rtl/ustring.hxx>
#include <unotools/pathoptions.hxx>
#include <osl/time.h>
#include <sfx2/lokhelper.hxx>

#include <map>
#include <memory>
#include <string_view>

#include <sal/log.hxx>
#include <LibreOfficeKit/LibreOfficeKitEnums.h>
#include <comphelper/lok.hxx>

using namespace ::com::sun::star;
using namespace ::com::sun::star::uno;
using namespace ::com::sun::star::util;

namespace {

enum URLTypeId
{
    URLType_BOOL,
    URLType_BYTE,
    URLType_SHORT,
    URLType_LONG,
    URLType_HYPER,
    URLType_STRING,
    URLType_FLOAT,
    URLType_DOUBLE,
    URLType_COUNT
};

}

const char* const URLTypeNames[URLType_COUNT] =
{
    "bool",
    "byte",
    "short",
    "long",
    "hyper",
    "string",
    "float",
    "double"
};

static void InterceptLOKStateChangeEvent( sal_uInt16 nSID, SfxViewFrame* pViewFrame, const css::frame::FeatureStateEvent& aEvent, const SfxPoolItem* pState );

void SfxStatusDispatcher::ReleaseAll()
{
    css::lang::EventObject aObject;
    aObject.Source = static_cast<cppu::OWeakObject*>(this);
    aListeners.disposeAndClear( aObject );
}

void SAL_CALL SfxStatusDispatcher::dispatch( const css::util::URL&, const css::uno::Sequence< css::beans::PropertyValue >& )
{
}

void SAL_CALL SfxStatusDispatcher::dispatchWithNotification(
    const css::util::URL&,
    const css::uno::Sequence< css::beans::PropertyValue >&,
    const css::uno::Reference< css::frame::XDispatchResultListener >& )
{
}

SfxStatusDispatcher::SfxStatusDispatcher()
    : aListeners( aMutex )
{
}

void SAL_CALL SfxStatusDispatcher::addStatusListener(const css::uno::Reference< css::frame::XStatusListener > & aListener, const css::util::URL& aURL)
{
    aListeners.addInterface( aURL.Complete, aListener );
    if ( aURL.Complete == ".uno:LifeTime" )
    {
        css::frame::FeatureStateEvent aEvent;
        aEvent.FeatureURL = aURL;
        aEvent.Source = static_cast<css::frame::XDispatch*>(this);
        aEvent.IsEnabled = true;
        aEvent.Requery = false;
        aListener->statusChanged( aEvent );
    }
}

void SAL_CALL SfxStatusDispatcher::removeStatusListener( const css::uno::Reference< css::frame::XStatusListener > & aListener, const css::util::URL& aURL )
{
    aListeners.removeInterface( aURL.Complete, aListener );
}


// XUnoTunnel
sal_Int64 SAL_CALL SfxOfficeDispatch::getSomething( const css::uno::Sequence< sal_Int8 >& aIdentifier )
{
    if ( aIdentifier == impl_getStaticIdentifier() )
        return sal::static_int_cast< sal_Int64 >( reinterpret_cast< sal_IntPtr >( this ));
    else
        return 0;
}

SfxOfficeDispatch::SfxOfficeDispatch( SfxBindings& rBindings, SfxDispatcher* pDispat, const SfxSlot* pSlot, const css::util::URL& rURL )
    : pImpl( new SfxDispatchController_Impl( this, &rBindings, pDispat, pSlot, rURL ))
{
    // pImpl is an adapter that shows a css::frame::XDispatch-Interface to the outside and uses a SfxControllerItem to monitor a state

}

SfxOfficeDispatch::SfxOfficeDispatch( SfxDispatcher* pDispat, const SfxSlot* pSlot, const css::util::URL& rURL )
    : pImpl( new SfxDispatchController_Impl( this, nullptr, pDispat, pSlot, rURL ))
{
    // pImpl is an adapter that shows a css::frame::XDispatch-Interface to the outside and uses a SfxControllerItem to monitor a state
}

SfxOfficeDispatch::~SfxOfficeDispatch()
{
    if ( pImpl )
    {
        // when dispatch object is released, destroy its connection to this object and destroy it
        pImpl->UnBindController();
    }
}

const css::uno::Sequence< sal_Int8 >& SfxOfficeDispatch::impl_getStaticIdentifier()
{
    // {38 57 CA 80 09 36 11 d4 83 FE 00 50 04 52 6B 21}
    static const sal_uInt8 pGUID[16] = { 0x38, 0x57, 0xCA, 0x80, 0x09, 0x36, 0x11, 0xd4, 0x83, 0xFE, 0x00, 0x50, 0x04, 0x52, 0x6B, 0x21 };
    static css::uno::Sequence< sal_Int8 > seqID(reinterpret_cast<const sal_Int8*>(pGUID), 16) ;
    return seqID ;
}

#if HAVE_FEATURE_JAVA
// The JavaContext contains an interaction handler which is used when
// the creation of a Java Virtual Machine fails. There shall only be one
// user notification (message box) even if the same error (interaction)
// reoccurs. The effect is, that if a user selects a menu entry than they
// may get only one notification that a JRE is not selected.
// This function checks if a JavaContext is already available (typically
// created by Desktop::Main() in app.cxx), and creates new one if not.
namespace {
std::unique_ptr< css::uno::ContextLayer > EnsureJavaContext()
{
    css::uno::Reference< css::uno::XCurrentContext > xContext(css::uno::getCurrentContext());
    if (xContext.is())
    {
        css::uno::Reference< css::task::XInteractionHandler > xHandler;
        xContext->getValueByName(JAVA_INTERACTION_HANDLER_NAME) >>= xHandler;
        if (xHandler.is())
            return nullptr; // No need to add new layer: JavaContext already present
    }
    return std::make_unique< css::uno::ContextLayer >(new svt::JavaContext(xContext));
}
}
#endif

void SAL_CALL SfxOfficeDispatch::dispatch( const css::util::URL& aURL, const css::uno::Sequence< css::beans::PropertyValue >& aArgs )
{
    // ControllerItem is the Impl class
    if ( pImpl )
    {
#if HAVE_FEATURE_JAVA
        std::unique_ptr< css::uno::ContextLayer > layer(EnsureJavaContext());
#endif
        pImpl->dispatch( aURL, aArgs, css::uno::Reference < css::frame::XDispatchResultListener >() );
    }
}

void SAL_CALL SfxOfficeDispatch::dispatchWithNotification( const css::util::URL& aURL,
        const css::uno::Sequence< css::beans::PropertyValue >& aArgs,
        const css::uno::Reference< css::frame::XDispatchResultListener >& rListener )
{
    // ControllerItem is the Impl class
    if ( pImpl )
    {
#if HAVE_FEATURE_JAVA
        std::unique_ptr< css::uno::ContextLayer > layer(EnsureJavaContext());
#endif
        pImpl->dispatch( aURL, aArgs, rListener );
    }
}

void SAL_CALL SfxOfficeDispatch::addStatusListener(const css::uno::Reference< css::frame::XStatusListener > & aListener, const css::util::URL& aURL)
{
    GetListeners().addInterface( aURL.Complete, aListener );
    if ( pImpl )
    {
        // ControllerItem is the Impl class
        pImpl->addStatusListener( aListener, aURL );
    }
}

SfxDispatcher* SfxOfficeDispatch::GetDispatcher_Impl()
{
    return pImpl->GetDispatcher();
}

void SfxOfficeDispatch::SetFrame(const css::uno::Reference< css::frame::XFrame >& xFrame)
{
    if ( pImpl )
        pImpl->SetFrame( xFrame );
}

void SfxOfficeDispatch::SetMasterUnoCommand( bool bSet )
{
    if ( pImpl )
        pImpl->setMasterSlaveCommand( bSet );
}

// Determine if URL contains a master/slave command which must be handled a little bit different
bool SfxOfficeDispatch::IsMasterUnoCommand( const css::util::URL& aURL )
{
    return aURL.Protocol == ".uno:" && ( aURL.Path.indexOf( '.' ) > 0 );
}

OUString SfxOfficeDispatch::GetMasterUnoCommand( const css::util::URL& aURL )
{
    OUString aMasterCommand;
    if ( IsMasterUnoCommand( aURL ))
    {
        sal_Int32 nIndex = aURL.Path.indexOf( '.' );
        if ( nIndex > 0 )
            aMasterCommand = aURL.Path.copy( 0, nIndex );
    }

    return aMasterCommand;
}

SfxDispatchController_Impl::SfxDispatchController_Impl(
    SfxOfficeDispatch*                 pDisp,
    SfxBindings*                       pBind,
    SfxDispatcher*                     pDispat,
    const SfxSlot*                     pSlot,
    const css::util::URL&              rURL )
    : aDispatchURL( rURL )
    , pDispatcher( pDispat )
    , pBindings( pBind )
    , pLastState( nullptr )
    , pDispatch( pDisp )
    , bMasterSlave( false )
    , bVisible( true )
{
    if ( aDispatchURL.Protocol == "slot:" && pSlot->pUnoName )
    {
        aDispatchURL.Complete = ".uno:" + OUString::createFromAscii(pSlot->pUnoName);
        Reference< XURLTransformer > xTrans( URLTransformer::create( ::comphelper::getProcessComponentContext() ) );
        xTrans->parseStrict( aDispatchURL );
    }

    sal_uInt16 nSlot = pSlot->GetSlotId();
    SetId( nSlot );
    if ( pBindings )
    {
        // Bind immediately to enable the cache to recycle dispatches when asked for the same command
        // a command in "slot" or in ".uno" notation must be treated as identical commands!
        pBindings->ENTERREGISTRATIONS();
        BindInternal_Impl( nSlot, pBindings );
        pBindings->LEAVEREGISTRATIONS();
    }
    assert(pDispatcher);
    assert(SfxApplication::Get()->GetAppDispatcher_Impl() == pDispatcher
        || pDispatcher->GetFrame() != nullptr);
    if (pDispatcher->GetFrame())
    {
        StartListening(*pDispatcher->GetFrame());
    }
    else
    {
        StartListening(*SfxApplication::Get());
    }
}

void SfxDispatchController_Impl::Notify(SfxBroadcaster& rBC, SfxHint const& rHint)
{
    if (rHint.GetId() == SfxHintId::Dying)
    {   // both pBindings and pDispatcher are dead if SfxViewFrame is dead
        pBindings = nullptr;
        pDispatcher = nullptr;
        EndListening(rBC);
    }
}

SfxDispatchController_Impl::~SfxDispatchController_Impl()
{
    if ( pLastState && !IsInvalidItem( pLastState ) )
        delete pLastState;

    if ( pDispatch )
    {
        // disconnect
        pDispatch->pImpl = nullptr;

        // force all listeners to release the dispatch object
        css::lang::EventObject aObject;
        aObject.Source = static_cast<cppu::OWeakObject*>(pDispatch);
        pDispatch->GetListeners().disposeAndClear( aObject );
    }
}

void SfxDispatchController_Impl::SetFrame(const css::uno::Reference< css::frame::XFrame >& _xFrame)
{
    xFrame = _xFrame;
}

void SfxDispatchController_Impl::setMasterSlaveCommand( bool bSet )
{
    bMasterSlave = bSet;
}

void SfxDispatchController_Impl::UnBindController()
{
    pDispatch = nullptr;
    if ( IsBound() )
    {
        GetBindings().ENTERREGISTRATIONS();
        SfxControllerItem::UnBind();
        GetBindings().LEAVEREGISTRATIONS();
    }
}

void SfxDispatchController_Impl::addParametersToArgs( const css::util::URL& aURL, css::uno::Sequence< css::beans::PropertyValue >& rArgs )
{
    // Extract the parameter from the URL and put them into the property value sequence
    sal_Int32 nQueryIndex = aURL.Complete.indexOf( '?' );
    if ( nQueryIndex <= 0 )
        return;

    OUString aParamString( aURL.Complete.copy( nQueryIndex+1 ));
    sal_Int32 nIndex = 0;
    do
    {
        OUString aToken = aParamString.getToken( 0, '&', nIndex );

        sal_Int32 nParmIndex = 0;
        OUString aParamType;
        OUString aParamName = aToken.getToken( 0, '=', nParmIndex );
        OUString aValue     = aToken.getToken( 0, '=', nParmIndex );

        if ( !aParamName.isEmpty() )
        {
            nParmIndex = 0;
            aToken = aParamName;
            aParamName = aToken.getToken( 0, ':', nParmIndex );
            aParamType = aToken.getToken( 0, ':', nParmIndex );
        }

        sal_Int32 nLen = rArgs.getLength();
        rArgs.realloc( nLen+1 );
        rArgs[nLen].Name = aParamName;

        if ( aParamType.isEmpty() )
        {
            // Default: LONG
            rArgs[nLen].Value <<= aValue.toInt32();
        }
        else if ( aParamType.equalsAsciiL( URLTypeNames[URLType_BOOL], 4 ))
        {
            // sal_Bool support
            rArgs[nLen].Value <<= aValue.toBoolean();
        }
        else if ( aParamType.equalsAsciiL( URLTypeNames[URLType_BYTE], 4 ))
        {
            // sal_uInt8 support
            rArgs[nLen].Value <<= sal_Int8( aValue.toInt32() );
        }
        else if ( aParamType.equalsAsciiL( URLTypeNames[URLType_LONG], 4 ))
        {
            // LONG support
            rArgs[nLen].Value <<= aValue.toInt32();
        }
        else if ( aParamType.equalsAsciiL( URLTypeNames[URLType_SHORT], 5 ))
        {
            // SHORT support
            rArgs[nLen].Value <<= sal_Int16( aValue.toInt32() );
        }
        else if ( aParamType.equalsAsciiL( URLTypeNames[URLType_HYPER], 5 ))
        {
            // HYPER support
            rArgs[nLen].Value <<= aValue.toInt64();
        }
        else if ( aParamType.equalsAsciiL( URLTypeNames[URLType_FLOAT], 5 ))
        {
            // FLOAT support
            rArgs[nLen].Value <<= aValue.toFloat();
        }
        else if ( aParamType.equalsAsciiL( URLTypeNames[URLType_STRING], 6 ))
        {
            // STRING support
            rArgs[nLen].Value <<= INetURLObject::decode( aValue, INetURLObject::DecodeMechanism::WithCharset );
        }
        else if ( aParamType.equalsAsciiL( URLTypeNames[URLType_DOUBLE], 6))
        {
            // DOUBLE support
            rArgs[nLen].Value <<= aValue.toDouble();
        }
    }
    while ( nIndex >= 0 );
}

MapUnit SfxDispatchController_Impl::GetCoreMetric( SfxItemPool const & rPool, sal_uInt16 nSlotId )
{
    sal_uInt16 nWhich = rPool.GetWhich( nSlotId );
    return rPool.GetMetric( nWhich );
}

OUString SfxDispatchController_Impl::getSlaveCommand( const css::util::URL& rURL )
{
    OUString   aSlaveCommand;
    sal_Int32       nIndex = rURL.Path.indexOf( '.' );
    if (( nIndex > 0 ) && ( nIndex < rURL.Path.getLength() ))
        aSlaveCommand = rURL.Path.copy( nIndex+1 );
    return aSlaveCommand;
}

namespace {

/// Class that collects the usage information - how many times what .uno: command was used.
class UsageInfo {

    typedef std::map<OUString, int> UsageMap;

    /// Are we collecting the info?  We cache the value because the call to save can happen very late.
    bool mbIsCollecting;

    /// Command vs. how many times it was used
    UsageMap maUsage;

    /// config path, get it long before atexit time
    OUString msConfigPath;

public:
    UsageInfo() : mbIsCollecting(false)
    {
    }

    ~UsageInfo()
    {
        save();
    }

    /// Increment command's use.
    void increment(const OUString &rCommand);

    /// Save the usage data for the next session.
    void save();

    /// Modify the flag whether we are collecting.
    void setCollecting(bool bIsCollecting)
    {
        mbIsCollecting = bIsCollecting;
        if (mbIsCollecting)
        {
            msConfigPath = SvtPathOptions().GetConfigPath();
            msConfigPath += "usage/";
        }
    }
};

void UsageInfo::increment(const OUString &rCommand)
{
    UsageMap::iterator it = maUsage.find(rCommand);

    if (it != maUsage.end())
        ++(it->second);
    else
        maUsage[rCommand] = 1;
}

void UsageInfo::save()
{
    if (!mbIsCollecting)
        return;

    osl::Directory::createPath(msConfigPath);

    //get system time information.
    TimeValue systemTime;
    TimeValue localTime;
    oslDateTime localDateTime;
    osl_getSystemTime( &systemTime );
    osl_getLocalTimeFromSystemTime( &systemTime, &localTime );
    osl_getDateTimeFromTimeValue( &localTime, &localDateTime );

    char time[1024];
    sprintf(time,"%4i-%02i-%02iT%02i_%02i_%02i", localDateTime.Year, localDateTime.Month, localDateTime.Day, localDateTime.Hours, localDateTime.Minutes, localDateTime.Seconds);

    //filename type: usage-YYYY-MM-DDTHH_MM_SS.csv
    OUString filename = "usage-" + OUString::createFromAscii(time) + ".csv";
    OUString path = msConfigPath + filename;

    osl::File file(path);

    if( file.open(osl_File_OpenFlag_Read | osl_File_OpenFlag_Write | osl_File_OpenFlag_Create) == osl::File::E_None )
    {
        OStringBuffer aUsageInfoMsg("Document Type;Command;Count");

        for (auto const& elem : maUsage)
            aUsageInfoMsg.append("\n").append(elem.first.toUtf8()).append(";").append(OString::number(elem.second));

        sal_uInt64 written = 0;
        auto s = aUsageInfoMsg.makeStringAndClear();
        file.write(s.getStr(), s.getLength(), written);
        file.close();
    }
}

class theUsageInfo : public rtl::Static<UsageInfo, theUsageInfo> {};

/// Extracts information about the command + args, and stores that.
void collectUsageInformation(const util::URL& rURL, const uno::Sequence<beans::PropertyValue>& rArgs)
{
    bool bCollecting = getenv("LO_COLLECT_USAGE") || officecfg::Office::Common::Misc::CollectUsageInformation::get();
    theUsageInfo::get().setCollecting(bCollecting);
    if (!bCollecting)
        return;

    OUStringBuffer aBuffer;

    // app identification [uh, several UNO calls :-(]
    uno::Reference<uno::XComponentContext> xContext = ::comphelper::getProcessComponentContext();
    uno::Reference<frame::XModuleManager2> xModuleManager(frame::ModuleManager::create(xContext));
    uno::Reference<frame::XDesktop2> xDesktop = frame::Desktop::create(xContext);
    uno::Reference<frame::XFrame> xFrame = xDesktop->getCurrentFrame();

    OUString aModule(xModuleManager->identify(xFrame));
    sal_Int32 nLastDot = aModule.lastIndexOf('.');
    if (nLastDot >= 0)
        aModule = aModule.copy(nLastDot + 1);

    aBuffer.append(aModule);
    aBuffer.append(';');

    // command
    aBuffer.append(rURL.Protocol);
    aBuffer.append(rURL.Path);
    sal_Int32 nCount = rArgs.getLength();

    // parameters - only their names, not the values (could be sensitive!)
    if (nCount > 0)
    {
        aBuffer.append('(');
        for (sal_Int32 n = 0; n < nCount; n++)
        {
            const css::beans::PropertyValue& rProp = rArgs[n];
            if (n > 0)
                aBuffer.append(',');
            aBuffer.append(rProp.Name);
        }
        aBuffer.append(')');
    }

    OUString aCommand(aBuffer.makeStringAndClear());

    // store
    theUsageInfo::get().increment(aCommand);
}

void collectUIInformation(const util::URL& rURL, const css::uno::Sequence< css::beans::PropertyValue >& rArgs)
{
    static const char* pFile = std::getenv("LO_COLLECT_UIINFO");
    if (!pFile)
        return;

    UITestLogger::getInstance().logCommand("Send UNO Command (\"" + rURL.Complete + "\") ", rArgs);
}

}

void SfxDispatchController_Impl::dispatch( const css::util::URL& aURL,
        const css::uno::Sequence< css::beans::PropertyValue >& aArgs,
        const css::uno::Reference< css::frame::XDispatchResultListener >& rListener )
{
    collectUsageInformation(aURL, aArgs);
    collectUIInformation(aURL, aArgs);

    SolarMutexGuard aGuard;
    if (
        !(pDispatch &&
        (
         (aURL.Protocol == ".uno:" && aURL.Path == aDispatchURL.Path) ||
         (aURL.Protocol == "slot:" && aURL.Path.toInt32() == GetId())
        ))
       )
        return;

    if ( !pDispatcher && pBindings )
        pDispatcher = GetBindings().GetDispatcher_Impl();

    css::uno::Sequence< css::beans::PropertyValue > lNewArgs;
    sal_Int32 nCount = aArgs.getLength();

    // Support for URL based arguments
    INetURLObject aURLObj( aURL.Complete );
    if ( aURLObj.HasParam() )
        addParametersToArgs( aURL, lNewArgs );

    // Try to find call mode and frame name inside given arguments...
    SfxCallMode nCall = SfxCallMode::RECORD;
    sal_Int32   nMarkArg = -1;

    // Filter arguments which shouldn't be part of the sequence property value
    sal_uInt16  nModifier(0);
    std::vector< css::beans::PropertyValue > aAddArgs;
    for( sal_Int32 n=0; n<nCount; n++ )
    {
        const css::beans::PropertyValue& rProp = aArgs[n];
        if( rProp.Name == "SynchronMode" )
        {
            bool    bTemp;
            if( rProp.Value >>= bTemp )
                nCall = bTemp ? SfxCallMode::SYNCHRON : SfxCallMode::ASYNCHRON;
        }
        else if( rProp.Name == "Bookmark" )
        {
            nMarkArg = n;
            aAddArgs.push_back( aArgs[n] );
        }
        else if( rProp.Name == "KeyModifier" )
            rProp.Value >>= nModifier;
        else
            aAddArgs.push_back( aArgs[n] );
    }

    // Add needed arguments to sequence property value
    sal_uInt32 nAddArgs = aAddArgs.size();
    if ( nAddArgs > 0 )
    {
        sal_uInt32 nIndex( lNewArgs.getLength() );

        lNewArgs.realloc( nIndex + nAddArgs );
        std::copy(aAddArgs.begin(), aAddArgs.end(), std::next(lNewArgs.begin(), nIndex));
    }

    // Overwrite possible detected synchron argument, if real listener exists (currently no other way)
    if ( rListener.is() )
        nCall = SfxCallMode::SYNCHRON;

    if( GetId() == SID_JUMPTOMARK && nMarkArg == - 1 )
    {
        // we offer dispatches for SID_JUMPTOMARK if the URL points to a bookmark inside the document
        // so we must retrieve this as an argument from the parsed URL
        lNewArgs.realloc( lNewArgs.getLength()+1 );
        nMarkArg = lNewArgs.getLength()-1;
        lNewArgs[nMarkArg].Name = "Bookmark";
        lNewArgs[nMarkArg].Value <<= aURL.Mark;
    }

    css::uno::Reference< css::frame::XFrame > xFrameRef(xFrame.get(), css::uno::UNO_QUERY);
    if (! xFrameRef.is() && pDispatcher)
    {
        SfxViewFrame* pViewFrame = pDispatcher->GetFrame();
        if (pViewFrame)
            xFrameRef = pViewFrame->GetFrame().GetFrameInterface();
    }

    bool bSuccess = false;
    const SfxPoolItem* pItem = nullptr;
    MapUnit eMapUnit( MapUnit::Map100thMM );

    // Extra scope so that aInternalSet is destroyed before
    // rListener->dispatchFinished potentially calls
    // framework::Desktop::terminate -> SfxApplication::Deinitialize ->
    // ~CntItemPool:
    if (pDispatcher)
    {
        SfxAllItemSet aInternalSet( SfxGetpApp()->GetPool() );
        if (xFrameRef.is()) // an empty set is no problem ... but an empty frame reference can be a problem !
            aInternalSet.Put( SfxUnoFrameItem( SID_FILLFRAME, xFrameRef ) );

        SfxShell* pShell( nullptr );
        // #i102619# Retrieve metric from shell before execution - the shell could be destroyed after execution
        if ( pDispatcher->GetBindings() )
        {
            if ( !pDispatcher->IsLocked() )
            {
                const SfxSlot *pSlot = nullptr;
                if ( pDispatcher->GetShellAndSlot_Impl( GetId(), &pShell, &pSlot, false, false ) )
                {
                    if ( bMasterSlave )
                    {
                        // Extract slave command and add argument to the args list. Master slot MUST
                        // have an argument that has the same name as the master slot and type is SfxStringItem.
                        sal_Int32 nIndex = lNewArgs.getLength();
                        lNewArgs.realloc( nIndex+1 );
                        lNewArgs[nIndex].Name   = OUString::createFromAscii( pSlot->pUnoName );
                        lNewArgs[nIndex].Value  <<= SfxDispatchController_Impl::getSlaveCommand( aDispatchURL );
                    }

                    eMapUnit = GetCoreMetric( pShell->GetPool(), GetId() );
                    std::unique_ptr<SfxAllItemSet> xSet(new SfxAllItemSet(pShell->GetPool()));
                    TransformParameters(GetId(), lNewArgs, *xSet, pSlot);
                    if (xSet->Count())
                    {
                        // execute with arguments - call directly
                        pItem = pDispatcher->Execute(GetId(), nCall, xSet.get(), &aInternalSet, nModifier);
                        if ( pItem != nullptr )
                        {
                            if (const SfxBoolItem* pBoolItem = dynamic_cast<const SfxBoolItem*>(pItem))
                                bSuccess = pBoolItem->GetValue();
                            else if ( !pItem->IsVoidItem() )
                                bSuccess = true;  // all other types are true
                        }
                        // else bSuccess = false look to line 664 it is false
                    }
                    else
                    {
                        // Be sure to delete this before we send a dispatch
                        // request, which will destroy the current shell.
                        xSet.reset();

                        // execute using bindings, enables support for toggle/enum etc.
                        SfxRequest aReq( GetId(), nCall, pShell->GetPool() );
                        aReq.SetModifier( nModifier );
                        aReq.SetInternalArgs_Impl(aInternalSet);
                        pDispatcher->GetBindings()->Execute_Impl( aReq, pSlot, pShell );
                        pItem = aReq.GetReturnValue();
                        bSuccess = aReq.IsDone() || pItem != nullptr;
                    }
                }
                else
                    SAL_INFO("sfx.control", "MacroPlayer: Unknown slot dispatched!");
            }
        }
        else
        {
            eMapUnit = GetCoreMetric( SfxGetpApp()->GetPool(), GetId() );
            // AppDispatcher
            SfxAllItemSet aSet( SfxGetpApp()->GetPool() );
            TransformParameters( GetId(), lNewArgs, aSet );

            if ( aSet.Count() )
                pItem = pDispatcher->Execute(GetId(), nCall, &aSet, &aInternalSet, nModifier);
            else
                // SfxRequests take empty sets as argument sets, GetArgs() returning non-zero!
                pItem = pDispatcher->Execute(GetId(), nCall, nullptr, &aInternalSet, nModifier);

            // no bindings, no invalidate ( usually done in SfxDispatcher::Call_Impl()! )
            if (SfxApplication* pApp = SfxApplication::Get())
            {
                SfxDispatcher* pAppDispat = pApp->GetAppDispatcher_Impl();
                if ( pAppDispat )
                {
                    const SfxPoolItem* pState=nullptr;
                    SfxItemState eState = pDispatcher->QueryState( GetId(), pState );
                    StateChanged( GetId(), eState, pState );
                }
            }

            bSuccess = (pItem != nullptr);
        }
    }

    if ( !rListener.is() )
        return;

    css::frame::DispatchResultEvent aEvent;
    if ( bSuccess )
        aEvent.State = css::frame::DispatchResultState::SUCCESS;
    else
        aEvent.State = css::frame::DispatchResultState::FAILURE;

    aEvent.Source = static_cast<css::frame::XDispatch*>(pDispatch);
    if ( bSuccess && pItem && !pItem->IsVoidItem() )
    {
        sal_uInt16 nSubId( 0 );
        if ( eMapUnit == MapUnit::MapTwip )
            nSubId |= CONVERT_TWIPS;
        pItem->QueryValue( aEvent.Result, static_cast<sal_uInt8>(nSubId) );
    }

    rListener->dispatchFinished( aEvent );
}

SfxDispatcher* SfxDispatchController_Impl::GetDispatcher()
{
    if ( !pDispatcher && pBindings )
        pDispatcher = GetBindings().GetDispatcher_Impl();
    return pDispatcher;
}

void SfxDispatchController_Impl::addStatusListener(const css::uno::Reference< css::frame::XStatusListener > & aListener, const css::util::URL& aURL)
{
    SolarMutexGuard aGuard;
    if ( !pDispatch )
        return;

    // Use alternative QueryState call to have a valid UNO representation of the state.
    css::uno::Any aState;
    if ( !pDispatcher && pBindings )
        pDispatcher = GetBindings().GetDispatcher_Impl();
    SfxItemState eState = pDispatcher ? pDispatcher->QueryState( GetId(), aState ) : SfxItemState::DONTCARE;

    if ( eState == SfxItemState::DONTCARE )
    {
        // Use special uno struct to transport don't care state
        css::frame::status::ItemStatus aItemStatus;
        aItemStatus.State = css::frame::status::ItemState::DONT_CARE;
        aState <<= aItemStatus;
    }

    css::frame::FeatureStateEvent  aEvent;
    aEvent.FeatureURL = aURL;
    aEvent.Source     = static_cast<css::frame::XDispatch*>(pDispatch);
    aEvent.Requery    = false;
    if ( bVisible )
    {
        aEvent.IsEnabled  = eState != SfxItemState::DISABLED;
        aEvent.State      = aState;
    }
    else
    {
        css::frame::status::Visibility aVisibilityStatus;
        aVisibilityStatus.bVisible = false;

        // MBA: we might decide to *not* disable "invisible" slots, but this would be
        // a change that needs to adjust at least the testtool
        aEvent.IsEnabled           = false;
        aEvent.State               <<= aVisibilityStatus;
    }

    aListener->statusChanged( aEvent );
}

void SfxDispatchController_Impl::sendStatusChanged(const OUString& rURL, const css::frame::FeatureStateEvent& rEvent)
{
    ::cppu::OInterfaceContainerHelper* pContnr = pDispatch->GetListeners().getContainer(rURL);
    if (!pContnr)
        return;
    ::cppu::OInterfaceIteratorHelper aIt(*pContnr);
    while (aIt.hasMoreElements())
    {
        try
        {
            static_cast<css::frame::XStatusListener*>(aIt.next())->statusChanged(rEvent);
        }
        catch (const css::uno::RuntimeException&)
        {
            aIt.remove();
        }
    }
}

void SfxDispatchController_Impl::StateChanged( sal_uInt16 nSID, SfxItemState eState, const SfxPoolItem* pState, SfxSlotServer const * pSlotServ )
{
    if ( !pDispatch )
        return;

    // Bindings instance notifies controller about a state change, listeners must be notified also
    // Don't cache visibility state changes as they are volatile. We need our real state to send it
    // to our controllers after visibility is set to true.
    bool bNotify = true;
    if ( pState && !IsInvalidItem( pState ) )
    {
        if ( dynamic_cast< const SfxVisibilityItem *>( pState ) ==  nullptr )
        {
            if (pLastState && !IsInvalidItem(pLastState))
            {
                bNotify = typeid(*pState) != typeid(*pLastState) || *pState != *pLastState;
                delete pLastState;
            }
            pLastState = !IsInvalidItem(pState) ? pState->Clone() : pState;
            bVisible = true;
        }
        else
            bVisible = static_cast<const SfxVisibilityItem *>(pState)->GetValue();
    }
    else
    {
        if ( pLastState && !IsInvalidItem( pLastState ) )
            delete pLastState;
        pLastState = pState;
    }

    if (!bNotify)
        return;

    css::uno::Any aState;
    if ( ( eState >= SfxItemState::DEFAULT ) && pState && !IsInvalidItem( pState ) && !pState->IsVoidItem() )
    {
        // Retrieve metric from pool to have correct sub ID when calling QueryValue
        sal_uInt16     nSubId( 0 );
        MapUnit eMapUnit( MapUnit::Map100thMM );

        // retrieve the core metric
        // it's enough to check the objectshell, the only shell that does not use the pool of the document
        // is SfxViewFrame, but it hasn't any metric parameters
        // TODO/LATER: what about the FormShell? Does it use any metric data?! Perhaps it should use the Pool of the document!
        if ( pSlotServ && pDispatcher )
        {
            SfxShell* pShell = pDispatcher->GetShell( pSlotServ->GetShellLevel() );
            DBG_ASSERT( pShell, "Can't get core metric without shell!" );
            if ( pShell )
                eMapUnit = GetCoreMetric( pShell->GetPool(), nSID );
        }

        if ( eMapUnit == MapUnit::MapTwip )
            nSubId |= CONVERT_TWIPS;

        pState->QueryValue( aState, static_cast<sal_uInt8>(nSubId) );
    }
    else if ( eState == SfxItemState::DONTCARE )
    {
        // Use special uno struct to transport don't care state
        css::frame::status::ItemStatus aItemStatus;
        aItemStatus.State = css::frame::status::ItemState::DONT_CARE;
        aState <<= aItemStatus;
    }

    css::frame::FeatureStateEvent aEvent;
    aEvent.FeatureURL = aDispatchURL;
    aEvent.Source = static_cast<css::frame::XDispatch*>(pDispatch);
    aEvent.IsEnabled = eState != SfxItemState::DISABLED;
    aEvent.Requery = false;
    aEvent.State = aState;

    if (pDispatcher && pDispatcher->GetFrame())
    {
        InterceptLOKStateChangeEvent(nSID, pDispatcher->GetFrame(), aEvent, pState);
    }

    const css::uno::Sequence<OUString> aContainedTypes = pDispatch->GetListeners().getContainedTypes();
    for (const OUString& rName: aContainedTypes)
    {
        if (rName == aDispatchURL.Main || rName == aDispatchURL.Complete)
            sendStatusChanged(rName, aEvent);
    }
}

void SfxDispatchController_Impl::StateChanged( sal_uInt16 nSID, SfxItemState eState, const SfxPoolItem* pState )
{
    StateChanged( nSID, eState, pState, nullptr );
}

static void InterceptLOKStateChangeEvent(sal_uInt16 nSID, SfxViewFrame* pViewFrame, const css::frame::FeatureStateEvent& aEvent, const SfxPoolItem* pState)
{
    if (!comphelper::LibreOfficeKit::isActive())
        return;

    OUStringBuffer aBuffer;
    aBuffer.append(aEvent.FeatureURL.Complete);
    aBuffer.append(u'=');

    // Modified by Firefly <firefly@ossii.com.tw>
    const css::uno::Type aType = aEvent.State.getValueType();
    // aEvent.IsEnabled == false 只能是 disabled
    if (!aEvent.IsEnabled)
    {
        aBuffer.append("disabled");
    }
    // 沒有型態是 void 單純就是 enabled
    else if (aType == cppu::UnoType<void>::get())
    {
        aBuffer.append("enabled");
    }
    // 型態是 true / false
    else if (aType == cppu::UnoType<bool>::get())
    {
        bool bTemp = false;
        aEvent.State >>= bTemp;
        aBuffer.append(bTemp);
    }
    // 型態是 short / long
    else if (aType == cppu::UnoType<sal_Int16>::get() ||
             aType == cppu::UnoType<sal_Int32>::get())
    {
        sal_Int32 aInt32;
        aEvent.State >>= aInt32;

        if (aEvent.FeatureURL.Path == "TransformPosX" ||
            aEvent.FeatureURL.Path == "TransformPosY" ||
            aEvent.FeatureURL.Path == "TransformWidth" ||
            aEvent.FeatureURL.Path == "TransformHeight")
        {
            const SfxViewShell* pViewShell = SfxViewShell::Current();
            if (pViewShell && pViewShell->isLOKMobilePhone())
            {
                boost::property_tree::ptree aTree;
                boost::property_tree::ptree aState;
                OUString aStr(aEvent.FeatureURL.Complete);

                aTree.put("commandName", aStr.toUtf8().getStr());
                pViewFrame->GetBindings().QueryControlState(nSID, aState);
                aTree.add_child("state", aState);

                aBuffer.setLength(0);
                std::stringstream aStream;
                boost::property_tree::write_json(aStream, aTree, false);
                aBuffer.appendAscii(aStream.str().c_str());
            }
            else
            {
                aBuffer.append(aInt32);
            }
        }
        else if (aEvent.FeatureURL.Path == "TableColumWidth" ||
                 aEvent.FeatureURL.Path == "TableRowHeight")
        {
            float nScaleValue = 1000.0;
            aInt32 *= nScaleValue;
            sal_Int32 nConvertedValue = OutputDevice::LogicToLogic(aInt32, MapUnit::MapTwip, MapUnit::MapInch);
            aBuffer.append(OUString::number(nConvertedValue / nScaleValue));
        }
        else
        {
            aBuffer.append(aInt32);
        }
     }
    // 型態是 OUString
    else if (aType == cppu::UnoType<OUString>::get())
    {
        OUString aString;
        aEvent.State >>= aString;
        aBuffer.append(aString);
    }
    // 型態是 OUString[]
    else if (aType == cppu::UnoType<css::uno::Sequence<OUString>>::get())
    {
        css::uno::Sequence<OUString> aSeq;
        aEvent.State >>= aSeq;
        if (aEvent.FeatureURL.Path == "LanguageStatus" ||
            aEvent.FeatureURL.Path == "StatePageNumber")
        {
            aBuffer.append(aSeq[0]);
        }
        else
        {
            aBuffer.append(u'{');
            for (sal_Int32 itSeq = 0; itSeq < aSeq.getLength(); itSeq++)
            {
                aBuffer.append("\"").append(aSeq[itSeq]);
                if (itSeq != aSeq.getLength() - 1)
                    aBuffer.append("\":true,");
                else
                    aBuffer.append("\":true");
            }
            aBuffer.append(u'}');
        }
    }
    else if (aType == cppu::UnoType<css::awt::FontDescriptor>::get())
    {
        css::awt::FontDescriptor aFontDesc;
        aEvent.State >>= aFontDesc;
        aBuffer.append(aFontDesc.Name);
    }
    else if (aType == cppu::UnoType<css::frame::status::FontHeight>::get())
    {
        css::frame::status::FontHeight aFontHeight;
        aEvent.State >>= aFontHeight;
        aBuffer.append(aFontHeight.Height);
    }
    else if (aType == cppu::UnoType<css::frame::status::Template>::get())
    {
        css::frame::status::Template aTemplate;
        aEvent.State >>= aTemplate;
        aBuffer.append(aTemplate.StyleName);
    }
    else if (aType == cppu::UnoType<css::awt::Point>::get())
    {
        css::awt::Point aPoint;
        aEvent.State >>= aPoint;
        aBuffer.append(OUString::number(aPoint.X)).append(" / ").append(OUString::number(aPoint.Y));
    }
    else if (aType == cppu::UnoType<css::awt::Size>::get())
    {
        css::awt::Size aSize;
        aEvent.State >>= aSize;
        aBuffer.append(OUString::number(aSize.Width)).append(" x ").append(OUString::number(aSize.Height));
    }
    else if (aType == cppu::UnoType<css::awt::Rectangle>::get())
    {
        css::awt::Rectangle aRectangle;
        aEvent.State >>= aRectangle;
        aBuffer.append(aRectangle.X).append(",")
               .append(aRectangle.Y).append(",")
               .append(aRectangle.Width).append(",")
               .append(aRectangle.Height);
    }
    else if (aType == cppu::UnoType<css::drawing::LineCap>::get())
    {
        css::drawing::LineCap aLineCap;
        aEvent.State >>= aLineCap;
        switch (aLineCap)
        {
            case drawing::LineCap_BUTT:
                aBuffer.append("butt");
                break;
            case drawing::LineCap_ROUND:
                aBuffer.append("round");
                break;
            case drawing::LineCap_SQUARE:
                aBuffer.append("square");
                break;
            default:
                aBuffer.append("unknown");
                break;
        }
    }
    else if (aType == cppu::UnoType<css::drawing::LineJoint>::get())
    {
        css::drawing::LineJoint aLineJoint;
        aEvent.State >>= aLineJoint;
        switch (aLineJoint)
        {
            case drawing::LineJoint_NONE:
                aBuffer.append("none");
                break;
            case drawing::LineJoint_MIDDLE:
                aBuffer.append("middle");
                break;
            case drawing::LineJoint_BEVEL:
                aBuffer.append("bevel");
                break;
            case drawing::LineJoint_MITER:
                aBuffer.append("miter");
                break;
            case drawing::LineJoint_ROUND:
                aBuffer.append("round");
                break;
            default:
                aBuffer.append("unknown");
                break;
        }
    }
    else if (aType == cppu::UnoType<css::drawing::LineStyle>::get())
    {
        css::drawing::LineStyle aLineStyle;
        aEvent.State >>= aLineStyle;
        switch (aLineStyle)
        {
            case drawing::LineStyle_NONE:
                aBuffer.append("none");
                break;
            case drawing::LineStyle_SOLID:
                aBuffer.append("soled");
                break;
            case drawing::LineStyle_DASH:
                aBuffer.append("dash");
                break;
            default:
                aBuffer.append("unknown");
                break;
        }
    }
    else if (aType == cppu::UnoType<css::style::LineSpacing>::get())
    {
        css::style::LineSpacing aLineSpacing;
        aEvent.State >>= aLineSpacing;

        boost::property_tree::ptree aItem;
        OUString aSpacingMode = "unknown";
        switch (aLineSpacing.Mode)
        {
            case css::style::LineSpacingMode::PROP:
                aSpacingMode = "prop";
                break;
            case css::style::LineSpacingMode::MINIMUM:
                aSpacingMode = "minimum";
                break;
            case css::style::LineSpacingMode::LEADING:
                aSpacingMode = "leading";
                break;
            case css::style::LineSpacingMode::FIX:
                aSpacingMode = "fix";
                break;
        }
        aItem.add("Mode", aSpacingMode);
        aItem.add("Height", aLineSpacing.Height);

        std::stringstream aStream;
        boost::property_tree::write_json(aStream, aItem, false);
        aBuffer.appendAscii(aStream.str().c_str());
    }
    else if (aType == cppu::UnoType<css::table::BorderLine2>::get())
    {
        css::table::BorderLine2 aBorderLine;
        aEvent.State >>= aBorderLine;

        OUString aLineStyle = "unknown";
        switch (aBorderLine.LineStyle)
        {
            case css::table::BorderLineStyle::DASHED: // 2
                aLineStyle = "dashed";
                break;
            case css::table::BorderLineStyle::DASH_DOT: // 16
                aLineStyle = "dash_dot";
                break;
            case css::table::BorderLineStyle::DASH_DOT_DOT: // 17
                aLineStyle = "dash_dot_dot";
                break;
            case css::table::BorderLineStyle::DOTTED: // 1
                aLineStyle = "dotted";
                break;
            case css::table::BorderLineStyle::DOUBLE: // 3
                aLineStyle = "double";
                break;
            case css::table::BorderLineStyle::DOUBLE_THIN: // 15
                aLineStyle = "double_thin";
                break;
            case css::table::BorderLineStyle::EMBOSSED: // 10
                aLineStyle = "embossed";
                break;
            case css::table::BorderLineStyle::ENGRAVED: // 11
                aLineStyle = "engraved";
                break;
            case css::table::BorderLineStyle::FINE_DASHED: // 14
                aLineStyle = "fine_dashed";
                break;
            case css::table::BorderLineStyle::INSET: // 13
                aLineStyle = "inset";
                break;
            case css::table::BorderLineStyle::NONE: // 32767
                aLineStyle = "none";
                break;
            case css::table::BorderLineStyle::OUTSET: // 12
                aLineStyle = "outset";
                break;
            case css::table::BorderLineStyle::SOLID: // 0
                aLineStyle = "solid";
                break;
            case css::table::BorderLineStyle::THICKTHIN_LARGEGAP: // 9
                aLineStyle = "thickthin_largegap";
                break;
            case css::table::BorderLineStyle::THICKTHIN_MEDIUMGAP: // 8
                aLineStyle = "thickthin_mediumgap";
                break;
            case css::table::BorderLineStyle::THICKTHIN_SMALLGAP: // 7
                aLineStyle = "thickthin_smallgap";
                break;
            case css::table::BorderLineStyle::THINTHICK_LARGEGAP: // 6
                aLineStyle = "thinthick_largegap";
                break;
            case css::table::BorderLineStyle::THINTHICK_MEDIUMGAP: // 5
                aLineStyle = "thinthick_mediumgap";
                break;
            case css::table::BorderLineStyle::THINTHICK_SMALLGAP: // 4
                aLineStyle = "thinthick_smallgap";
                break;
        }
        boost::property_tree::ptree aItem;
        aItem.add("Color", aBorderLine.Color);
        aItem.add("InnerLineWidth", aBorderLine.InnerLineWidth);
        aItem.add("OuterLineWidth", aBorderLine.OuterLineWidth);
        aItem.add("LineDistance", aBorderLine.LineDistance);
        aItem.add("LineStyle", aLineStyle);
        aItem.add("LineWidth", aBorderLine.LineWidth);

        std::stringstream aStream;
        boost::property_tree::write_json(aStream, aItem, false);
        aBuffer.appendAscii(aStream.str().c_str());
    }
    else if (aType == cppu::UnoType<css::table::CellHoriJustify>::get())
    {
        css::table::CellHoriJustify aHoriJustify;
        aEvent.State >>= aHoriJustify;
        switch (aHoriJustify)
        {
            case css::table::CellHoriJustify_LEFT:
            aBuffer.append("left");
            break;
            case css::table::CellHoriJustify_CENTER:
                aBuffer.append("center");
                break;
            case css::table::CellHoriJustify_RIGHT:
                aBuffer.append("right");
                break;
            case css::table::CellHoriJustify_BLOCK:
                aBuffer.append("block");
                break;
            case css::table::CellHoriJustify_REPEAT:
                aBuffer.append("repeat");
                break;
            case css::table::CellHoriJustify_STANDARD:
            default:
                aBuffer.append("standard");
                break;
        }
    }
    /* TODO: 目前看來尚不需要解析 css::beans::PropertyValue 陣列
    else if (aType == cppu::UnoType<css::uno::Sequence<css::beans::PropertyValue>>::get())
    {
        boost::property_tree::ptree aItem;
        css::uno::Sequence<css::beans::PropertyValue> aPropSeq;
        aEvent.State >>= aPropSeq;
        for (sal_Int32 itSeq = 0; itSeq < aPropSeq.getLength(); itSeq++)
        {
            const css::beans::PropertyValue& rProp = aPropSeq[itSeq];
            aItem.put(rProp.Name.toUtf8().getStr(), rProp.Value);
        }
        std::stringstream aStream;
        boost::property_tree::write_json(aStream, aItem, false);
        aBuffer.appendAscii(aStream.str().c_str());
    } */
    else if (aType == cppu::UnoType<css::frame::status::Visibility>::get())
    {
        css::frame::status::Visibility aVisibility;
        aEvent.State >>= aVisibility;
        aBuffer.append("{\"visible\":").append(aVisibility.bVisible).append("}");
    }
    // TODO: 如果有選取區域的話，極易產生此種 type
    else if (aType == cppu::UnoType<css::frame::status::ItemStatus>::get())
    {
        frame::status::ItemStatus aItemStatus;
        aEvent.State >>= aItemStatus;
        SfxItemState eState = static_cast<SfxItemState>(aItemStatus.State);
        OUString eStateName = "*";
        switch (eState)
        {
            case SfxItemState::UNKNOWN:
                eStateName = "UNKNOWN";
                break;
            case SfxItemState::DISABLED:
                eStateName = "DISABLED";
                aBuffer.append("disabled");
                break;
            case SfxItemState::READONLY:
                eStateName = "READONLY";
                break;
            case SfxItemState::DONTCARE:
                eStateName = "DONTCARE";
                break;
            case SfxItemState::DEFAULT:
                eStateName = "DEFAULT";
                break;
            case SfxItemState::SET:
                eStateName = "SET";
                break;
        }
    }
    else
    {
        const SfxViewShell* pViewShell = SfxViewShell::Current();
        boost::property_tree::ptree aItem;

        // Try to send JSON state version
        if (pViewShell && pState && pState != INVALID_POOL_ITEM)
        {
            aItem = pState->dumpAsJSON();
        }

        if (aItem.count("state"))
        {
            aItem.put("commandName", aEvent.FeatureURL.Complete);
            aBuffer.setLength(0);  // 清空 aBuffer
            std::stringstream aStream;
            boost::property_tree::write_json(aStream, aItem, false);
            aBuffer.appendAscii(aStream.str().c_str());
        }
        else
        {
            SAL_WARN("lok_StateChange", aEvent.FeatureURL.Complete << "=unknown type(" << aEvent.State.getValueTypeName() << ")");
            return;
        }
    }

    OUString payload = aBuffer.makeStringAndClear();
    if (const SfxViewShell* pViewShell = pViewFrame->GetViewShell())
    {
        pViewShell->libreOfficeKitViewCallback(LOK_CALLBACK_STATE_CHANGED, payload.toUtf8().getStr());
        SAL_INFO("lok_StateChange", payload.toUtf8().getStr());
    }
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
