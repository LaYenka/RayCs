cmake_minimum_required(VERSION 3.16)
project(RayCs LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(BUILD_PYTHON "Build Python _core bindings instead of CLI" OFF)

# ── Dependencies ────────────────────────────────────────────────────
find_package(OpenMP REQUIRED)
find_library(CGNS_LIBRARY cgns REQUIRED)
find_package(MPI QUIET COMPONENTS CXX)

# Common source files (every target except main.cpp)
set(RAYCS_SOURCES
    src/cgns_mesh.cpp
    src/bvh.cpp
    src/po.cpp
    src/sbr.cpp
    src/rcs.cpp
)

# Common compile options
set(RAYCS_COMPILE_OPTIONS -Wall -Wextra -O3 -march=native)

# ── CLI target ──────────────────────────────────────────────────────
if(NOT BUILD_PYTHON)
    add_executable(raycs src/main.cpp ${RAYCS_SOURCES})

    target_include_directories(raycs PRIVATE src)

    target_link_libraries(raycs PRIVATE
        OpenMP::OpenMP_CXX
        ${CGNS_LIBRARY}
    )

    target_compile_options(raycs PRIVATE ${RAYCS_COMPILE_OPTIONS})

    if(MPI_FOUND)
        target_compile_definitions(raycs PRIVATE USE_MPI=1)
        target_link_libraries(raycs PRIVATE MPI::MPI_CXX)
        message(STATUS "MPI found: ${MPI_CXX_LIBRARIES}")
    else()
        message(STATUS "MPI not found - building without MPI support")
    endif()

# ── Python _core target ─────────────────────────────────────────────
else()
    set(CMAKE_POSITION_INDEPENDENT_CODE ON)

    # Fetch pybind11
    include(FetchContent)
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG v2.12.0
    )
    FetchContent_MakeAvailable(pybind11)

    # pybind11_add_module instead of add_executable
    pybind11_add_module(_core
        python/src/raycs/_core/bindings.cpp
        ${RAYCS_SOURCES}
    )

    target_include_directories(_core PRIVATE
        src
        ${pybind11_INCLUDE_DIRS}
    )

    target_link_libraries(_core PRIVATE
        OpenMP::OpenMP_CXX
        ${CGNS_LIBRARY}
    )

    target_compile_options(_core PRIVATE ${RAYCS_COMPILE_OPTIONS} -fPIC)

    if(MPI_FOUND)
        target_compile_definitions(_core PRIVATE USE_MPI=1)
        target_link_libraries(_core PRIVATE MPI::MPI_CXX)
        message(STATUS "MPI found: ${MPI_CXX_LIBRARIES}")
    else()
        message(STATUS "MPI not found - building without MPI support")
    endif()

    install(TARGETS _core DESTINATION raycs)
endif()
