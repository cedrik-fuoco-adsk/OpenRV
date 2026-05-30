//
// Copyright (C) 2026 Autodesk, Inc. All Rights Reserved.
//
// SPDX-License-Identifier: Apache-2.0
//

#ifdef PLATFORM_LINUX

#include <RvCommon/QTVulkanVideoDevice.h>

#include <RvCommon/GLView.h>

#include <QGuiApplication>
#include <QImage>
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
#include <vector>

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
        m_bridgeSourceView = sourceView;
        m_bridgeUnavailableLogged = false;
        m_bridgeActivationLogged = false;
        m_bridgeStatusLogged = false;
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
                         << " swapchainExtent=" << m_swapchainExtent.width << "x" << m_swapchainExtent.height;
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
        if (m_bridgeCopySupported && m_bridgeSourceView && ensureBridgeResources())
        {
            useBridgePath = prepareBridgeFrameData();
            if (useBridgePath)
            {
                if (!m_bridgeActivationLogged)
                {
                    logInfo("Bridge path active: GL readback -> CPU pack -> Vulkan staging upload -> swapchain copy");
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

        if (!recordCommandBuffer(m_commandBuffers[imageIndex], imageIndex, useBridgePath))
            return;

        const VkPipelineStageFlags waitStages[] = {VK_PIPELINE_STAGE_ALL_COMMANDS_BIT};
        const VkSemaphore waitSemaphores[] = {m_imageAvailableSemaphores[m_currentFrame]};
        const VkSemaphore signalSemaphores[] = {m_renderFinishedSemaphores[m_currentFrame]};

        VkSubmitInfo submitInfo{};
        submitInfo.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
        submitInfo.waitSemaphoreCount = 1;
        submitInfo.pWaitSemaphores = waitSemaphores;
        submitInfo.pWaitDstStageMask = waitStages;
        submitInfo.commandBufferCount = 1;
        submitInfo.pCommandBuffers = &m_commandBuffers[imageIndex];
        submitInfo.signalSemaphoreCount = 1;
        submitInfo.pSignalSemaphores = signalSemaphores;

        result = vkQueueSubmit(m_graphicsQueue, 1, &submitInfo, currentFence);
        if (result != VK_SUCCESS)
        {
            logError(std::string("vkQueueSubmit failed: ") + vkResultString(result));
            return;
        }

        VkPresentInfoKHR presentInfo{};
        presentInfo.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
        presentInfo.waitSemaphoreCount = 1;
        presentInfo.pWaitSemaphores = signalSemaphores;
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
            for (const VkExtensionProperties& extension : availableExtensions)
            {
                if (std::strcmp(extension.extensionName, VK_KHR_SWAPCHAIN_EXTENSION_NAME) == 0)
                {
                    hasSwapchainExtension = true;
                    break;
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

            VkPhysicalDeviceProperties properties{};
            vkGetPhysicalDeviceProperties(m_physicalDevice, &properties);
            logInfo("Selected Vulkan physical device: " + std::string(properties.deviceName));
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

        const std::vector<const char*> deviceExtensions = {
            VK_KHR_SWAPCHAIN_EXTENSION_NAME
        };

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
            return true;

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
        os << "Bridge resources ready: uploadExtent=" << m_swapchainExtent.width << "x" << m_swapchainExtent.height
           << " dstFormat=" << formatName(m_swapchainImageFormat)
           << " colorSpace=" << colorSpaceName(m_swapchainColorSpace);
        logInfo(os.str());
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
        return true;
    }

    bool QTVulkanVideoDevice::recordCommandBuffer(VkCommandBuffer commandBuffer,
                                                  uint32_t imageIndex,
                                                  bool useBridgePath)
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
            VkImageMemoryBarrier bridgeToDst{};
            bridgeToDst.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
            bridgeToDst.oldLayout = m_bridgeImageLayout;
            bridgeToDst.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
            bridgeToDst.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            bridgeToDst.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            bridgeToDst.image = m_bridgeImage;
            bridgeToDst.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            bridgeToDst.subresourceRange.baseMipLevel = 0;
            bridgeToDst.subresourceRange.levelCount = 1;
            bridgeToDst.subresourceRange.baseArrayLayer = 0;
            bridgeToDst.subresourceRange.layerCount = 1;
            bridgeToDst.srcAccessMask = (m_bridgeImageLayout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL)
                                            ? VK_ACCESS_TRANSFER_READ_BIT
                                            : 0;
            bridgeToDst.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;

            const VkPipelineStageFlags bridgeSrcStage =
                (m_bridgeImageLayout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL)
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

            m_bridgeImageLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;

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
                                   m_bridgeImage,
                                   VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                                   1,
                                   &uploadRegion);

            VkImageMemoryBarrier bridgeToSrc{};
            bridgeToSrc.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
            bridgeToSrc.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
            bridgeToSrc.newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
            bridgeToSrc.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            bridgeToSrc.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            bridgeToSrc.image = m_bridgeImage;
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

            m_bridgeImageLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;

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

            vkCmdCopyImage(commandBuffer,
                           m_bridgeImage,
                           VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                           m_swapchainImages[imageIndex],
                           VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                           1,
                           &copyRegion);

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

    void QTVulkanVideoDevice::destroyBridgeResources()
    {
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
        m_bridgeStatusLogged = false;
        m_bridgeFrameCounter = 0;
        m_bridgeSourceWidth = 0;
        m_bridgeSourceHeight = 0;
        m_bridgePackPath.clear();
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
