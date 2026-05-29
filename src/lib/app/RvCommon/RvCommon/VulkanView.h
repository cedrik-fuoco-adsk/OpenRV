//
// Copyright (C) 2026 Autodesk, Inc. All Rights Reserved.
//
// SPDX-License-Identifier: Apache-2.0
//
#pragma once

#ifdef PLATFORM_LINUX

#include <QWidget>
#include <QSize>

class QEvent;
class QWindow;

namespace Rv
{
    class GLView;
    class RvDocument;

    // Linux-only QWidget wrapper around a native QWindow container that is
    // suitable for a future Vulkan presentation surface.
    class VulkanView : public QWidget
    {
    public:
        explicit VulkanView(RvDocument* doc, GLView* backendView, QWidget* parent = nullptr);
        ~VulkanView() override = default;

        GLView* backendView() const { return m_backendView; }
        void setBackendView(GLView* backendView);

        void stopProcessingEvents();

        void setContentSize(int w, int h) { m_csize = QSize(w, h); }
        void setMinimumContentSize(int w, int h) { m_msize = QSize(w, h); }

        QSize sizeHint() const override { return m_csize; }
        QSize minimumSizeHint() const override { return m_msize; }

        bool isNoOp() const { return true; }

    protected:
        bool event(QEvent* event) override;
        bool eventFilter(QObject* watched, QEvent* event) override;

    private:
        bool forwardEventToBackend(QEvent* event);

    private:
        RvDocument* m_doc;
        GLView* m_backendView;
        QWindow* m_presentationWindow;
        QWidget* m_windowContainer;
        bool m_stopProcessingEvents;
        QSize m_csize;
        QSize m_msize;
    };
} // namespace Rv

#endif // PLATFORM_LINUX
