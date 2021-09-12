#include <iostream>
#include <string>

struct interop
{
   int an_int;
   float a_float;
   const char* a_string;
};

interop out;
std::string append;

extern "C" interop* example(const char* in_string)
{
   out.an_int += 10;
   out.a_float += 3.14159265359;
   append = "you sent: ";
   append += in_string;
   out.a_string = append.c_str();
   return &out;
}
