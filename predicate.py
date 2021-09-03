import inspect

from stuffs import ComposeFabricBuilder

_PredicateBuilder = ComposeFabricBuilder.with_attributes(
    *{"__cmp__", "__eq__", "__ne__", "__lt__", "__gt__", "__le__", "__ge__", },
    **{attr_name : ComposeFabricBuilder.prune_attr_name(handler)
       for attr_name, handler in {
            "__and__": lambda a, b: a and b,
            "__rand__": lambda a, b: b and a,
            "__or__": lambda a, b: a or b,
            "__ror__": lambda a, b: b or a,
        }.items()
    },
)


class _AbstractPredicate:
    _func = None

    def __init__(self, func):
        self._func = func

    def __call__(self, *args, **kwargs):
        a = self._func(*args, **kwargs)
        return a


@_PredicateBuilder.decorate_fabric
class Predicate(_AbstractPredicate):
    def __call__(self, it, parent):
        return super().__call__(it, parent)


@_PredicateBuilder.decorate_fabric
class PredicateN(_AbstractPredicate):
    def __call__(self, *args):
        return super().__call__(*args)


@_PredicateBuilder.decorate_fabric
class PredicateI(_AbstractPredicate):
    def __call__(self, it):
        return super().__call__(it)


@_PredicateBuilder.decorate_fabric
class PredicateP(_AbstractPredicate):
    def __call__(self, _, parent):
        return super().__call__(parent)


