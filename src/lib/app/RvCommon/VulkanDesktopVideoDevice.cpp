//
//  Copyright (c) 2026 Autodesk, Inc. All Rights Reserved.
//
//  SPDX-License-Identifier: Apache-2.0
//
#include <RvCommon/VulkanDesktopVideoDevice.h>
#include <RvCommon/VulkanView.h>
#include <RvCommon/QTVulkanVideoDevice.h>
#include <RvCommon/QTTranslator.h>
#include <IPCore/ImageRenderer.h>

#include <QScreen>
#include <QGuiApplication>

namespace Rv
{
    using namespace std;

    VulkanDesktopVideoDevice::VulkanDesktopVideoDevice(TwkApp::VideoModule* module, const std::string& name, int screen,
                                                       const TwkGLF::GLVideoDevice* shareDevice)
        : DesktopVideoDevice(module, name, screen, shareDevice)
        , m_vulkanView(nullptr)
    {
    }

    VulkanDesktopVideoDevice::~VulkanDesktopVideoDevice() { close(); }

    void VulkanDesktopVideoDevice::open(const StringVector& args)
    {
        //  Passive Vulkan presentation surface: a null doc + presentationMode
        //  means the VulkanView never drives the session and never triggers the
        //  main-window GL fallback. It is composited into and presented by this
        //  device (via the inherited transfer()/transfer2() and syncBuffers()).
        m_vulkanView = new VulkanView(/*doc*/ nullptr, /*parent*/ nullptr, /*noResize*/ true, /*presentationMode*/ true);

        //  The VulkanView owns its QTVulkanVideoDevice; assigning it to the base
        //  m_viewDevice lets the inherited transfer()/transfer2() composite into
        //  its GL FBO exactly as they do for the GL ScreenView path.
        setViewDevice(m_vulkanView->videoDevice());
        m_translator = new QTTranslator(this, m_vulkanView);

        QRect g = screenGeometry();
        m_vulkanView->move(g.x(), g.y());
        m_vulkanView->setGeometry(g);

        if (useFullScreen())
        {
            m_vulkanView->setWindowState(Qt::WindowFullScreen);
        }
        else
        {
            m_vulkanView->setWindowState(Qt::WindowNoState);
        }

        m_vulkanView->setGeometry(g);

        //  Show the window: this is what makes it visible on the target screen
        //  AND triggers VulkanView::showEvent() -> initialize() -> initVulkan()
        //  (surface + swapchain). Without it the presentation surface never
        //  initializes Vulkan and never presents.
        m_vulkanView->show();

        // DIAG (issue 2): a black presentation that still composites+presents (see
        // the transfer/syncBuffers logs) points at window placement, not the feed.
        // Log intended vs actual screen, geometry, visibility and window state so we
        // can tell whether it landed on the main window's screen or was never
        // mapped/fullscreen/raised as expected. One-shot (open() is per enable).
        if (IPCore::ImageRenderer::debugGpu())
        {
            const QList<QScreen*> screens = QGuiApplication::screens();
            const int idx = qtScreen();
            const QString wantName = (idx >= 0 && idx < screens.size()) ? screens[idx]->name() : QString("<invalid>");
            const QRect wantGeom = (idx >= 0 && idx < screens.size()) ? screens[idx]->geometry() : QRect();
            QScreen* actual = m_vulkanView->screen();
            cout << "INFO: VulkanDesktopVideoDevice::open: intended screen " << idx << " '" << wantName.toStdString() << "' geom "
                 << wantGeom.x() << "," << wantGeom.y() << " " << wantGeom.width() << "x" << wantGeom.height() << "; computed geom "
                 << g.x() << "," << g.y() << " " << g.width() << "x" << g.height() << "; fullscreen=" << (useFullScreen() ? 1 : 0) << endl;
            cout << "INFO: VulkanDesktopVideoDevice::open: actual placed screen '"
                 << (actual ? actual->name().toStdString() : std::string("<null>")) << "' geom " << m_vulkanView->geometry().x() << ","
                 << m_vulkanView->geometry().y() << " " << m_vulkanView->geometry().width() << "x" << m_vulkanView->geometry().height()
                 << " visible=" << (m_vulkanView->isVisible() ? 1 : 0) << " windowState=" << int(m_vulkanView->windowState()) << endl;
        }

        //  Prime the offscreen GL context + FBO so the inherited transfer()'s
        //  fboID() guard passes on the first frame (QTVulkanVideoDevice::fboID()
        //  reports 0 until its context/FBO has been created).
        if (m_viewDevice)
        {
            m_viewDevice->makeCurrent();
        }
    }

    void VulkanDesktopVideoDevice::close()
    {
        //  The VulkanView owns its QTVulkanVideoDevice (== base m_viewDevice), so
        //  detach the base pointer WITHOUT deleting it, then delete the view
        //  (whose destructor frees the device and its Vulkan/interop resources).
        setViewDevice(nullptr);

        delete m_vulkanView;
        m_vulkanView = nullptr;

        delete m_translator;
        m_translator = nullptr;
    }

    bool VulkanDesktopVideoDevice::isOpen() const { return m_vulkanView != nullptr; }

    void VulkanDesktopVideoDevice::makeCurrent() const
    {
        if (m_viewDevice)
        {
            m_viewDevice->makeCurrent();
        }
    }

    void VulkanDesktopVideoDevice::redraw() const
    {
        //  Vulkan has no QOpenGLWidget auto-composite, so the frame already
        //  composited into the QTVulkanVideoDevice FBO by transfer()/transfer2()
        //  must be presented explicitly.
        if (m_viewDevice && m_vulkanView && m_vulkanView->isVisible())
            m_viewDevice->syncBuffers();
    }

    void VulkanDesktopVideoDevice::redrawImmediately() const { redraw(); }

    void VulkanDesktopVideoDevice::syncBuffers() const
    {
        if (m_viewDevice && m_vulkanView && m_vulkanView->isVisible())
        {
            // DIAG (issue 2): the present actually ran. If the external output is
            // black while this prints, the composite feed (transfer) or the shared
            // image is the problem, not the present.
            if (IPCore::ImageRenderer::debugGpu())
                cout << "INFO: VulkanDesktopVideoDevice::syncBuffers[screen " << qtScreen() << "]: presenting" << endl;
            m_viewDevice->syncBuffers();
        }
        else if (IPCore::ImageRenderer::debugGpu())
        {
            // DIAG (issue 2): present skipped. Shows which guard failed (a black
            // external output whose view never became visible lands here).
            cout << "INFO: VulkanDesktopVideoDevice::syncBuffers[screen " << qtScreen()
                 << "]: SKIPPED present (viewDevice=" << (m_viewDevice ? 1 : 0) << " vulkanView=" << (m_vulkanView ? 1 : 0)
                 << " visible=" << (m_vulkanView && m_vulkanView->isVisible() ? 1 : 0) << ")" << endl;
        }
    }

} // namespace Rv
