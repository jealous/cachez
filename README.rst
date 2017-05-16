Cache Decorator
===============

.. image:: https://travis-ci.org/jealous/cachez.svg
    :target: https://travis-ci.org/jealous/cachez
    
.. image:: https://coveralls.io/repos/jealous/cachez/badge.svg
    :target: https://coveralls.io/github/jealous/cachez

.. image:: https://img.shields.io/pypi/v/cachez.svg
    :target: https://pypi.python.org/pypi/cachez


VERSION: 0.1.2

Introduction
------------

Function decorator that helps to cache/memoize the result of a function/method.

This package contains following decorators.

- cache: cache the result of the function globally.
- instance_cache: cache the result of a method in the instance (``self``)
- clear_instance_cache: clear the method results cached on the instance.

And one function.

- clear_cache: clear the global function cache.

Tested on python 2.7 and python 3.4.

For quick start, check the tutorial section of this page.
Check `cachez_test.py`_ for detail examples.

Installation
------------

``pip install cachez``


License
-------

`Apache License version 2`_

Tutorial
--------

- To cache the result of the a function globally, decorate the function
  with ``cache``.

.. code-block:: python

    @cache
    def foo(x, y):
        ...


- To clear the global cache, call ``clear_cache()``.

.. code-block:: python

    clear_cache()


- To cache the result of the method in the instance, decorate the method
  with ``instance_cache``.
  To clear the method cache on the instance, decorate your clear method
  with ``clear_instance_cache``.

.. code-block:: python

    class Foo(object):
        @instance_cache
        def bar(a, b):
            ...

        @clear_instance_cache
        def clear():
            ...


- To persist the function return value, use ``persisted`` decorator.
  This decorator takes input parameter which specify when the cache
  will expire.  The default value for cache expiration is set to 1 day.

.. code-block:: python

    class Foo(object):
        @persisted()
        def default_persist_for_1_day(x):
            ...

        @persisted(seconds=5)
        def persist_return_value_for_5_seconds(y):
            ...


- The default persist folder is set to ``~/.cachez``.  You could customize
  it by calling ``set_persist_folder``.


To file issue, please visit:

https://github.com/jealous/cachez


Contact author:

- Cedric Zhuang <jealous@163.com>

Contributors:

- Ryan Liang <menglei.leung@gmail.com>

.. _Apache License version 2: LICENSE.txt
.. _cachez_test.py: cachez_test.py
