#pragma once
#include <string>

enum class Method { PO, SBR, BOTH };

struct Config {
    std::string mesh_file;
    std::string output_file = "rcs.csv";
    double frequency = 10e9;
    int max_bounces = 3;
    double ray_density = 10.0;
    double theta_min = 0.0, theta_max = 180.0;
    int theta_steps = 180;
    double phi_min = 0.0, phi_max = 360.0;
    int phi_steps = 360;
    Method method = Method::SBR;
    bool bistatic = false;
    double inc_theta = 0.0;
    double inc_phi = 0.0;
    bool verbose = false;
};
