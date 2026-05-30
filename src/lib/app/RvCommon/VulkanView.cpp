//
// Copyright (C) 2026 Autodesk, Inc. All Rights Reserved.
//
// SPDX-License-Identifier: Apache-2.0
//

#ifdef PLATFORM_LINUX

#include <RvCommon/VulkanView.h>
#include <RvCommon/GLView.h>
#include <RvCommon/QTVulkanVideoDevice.h>
#include <RvCommon/RvDocument.h>
#include <QCoreApplication>
#include <QColor>
#include <QPalette>
#include <QVBoxLayout>
#include <QWindow>

namespace Rv
{
    VulkanView::VulkanView(RvDocument* doc, GLView* backendView, QWidget* parent)
        : QWidget(parent)
        , m_doc(doc)
        , m_backendView(nullptr)
        , m_presentationWindow(new QWindow())
        , m_windowContainer(nullptr)
        , m_vulkanVideoDevice(makeNoOpQTVulkanVideoDevice())
        , m_stopProcessingEvents(false)
        , m_csize(1024, 576)
        , m_msize(128, 128)
    {
        setObjectName("VulkanView");
        setFocusPolicy(Qt::StrongFocus);
        setMouseTracking(true);
        setAcceptDrops(true);

        m_presentationWindow->setObjectName("VulkanPresentationWindow");
        m_presentationWindow->setSurfaceType(QSurface::VulkanSurface);

        m_windowContainer = QWidget::createWindowContainer(m_presentationWindow, this);
        m_windowContainer->setFocusPolicy(Qt::NoFocus);
        m_windowContainer->setMouseTracking(true);
        m_windowContainer->setAcceptDrops(true);
        m_windowContainer->setAutoFillBackground(true);
        m_windowContainer->setPalette(QPalette(QColor(24, 24, 32)));

        QVBoxLayout* layout = new QVBoxLayout(this);
        layout->setSpacing(0);
        layout->setContentsMargins(0, 0, 0, 0);
        layout->addWidget(m_windowContainer);

        setBackendView(backendView);

        m_windowContainer->installEventFilter(this);
        m_presentationWindow->installEventFilter(this);
    }

    VulkanView::~VulkanView()
    {
        m_vulkanVideoDevice.reset();
    }

    bool VulkanView::isNoOp() const
    {
        return !m_vulkanVideoDevice || m_vulkanVideoDevice->isNoOp();
    }

    void VulkanView::setBackendView(GLView* backendView)
    {
        m_backendView = backendView;
        if (m_vulkanVideoDevice)
            m_vulkanVideoDevice->setBridgeSourceView(m_backendView);
        if (!m_backendView)
            return;

        m_backendView->setParent(this);
        // Keep a live backend GLView so its normal paint/update cycle continues
        // (session render path, FTGL texture setup, etc.) while Vulkan owns the
        // visible presentation surface.
        m_backendView->setAttribute(Qt::WA_TransparentForMouseEvents, true);
        m_backendView->setFocusPolicy(Qt::NoFocus);
        m_backendView->setGeometry(rect());
        m_backendView->lower();
        if (m_windowContainer)
            m_windowContainer->raise();
        m_backendView->show();
        m_backendView->update();
    }

    void VulkanView::stopProcessingEvents()
    {
        m_stopProcessingEvents = true;
        if (m_backendView)
            m_backendView->stopProcessingEvents();
    }

    bool VulkanView::forwardEventToBackend(QEvent* event)
    {
        if (!m_backendView)
            return false;

        if (QEvent* copiedEvent = event->clone())
        {
            QCoreApplication::postEvent(m_backendView, copiedEvent);
            return true;
        }

        return false;
    }

    void VulkanView::renderVulkanFrame()
    {
        if (m_stopProcessingEvents || !m_presentationWindow || !m_vulkanVideoDevice)
            return;

        if (!m_presentationWindow->isExposed())
            return;

        if (!m_vulkanVideoDevice->isInitialized() &&
            !m_vulkanVideoDevice->initializeForWindow(m_presentationWindow))
        {
            return;
        }

        m_vulkanVideoDevice->renderFrame();
        m_presentationWindow->requestUpdate();
    }

    bool VulkanView::event(QEvent* event)
    {
        if (m_stopProcessingEvents)
        {
            event->accept();
            return true;
        }

        switch (event->type())
        {
        case QEvent::Show:
            if (m_backendView)
            {
                m_backendView->setGeometry(rect());
                m_backendView->show();
                m_backendView->update();
            }
            if (m_presentationWindow)
                m_presentationWindow->requestUpdate();
            break;
        case QEvent::UpdateRequest:
            if (m_backendView)
                m_backendView->update();
            break;
        case QEvent::Resize:
        {
            if (m_backendView)
            {
                m_backendView->setGeometry(rect());
                m_backendView->update();
            }
            if (m_doc)
            {
                const QSize s = size();
                m_doc->viewSizeChanged(s.width(), s.height());
            }
            if (m_vulkanVideoDevice)
                m_vulkanVideoDevice->resizeSwapchain();
            break;
        }
        default:
            break;
        }

        return QWidget::event(event);
    }

    bool VulkanView::eventFilter(QObject* watched, QEvent* event)
    {
        if (watched == m_presentationWindow)
        {
            switch (event->type())
            {
            case QEvent::Expose:
                if (m_presentationWindow && m_presentationWindow->isExposed())
                    m_presentationWindow->requestUpdate();
                break;
            case QEvent::Resize:
                if (m_vulkanVideoDevice)
                    m_vulkanVideoDevice->resizeSwapchain();
                if (m_presentationWindow && m_presentationWindow->isExposed())
                    m_presentationWindow->requestUpdate();
                break;
            case QEvent::UpdateRequest:
                renderVulkanFrame();
                return true;
            default:
                break;
            }
        }

        // Only forward QWidget-container input events. QWindow-native events use
        // different event classes/coordinates and can recurse badly when routed
        // through the GLView Qt-translator path.
        if (watched == m_windowContainer)
        {
            switch (event->type())
            {
            case QEvent::KeyPress:
            case QEvent::KeyRelease:
            case QEvent::MouseButtonPress:
            case QEvent::MouseButtonRelease:
            case QEvent::MouseButtonDblClick:
            case QEvent::MouseMove:
            case QEvent::Wheel:
            case QEvent::DragEnter:
            case QEvent::DragMove:
            case QEvent::DragLeave:
            case QEvent::Drop:
            case QEvent::TabletPress:
            case QEvent::TabletMove:
            case QEvent::TabletRelease:
                if (forwardEventToBackend(event))
                {
                    event->accept();
                    return true;
                }
                break;
            default:
                break;
            }
        }

        return false;
    }
} // namespace Rv

#endif // PLATFORM_LINUX
