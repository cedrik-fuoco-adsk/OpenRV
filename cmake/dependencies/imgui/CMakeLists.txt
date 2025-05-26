# imgui/CMakeLists.txt
cmake_minimum_required(VERSION 3.27)
project(imgui)

set(IMGUI_SOURCES
    imgui.cpp
    imgui_draw.cpp
    imgui_tables.cpp
    imgui_widgets.cpp
    imgui_demo.cpp # for testing
    misc/cpp/imgui_stdlib.cpp
    backends/imgui_impl_opengl2.cpp
    # Add/remove files as needed
)

set(IMGUI_HEADERS
    imgui.h
    backends/imgui_impl_opengl2.h
    misc/cpp/imgui_stdlib.h
    imconfig.h
    imstb_rectpack.h
    imstb_textedit.h
    imstb_truetype.h
    # Add/remove headers as needed
)

add_library(imgui SHARED ${IMGUI_SOURCES})

target_include_directories(imgui PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

install(TARGETS imgui LIBRARY DESTINATION lib)
install(FILES ${IMGUI_HEADERS} DESTINATION includes)