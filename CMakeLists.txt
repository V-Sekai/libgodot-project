cmake_minimum_required(VERSION 3.15)
project(godot_project)

set(CMAKE_VERBOSE_MAKEFILE ON)
set(CMAKE_NINJA_VERBOSE TRUE)

include(ProcessorCount)
ProcessorCount(num_cores)
if(num_cores EQUAL 0)
    set(num_cores 1)
endif()

set(BASE_DIR ${CMAKE_SOURCE_DIR})
set(BUILD_DIR ${CMAKE_BINARY_DIR})

set(SCONS_CACHE_PATH "${BUILD_DIR}/scons_cache")

if(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    execute_process(COMMAND uname -m OUTPUT_VARIABLE ARCHITECTURE OUTPUT_STRIP_TRAILING_WHITESPACE)
    if(ARCHITECTURE STREQUAL "arm64")
        set(ARCH_SUFFIX "arm64")
    else()
        set(ARCH_SUFFIX "x86_64")
    endif()
else()
    set(ARCH_SUFFIX "x86_64")
endif()

if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    set(host_platform "linuxbsd")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    set(host_platform "windows")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    set(host_platform "macos")
else()
    set(host_platform "linuxbsd")
endif()

set(TARGET_PLATFORM "${host_platform}" CACHE STRING "Target platform (linuxbsd, windows, macos, ios)")
set(PRECISION "double" CACHE STRING "Floating-point precision (single/double)")
set(REGENERATE OFF CACHE BOOL "Force regeneration of build files")

if(TARGET_PLATFORM STREQUAL "windows")
    set(LIB_SUFFIX "dll")
    set(EXE_SUFFIX ".exe")
elseif(TARGET_PLATFORM STREQUAL "macos")
    set(LIB_SUFFIX "dylib")
    set(EXE_SUFFIX "")
elseif(TARGET_PLATFORM STREQUAL "ios")
    set(LIB_SUFFIX "a")
    set(EXE_SUFFIX "")
else()
    set(LIB_SUFFIX "so")
    set(EXE_SUFFIX "")
endif()

set(BUILD_SUFFIX "${TARGET_PLATFORM}.editor.${PRECISION}")

set(GODOT_DIR "${BASE_DIR}/godot")
set(GODOT_CPP_DIR "${BASE_DIR}/godot-cpp")
set(SWIFT_DIR "${BASE_DIR}/SwiftGodot")
set(GODOT_BIN_PATH "${GODOT_DIR}/bin/godot.${BUILD_SUFFIX}.${ARCH_SUFFIX}${EXE_SUFFIX}")
set(GODOT_LIB_PATH "${GODOT_DIR}/bin/obj/bin/libgodot.${BUILD_SUFFIX}.${ARCH_SUFFIX}.${LIB_SUFFIX}")
set(GODOT_LIB_COPY_PATH "${BUILD_DIR}/libgodot.${LIB_SUFFIX}")

add_custom_command(
    OUTPUT "${GODOT_BIN_PATH}"
    COMMAND scons
        platform=${TARGET_PLATFORM}
        target=editor
        precision=${PRECISION}
        arch=${ARCH_SUFFIX}
        cache_path=${SCONS_CACHE_PATH}
        -j${num_cores}
    WORKING_DIRECTORY "${GODOT_DIR}"
    COMMENT "Building Godot executable with ${num_cores} cores"
    DEPENDS "${GODOT_DIR}/SConstruct"
)

# Also build the shared library version
add_custom_command(
    OUTPUT "${GODOT_LIB_PATH}"
    COMMAND scons
        platform=${TARGET_PLATFORM}
        target=editor
        precision=${PRECISION}
        arch=${ARCH_SUFFIX}
        library_type=shared_library
        cache_path=${SCONS_CACHE_PATH}
        -j${num_cores}
    WORKING_DIRECTORY "${GODOT_DIR}"
    COMMENT "Building Godot shared library with ${num_cores} cores"
    DEPENDS "${GODOT_DIR}/SConstruct"
)

add_custom_command(
    OUTPUT "${GODOT_LIB_COPY_PATH}"
    COMMAND ${CMAKE_COMMAND} -E copy "${GODOT_LIB_PATH}" "${GODOT_LIB_COPY_PATH}"
    DEPENDS "${GODOT_LIB_PATH}"
    COMMENT "Copying libgodot shared library to build directory"
)

add_custom_target(copy_godot_lib ALL DEPENDS "${GODOT_LIB_COPY_PATH}")

set(EXTENSION_API "${BUILD_DIR}/extension_api.json")
add_custom_command(
    OUTPUT "${EXTENSION_API}"
    COMMAND "${GODOT_BIN_PATH}" --verbose --dump-extension-api "${EXTENSION_API}"
    DEPENDS "${GODOT_BIN_PATH}"
    WORKING_DIRECTORY "${BUILD_DIR}"
    COMMENT "Generating extension API JSON"
)

# Copy gdextension_interface.h to build directory for godot-cpp
set(GDEXTENSION_INTERFACE "${BUILD_DIR}/gdextension_interface.h")
add_custom_command(
    OUTPUT "${GDEXTENSION_INTERFACE}"
    COMMAND ${CMAKE_COMMAND} -E copy "${GODOT_CPP_DIR}/gdextension/gdextension_interface.h" "${GDEXTENSION_INTERFACE}"
    DEPENDS "${GODOT_CPP_DIR}/gdextension/gdextension_interface.h"
    COMMENT "Copying gdextension_interface.h to build directory"
)

add_custom_target(copy_gdextension_interface ALL DEPENDS "${GDEXTENSION_INTERFACE}")

# Custom target to configure and build cpp_sample after API generation
add_custom_target(configure_cpp_sample
    COMMAND ${CMAKE_COMMAND} -E make_directory "${BUILD_DIR}/samples/cpp_sample"
    COMMAND ${CMAKE_COMMAND} -S "${BASE_DIR}/samples/cpp_sample" -B "${BUILD_DIR}/samples/cpp_sample"
        -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
        -DGODOTCPP_CUSTOM_API_FILE=${EXTENSION_API}
        -DLIBGODOT_BUILD_DIR=${BUILD_DIR}
    DEPENDS "${EXTENSION_API}" "${GDEXTENSION_INTERFACE}"
    COMMENT "Configuring cpp_sample with generated API"
    WORKING_DIRECTORY "${BUILD_DIR}"
)

# Custom target to build the sample after configuration
add_custom_target(build_cpp_sample
    COMMAND ${CMAKE_COMMAND} --build "${BUILD_DIR}/samples/cpp_sample" --target sample
    DEPENDS configure_cpp_sample
    COMMENT "Building cpp_sample"
)

# Create a target alias for convenience
add_custom_target(sample DEPENDS build_cpp_sample)

if(TARGET_PLATFORM STREQUAL "ios")
    set(SWIFT_FRAMEWORK "${BUILD_DIR}/libgodot.framework")
    add_custom_command(
        OUTPUT "${SWIFT_FRAMEWORK}"
        COMMAND "${SWIFT_DIR}/scripts/make-libgodot.framework"
            "${GODOT_DIR}"
            "${BUILD_DIR}"
        WORKING_DIRECTORY "${SWIFT_DIR}"
        COMMENT "Building Swift framework"
        DEPENDS "${GODOT_BIN_PATH}"
    )
    add_custom_target(swift_framework ALL DEPENDS "${SWIFT_FRAMEWORK}")
endif()

add_custom_target(build_godot ALL DEPENDS "${GODOT_BIN_PATH}")
add_custom_target(generate_api ALL DEPENDS "${EXTENSION_API}")

add_dependencies(generate_api build_godot)
add_dependencies(copy_godot_lib build_godot)

# Ensure cpp_sample depends on the extension API being generated
add_dependencies(sample generate_api)
add_dependencies(sample copy_gdextension_interface)

if(TARGET_PLATFORM STREQUAL "ios")
    add_dependencies(swift_framework sample)
endif()

if(TARGET_PLATFORM STREQUAL "windows")
    set(ENV{PATH} "$ENV{PATH};${GODOT_DIR}/bin")
endif()

message(STATUS "Build configuration:")
message(STATUS "  Target platform:    ${TARGET_PLATFORM}")
message(STATUS "  Floating precision: ${PRECISION}")
message(STATUS "  Build directory:    ${BUILD_DIR}")
message(STATUS "  CPU cores detected: ${num_cores}")
message(STATUS "  Architecture:       ${ARCH_SUFFIX}")
message(STATUS "  SCons cache:        ${SCONS_CACHE_PATH}")
