#pragma once
#include "mesh.hpp"
#include <string>

Mesh load_cgns_mesh(const std::string& filename);
Mesh load_obj_mesh(const std::string& filename);
