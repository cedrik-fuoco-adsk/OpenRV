//
//  Copyright (c) 2011 Tweak Software.
//  All rights reserved.
//
//  SPDX-License-Identifier: Apache-2.0
//
//
#ifndef __RvCommon__QTGLVideoDevice__h__
#define __RvCommon__QTGLVideoDevice__h__
#include <iostream>
#include <TwkGLF/GLVideoDevice.h>
#include <QOpenGLWidget>
#include <QWindow>
#include <QtWidgets/QWidget>
#include <RvCommon/QTTranslator.h>

namespace Rv
{

    //
    //  QTGLVideoDevice
    //
    //  Wraps a QGLWidget as a TwkGLF::GLVideoDevice. This gives a handle
    //  on a concrete window system device. QTGLVideoDevice can generate
    //  events from the window system
    //

    class QTGLVideoDevice : public TwkGLF::GLVideoDevice
    {
    public:
        QTGLVideoDevice(TwkApp::VideoModule*, const std::string& name, QOpenGLWidget* view);
        QTGLVideoDevice(TwkApp::VideoModule*, const std::string& name);
        virtual ~QTGLVideoDevice();

        void setWidget(QOpenGLWidget*);

        QOpenGLWidget* widget() const { return m_view; }

        virtual void makeCurrent() const;

        const QTTranslator& translator() const { return *m_translator; }

        virtual void redraw() const;
        virtual void redrawImmediately() const;

        void setAbsolutePosition(int x, int y);

        //
        //  VideoDevice API
        //

        virtual GLVideoDevice* newSharedContextWorkerDevice() const;
        virtual Resolution resolution() const;
        virtual Offset offset() const;
        virtual Timing timing() const;
        virtual VideoFormat format() const;

        virtual size_t width() const;
        virtual size_t height() const;

        virtual Resolution internalResolution() const;

        virtual void open(const StringVector&);
        virtual void close();
        virtual bool isOpen() const;

        virtual void syncBuffers() const;

        virtual GLuint fboID() const;

        //
        //  High-precision (RGBA16F) offscreen render target.
        //
        //  Opt-in. When enabled the session renders into a 16-bit float FBO
        //  instead of the 8-bit QOpenGLWidget default framebuffer, so >8-bit
        //  content keeps its precision (mirrors the macOS QTMetalVideoDevice
        //  path). Used by the Linux Vulkan bridge backend; off by default so the
        //  normal on-screen GL path and other platforms are unaffected.
        //
        void setHighPrecisionRender(bool enable);

        virtual TwkGLF::GLFBO* defaultFBO() override;
        virtual const TwkGLF::GLFBO* defaultFBO() const override;

        bool isWorkerDevice() const { return Capabilities(capabilities()) == NoCapabilities; }

        virtual void setPhysicalDevice(VideoDevice* d);

        // Device pixel ratio for high DPI displays
        // For reference: https://doc.qt.io/qt-6/highdpi.html
        float devicePixelRatio() const override { return m_devicePixelRatio; }

    protected:
        QTGLVideoDevice(const std::string& name, QOpenGLWidget* view);

        // Lazily (re)create the RGBA16F render FBO sized to the view; no-op when
        // high-precision rendering is disabled or the size is unchanged.
        void ensureHighPrecisionFBO() const;

    protected:
        int m_x;
        int m_y;
        float m_refresh;
        float m_devicePixelRatio{1.0f};
        QOpenGLWidget* m_view;
        QTTranslator* m_translator;

        bool m_highPrecisionRender{false};
        mutable TwkGLF::GLFBO* m_renderFBO{nullptr};
        mutable unsigned int m_renderColorTex{0}; // attached to m_renderFBO; GLFBO does not own it
        mutable int m_renderFBOWidth{0};
        mutable int m_renderFBOHeight{0};
    };

} // namespace Rv

#endif // __RvCommon__QTGLVideoDevice__h__
