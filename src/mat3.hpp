#pragma once
#include "vec3.hpp"

struct Mat3 {
    double m[3][3];

    Mat3() { for(int i=0;i<3;++i) for(int j=0;j<3;++j) m[i][j]=0; }
    static Mat3 identity() {
        Mat3 r;
        r.m[0][0]=r.m[1][1]=r.m[2][2]=1.0;
        return r;
    }
    static Mat3 rotation(const Vec3& axis, double angle) {
        Vec3 a = axis.normalized();
        double c = std::cos(angle), s = std::sin(angle), t = 1-c;
        Mat3 r;
        r.m[0][0] = c + a.x*a.x*t; r.m[0][1] = a.x*a.y*t - a.z*s; r.m[0][2] = a.x*a.z*t + a.y*s;
        r.m[1][0] = a.y*a.x*t + a.z*s; r.m[1][1] = c + a.y*a.y*t; r.m[1][2] = a.y*a.z*t - a.x*s;
        r.m[2][0] = a.z*a.x*t - a.y*s; r.m[2][1] = a.z*a.y*t + a.x*s; r.m[2][2] = c + a.z*a.z*t;
        return r;
    }
    Vec3 mul(const Vec3& v) const {
        return {
            m[0][0]*v.x + m[0][1]*v.y + m[0][2]*v.z,
            m[1][0]*v.x + m[1][1]*v.y + m[1][2]*v.z,
            m[2][0]*v.x + m[2][1]*v.y + m[2][2]*v.z
        };
    }
};
