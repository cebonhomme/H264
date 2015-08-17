#!/usr/bin/python

""" 
Author: Cedric Bonhomme
Date: 26-07-2015

This file consists of the interface of the coordination tool.
"""

import sys
import time
from sender import Sender
from listener import Listener

# Parsing the file containing the results of the measurement tool.
def parse_params(src):
   params = []
   l = 0
   try:
      file = open(src, 'r')
      
      for line in file:
         line = line.strip()         
         if not line:
            continue
         
         # IP address of the listener.
         if l == 0:
            params.append(line)
         # Pair (rho, sigma).
         elif l == 1:
            tmp = line.split()
            params.append((int(tmp[0]), int(tmp[1])))
         # Rho'.
         elif l == 2:
            params.append(int(line))
         # Rho".
         else:
            tmp = line.split()
            params.append((tmp[0], int(tmp[1])))
            
         l += 1
         
   except IOError: 
      print 'Cannot open', src
      params = None
   finally:
      file.close()
      return params

# Parsing the file containing the list of frame sizes of a video.
def parse_h264(f):
   cbr = []
   vbr = []
   try:
      file = open(f, 'r')

      for line in file:
         line = line.strip()
         if not line:
            continue
         
         tmp = line.split()
         vbr.append((int(tmp[0]), float(tmp[1])))
         cbr.append((int(tmp[2]), float(tmp[3])))
            
      frames = (vbr, cbr)
   except IOError: 
      print 'Cannot open', f
      frames = None
   finally:
      file.close()
      return frames
         
# Sender side.
if len(sys.argv) == 4 and sys.argv[1] == '--send':
   params = parse_params(sys.argv[2])
   frames = parse_h264(sys.argv[3])
   if not params or not frames:
      sys.exit(0)

   print 'Streaming from', sys.argv[2], 'to', params[0]
   time.sleep(1)
   sender = Sender(sys.argv[2], params, frames[1], frames[0])
   if sender.isAlive():
      sender.run(1)
   sender.close()
   
# Listener side.
elif len(sys.argv) == 3 and sys.argv[1] == '--listen':
   print 'Listening at', sys.argv[2]
   listener = Listener(sys.argv[2])
   if listener.isAlive():
      listener.run()
   listener.close()
   
else:
   print 'Wrong usage'
   print 'python stream.py [--send|--listen] addr'
   
sys.exit(0)