//
// Copyright (C) 2026 Autodesk, Inc. All Rights Reserved.
//
// SPDX-License-Identifier: Apache-2.0
//
#pragma once

#ifdef PLATFORM_LINUX

#include <memory>
#include <cstdint>
#include <string>
#include <vector>

#include <vulkan/vulkan_core.h>

class QWindow;
struct _XDisplay;

namespace Rv
{
    class GLView;

    class QTVulkanVideoDevice
    {
    public:
        QTVulkanVideoDevice();
        ~QTVulkanVideoDevice();

        bool initializeForWindow(QWindow* window);
        void setBridgeSourceView(GLView* sourceView);
        void renderFrame();
        void resizeSwapchain();

        bool isInitialized() const { return m_initialized; }
        bool selectedFormatIs10Bit() const { return m_selectedFormatIs10Bit; }
        bool isNoOp() const { return !m_initialized; }

    private:
        bool createInstance();
        bool createSurface();
        bool pickPhysicalDevice();
        bool createLogicalDevice();
        bool createSwapchain();
        bool createImageViews();
        bool createRenderPass();
        bool createFramebuffers();
        bool createCommandPool();
        bool createCommandBuffers();
        bool createSyncObjects();
        bool recreateSwapchain();
        bool ensureBridgeResources();
        bool prepareBridgeFrameData();
        bool recordCommandBuffer(VkCommandBuffer commandBuffer, uint32_t imageIndex, bool useBridgePath);
        void destroyBridgeResources();
        uint32_t findMemoryType(uint32_t typeFilter, VkMemoryPropertyFlags properties) const;
        void cleanupSwapchain();
        void cleanup();

    private:
        static constexpr uint32_t kFramesInFlight = 2;

        QWindow* m_window{nullptr};
        bool m_initialized{false};
        bool m_swapchainDirty{false};
        bool m_selectedFormatIs10Bit{false};
        bool m_surfaceFormatsLogged{false};
        bool m_bridgeCopySupported{false};
        bool m_bridgeUnavailableLogged{false};
        bool m_bridgeActivationLogged{false};
        bool m_bridgeStatusLogged{false};
        uint64_t m_frameCounter{0};
        uint64_t m_bridgeFrameCounter{0};
        GLView* m_bridgeSourceView{nullptr};

        _XDisplay* m_x11Display{nullptr};

        VkInstance m_instance{VK_NULL_HANDLE};
        VkPhysicalDevice m_physicalDevice{VK_NULL_HANDLE};
        VkDevice m_device{VK_NULL_HANDLE};
        VkSurfaceKHR m_surface{VK_NULL_HANDLE};
        VkQueue m_graphicsQueue{VK_NULL_HANDLE};
        VkQueue m_presentQueue{VK_NULL_HANDLE};
        uint32_t m_graphicsQueueFamily{VK_QUEUE_FAMILY_IGNORED};
        uint32_t m_presentQueueFamily{VK_QUEUE_FAMILY_IGNORED};

        VkSwapchainKHR m_swapchain{VK_NULL_HANDLE};
        std::vector<VkImage> m_swapchainImages;
        std::vector<VkImageView> m_swapchainImageViews;
        std::vector<VkFramebuffer> m_swapchainFramebuffers;
        std::vector<VkImageLayout> m_swapchainImageLayouts;
        VkFormat m_swapchainImageFormat{VK_FORMAT_UNDEFINED};
        VkColorSpaceKHR m_swapchainColorSpace{VK_COLOR_SPACE_SRGB_NONLINEAR_KHR};
        VkExtent2D m_swapchainExtent{0, 0};

        VkRenderPass m_renderPass{VK_NULL_HANDLE};
        VkCommandPool m_commandPool{VK_NULL_HANDLE};
        std::vector<VkCommandBuffer> m_commandBuffers;
        std::vector<uint8_t> m_bridgePackedFrame;
        uint32_t m_bridgeSourceWidth{0};
        uint32_t m_bridgeSourceHeight{0};
        std::string m_bridgePackPath;
        VkBuffer m_bridgeStagingBuffer{VK_NULL_HANDLE};
        VkDeviceMemory m_bridgeStagingMemory{VK_NULL_HANDLE};
        VkDeviceSize m_bridgeStagingCapacity{0};
        VkImage m_bridgeImage{VK_NULL_HANDLE};
        VkDeviceMemory m_bridgeImageMemory{VK_NULL_HANDLE};
        VkImageLayout m_bridgeImageLayout{VK_IMAGE_LAYOUT_UNDEFINED};

        std::vector<VkSemaphore> m_imageAvailableSemaphores;
        std::vector<VkSemaphore> m_renderFinishedSemaphores;
        std::vector<VkFence> m_inFlightFences;
        std::vector<VkFence> m_imagesInFlight;
        uint32_t m_currentFrame{0};
    };

    std::unique_ptr<QTVulkanVideoDevice> makeNoOpQTVulkanVideoDevice();
} // namespace Rv

#endif // PLATFORM_LINUX
