//
// Copyright (C) 2026 Autodesk, Inc. All Rights Reserved.
//
// SPDX-License-Identifier: Apache-2.0
//

#ifdef PLATFORM_LINUX

#include <RvCommon/QTVulkanVideoDevice.h>

#include <RvCommon/GLView.h>
#include <RvCommon/QTGLVideoDevice.h>

#include <QGuiApplication>
#include <QImage>
#include <QOpenGLContext>
#include <QWindow>

#ifndef VK_USE_PLATFORM_XLIB_KHR
#define VK_USE_PLATFORM_XLIB_KHR
#endif
#include <vulkan/vulkan.h>
#include <X11/Xlib.h>

#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <set>
#include <sstream>
#include <unistd.h>
#include <vector>

#ifndef GL_HANDLE_TYPE_OPAQUE_FD_EXT
#define GL_HANDLE_TYPE_OPAQUE_FD_EXT 0x9586
#endif

#ifndef GL_LAYOUT_GENERAL_EXT
#define GL_LAYOUT_GENERAL_EXT 0x958D
#endif

#ifndef GL_TEXTURE_TILING_EXT
#define GL_TEXTURE_TILING_EXT 0x9580
#endif

#ifndef GL_LINEAR_TILING_EXT
#define GL_LINEAR_TILING_EXT 0x9585
#endif

#ifndef VK_QUEUE_FAMILY_EXTERNAL
#define VK_QUEUE_FAMILY_EXTERNAL VK_QUEUE_FAMILY_EXTERNAL_KHR
#endif

namespace
{
    const char* vkResultString(VkResult result)
    {
        switch (result)
        {
        case VK_SUCCESS:
            return "VK_SUCCESS";
        case VK_NOT_READY:
            return "VK_NOT_READY";
        case VK_TIMEOUT:
            return "VK_TIMEOUT";
        case VK_EVENT_SET:
            return "VK_EVENT_SET";
        case VK_EVENT_RESET:
            return "VK_EVENT_RESET";
        case VK_INCOMPLETE:
            return "VK_INCOMPLETE";
        case VK_ERROR_OUT_OF_HOST_MEMORY:
            return "VK_ERROR_OUT_OF_HOST_MEMORY";
        case VK_ERROR_OUT_OF_DEVICE_MEMORY:
            return "VK_ERROR_OUT_OF_DEVICE_MEMORY";
        case VK_ERROR_INITIALIZATION_FAILED:
            return "VK_ERROR_INITIALIZATION_FAILED";
        case VK_ERROR_DEVICE_LOST:
            return "VK_ERROR_DEVICE_LOST";
        case VK_ERROR_MEMORY_MAP_FAILED:
            return "VK_ERROR_MEMORY_MAP_FAILED";
        case VK_ERROR_LAYER_NOT_PRESENT:
            return "VK_ERROR_LAYER_NOT_PRESENT";
        case VK_ERROR_EXTENSION_NOT_PRESENT:
            return "VK_ERROR_EXTENSION_NOT_PRESENT";
        case VK_ERROR_FEATURE_NOT_PRESENT:
            return "VK_ERROR_FEATURE_NOT_PRESENT";
        case VK_ERROR_INCOMPATIBLE_DRIVER:
            return "VK_ERROR_INCOMPATIBLE_DRIVER";
        case VK_ERROR_TOO_MANY_OBJECTS:
            return "VK_ERROR_TOO_MANY_OBJECTS";
        case VK_ERROR_FORMAT_NOT_SUPPORTED:
            return "VK_ERROR_FORMAT_NOT_SUPPORTED";
        case VK_ERROR_SURFACE_LOST_KHR:
            return "VK_ERROR_SURFACE_LOST_KHR";
        case VK_ERROR_NATIVE_WINDOW_IN_USE_KHR:
            return "VK_ERROR_NATIVE_WINDOW_IN_USE_KHR";
        case VK_SUBOPTIMAL_KHR:
            return "VK_SUBOPTIMAL_KHR";
        case VK_ERROR_OUT_OF_DATE_KHR:
            return "VK_ERROR_OUT_OF_DATE_KHR";
        default:
            return "VK_UNKNOWN_ERROR";
        }
    }

    void logInfo(const std::string& msg)
    {
        std::cout << "[QTVulkanVideoDevice] " << msg << std::endl;
    }

    void logWarn(const std::string& msg)
    {
        std::cerr << "[QTVulkanVideoDevice] WARNING: " << msg << std::endl;
    }

    void logError(const std::string& msg)
    {
        std::cerr << "[QTVulkanVideoDevice] ERROR: " << msg << std::endl;
    }

    bool isTenBitSurfaceFormat(VkFormat format)
    {
        return format == VK_FORMAT_A2B10G10R10_UNORM_PACK32
            || format == VK_FORMAT_A2R10G10B10_UNORM_PACK32;
    }

    std::string formatName(VkFormat format)
    {
        switch (format)
        {
        case VK_FORMAT_A2B10G10R10_UNORM_PACK32:
            return "VK_FORMAT_A2B10G10R10_UNORM_PACK32";
        case VK_FORMAT_A2R10G10B10_UNORM_PACK32:
            return "VK_FORMAT_A2R10G10B10_UNORM_PACK32";
        case VK_FORMAT_B8G8R8A8_UNORM:
            return "VK_FORMAT_B8G8R8A8_UNORM";
        case VK_FORMAT_R8G8B8A8_UNORM:
            return "VK_FORMAT_R8G8B8A8_UNORM";
        case VK_FORMAT_B8G8R8A8_SRGB:
            return "VK_FORMAT_B8G8R8A8_SRGB";
        case VK_FORMAT_R8G8B8A8_SRGB:
            return "VK_FORMAT_R8G8B8A8_SRGB";
        default:
            return "VK_FORMAT_" + std::to_string(static_cast<int>(format));
        }
    }

    std::string colorSpaceName(VkColorSpaceKHR colorSpace)
    {
        switch (colorSpace)
        {
        case VK_COLOR_SPACE_SRGB_NONLINEAR_KHR:
            return "VK_COLOR_SPACE_SRGB_NONLINEAR_KHR";
        case VK_COLOR_SPACE_DISPLAY_P3_NONLINEAR_EXT:
            return "VK_COLOR_SPACE_DISPLAY_P3_NONLINEAR_EXT";
        case VK_COLOR_SPACE_EXTENDED_SRGB_LINEAR_EXT:
            return "VK_COLOR_SPACE_EXTENDED_SRGB_LINEAR_EXT";
        case VK_COLOR_SPACE_EXTENDED_SRGB_NONLINEAR_EXT:
            return "VK_COLOR_SPACE_EXTENDED_SRGB_NONLINEAR_EXT";
        case VK_COLOR_SPACE_HDR10_ST2084_EXT:
            return "VK_COLOR_SPACE_HDR10_ST2084_EXT";
        case VK_COLOR_SPACE_BT2020_LINEAR_EXT:
            return "VK_COLOR_SPACE_BT2020_LINEAR_EXT";
        default:
            return "VK_COLOR_SPACE_" + std::to_string(static_cast<int>(colorSpace));
        }
    }

    uint32_t clampToRange(uint32_t value, uint32_t minValue, uint32_t maxValue)
    {
        return std::max(minValue, std::min(value, maxValue));
    }

    uint32_t quantize10(uint8_t c)
    {
        return static_cast<uint32_t>((static_cast<uint32_t>(c) * 1023u + 127u) / 255u);
    }

    uint32_t quantize2(uint8_t c)
    {
        return static_cast<uint32_t>((static_cast<uint32_t>(c) * 3u + 127u) / 255u);
    }

    using GLCreateMemoryObjectsEXTProc = void (*)(GLsizei n, GLuint* memoryObjects);
    using GLDeleteMemoryObjectsEXTProc = void (*)(GLsizei n, const GLuint* memoryObjects);
    using GLImportMemoryFdEXTProc = void (*)(GLuint memory, GLuint64 size, GLenum handleType, GLint fd);
    using GLTexStorageMem2DEXTProc =
        void (*)(GLenum target, GLsizei levels, GLenum internalFormat, GLsizei width, GLsizei height, GLuint memory, GLuint64 offset);
    using GLGenSemaphoresEXTProc = void (*)(GLsizei n, GLuint* semaphores);
    using GLDeleteSemaphoresEXTProc = void (*)(GLsizei n, const GLuint* semaphores);
    using GLImportSemaphoreFdEXTProc = void (*)(GLuint semaphore, GLenum handleType, GLint fd);
    using GLWaitSemaphoreEXTProc = void (*)(GLuint semaphore,
                                            GLuint numBufferBarriers,
                                            const GLuint* buffers,
                                            GLuint numTextureBarriers,
                                            const GLuint* textures,
                                            const GLenum* srcLayouts);
    using GLSignalSemaphoreEXTProc = void (*)(GLuint semaphore,
                                              GLuint numBufferBarriers,
                                              const GLuint* buffers,
                                              GLuint numTextureBarriers,
                                              const GLuint* textures,
                                              const GLenum* dstLayouts);

    struct GLInteropFunctions
    {
        GLCreateMemoryObjectsEXTProc createMemoryObjects{nullptr};
        GLDeleteMemoryObjectsEXTProc deleteMemoryObjects{nullptr};
        GLImportMemoryFdEXTProc importMemoryFd{nullptr};
        GLTexStorageMem2DEXTProc texStorageMem2D{nullptr};

        bool valid() const
        {
            return createMemoryObjects && deleteMemoryObjects && importMemoryFd && texStorageMem2D;
        }
    };

    struct GLSemaphoreInteropFunctions
    {
        GLGenSemaphoresEXTProc genSemaphores{nullptr};
        GLDeleteSemaphoresEXTProc deleteSemaphores{nullptr};
        GLImportSemaphoreFdEXTProc importSemaphoreFd{nullptr};
        GLWaitSemaphoreEXTProc waitSemaphore{nullptr};
        GLSignalSemaphoreEXTProc signalSemaphore{nullptr};

        bool valid() const
        {
            return genSemaphores && deleteSemaphores && importSemaphoreFd && waitSemaphore && signalSemaphore;
        }
    };

    bool resolveGLInteropFunctions(QOpenGLContext* context,
                                   GLInteropFunctions& fns,
                                   std::string& reason)
    {
        if (!context)
        {
            reason = "No current OpenGL context is available.";
            return false;
        }

        const bool hasMemoryObject = context->hasExtension(QByteArrayLiteral("GL_EXT_memory_object"));
        const bool hasMemoryObjectFd = context->hasExtension(QByteArrayLiteral("GL_EXT_memory_object_fd"));
        if (!hasMemoryObject || !hasMemoryObjectFd)
        {
            reason = "OpenGL context is missing GL_EXT_memory_object and/or GL_EXT_memory_object_fd.";
            return false;
        }

        fns.createMemoryObjects = reinterpret_cast<GLCreateMemoryObjectsEXTProc>(context->getProcAddress("glCreateMemoryObjectsEXT"));
        fns.deleteMemoryObjects = reinterpret_cast<GLDeleteMemoryObjectsEXTProc>(context->getProcAddress("glDeleteMemoryObjectsEXT"));
        fns.importMemoryFd = reinterpret_cast<GLImportMemoryFdEXTProc>(context->getProcAddress("glImportMemoryFdEXT"));
        fns.texStorageMem2D = reinterpret_cast<GLTexStorageMem2DEXTProc>(context->getProcAddress("glTexStorageMem2DEXT"));
        if (!fns.valid())
        {
            reason = "Failed to resolve GL_EXT_memory_object_fd function pointers.";
            return false;
        }

        return true;
    }

    bool resolveGLSemaphoreInteropFunctions(QOpenGLContext* context,
                                            GLSemaphoreInteropFunctions& fns,
                                            std::string& reason)
    {
        if (!context)
        {
            reason = "No current OpenGL context is available for semaphore interop.";
            return false;
        }

        const bool hasSemaphore = context->hasExtension(QByteArrayLiteral("GL_EXT_semaphore"));
        const bool hasSemaphoreFd = context->hasExtension(QByteArrayLiteral("GL_EXT_semaphore_fd"));
        if (!hasSemaphore || !hasSemaphoreFd)
        {
            reason = "OpenGL context is missing GL_EXT_semaphore and/or GL_EXT_semaphore_fd.";
            return false;
        }

        fns.genSemaphores = reinterpret_cast<GLGenSemaphoresEXTProc>(context->getProcAddress("glGenSemaphoresEXT"));
        fns.deleteSemaphores = reinterpret_cast<GLDeleteSemaphoresEXTProc>(context->getProcAddress("glDeleteSemaphoresEXT"));
        fns.importSemaphoreFd = reinterpret_cast<GLImportSemaphoreFdEXTProc>(context->getProcAddress("glImportSemaphoreFdEXT"));
        fns.waitSemaphore = reinterpret_cast<GLWaitSemaphoreEXTProc>(context->getProcAddress("glWaitSemaphoreEXT"));
        fns.signalSemaphore = reinterpret_cast<GLSignalSemaphoreEXTProc>(context->getProcAddress("glSignalSemaphoreEXT"));
        if (!fns.valid())
        {
            reason = "Failed to resolve GL_EXT_semaphore_fd function pointers.";
            return false;
        }

        return true;
    }

    bool formatSupportsBlitSrc(VkPhysicalDevice physicalDevice, VkFormat format)
    {
        VkFormatProperties props{};
        vkGetPhysicalDeviceFormatProperties(physicalDevice, format, &props);
        return (props.optimalTilingFeatures & VK_FORMAT_FEATURE_BLIT_SRC_BIT) != 0;
    }

    bool formatSupportsBlitDst(VkPhysicalDevice physicalDevice, VkFormat format)
    {
        VkFormatProperties props{};
        vkGetPhysicalDeviceFormatProperties(physicalDevice, format, &props);
        return (props.optimalTilingFeatures & VK_FORMAT_FEATURE_BLIT_DST_BIT) != 0;
    }

    bool formatSupportsTransferSrc(VkPhysicalDevice physicalDevice, VkFormat format)
    {
        VkFormatProperties props{};
        vkGetPhysicalDeviceFormatProperties(physicalDevice, format, &props);
        return (props.optimalTilingFeatures & VK_FORMAT_FEATURE_TRANSFER_SRC_BIT) != 0;
    }

    bool formatSupportsTransferDst(VkPhysicalDevice physicalDevice, VkFormat format)
    {
        VkFormatProperties props{};
        vkGetPhysicalDeviceFormatProperties(physicalDevice, format, &props);
        return (props.optimalTilingFeatures & VK_FORMAT_FEATURE_TRANSFER_DST_BIT) != 0;
    }

    bool isA2R10SwapchainFormat(VkFormat format)
    {
        return format == VK_FORMAT_A2R10G10B10_UNORM_PACK32 ||
               format == VK_FORMAT_A2B10G10R10_UNORM_PACK32;
    }
} // namespace

namespace Rv
{
    QTVulkanVideoDevice::QTVulkanVideoDevice() = default;

    QTVulkanVideoDevice::~QTVulkanVideoDevice()
    {
        cleanup();
    }

