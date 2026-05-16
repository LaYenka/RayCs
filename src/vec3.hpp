#pragma once
#include <cmath>
#include <complex>
#include <algorithm>
#include <iostream>

struct Vec3 {
    double x, y, z;

    Vec3() : x(0), y(0), z(0) {}
    Vec3(double x, double y, double z) : x(x), y(y), z(z) {}

    Vec3 operator+(const Vec3& o) const { return {x+o.x, y+o.y, z+o.z}; }
    Vec3 operator-(const Vec3& o) const { return {x-o.x, y-o.y, z-o.z}; }
    Vec3 operator*(double s) const { return {x*s, y*s, z*s}; }
    Vec3 operator/(double s) const { double inv=1.0/s; return {x*inv, y*inv, z*inv}; }
    Vec3 operator-() const { return {-x, -y, -z}; }

    double operator[](int i) const { return (&x)[i]; }
    double& operator[](int i) { return (&x)[i]; }

    double dot(const Vec3& o) const { return x*o.x + y*o.y + z*o.z; }
    Vec3 cross(const Vec3& o) const {
        return {y*o.z - z*o.y, z*o.x - x*o.z, x*o.y - y*o.x};
    }
    double norm() const { return std::sqrt(dot(*this)); }
    double norm_sq() const { return dot(*this); }
    Vec3 normalized() const { double n = norm(); return n > 1e-15 ? *this / n : Vec3{0,0,0}; }
    Vec3 reflect(const Vec3& n) const { return *this - n * (2.0 * dot(n)); }
};

struct CVec3 {
    std::complex<double> x, y, z;
    CVec3() : x(0), y(0), z(0) {}
    CVec3(std::complex<double> x, std::complex<double> y, std::complex<double> z)
        : x(x), y(y), z(z) {}
    CVec3(double x, double y, double z)
        : x(x), y(y), z(z) {}

    CVec3 operator+(const CVec3& o) const { return {x+o.x, y+o.y, z+o.z}; }
    CVec3 operator-(const CVec3& o) const { return {x-o.x, y-o.y, z-o.z}; }
    CVec3 operator*(std::complex<double> s) const { return {x*s, y*s, z*s}; }
    CVec3 operator*(double s) const { return {x*s, y*s, z*s}; }
    CVec3 operator/(double s) const { double inv=1.0/s; return {x*inv, y*inv, z*inv}; }

    double mag_sq() const {
        return std::norm(x) + std::norm(y) + std::norm(z);
    }
};

inline double dot(const Vec3& a, const Vec3& b) { return a.dot(b); }
inline Vec3 cross(const Vec3& a, const Vec3& b) { return a.cross(b); }
