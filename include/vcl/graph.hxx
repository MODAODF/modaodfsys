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

#ifndef INCLUDED_VCL_GRAPH_HXX
#define INCLUDED_VCL_GRAPH_HXX

#include <memory>
#include <vcl/dllapi.h>
#include <tools/solar.h>
#include <rtl/ustring.hxx>
#include <vcl/bitmapex.hxx>
#include <vcl/animate/Animation.hxx>
#include <vcl/gfxlink.hxx>
#include <com/sun/star/uno/Reference.hxx>
#include <vcl/vectorgraphicdata.hxx>
#include <basegfx/vector/b2dsize.hxx>
#include <vcl/GraphicExternalLink.hxx>


enum class GraphicType
{
    NONE,
    Bitmap,
    GdiMetafile,
    Default
};

namespace com { namespace sun { namespace star { namespace graphic { class XGraphic;} } } }
namespace vcl { class Font; }

class Bitmap;
class GDIMetaFile;
class SvStream;
class ImpGraphic;
class OutputDevice;
class ReaderData;

class VCL_DLLPUBLIC GraphicReader
{
public:
    virtual         ~GraphicReader();

    const OUString& GetUpperFilterName() const { return maUpperName; }

    // TODO: when incompatible changes are possible again
    // the preview size hint should be redone
    void            DisablePreviewMode();
    void            SetPreviewSize( const Size& );
    Size            GetPreviewSize() const;

protected:
    OUString        maUpperName;

                    GraphicReader();
private:
    std::unique_ptr<ReaderData>   mpReaderData;
};

class VCL_DLLPUBLIC GraphicConversionParameters
{
private:
    Size const            maSizePixel;            // default is (0,0)

    bool const            mbUnlimitedSize : 1;    // default is false
    bool const            mbAntiAliase : 1;       // default is false
    bool const            mbSnapHorVerLines : 1;  // default is false

public:
    GraphicConversionParameters(
        const Size& rSizePixel = Size(),
        bool bUnlimitedSize = false,
        bool bAntiAliase = false,
        bool bSnapHorVerLines = false)
    :   maSizePixel(rSizePixel),
        mbUnlimitedSize(bUnlimitedSize),
        mbAntiAliase(bAntiAliase),
        mbSnapHorVerLines(bSnapHorVerLines)
    {
    }

    // data read access
    const Size&     getSizePixel() const { return maSizePixel; }
    bool            getUnlimitedSize() const { return mbUnlimitedSize; }
    bool            getAntiAliase() const { return mbAntiAliase; }
    bool            getSnapHorVerLines() const { return mbSnapHorVerLines; }
};

class Image;
class VCL_DLLPUBLIC Graphic
{
private:

    std::shared_ptr<ImpGraphic> mxImpGraphic;

public:

    SAL_DLLPRIVATE void ImplTestRefCount();
    SAL_DLLPRIVATE ImpGraphic* ImplGetImpGraphic() const { return mxImpGraphic.get(); }

public:
                    Graphic();
                    Graphic( const GraphicExternalLink& rGraphicLink );
                    Graphic( const Graphic& rGraphic );
                    Graphic( Graphic&& rGraphic );
                    Graphic( const Bitmap& rBmp );
                    Graphic( const Image& rImage );
                    Graphic( const BitmapEx& rBmpEx );
                    Graphic( const VectorGraphicDataPtr& rVectorGraphicDataPtr );
                    Graphic( const Animation& rAnimation );
                    Graphic( const GDIMetaFile& rMtf );
                    Graphic( const css::uno::Reference< css::graphic::XGraphic >& rxGraphic );

    Graphic&        operator=( const Graphic& rGraphic );
    Graphic&        operator=( Graphic&& rGraphic );
    bool            operator==( const Graphic& rGraphic ) const;
    bool            operator!=( const Graphic& rGraphic ) const;

    bool            IsNone() const;

    void            Clear();

    GraphicType     GetType() const;
    void            SetDefaultType();
    bool            IsSupportedGraphic() const;

    bool            IsTransparent() const;
    bool            IsAlpha() const;
    bool            IsAnimated() const;
    bool            IsEPS() const;