    bool QTVulkanVideoDevice::initializeForWindow(QWindow* window)
    {
        if (!window)
        {
            logError("initializeForWindow called with null QWindow");
            return false;
        }

        if (m_initialized && m_window == window)
            return true;

        cleanup();
        m_window = window;

        if (!createInstance())
            return false;
        if (!createSurface())
            return false;
        if (!pickPhysicalDevice())
            return false;
        if (!createLogicalDevice())
            return false;
        if (!createSwapchain())
            return false;
        if (!createImageViews())
            return false;
        if (!createRenderPass())
            return false;
        if (!createFramebuffers())
            return false;
        if (!createCommandPool())
            return false;
        if (!createCommandBuffers())
            return false;
        m_gpuBridgeRuntimeDisabled = false;
        m_gpuBridgeDisableReason.clear();
        if (!ensureBridgeResources())
        {
            logWarn("Failed to create Vulkan bridge resources; keeping clear-only fallback path.");
            m_bridgeCopySupported = false;
            destroyBridgeResources();
        }
        if (!createSyncObjects())
            return false;

        m_initialized = true;
        return true;
    }

    void QTVulkanVideoDevice::resizeSwapchain()
    {
        m_swapchainDirty = true;
    }

    void QTVulkanVideoDevice::setBridgeSourceView(GLView* sourceView)
    {
        if (m_bridgeSourceView != sourceView)
        {
            destroyGpuBridgeResources();
        }

        m_bridgeSourceView = sourceView;

        // Render the session into a high-precision (RGBA16F) FBO so >8-bit content
        // keeps its precision through the bridge into the 10-bit swapchain, instead
        // of the 8-bit QOpenGLWidget default framebuffer.
        if (m_bridgeSourceView && m_bridgeSourceView->videoDevice())
            m_bridgeSourceView->videoDevice()->setHighPrecisionRender(true);

        m_bridgeUnavailableLogged = false;
        m_bridgeActivationLogged = false;
        m_gpuBridgeActivationLogged = false;
        m_bridgeStatusLogged = false;
        m_gpuBridgeRuntimeDisabled = false;
        m_gpuBridgeDisableReason.clear();
    }

    void QTVulkanVideoDevice::renderFrame()
    {
        if (!m_initialized || !m_window)
            return;

        if ((m_window->width() < 1 || m_window->height() < 1) &&
            (m_swapchainExtent.width < 1 || m_swapchainExtent.height < 1))
            return;

        if (m_swapchainDirty && !recreateSwapchain())
            return;

        if (!m_bridgeStatusLogged)
        {
            std::ostringstream bridgeStatus;
            bridgeStatus << "Bridge status: sourceView=" << (m_bridgeSourceView ? "set" : "null")
                         << " copySupported=" << (m_bridgeCopySupported ? "true" : "false")
                         << " gpuInteropDeviceExt="
                         << ((m_vulkanExternalMemorySupported && m_vulkanExternalMemoryFdSupported) ? "true" : "false")
                         << " gpuInteropSyncExt="
                         << ((m_vulkanExternalSemaphoreSupported && m_vulkanExternalSemaphoreFdSupported) ? "true" : "false")
                         << " gpuInteropSync=" << (m_gpuBridgeSemaphoreSyncActive ? "semaphore-fd" : "legacy-finish")
                         << " gpuInteropMode=" << (m_gpuBridgeMode.empty() ? "unset" : m_gpuBridgeMode)
                         << " gpuInteropState=" << (m_gpuBridgeRuntimeDisabled ? "disabled" : "enabled")
                         << " swapchainExtent=" << m_swapchainExtent.width << "x" << m_swapchainExtent.height;
            if (m_gpuBridgeRuntimeDisabled && !m_gpuBridgeDisableReason.empty())
            {
                bridgeStatus << " gpuFallbackReason=" << m_gpuBridgeDisableReason;
            }
            logInfo(bridgeStatus.str());
            m_bridgeStatusLogged = true;
        }

        if (m_bridgeCopySupported && m_bridgeSourceView && !m_inFlightFences.empty())
        {
            vkWaitForFences(m_device,
                            static_cast<uint32_t>(m_inFlightFences.size()),
                            m_inFlightFences.data(),
                            VK_TRUE,
                            UINT64_MAX);
        }

        const VkFence currentFence = m_inFlightFences[m_currentFrame];
        vkWaitForFences(m_device, 1, &currentFence, VK_TRUE, UINT64_MAX);

        uint32_t imageIndex = 0;
        VkResult result = VK_SUCCESS;
        bool acquiredImage = false;
        for (int attempt = 0; attempt < 2; ++attempt)
        {
            result = vkAcquireNextImageKHR(m_device,
                                           m_swapchain,
                                           UINT64_MAX,
                                           m_imageAvailableSemaphores[m_currentFrame],
                                           VK_NULL_HANDLE,
                                           &imageIndex);
            if (result == VK_ERROR_OUT_OF_DATE_KHR)
            {
                if (!recreateSwapchain())
                    return;
                continue;
            }
            if (result != VK_SUCCESS && result != VK_SUBOPTIMAL_KHR)
            {
                logError(std::string("vkAcquireNextImageKHR failed: ") + vkResultString(result));
                return;
            }
            acquiredImage = true;
            break;
        }
        if (!acquiredImage)
        {
            logWarn("vkAcquireNextImageKHR remained out-of-date after swapchain recreation; skipping frame.");
            return;
        }

        if (m_imagesInFlight[imageIndex] != VK_NULL_HANDLE)
            vkWaitForFences(m_device, 1, &m_imagesInFlight[imageIndex], VK_TRUE, UINT64_MAX);
        m_imagesInFlight[imageIndex] = currentFence;

        vkResetFences(m_device, 1, &currentFence);
        vkResetCommandBuffer(m_commandBuffers[imageIndex], 0);

        bool useBridgePath = false;
        bool useGpuBridgePath = false;
        if (m_bridgeCopySupported && m_bridgeSourceView && ensureBridgeResources())
        {
            if (!m_gpuBridgeRuntimeDisabled &&
                m_gpuBridgeImage != VK_NULL_HANDLE &&
                m_gpuBridgeImageMemory != VK_NULL_HANDLE &&
                m_gpuBridgeGLFramebuffer != 0)
            {
                std::string gpuBridgeFailureReason;
                useBridgePath = prepareGpuBridgeFrameData(gpuBridgeFailureReason);
                if (useBridgePath)
                {
                    useGpuBridgePath = true;
                    m_bridgeUnavailableLogged = false;
                    if (!m_gpuBridgeActivationLogged)
                    {
                        logInfo("GPU bridge path active: GL framebuffer blit -> Vulkan external-memory image -> swapchain transfer (no CPU readback).");
                        m_gpuBridgeActivationLogged = true;
                    }
                }
                else if (!gpuBridgeFailureReason.empty())
                {
                    m_gpuBridgeRuntimeDisabled = true;
                    m_gpuBridgeDisableReason = gpuBridgeFailureReason;
                    destroyGpuBridgeResources();
                    logWarn("GPU bridge fallback activated: " + gpuBridgeFailureReason +
                            " Falling back to CPU readback bridge.");
                }
            }
        }

        if (!useBridgePath && m_bridgeCopySupported && m_bridgeSourceView && ensureBridgeResources())
        {
            useBridgePath = prepareBridgeFrameData();
            if (useBridgePath)
            {
                if (!m_bridgeActivationLogged)
                {
                    logInfo("CPU bridge path active: GL readback -> CPU pack -> Vulkan staging upload -> swapchain copy");
                    m_bridgeActivationLogged = true;
                }
                m_bridgeUnavailableLogged = false;
            }
            else if (!m_bridgeUnavailableLogged)
            {
                logWarn("Bridge source frame unavailable; using clear-only fallback for this frame.");
                m_bridgeUnavailableLogged = true;
            }
        }

        if (!recordCommandBuffer(m_commandBuffers[imageIndex], imageIndex, useBridgePath, useGpuBridgePath))
            return;

        std::vector<VkPipelineStageFlags> waitStages = {VK_PIPELINE_STAGE_ALL_COMMANDS_BIT};
        std::vector<VkSemaphore> waitSemaphores = {m_imageAvailableSemaphores[m_currentFrame]};
        std::vector<VkSemaphore> signalSemaphores = {m_renderFinishedSemaphores[m_currentFrame]};
        if (useGpuBridgePath && m_gpuBridgeSemaphoreSyncActive)
        {
            const size_t syncIndex = static_cast<size_t>(m_currentFrame);
            waitStages.push_back(VK_PIPELINE_STAGE_TRANSFER_BIT);
            waitSemaphores.push_back(m_gpuBridgeVkReadySemaphores[syncIndex]);
            signalSemaphores.push_back(m_gpuBridgeVkDoneSemaphores[syncIndex]);
        }

        VkSubmitInfo submitInfo{};
        submitInfo.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
        submitInfo.waitSemaphoreCount = static_cast<uint32_t>(waitSemaphores.size());
        submitInfo.pWaitSemaphores = waitSemaphores.data();
        submitInfo.pWaitDstStageMask = waitStages.data();
        submitInfo.commandBufferCount = 1;
        submitInfo.pCommandBuffers = &m_commandBuffers[imageIndex];
        submitInfo.signalSemaphoreCount = static_cast<uint32_t>(signalSemaphores.size());
        submitInfo.pSignalSemaphores = signalSemaphores.data();

        result = vkQueueSubmit(m_graphicsQueue, 1, &submitInfo, currentFence);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkQueueSubmit failed: ") + vkResultString(result));
            return;
        }
        if (useGpuBridgePath && m_gpuBridgeSemaphoreSyncActive)
        {
            const size_t syncIndex = static_cast<size_t>(m_currentFrame);
            m_gpuBridgeAwaitVkDoneOnGl[syncIndex] = 1;
        }

        VkPresentInfoKHR presentInfo{};
        presentInfo.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
        presentInfo.waitSemaphoreCount = 1;
        presentInfo.pWaitSemaphores = &signalSemaphores[0];
        presentInfo.swapchainCount = 1;
        presentInfo.pSwapchains = &m_swapchain;
        presentInfo.pImageIndices = &imageIndex;

        result = vkQueuePresentKHR(m_presentQueue, &presentInfo);
        if (result == VK_ERROR_OUT_OF_DATE_KHR)
        {
            recreateSwapchain();
        }
        else if (result != VK_SUCCESS)
        {
            logError(std::string("vkQueuePresentKHR failed: ") + vkResultString(result));
        }

