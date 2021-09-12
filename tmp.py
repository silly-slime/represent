import functools
import random

import networkx as nx
import matplotlib.pyplot as plt

from represent import SheetRepresent, SubRepresent as SubRep, Represent

class RepresentGraph:
    def __init__(self):
        super().__init__()

        for name, attr in self.__class__.__dict__.items(): # in superclass?
            if isinstance(attr, type) and issubclass(attr, SheetRepresent):
                @functools.wraps(attr, updated=())
                class _wrap_(attr):
                    G=self
                setattr(self, name, _wrap_)

    @staticmethod
    def no_remove_rep(func):
        setattr(func, "__remove_rep__", False)
        return func

    @staticmethod
    def remove_rep_wrap(v, method_name=""):
        if isinstance(v, SheetRepresent):
            return v._graph_value()
        return v

    @classmethod
    def remove_rep_args(cls, func, name=None):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            return func(
                *(cls.remove_rep_wrap(a, name or func.__name__) for a in args),
                **{k: cls.remove_rep_wrap(v, name or func.__name__) for k, v in kwargs.items()}
            )
        return wrap

    def __getattribute__(self, item):
        a = super().__getattribute__(item)
        if callable(a) and getattr(a, "__remove_rep__", True) and item != "remove_rep_args":
            a = self.remove_rep_args(a, item)
        return a

class NXGraph(RepresentGraph, nx.Graph):

    def __init__(self):
        super().__init__()

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

def Vic(*names):
    def f(it):
        _names = [names[i] for i in (*range(len(names)),0)]
        for i in range(len(names)):
            a,b = _names[i], _names[i+1]
            if getattr(it, a) not in getattr(it, b).vicinity():
                return False
        return True
    return f

def All(p, *names):
    def f(it):
        return all(p(getattr(it, a)) for a in names)
    return f

class Triangle(Represent):
    #_debug_ = True
    _predicate = Vic("a", "b", "c")

    a = SubRep(NXGraph.Node)
    b = SubRep(NXGraph.Node)
    c = SubRep(NXGraph.Node)

    def setcolor(self, color):
        nodes = self._scheme().values()
        for a in nodes:
            a.color = color

        for a,b in {(a,b) for a in nodes for b in nodes if a != b}:
            a.G:nx.Graph
            a.G.edges()[(a.it, b.it)]['color'] = color

G = NXGraph()
N = 60

def f(i):
    a = []
    while len(a) != 2:
        b = random.choice(range(N))
        if b != i and b not in a:
            a = [*a, b]
    return a

for i in range(N):
    n = set()
    G.Node(i, f(i))

nodes = {G.Node(a) for a in G.nodes()}
ts = set()
for node in nodes:
    ts = {*ts, *Triangle.find({node})}
for t in ts:
    t.setcolor("pink")

G.draw()