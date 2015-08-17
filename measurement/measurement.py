#!/usr/bin/python

""" 
Author: Cedric Bonhomme
Date: 19-07-2015

This file consists in the interface of the measurement tool.
"""

import sys
import time
from sender import Sender
from listener import Listener

# Parse the file containing the IP addresses of all senders.
def parse(f, src):
   senders = []
   index = -1
   
   try:
      file = open(f, 'r')
      for line in file:
         if not line.strip(): continue
         senders.append(line.split()[0])
         if line.split()[0] == src: 
            index = len(senders) - 1
   except IOError: 
      print 'Cannot open', f
      senders = None
      index = -1
      self.ON = False
   finally:
      file.close()
      return senders, index

if len(sys.argv) == 5 and sys.argv[1] == '--send':
   print 'Starting the measurement tool from', sys.argv[2], 'to', sys.argv[3]
   time.sleep(1)
   
   senders, index = parse(sys.argv[4], sys.argv[2])
   if index == -1:
      sys.exit(0)
   
   sender = Sender(sys.argv[2], sys.argv[3], senders, index)
   if sender.isAlive():
      sender.run()
   sender.close()
   
elif len(sys.argv) == 3 and sys.argv[1] == '--listen':
   print 'Listening at', sys.argv[2]
   listener = Listener(sys.argv[2])
   if listener.isAlive():
      listener.run()
   listener.close()
   
else:
   print 'python measurement.py [--send|--listen] addr'

sys.exit(0)