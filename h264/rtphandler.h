#ifndef RTP_HANDLER_H
#define RTP_HANDLER_H

#include "rtpsession.h"
#include "rtpudpv4transmitter.h"
#include "rtpipv4address.h"
#include "rtpsessionparams.h"
#include "rtperrors.h"
#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <string>

#define RCV_PORT 5000
#define CLK_RATE 90000.0
#define FPS      30

using namespace jrtplib;
using namespace std;

class RTPHandler
{

private:

   RTPSession sess;
   uint16_t portbase;
	uint32_t destip;
   uint16_t destport;
   bool alive;

public:

   RTPHandler(char* di, char* dp);
   ~RTPHandler();

   bool isAlive();
   void send(unsigned char* pckt, unsigned int n);
   bool error(int e);
};

#endif