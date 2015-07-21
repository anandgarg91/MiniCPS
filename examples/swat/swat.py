"""
Build SWaT testbed with MiniCPS

graph_name functions are used to build networkx graphs representing the
topology you want to build.

mininet_name functions are used to setup mininet configs
eg: preload webservers, enip servers, attacks, ecc...

launcher interacts with MiniCPS topologies module and optionally plot and/or
save a graph representation in the examples/swat folder.

"""

# TODO: check the log files, merge with swat controller

import time
import sys
import os
sys.path.append(os.getcwd())

from minicps.devices import PLC, HMI, DumbSwitch, Histn, Attacker, Workstn, POXSwat
from minicps.links import EthLink
from minicps.topologies import TopoFromNxGraph
from minicps import constants as c

# FIXME: import only necessary data objects
from constants import *  # those are SWaT specific constants
# used to separate different log sessions
logger.debug('----------'+time.asctime()+'----------')

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel

import networkx as nx
import matplotlib.pyplot as plt


def graph_level1(attacker=False):
    """
    SWaT testbed L1 graph + L2 hmi + L3 histn and L3 workstn + optional
    attacker

    :attacker: add an additional Attacker device to the graph

    :returns: graph
    """

    graph = nx.Graph()
    # graph = nx.DiGraph()

    graph.name = 'swat_level1'
    
    # Init switches
    s3 = DumbSwitch('s3')
    graph.add_node('s3', attr_dict=s3.get_params())

    # Init links

    # Create nodes and connect edges
    nodes = {}
    count = 0
    for i in range(1, 7):
        key = 'plc'+str(i)
        nodes[key] = PLC(key, L1_PLCS_IP[key], L1_NETMASK, PLCS_MAC[key])
        graph.add_node(key, attr_dict=nodes[key].get_params())
        link = EthLink(id=str(count), bw=30, delay=0, loss=0)
        graph.add_edge(key, 's3', attr_dict=link.get_params())
        count += 1
    assert len(graph) == 7, "plc nodes error"

    nodes['hmi'] = HMI('hmi', L2_HMI['hmi'], L1_NETMASK, OTHER_MACS['hmi'])
    graph.add_node('hmi', attr_dict=nodes['hmi'].get_params())
    link = EthLink(id=str(count), bw=30, delay=0, loss=0)
    graph.add_edge('hmi', 's3', attr_dict=link.get_params())
    count += 1

    nodes['histn'] = Histn('histn', L3_PLANT_NETWORK['histn'], L1_NETMASK,
            OTHER_MACS['histn'])
    graph.add_node('histn', attr_dict=nodes['histn'].get_params())
    link = EthLink(id=str(count), bw=30, delay=0, loss=0)
    graph.add_edge('histn', 's3', attr_dict=link.get_params())
    count += 1

    nodes['workstn'] = Histn('workstn', L3_PLANT_NETWORK['workstn'], L1_NETMASK,
            OTHER_MACS['workstn'])
    graph.add_node('workstn', attr_dict=nodes['workstn'].get_params())
    link = EthLink(id=str(count), bw=30, delay=0, loss=0)
    graph.add_edge('workstn', 's3', attr_dict=link.get_params())
    count += 1

    if attacker:
        nodes['attacker'] = Attacker('attacker', L1_PLCS_IP['attacker'], L1_NETMASK,
        OTHER_MACS['attacker'])
        graph.add_node('attacker', attr_dict=nodes['attacker'].get_params())
        link = EthLink(id=str(count), bw=30, delay=0, loss=0)
        graph.add_edge('attacker', 's3', attr_dict=link.get_params())
        assert len(graph) == 11, "attacker node error"

    return graph


def mininet_std(net):
    """Launch the miniCPS SWaT simulation"""

    net.start()

    CLI(net)
    # launch device simulation scripts

    net.stop()

def mininet_workshop(net):
    """
    Settings used for the Think-in workshop

    :net: TODO

    """
    pass

def minicps_tutorial(net):
    """
    Settings used for the Think-in workshop

    :net: TODO

    """
    # init the db
    os.system("python examples/swat/state_db.py")
    logger.debug("DB ready")

    net.start()

    plc1, plc2, plc3, hmi = net.get('plc1', 'plc2', 'plc3', 'hmi')

    # Init cpppo enip servers and run main loop
    plc1_pid = plc1.cmd("python examples/swat/plc1.py &")
    plc2_pid = plc2.cmd("python examples/swat/plc2.py &")
    plc3_pid = plc3.cmd("python examples/swat/plc3.py &")
    # hmi_pid = hmi.cmd("python examples/swat/hmi.py &")

    
    CLI(net)
    # launch device simulation scripts

    net.stop()


def laucher(graph, mininet_config, draw_mpl=False, write_gexf=False):
    """
    Launch the miniCPS SWaT simulation
    
    :graph: networkx graph
    :mininet_config: function pointer to the mininet configuration
    :draw_mpl: flag to draw and save the graph using matplotlib
    """

    # TODO: use different color for plcs, switch and attacker
    if draw_mpl:
        nx.draw_networkx(graph)
        plt.axis('off')
        # plt.show()
        plt.savefig("examples/swat/%s.pdf" % graph.name)
    if write_gexf:
        g_gexf = nx.write_gexf(graph, "examples/swat/l1_gexf.xml")
        # g2 = nx.read_gexf("examples/swat/g_gexf.xml")

    # for node in graph.nodes(data=True):
    #     logger.debug( '%s attributes: %s' % (node[0], node[1]))

    # for edge in graph.edges(data=True):
    #     logger.debug( '%s<--->%s  attributes: %s' % (edge[0], edge[1], edge[2]))

    # Build miniCPS topo
    topo = TopoFromNxGraph(graph)
    controller = POXSwat
    net = Mininet(topo=topo, controller=controller, link=TCLink, listenPort=6634)

    mininet_config(net)



if __name__ == '__main__':
    swat_graph = graph_level1(attacker=True)

    nx.write_gexf(swat_graph, "examples/swat/l1_gexf.xml", prettyprint=True)
    rgraph = nx.read_gexf("examples/swat/l1_gexf.xml", relabel=False)

    # laucher(swat_graph, mininet_std, draw_mpl=False)
    laucher(rgraph, minicps_tutorial, draw_mpl=False)