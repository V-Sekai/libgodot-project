cmake_minimum_required(VERSION 3.17)

project(sample)

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++17 -g")

set(GODOT_CPP_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../../godot-cpp)
set(LIBGODOT_BUILD_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../../build)

# Set godot-cpp to use the extension_api.json from our build directory
set(GODOTCPP_CUSTOM_API_FILE ${LIBGODOT_BUILD_DIR}/extension_api.json CACHE FILEPATH "Path to custom extension_api.json file" FORCE)

# Add godot-cpp as subdirectory
add_subdirectory(${GODOT_CPP_DIR} ${CMAKE_CURRENT_BINARY_DIR}/godot-cpp)

set(SOURCES src/main.cpp)

add_executable(${PROJECT_NAME} ${SOURCES})

# Option to override godot-cpp target selection
set(GODOTCPP_TARGET "auto" CACHE STRING "Godot-cpp target to link against (auto|template_debug|template_release|editor)")
set_property(CACHE GODOTCPP_TARGET PROPERTY STRINGS "auto;template_debug;template_release;editor")

# Determine the appropriate godot-cpp target based on build type
if(GODOTCPP_TARGET STREQUAL "auto")
    # Map build types to godot-cpp targets
    set(RELEASE_TYPES "Release;RelWithDebInfo;MinSizeRel")
    if(CMAKE_BUILD_TYPE IN_LIST RELEASE_TYPES)
        set(SELECTED_GODOTCPP_TARGET "godot-cpp::template_release")
    else()
        # Default to debug for Debug build type or unspecified build type
        set(SELECTED_GODOTCPP_TARGET "godot-cpp::template_debug")
    endif()
else()
    # Use user-specified target
    set(SELECTED_GODOTCPP_TARGET "godot-cpp::${GODOTCPP_TARGET}")
endif()

message(STATUS "Using godot-cpp target: ${SELECTED_GODOTCPP_TARGET}")

# Link against the selected godot-cpp CMake target
target_link_libraries(${PROJECT_NAME} 
    ${SELECTED_GODOTCPP_TARGET}
    Threads::Threads
)

add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
                   COMMAND ${CMAKE_COMMAND} -E copy
                       ${LIBGODOT_BUILD_DIR}/libgodot${CMAKE_SHARED_LIBRARY_SUFFIX}
                       ${CMAKE_BINARY_DIR}
                   COMMENT "Copying ${LIBGODOT_BUILD_DIR}/libgodot.${CMAKE_SHARED_LIBRARY_SUFFIX} to '${CMAKE_BINARY_DIR}'")
