import functools

from stuffs import colddict, scheme_search
from predicate import Predicate


class Represent:
    predicate = Predicate(lambda: True)

    __owner_with_predicate__ = None

    @classmethod
    def _subreps(cls):
        return {a for a in map(lambda a: getattr(cls, a), dir(cls)) if isinstance(a, SubRepresent)}

    @classmethod
    def _pattern(cls):
        return {a.name: a.represent_class for a in cls._subreps()}

    def _scheme(self):
        return {a.name: a.get(self) for a in self._subreps()}

    @classmethod
    def is_correct(cls, rep, block_exception=True):
        try:
            return cls.predicate(rep)
        except Exception:
            if block_exception and not getattr(cls, "_debug_", False):
                return False
            raise

    @classmethod
    def is_correct_scheme(cls, scheme):
        try:
            cls(scheme)
            return True
        except IncorrectScheme:
            return False

    @classmethod
    def with_predicate(cls, _predicate, name=""):
        @functools.wraps(cls, updated=())
        class _with_(cls):
            predicate = _predicate
            __owner_with_predicate__ = getattr(cls, "__owner_with_predicate__", None) or cls

        _with_.__name__ = name or f"{_with_.__owner_with_predicate__.__name__}?"
        _with_.__qualname__ = f"{_with_.__owner_with_predicate__.__qualname__}" + (f":{name}" if name else "?")
        return _with_

    @classmethod
    def find(cls, space, used=set()):
        return {a['self'] for a in scheme_search(pattern={"self": cls}, space=space, used=used)}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.predicate = Predicate(cls.predicate)

    def __init__(self, scheme=dict(), **kwscheme):
        _scheme = {k: v for k, v in {**scheme, **kwscheme}.items() if k in self._pattern()}
        nofields = {k for k in self._pattern() if k not in _scheme}
        if nofields:
            raise IncompleteScheme(_scheme, nofields, self, (scheme, kwscheme))

        for k, v in _scheme.items():
            getattr(self.__class__, k).set(self, v)
        if not self.__class__.is_correct(self): # .class??
            raise IncorrectScheme

    def __hash__(self):
        if not self._scheme():
            return super().__hash__(self)
        return hash(colddict(self._scheme()))

    def __eq__(self, other):
        if not self._scheme() or not hasattr(other, "_scheme"):
            return super().__eq__(self, other)
        return self._scheme() == other._scheme()

    def _inners(self):  # empty scheme => ?
        return {b for a in self._scheme().values() for b in a._inners()}

    def _outers(self):
        return functools.reduce(set.union, (a._outers() for a in self._inners()), set()).difference(self._inners())


class SubRepresent:
    name = None
    owner = None
    represent_class = None

    def __init__(self, represent_class, add_predicate=None):
        if add_predicate is not None:
            represent_class = represent_class.with_predicate(add_predicate)
        self.represent_class = represent_class

    def __set_name__(self, owner, name):
        self.name = name
        self.owner = owner

    def get(self, instance):
        return instance.__dict__.get(self.name)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.get(instance)

    def set(self, instance, value):
        if not self.represent_class.is_correct(value):
            raise WrongSubRepresent(value, self.represent_class, self.name, instance)
        instance.__dict__[self.name] = value

    def __set__(self, instance, value):
        oldvalue = self.get(instance)
        self.set(instance, value)
        if not self.owner.is_correct(instance):
            self.set(instance, oldvalue)
            raise IncorrectScheme()

class RepresentGraph:

    @classmethod
    def unwrap_represent_args(cls, func):
        def unwrap(arg: SheetRepresent):
            return arg._graph_value() if isinstance(arg, SheetRepresent) else arg

        @functools.wraps(func)
        def wrap(*args, **kwargs):
            return func(
                *(unwrap(a) for a in args),
                **{k: unwrap(v) for k, v in kwargs.items()}
            )

        return wrap

    def __init__(self):
        super().__init__()
        for name, sheet in ((k, getattr(self,k)) for k in dir(self) if hasattr(self, k)):
            if isinstance(sheet, type) and issubclass(sheet, SheetRepresent):
                setattr(self, name, sheet.with_graph(self))

    def __getattribute__(self, item):
        a = super().__getattribute__(item)
        if callable(a) and not isinstance(a, type) and item != "unwrap_represent_args":
            a = self.unwrap_represent_args(a)
        return a


class SheetRepresent(Represent):
    G = None

    __owner_with_graph__ = None

    def __init__(self, G=None):
        if G is not None:
            self.G = G

    @classmethod
    def with_graph(cls, _G):
        @functools.wraps(cls, updated=())
        class _with_(cls):
            G = _G
            __owner_with_graph__ = getattr(cls, "__owner_with_predicate__", None) or cls
        _with_.__name__ = f"{_with_.__owner_with_graph__.__name__} with {_G}"
        _with_.__qualname__ = f"{_with_.__owner_with_graph__.__qualname__} with {_G}"
        return _with_

    def _inners(self):
        return {self}

    def _outers(self):
        raise NotImplementedError

    def _graph_value(self):  # name # id in graph
        raise NotImplementedError

    def __hash__(self):
        return hash(self._graph_value())

    def __eq__(self, other):
        return hasattr(other, "_graph_value") and self._graph_value() == other._graph_value()

    @classmethod
    def find(cls, space, used=set(), scheme=dict()):
        return {a for a in space if cls.is_correct(a) if a not in used}

    @classmethod
    def is_correct_scheme(cls):
        return False


# strange
def _safe_repr(obj):
    try:
        return repr(obj)
    except:
        pass
    try:
        return str(obj)
    except:
        pass
    return f"<cant get repr or str>"


class IncorrectScheme(ValueError):
    pass

# this is not how exceptions are called

class IncompleteScheme(ValueError):
    def __init__(self, scheme, nofields, rep=None, related_data=None, message=""):
        if not message: \
                message = f"\nincomplete scheme: {scheme}" \
                          f"\nno fields: {nofields}" \
                          f"\nin: {_safe_repr(rep) if rep is not None else '?'}" \
                          f"\ntype: {type(rep) if rep is not None else '?'}" \
                          f"\nadditionally: {related_data}"
        super().__init__(message)


class NoneSubRepresent(NameError):
    def __init__(self, attr_name, rep, message=""):
        if not message:
            message = f"\nnone subrepresent: attribute {attr_name}" \
                      f"\nin {_safe_repr(rep)}" \
                      f"\ntype {type(rep)}"
        super().__init__(message)


class WrongSubRepresent(ValueError):
    def __init__(self, value, rep_class, attr_name=None, rep=None, message=""):
        if not message:
            message = f"\nwrong subrepresent: {value} of {rep_class}" \
                      f"\nin attribute: {attr_name if attr_name else '?'} of {type(rep) if rep is not None else '?'}" \
                      f"\nin instance: {_safe_repr(rep) if rep is not None else '?'}"
            try:
                rep_class.is_correct(value, block_exception=False)
            except Exception as e:
                message += f"\nwith exception: {e}"
        super().__init__(message)
