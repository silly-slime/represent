from stuffs import ComposeFunctorBuilder, _AbstractComposeFunctor


class _PredicateBuilder(ComposeFunctorBuilder):
    @staticmethod
    def build_functor_method(functor_class, attr_name, handler):
        def functor_method(self, other):
            def functor_caller(*args, **kwargs):
                return handler(
                    attr_name,
                    self(*args, **kwargs),
                    other if not isinstance(other, _AbstractPredicate) else other(*args, **kwargs))
            return functor_class(functor_caller)
        return functor_method

    @classmethod
    def default(cls):
        predicate_defaults = {"__cmp__", "__eq__", "__ne__", "__lt__", "__gt__", "__le__", "__ge__", }
        predicate_handlers = {
            "__and__": lambda a, b: a and b,
            "__rand__": lambda a, b: b and a,
            "__or__": lambda a, b: a or b,
            "__ror__": lambda a, b: b or a,
        }
        return cls.with_attributes(*predicate_defaults, **predicate_handlers)


class _AbstractPredicate(_AbstractComposeFunctor, _PredicateBuilder.default()):
    pass


class Predicate(_AbstractPredicate):
    def __call__(self, it, parent):
        return self._func(it, parent)


class PredicateN(_AbstractPredicate):
    def __call__(self, *args):
        return self._func(*args)


class PredicateI(_AbstractPredicate):
    def __call__(self, it):
        return self._func(it)


class PredicateP(_AbstractPredicate):
    def __call__(self, _, parent):
        return self._func(parent)


