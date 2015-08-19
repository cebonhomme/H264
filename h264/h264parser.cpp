#include "h264parser.h"

string H264Parser::nal_unit_type[] = 
{
   "                         Unspecified",
   "    Coded slice of a non-IDR picture",
   "        Coded slice data partition A",
   "        Coded slice data partition B",
   "        Coded slice data partition C",
   "       Coded slice of an IDR picture",
   "Supplemental enhancement information",
   "              Sequence parameter set",
   "               Picture parameter set",
   "               Access unit delimiter",
   "                     End of sequence",
   "                       End of stream",
   "                         Filler data",
   "                            Reserved",
   "                            Reserved",
   "                            Reserved",
   "                            Reserved",
   "                            Reserved",
   "                            Reserved",
   "                            Reserved",
   "                            Reserved",
   "                            Reserved",
   "                            Reserved",
   "                            Reserved"
};
   
H264Parser::H264Parser(char* i, char* o)
{
   valid = false;
   in_file = i;
   out_file = o;
   
   if(!in_file)
      return;
   
   in_stream = new ifstream(in_file, ifstream::in | ifstream::binary);
   
   if(out_file)
      out_stream = new ofstream(out_file, ofstream::out | ofstream::trunc);
   
   valid = init();
}

H264Parser::~H264Parser()
{
   if(in_file)
   {
      if(in_stream->is_open())
         in_stream->close();
      delete in_stream;
   }
   
   if(out_file)
   {
      if(out_stream->is_open())
         out_stream->close();
      delete out_stream;
   }
}

bool H264Parser::init()
{
   char buffer = 0x00;
   int cnt = 0;
   while(in_stream->get(buffer))
   {
      if(cnt >= 2 && buffer == 0x01)
         return true;
      else if(buffer == 0x00)
         cnt++;
      else 
         return false;
   }
   return false;
}

void H264Parser::reset()
{
   in_stream->seekg(0, in_stream->beg);
   valid = init();
}

bool H264Parser::isValid()
{
   return valid;
}

unsigned char* H264Parser::read(unsigned int* length)
{
   if(!isValid())
      return NULL;
   
   *length = 0;
   unsigned int start = in_stream->tellg();
   char buffer = 0x00;
   char window[3];

   // Initialization of the window.
   for(int i = 1; i < 3; i++)
   {
      if(!in_stream->get(buffer))
         return NULL;
      window[i] = buffer;
   }

   while(in_stream->get(buffer))
   {
      window[0] = window[1];
      window[1] = window[2];
      window[2] = buffer;

      // zero_byte (0x00) + start_code_prefix_one_3bytes (0x000001)
      if(window[0] == 0x00 && window[1] == 0x00 && window[2] == 0x00)
         continue;
      else if(window[0] == 0x00 && window[1] == 0x00 && window[2] == 0x01)
         break;
      // Isolating the NumBytesInNALunit bytes of the NALU.
      else
         (*length)++;
   }
   
   unsigned int end = in_stream->tellg();
   
   if(*length == 0)
      return NULL;
   
   in_stream->seekg(start);
   char* nal_unit = new char[*length];
   in_stream->read(nal_unit, *length);
   in_stream->seekg(end);
   return  (unsigned char*) nal_unit;
}

void H264Parser::readAll()
{
   if(!isValid() || !out_file || !out_stream->is_open())
      return;
   
   unsigned int uID = 0;
   unsigned int uS  = 0;
   while(true)
   {
      unsigned char* nU = read(&uS);

      if(nU == NULL)
         break;
      
      (*out_stream) << setfill('0') << setw(5) << uID << ",   "
                    << setfill('0') << setw(5) << (unsigned int) (nU[0] & 0x1F) << ",   "
                    << setfill('0') << setiosflags(ios::fixed) << setw(10) << setprecision(3)  << (float) uS/125 << ",   "
                    << nal_unit_type[nU[0] & 0x1F] << endl;

      delete nU;
      uID++;
   }

   cout << uID << " NAL units processed." << endl;
}