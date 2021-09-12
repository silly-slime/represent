import functools
import random

import networkx as nx
import matplotlib.pyplot as plt

from represent import SheetRepresent, SubRepresent as SubRep, Represent, RepresentGraph

class NXGraph(RepresentGraph, nx.Graph):

    def draw(self):
        nx.draw(self, node_color=[self.Node(a).color for a in self.nodes()], edge_color=[self.edges()[e].get('color', 'black') for e in self.edges()], with_labels=True)
        plt.show()


    class Node(SheetRepresent):
        G :nx.Graph

        def _set_color(self, color):
            self.G.nodes()[self.it]['color'] = color

        def _get_color(self):
            return self.G.nodes()[self.it].get('color', 'gray')

        color = property(fget=_get_color, fset=_set_color)

        def __repr__(self):
            return f"<{self.it}>"

        def vicinity(self):
            return self._outers()

        def edge(self, other):
            return {e for e in map(G.Edge, self.G.edges(self.it)) if e.incident(other)}

        def edges(self):
            return map(G.Edge, self.G.edges(self.it))

        def _outers(self):
            return {self.__class__(a) for a in self.G.neighbors(self.it)}

        def _graph_value(self):
            return self.it

        def __init__(self, it, neighs=set(), G=None):
            super().__init__(G=G)
            if not self.G.has_node(it):
                self.G.add_node(it)
            if neighs:
                self.G.add_edges_from((it, other) for other in neighs)
            self.it = it

    class Edge(SheetRepresent):
        G: nx.Graph
        def __init__(self, it, G=None):
            super().__init__(G=G)
            a,b = it
            if not self.G.has_edge(a,b):
                self.G.add_edge(a,b)
            self.it = (a,b)

        def _outers(self):
            return {*map(self.G.Node, self.it)}

        def _graph_value(self):
            return self.it

        def _set_color(self, color):
            self.G.edges()[self.it]['color'] = color

        def _get_color(self):
            return self.G.edges()[self.it].get('color', 'gray')

        def incident(self, node):
            return node.it in self.it

        def other_end(self, node):
            a,b = self.it
            return self.G.Node(a) if a != node.it else self.G.Node(b)

        color = property(fget=_get_color, fset=_set_color)

def Vic(*names):
    def f(it):
        _names = [names[i] for i in (*range(len(names)),0)]
        for i in range(len(names)):
            a,b = _names[i], _names[i+1]
            if getattr(it, a) not in getattr(it, b).vicinity():
                return False
        return True
    return f

class Triangle(Represent):
    predicate = Vic("a", "b", "c")

    a = SubRep(NXGraph.Node)
    b = SubRep(NXGraph.Node)
    c = SubRep(NXGraph.Node)

    def setcolor(self, color):
        nodes = self._scheme().values()
        for a in nodes:
            a.color = color
            for b in filter(lambda e: e.other_end(a) in nodes, a.edges()):
                b.color = color

def random_neighs(i):
    a = set()
    r = 2
    while len(a) < r:
        b = random.choice(range(N))
        if b != i and b not in a:
            a.add(b)
    return a

G = NXGraph()
N = 50
for i in range(N):
    G.Node(i, random_neighs(i))

ts = Triangle.find({G.Node(a) for a in G.nodes()})
for t in ts:
    t.setcolor("red")

G.draw()
