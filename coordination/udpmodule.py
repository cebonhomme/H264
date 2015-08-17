""" 
Author: Cedric Bonhomme
Date: 26-07-2015

This file contains the implementation of the UDP module, used in senders 
(UDPClient) and listeners (UDPServer).
UDPClients send UDPPackets to UDPServers at a given rate, while those 
servers keep tracks on various statistics about their incoming streams.
"""

import time
import socket
from threading import Thread

###############################################################################
class UDPPacket:

   """
   UDPPacket is the data structure representing UDP packets. The max payload 
   size is fixed to 1250 bytes (10kb) to ease the measurement. The separation 
   between header and payload allows to measure the goodput only. Each packet 
   has a timestamp, in order to track losses. It contains only two static 
   methods: encode and decode.
   """

   payload_size = 1250
   timestamp_size = 10
   header_size = timestamp_size + 2 # Minimum RTP header size.
   tot_size = header_size + payload_size

   header = 'a' * (header_size - timestamp_size)
   
   @staticmethod
   def decode(data):
      return int(data[0:10]), float(len(data) - UDPPacket.header_size)/125
   @staticmethod
   def encode(timestamp, payload_size):
      return ('%010d' % (timestamp%10000000000)) + UDPPacket.header + 'b' * payload_size
      
###############################################################################
class UDPFlow:

   """
   UDPFlow is a data structure used by UDPServers to keep tracks of incoming 
   UDP streams and to compute statistics about them.   
   """
   
   dt = 1
   # There must be only one stream per source.
   def __init__(self, src):
      self.src = src
      self.miss = [] # List of missing (delayed or lost) packets.
      self.N = [] # Array of arrived packets.
      self.N.append(0)
      self.current = (0,0) # Timestamp and arrival time of the last packet.

   def add(self, data, t):
      timestamp, size = UDPPacket.decode(data)
      # The initial time is taken at the arrival of the first packet.
      if self.N[0] == 0:
         self.t_init = t

      # Arrival time is relative to t_init.
      self.dt = t - self.t_init
      
      # Each packet arrives in a specific time interval of size dt.
      if self.dt < len(self.N) * UDPFlow.dt:
         self.N[len(self.N) - 1] += size
      else:
         self.N.append(size)

      # The incoming packet is delayed.
      if timestamp < self.current[0]:
         for p in self.miss:
            if p[0] == timestamp:
               self.miss.remove(p)
      
      # The incoming packet is not delayed, but prior packets may be missing.
      elif timestamp > self.current[0]:
         for i in range(self.current[0] + 1, timestamp):
            self.miss.append((i,self.current[1]))
         self.current = (timestamp, self.dt)

   # Returns the (rho, sigma) parameters based on the stream's statistics.
   def log(self):
      return (self.N,self.miss)
###############################################################################
class UDPServer(Thread):

   """
   UDPServer is a thread handling incoming UDPPackets. If packets belong to an 
   existing flow, they are added to it, or discarded otherwise.
   """
   
   port = 6000
   expiration = 5
   
   def __init__(self, addr):
      Thread.__init__(self)
      try:
         self.ON = True
         self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
         self.s.bind((addr, UDPServer.port))
         self.s.settimeout(UDPServer.expiration)
         self.flowHandler = []

      except socket.error, msg:
         print 'Socket creation error:', msg
         self.ON = False      
      
   def close(self):
      self.ON = False
      self.s.close()

   def isAlive(self):
      return self.ON
   # Finds a flow based on an IP address.
   def find(self, src):
      for i in range(len(self.flowHandler)):
         if self.flowHandler[i].src == src:
            return i
      return -1

   # Adds a flow to the flow handler.
   def addFlow(self, src):
      self.flowHandler.append(UDPFlow(src))

   # Removes a flow from the flow handler and returns (rho,sigma).
   def delFlow(self, src):
      f = self.find(src)
      if f == -1: 
         return ''
      stats = self.flowHandler[f].log()
      self.flowHandler.pop(f)
      return stats

   # Infinite loop handling incoming packets.
   def run(self):
      while self.ON:
         try:
            d = self.s.recvfrom(UDPPacket.tot_size) # Blocking operation.
            t = time.time()
            f = self.find(d[1][0])
            if d[0] and f != -1:
               self.flowHandler[f].add(d[0], t)
         # The timeout allows for closing the server properly.
         except socket.timeout:
            continue
         except socket.error, msg:
            print 'Socket error:', msg
            self.ON = False 

###############################################################################
class UDPClient:

   """
   UDPClient is the class streaming UDPPackets towards a single UDPServer, 
   based on the size of the frame to send.
   """
   
   def __init__(self, addr):
      try:
         self.ON = True
         self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
         self.dest = (addr, UDPServer.port)
         self.timestamp = 0
      except socket.error, msg:
         print 'Socket creation error:', msg
         self.ON = False

   def close(self):
      self.ON = False
      self.s.close()
      
   def isAlive(self):
      return self.ON
 
   def send(self, frame_size):
      
      if not self.ON:
         return
      
      # S = N*UDPPacket.payload_size + M bytes
      S = int(125*frame_size)
      N = S / UDPPacket.payload_size
      M = S % UDPPacket.payload_size

      try:
         
         for i in range(N):
            self.s.sendto(UDPPacket.encode(self.timestamp, UDPPacket.payload_size), self.dest)
            self.timestamp += 1
            
         if M != 0:
            self.s.sendto(UDPPacket.encode(self.timestamp, M), self.dest)
            self.timestamp += 1

      except socket.error, msg:
         print 'Unable to send the UDP stream:', msg
         self.ON = False