        ++m_frameCounter;
        m_currentFrame = (m_currentFrame + 1) % kFramesInFlight;
    }

    bool QTVulkanVideoDevice::createInstance()
    {
        const std::vector<const char*> requiredExtensions = {
            VK_KHR_SURFACE_EXTENSION_NAME,
            VK_KHR_XLIB_SURFACE_EXTENSION_NAME
        };

        uint32_t extensionCount = 0;
        vkEnumerateInstanceExtensionProperties(nullptr, &extensionCount, nullptr);
        std::vector<VkExtensionProperties> extensions(extensionCount);
        vkEnumerateInstanceExtensionProperties(nullptr, &extensionCount, extensions.data());

        for (const char* required : requiredExtensions)
        {
            bool found = false;
            for (const VkExtensionProperties& ext : extensions)
            {
                if (std::strcmp(ext.extensionName, required) == 0)
                {
                    found = true;
                    break;
                }
            }

            if (!found)
            {
                logError(std::string("Required instance extension missing: ") + required);
                return false;
            }
        }

        VkApplicationInfo appInfo{};
        appInfo.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
        appInfo.pApplicationName = "OpenRV";
        appInfo.applicationVersion = VK_MAKE_VERSION(1, 0, 0);
        appInfo.pEngineName = "RV";
        appInfo.engineVersion = VK_MAKE_VERSION(1, 0, 0);
        appInfo.apiVersion = VK_API_VERSION_1_0;

        VkInstanceCreateInfo createInfo{};
        createInfo.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
        createInfo.pApplicationInfo = &appInfo;
        createInfo.enabledExtensionCount = static_cast<uint32_t>(requiredExtensions.size());
        createInfo.ppEnabledExtensionNames = requiredExtensions.data();

        const VkResult result = vkCreateInstance(&createInfo, nullptr, &m_instance);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkCreateInstance failed: ") + vkResultString(result));
            return false;
        }

        return true;
    }

    bool QTVulkanVideoDevice::createSurface()
    {
        if (!m_window)
            return false;

        const QString platformName = QGuiApplication::platformName();
        if (platformName != "xcb")
        {
            logError("Only X11/XCB platform is currently supported for Linux Vulkan presentation. platform=" +
                     platformName.toStdString());
            return false;
        }

        m_window->create();
        const WId windowId = m_window->winId();
        if (!windowId)
        {
            logWarn("QWindow has no native X11 window yet; deferring Vulkan surface creation");
            return false;
        }

        m_x11Display = XOpenDisplay(nullptr);
        if (!m_x11Display)
        {
            logError("XOpenDisplay failed while creating Vulkan surface");
            return false;
        }

        VkXlibSurfaceCreateInfoKHR surfaceCreateInfo{};
        surfaceCreateInfo.sType = VK_STRUCTURE_TYPE_XLIB_SURFACE_CREATE_INFO_KHR;
        surfaceCreateInfo.dpy = m_x11Display;
        surfaceCreateInfo.window = static_cast<Window>(windowId);

        const VkResult result =
            vkCreateXlibSurfaceKHR(m_instance, &surfaceCreateInfo, nullptr, &m_surface);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkCreateXlibSurfaceKHR failed: ") + vkResultString(result));
            XCloseDisplay(m_x11Display);
            m_x11Display = nullptr;
            return false;
        }

        return true;
    }

    bool QTVulkanVideoDevice::pickPhysicalDevice()
    {
        uint32_t deviceCount = 0;
        vkEnumeratePhysicalDevices(m_instance, &deviceCount, nullptr);
        if (deviceCount == 0)
        {
            logError("No Vulkan physical devices found");
            return false;
        }

        std::vector<VkPhysicalDevice> devices(deviceCount);
        vkEnumeratePhysicalDevices(m_instance, &deviceCount, devices.data());

        for (VkPhysicalDevice device : devices)
        {
            uint32_t queueFamilyCount = 0;
            vkGetPhysicalDeviceQueueFamilyProperties(device, &queueFamilyCount, nullptr);
            std::vector<VkQueueFamilyProperties> queueFamilies(queueFamilyCount);
            vkGetPhysicalDeviceQueueFamilyProperties(device, &queueFamilyCount, queueFamilies.data());

            uint32_t graphicsFamily = VK_QUEUE_FAMILY_IGNORED;
            uint32_t presentFamily = VK_QUEUE_FAMILY_IGNORED;

            for (uint32_t i = 0; i < queueFamilyCount; ++i)
            {
                if ((queueFamilies[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) &&
                    graphicsFamily == VK_QUEUE_FAMILY_IGNORED)
                {
                    graphicsFamily = i;
                }

                VkBool32 presentSupport = VK_FALSE;
                vkGetPhysicalDeviceSurfaceSupportKHR(device, i, m_surface, &presentSupport);
                if (presentSupport && presentFamily == VK_QUEUE_FAMILY_IGNORED)
                    presentFamily = i;
            }

            if (graphicsFamily == VK_QUEUE_FAMILY_IGNORED || presentFamily == VK_QUEUE_FAMILY_IGNORED)
                continue;

            uint32_t extensionCount = 0;
            vkEnumerateDeviceExtensionProperties(device, nullptr, &extensionCount, nullptr);
            std::vector<VkExtensionProperties> availableExtensions(extensionCount);
            vkEnumerateDeviceExtensionProperties(device, nullptr, &extensionCount, availableExtensions.data());

            bool hasSwapchainExtension = false;
            bool hasExternalMemoryExtension = false;
            bool hasExternalMemoryFdExtension = false;
            bool hasExternalSemaphoreExtension = false;
            bool hasExternalSemaphoreFdExtension = false;
            for (const VkExtensionProperties& extension : availableExtensions)
            {
                if (std::strcmp(extension.extensionName, VK_KHR_SWAPCHAIN_EXTENSION_NAME) == 0)
                {
                    hasSwapchainExtension = true;
                }
                else if (std::strcmp(extension.extensionName, VK_KHR_EXTERNAL_MEMORY_EXTENSION_NAME) == 0)
                {
                    hasExternalMemoryExtension = true;
                }
                else if (std::strcmp(extension.extensionName, VK_KHR_EXTERNAL_MEMORY_FD_EXTENSION_NAME) == 0)
                {
                    hasExternalMemoryFdExtension = true;
                }
                else if (std::strcmp(extension.extensionName, VK_KHR_EXTERNAL_SEMAPHORE_EXTENSION_NAME) == 0)
                {
                    hasExternalSemaphoreExtension = true;
                }
                else if (std::strcmp(extension.extensionName, VK_KHR_EXTERNAL_SEMAPHORE_FD_EXTENSION_NAME) == 0)
                {
                    hasExternalSemaphoreFdExtension = true;
                }
            }
            if (!hasSwapchainExtension)
                continue;

            uint32_t formatCount = 0;
            uint32_t presentModeCount = 0;
            vkGetPhysicalDeviceSurfaceFormatsKHR(device, m_surface, &formatCount, nullptr);
            vkGetPhysicalDeviceSurfacePresentModesKHR(device, m_surface, &presentModeCount, nullptr);

            if (formatCount == 0 || presentModeCount == 0)
                continue;

            m_physicalDevice = device;
            m_graphicsQueueFamily = graphicsFamily;
            m_presentQueueFamily = presentFamily;
            m_vulkanExternalMemorySupported = hasExternalMemoryExtension;
            m_vulkanExternalMemoryFdSupported = hasExternalMemoryFdExtension;
            m_vulkanExternalSemaphoreSupported = hasExternalSemaphoreExtension;
            m_vulkanExternalSemaphoreFdSupported = hasExternalSemaphoreFdExtension;

            VkPhysicalDeviceProperties properties{};
            vkGetPhysicalDeviceProperties(m_physicalDevice, &properties);
            m_isRadvDevice = std::strstr(properties.deviceName, "RADV") != nullptr;
            logInfo("Selected Vulkan physical device: " + std::string(properties.deviceName));
            if (!m_vulkanExternalMemorySupported || !m_vulkanExternalMemoryFdSupported)
            {
                logWarn("Selected Vulkan device lacks VK_KHR_external_memory and/or VK_KHR_external_memory_fd; GPU bridge interop will use CPU fallback.");
            }
            if (!m_vulkanExternalSemaphoreSupported || !m_vulkanExternalSemaphoreFdSupported)
            {
                logWarn("Selected Vulkan device lacks VK_KHR_external_semaphore and/or VK_KHR_external_semaphore_fd; GPU bridge sync will use CPU fallback.");
            }
            return true;
        }

        logError("No Vulkan device supports graphics+presentation+swapchain for this surface");
        return false;
    }

    bool QTVulkanVideoDevice::createLogicalDevice()
    {
        std::set<uint32_t> uniqueFamilies = {m_graphicsQueueFamily, m_presentQueueFamily};
        std::vector<VkDeviceQueueCreateInfo> queueCreateInfos;
        queueCreateInfos.reserve(uniqueFamilies.size());

        float queuePriority = 1.0f;
        for (uint32_t queueFamily : uniqueFamilies)
        {
            VkDeviceQueueCreateInfo queueCreateInfo{};
            queueCreateInfo.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
            queueCreateInfo.queueFamilyIndex = queueFamily;
            queueCreateInfo.queueCount = 1;
            queueCreateInfo.pQueuePriorities = &queuePriority;
            queueCreateInfos.push_back(queueCreateInfo);
        }

        std::vector<const char*> deviceExtensions = {VK_KHR_SWAPCHAIN_EXTENSION_NAME};
        if (m_vulkanExternalMemorySupported && m_vulkanExternalMemoryFdSupported)
        {
            deviceExtensions.push_back(VK_KHR_EXTERNAL_MEMORY_EXTENSION_NAME);
            deviceExtensions.push_back(VK_KHR_EXTERNAL_MEMORY_FD_EXTENSION_NAME);
        }
        if (m_vulkanExternalSemaphoreSupported && m_vulkanExternalSemaphoreFdSupported)
        {
            deviceExtensions.push_back(VK_KHR_EXTERNAL_SEMAPHORE_EXTENSION_NAME);
            deviceExtensions.push_back(VK_KHR_EXTERNAL_SEMAPHORE_FD_EXTENSION_NAME);
        }

        VkDeviceCreateInfo createInfo{};
        createInfo.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
        createInfo.queueCreateInfoCount = static_cast<uint32_t>(queueCreateInfos.size());
        createInfo.pQueueCreateInfos = queueCreateInfos.data();
        createInfo.enabledExtensionCount = static_cast<uint32_t>(deviceExtensions.size());
        createInfo.ppEnabledExtensionNames = deviceExtensions.data();

        const VkResult result = vkCreateDevice(m_physicalDevice, &createInfo, nullptr, &m_device);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkCreateDevice failed: ") + vkResultString(result));
            return false;
        }

        vkGetDeviceQueue(m_device, m_graphicsQueueFamily, 0, &m_graphicsQueue);
        vkGetDeviceQueue(m_device, m_presentQueueFamily, 0, &m_presentQueue);
        return true;
    }

    bool QTVulkanVideoDevice::createSwapchain()
    {
        VkSurfaceCapabilitiesKHR capabilities{};
        vkGetPhysicalDeviceSurfaceCapabilitiesKHR(m_physicalDevice, m_surface, &capabilities);

        uint32_t formatCount = 0;
        vkGetPhysicalDeviceSurfaceFormatsKHR(m_physicalDevice, m_surface, &formatCount, nullptr);
        if (formatCount == 0)
        {
            logError("vkGetPhysicalDeviceSurfaceFormatsKHR returned zero formats");
            return false;
        }

        std::vector<VkSurfaceFormatKHR> formats(formatCount);
        vkGetPhysicalDeviceSurfaceFormatsKHR(m_physicalDevice, m_surface, &formatCount, formats.data());

        if (!m_surfaceFormatsLogged)
        {
            logInfo("vkGetPhysicalDeviceSurfaceFormatsKHR returned " + std::to_string(formats.size()) + " format(s):");
            for (size_t i = 0; i < formats.size(); ++i)
            {
                std::ostringstream os;
                os << "  [" << i << "] format=" << formatName(formats[i].format)
                   << " colorSpace=" << colorSpaceName(formats[i].colorSpace);
                logInfo(os.str());
            }
            m_surfaceFormatsLogged = true;
        }

        uint32_t presentModeCount = 0;
        vkGetPhysicalDeviceSurfacePresentModesKHR(m_physicalDevice, m_surface, &presentModeCount, nullptr);
        std::vector<VkPresentModeKHR> presentModes(presentModeCount);
        vkGetPhysicalDeviceSurfacePresentModesKHR(m_physicalDevice, m_surface, &presentModeCount, presentModes.data());

        VkSurfaceFormatKHR selectedFormat = formats.front();
        const std::vector<VkFormat> preferred10BitFormats = {
            VK_FORMAT_A2B10G10R10_UNORM_PACK32,
            VK_FORMAT_A2R10G10B10_UNORM_PACK32
        };
        const std::vector<VkFormat> preferred8BitFormats = {
            VK_FORMAT_B8G8R8A8_UNORM,
            VK_FORMAT_R8G8B8A8_UNORM
        };

        bool tenBitFormatAvailable = false;
        for (const VkSurfaceFormatKHR& candidate : formats)
        {
            if (isTenBitSurfaceFormat(candidate.format))
            {
                tenBitFormatAvailable = true;
                break;
            }
        }

        auto pickFromList = [&formats, &selectedFormat](const std::vector<VkFormat>& preferredFormats,
                                                        bool requireSrgbColorSpace) -> bool
        {
            for (VkFormat preferred : preferredFormats)
            {
                for (const VkSurfaceFormatKHR& candidate : formats)
                {
                    if (candidate.format == preferred &&
                        (!requireSrgbColorSpace || candidate.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR))
                    {
                        selectedFormat = candidate;
                        return true;
                    }
                }
            }
            return false;
        };

        if (!pickFromList(preferred10BitFormats, true) &&
            !pickFromList(preferred10BitFormats, false) &&
            !pickFromList(preferred8BitFormats, true) &&
            !pickFromList(preferred8BitFormats, false))
        {
            selectedFormat = formats.front();
        }

        m_selectedFormatIs10Bit = isTenBitSurfaceFormat(selectedFormat.format);
        if (!m_selectedFormatIs10Bit)
        {
            if (!tenBitFormatAvailable)
            {
                logWarn("No 10-bit Vulkan swapchain surface format is available; using 8-bit fallback.");
            }
            else
            {
                logWarn("10-bit surface formats are present but none matched preferred ordering; using fallback format.");
            }
        }

        std::ostringstream selectionLog;
        selectionLog << "Selected swapchain format=" << formatName(selectedFormat.format)
                     << " colorSpace=" << colorSpaceName(selectedFormat.colorSpace)
                     << " bitDepth=" << (m_selectedFormatIs10Bit ? "10-bit" : "8-bit");
        logInfo(selectionLog.str());

        VkPresentModeKHR presentMode = VK_PRESENT_MODE_FIFO_KHR;
        for (VkPresentModeKHR mode : presentModes)
        {
            if (mode == VK_PRESENT_MODE_FIFO_KHR)
            {
                presentMode = mode;
                break;
            }
        }

        VkExtent2D extent = capabilities.currentExtent;
        if (extent.width == UINT32_MAX)
        {
            const double dpr = m_window ? m_window->devicePixelRatio() : 1.0;
            const uint32_t requestedWidth =
                static_cast<uint32_t>(std::max(1.0, static_cast<double>(m_window->width()) * dpr));
            const uint32_t requestedHeight =
                static_cast<uint32_t>(std::max(1.0, static_cast<double>(m_window->height()) * dpr));

            extent.width = clampToRange(requestedWidth,
                                        capabilities.minImageExtent.width,
                                        capabilities.maxImageExtent.width);
            extent.height = clampToRange(requestedHeight,
                                         capabilities.minImageExtent.height,
                                         capabilities.maxImageExtent.height);
        }

        uint32_t imageCount = capabilities.minImageCount + 1;
        if (capabilities.maxImageCount > 0)
            imageCount = std::min(imageCount, capabilities.maxImageCount);

        VkCompositeAlphaFlagBitsKHR compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
        const VkCompositeAlphaFlagBitsKHR compositeCandidates[] = {
            VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
            VK_COMPOSITE_ALPHA_PRE_MULTIPLIED_BIT_KHR,
            VK_COMPOSITE_ALPHA_POST_MULTIPLIED_BIT_KHR,
            VK_COMPOSITE_ALPHA_INHERIT_BIT_KHR
        };
        for (VkCompositeAlphaFlagBitsKHR candidate : compositeCandidates)
        {
            if (capabilities.supportedCompositeAlpha & candidate)
            {
                compositeAlpha = candidate;
                break;
            }
        }

        VkSwapchainCreateInfoKHR createInfo{};
        createInfo.sType = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR;
        createInfo.surface = m_surface;
        createInfo.minImageCount = imageCount;
        createInfo.imageFormat = selectedFormat.format;
        createInfo.imageColorSpace = selectedFormat.colorSpace;
        createInfo.imageExtent = extent;
        createInfo.imageArrayLayers = 1;
        createInfo.imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
        m_bridgeCopySupported = (capabilities.supportedUsageFlags & VK_IMAGE_USAGE_TRANSFER_DST_BIT) != 0;
        if (m_bridgeCopySupported)
        {
            createInfo.imageUsage |= VK_IMAGE_USAGE_TRANSFER_DST_BIT;
        }
        else
        {
            logWarn("Swapchain images do not support VK_IMAGE_USAGE_TRANSFER_DST_BIT; bridge path disabled.");
        }
        createInfo.preTransform = capabilities.currentTransform;
        createInfo.compositeAlpha = compositeAlpha;
        createInfo.presentMode = presentMode;
        createInfo.clipped = VK_TRUE;
        createInfo.oldSwapchain = VK_NULL_HANDLE;

        const uint32_t queueFamilyIndices[] = {m_graphicsQueueFamily, m_presentQueueFamily};
        if (m_graphicsQueueFamily != m_presentQueueFamily)
        {
            createInfo.imageSharingMode = VK_SHARING_MODE_CONCURRENT;
            createInfo.queueFamilyIndexCount = 2;
            createInfo.pQueueFamilyIndices = queueFamilyIndices;
        }
        else
        {
            createInfo.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE;
        }

        const VkResult result = vkCreateSwapchainKHR(m_device, &createInfo, nullptr, &m_swapchain);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkCreateSwapchainKHR failed: ") + vkResultString(result));
            return false;
        }

        m_swapchainImageFormat = selectedFormat.format;
        m_swapchainColorSpace = selectedFormat.colorSpace;
        m_swapchainExtent = extent;

        uint32_t swapchainImageCount = 0;
        vkGetSwapchainImagesKHR(m_device, m_swapchain, &swapchainImageCount, nullptr);
        m_swapchainImages.resize(swapchainImageCount);
        vkGetSwapchainImagesKHR(m_device, m_swapchain, &swapchainImageCount, m_swapchainImages.data());
        m_swapchainImageLayouts.assign(m_swapchainImages.size(), VK_IMAGE_LAYOUT_UNDEFINED);

        return true;
    }

    bool QTVulkanVideoDevice::createImageViews()
    {
        m_swapchainImageViews.resize(m_swapchainImages.size(), VK_NULL_HANDLE);

        for (size_t i = 0; i < m_swapchainImages.size(); ++i)
        {
            VkImageViewCreateInfo createInfo{};
            createInfo.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
            createInfo.image = m_swapchainImages[i];
            createInfo.viewType = VK_IMAGE_VIEW_TYPE_2D;
            createInfo.format = m_swapchainImageFormat;
            createInfo.components.r = VK_COMPONENT_SWIZZLE_IDENTITY;
            createInfo.components.g = VK_COMPONENT_SWIZZLE_IDENTITY;
            createInfo.components.b = VK_COMPONENT_SWIZZLE_IDENTITY;
            createInfo.components.a = VK_COMPONENT_SWIZZLE_IDENTITY;
            createInfo.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            createInfo.subresourceRange.baseMipLevel = 0;
            createInfo.subresourceRange.levelCount = 1;
            createInfo.subresourceRange.baseArrayLayer = 0;
            createInfo.subresourceRange.layerCount = 1;

            const VkResult result = vkCreateImageView(m_device, &createInfo, nullptr, &m_swapchainImageViews[i]);
            if (result != VK_SUCCESS)
            {
                logError(std::string("vkCreateImageView failed: ") + vkResultString(result));
                return false;
            }
        }

        return true;
    }

    bool QTVulkanVideoDevice::createRenderPass()
    {
        VkAttachmentDescription colorAttachment{};
        colorAttachment.format = m_swapchainImageFormat;
        colorAttachment.samples = VK_SAMPLE_COUNT_1_BIT;
        colorAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
        colorAttachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
        colorAttachment.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
        colorAttachment.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
        colorAttachment.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        colorAttachment.finalLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;

        VkAttachmentReference colorAttachmentRef{};
        colorAttachmentRef.attachment = 0;
        colorAttachmentRef.layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

        VkSubpassDescription subpass{};
        subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
        subpass.colorAttachmentCount = 1;
        subpass.pColorAttachments = &colorAttachmentRef;

        VkSubpassDependency dependency{};
        dependency.srcSubpass = VK_SUBPASS_EXTERNAL;
        dependency.dstSubpass = 0;
        dependency.srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        dependency.dstStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        dependency.dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;

        VkRenderPassCreateInfo renderPassInfo{};
        renderPassInfo.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
        renderPassInfo.attachmentCount = 1;
        renderPassInfo.pAttachments = &colorAttachment;
        renderPassInfo.subpassCount = 1;
        renderPassInfo.pSubpasses = &subpass;
        renderPassInfo.dependencyCount = 1;
        renderPassInfo.pDependencies = &dependency;

        const VkResult result = vkCreateRenderPass(m_device, &renderPassInfo, nullptr, &m_renderPass);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkCreateRenderPass failed: ") + vkResultString(result));
            return false;
        }
        return true;
    }

    bool QTVulkanVideoDevice::createFramebuffers()
    {
        m_swapchainFramebuffers.resize(m_swapchainImageViews.size(), VK_NULL_HANDLE);

        for (size_t i = 0; i < m_swapchainImageViews.size(); ++i)
        {
            VkImageView attachments[] = {m_swapchainImageViews[i]};

            VkFramebufferCreateInfo framebufferInfo{};
            framebufferInfo.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
            framebufferInfo.renderPass = m_renderPass;
            framebufferInfo.attachmentCount = 1;
            framebufferInfo.pAttachments = attachments;
            framebufferInfo.width = m_swapchainExtent.width;
            framebufferInfo.height = m_swapchainExtent.height;
            framebufferInfo.layers = 1;

            const VkResult result = vkCreateFramebuffer(m_device, &framebufferInfo, nullptr, &m_swapchainFramebuffers[i]);
            if (result != VK_SUCCESS)
            {
                logError(std::string("vkCreateFramebuffer failed: ") + vkResultString(result));
                return false;
            }
        }

        return true;
    }

    bool QTVulkanVideoDevice::createCommandPool()
    {
        VkCommandPoolCreateInfo poolInfo{};
        poolInfo.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
        poolInfo.queueFamilyIndex = m_graphicsQueueFamily;
        poolInfo.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;

        const VkResult result = vkCreateCommandPool(m_device, &poolInfo, nullptr, &m_commandPool);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkCreateCommandPool failed: ") + vkResultString(result));
            return false;
        }
        return true;
    }

    bool QTVulkanVideoDevice::createCommandBuffers()
    {
        if (m_commandPool == VK_NULL_HANDLE)
            return false;

        if (!m_commandBuffers.empty())
        {
            vkFreeCommandBuffers(
                m_device,
                m_commandPool,
                static_cast<uint32_t>(m_commandBuffers.size()),
                m_commandBuffers.data());
            m_commandBuffers.clear();
        }

        m_commandBuffers.resize(m_swapchainFramebuffers.size(), VK_NULL_HANDLE);

        VkCommandBufferAllocateInfo allocInfo{};
        allocInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
        allocInfo.commandPool = m_commandPool;
        allocInfo.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
        allocInfo.commandBufferCount = static_cast<uint32_t>(m_commandBuffers.size());

        const VkResult result = vkAllocateCommandBuffers(m_device, &allocInfo, m_commandBuffers.data());
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkAllocateCommandBuffers failed: ") + vkResultString(result));
            return false;
        }
        return true;
    }

    bool QTVulkanVideoDevice::createSyncObjects()
    {
        m_imageAvailableSemaphores.resize(kFramesInFlight, VK_NULL_HANDLE);
        m_renderFinishedSemaphores.resize(kFramesInFlight, VK_NULL_HANDLE);
        m_inFlightFences.resize(kFramesInFlight, VK_NULL_HANDLE);
        m_imagesInFlight.resize(m_swapchainImages.size(), VK_NULL_HANDLE);

        VkSemaphoreCreateInfo semaphoreInfo{};
        semaphoreInfo.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;

        VkFenceCreateInfo fenceInfo{};
        fenceInfo.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
        fenceInfo.flags = VK_FENCE_CREATE_SIGNALED_BIT;

        for (uint32_t i = 0; i < kFramesInFlight; ++i)
        {
            VkResult result = vkCreateSemaphore(m_device, &semaphoreInfo, nullptr, &m_imageAvailableSemaphores[i]);
            if (result != VK_SUCCESS)
            {
                logError(std::string("vkCreateSemaphore(imageAvailable) failed: ") + vkResultString(result));
                return false;
            }

            result = vkCreateSemaphore(m_device, &semaphoreInfo, nullptr, &m_renderFinishedSemaphores[i]);
            if (result != VK_SUCCESS)
            {
                logError(std::string("vkCreateSemaphore(renderFinished) failed: ") + vkResultString(result));
                return false;
            }

            result = vkCreateFence(m_device, &fenceInfo, nullptr, &m_inFlightFences[i]);
            if (result != VK_SUCCESS)
            {
                logError(std::string("vkCreateFence failed: ") + vkResultString(result));
                return false;
            }
        }

        return true;
    }

    uint32_t QTVulkanVideoDevice::findMemoryType(uint32_t typeFilter,
                                                 VkMemoryPropertyFlags properties) const
    {
        VkPhysicalDeviceMemoryProperties memProperties{};
        vkGetPhysicalDeviceMemoryProperties(m_physicalDevice, &memProperties);

        for (uint32_t i = 0; i < memProperties.memoryTypeCount; ++i)
        {
            const bool typeMatches = (typeFilter & (1u << i)) != 0;
            const bool propertyMatches =
                (memProperties.memoryTypes[i].propertyFlags & properties) == properties;
            if (typeMatches && propertyMatches)
                return i;
        }

        return std::numeric_limits<uint32_t>::max();
    }

    bool QTVulkanVideoDevice::ensureBridgeResources()
    {
        if (!m_bridgeCopySupported)
            return true;

        if (m_device == VK_NULL_HANDLE || m_swapchainExtent.width == 0 || m_swapchainExtent.height == 0)
            return false;

        const VkDeviceSize requiredSize =
            static_cast<VkDeviceSize>(m_swapchainExtent.width) *
            static_cast<VkDeviceSize>(m_swapchainExtent.height) *
            static_cast<VkDeviceSize>(4);

        const bool hasReusableResources =
            m_bridgeStagingBuffer != VK_NULL_HANDLE &&
            m_bridgeStagingMemory != VK_NULL_HANDLE &&
            m_bridgeImage != VK_NULL_HANDLE &&
            m_bridgeImageMemory != VK_NULL_HANDLE &&
            m_bridgeStagingCapacity >= requiredSize;

        if (hasReusableResources)
        {
            ensureGpuBridgeResources();
            return true;
        }

        destroyBridgeResources();

        VkBufferCreateInfo bufferInfo{};
        bufferInfo.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bufferInfo.size = requiredSize;
        bufferInfo.usage = VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
        bufferInfo.sharingMode = VK_SHARING_MODE_EXCLUSIVE;

        VkResult result = vkCreateBuffer(m_device, &bufferInfo, nullptr, &m_bridgeStagingBuffer);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkCreateBuffer(bridge staging) failed: ") + vkResultString(result));
            destroyBridgeResources();
            return false;
        }

        VkMemoryRequirements stagingMemReq{};
        vkGetBufferMemoryRequirements(m_device, m_bridgeStagingBuffer, &stagingMemReq);

        uint32_t stagingMemoryType =
            findMemoryType(stagingMemReq.memoryTypeBits,
                           VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        if (stagingMemoryType == std::numeric_limits<uint32_t>::max())
        {
            logError("No HOST_VISIBLE|HOST_COHERENT memory type found for bridge staging buffer.");
            destroyBridgeResources();
            return false;
        }

        VkMemoryAllocateInfo stagingAllocInfo{};
        stagingAllocInfo.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        stagingAllocInfo.allocationSize = stagingMemReq.size;
        stagingAllocInfo.memoryTypeIndex = stagingMemoryType;

        result = vkAllocateMemory(m_device, &stagingAllocInfo, nullptr, &m_bridgeStagingMemory);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkAllocateMemory(bridge staging) failed: ") + vkResultString(result));
            destroyBridgeResources();
            return false;
        }

        result = vkBindBufferMemory(m_device, m_bridgeStagingBuffer, m_bridgeStagingMemory, 0);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkBindBufferMemory(bridge staging) failed: ") + vkResultString(result));
            destroyBridgeResources();
            return false;
        }

        m_bridgeStagingCapacity = requiredSize;

        VkImageCreateInfo imageInfo{};
        imageInfo.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        imageInfo.imageType = VK_IMAGE_TYPE_2D;
        imageInfo.format = m_swapchainImageFormat;
        imageInfo.extent.width = m_swapchainExtent.width;
        imageInfo.extent.height = m_swapchainExtent.height;
        imageInfo.extent.depth = 1;
        imageInfo.mipLevels = 1;
        imageInfo.arrayLayers = 1;
        imageInfo.samples = VK_SAMPLE_COUNT_1_BIT;
        imageInfo.tiling = VK_IMAGE_TILING_OPTIMAL;
        imageInfo.usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
        imageInfo.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        imageInfo.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;

        result = vkCreateImage(m_device, &imageInfo, nullptr, &m_bridgeImage);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkCreateImage(bridge image) failed: ") + vkResultString(result));
            destroyBridgeResources();
            return false;
        }

        VkMemoryRequirements imageMemReq{};
        vkGetImageMemoryRequirements(m_device, m_bridgeImage, &imageMemReq);

        uint32_t imageMemoryType =
            findMemoryType(imageMemReq.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        if (imageMemoryType == std::numeric_limits<uint32_t>::max())
        {
            imageMemoryType = findMemoryType(imageMemReq.memoryTypeBits, 0);
        }
        if (imageMemoryType == std::numeric_limits<uint32_t>::max())
        {
            logError("No compatible memory type found for bridge image.");
            destroyBridgeResources();
            return false;
        }

        VkMemoryAllocateInfo imageAllocInfo{};
        imageAllocInfo.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        imageAllocInfo.allocationSize = imageMemReq.size;
        imageAllocInfo.memoryTypeIndex = imageMemoryType;

        result = vkAllocateMemory(m_device, &imageAllocInfo, nullptr, &m_bridgeImageMemory);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkAllocateMemory(bridge image) failed: ") + vkResultString(result));
            destroyBridgeResources();
            return false;
        }

        result = vkBindImageMemory(m_device, m_bridgeImage, m_bridgeImageMemory, 0);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkBindImageMemory(bridge image) failed: ") + vkResultString(result));
            destroyBridgeResources();
            return false;
        }

        m_bridgeImageLayout = VK_IMAGE_LAYOUT_UNDEFINED;

        std::ostringstream os;
        os << "CPU bridge resources ready: uploadExtent=" << m_swapchainExtent.width << "x" << m_swapchainExtent.height
           << " dstFormat=" << formatName(m_swapchainImageFormat)
           << " colorSpace=" << colorSpaceName(m_swapchainColorSpace);
        logInfo(os.str());

        ensureGpuBridgeResources();
        return true;
    }

    bool QTVulkanVideoDevice::ensureGpuBridgeResources()
    {
        if (m_gpuBridgeRuntimeDisabled)
            return true;

        if (!m_bridgeSourceView)
            return true;

        if (m_device == VK_NULL_HANDLE || m_swapchainExtent.width == 0 || m_swapchainExtent.height == 0)
            return false;

        const bool canUse10BitBridge =
            isA2R10SwapchainFormat(m_swapchainImageFormat) &&
            formatSupportsTransferSrc(m_physicalDevice, m_swapchainImageFormat) &&
            formatSupportsTransferDst(m_physicalDevice, m_swapchainImageFormat);
        const VkFormat expectedInteropFormat = canUse10BitBridge ? m_swapchainImageFormat : VK_FORMAT_R8G8B8A8_UNORM;

        const bool hasReusableGpuResources =
            m_gpuBridgeImage != VK_NULL_HANDLE &&
            m_gpuBridgeImageMemory != VK_NULL_HANDLE &&
            m_gpuBridgeGLMemoryObject != 0 &&
            m_gpuBridgeGLTexture != 0 &&
            m_gpuBridgeGLFramebuffer != 0 &&
            m_gpuBridgeVkReadySemaphores.size() == kFramesInFlight &&
            m_gpuBridgeVkDoneSemaphores.size() == kFramesInFlight &&
            m_gpuBridgeGLReadySemaphores.size() == kFramesInFlight &&
            m_gpuBridgeGLDoneSemaphores.size() == kFramesInFlight &&
            std::all_of(m_gpuBridgeVkReadySemaphores.begin(),
                        m_gpuBridgeVkReadySemaphores.end(),
                        [](VkSemaphore semaphore) { return semaphore != VK_NULL_HANDLE; }) &&
            std::all_of(m_gpuBridgeVkDoneSemaphores.begin(),
                        m_gpuBridgeVkDoneSemaphores.end(),
                        [](VkSemaphore semaphore) { return semaphore != VK_NULL_HANDLE; }) &&
            std::all_of(m_gpuBridgeGLReadySemaphores.begin(),
                        m_gpuBridgeGLReadySemaphores.end(),
                        [](GLuint semaphore) { return semaphore != 0; }) &&
            std::all_of(m_gpuBridgeGLDoneSemaphores.begin(),
                        m_gpuBridgeGLDoneSemaphores.end(),
                        [](GLuint semaphore) { return semaphore != 0; }) &&
            m_gpuBridgeAwaitVkDoneOnGl.size() == kFramesInFlight &&
            m_gpuBridgeSemaphoreSyncActive &&
            m_gpuBridgeImageFormat == expectedInteropFormat;
        if (hasReusableGpuResources)
            return true;

        auto disableGpuBridge = [this](const std::string& reason)
        {
            m_gpuBridgeRuntimeDisabled = true;
            m_gpuBridgeDisableReason = reason;
            m_bridgeStatusLogged = false;
            destroyGpuBridgeResources();
            logWarn("GPU bridge interop unavailable: " + reason + " Using CPU readback bridge.");
        };

        if (!m_vulkanExternalMemorySupported || !m_vulkanExternalMemoryFdSupported)
        {
            disableGpuBridge("Vulkan external-memory-fd device extensions are not enabled.");
            return true;
        }
        if (!m_vulkanExternalSemaphoreSupported || !m_vulkanExternalSemaphoreFdSupported)
        {
            disableGpuBridge("Vulkan external-semaphore-fd device extensions are not enabled.");
            return true;
        }

        bool use10BitBridge = isA2R10SwapchainFormat(m_swapchainImageFormat);
        if (use10BitBridge &&
            (!formatSupportsTransferSrc(m_physicalDevice, m_swapchainImageFormat) ||
             !formatSupportsTransferDst(m_physicalDevice, m_swapchainImageFormat)))
        {
            logWarn("10-bit GPU bridge format does not support transfer src/dst; falling back to 8-bit bridge + blit mode.");
            use10BitBridge = false;
        }

        const VkFormat interopFormat = use10BitBridge ? m_swapchainImageFormat : VK_FORMAT_R8G8B8A8_UNORM;
        const GLenum interopGLInternalFormat = use10BitBridge ? GL_RGB10_A2 : GL_RGBA8;
        const char* interopGLFormatName = use10BitBridge ? "GL_RGB10_A2" : "GL_RGBA8";
        m_gpuBridgeMode = use10BitBridge ? "10-bit-copy" : "8-bit-blit";
        m_gpuBridgeUsesBlit = interopFormat != m_swapchainImageFormat;
        m_gpuBridgeBlitSupported =
            !m_gpuBridgeUsesBlit ||
            (formatSupportsBlitSrc(m_physicalDevice, interopFormat) &&
             formatSupportsBlitDst(m_physicalDevice, m_swapchainImageFormat));
        if (m_gpuBridgeUsesBlit && !m_gpuBridgeBlitSupported)
        {
            disableGpuBridge("vkCmdBlitImage format conversion is not supported for src=" + formatName(interopFormat) +
                             " dst=" + formatName(m_swapchainImageFormat) + ".");
            return true;
        }

        m_bridgeSourceView->makeCurrent();
        QOpenGLContext* context = QOpenGLContext::currentContext();
        if (!context)
        {
            return true;
        }
        GLInteropFunctions glFns;
        std::string glInteropReason;
        if (!resolveGLInteropFunctions(context, glFns, glInteropReason))
        {
            disableGpuBridge(glInteropReason);
            return true;
        }

        GLSemaphoreInteropFunctions glSemaphoreFns;
        std::string glSemaphoreInteropReason;
        if (!resolveGLSemaphoreInteropFunctions(context, glSemaphoreFns, glSemaphoreInteropReason))
        {
            disableGpuBridge(glSemaphoreInteropReason);
            return true;
        }

        VkImage interopImage = VK_NULL_HANDLE;
        VkDeviceMemory interopMemory = VK_NULL_HANDLE;
        GLuint glMemoryObject = 0;
        GLuint glTexture = 0;
        GLuint glFramebuffer = 0;
        std::vector<VkSemaphore> vkReadySemaphores;
        std::vector<VkSemaphore> vkDoneSemaphores;
        std::vector<GLuint> glReadySemaphores;
        std::vector<GLuint> glDoneSemaphores;
        int memoryFd = -1;
        vkReadySemaphores.reserve(kFramesInFlight);
        vkDoneSemaphores.reserve(kFramesInFlight);
        glReadySemaphores.reserve(kFramesInFlight);
        glDoneSemaphores.reserve(kFramesInFlight);

        VkExternalMemoryImageCreateInfo externalImageInfo{};
        externalImageInfo.sType = VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO;
        externalImageInfo.handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_FD_BIT;

        VkImageCreateInfo imageInfo{};
        imageInfo.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        imageInfo.pNext = &externalImageInfo;
        imageInfo.imageType = VK_IMAGE_TYPE_2D;
        imageInfo.format = interopFormat;
        imageInfo.extent.width = m_swapchainExtent.width;
        imageInfo.extent.height = m_swapchainExtent.height;
        imageInfo.extent.depth = 1;
        imageInfo.mipLevels = 1;
        imageInfo.arrayLayers = 1;
        imageInfo.samples = VK_SAMPLE_COUNT_1_BIT;
        // Use LINEAR tiling for the shared external-memory image. The OPAQUE_FD handle
        // shares raw bytes with no tiling metadata, and on Mesa the GL driver (radeonsi)
        // and the Vulkan driver (RADV) do not agree on an OPTIMAL swizzle for the same
        // memory -- importing an OPTIMAL image into GL yields a statically garbled /
        // sheared frame. LINEAR has a deterministic row-major layout both drivers honor.
        imageInfo.tiling = VK_IMAGE_TILING_LINEAR;
        imageInfo.usage = VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT;
        imageInfo.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        imageInfo.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;

        VkResult result = vkCreateImage(m_device, &imageInfo, nullptr, &interopImage);
        if (result != VK_SUCCESS)
        {
            disableGpuBridge(std::string("vkCreateImage(GPU bridge image) failed: ") + vkResultString(result));
            return true;
        }

        VkMemoryRequirements imageMemReq{};
        vkGetImageMemoryRequirements(m_device, interopImage, &imageMemReq);

        uint32_t imageMemoryType = findMemoryType(imageMemReq.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        if (imageMemoryType == std::numeric_limits<uint32_t>::max())
        {
            imageMemoryType = findMemoryType(imageMemReq.memoryTypeBits, 0);
        }
        if (imageMemoryType == std::numeric_limits<uint32_t>::max())
        {
            vkDestroyImage(m_device, interopImage, nullptr);
            disableGpuBridge("No compatible memory type for GPU bridge external-memory image.");
            return true;
        }

        VkExportMemoryAllocateInfo exportAllocInfo{};
        exportAllocInfo.sType = VK_STRUCTURE_TYPE_EXPORT_MEMORY_ALLOCATE_INFO;
        exportAllocInfo.handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_FD_BIT;

        VkMemoryDedicatedAllocateInfo dedicatedAllocInfo{};
        dedicatedAllocInfo.sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO;
        dedicatedAllocInfo.image = interopImage;
        dedicatedAllocInfo.buffer = VK_NULL_HANDLE;
        exportAllocInfo.pNext = &dedicatedAllocInfo;

        VkMemoryAllocateInfo imageAllocInfo{};
        imageAllocInfo.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        imageAllocInfo.pNext = &exportAllocInfo;
        imageAllocInfo.allocationSize = imageMemReq.size;
        imageAllocInfo.memoryTypeIndex = imageMemoryType;

        result = vkAllocateMemory(m_device, &imageAllocInfo, nullptr, &interopMemory);
        if (result != VK_SUCCESS)
        {
            vkDestroyImage(m_device, interopImage, nullptr);
            disableGpuBridge(std::string("vkAllocateMemory(GPU bridge image) failed: ") + vkResultString(result));
            return true;
        }

        result = vkBindImageMemory(m_device, interopImage, interopMemory, 0);
        if (result != VK_SUCCESS)
        {
            vkFreeMemory(m_device, interopMemory, nullptr);
            vkDestroyImage(m_device, interopImage, nullptr);
            disableGpuBridge(std::string("vkBindImageMemory(GPU bridge image) failed: ") + vkResultString(result));
            return true;
        }

        // glTexStorageMem2DEXT assumes a tightly-packed linear layout (rowPitch == width*bpp,
        // offset 0). If the driver padded the linear row pitch, the GL import would shear the
        // frame, so fall back to the CPU bridge rather than presenting corruption.
        {
            VkImageSubresource interopSubresource{};
            interopSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            interopSubresource.mipLevel = 0;
            interopSubresource.arrayLayer = 0;
            VkSubresourceLayout interopLayout{};
            vkGetImageSubresourceLayout(m_device, interopImage, &interopSubresource, &interopLayout);
            const VkDeviceSize expectedRowPitch =
                static_cast<VkDeviceSize>(m_swapchainExtent.width) * 4u; // both interop formats are 32-bit
            if (interopLayout.offset != 0 || interopLayout.rowPitch != expectedRowPitch)
            {
                std::ostringstream reason;
                reason << "Linear GPU bridge image is not tightly packed (offset=" << interopLayout.offset
                       << " rowPitch=" << interopLayout.rowPitch << " expected=" << expectedRowPitch << ").";
                vkFreeMemory(m_device, interopMemory, nullptr);
                vkDestroyImage(m_device, interopImage, nullptr);
                disableGpuBridge(reason.str());
                return true;
            }
        }

        PFN_vkGetMemoryFdKHR vkGetMemoryFd =
            reinterpret_cast<PFN_vkGetMemoryFdKHR>(vkGetDeviceProcAddr(m_device, "vkGetMemoryFdKHR"));
        if (!vkGetMemoryFd)
        {
            vkFreeMemory(m_device, interopMemory, nullptr);
            vkDestroyImage(m_device, interopImage, nullptr);
            disableGpuBridge("vkGetMemoryFdKHR is unavailable.");
            return true;
        }
        PFN_vkGetSemaphoreFdKHR vkGetSemaphoreFd =
            reinterpret_cast<PFN_vkGetSemaphoreFdKHR>(vkGetDeviceProcAddr(m_device, "vkGetSemaphoreFdKHR"));
        if (!vkGetSemaphoreFd)
        {
            vkFreeMemory(m_device, interopMemory, nullptr);
            vkDestroyImage(m_device, interopImage, nullptr);
            disableGpuBridge("vkGetSemaphoreFdKHR is unavailable.");
            return true;
        }

        VkMemoryGetFdInfoKHR getFdInfo{};
        getFdInfo.sType = VK_STRUCTURE_TYPE_MEMORY_GET_FD_INFO_KHR;
        getFdInfo.memory = interopMemory;
        getFdInfo.handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_FD_BIT;
        result = vkGetMemoryFd(m_device, &getFdInfo, &memoryFd);
        if (result != VK_SUCCESS || memoryFd < 0)
        {
            vkFreeMemory(m_device, interopMemory, nullptr);
            vkDestroyImage(m_device, interopImage, nullptr);
            disableGpuBridge(std::string("vkGetMemoryFdKHR failed: ") + vkResultString(result));
            return true;
        }

        while (glGetError() != GL_NO_ERROR)
        {
            // Clear stale GL errors before interop calls.
        }

        glFns.createMemoryObjects(1, &glMemoryObject);
        if (glMemoryObject == 0)
        {
            close(memoryFd);
            vkFreeMemory(m_device, interopMemory, nullptr);
            vkDestroyImage(m_device, interopImage, nullptr);
            disableGpuBridge("glCreateMemoryObjectsEXT returned 0.");
            return true;
        }

        glFns.importMemoryFd(glMemoryObject,
                             static_cast<GLuint64>(imageMemReq.size),
                             GL_HANDLE_TYPE_OPAQUE_FD_EXT,
                             memoryFd);
        if (glGetError() != GL_NO_ERROR)
        {
            if (memoryFd >= 0)
            {
                close(memoryFd);
                memoryFd = -1;
            }
            glFns.deleteMemoryObjects(1, &glMemoryObject);
            vkFreeMemory(m_device, interopMemory, nullptr);
            vkDestroyImage(m_device, interopImage, nullptr);
            disableGpuBridge("glImportMemoryFdEXT failed.");
            return true;
        }
        memoryFd = -1; // GL owns the file descriptor after successful import call.

        GLint previousTexture = 0;
        GLint previousFramebuffer = 0;
        glGetIntegerv(GL_TEXTURE_BINDING_2D, &previousTexture);
        glGetIntegerv(GL_FRAMEBUFFER_BINDING, &previousFramebuffer);

        glGenTextures(1, &glTexture);
        glBindTexture(GL_TEXTURE_2D, glTexture);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        // Match the Vulkan image's LINEAR tiling so radeonsi interprets the imported
        // RADV memory with the same row-major layout (default is OPTIMAL, which mismatches).
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_TILING_EXT, GL_LINEAR_TILING_EXT);
        glFns.texStorageMem2D(GL_TEXTURE_2D,
                              1,
                              interopGLInternalFormat,
                              static_cast<GLsizei>(m_swapchainExtent.width),
                              static_cast<GLsizei>(m_swapchainExtent.height),
                              glMemoryObject,
                              0);
        if (glGetError() != GL_NO_ERROR)
        {
            glDeleteTextures(1, &glTexture);
            glTexture = 0;
            glBindTexture(GL_TEXTURE_2D, previousTexture);
            glFns.deleteMemoryObjects(1, &glMemoryObject);
            vkFreeMemory(m_device, interopMemory, nullptr);
            vkDestroyImage(m_device, interopImage, nullptr);
            disableGpuBridge("glTexStorageMem2DEXT failed for imported memory object.");
            return true;
        }

        glGenFramebuffers(1, &glFramebuffer);
        glBindFramebuffer(GL_FRAMEBUFFER, glFramebuffer);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, glTexture, 0);
        const GLenum fboStatus = glCheckFramebufferStatus(GL_FRAMEBUFFER);
        glBindFramebuffer(GL_FRAMEBUFFER, previousFramebuffer);
        glBindTexture(GL_TEXTURE_2D, previousTexture);
        if (fboStatus != GL_FRAMEBUFFER_COMPLETE)
        {
            glDeleteFramebuffers(1, &glFramebuffer);
            glDeleteTextures(1, &glTexture);
            glFns.deleteMemoryObjects(1, &glMemoryObject);
            vkFreeMemory(m_device, interopMemory, nullptr);
            vkDestroyImage(m_device, interopImage, nullptr);
            disableGpuBridge("GPU bridge framebuffer is incomplete for imported memory texture.");
            return true;
        }

        auto destroyInteropResources = [&]()
        {
            if (glSemaphoreFns.deleteSemaphores)
            {
                for (GLuint semaphore : glReadySemaphores)
                {
                    if (semaphore != 0)
                        glSemaphoreFns.deleteSemaphores(1, &semaphore);
                }
                for (GLuint semaphore : glDoneSemaphores)
                {
                    if (semaphore != 0)
                        glSemaphoreFns.deleteSemaphores(1, &semaphore);
                }
            }
            for (VkSemaphore semaphore : vkReadySemaphores)
            {
                if (semaphore != VK_NULL_HANDLE)
                    vkDestroySemaphore(m_device, semaphore, nullptr);
            }
            for (VkSemaphore semaphore : vkDoneSemaphores)
            {
                if (semaphore != VK_NULL_HANDLE)
                    vkDestroySemaphore(m_device, semaphore, nullptr);
            }

            glDeleteFramebuffers(1, &glFramebuffer);
            glDeleteTextures(1, &glTexture);
            glFns.deleteMemoryObjects(1, &glMemoryObject);
            vkFreeMemory(m_device, interopMemory, nullptr);
            vkDestroyImage(m_device, interopImage, nullptr);
        };

        VkExportSemaphoreCreateInfo exportSemaphoreInfo{};
        exportSemaphoreInfo.sType = VK_STRUCTURE_TYPE_EXPORT_SEMAPHORE_CREATE_INFO;
        exportSemaphoreInfo.handleTypes = VK_EXTERNAL_SEMAPHORE_HANDLE_TYPE_OPAQUE_FD_BIT;

        VkSemaphoreCreateInfo semaphoreCreateInfo{};
        semaphoreCreateInfo.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
        semaphoreCreateInfo.pNext = &exportSemaphoreInfo;

        VkSemaphoreGetFdInfoKHR semaphoreFdInfo{};
        semaphoreFdInfo.sType = VK_STRUCTURE_TYPE_SEMAPHORE_GET_FD_INFO_KHR;
        semaphoreFdInfo.handleType = VK_EXTERNAL_SEMAPHORE_HANDLE_TYPE_OPAQUE_FD_BIT;

        while (glGetError() != GL_NO_ERROR)
        {
            // Clear stale GL errors before semaphore interop calls.
        }

        for (size_t i = 0; i < kFramesInFlight; ++i)
        {
            VkSemaphore vkReadySemaphore = VK_NULL_HANDLE;
            VkSemaphore vkDoneSemaphore = VK_NULL_HANDLE;
            GLuint glReadySemaphore = 0;
            GLuint glDoneSemaphore = 0;
            int readySemaphoreFd = -1;
            int doneSemaphoreFd = -1;

            result = vkCreateSemaphore(m_device, &semaphoreCreateInfo, nullptr, &vkReadySemaphore);
            if (result != VK_SUCCESS)
            {
                destroyInteropResources();
                disableGpuBridge(std::string("vkCreateSemaphore(GL->VK ready) failed: ") + vkResultString(result));
                return true;
            }
            vkReadySemaphores.push_back(vkReadySemaphore);

            result = vkCreateSemaphore(m_device, &semaphoreCreateInfo, nullptr, &vkDoneSemaphore);
            if (result != VK_SUCCESS)
            {
                destroyInteropResources();
                disableGpuBridge(std::string("vkCreateSemaphore(VK->GL done) failed: ") + vkResultString(result));
                return true;
            }
            vkDoneSemaphores.push_back(vkDoneSemaphore);

            semaphoreFdInfo.semaphore = vkReadySemaphore;
            result = vkGetSemaphoreFd(m_device, &semaphoreFdInfo, &readySemaphoreFd);
            if (result != VK_SUCCESS || readySemaphoreFd < 0)
            {
                destroyInteropResources();
                disableGpuBridge(std::string("vkGetSemaphoreFdKHR(GL->VK ready) failed: ") + vkResultString(result));
                return true;
            }

            semaphoreFdInfo.semaphore = vkDoneSemaphore;
            result = vkGetSemaphoreFd(m_device, &semaphoreFdInfo, &doneSemaphoreFd);
            if (result != VK_SUCCESS || doneSemaphoreFd < 0)
            {
                close(readySemaphoreFd);
                destroyInteropResources();
                disableGpuBridge(std::string("vkGetSemaphoreFdKHR(VK->GL done) failed: ") + vkResultString(result));
                return true;
            }

            glSemaphoreFns.genSemaphores(1, &glReadySemaphore);
            if (glReadySemaphore == 0)
            {
                close(readySemaphoreFd);
                close(doneSemaphoreFd);
                destroyInteropResources();
                disableGpuBridge("glGenSemaphoresEXT failed for GL->VK ready semaphore.");
                return true;
            }
            glSemaphoreFns.importSemaphoreFd(glReadySemaphore, GL_HANDLE_TYPE_OPAQUE_FD_EXT, readySemaphoreFd);
            if (glGetError() != GL_NO_ERROR)
            {
                if (readySemaphoreFd >= 0)
                    close(readySemaphoreFd);
                close(doneSemaphoreFd);
                glSemaphoreFns.deleteSemaphores(1, &glReadySemaphore);
                destroyInteropResources();
                disableGpuBridge("glImportSemaphoreFdEXT failed for GL->VK ready semaphore.");
                return true;
            }
            readySemaphoreFd = -1;
            glReadySemaphores.push_back(glReadySemaphore);

            glSemaphoreFns.genSemaphores(1, &glDoneSemaphore);
            if (glDoneSemaphore == 0)
            {
                close(doneSemaphoreFd);
                destroyInteropResources();
                disableGpuBridge("glGenSemaphoresEXT failed for VK->GL done semaphore.");
                return true;
            }
            glSemaphoreFns.importSemaphoreFd(glDoneSemaphore, GL_HANDLE_TYPE_OPAQUE_FD_EXT, doneSemaphoreFd);
            if (glGetError() != GL_NO_ERROR)
            {
                if (doneSemaphoreFd >= 0)
                    close(doneSemaphoreFd);
                glSemaphoreFns.deleteSemaphores(1, &glDoneSemaphore);
                destroyInteropResources();
                disableGpuBridge("glImportSemaphoreFdEXT failed for VK->GL done semaphore.");
                return true;
            }
            doneSemaphoreFd = -1;
            glDoneSemaphores.push_back(glDoneSemaphore);
        }

        m_gpuBridgeImage = interopImage;
        m_gpuBridgeImageMemory = interopMemory;
        m_gpuBridgeImageLayout = VK_IMAGE_LAYOUT_GENERAL;
        m_gpuBridgeImageFormat = interopFormat;
        m_gpuBridgeImageMemorySize = imageMemReq.size;
        m_gpuBridgeGLMemoryObject = glMemoryObject;
        m_gpuBridgeGLTexture = glTexture;
        m_gpuBridgeGLFramebuffer = glFramebuffer;
        m_gpuBridgeGLReadySemaphores = std::move(glReadySemaphores);
        m_gpuBridgeGLDoneSemaphores = std::move(glDoneSemaphores);
        m_gpuBridgeVkReadySemaphores = std::move(vkReadySemaphores);
        m_gpuBridgeVkDoneSemaphores = std::move(vkDoneSemaphores);
        m_gpuBridgeAwaitVkDoneOnGl.assign(kFramesInFlight, 0);
        m_gpuBridgeSemaphoreSyncActive = true;
        m_bridgeStatusLogged = false;
        m_gpuBridgeMechanism =
            "external-memory-fd + external-semaphore-fd (VK_KHR_external_memory_fd + VK_KHR_external_semaphore_fd + GL_EXT_memory_object_fd + GL_EXT_semaphore_fd)";

        std::ostringstream gpuBridgeLog;
        gpuBridgeLog << "GPU bridge selected: mechanism=" << m_gpuBridgeMechanism
                     << " reason=device+GL interop extensions available"
                     << " mode=" << m_gpuBridgeMode
                     << " sourceFormat=" << interopGLFormatName
                     << " bridgeFormat=" << formatName(m_gpuBridgeImageFormat)
                     << " destinationFormat=" << formatName(m_swapchainImageFormat)
                     << " transferOp=" << (m_gpuBridgeUsesBlit ? "vkCmdBlitImage" : "vkCmdCopyImage")
                     << " sync=external-semaphore-fd"
                     << " syncSlots=" << kFramesInFlight;
        logInfo(gpuBridgeLog.str());
        return true;
    }

    bool QTVulkanVideoDevice::prepareGpuBridgeFrameData(std::string& failureReason)
    {
        failureReason.clear();
        if (!m_bridgeSourceView || m_gpuBridgeGLFramebuffer == 0)
        {
            return false;
        }

        const double sourceDpr = m_bridgeSourceView->devicePixelRatio();
        const int readWidth =
            std::max(1, static_cast<int>(std::llround(static_cast<double>(m_bridgeSourceView->width()) * sourceDpr)));
        const int readHeight =
            std::max(1, static_cast<int>(std::llround(static_cast<double>(m_bridgeSourceView->height()) * sourceDpr)));
        const int dstWidth = static_cast<int>(m_swapchainExtent.width);
        const int dstHeight = static_cast<int>(m_swapchainExtent.height);
        if (readWidth < 1 || readHeight < 1 || dstWidth < 1 || dstHeight < 1)
        {
            return false;
        }

        m_bridgeSourceView->makeCurrent();
        QOpenGLContext* context = QOpenGLContext::currentContext();
        if (!context)
        {
            return false;
        }
        GLSemaphoreInteropFunctions glSemaphoreFns;
        if (m_gpuBridgeSemaphoreSyncActive)
        {
            std::string glSemaphoreReason;
            if (!resolveGLSemaphoreInteropFunctions(context, glSemaphoreFns, glSemaphoreReason))
            {
                failureReason = glSemaphoreReason;
                return false;
            }
        }

        GLint previousReadFramebuffer = 0;
        GLint previousDrawFramebuffer = 0;
        const GLboolean previousScissor = glIsEnabled(GL_SCISSOR_TEST);
        glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &previousReadFramebuffer);
        glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &previousDrawFramebuffer);

        if (previousScissor == GL_TRUE)
        {
            glDisable(GL_SCISSOR_TEST);
        }

        while (glGetError() != GL_NO_ERROR)
        {
            // Clear stale GL errors before frame blit.
        }
        const size_t syncIndex = static_cast<size_t>(m_currentFrame);
        if (m_gpuBridgeSemaphoreSyncActive &&
            (syncIndex >= m_gpuBridgeGLReadySemaphores.size() ||
             syncIndex >= m_gpuBridgeGLDoneSemaphores.size() ||
             syncIndex >= m_gpuBridgeAwaitVkDoneOnGl.size()))
        {
            failureReason = "GPU bridge semaphore slot is unavailable for the current frame.";
            return false;
        }
        if (m_gpuBridgeSemaphoreSyncActive &&
            syncIndex < m_gpuBridgeAwaitVkDoneOnGl.size() &&
            m_gpuBridgeAwaitVkDoneOnGl[syncIndex] != 0)
        {
            const GLuint textures[] = {m_gpuBridgeGLTexture};
            const GLenum layouts[] = {GL_LAYOUT_GENERAL_EXT};
            glSemaphoreFns.waitSemaphore(m_gpuBridgeGLDoneSemaphores[syncIndex], 0, nullptr, 1, textures, layouts);
            if (glGetError() != GL_NO_ERROR)
            {
                failureReason = "glWaitSemaphoreEXT failed for VK->GL bridge handoff.";
                return false;
            }
            m_gpuBridgeAwaitVkDoneOnGl[syncIndex] = 0;
        }

        // Match glReadPixels-style completion behavior before reading from the source framebuffer.
        glFinish();
        // Read from the device's active render target (the high-precision RGBA16F FBO when the
        // bridge is active, otherwise the widget default framebuffer). The blit into the 10-bit
        // GL_RGB10_A2 bridge texture performs the single, final 16F->10-bit quantization.
        const GLuint sourceFbo = m_bridgeSourceView->videoDevice()
                                     ? static_cast<GLuint>(m_bridgeSourceView->videoDevice()->fboID())
                                     : static_cast<GLuint>(m_bridgeSourceView->defaultFramebufferObject());
        glBindFramebuffer(GL_READ_FRAMEBUFFER, sourceFbo);

        // Optional precision diagnostic (enable with RV_BRIDGE_PRECISION_DIAG=1): read a middle
        // scanline of the source render target as float and count distinct 10-bit vs 8-bit levels.
        // A true >8-bit source yields many more distinct 10-bit levels than 8-bit (which caps at
        // ~256, every 10-bit value a multiple of 4). Logged for the first few frames only.
        static const bool s_precisionDiag = (getenv("RV_BRIDGE_PRECISION_DIAG") != nullptr);
        if (s_precisionDiag && m_bridgeFrameCounter < 3 && readWidth > 1 && readHeight > 1)
        {
            std::vector<float> scan(static_cast<size_t>(readWidth) * 4u, 0.0f);
            glReadPixels(0, readHeight / 2, readWidth, 1, GL_RGBA, GL_FLOAT, scan.data());
            std::set<int> levels10, levels8;
            float minR = 1e9f, maxR = -1e9f;
            for (int i = 0; i < readWidth; ++i)
            {
                const float r = scan[static_cast<size_t>(i) * 4u];
                minR = std::min(minR, r);
                maxR = std::max(maxR, r);
                const float c = std::max(0.0f, std::min(1.0f, r));
                levels10.insert(static_cast<int>(c * 1023.0f + 0.5f));
                levels8.insert(static_cast<int>(c * 255.0f + 0.5f));
            }
            std::ostringstream d;
            d << "PRECISION DIAG frame " << m_bridgeFrameCounter << ": sourceFbo=" << sourceFbo
              << " width=" << readWidth << " distinct10bit=" << levels10.size()
              << " distinct8bit=" << levels8.size() << " minR=" << minR << " maxR=" << maxR;
            logInfo(d.str());
        }

        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, m_gpuBridgeGLFramebuffer);
        glBlitFramebuffer(0, 0, readWidth, readHeight, 0, dstHeight, dstWidth, 0, GL_COLOR_BUFFER_BIT, GL_LINEAR);
        glBindFramebuffer(GL_READ_FRAMEBUFFER, static_cast<GLuint>(previousReadFramebuffer));
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, static_cast<GLuint>(previousDrawFramebuffer));
        if (previousScissor == GL_TRUE)
        {
            glEnable(GL_SCISSOR_TEST);
        }

        if (glGetError() != GL_NO_ERROR)
        {
            failureReason = "glBlitFramebuffer failed while copying into GPU bridge image.";
            return false;
        }

        glMemoryBarrier(GL_FRAMEBUFFER_BARRIER_BIT | GL_TEXTURE_UPDATE_BARRIER_BIT);
        if (m_gpuBridgeSemaphoreSyncActive)
        {
            const GLuint textures[] = {m_gpuBridgeGLTexture};
            const GLenum layouts[] = {GL_LAYOUT_GENERAL_EXT};
            glSemaphoreFns.signalSemaphore(m_gpuBridgeGLReadySemaphores[syncIndex], 0, nullptr, 1, textures, layouts);
            if (glGetError() != GL_NO_ERROR)
            {
                failureReason = "glSignalSemaphoreEXT failed for GL->VK bridge handoff.";
                return false;
            }
            glFlush();
        }
        else
        {
            glFinish();
        }

        m_bridgeSourceWidth = static_cast<uint32_t>(readWidth);
        m_bridgeSourceHeight = static_cast<uint32_t>(readHeight);

        std::ostringstream frameLog;
        frameLog << "Bridge frame " << m_bridgeFrameCounter
                 << ": source=" << m_bridgeSourceWidth << "x" << m_bridgeSourceHeight
                 << " sourceFormat=" << (m_gpuBridgeMode == "10-bit-copy" ? "GL_RGB10_A2" : "GL_RGBA8")
                 << " destination=" << m_swapchainExtent.width << "x" << m_swapchainExtent.height
                 << " bridgeFormat=" << formatName(m_gpuBridgeImageFormat)
                 << " swapchainFormat=" << formatName(m_swapchainImageFormat)
                 << " colorSpace=" << colorSpaceName(m_swapchainColorSpace)
                 << " syncSlot=" << syncIndex
                 << " packPath=gpu-interop mode=" << m_gpuBridgeMode
                 << " transferOp=" << (m_gpuBridgeUsesBlit ? "vkCmdBlitImage" : "vkCmdCopyImage");
        logInfo(frameLog.str());
        ++m_bridgeFrameCounter;

        return true;
    }

    bool QTVulkanVideoDevice::prepareBridgeFrameData()
    {
        if (!m_bridgeSourceView || m_bridgeStagingBuffer == VK_NULL_HANDLE || m_bridgeStagingMemory == VK_NULL_HANDLE)
            return false;

        const double sourceDpr = m_bridgeSourceView->devicePixelRatio();
        const int readWidth =
            std::max(1, static_cast<int>(std::llround(static_cast<double>(m_bridgeSourceView->width()) * sourceDpr)));
        const int readHeight =
            std::max(1, static_cast<int>(std::llround(static_cast<double>(m_bridgeSourceView->height()) * sourceDpr)));

        QImage sourceImage = m_bridgeSourceView->readPixels(0, 0, readWidth, readHeight);
        if (sourceImage.isNull() || sourceImage.width() < 1 || sourceImage.height() < 1)
            return false;

        m_bridgeSourceWidth = static_cast<uint32_t>(sourceImage.width());
        m_bridgeSourceHeight = static_cast<uint32_t>(sourceImage.height());

        const int dstWidth = static_cast<int>(m_swapchainExtent.width);
        const int dstHeight = static_cast<int>(m_swapchainExtent.height);
        if (dstWidth < 1 || dstHeight < 1)
            return false;

        QImage uploadImage = sourceImage;
        if (uploadImage.width() != dstWidth || uploadImage.height() != dstHeight)
        {
            uploadImage =
                uploadImage.scaled(dstWidth, dstHeight, Qt::IgnoreAspectRatio, Qt::SmoothTransformation);
        }
        uploadImage = uploadImage.convertToFormat(QImage::Format_RGBA8888);

        const size_t pixelCount =
            static_cast<size_t>(m_swapchainExtent.width) * static_cast<size_t>(m_swapchainExtent.height);
        const size_t packedSize = pixelCount * sizeof(uint32_t);
        m_bridgePackedFrame.resize(packedSize);

        const bool is10BitFormat = m_swapchainImageFormat == VK_FORMAT_A2B10G10R10_UNORM_PACK32 ||
                                   m_swapchainImageFormat == VK_FORMAT_A2R10G10B10_UNORM_PACK32;

        switch (m_swapchainImageFormat)
        {
        case VK_FORMAT_A2B10G10R10_UNORM_PACK32:
            m_bridgePackPath = "10-bit-A2B10G10R10";
            break;
        case VK_FORMAT_A2R10G10B10_UNORM_PACK32:
            m_bridgePackPath = "10-bit-A2R10G10B10";
            break;
        case VK_FORMAT_B8G8R8A8_UNORM:
        case VK_FORMAT_B8G8R8A8_SRGB:
            m_bridgePackPath = "8-bit-B8G8R8A8-fallback";
            break;
        case VK_FORMAT_R8G8B8A8_UNORM:
        case VK_FORMAT_R8G8B8A8_SRGB:
            m_bridgePackPath = "8-bit-R8G8B8A8-fallback";
            break;
        default:
            logWarn("Unsupported swapchain format for bridge upload path: " + formatName(m_swapchainImageFormat));
            return false;
        }

        for (uint32_t y = 0; y < m_swapchainExtent.height; ++y)
        {
            const uint32_t sourceY = m_swapchainExtent.height - 1u - y;
            const uint8_t* srcRow = uploadImage.constScanLine(static_cast<int>(sourceY));
            uint8_t* dstRow =
                m_bridgePackedFrame.data() + (static_cast<size_t>(y) * static_cast<size_t>(m_swapchainExtent.width) * 4u);

            for (uint32_t x = 0; x < m_swapchainExtent.width; ++x)
            {
                const uint8_t* srcPixel = srcRow + static_cast<size_t>(x) * 4u;
                const uint8_t r = srcPixel[0];
                const uint8_t g = srcPixel[1];
                const uint8_t b = srcPixel[2];
                const uint8_t a = srcPixel[3];

                if (is10BitFormat)
                {
                    const uint32_t r10 = quantize10(r);
                    const uint32_t g10 = quantize10(g);
                    const uint32_t b10 = quantize10(b);
                    const uint32_t a2 = quantize2(a);

                    uint32_t packed = 0;
                    if (m_swapchainImageFormat == VK_FORMAT_A2R10G10B10_UNORM_PACK32)
                    {
                        packed = (a2 << 30) | (r10 << 20) | (g10 << 10) | b10;
                    }
                    else
                    {
                        packed = (a2 << 30) | (b10 << 20) | (g10 << 10) | r10;
                    }

                    std::memcpy(dstRow + static_cast<size_t>(x) * 4u, &packed, sizeof(uint32_t));
                }
                else if (m_swapchainImageFormat == VK_FORMAT_B8G8R8A8_UNORM ||
                         m_swapchainImageFormat == VK_FORMAT_B8G8R8A8_SRGB)
                {
                    uint8_t* dstPixel = dstRow + static_cast<size_t>(x) * 4u;
                    dstPixel[0] = b;
                    dstPixel[1] = g;
                    dstPixel[2] = r;
                    dstPixel[3] = a;
                }
                else
                {
                    uint8_t* dstPixel = dstRow + static_cast<size_t>(x) * 4u;
                    dstPixel[0] = r;
                    dstPixel[1] = g;
                    dstPixel[2] = b;
                    dstPixel[3] = a;
                }
            }
        }

        void* mapped = nullptr;
        const VkResult mapResult =
            vkMapMemory(m_device, m_bridgeStagingMemory, 0, static_cast<VkDeviceSize>(m_bridgePackedFrame.size()), 0, &mapped);
        if (mapResult != VK_SUCCESS || !mapped)
        {
            logError(std::string("vkMapMemory(bridge staging) failed: ") + vkResultString(mapResult));
            return false;
        }

        std::memcpy(mapped, m_bridgePackedFrame.data(), m_bridgePackedFrame.size());
        vkUnmapMemory(m_device, m_bridgeStagingMemory);

        std::ostringstream frameLog;
        frameLog << "Bridge frame " << m_bridgeFrameCounter
                 << ": source=" << m_bridgeSourceWidth << "x" << m_bridgeSourceHeight
                 << " pixelFormat=GL_RGBA8 destination=" << m_swapchainExtent.width << "x" << m_swapchainExtent.height
                 << " swapchainFormat=" << formatName(m_swapchainImageFormat)
                 << " colorSpace=" << colorSpaceName(m_swapchainColorSpace)
                 << " packPath=" << m_bridgePackPath;
        logInfo(frameLog.str());
        ++m_bridgeFrameCounter;

        return true;
    }

    bool QTVulkanVideoDevice::recreateSwapchain()
    {
        if (!m_initialized || !m_window || m_window->width() < 1 || m_window->height() < 1)
            return false;

        vkDeviceWaitIdle(m_device);
        cleanupSwapchain();

        if (!createSwapchain())
            return false;
        if (!createImageViews())
            return false;
        if (!createRenderPass())
            return false;
        if (!createFramebuffers())
            return false;
        if (!createCommandBuffers())
            return false;
        if (!ensureBridgeResources())
        {
            logWarn("Failed to recreate bridge resources after swapchain resize; using clear-only fallback.");
            m_bridgeCopySupported = false;
            destroyBridgeResources();
        }

        m_imagesInFlight.assign(m_swapchainImages.size(), VK_NULL_HANDLE);
        m_swapchainDirty = false;
        m_bridgeStatusLogged = false;
        m_bridgeActivationLogged = false;
        m_gpuBridgeActivationLogged = false;
        m_bridgeUnavailableLogged = false;
        return true;
    }

    bool QTVulkanVideoDevice::recordCommandBuffer(VkCommandBuffer commandBuffer,
                                                  uint32_t imageIndex,
                                                  bool useBridgePath,
                                                  bool useGpuBridgePath)
    {
        VkCommandBufferBeginInfo beginInfo{};
        beginInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
        beginInfo.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;

        VkResult result = vkBeginCommandBuffer(commandBuffer, &beginInfo);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkBeginCommandBuffer failed: ") + vkResultString(result));
            return false;
        }

        if (useBridgePath && imageIndex < m_swapchainImages.size() && imageIndex < m_swapchainImageLayouts.size())
        {
            const VkImage bridgeSourceImage = useGpuBridgePath ? m_gpuBridgeImage : m_bridgeImage;
            VkImageLayout& bridgeSourceLayout = useGpuBridgePath ? m_gpuBridgeImageLayout : m_bridgeImageLayout;

            if (useGpuBridgePath)
            {
                VkImageMemoryBarrier bridgeToSrc{};
                bridgeToSrc.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
                bridgeToSrc.oldLayout = bridgeSourceLayout;
                bridgeToSrc.newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
                bridgeToSrc.srcQueueFamilyIndex = VK_QUEUE_FAMILY_EXTERNAL;
                bridgeToSrc.dstQueueFamilyIndex = m_graphicsQueueFamily;
                bridgeToSrc.image = bridgeSourceImage;
                bridgeToSrc.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
                bridgeToSrc.subresourceRange.baseMipLevel = 0;
                bridgeToSrc.subresourceRange.levelCount = 1;
                bridgeToSrc.subresourceRange.baseArrayLayer = 0;
                bridgeToSrc.subresourceRange.layerCount = 1;
                bridgeToSrc.srcAccessMask = 0;
                bridgeToSrc.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;

                vkCmdPipelineBarrier(commandBuffer,
                                     VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                                     VK_PIPELINE_STAGE_TRANSFER_BIT,
                                     0,
                                     0,
                                     nullptr,
                                     0,
                                     nullptr,
                                     1,
                                     &bridgeToSrc);

                bridgeSourceLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
            }
            else
            {
                VkImageMemoryBarrier bridgeToDst{};
                bridgeToDst.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
                bridgeToDst.oldLayout = bridgeSourceLayout;
                bridgeToDst.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
                bridgeToDst.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
                bridgeToDst.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
                bridgeToDst.image = bridgeSourceImage;
                bridgeToDst.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
                bridgeToDst.subresourceRange.baseMipLevel = 0;
                bridgeToDst.subresourceRange.levelCount = 1;
                bridgeToDst.subresourceRange.baseArrayLayer = 0;
                bridgeToDst.subresourceRange.layerCount = 1;
                bridgeToDst.srcAccessMask = (bridgeSourceLayout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL)
                                                ? VK_ACCESS_TRANSFER_READ_BIT
                                                : 0;
                bridgeToDst.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;

                const VkPipelineStageFlags bridgeSrcStage =
                    (bridgeSourceLayout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL)
                        ? VK_PIPELINE_STAGE_TRANSFER_BIT
                        : VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT;

                vkCmdPipelineBarrier(commandBuffer,
                                     bridgeSrcStage,
                                     VK_PIPELINE_STAGE_TRANSFER_BIT,
                                     0,
                                     0,
                                     nullptr,
                                     0,
                                     nullptr,
                                     1,
                                     &bridgeToDst);

                bridgeSourceLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;

                VkBufferImageCopy uploadRegion{};
                uploadRegion.bufferOffset = 0;
                uploadRegion.bufferRowLength = 0;
                uploadRegion.bufferImageHeight = 0;
                uploadRegion.imageSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
                uploadRegion.imageSubresource.mipLevel = 0;
                uploadRegion.imageSubresource.baseArrayLayer = 0;
                uploadRegion.imageSubresource.layerCount = 1;
                uploadRegion.imageOffset = {0, 0, 0};
                uploadRegion.imageExtent = {m_swapchainExtent.width, m_swapchainExtent.height, 1};

                vkCmdCopyBufferToImage(commandBuffer,
                                       m_bridgeStagingBuffer,
                                       bridgeSourceImage,
                                       VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                                       1,
                                       &uploadRegion);

                VkImageMemoryBarrier bridgeToSrc{};
                bridgeToSrc.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
                bridgeToSrc.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
                bridgeToSrc.newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
                bridgeToSrc.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
                bridgeToSrc.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
                bridgeToSrc.image = bridgeSourceImage;
                bridgeToSrc.subresourceRange = bridgeToDst.subresourceRange;
                bridgeToSrc.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
                bridgeToSrc.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;

                vkCmdPipelineBarrier(commandBuffer,
                                     VK_PIPELINE_STAGE_TRANSFER_BIT,
                                     VK_PIPELINE_STAGE_TRANSFER_BIT,
                                     0,
                                     0,
                                     nullptr,
                                     0,
                                     nullptr,
                                     1,
                                     &bridgeToSrc);

                bridgeSourceLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
            }

            const VkImageLayout oldSwapchainLayout = m_swapchainImageLayouts[imageIndex];
            VkImageMemoryBarrier swapchainToDst{};
            swapchainToDst.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
            swapchainToDst.oldLayout = oldSwapchainLayout;
            swapchainToDst.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
            swapchainToDst.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            swapchainToDst.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            swapchainToDst.image = m_swapchainImages[imageIndex];
            swapchainToDst.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            swapchainToDst.subresourceRange.baseMipLevel = 0;
            swapchainToDst.subresourceRange.levelCount = 1;
            swapchainToDst.subresourceRange.baseArrayLayer = 0;
            swapchainToDst.subresourceRange.layerCount = 1;
            swapchainToDst.srcAccessMask = 0;
            swapchainToDst.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;

            const VkPipelineStageFlags swapchainSrcStage =
                (oldSwapchainLayout == VK_IMAGE_LAYOUT_UNDEFINED)
                    ? VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT
                    : VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT;

            vkCmdPipelineBarrier(commandBuffer,
                                 swapchainSrcStage,
                                 VK_PIPELINE_STAGE_TRANSFER_BIT,
                                 0,
                                 0,
                                 nullptr,
                                 0,
                                 nullptr,
                                 1,
                                 &swapchainToDst);

            VkImageCopy copyRegion{};
            copyRegion.srcSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            copyRegion.srcSubresource.mipLevel = 0;
            copyRegion.srcSubresource.baseArrayLayer = 0;
            copyRegion.srcSubresource.layerCount = 1;
            copyRegion.srcOffset = {0, 0, 0};
            copyRegion.dstSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            copyRegion.dstSubresource.mipLevel = 0;
            copyRegion.dstSubresource.baseArrayLayer = 0;
            copyRegion.dstSubresource.layerCount = 1;
            copyRegion.dstOffset = {0, 0, 0};
            copyRegion.extent = {m_swapchainExtent.width, m_swapchainExtent.height, 1};

            if (useGpuBridgePath && m_gpuBridgeUsesBlit)
            {
                VkImageBlit blitRegion{};
                blitRegion.srcSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
                blitRegion.srcSubresource.mipLevel = 0;
                blitRegion.srcSubresource.baseArrayLayer = 0;
                blitRegion.srcSubresource.layerCount = 1;
                blitRegion.srcOffsets[0] = {0, 0, 0};
                blitRegion.srcOffsets[1] = {
                    static_cast<int32_t>(m_swapchainExtent.width),
                    static_cast<int32_t>(m_swapchainExtent.height),
                    1};
                blitRegion.dstSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
                blitRegion.dstSubresource.mipLevel = 0;
                blitRegion.dstSubresource.baseArrayLayer = 0;
                blitRegion.dstSubresource.layerCount = 1;
                blitRegion.dstOffsets[0] = {0, 0, 0};
                blitRegion.dstOffsets[1] = {
                    static_cast<int32_t>(m_swapchainExtent.width),
                    static_cast<int32_t>(m_swapchainExtent.height),
                    1};

                vkCmdBlitImage(commandBuffer,
                               bridgeSourceImage,
                               VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                               m_swapchainImages[imageIndex],
                               VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                               1,
                               &blitRegion,
                               VK_FILTER_LINEAR);
            }
            else
            {
                vkCmdCopyImage(commandBuffer,
                               bridgeSourceImage,
                               VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                               m_swapchainImages[imageIndex],
                               VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                               1,
                               &copyRegion);
            }

            VkImageMemoryBarrier swapchainToPresent{};
            swapchainToPresent.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
            swapchainToPresent.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
            swapchainToPresent.newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
            swapchainToPresent.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            swapchainToPresent.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            swapchainToPresent.image = m_swapchainImages[imageIndex];
            swapchainToPresent.subresourceRange = swapchainToDst.subresourceRange;
            swapchainToPresent.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
            swapchainToPresent.dstAccessMask = 0;

            vkCmdPipelineBarrier(commandBuffer,
                                 VK_PIPELINE_STAGE_TRANSFER_BIT,
                                 VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,
                                 0,
                                 0,
                                 nullptr,
                                 0,
                                 nullptr,
                                 1,
                                 &swapchainToPresent);

            if (useGpuBridgePath)
            {
                VkImageMemoryBarrier bridgeReleaseToExternal{};
                bridgeReleaseToExternal.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
                bridgeReleaseToExternal.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
                bridgeReleaseToExternal.newLayout = VK_IMAGE_LAYOUT_GENERAL;
                bridgeReleaseToExternal.srcQueueFamilyIndex = m_graphicsQueueFamily;
                bridgeReleaseToExternal.dstQueueFamilyIndex = VK_QUEUE_FAMILY_EXTERNAL;
                bridgeReleaseToExternal.image = bridgeSourceImage;
                bridgeReleaseToExternal.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
                bridgeReleaseToExternal.subresourceRange.baseMipLevel = 0;
                bridgeReleaseToExternal.subresourceRange.levelCount = 1;
                bridgeReleaseToExternal.subresourceRange.baseArrayLayer = 0;
                bridgeReleaseToExternal.subresourceRange.layerCount = 1;
                bridgeReleaseToExternal.srcAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
                bridgeReleaseToExternal.dstAccessMask = 0;

                vkCmdPipelineBarrier(commandBuffer,
                                     VK_PIPELINE_STAGE_TRANSFER_BIT,
                                     VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,
                                     0,
                                     0,
                                     nullptr,
                                     0,
                                     nullptr,
                                     1,
                                     &bridgeReleaseToExternal);
                bridgeSourceLayout = VK_IMAGE_LAYOUT_GENERAL;
            }

            m_swapchainImageLayouts[imageIndex] = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
        }
        else
        {
            const float phase = static_cast<float>((m_frameCounter % 600ull) / 600.0);
            VkClearValue clearColor{};
            clearColor.color.float32[0] = 0.15f + 0.70f * phase;
            clearColor.color.float32[1] = 0.15f + 0.70f * (1.0f - phase);
            clearColor.color.float32[2] = 0.25f;
            clearColor.color.float32[3] = 1.0f;

            VkRenderPassBeginInfo renderPassInfo{};
            renderPassInfo.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
            renderPassInfo.renderPass = m_renderPass;
            renderPassInfo.framebuffer = m_swapchainFramebuffers[imageIndex];
            renderPassInfo.renderArea.offset = {0, 0};
            renderPassInfo.renderArea.extent = m_swapchainExtent;
            renderPassInfo.clearValueCount = 1;
            renderPassInfo.pClearValues = &clearColor;

            vkCmdBeginRenderPass(commandBuffer, &renderPassInfo, VK_SUBPASS_CONTENTS_INLINE);
            vkCmdEndRenderPass(commandBuffer);
            if (imageIndex < m_swapchainImageLayouts.size())
                m_swapchainImageLayouts[imageIndex] = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
        }

        result = vkEndCommandBuffer(commandBuffer);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkEndCommandBuffer failed: ") + vkResultString(result));
            return false;
        }

        return true;
    }

    void QTVulkanVideoDevice::destroyGpuBridgeResources()
    {
        if ((m_gpuBridgeGLFramebuffer != 0 || m_gpuBridgeGLTexture != 0 || m_gpuBridgeGLMemoryObject != 0) &&
            m_bridgeSourceView)
        {
            m_bridgeSourceView->makeCurrent();
            QOpenGLContext* context = QOpenGLContext::currentContext();
            if (context)
            {
                GLInteropFunctions glFns;
                GLSemaphoreInteropFunctions glSemaphoreFns;
                std::string reason;
                std::string semaphoreReason;
                resolveGLInteropFunctions(context, glFns, reason);
                resolveGLSemaphoreInteropFunctions(context, glSemaphoreFns, semaphoreReason);

                if (glSemaphoreFns.deleteSemaphores)
                {
                    for (unsigned int semaphore : m_gpuBridgeGLReadySemaphores)
                    {
                        if (semaphore != 0)
                            glSemaphoreFns.deleteSemaphores(1, &semaphore);
                    }
                    for (unsigned int semaphore : m_gpuBridgeGLDoneSemaphores)
                    {
                        if (semaphore != 0)
                            glSemaphoreFns.deleteSemaphores(1, &semaphore);
                    }
                }

                if (m_gpuBridgeGLFramebuffer != 0)
                {
                    glDeleteFramebuffers(1, &m_gpuBridgeGLFramebuffer);
                    m_gpuBridgeGLFramebuffer = 0;
                }
                if (m_gpuBridgeGLTexture != 0)
                {
                    glDeleteTextures(1, &m_gpuBridgeGLTexture);
                    m_gpuBridgeGLTexture = 0;
                }
                if (m_gpuBridgeGLMemoryObject != 0 && glFns.deleteMemoryObjects)
                {
                    glFns.deleteMemoryObjects(1, &m_gpuBridgeGLMemoryObject);
                    m_gpuBridgeGLMemoryObject = 0;
                }
            }
        }

        if (m_device != VK_NULL_HANDLE)
        {
            if (m_gpuBridgeImage != VK_NULL_HANDLE)
            {
                vkDestroyImage(m_device, m_gpuBridgeImage, nullptr);
                m_gpuBridgeImage = VK_NULL_HANDLE;
            }

            if (m_gpuBridgeImageMemory != VK_NULL_HANDLE)
            {
                vkFreeMemory(m_device, m_gpuBridgeImageMemory, nullptr);
                m_gpuBridgeImageMemory = VK_NULL_HANDLE;
            }
            for (VkSemaphore semaphore : m_gpuBridgeVkReadySemaphores)
            {
                if (semaphore != VK_NULL_HANDLE)
                    vkDestroySemaphore(m_device, semaphore, nullptr);
            }
            for (VkSemaphore semaphore : m_gpuBridgeVkDoneSemaphores)
            {
                if (semaphore != VK_NULL_HANDLE)
                    vkDestroySemaphore(m_device, semaphore, nullptr);
            }
        }

        m_gpuBridgeGLMemoryObject = 0;
        m_gpuBridgeGLTexture = 0;
        m_gpuBridgeGLFramebuffer = 0;
        m_gpuBridgeGLReadySemaphores.clear();
        m_gpuBridgeGLDoneSemaphores.clear();
        m_gpuBridgeVkReadySemaphores.clear();
        m_gpuBridgeVkDoneSemaphores.clear();
        m_gpuBridgeAwaitVkDoneOnGl.clear();
        m_gpuBridgeImageLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        m_gpuBridgeImageFormat = VK_FORMAT_UNDEFINED;
        m_gpuBridgeImageMemorySize = 0;
        m_gpuBridgeMechanism.clear();
        m_gpuBridgeMode.clear();
        m_gpuBridgeUsesBlit = false;
        m_gpuBridgeSemaphoreSyncActive = false;
        m_gpuBridgeActivationLogged = false;
    }

    void QTVulkanVideoDevice::destroyBridgeResources()
    {
        destroyGpuBridgeResources();

        if (m_device == VK_NULL_HANDLE)
            return;

        if (m_bridgeImage != VK_NULL_HANDLE)
        {
            vkDestroyImage(m_device, m_bridgeImage, nullptr);
            m_bridgeImage = VK_NULL_HANDLE;
        }

        if (m_bridgeImageMemory != VK_NULL_HANDLE)
        {
            vkFreeMemory(m_device, m_bridgeImageMemory, nullptr);
            m_bridgeImageMemory = VK_NULL_HANDLE;
        }

        if (m_bridgeStagingBuffer != VK_NULL_HANDLE)
        {
            vkDestroyBuffer(m_device, m_bridgeStagingBuffer, nullptr);
            m_bridgeStagingBuffer = VK_NULL_HANDLE;
        }

        if (m_bridgeStagingMemory != VK_NULL_HANDLE)
        {
            vkFreeMemory(m_device, m_bridgeStagingMemory, nullptr);
            m_bridgeStagingMemory = VK_NULL_HANDLE;
        }

        m_bridgeStagingCapacity = 0;
        m_bridgeImageLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    }

    void QTVulkanVideoDevice::cleanupSwapchain()
    {
        if (m_device == VK_NULL_HANDLE)
            return;

        destroyBridgeResources();

        if (!m_commandBuffers.empty() && m_commandPool != VK_NULL_HANDLE)
        {
            vkFreeCommandBuffers(
                m_device,
                m_commandPool,
                static_cast<uint32_t>(m_commandBuffers.size()),
                m_commandBuffers.data());
            m_commandBuffers.clear();
        }

        for (VkFramebuffer framebuffer : m_swapchainFramebuffers)
        {
            if (framebuffer != VK_NULL_HANDLE)
                vkDestroyFramebuffer(m_device, framebuffer, nullptr);
        }
        m_swapchainFramebuffers.clear();

        if (m_renderPass != VK_NULL_HANDLE)
        {
            vkDestroyRenderPass(m_device, m_renderPass, nullptr);
            m_renderPass = VK_NULL_HANDLE;
        }

        for (VkImageView imageView : m_swapchainImageViews)
        {
            if (imageView != VK_NULL_HANDLE)
                vkDestroyImageView(m_device, imageView, nullptr);
        }
        m_swapchainImageViews.clear();

        if (m_swapchain != VK_NULL_HANDLE)
        {
            vkDestroySwapchainKHR(m_device, m_swapchain, nullptr);
            m_swapchain = VK_NULL_HANDLE;
        }

        m_swapchainImages.clear();
        m_swapchainImageLayouts.clear();
        m_imagesInFlight.clear();
    }

    void QTVulkanVideoDevice::cleanup()
    {
        if (m_device != VK_NULL_HANDLE)
            vkDeviceWaitIdle(m_device);

        if (m_device != VK_NULL_HANDLE)
        {
            for (VkSemaphore semaphore : m_imageAvailableSemaphores)
            {
                if (semaphore != VK_NULL_HANDLE)
                    vkDestroySemaphore(m_device, semaphore, nullptr);
            }
            m_imageAvailableSemaphores.clear();

            for (VkSemaphore semaphore : m_renderFinishedSemaphores)
            {
                if (semaphore != VK_NULL_HANDLE)
                    vkDestroySemaphore(m_device, semaphore, nullptr);
            }
            m_renderFinishedSemaphores.clear();

            for (VkFence fence : m_inFlightFences)
            {
                if (fence != VK_NULL_HANDLE)
                    vkDestroyFence(m_device, fence, nullptr);
            }
            m_inFlightFences.clear();

            cleanupSwapchain();

            if (m_commandPool != VK_NULL_HANDLE)
            {
                vkDestroyCommandPool(m_device, m_commandPool, nullptr);
                m_commandPool = VK_NULL_HANDLE;
            }

            vkDestroyDevice(m_device, nullptr);
            m_device = VK_NULL_HANDLE;
        }

        if (m_surface != VK_NULL_HANDLE && m_instance != VK_NULL_HANDLE)
        {
            vkDestroySurfaceKHR(m_instance, m_surface, nullptr);
            m_surface = VK_NULL_HANDLE;
        }

        if (m_instance != VK_NULL_HANDLE)
        {
            vkDestroyInstance(m_instance, nullptr);
            m_instance = VK_NULL_HANDLE;
        }

        if (m_x11Display)
        {
            XCloseDisplay(m_x11Display);
            m_x11Display = nullptr;
        }

        m_window = nullptr;
        m_physicalDevice = VK_NULL_HANDLE;
        m_graphicsQueue = VK_NULL_HANDLE;
        m_presentQueue = VK_NULL_HANDLE;
        m_graphicsQueueFamily = VK_QUEUE_FAMILY_IGNORED;
        m_presentQueueFamily = VK_QUEUE_FAMILY_IGNORED;
        m_swapchainImageFormat = VK_FORMAT_UNDEFINED;
        m_swapchainExtent = {0, 0};
        m_swapchainColorSpace = VK_COLOR_SPACE_SRGB_NONLINEAR_KHR;
        m_bridgeCopySupported = false;
        m_bridgeUnavailableLogged = false;
        m_bridgeActivationLogged = false;
        m_gpuBridgeActivationLogged = false;
        m_bridgeStatusLogged = false;
        m_gpuBridgeRuntimeDisabled = false;
        m_gpuBridgeDisableReason.clear();
        m_vulkanExternalMemorySupported = false;
        m_vulkanExternalMemoryFdSupported = false;
        m_vulkanExternalSemaphoreSupported = false;
        m_vulkanExternalSemaphoreFdSupported = false;
        m_gpuBridgeBlitSupported = false;
        m_gpuBridgeUsesBlit = false;
        m_gpuBridgeSemaphoreSyncActive = false;
        m_isRadvDevice = false;
        m_bridgeFrameCounter = 0;
        m_bridgeSourceWidth = 0;
        m_bridgeSourceHeight = 0;
        m_bridgePackPath.clear();
        m_gpuBridgeMechanism.clear();
        m_gpuBridgeMode.clear();
        m_gpuBridgeGLReadySemaphores.clear();
        m_gpuBridgeGLDoneSemaphores.clear();
        m_gpuBridgeVkReadySemaphores.clear();
        m_gpuBridgeVkDoneSemaphores.clear();
        m_gpuBridgeAwaitVkDoneOnGl.clear();
        m_bridgePackedFrame.clear();
        m_currentFrame = 0;
        m_frameCounter = 0;
        m_swapchainDirty = false;
        m_initialized = false;
    }

    std::unique_ptr<QTVulkanVideoDevice> makeNoOpQTVulkanVideoDevice()
    {
        return std::make_unique<QTVulkanVideoDevice>();
    }
} // namespace Rv

#endif // PLATFORM_LINUX
