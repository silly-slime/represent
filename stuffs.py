class ComposeFabricBuilder:
    handlers = dict()

    @staticmethod
    def default_handler(attr_name, it, *args, **kwargs):
        return getattr(it, attr_name)(*args, **kwargs)

    @staticmethod
    def prune_attr_name(handler):
        return lambda attr_name, it, *args, **kwargs: handler(it, *args, **kwargs)

    @staticmethod
    def build_fabric_method(fabric_class, attr_name, handler):
        def fabric_method(self, *handler_args, **handler_kwargs):
            def functor_caller(*args, **kwargs):
                return handler(attr_name, self(*args, **kwargs), *handler_args, **handler_kwargs)
            return fabric_class(functor_caller)
        return fabric_method

    @classmethod
    def with_attributes(cls, *attr_names_default, **attr_handlers):
        class _with_atributes_(cls):
            pass

        handlers = {k: attr_handlers.get(k, None) or cls.default_handler
                    for k in {*attr_names_default, *attr_handlers.keys()}}
        _with_atributes_.handlers = {**cls.handlers, **handlers}
        return _with_atributes_

    @classmethod
    def decorate_fabric(cls, fabric_class):
        handlers = {attr_name: cls.build_fabric_method(fabric_class, attr_name, handler)
                    for attr_name, handler in cls.handlers.items()}
        for attr_name, handler in handlers.items():
            setattr(fabric_class, attr_name, handler)
        return fabric_class

class ComposeFabricsBuilder(ComposeFabricBuilder):
    @staticmethod
    def build_fabric_method(fabric_class, attr_name, handler):
        def fabric_method(self, *handler_args, **handler_kwargs):
            def functor_caller(*args, **kwargs):
                _handler_args = [a if not callable(a) else a(*args, **kwargs) for a in handler_args]
                _handler_kwargs = {k: (a if not callable(a) else a(*args, **kwargs)) for k,a in handler_kwargs.items()}
                return handler(attr_name, self(*args, **kwargs), *_handler_args, **_handler_kwargs)
            return fabric_class(functor_caller)
        return fabric_method
