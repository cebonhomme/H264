""" 
Author: Cedric Bonhomme
Date: 19-07-2015

This file contains the different topologies used to test the measurement tool, 
as well as the coordination protocol.
"""

from mininet.topo import Topo
from mininet.link import TCLink

class LineTopo(Topo):
    
    """
    LineTopo is a topology consisting of k hosts attached at the left of 
    a line of n switches. The rightmost switch is connected to another host.
    """

    def __init__(self, k=2, n=1, **opts):
        Topo.__init__(self, **opts)
        
        switch = [None] * n
        hosts = [None] * k
        dest = self.addHost( 'h%s'% (k + 1))
        
        for i in range(n)[::-1]:
           switch[i] = self.addSwitch('s%s'% (i + 1))

           if i == n-1:
              self.addLink(switch[i], dest, cls=TCLink, bw = 2.5, max_queue_size = 1000)
           else:
              self.addLink(switch[i], switch[i+1], cls=TCLink, bw = 100, max_queue_size = 1000)
               
        for i in range(k):
           hosts[i] = self.addHost( 'h%s'% (i + 1))
           self.addLink(hosts[i], switch[0], cls=TCLink, bw = 100, max_queue_size = 1000, delay='100ms')
           
###############################################################################
class CorrelTopo(Topo):
    
    """
    CorrelTopo is a topology consisting of 2n+k hosts and n switches, each pair 
    being linked to a single switch. Switches are connected in line. The k 
    remaining hosts are linked to the extremity of the line.
    """

    def __init__(self, n=1, k=1, **opts):
        Topo.__init__(self, **opts)
        
        switch = [None] * n
        hosts = [None] * 2 * n
        dests = [None] * k
        
        for i in range(n)[::-1]:
           switch[i] = self.addSwitch('s%s'% (i + 1))
           hosts[2*i] = self.addHost( 'h%s'% (2*i + 1))
           hosts[2*i+1] = self.addHost( 'h%s'% (2*i + 2))
           
           self.addLink(switch[i], hosts[2*i], cls=TCLink, bw = 100, max_queue_size = 1000)
           self.addLink(switch[i], hosts[2*i+1], cls=TCLink, bw = 100, max_queue_size = 1000)
           
           if i == n-1:
              for j in range(k):
                 dests[j] = self.addHost( 'h%s'% (2*n + 1 + j))
                 self.addLink(switch[i], dests[j], cls=TCLink, bw = 4, max_queue_size = 500, delay='10ms')
           else:
              self.addLink(switch[i], switch[i+1], cls=TCLink, bw = 2.5, max_queue_size = 500)

###############################################################################
topos = {
   'linetopo': ( lambda: LineTopo() ),
   'correltopo': ( lambda: CorrelTopo() )
}