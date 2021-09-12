import inspect
from stuffs import FabricComposer

PredicateComposer = FabricComposer(
    *{"__cmp__", "__eq__", "__ne__", "__lt__", "__gt__", "__le__", "__ge__", },
    **{attr_name: FabricComposer.prune_attr_name(handler)
       for attr_name, handler in {
           "__and__": lambda a, b: a and b,
           "__rand__": lambda a, b: b and a,
           "__or__": lambda a, b: a or b,
           "__ror__": lambda a, b: b or a,

           "__iand__": lambda a, b: a and b,
           "__ior__": lambda a, b: a or b,
       }.items()
       },
)


@PredicateComposer
class Predicate:
    _func = None
    _args_count = 0
    _args_exist = False

    def wrapped_func(self):
        f = self._func
        while isinstance(f, Predicate):
            print(f)
            f = f._func
        return f

    def __new__(cls, func):
        return func if isinstance(func, Predicate) else super().__new__(cls)

    def __init__(self, func):
        if isinstance(func, Predicate):
            return
        p = inspect.signature(func).parameters
        self._func = func
        self._args_count = len(p)
        self._args_exist = any(a.kind == a.VAR_POSITIONAL for a in p.values())

    def __call__(self, *args):
        if not self._args_exist:
            args = args[:self._args_count]
        return self._func(*args)


PTrue = Predicate(lambda: True)
