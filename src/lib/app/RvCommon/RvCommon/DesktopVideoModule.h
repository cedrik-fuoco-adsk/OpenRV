//
//  Copyright (c) 2011 Tweak Software.
//  All rights reserved.
//
//  SPDX-License-Identifier: Apache-2.0
//
//
#ifndef __RvCommon__DesktopVideoModule__h__
#define __RvCommon__DesktopVideoModule__h__
#include <TwkGLF/GL.h>
#include <iostream>
#include <TwkApp/VideoModule.h>

namespace TwkGLF
{
    class GLVideoDevice;
}

namespace Rv
{

    //
    //  class DesktopVideoModule
    //
    //  This instantiates whichever video devices it can based on the
    //  platform and availability.
    //

    class DesktopVideoModule : public TwkApp::VideoModule
    {
    public:
        //
        //  shareDevice is the controller's main view device and may be a GL
        //  (QTGLVideoDevice) or Vulkan (QTVulkanVideoDevice) device, so it is
        //  typed as their common base TwkGLF::GLVideoDevice.
        //
        DesktopVideoModule(NativeDisplayPtr np, TwkGLF::GLVideoDevice* shareDevice);
        virtual ~DesktopVideoModule();

        //
        //  Re-evaluate the presentation backend (GL ScreenView vs Vulkan
        //  swapchain) against the current display-depth preference and rebuild
        //  the per-screen devices to match, using shareDevice (the controller's
        //  current main-view device) as the new share device. This is the
        //  post-startup analogue of the constructor's one-time
        //  createDesktopVideoDevices call, needed because the backend decision is
        //  no longer frozen at launch.
        //
        //  A cleanly open device is closed (releasing its Vulkan swapchain / GL
        //  ScreenView) before its old device is destroyed. To avoid a needless
        //  teardown / transient on the second display, this is a no-op when the
        //  effective backend has not changed; it then returns false and leaves
        //  m_devices untouched (the caller still re-binds the share device).
        //  Returns true when the devices were actually rebuilt.
        //
        //  Note: this does not touch the session's output video device. The
        //  caller (RvApplication::rebuildDesktopVideoDevices) owns re-binding the
        //  share device and re-opening the presentation output, because the old
        //  devices this destroys may be referenced as the session output.
        //
        bool rebuildDevices(const TwkGLF::GLVideoDevice* shareDevice);

        virtual std::string name() const;
        virtual void open();
        virtual void close();
        virtual bool isOpen() const;

        //
        //  If possible, derive the appropriate refresh rate or devicefrom
        //  the absolute position of the window on the desktop.
        //

        virtual TwkApp::VideoDevice* deviceFromPosition(int x, int y) const;
    };

} // namespace Rv

#endif // __RvCommon__DesktopVideoModule__h__
