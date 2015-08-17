""" 
Author: Cedric Bonhomme
Date: 19-07-2015

This file contains the implementation of the TCP module, used to handle out of 
band requests, both in senders and listeners.
"""

import socket
import json
from threading import Thread

class TCPPacket:
   
   """
   TCPPacket is a data structure containing a message, together with 0 or more
   attributes. The class is encoded/decoded into json before/after its sending.
   It contains only two static methods.
   """

   @staticmethod
   def encode(type, attr = None):
      return json.dumps((type, attr))

   @staticmethod
   def decode(data):
      p = json.loads(data)
      return(str(p[0]), p[1])

###############################################################################
class TCPServer(Thread):

    """
    TCPServer is a Thread that handles incoming out of band requests.
    """

    port = 5000
    max_connections = 50
    expiration = 3
    
    def __init__(self, addr, q):
       Thread.__init__(self)
       try:
          self.ON = True
          self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          self.s.bind((addr, TCPServer.port))
          self.s.settimeout(TCPServer.expiration)
          self.s.listen(TCPServer.max_connections)
          self.q = q
       except socket.error, msg:
          print 'Socket creation error:', msg
          self.ON = False

    def close(self):
       self.ON = False
       self.s.close()
            
    def isAlive(self):
       return self.ON

    def run(self):
       while self.ON:
          # Incoming packets are put in the queue and the connection is closed.
          try:
             input, addr = self.s.accept()
             self.q.put(self.handle(input, addr[0]))
             input.close()
             
          # The timeout allows to close the server properly.
          except socket.timeout:
             continue
          except socket.error, msg:
             print 'Socket error:', msg
             self.ON = False
             input.close()
    
    # Messages are reconstructed and decoded.
    def handle(self, input, addr):
       data = ''
       while True:
            d = input.recv(1024)
            if d: data += d
            else: return TCPPacket.decode(data), addr

###############################################################################
class TCPClient:

   """
   TCPClient is a class sending out of band messages. It is made of a single 
   static method, sending a string msg to the specified addr.
   """

   @staticmethod
   def send(addr, payload_type, payload_attributes = None):
      try:
         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         s.connect((addr, TCPServer.port))
         s.sendall(TCPPacket.encode(payload_type, payload_attributes))
         ACK = True
      except socket.error, msg:
         print 'Unable to send TCP message:', msg
         ACK = False
      finally:
         s.close()
         return ACK