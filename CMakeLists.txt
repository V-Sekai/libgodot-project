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

set(BUILD_SUFFIX "${TARGET_PLATFORM}.template_release.${PRECISION}")

set(GODOT_DIR "${BASE_DIR}/godot")
set(GODOT_CPP_DIR "${BASE_DIR}/godot-cpp")
set(SWIFT_DIR "${BASE_DIR}/SwiftGodot")
set(GODOT_BIN_PATH "${GODOT_DIR}/bin/godot.${BUILD_SUFFIX}.x86_64${EXE_SUFFIX}")

add_custom_command(
    OUTPUT "${GODOT_BIN_PATH}"
    COMMAND scons
        platform=${TARGET_PLATFORM}
        target=template_release
        precision=${PRECISION}
        -j${num_cores}
    WORKING_DIRECTORY "${GODOT_DIR}"
    COMMENT "Building Godot executable with ${num_cores} cores"
    DEPENDS "${GODOT_DIR}/SConstruct"
)

set(EXTENSION_API "${BUILD_DIR}/extension_api.json")
add_custom_command(
    OUTPUT "${EXTENSION_API}"
    COMMAND "${GODOT_BIN_PATH}" --verbose --dump-extension-api "${EXTENSION_API}"
    DEPENDS "${GODOT_BIN_PATH}"
    WORKING_DIRECTORY "${BUILD_DIR}"
    COMMENT "Generating extension API JSON"
)

set(GODOT_CPP_LIB "${BUILD_DIR}/libgodot-cpp.a")
add_custom_command(
    OUTPUT "${GODOT_CPP_LIB}"
    COMMAND scons
        generate_bindings=yes
        platform=${TARGET_PLATFORM}
        precision=${PRECISION}
        -j${num_cores}
    WORKING_DIRECTORY "${GODOT_CPP_DIR}"
    COMMENT "Building godot-cpp library"
    DEPENDS "${EXTENSION_API}"
)

if(TARGET_PLATFORM STREQUAL "ios")
    set(SWIFT_FRAMEWORK "${BUILD_DIR}/libgodot.framework")
    add_custom_command(
        OUTPUT "${SWIFT_FRAMEWORK}"
        COMMAND "${SWIFT_DIR}/scripts/make-libgodot.framework"
            "${GODOT_DIR}"
            "${BUILD_DIR}"
        WORKING_DIRECTORY "${SWIFT_DIR}"
        COMMENT "Building Swift framework"
        DEPENDS "${GODOT_BIN_PATH}" "${GODOT_CPP_LIB}"
    )
    add_custom_target(swift_framework ALL DEPENDS "${SWIFT_FRAMEWORK}")
endif()

add_custom_target(build_godot ALL DEPENDS "${GODOT_BIN_PATH}")
add_custom_target(generate_api ALL DEPENDS "${EXTENSION_API}")
add_custom_target(build_cpp ALL DEPENDS "${GODOT_CPP_LIB}")

add_dependencies(generate_api build_godot)
add_dependencies(build_cpp generate_api)

if(TARGET_PLATFORM STREQUAL "ios")
    add_dependencies(swift_framework build_cpp)
endif()

if(TARGET_PLATFORM STREQUAL "windows")
    set(ENV{PATH} "$ENV{PATH};${GODOT_DIR}/bin")
endif()

message(STATUS "Build configuration:")
message(STATUS "  Target platform:    ${TARGET_PLATFORM}")
message(STATUS "  Floating precision: ${PRECISION}")
message(STATUS "  Build directory:    ${BUILD_DIR}")
message(STATUS "  CPU cores detected: ${num_cores}")
