""" 
Author: Cedric Bonhomme
Date: 19-07-2015

This file contains the implementation of the sender class, which is at the
heart of the measurement tool. Senders are required to communicate between 
them and compute various parameters of the network.
"""

import sys
import time
import Queue
from udpmodule import *
from tcpmodule import *

class Sender:

   """
   A Sender is a program streaming UDP content to its related Listener. It then
   computes various measurements based on statistics of these streams. In order 
   to communicate with other senders and its Listener, a TCP server is attached 
   to catch incoming TCP messages.
   """

   dt = 2
   CBR = 1000
   expiration = 5
   alpha = 0.05
   beta = 1.5
   sleep = 1
   step = 100
   
   def __init__(self, src, dest, s, i):
      self.ON = True
      self.src = src
      self.dest = dest
      self.senders = s
      self.index = i
      self.N = len(self.senders)

      self.tcp_queue = Queue.Queue()
      self.tcpServer = TCPServer(src, self.tcp_queue)
      self.tcpServer.start()
      
      # The sender is alive if its server is alive too.
      self.ON = self.tcpServer.isAlive()
      
   def close(self):
      print 'Shutting down...'
      
      self.tcpServer.close()
      self.tcpServer.join()

      # Values are not computed if an error occurred.
      if not self.isAlive():
         return

      # Logging the results on the corresponding file.        
      file = open(self.src, 'w')
      file.write(self.dest + '\n')

      file.write(str(self.rs1[0]) + ' ' + str(self.rs1[1]) + '\n')
      print 'rho =',  self.rs1[0]
      print 'sigma =', self.rs1[1]
      
      # rho' and rho" do not exist if the sender is alone.
      if self.N != 1:

         file.write(str(self.rs2[0]) + ' ' + str(self.rs2[1]) + '\n')
         print 'rho\' =',  self.rs2[0]
         print 'sigma\' =', self.rs2[1]

         self.rs3.pop(self.index)
         for r in self.rs3:
            file.write(r[0] + ' ' + str(r[1]) + ' ' + str(r[2]) + '\n')
            print 'rho" =', r[1]
            print 'sigma" =', r[2]

      file.close()               
      print 'End of measure: results are available in', self.src
   
   def isAlive(self):
      return self.ON

   # This method waits for an incoming TCP packet and a specific payload_type.
   # It returns the payload attributes if any.
   def wait(self, addr, payload_type):
      while self.ON:
         try:
            p, src = self.tcp_queue.get(True, Sender.expiration)
            if src == addr and p[0] == payload_type:
               return p[1]
            else:
               self.tcp_queue.put((p, src))
         # Closing the blocking operation in case of error.
         except Queue.Empty:
            self.ON = self.tcpServer.isAlive()

      raise Exception()

   # Method sending a stream of bw kbps during dt seconds.
   def send(self, bw, dt):
   
      # Notifying the listener of the creation of a new stream.
      if not TCPClient.send(self.dest, 'init_stream', [bw]):
         raise Exception()
         
      time.sleep(1)
      n = UDPClient.send(self.dest, bw, dt)
      
      if n == -1:
         raise Exception()
      
      print int(bw), 'kbps during', dt, 'seconds =>', UDPPacket.payload_size*n/125, 'kbits'  
            
      time.sleep(1)
      
      # Closing the stream at the listener side.
      if not TCPClient.send(self.dest, 'close_stream'):
         raise Exception()
      
      # Reception of the pair (rho,sigma) from the listener.
      return self.wait(self.dest, 'close_ack')

   # This algorithm computes an estimation for (r, s).
   def primary(self):
      try:

         bw = 1000
         rho = 1000
         
         # Rho: exponential increase on bw,constant dt.
         while abs(float(rho)/float(bw) - 1) < Sender.alpha:
            bw *= 10
            rho, sigma = self.send(bw, Sender.dt)

         r = rho

         # Sigma: exponential increase on dt, constant bw.
         dt = Sender.dt
         sigma = -1
         r_sum = r
         n = 1
         while sigma == -1:
            rho, sigma = self.send(Sender.beta*r, dt)
            dt *= 2
            r_sum += rho
            n += 1
          
         return (r_sum/n), sigma

      except Exception:
         raise Exception()

   # Main method, aiming at computing (r, s), r', and r".
   def run(self):
      try:
         """ First step: computing (r,s) for each sender."""

         # Each source waits for the previous one to finish its work.
         if self.index != 0:
            p = self.wait(self.senders[self.index - 1], 'start')

         # DEBUG: sending packets to avoid early loss in the next bursts.
         if UDPClient.send(self.dest, 600, 1) == -1:
            raise Exception('cannot send debug stream')
         
         # Computing (r,s)
         self.rs1 = self.primary()
         
         # Computing the minimum rho among those of each sender.
         if self.index == 0:
            bw = self.rs1[0]
         else:
            bw = min(p[0], self.rs1[0])
         
         # Finally, sending the start signal to the next sender and 
         # wait for the end signal from the last source.
         if self.index != self.N - 1:
            TCPClient.send(self.senders[self.index + 1], 'start', [bw])
            p = self.wait(self.senders[self.N - 1], 'finish')
            bw = p[0]
         else:
            bw = bw/self.N
            for i in range(self.N-1):
               TCPClient.send(self.senders[i], 'finish', [bw])
               
         # If there is only one sender, the next parts are irrelevant.
         if self.N == 1:
            return
               
         """ Second step: computing r' for each sender."""

         # In this step, sources increase their rate (from min(rho)/N) until 
         # they reach their limit. The sending must be done simultaneously.
         # Moreover, they need to communicate, in order to know when to stop 
         # the measure. The N-1 sender is the master that leads this measure.

         send = True # True if another measurement round must be done.
         stop = False # True if the corresponding sender has reached its limit.
         
         while True:
            # The last sender indicates if yes or no the measure goes on.
            # For the synchronization, it indicates a future time at which all 
            # sources must start to stream. On the other hand, other senders 
            # wait for this message to start.
            if self.index == self.N - 1:
               t = time.time()
               for i in range(self.N - 1):
                  TCPClient.send(self.senders[i], 'continue', [t + Sender.sleep, send])
               time.sleep(Sender.sleep - (time.time() - t))
            else:
               p = self.wait(self.senders[self.N - 1], 'continue')
               send = p[1]
               time.sleep(max(0,p[0] - time.time()))
                  
            # The measurement is done if the signal is false.
            if not send:
               break
               
            # Parameters are computed by streaming during a constant time.
            rho, sigma = self.send(bw, Sender.dt)
            
            # The sender reaches its limit when bw >> rho. Otherwise, the 
            # bandwidth is increased.
            if not stop and abs(float(rho)/float(bw) - 1) < Sender.alpha:
               bw += Sender.step
            else:
               stop = True

            self.rs2 = (rho, sigma)
            
            # At the end of the round, each sender notify the master if 
            # yes or no it has reached its limit. If all sources want to 
            # stop, the measurement ends.
            if self.index == self.N - 1:
               send = not stop
               for i in range(self.N - 1):
                  p = self.wait(self.senders[i], 'stop')
                  send = send or not p[0]
            else:
               TCPClient.send(self.senders[self.N - 1], 'stop', [stop])
         
         """ Third step: computing r" for each pair of senders."""

         # In this step, N different r" are computed, for each sender streaming 
         # at a lower (CBR) rate. The principle is similar to the previous one, 
         # except that the master is the one sending at a constant rate (hence 
         # not increasing its rate.

         # Initialisation of rs3.
         self.rs3 = [None] * self.N

         for i in range(len(self.senders)):

            send = True
            stop = False
            bw = self.rs2[0] # The initial rate is r'.

            # Slaves wait for the round to start.
            if self.index != i:
               self.wait(self.senders[i], 'start')

               while True:
                  p = self.wait(self.senders[i], 'continue')
                  time.sleep(max(0,p[0] - time.time()))

                  if not p[1]:
                     break
                     
                  rho, sigma = self.send(bw, Sender.dt)
                  if not stop and abs(float(rho)/float(bw) - 1) < Sender.alpha:
                     bw += Sender.step
                  else:
                     stop = True

                  self.rs3[i] = (self.senders[i], rho, sigma)

                  TCPClient.send(self.senders[i], 'stop', [stop])

            # The CBR sender is the master of the measurement.
            else:
               if i != 0:
                  self.wait(self.senders[i - 1], 'finish')
                  
               for j in range(len(self.senders)):
                  if i != j:
                     TCPClient.send(self.senders[j], 'start')

               margin = 0
               while True:
                  t = time.time()
                  for j in range(self.N):
                     if i != j:
                        TCPClient.send(self.senders[j], 'continue', [t + Sender.sleep, send])
                  time.sleep(Sender.sleep - (time.time() - t))
               
                  if not send:
                     break
                     
                  # The condition is that the rate must be >= to the CBR rate.
                  rho, sigma = self.send(Sender.CBR + margin, Sender.dt)
                  if rho < Sender.CBR:
                     margin += Sender.step
                  else:
                     stop = True

                  # If all senders are done, the measurement can be finished.
                  send = not stop
                  for j in range(self.N):
                     if i != j:
                        p = self.wait(self.senders[j], 'stop')
                        send = send or not p[0]
               
               # The master notify the next sender for the next round.
               if i != self.N - 1:
                  TCPClient.send(self.senders[self.index + 1], 'finish')

      # Handling errors from wait and send methods.
      except Exception, msg:
         print msg
         self.ON = False