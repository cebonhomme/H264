#!/usr/bin/python

""" 
Author: Cedric Bonhomme
Date: 26-07-2015

This script launches a Mininet session running the coordination protocol.
The different paths are given in a file in argument. Besides these paths, 
it gives the different H264 videos to stream for the different sources 
(in CBR and VBR mode).
"""

import sys
import time
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import OVSController
from topos import *

if len(sys.argv) != 2:
   print 'Usage: python mininet.py configuration_file '
   exit(0)

setLogLevel('info')   
net = Mininet(topo=LineTopo(2,1), controller = OVSController)
net.start()

def parse_config(path_file):
   paths = []
   try:
      file = open(path_file, 'r')
      for line in file:
         line = line.strip()         
         if not line:
            continue
         
         path = line.split(' ')
         if len(path) != 3:
            raise Exception('Configuration file: missing parameters')

         src = net.getNodeByName(path[0])
         dest = net.getNodeByName(path[1])
         frames = path[2]
         paths.append((src, dest, frames))
         
   except IOError: 
      print 'Cannot open', src
      paths = None
   except Exception, msg:
      print msg
      paths = None
   finally:
      file.close()
      return paths

paths = parse_config(sys.argv[1])
if not paths:
   sys.exit(0)

xterm = 'xterm -hold -e python stream.py'
for i in range(len(paths)):
   b = False
   for j in range(i):
      if paths[i][1].IP() == paths[j][1].IP():
         b = True
         break
   if not b:
      paths[i][1].cmd(xterm + ' --listen %s &' % (paths[i][1].IP()))

for i in range(len(paths)):
   if i < len(paths)-1:
      paths[i][0].cmd(xterm + ' --send %s %s&' % (paths[i][0].IP(), paths[i][2]))
   else:
      paths[i][0].cmd(xterm + ' --send %s %s' % (paths[i][0].IP(), paths[i][2]))
 
net.stop()
sys.exit(0)