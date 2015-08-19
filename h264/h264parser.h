#ifndef H264_PARSER_H
#define H264_PARSER_H

#include <fstream>
#include <iostream>
#include <iomanip>

using namespace std;

class H264Parser
{

private:

   const char* in_file;
   const char* out_file;
   ifstream* in_stream;
   ofstream* out_stream;
   bool valid;
   static string nal_unit_type[];
   
public:

   H264Parser(char* i, char* o);
   ~H264Parser();
   
   bool init();
   void reset();
   bool isValid();
   unsigned char* read(unsigned int* length);
   void readAll();
};

#endif
