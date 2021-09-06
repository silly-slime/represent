import functools

"""
@FabricComposer("compose_method")
class Fabric: ...

fabric = Fabric(caller)
value = fabric(caller_args) <=> fabric.caller(caller_args)

derived_fabric = fabric.compose_method(method_args) <=> Fabric(closure caller)
value = derived_fabric(caller_args) <=> fabric.caller(caller_args).compose_method(method_args)
"""


class FabricComposer:
    redirect_handlers = dict()

    class DefaultLabel: pass
    fabric_class_label = DefaultLabel

    @staticmethod
    def default_redirect(_attr_name, _it, *args, **kwargs):
        return getattr(_it, _attr_name)(*args, **kwargs)

    @staticmethod
    def prune_attr_name(redirect_handler):
        return lambda attr_name, it, *args, **kwargs: redirect_handler(it, *args, **kwargs)

    @classmethod
    def is_compose_fabric(cls, a):
        return isinstance(a, cls.fabric_class_label)

    @classmethod
    def unpack_method_args(cls, arg, caller_args, caller_kwargs):
        if cls.is_compose_fabric(arg):
            arg = arg(*caller_args, **caller_kwargs)
        return arg

    @classmethod
    def build_compose_method(cls, fabric_class, attr_name, redirect_handler):
        def fabric_method(self, *method_args, **method_kwargs):
            def fabric_caller(*args, **kwargs):
                _method_args = (cls.unpack_method_args(a, args, kwargs) for a in method_args)
                _method_kwargs = {k: cls.unpack_method_args(a, args, kwargs) for k, a in method_kwargs.items()}
                return redirect_handler(attr_name, self(*args, **kwargs), *_method_args, **_method_kwargs)
            return fabric_class(fabric_caller)
        return fabric_method

    @classmethod
    def build_redirect_handlers(cls, names_default, names_with_handlers):
        return {
            **cls.redirect_handlers,
            **{k: names_with_handlers.get(k, None) or cls.default_redirect
               for k in {*names_default, *names_with_handlers.keys()}}
        }

    @classmethod
    def with_methods(cls, *names_default, **names_with_handlers):
        class _with_methods_(cls):
            redirect_handlers = cls.build_redirect_handlers(names_default, names_with_handlers)
        return _with_methods_

    def __init_subclass__(cls):
        cls.redirect_handlers = cls.redirect_handlers.copy()

    def __init__(self, *names_default, **names_with_handlers):
        if names_default or names_with_handlers:
            self.redirect_handlers = self.build_redirect_handlers(names_default, names_with_handlers)

    def __call__(self, fabric_class):
        @functools.wraps(fabric_class, updated=())
        class _wrap_(fabric_class, self.fabric_class_label):
            pass

        compose_methods = {attr_name: self.build_compose_method(_wrap_, attr_name, handler)
                           for attr_name, handler in self.redirect_handlers.items()}
        for attr_name, method in compose_methods.items():
            setattr(_wrap_, attr_name, method)
        return _wrap_


class colddict(dict):
    def __hash__(self):
        return hash(frozenset((k,v) for k,v in self.items()))