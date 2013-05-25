==============
singledispatch
==============

`PEP 443 <http://www.python.org/dev/peps/pep-0443/>`_ proposed to expose
a mechanism in the ``functools`` standard library module in Python 3.4
that provides a simple form of generic programming known as
single-dispatch generic functions.

This library is a backport of this functionality to Python 2.6 - 3.3.

To define a generic function, decorate it with the ``@singledispatch``
decorator. Note that the dispatch happens on the type of the first
argument, create your function accordingly::

  >>> from functools import singledispatch
  >>> @singledispatch
  ... def fun(arg, verbose=False):
  ...     if verbose:
  ...         print("Let me just say,", end=" ")
  ...     print(arg)

To add overloaded implementations to the function, use the
``register()`` attribute of the generic function. It takes a type
parameter::

  >>> @fun.register(int)
  ... def _(arg, verbose=False):
  ...     if verbose:
  ...         print("Strength in numbers, eh?", end=" ")
  ...     print(arg)
  ...
  >>> @fun.register(list)
  ... def _(arg, verbose=False):
  ...     if verbose:
  ...         print("Enumerate this:")
  ...     for i, elem in enumerate(arg):
  ...         print(i, elem)

To enable registering lambdas and pre-existing functions, the
``register()`` attribute can be used in a functional form::

  >>> def nothing(arg, verbose=False):
  ...     print("Nothing.")
  ...
  >>> fun.register(type(None), nothing)

The ``register()`` attribute returns the undecorated function which
enables decorator stacking, pickling, as well as creating unit tests for
each variant independently::

  >>> @fun.register(float)
  ... @fun.register(Decimal)
  ... def fun_num(arg, verbose=False):
  ...     if verbose:
  ...         print("Half of your number:", end=" ")
  ...     print(arg / 2)
  ...
  >>> fun_num is fun
  False

When called, the generic function dispatches on the first argument::

  >>> fun("Hello, world.")
  Hello, world.
  >>> fun("test.", verbose=True)
  Let me just say, test.
  >>> fun(42, verbose=True)
  Strength in numbers, eh? 42
  >>> fun(['spam', 'spam', 'eggs', 'spam'], verbose=True)
  Enumerate this:
  0 spam
  1 spam
  2 eggs
  3 spam
  >>> fun(None)
  Nothing.
  >>> fun(1.23)
  0.615

To get the implementation for a specific type, use the ``dispatch()``
attribute::

  >>> fun.dispatch(float)
  <function fun_num at 0x104319058>
  >>> fun.dispatch(dict)
  <function fun at 0x103fe4788>

To access all registered overloads, use the read-only ``registry``
attribute::

  >>> fun.registry.keys()
  dict_keys([<class 'NoneType'>, <class 'int'>, <class 'object'>,
            <class 'decimal.Decimal'>, <class 'list'>,
            <class 'float'>])
  >>> fun.registry[float]
  <function fun_num at 0x1035a2840>
  >>> fun.registry[object]
  <function fun at 0x103170788>

The vanilla documentation is available at
http://docs.python.org/3/library/functools.html#functools.singledispatch.


Versioning
----------

This backport is intended to keep 100% compatibility with the vanilla
release in Python 3.4+. To help maintaining a version you want and
expect, a versioning scheme is used where:

* the first three numbers indicate the version of Python 3.x from which the
  backport is done

* a backport release number is provided after the last dot

For example, ``3.4.0.0`` is the **first** release of ``singledispatch``
compatible with the library found in Python **3.4.0**.

A single exception from the 100% compatibility principle is that bugs
fixed before releasing another minor Python 3.x.y version **will be
included** in the backport releases done in the mean time. This rule
applies to bugs only.


Maintenance
-----------

This backport is maintained on BitBucket by Łukasz Langa, one of the
members of the core CPython team:

* `singledispatch Mercurial repository <https://bitbucket.org/ambv/singledispatch>`_

* `singledispatch issue tracker <https://bitbucket.org/ambv/singledispatch/issues>`_


Change Log
----------

3.4.0.0
~~~~~~~

* the first public release compatible with 3.4.0


Conversion Process
------------------

This section is technical and should bother you only if you are
wondering how this backport is produced. If the implementation details
of this backport are not important for you, feel free to ignore the
following content.

``singledispatch`` is converted using `six
<http://pypi.python.org/pypi/six>`_ so that a single codebase can be
used for all compatible Python versions.  Because a fully automatic
conversion was not doable, I took the following branching approach:

* the ``upstream`` branch holds unchanged files synchronized from the
  upstream CPython repository. The synchronization is currently done by
  manually copying the required code parts and stating from which
  CPython changeset they come from. The tests should pass on Python 3.4
  on this branch.

* the ``default`` branch holds the manually translated version and this
  is where all tests are run for all supported Python versions using
  Tox.
