#!/usr/bin/python

""" 
Author: Cedric Bonhomme
Date: 19-07-2015

This script launches a Mininet session with the measurement tool.
The different paths are given in a file in argument.
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
   print 'Usage: python mininet.py path_file'
   exit(0)

setLogLevel('info')   
net = Mininet(topo=LineTopo(1,1), controller = OVSController)
net.start()

paths = []
path_file = open(sys.argv[1], 'r')
senders = open('senders', 'w')
for line in path_file:
   if not line.strip(): continue
   path = line.strip().split(' ')
   src = net.getNodeByName(path[0])
   dest = net.getNodeByName(path[1])
   paths.append((src, dest))
   senders.write(src.IP() + '\n')

path_file.close()
senders.close()

for i in range(len(paths)):
   b = False
   for j in range(i):
      if paths[i][1].IP() == paths[j][1].IP():
         b = True
         break
   if not b:
      paths[i][1].cmd('xterm -hold -e python measurement.py --listen %s &' % (paths[i][1].IP()))

for i in range(len(paths)):
   if i < len(paths)-1:
      paths[i][0].cmd('xterm -hold -e python measurement.py --send %s %s senders &' % (paths[i][0].IP(), paths[i][1].IP()))
   else:
      paths[i][0].cmd('xterm -hold -e python measurement.py --send %s %s senders  ' % (paths[i][0].IP(), paths[i][1].IP()))
 
net.stop()
sys.exit(0)