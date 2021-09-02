

class _AbstractComposeFunctor:
    _func = None

    def __init__(self, func):
        self._func = func

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)


class ComposeFunctorBuilder:
    @staticmethod
    def default_handler(attr_name, it, *args, **kwargs):
        return getattr(it, attr_name)(*args, **kwargs)

    @staticmethod
    def prune_attr_name(handler):
        return lambda attr_name, it, *args, **kwargs: handler(it, *args, **kwargs)

    @staticmethod
    def build_functor_method(functor_class, attr_name, handler):
        def functor_method(self, *handler_args, **handler_kwargs):
            def functor_caller(*args, **kwargs):
                return handler(attr_name, self(*args, **kwargs), *handler_args, **handler_kwargs)
            return functor_class(functor_caller)
        return functor_method

    @classmethod
    def with_attributes(cls, *attr_names_default, _base_cls=_AbstractComposeFunctor, **attr_handlers):
        class _ComposeFunctor(_base_cls):
            pass

        handlers = {k: attr_handlers.get(k, None) or cls.default_handler
                    for k in {*attr_names_default, *attr_handlers.keys()}}
        handlers = {attr_name: cls.build_functor_method(_ComposeFunctor, attr_name, handler)
                    for attr_name, handler in handlers.items()}
        for attr_name, handler in handlers.items():
            setattr(_ComposeFunctor, attr_name, handler)
        return _ComposeFunctor


