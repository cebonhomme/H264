CC      = g++
CFLAGS  =
LDFLAGS = -I/usr/include/jrtplib3/ -ljrtp

all : h264 rtpclient

h264 : h264.o h264parser.o rtphandler.o
	$(CC) -o h264 h264.o h264parser.o rtphandler.o $(LDFLAGS)
rtpclient : rtpclient.o
	$(CC) -o rtpclient rtpclient.o $(LDFLAGS)

h264.o : h264.cpp
	$(CC) -c h264.cpp $(CFLAGS) $(LDFLAGS)
h264parser.o : h264parser.cpp
	$(CC) -c h264parser.cpp $(CFLAGS)
rtphandler.o : rtphandler.cpp
	$(CC) -c rtphandler.cpp $(CFLAGS) $(LDFLAGS)
rtpclient.o : rtpclient.cpp
	$(CC) -c rtpclient.cpp $(CFLAGS) $(LDFLAGS)

clean : 
	rm h264 rtpclient *~ *.o
