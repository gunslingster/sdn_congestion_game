import networkx as nx
import math
import random
import networkx as nx
import typing

def genGraph(vertices: typing.List[int], edges: typing.List[typing.Tuple[int]]):
    '''Return a graph which is a tuple of vertices and edges'''
    return (vertices, edges)

# The below function is used to represent a fat tree, given input number of ports k
# Returns a list of integer indicies representing verticies, and a list of tuples
# that represent edges
def genFatTree(k: int=4) -> typing.Tuple[typing.List[int], typing.List[typing.Tuple[int, int]]]:
    '''A fat tree is completely determined by k, the number of ports'''

    def genFatTreeCoreSwitch(k: int=4) -> typing.List[int]:
        '''Return a list of core switch indexes for a given number of ports k'''

        core_switches = []
        num_core_switches = int(pow(k/2, 2))
        prefix_id = '10'
        for i in range(num_core_switches):
            core_switch_id = int(prefix_id + str(i))
            core_switches.append(core_switch_id)
        return core_switches

    def genFatTreeAggSwitch(k: int=4) -> typing.List[int]:
        '''Return a list of aggregation switch indexes for a given number of ports k'''

        agg_switches = []
        num_agg_switches = int(k/2) * k
        prefix_id = '20'
        for i in range(num_agg_switches):
            agg_switch_id = int(prefix_id + str(i))
            agg_switches.append(agg_switch_id)
        return agg_switches

    def genFatTreeEdgeSwitch(k: int=4) -> typing.List[int]:
        '''Return a list of edge switch indexes for a given number of ports k'''

        edge_switches = []
        num_edge_switches = int(k/2) * k
        prefix_id = '30'
        for i in range(num_edge_switches):
            edge_switch_id = int(prefix_id + str(i))
            edge_switches.append(edge_switch_id)
        return edge_switches

    def genFatTreeHosts(k: int=4) -> typing.List[int]:
        '''Return a list of host switch indexes for a given number of ports k'''

        hosts = []
        num_hosts = int(k/2) * k * int(k/2)
        prefix_id = '40'
        for i in range(num_hosts):
            host_id = int(prefix_id + str(i))
            hosts.append(host_id)
        return hosts

    def genFatTreePods(k: int, fat_tree_agg_switches: typing.List[int],
            fat_tree_edge_switches: typing.List[int]) -> typing.List[typing.List[int]]:
        '''Return a list of lists, each pod is a list of agg and edge switches'''

        num_pods = k
        # Pod size = number of edge and agg switches in a pod
        pod_size = int(k/2)
        # Start with an empty list of pods
        pods = []
        # Max index to iterate through
        max_index = len(fat_tree_agg_switches)
        i = 0
        while i < max_index:
            pod = []
            for j in range(i, i + pod_size):
                # Need to add pod_size edge and agg switches to a pod
                pod.append(fat_tree_agg_switches[j])
                pod.append(fat_tree_edge_switches[j])
            # Add the pod to the list of pods
            pods.append(pod)
            i += pod_size
        return pods

    def genFatTreeNodes(core_switches: typing.List[int], \
        agg_switches: typing.List[int], edge_switches: typing.List[int], \
        hosts: typing.List[int]) -> typing.List[int]:
        '''Return a list of all nodes in the fat tree network'''

        all_nodes = core_switches + agg_switches + edge_switches + hosts
        return all_nodes

    def genFatTreeEdges(k: int, core_switches: typing.List[int], \
        agg_switches: typing.List[int], edge_switches: typing.List[int], \
        hosts: typing.List[int]) -> typing.List[typing.Tuple[int, int]]:
        '''Return a list of 2-tuples, where each tuple represents an edge'''

        pod_size = int(k/2)
        num_pods = k
        num_core_switches = int(pow(k/2, 2))
        num_agg_switches = int(k/2) * k
        def core_to_agg_edges():
            # All edges connecting core switches to agg switches
            # Each core switch is connected to k pods
            # Each agg switch is connected to k/2 core switches
            edges = []
            # The pod modulus gives us the modulus to start at
            # the first k/2 core switches will be connected to the mod 0 agg switch
            # in each pod, then the next k/2 core switches will be connected to the
            # mod 1 agg switch in each pod, and so on
            pod_modulus = 0
            for i in range(0, num_core_switches, pod_size):
                for x in range(i, i+pod_size):
                    for j in range(pod_modulus, num_agg_switches, pod_size):
                        edges.append((core_switches[x], agg_switches[j]))
                pod_modulus += 1
            return edges
        def pod_edges():
            # All edges connecting agg to edge switches
            # These are the pod connections
            # For each pod, each agg switch is connected to every edge switch
            edges = []
            # Quick and dirty but inefficient way of getting the pod edges
            pods = genFatTreePods(k, agg_switches, edge_switches)
            for pod in pods:
                aggs = [node for node in pod if str(node)[0] == '2']
                es = [node for node in pod if str(node)[0] == '3']
                for agg_switch in aggs:
                    for edge_switch in es:
                        edges.append((agg_switch, edge_switch))
            return edges
        def host_edges():
            # All edges connecting edge switches to hosts
            # Each edge switch is connected to k/2 (pod size) hosts
            edges = []
            host_switch_counter = 0
            for edge_switch in edge_switches:
                for i in range(host_switch_counter, host_switch_counter + pod_size):
                    edges.append((edge_switch, hosts[i]))
                host_switch_counter += pod_size
            return edges
        all_edges = core_to_agg_edges() + pod_edges() + host_edges()
        return all_edges

    core_switches = genFatTreeCoreSwitch(k)
    agg_switches = genFatTreeAggSwitch(k)
    edge_switches = genFatTreeEdgeSwitch(k)
    hosts = genFatTreeHosts(k)
    all_nodes = genFatTreeNodes(core_switches, agg_switches, edge_switches, hosts)
    all_edges = genFatTreeEdges(k, core_switches, agg_switches, edge_switches, hosts)
    return genGraph(all_nodes, all_edges)

