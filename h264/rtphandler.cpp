#include "rtphandler.h"

RTPHandler::RTPHandler(char* di, char* dp)
{
	portbase = RCV_PORT;
	destip = inet_addr(di);
   destport = (uint16_t) atoi(dp);
   alive = true;

	if (destip == INADDR_NONE)
	{
		cerr << "Bad IP address specified" << endl;
		alive = false;
      return;
	}

	destip = ntohl(destip);
	
	RTPUDPv4TransmissionParams transparams;
	RTPSessionParams sessparams;
 
	sessparams.SetOwnTimestampUnit(1.0/CLK_RATE);		
	
	sessparams.SetAcceptOwnPackets(true);
	transparams.SetPortbase(portbase);
   int e = sess.Create(sessparams,&transparams);
   if(error(e)) return;
	cout << sessparams.GetMaximumPacketSize()<< endl;
	RTPIPv4Address addr(destip,destport);
	
   e = sess.AddDestination(addr);
	if(error(e)) return;
}
	
RTPHandler::~RTPHandler()
{
   sess.BYEDestroy(RTPTime(10,0),0,0);
}

bool RTPHandler::isAlive()
{
   return alive;
}
    
void RTPHandler::send(unsigned char* pckt, unsigned int n)
{
   //TODO: Fragmentation;
   
   
   int e = sess.SendPacket((void *)pckt,n,0,false,CLK_RATE);
   if(error(e)) return;

   sess.BeginDataAccess();
	
   // check incoming packets
   if (sess.GotoFirstSourceWithData())
   {
      while(sess.GotoNextSourceWithData())
      {
         RTPPacket *pack;
         
         while ((pack = sess.GetNextPacket()) != NULL)
         {
            cout <<"Got packet !" << endl;
            sess.DeletePacket(pack);
         }
      }
   }
   sess.EndDataAccess();

   RTPTime::Wait(RTPTime(0,FPS));

}

bool RTPHandler::error(int e)
{
   if(e < 0)
   {   
	  cerr << "ERROR: " << RTPGetErrorString(e) << endl;
     alive = false;
     return true;
   }
   return false;
}