import functools

from stuffs import colddict
from predicate import Predicate


class Represent:
    _predicate = Predicate(lambda: True)

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
            return cls._predicate(rep)
        except Exception:
            if not block_exception or isinstance(rep, cls):
                raise
            return False

    @classmethod
    def with_predicate(cls, predicate, name=""):
        @functools.wraps(cls, updated=())
        class _rep_(cls):
            _predicate = predicate
            __owner_represent__ = getattr(cls, "__owner_represent__", None) or cls

        _rep_.__name__ = name or f"{_rep_.__owner_represent__.__name__}?"
        _rep_.__qualname__ = f"{_rep_.__owner_represent__.__qualname__}" + (f":{name}" if name else "?") # ??? view
        return _rep_

    @classmethod
    def find(cls, space, used=set(), scheme=dict()):
        def tr(a): # silly name
            try:
                return cls(a)
            except IncorrectScheme:
                return None

        return {tr(a) for a in cls._find(space=space, used=used, scheme=scheme)}.difference([None])

    @classmethod
    def _find(cls, space, used=set(), scheme=dict()):
        pattern = cls._pattern()
        if not pattern: return frozenset()

        needs = {k for k in pattern if scheme.get(k, None) is None}
        frees = {a for a in space if a not in used}

        if not needs: return frozenset([colddict(scheme)])
        if not frees: return frozenset()

        finds = {(k, a) for k in needs for a in frees
                 if pattern.get(k).is_correct(a)
                 if not used.intersection(a._inners())} \
            .union({(k, r) for k in needs for a in frees
                    for r in pattern.get(k).find(space={a}, used=used)})

        return frozenset(colddict(a) for k, v in finds for a in cls._find(
            space={*space, *v._outers()},
            used={*used, *v._inners()},
            scheme={**scheme, k: v}
        ))

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
            return super.__hash__(self)
        return hash(colddict(self._scheme()))

    def __eq__(self, other):
        if not self._scheme():
            return super.__eq__(self)
        return self._scheme() == other._scheme()

    def _inners(self):
        if not self._scheme():
            raise NotImplementedError
        return {a._inners() for a in self._scheme().items()}

    def _outers(self):
        return functools.reduce(lambda a, b: a.union(b._outers()), self._inners(), set()).difference(self._inners())


class SheetRepresent(Represent):
    def __init__(self):
        pass

    def _inners(self):
        return {self}

    def _outers(self):
        raise NotImplementedError

    @classmethod
    def find(cls, space, used=set(), scheme=dict()):
        return {a for a in space if cls.is_correct(a) if a not in used}


class SubRepresent:
    name = None
    represent_class = None
    owner = None # need? # no...

    def __init__(self, represent_class, cls_predicate=None, own_predicate=None):
        if cls_predicate is not None and not isinstance(cls_predicate, Predicate):
            cls_predicate = Predicate(cls_predicate)
        if own_predicate is not None and not isinstance(own_predicate, Predicate):
            own_predicate = Predicate(own_predicate)

        if cls_predicate is not None:
            represent_class = represent_class.with_predicate(cls_predicate)
        self.represent_class = represent_class
        self._own_predicate = own_predicate  # ?

    def __set_name__(self, owner, name):
        if self._own_predicate is not None:
            owner._predicate = owner._predicate & self._own_predicate
        self.name = name
        self.owner = owner

    def get(self, instance):
        return instance.__dict__.get(self.name)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.get(instance) is None:
            raise NoneSubRepresent(self.name, instance)
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