def generate_network(k, num_users, vnf_distribution, min_weight, max_weight, capacity):
    '''
    Generate a network with servers and users. Each edge has a weight.
    We use a fat tree network model for the network.
    
    @param k: Number of ports in each switch of the fat tree
    @param num_users: Number of users in the game
    @param vnf_distribution: Probability distrubition (dictionary) to represent vnfs in the network
    @param min_weight: Minimum weight
    @param max_weight: Maximum weight
    @return: A networkx undirected graph
    '''

    def get_users(G, num_users):
        possible_users = [node for node in list(G.nodes) if str(node)[0] == '4']
        return random.sample(possible_users, num_users)

    def get_vnfs(G, vnf_distribution):
        possible_vnfs = [node for node in list(G.nodes) if str(node)[0] != '4']
        vnfs = {}
        for vnf, num_vnf in vnf_distribution.items():
            chosen_vnfs = random.sample(possible_vnfs, num_vnf) 
            vnfs[vnf] = chosen_vnfs
            possible_vnfs = [node for node in possible_vnfs if node not in chosen_vnfs]
        return vnfs

    def assign_weights(G, min_weight, max_weight):
        for edge in G.edges():
            G[edge[0]][edge[1]]['weight'] = random.randrange(min_weight, max_weight)
    
    def assign_capacities(G, capacity):
        for edge in G.edges():
            G[edge[0]][edge[1]]['capacity'] = capacity

    graph_edges = genFatTree(k)[1]
    network = nx.Graph()
    network.add_edges_from(graph_edges)
    assign_weights(network, min_weight, max_weight)
    assign_capacities(network, capacity)
    return network

# def test():
#     generate_network(4, 3, {'firewall': 2, 'load balancer': 3}, 5, 10, 2)
# test()