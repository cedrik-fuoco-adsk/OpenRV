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
