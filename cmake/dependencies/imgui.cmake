INCLUDE(ProcessorCount) # require CMake 3.15+

SET(_target
    "RV_DEPS_IMGUI"
)

SET(_imgui_version
    "v1.91.9"
)
SET(_implot_version
    "main"
)

# Download URLs for imgui and implot
SET(_imgui_download_url
    "https://github.com/ocornut/imgui/archive/refs/tags/${_imgui_version}.zip"
)
SET(_implot_download_url
    "https://github.com/epezent/implot/archive/refs/heads/${_implot_version}.zip"
)

# Hashes for verification (replace with actual hash values)
SET(_imgui_download_hash
    "PLACEHOLDER_HASH_FOR_IMGUI"
)
SET(_implot_download_hash
    "PLACEHOLDER_HASH_FOR_IMPLOT"
)

SET(_install_dir
    ${RV_DEPS_BASE_DIR}/${_target}/install
)

SET(_lib_dir
    ${_install_dir}/lib
)

IF(RV_TARGET_WINDOWS)
  SET(_imgui_lib_name
      imgui.lib
  )
  SET(_implot_lib_name
      implot.lib
  )
ELSE()
  SET(_imgui_lib_name
      ${CMAKE_STATIC_LIBRARY_PREFIX}imgui${CMAKE_STATIC_LIBRARY_SUFFIX}
  )
  SET(_implot_lib_name
      ${CMAKE_STATIC_LIBRARY_PREFIX}implot${CMAKE_STATIC_LIBRARY_SUFFIX}
  )
ENDIF()

SET(_imgui_lib
    ${_lib_dir}/${_imgui_lib_name}
)
SET(_implot_lib
    ${_lib_dir}/${_implot_lib_name}
)

SET(_build_dir
    "_build"
)

SET(_imgui_lib
    ${_lib_dir}/libimgui.dylib
)
LIST(APPEND _imgui_byproducts ${_imgui_lib})
MESSAGE(STATUS "cedrik: ${_imgui_byproducts}")
EXTERNALPROJECT_ADD(
  ${_target}
  GIT_REPOSITORY "https://github.com/ocornut/imgui.git"
  GIT_TAG "master"
  DOWNLOAD_DIR ${RV_DEPS_DOWNLOAD_DIR}
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
  SOURCE_DIR ${CMAKE_BINARY_DIR}/${_target}/src
  PATCH_COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_CURRENT_SOURCE_DIR}/imgui/CMakeLists.txt ${CMAKE_BINARY_DIR}/${_target}/src/CMakeLists.txt
  CONFIGURE_COMMAND ${CMAKE_COMMAND} -B ${_build_dir} -DCMAKE_BUILD_TYPE=Release
  BUILD_COMMAND ${CMAKE_COMMAND} --build ${_build_dir} --config Release -v --parallel=24
  INSTALL_COMMAND ${CMAKE_COMMAND} --install ${_build_dir} --prefix ${CMAKE_BINARY_DIR}/${_target}/install --config ${CMAKE_BUILD_TYPE}
  BUILD_BYPRODUCTS ${_imgui_byproducts}
  BUILD_IN_SOURCE TRUE
  USES_TERMINAL_BUILD TRUE
)

FILE(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/${_target}/install")
FILE(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/${_target}/install/includes")

SET(_lib_dir
    "${CMAKE_BINARY_DIR}/${_target}/src/_build"
)
SET(_libname
    "libimgui"
)

ADD_CUSTOM_COMMAND(
  COMMENT "Installing ${_target}'s libs into ${RV_STAGE_LIB_DIR}"
  OUTPUT ${RV_STAGE_LIB_DIR}/${_libname}
  COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
  DEPENDS ${_target}
)
ADD_CUSTOM_TARGET(
  ${_target}-stage-target ALL
  DEPENDS ${RV_STAGE_LIB_DIR}/${_libname}
)

ADD_DEPENDENCIES(dependencies ${_target}-stage-target)

ADD_LIBRARY(imgui::imgui SHARED IMPORTED GLOBAL)
ADD_DEPENDENCIES(imgui::imgui ${_target})

SET_PROPERTY(
  TARGET imgui::imgui
  # PROPERTY IMPORTED_LOCATION "${CMAKE_BINARY_DIR}/${_target}/install/lib/libimgui.so"
  PROPERTY IMPORTED_LOCATION "${CMAKE_BINARY_DIR}/${_target}/install/lib/libimgui.dylib"
)

SET_PROPERTY(
  TARGET imgui::imgui
  PROPERTY IMPORTED_SONAME ${_libname}
)

FILE(MAKE_DIRECTORY "${_include_dir}")
TARGET_INCLUDE_DIRECTORIES(
  imgui::imgui
  INTERFACE ${CMAKE_BINARY_DIR}/${_target}/install/includes
)

LIST(APPEND RV_DEPS_LIST imgui::imgui)
