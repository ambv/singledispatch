#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__all__ = ['singledispatch']

from functools import update_wrapper
from weakref import WeakKeyDictionary
from singledispatch_helpers import MappingProxyType, get_cache_token

################################################################################
### singledispatch() - single-dispatch generic function decorator
################################################################################

def _compose_mro(cls, haystack):
    """Calculates the MRO for a given class `cls`, including relevant abstract
    base classes from `haystack`."""
    bases = set(cls.__mro__)
    mro = list(cls.__mro__)
    for regcls in haystack:
        if regcls in bases or not issubclass(cls, regcls):
            continue   # either present in the __mro__ already or unrelated
        for index, base in enumerate(mro):
            if not issubclass(base, regcls):
                break
        if base in bases and not issubclass(regcls, base):
            # Conflict resolution: put classes present in __mro__ and their
            # subclasses first. See test_mro_conflicts() in test_functools.py
            # for examples.
            index += 1
        mro.insert(index, regcls)
    return mro

def singledispatch(func):
    """Single-dispatch generic function decorator.

    Transforms a function into a generic function, which can have different
    behaviours depending upon the type of its first argument. The decorated
    function acts as the default implementation, and additional
    implementations can be registered using the 'register()' attribute of
    the generic function.

    """
    registry = {}
    dispatch_cache = WeakKeyDictionary()
    cache_token = None

    def dispatch(cls):
        """generic_func.dispatch(type) -> <function implementation>

        Runs the dispatch algorithm to return the best available implementation
        for the given `type` registered on `generic_func`.

        """
        if cache_token is not None:
            mro = _compose_mro(cls, registry.keys())
            match = None
            for t in mro:
                if not match:
                    if t in registry:
                        match = t
                    continue
                if (t in registry and not issubclass(match, t)
                                  and match not in cls.__mro__):
                    # `match` is an ABC but there is another unrelated, equally
                    # matching ABC. Refuse the temptation to guess.
                    raise RuntimeError("Ambiguous dispatch: {} or {}".format(
                        match, t))
                return registry[match]
        else:
            for t in cls.__mro__:
                if t in registry:
                    return registry[t]
        return func

    def wrapper(*args, **kw):
        nonlocal cache_token
        if cache_token is not None:
            current_token = get_cache_token()
            if cache_token != current_token:
                dispatch_cache.clear()
                cache_token = current_token
        cls = args[0].__class__
        try:
            impl = dispatch_cache[cls]
        except KeyError:
            impl = dispatch_cache[cls] = dispatch(cls)
        return impl(*args, **kw)

    def register(typ, func=None):
        """generic_func.register(type, func) -> func

        Registers a new overload for the given `type` on a `generic_func`.

        """
        nonlocal cache_token
        if func is None:
            return lambda f: register(typ, f)
        registry[typ] = func
        if cache_token is None and hasattr(typ, '__abstractmethods__'):
            cache_token = get_cache_token()
        dispatch_cache.clear()
        return func

    registry[object] = func
    wrapper.register = register
    wrapper.dispatch = dispatch
    wrapper.registry = MappingProxyType(registry)
    update_wrapper(wrapper, func)
    return wrapper

