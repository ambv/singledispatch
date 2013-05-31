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
    base classes from `haystack`.

    """
    bases = set(cls.__mro__)
    mro = list(cls.__mro__)
    for needle in haystack:
        if (needle in bases or not hasattr(needle, '__mro__')
                            or not issubclass(cls, needle)):
            continue   # either present in the __mro__ already or unrelated
        for index, base in enumerate(mro):
            if not issubclass(base, needle):
                break
        if base in bases and not issubclass(needle, base):
            # Conflict resolution: put classes present in __mro__ and their
            # subclasses first. See test_mro_conflicts() in test_functools.py
            # for examples.
            index += 1
        mro.insert(index, needle)
    return mro

def _find_impl(cls, registry):
    """Returns the best matching implementation for the given class `cls` in
    `registry`. Where there is no registered implementation for a specific
    type, its method resolution order is used to find a more generic
    implementation.

    Note: if `registry` does not contain an implementation for the base
    `object` type, this function may return None.

    """
    mro = _compose_mro(cls, registry.keys())
    match = None
    for t in mro:
        if match is not None:
            # If `match` is an ABC but there is another unrelated, equally
            # matching ABC. Refuse the temptation to guess.
            if (t in registry and not issubclass(match, t)
                              and match not in cls.__mro__):
                raise RuntimeError("Ambiguous dispatch: {0} or {1}".format(
                    match, t))
            break
        if t in registry:
            match = t
    return registry.get(match)

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
    def ns(): pass
    ns.cache_token = None

    def dispatch(typ):
        """generic_func.dispatch(type) -> <function implementation>

        Runs the dispatch algorithm to return the best available implementation
        for the given `type` registered on `generic_func`.

        """
        if ns.cache_token is not None:
            current_token = get_cache_token()
            if ns.cache_token != current_token:
                dispatch_cache.clear()
                ns.cache_token = current_token
        try:
            impl = dispatch_cache[typ]
        except KeyError:
            try:
                impl = registry[typ]
            except KeyError:
                impl = _find_impl(typ, registry)
            dispatch_cache[typ] = impl
        return impl

    def register(typ, func=None):
        """generic_func.register(type, func) -> func

        Registers a new implementation for the given `type` on a `generic_func`.

        """
        if func is None:
            return lambda f: register(typ, f)
        registry[typ] = func
        if ns.cache_token is None and hasattr(typ, '__abstractmethods__'):
            ns.cache_token = get_cache_token()
        dispatch_cache.clear()
        return func

    def wrapper(*args, **kw):
        return dispatch(args[0].__class__)(*args, **kw)

    registry[object] = func
    wrapper.register = register
    wrapper.dispatch = dispatch
    wrapper.registry = MappingProxyType(registry)
    wrapper._clear_cache = dispatch_cache.clear
    update_wrapper(wrapper, func)
    return wrapper

