#include "h264parser.h"
#include "rtphandler.h"

using namespace std;

int main(int argc, char* argv[])
{
   if(argc == 3)
   {
      H264Parser* parser = new H264Parser(argv[1], argv[2]);
      if(!parser->isValid())
      {
         cerr << "Cannot open input file " << argv[1] << endl;
         delete parser;
         return -1;
      }
      parser->readAll();
 
      delete parser;
      return 0;
   }

   if(argc != 6)
   {
      cerr << "Invalid number of parameters" << endl;
      cerr << "./h264 input1 input2 address port number" << endl;
      return -1;
   }

   H264Parser* parser = new H264Parser(argv[1], NULL);
   if(!parser->isValid())
   {
      cerr << "Cannot open input file " << argv[1] << endl;
      delete parser;
      return -1;
   }

   RTPHandler* handler = new RTPHandler(argv[3], argv[4]);
   if(!handler->isAlive())
   {
      delete parser;
      delete handler;
      return -1;
   }

   int num = atoi(argv[5]);
   for (int i = 1 ; i <= num ; i++)
	{
      unsigned int n = 0;
      unsigned char* nal_unit = parser->read(&n);

      cout << endl << "Sending packet " << i << "/" << num << " of size " <<  n << endl;

      handler->send(nal_unit, n);
      delete nal_unit;

      if(!handler->isAlive())
         break;
   }
   
   delete parser;
   delete handler;
   return 0;
}