    bool isAvailable() const;
    bool makeAvailable();

    // #i102089# Access of Bitmap potentially will have to rasterconvert the Graphic
    // if it is a MetaFile. To be able to control this conversion it is necessary to
    // allow giving parameters which control AntiAliasing and LineSnapping of the
    // MetaFile when played. Defaults will use a no-AAed, not snapped conversion as
    // before.
    BitmapEx        GetBitmapEx(const GraphicConversionParameters& rParameters = GraphicConversionParameters()) const;
    /// Gives direct access to the contained BitmapEx.
    const BitmapEx& GetBitmapExRef() const;

    Animation       GetAnimation() const;
    const GDIMetaFile& GetGDIMetaFile() const;

    css::uno::Reference< css::graphic::XGraphic > GetXGraphic() const;

    Size            GetPrefSize() const;
    void            SetPrefSize( const Size& rPrefSize );

    MapMode         GetPrefMapMode() const;
    void            SetPrefMapMode( const MapMode& rPrefMapMode );

    basegfx::B2DSize GetPPI() const;

    Size            GetSizePixel( const OutputDevice* pRefDevice = nullptr ) const;

    sal_uLong       GetSizeBytes() const;

    void            Draw( OutputDevice* pOutDev,
                          const Point& rDestPt ) const;
    void            Draw( OutputDevice* pOutDev,
                          const Point& rDestPt,
                          const Size& rDestSize ) const;
    static void     DrawEx( OutputDevice* pOutDev, const OUString& rText,
                          vcl::Font& rFont, const BitmapEx& rBitmap,
                          const Point& rDestPt, const Size& rDestSize );

    void            StartAnimation( OutputDevice* pOutDev,
                          const Point& rDestPt,
                          const Size& rDestSize,
                          long nExtraData = 0,
                          OutputDevice* pFirstFrameOutDev = nullptr );
    void            StopAnimation( OutputDevice* pOutputDevice,
                          long nExtraData );

    void            SetAnimationNotifyHdl( const Link<Animation*,void>& rLink );
    Link<Animation*,void> GetAnimationNotifyHdl() const;

    sal_uInt32      GetAnimationLoopCount() const;

    BitmapChecksum  GetChecksum() const;

    OUString getOriginURL() const;
    void setOriginURL(OUString const & rOriginURL);

    OString getUniqueID() const;

public:

    std::shared_ptr<GraphicReader>& GetContext();
    void                            SetContext( const std::shared_ptr<GraphicReader> &pReader );
    void                            SetDummyContext(bool value);
    bool                            IsDummyContext();
private:
    friend class GraphicObject;

public:
    void            SetGfxLink(const std::shared_ptr<GfxLink>& rGfxLink);
    GfxLink         GetGfxLink() const;
    bool            IsGfxLink() const;

    bool            ExportNative( SvStream& rOStream ) const;

    friend VCL_DLLPUBLIC void WriteGraphic(SvStream& rOStream, const Graphic& rGraphic);
    friend VCL_DLLPUBLIC void ReadGraphic(SvStream& rIStream, Graphic& rGraphic);

public:

    const VectorGraphicDataPtr& getVectorGraphicData() const;

    void setPdfData(const std::shared_ptr<css::uno::Sequence<sal_Int8>>& rPdfData);
    const std::shared_ptr<css::uno::Sequence<sal_Int8>>& getPdfData() const;
    bool hasPdfData() const;

    /// Set the page number of the multi-page source this Graphic is rendered from.
    void setPageNumber(sal_Int32 nPageNumber);
    /// Get the page number of the multi-page source this Graphic is rendered from.
    sal_Int32 getPageNumber() const;

    static css::uno::Sequence<sal_Int8> getUnoTunnelId();
};

namespace std {

template <>
struct hash<Graphic>
{
    std::size_t operator()(Graphic const & rGraphic) const
    {
        return static_cast<std::size_t>(rGraphic.GetChecksum());
    }
};

} // end namespace std

#endif // INCLUDED_VCL_GRAPH_HXX

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
