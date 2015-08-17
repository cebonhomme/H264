""" 
Author: Cedric Bonhomme
Date: 26-07-2015

This file contains the implementation of the Listener class, whose job is to 
listen to senders (sender.py) streaming UDP content and reply resulting 
statistics.
"""

import Queue
from tcpmodule import *
from udpmodule import *

class Listener:

   """
   Listener is a class containing two threads, respectively handling incoming 
   TCP and UDP requests. The main method run() handles the communication 
   between those threads.
   """
   
   expiration = 5
   
   def __init__(self, dest):
      self.ON = True
      self.tcp_queue = Queue.Queue()
      self.tcpServer = TCPServer(dest, self.tcp_queue)
      self.udpServer = UDPServer(dest)
      self.tcpServer.start()
      self.udpServer.start()
      
      # The listener is up if its servers are up too.
      self.ON = self.udpServer.isAlive() and self.tcpServer.isAlive()
      
   def close(self):
      self.ON = False
      self.tcpServer.close()
      self.udpServer.close()
      self.tcpServer.join()
      self.udpServer.join()

   def isAlive(self):
      return self.ON
      
   def run(self):
      while self.isAlive():
         try:
            payload, src = self.tcp_queue.get(True, Listener.expiration)

            # Sender at address 'src' starts a UDP measure.
            if payload[0] == 'init_stream':
               self.udpServer.addFlow(src)
               
            # Sender at address 'src' closes its UDP measure.
            # The listener replies with the rho and sigma measure.
            elif payload[0] == 'close_stream':
               self.ON = TCPClient.send(src, 'close_ack', self.udpServer.delFlow(src))

         # Checking periodically if both TCP and UDP servers are still alive.
         except Queue.Empty: 
             self.ON = self.tcpServer.isAlive() and self.udpServer.isAlive()