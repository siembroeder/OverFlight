cmake_minimum_required(VERSION 3.16)
project(wlhelper LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(Qt6 REQUIRED COMPONENTS Gui GuiPrivate)
find_package(PkgConfig REQUIRED)
pkg_check_modules(WAYLAND REQUIRED wayland-client)

add_library(wlhelper SHARED wlhelper.cpp)

target_link_libraries(wlhelper
    PRIVATE
    Qt6::Gui
    Qt6::GuiPrivate   # gives us the private/unstable Wayland interface headers
    ${WAYLAND_LIBRARIES}
)
target_include_directories(wlhelper PRIVATE ${WAYLAND_INCLUDE_DIRS})