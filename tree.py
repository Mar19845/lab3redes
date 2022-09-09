import random
import networkx as nx

class Tree():
    def __init__(self, topo, usernames):
        self.Graph = nx.Graph()
        # Adding nodes
        for key, value in usernames["config"].items():
            self.Graph.add_node(key, jid=value)
            
        # Adding edges and assigning different weights
        for key, value in topo["config"].items():
            for i in value:
                weightA = random.uniform(0, 1)
                self.Graph.add_edge(key, i, weight=weightA)
        
    def get_graph(self):
        return self.Graph