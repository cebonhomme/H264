""" 
Author: Cedric Bonhomme
Date: 26-07-2015

This file contains the implementation of the sender class, which is at the
heart of the coordination protocol. Senders are required to communicate between
them to use the network in the most optimal way.
"""

import sys
import time
import Queue
from udpmodule import *
from tcpmodule import *

class Sender:

   """
   A Sender is a program streaming H264 content to its related Listener. It 
   has two different encodings (CBR and VBR) and choose which one to send to 
   get the maximum fidelity and avoid losses. To do that, it handles TCP 
   connections with other senders, in order to exploit the network's 
   characteristics, computed by the measurement tool.
   """

   fps = 30
   dt = float(1)/float(fps)
   expiration = 5
   rounding = 100
   
   def __init__(self, src, params, cbr, vbr):
      self.ON = True

      # IP addresses.
      self.src = src
      self.dest = params[0]
      
      # CBR and VBR encodings of the video to stream.
      self.cbr = cbr
      self.vbr = vbr

      # A neighbour is a sender with:
      # - its IP address
      # - the bandwidth margin (rho - rho")
      # - the future instant when it will switch back to VBR (-1 by default).
      self.sources = []

      self.sigma = params[1][1]
      self.sig = self.sigma

      # Case 1: the sender is alone.
      if len(params) == 2:
         self.base_frame_size = (params[1][0]/Sender.fps)
         
      # Case 2: the sender is probably correlated with other sources.
      else:
         self.base_frame_size = (params[2]/Sender.fps)

         # Computing the bandwidth gain
         for i in range(3, len(params)):
            margin =  ((params[i][1] - params[2])/Sender.fps)
            self.sources.append([params[i][0], margin, -1])

      self.cN = []
      for n in self.sources:
         if n[1] != 0:
            self.cN.append([n[0], n[1], n[2], -1])
 
      self.nm = 0
      
      # Starting the udpClient and the tcpServer.
      self.udpClient = UDPClient(self.dest)
      self.tcp_queue = Queue.Queue()
      self.tcpServer = TCPServer(self.src, self.tcp_queue)
      self.tcpServer.start()
      self.ON = self.tcpServer.isAlive() and self.udpClient.isAlive()
      
   def close(self):
      print 'Shutting down...'
      self.udpClient.close()
      self.tcpServer.close()
      self.tcpServer.join()
      self.ON = self.tcpServer.isAlive() and self.udpClient.isAlive()
      print 'Closed.'
      
   def isAlive(self):
      return self.ON
      
   # This method waits for an incoming TCP packet and a specific payload_type.
   # It returns the payload attributes if any.
   def wait(self, addr, payload_type):
      while self.isAlive():
         try:
            p, src = self.tcp_queue.get(True, Sender.expiration)
            if src == addr and p[0] == payload_type:
               return p[1]
            else:
               self.tcp_queue.put((p, src))
         except Queue.Empty:
            self.ON = self.tcpServer.isAlive()
      raise Exception()

   # Based on an IP address, returns the index of the neighbour.
   # -1 if it does not belong to the list of neighbours.
   def isNeighbour(self, addr):
      for k in range(len(self.cN)):
         if addr == self.cN[k][0]:
            return k
      return -1
      
   # Based on an IP address, returns the index of the source.
   # -1 if it does not belong to the list of sources.
   def isSource(self, addr):
      for k in range(len(self.sources)):
         if addr == self.sources[k][0]:
            self.sources[k]
      return None
   
   # Gathers the TCP messages from the TCP queue. If the sender 
   # is not a neighbour, a 'prune' message is replied.
   def flush_queue(self):
      msgs = []
      try:
         while True:
             p, addr = self.tcp_queue.get(False)
             src = self.isNeighbour(addr)
             if src != -1:
                msgs.append((src, p))
             elif p[0] == 'prune':
                src = self.isSource(addr)
                if src:
                   self.cN.add((src[0], src[1], p[1][0], -1))
                   self.sig = self.updateSigma()
      finally:
         return msgs

   # Encapsulation of the TCPClient send method.
   def notify(self, dest, payload_type, attr = None):
      self.nm += 1
      print dest, payload_type
      return TCPClient.send(dest, payload_type, attr)

   # Notifies all the neighbours.
   def notifyAll(self, payload_type, attr = None):
      ack = True
      for cn in self.cN:
         ack = ack and self.notify(cn[0], payload_type, attr)
      return ack
         
   def updateSigma(self):
      self.sig = self.sigma
      for cn in self.cN:
         self.sig = min(self.sig,cn[2])
      self.sig /= (1 + len(self.cN))
      
   def nextGOP(self, j):
      n = 1;
      for i in range(j+1, len(self.vbr)):
         if self.vbr[i][0] == 5:
            break
         else:
            n += 1
      return n
   
   def findIndex(self):
      tmp = self.src.split('.')
      c = int(tmp[len(tmp)-1])
      j = -1
      k = 10
      a = -1
      b = -1
      for i in range(len(self.sources)):
         tmp = self.sources[i][0].split('.')
         x = int(tmp[len(tmp)-1])
         if x > j and x < c:
            j = x
            a = i
         elif x > c and x < k:
            k = x
            b = i
      return a,b
      
   # Main method, running the coordination protocol.
   def run(self, rounds=1):

      a,b = self.findIndex()
         
      if a != -1:
         self.wait(self.sources[a][0], 'turn')
      
      # Pruning the neighbours with sigma.
      self.notifyAll('prune', [self.sigma])

      if b != -1:
         self.notify(self.sources[a][0], 'turn')

      # Waiting for their answer.
      for k in range(len(self.cN)):
         p = self.wait(self.cN[k][0], 'prune')
         self.cN[k][2] = p[0]
   
      # Sigma is computed.
      self.updateSigma()
      print self.cN
      # Opening the connection at the listener side.
      if not self.notify(self.dest, 'init_stream'):
         return
      time.sleep(1)  

      # Initialization of the different parameters.
      max_frame_size = self.base_frame_size
      buffer = 0
      CBR = 0      
      s_tot = 0
      f = 0
      GOP = self.nextGOP(0)
      log = []
      
      # The video is streamed several times.
      for i in range(rounds):
         for j in range(len(self.vbr)):
            t = time.time()
            
            # Switching back to VBR at the end of the GOP.
            if f == GOP:
               f = 0
               GOP = self.nextGOP(j)
               if CBR:
                  CBR = 0
                  
            # Implicit switch to VBR: the frame size is decreased.
            for i in range(len(self.cN)):
               # Implicit: a timeout is given.
               if self.cN[i][3] != -1 and self.cN[i][3] <= t:
                  self.cN[i][3] = -1
                  max_frame_size -= self.cN[i][1]
            
            # Handling incoming messages from neighbours.
            msgs = self.flush_queue()
            for msg in msgs:
               if msg[1][0] == 'switch':
                  self.cN[msg[0]][3] = msg[1][1][0]
                  max_frame_size += self.cN[msg[0]][1]

            # Case 1: If streaming in CBR, stay in CBR.
            if CBR:
               s = self.cbr[j][1]
            # Case 2: the VBR frame is too large, even for the buffer.
            # In this case, switch to CBR instantaneously.
            elif self.vbr[j][1] - max_frame_size > self.sig - buffer:
               CBR = 1
               self.notifyAll('switch', [t + (GOP - f)*Sender.dt])
               s = self.cbr[j][1]
            # Case 3: sending the VBR frame.
            else:
               s = self.vbr[j][1]
            
            # Sending the most appropriate frame.
            self.udpClient.send(s)
            
            # Buffering capacity refreshment.
            buffer += s - max_frame_size
            buffer = max(0, min(self.sig, buffer))

            # Going to the next frame of the GOP.
            f += 1

            # Logging statistics.
            log.append((self.sig, buffer, max_frame_size, s, CBR))
            
            # Waiting for the next frame.
            time.sleep(max(0, Sender.dt - (time.time() - t)))
      
      # Closing the connection at the listener side.
      time.sleep(1)
      if not self.notify(self.dest, 'close_stream'):
         return

      # Waiting for the listener statistics and print them.
      lL = self.wait(self.dest, 'close_ack')
      
      file = open('data%s.txt' % self.src, 'w')
      for l in log:
         file.write('%010.3f %010.3f %010.3f %010.3f %d\n' % l)
      
      print sum(lL[0])/len(lL[0]), 'kbps'
      print sum(lL[1]), 'packets dropped'
      print self.nm, 'messages sent'
      
      file.close()