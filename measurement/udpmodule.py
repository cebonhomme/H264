""" 
Author: Cedric Bonhomme
Date: 19-07-2015

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
   UDPPacket is the data structure representing UDP packets. The payload size 
   is fixed to 1250 bytes (10kb) to ease the measurement. The separation 
   between header and payload allows to measure the goodput only. Each packet 
   has a timestamp, in order to track losses. It contains only two static 
   methods: encode and decode.
   """

   payload_size = 1250
   timestamp_size = 10
   header_size = timestamp_size + 2 # Minimum RTP header size.
   tot_size = header_size + payload_size

   header = 'a' * (header_size - timestamp_size)
   payload = 'b' * payload_size
   
   @staticmethod
   def decode(data):
      return int(data[0:10])

   @staticmethod
   def encode(timestamp):
      return ('%010d' % (timestamp%10000000000)) + UDPPacket.header + UDPPacket.payload
      
###############################################################################
class UDPFlow:

   """
   UDPFlow is a data structure used by UDPServers to keep tracks of incoming 
   UDP streams and to compute statistics about them.   
   """

   dt = 1
   
   # There must be only one stream per source.
   def __init__(self, src, bw):
      self.src = src
      self.bw = bw
      self.miss = [] # List of missing (delayed or lost) packets.
      self.N = [] # Array of arrived packets.
      self.N.append(0)
      self.current = (0,0) # Timestamp and arrival time of the last packet.

      # Based on the bandwidth, the number of packets per second can be computed. 
      self.M = max(UDPClient.bps, self.bw / (UDPPacket.payload_size/125))
      self.Mratio = self.M / UDPClient.bps
      self.Mmod = self.M % UDPClient.bps

   def add(self, timestamp, t):

      # The initial time is taken at the arrival of the first packet.
      if self.N[0] == 0:
         self.t_init = t

      # Arrival time is relative to t_init.
      self.dt = t - self.t_init

      # Each packet arrives in a specific time interval of size dt.
      if self.dt < len(self.N) * UDPFlow.dt:
         self.N[len(self.N) - 1] += 1
      else:
         self.N.append(1)
      
      # The incoming packet is delayed.
      if timestamp < self.current[0]:
         for i in range(len(self.miss)):
            if self.miss[i] == timestamp:
               self.miss.pop(i)
               break

      # The incoming packet is not delayed, but prior packets may be missing.
      elif timestamp > self.current[0]:
         for i in range(self.current[0] + 1, timestamp):
            self.miss.append(i)
         self.current = (timestamp, self.dt)

   # Returns the (rho, sigma) parameters based on the stream's statistics.
   def log(self):
      # rho = db/dt
      rho = float(sum(self.N)*UDPPacket.payload_size)/float(125*self.dt)
      
      """
      print '----------------------'
      for t in self.miss:
         print t, self.compute_dt(t)
      """

      # sigma = db*dt
      if self.miss:
         t = self.miss[0]
         sigma = (self.bw - rho) * self.compute_dt(self.miss[0])
      # No loss: undefined.
      else:
         sigma = -1

      # Values are rounded to integers.
      return int(rho), int(sigma)
      
   # Compute the relative sending time based on the timestamp and the bandwidth.
   def compute_dt(self, t):
      dt = t / self.M
      t -= dt*self.M

      if t < self.Mmod*(self.Mratio+1):
         dt += (t /(self.Mratio+1))*UDPClient.dt
      else:
         dt += self.Mmod*UDPClient.dt
         t -= self.Mmod*(self.Mratio+1)
         dt += (t/self.Mratio)*UDPClient.dt
      return dt   

###############################################################################
class UDPServer(Thread):

   """
   UDPServer is a thread handling incoming UDPPackets. If packets belong to an 
   existing flow, they are added to it, or discarded otherwise.
   """
   
   port = 6000
   expiration = 3
   
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
   def addFlow(self, src, bw):
      self.flowHandler.append(UDPFlow(src, bw))

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
               self.flowHandler[f].add(UDPPacket.decode(d[0]), t)

         # The timeout allows for closing the server properly.
         except socket.timeout:
            continue
         except socket.error, msg:
            print 'Socket error:', msg
            self.ON = False 

###############################################################################
class UDPClient:

   """
   UDPClient is the class streaming UDPPackets at a given rate, towards a 
   single UDPServer. It contains a single static method.
   """

   # Bursts per second: packets are sent at discrete, finite times. Setting 
   # a frequency similar to those in video streaming gives a measure that is 
   # close to the real behaviour of its target application.   
   bps = 30
   dt = float(1)/float(bps)
   
   @staticmethod   
   def send(addr, bw, dt):

      # Bandwidth and time interval must be integers.
      bw = int(bw)
      dt = int(dt)

      # The minimum bandwidth is UDPClient.bps*UDPPacket.payload_size kbps,
      # with a maximum precision of UDPPacket.payload_size kbps.
      N = max(UDPClient.bps, bw / (UDPPacket.payload_size/125))
      Nratio = N / UDPClient.bps
      Nmod = N % UDPClient.bps

      try:
         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

         timestamp = 0
         for t in range(dt):
            for i in range(UDPClient.bps):
               t_i = time.time()
               if i < Nmod: M = Nratio + 1
               else: M = Nratio
               for j in range(M):
                  s.sendto(UDPPacket.encode(timestamp), (addr, UDPServer.port))
                  timestamp += 1
               t_e = time.time()
               time.sleep(max(0, UDPClient.dt - (t_e - t_i)));

      except socket.error, msg:
         print 'Unable to send the UDP stream:', msg
         timestamp = -1
      finally:
         s.close()
         return timestamp