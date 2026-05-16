#pragma once
#include "vec3.hpp"

struct Ray {
    Vec3 origin;
    Vec3 direction;
    CVec3 E_field;
    double phase;
    int bounce_count;
    bool active;
};
