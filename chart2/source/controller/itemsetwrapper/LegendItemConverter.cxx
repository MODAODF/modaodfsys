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

#include <LegendItemConverter.hxx>
#include "SchWhichPairs.hxx"
#include <GraphicPropertyItemConverter.hxx>
#include <CharacterPropertyItemConverter.hxx>
#include <com/sun/star/chart2/LegendPosition.hpp>
#include <com/sun/star/chart/ChartLegendExpansion.hpp>
#include <com/sun/star/beans/XPropertySet.hpp>

#include <svl/intitem.hxx>
#include <svl/eitem.hxx>
#include <tools/diagnose_ex.h>

#include <memory>

using namespace ::com::sun::star;

namespace chart::wrapper
{

LegendItemConverter::LegendItemConverter(
    const css::uno::Reference< css::beans::XPropertySet > & rPropertySet,
    SfxItemPool& rItemPool,
    SdrModel& rDrawModel,
    const uno::Reference< lang::XMultiServiceFactory > & xNamedPropertyContainerFactory,
    const awt::Size* pRefSize ) :
        ItemConverter( rPropertySet, rItemPool )
{
    m_aConverters.emplace_back( new GraphicPropertyItemConverter(
                                 rPropertySet, rItemPool, rDrawModel, xNamedPropertyContainerFactory,
                                 GraphicObjectType::LineAndFillProperties ));
    m_aConverters.emplace_back( new CharacterPropertyItemConverter(
                                 rPropertySet, rItemPool, pRefSize,
                                 "ReferencePageSize" ));
}

LegendItemConverter::~LegendItemConverter()
{
}

void LegendItemConverter::FillItemSet( SfxItemSet & rOutItemSet ) const
{
    for( const auto& pConv : m_aConverters )
        pConv->FillItemSet( rOutItemSet );

    // own items
    ItemConverter::FillItemSet( rOutItemSet );
}

bool LegendItemConverter::ApplyItemSet( const SfxItemSet & rItemSet )
{
    bool bResult = false;

    for( const auto& pConv : m_aConverters )
        bResult = pConv->ApplyItemSet( rItemSet ) || bResult;

    // own items
    return ItemConverter::ApplyItemSet( rItemSet ) || bResult;
}

const sal_uInt16 * LegendItemConverter::GetWhichPairs() const
{
    // must span all used items!
    return nLegendWhichPairs;
}

bool LegendItemConverter::GetItemProperty( tWhichIdType /*nWhichId*/, tPropertyNameWithMemberId & /*rOutProperty*/ ) const
{
    // No own (non-special) properties
    return false;
}

bool LegendItemConverter::ApplySpecialItem( sal_uInt16 nWhichId, const SfxItemSet& rInItemSet )
{
    bool bChanged = false;

    switch( nWhichId )
    {
        case SCHATTR_LEGEND_SHOW:
        {
            const SfxPoolItem* pPoolItem = nullptr;
            if( rInItemSet.GetItemState( SCHATTR_LEGEND_SHOW, true, &pPoolItem ) == SfxItemState::SET )
            {
                bool bShow = static_cast< const SfxBoolItem * >( pPoolItem )->GetValue();
                bool bWasShown = true;
                if( ! (GetPropertySet()->getPropertyValue( "Show" ) >>= bWasShown) ||
                    ( bWasShown != bShow ))
                {
                    GetPropertySet()->setPropertyValue( "Show" , uno::Any( bShow ));
                    bChanged = true;
                }
            }

        }
        break;
        case SCHATTR_LEGEND_POS:
        {
            const SfxPoolItem* pPoolItem = nullptr;
            if( rInItemSet.GetItemState( SCHATTR_LEGEND_POS, true, &pPoolItem ) == SfxItemState::SET )
            {
                chart2::LegendPosition eNewPos = static_cast<chart2::LegendPosition>(static_cast<const SfxInt32Item*>(pPoolItem)->GetValue());

                css::chart::ChartLegendExpansion eExpansion = css::chart::ChartLegendExpansion_HIGH;
                switch( eNewPos )
                {
                    case chart2::LegendPosition_LINE_START:
                    case chart2::LegendPosition_LINE_END:
                        eExpansion = css::chart::ChartLegendExpansion_HIGH;
                        break;
                    case chart2::LegendPosition_PAGE_START:
                    case chart2::LegendPosition_PAGE_END:
                        eExpansion = css::chart::ChartLegendExpansion_WIDE;
                        break;
                    default:
                        break;
                }

                try
                {
                    chart2::LegendPosition eOldPos;
                    if( ! ( GetPropertySet()->getPropertyValue( "AnchorPosition" ) >>= eOldPos ) ||
                        ( eOldPos != eNewPos ))
                    {
                        GetPropertySet()->setPropertyValue( "AnchorPosition" , uno::Any( eNewPos ));
                        GetPropertySet()->setPropertyValue( "Expansion" , uno::Any( eExpansion ));
                        GetPropertySet()->setPropertyValue( "RelativePosition" , uno::Any());
                        bChanged = true;
                    }
                }
                catch( const uno::Exception & )
                {
                    DBG_UNHANDLED_EXCEPTION("chart2");
                }
            }
        }
        break;
        case SCHATTR_LEGEND_NO_OVERLAY:
        {
            const SfxPoolItem* pPoolItem = nullptr;
            if(rInItemSet.GetItemState(SCHATTR_LEGEND_NO_OVERLAY, true, &pPoolItem) == SfxItemState::SET)
            {
                bool bOverlay = !static_cast<const SfxBoolItem *>(pPoolItem)->GetValue();
                bool bOldOverlay = false;
                if(!(GetPropertySet()->getPropertyValue("Overlay") >>= bOldOverlay) ||
                    (bOldOverlay != bOverlay))
                {
                    GetPropertySet()->setPropertyValue("Overlay", uno::Any(bOverlay));
                    bChanged = true;
                }
            }

        }
        break;
    }

    return bChanged;
}

void LegendItemConverter::FillSpecialItem(
    sal_uInt16 nWhichId, SfxItemSet & rOutItemSet ) const
{
    switch( nWhichId )
    {
        case SCHATTR_LEGEND_SHOW:
        {
            bool bShow = true;
            GetPropertySet()->getPropertyValue( "Show" ) >>= bShow;
            rOutItemSet.Put( SfxBoolItem(SCHATTR_LEGEND_SHOW, bShow) );
        }
        break;
        case SCHATTR_LEGEND_POS:
        {
            chart2::LegendPosition eLegendPos( chart2::LegendPosition_LINE_END );
            GetPropertySet()->getPropertyValue( "AnchorPosition" ) >>= eLegendPos;
            rOutItemSet.Put( SfxInt32Item(SCHATTR_LEGEND_POS, static_cast<sal_Int32>(eLegendPos) ) );
        }
        break;
        case SCHATTR_LEGEND_NO_OVERLAY:
        {
            bool bOverlay = false;
            GetPropertySet()->getPropertyValue("Overlay") >>= bOverlay;
            rOutItemSet.Put(SfxBoolItem(SCHATTR_LEGEND_NO_OVERLAY, !bOverlay));
        }
        break;
   }
}

} //  namespace chart::wrapper

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */