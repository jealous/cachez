# coding=utf-8
# Copyright (c) 2016 EMC Corporation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import unicode_literals

from collections import defaultdict
from datetime import datetime
import functools
import hashlib
import logging
import os
import pickle
import threading

__author__ = 'Cedric Zhuang'

__all__ = ['cache', 'clear_cache',
           'instance_cache', 'clear_instance_cache',
           'persisted', 'set_persist_folder']

log = logging.getLogger(__name__)


def _cache_holder():
    return defaultdict(lambda: {})


def _cache_lock_holder():
    return defaultdict(lambda: threading.Lock())


class Cache(object):
    _cache = _cache_holder()
    _lock_map = _cache_lock_holder()

    @classmethod
    def get_key(cls, func):
        return hash(func)

    @classmethod
    def get_cache(cls, key):
        return cls._cache[key]

    @classmethod
    def clear_cache(cls):
        """ clear all global cache

        :return: None
        """
        cls._cache = _cache_holder()
        cls._lock_map = _cache_lock_holder()

    @classmethod
    def get_cache_lock(cls, key):
        return cls._lock_map[key]

    @staticmethod
    def _hash(li):
        return hash(frozenset(li))

    @classmethod
    def result_cache_key_gen(cls, *args, **kwargs):
        return cls._hash(args), cls._hash(kwargs.items())

    @classmethod
    def _get_value_from_cache(cls, func, val_cache, lock, *args, **kwargs):
        key = cls.result_cache_key_gen(*args, **kwargs)
        if key in val_cache:
            ret = val_cache[key]
        else:
            with lock:
                ret = func(*args, **kwargs)
                val_cache[key] = ret
        return ret

    @classmethod
    def cache(cls, func):
        """ Global cache decorator

        :param func: the function to be decorated
        :return: the decorator
        """

        @functools.wraps(func)
        def func_wrapper(*args, **kwargs):
            func_key = cls.get_key(func)
            val_cache = cls.get_cache(func_key)
            lock = cls.get_cache_lock(func_key)

            return cls._get_value_from_cache(
                func, val_cache, lock, *args, **kwargs)

        return func_wrapper

    @staticmethod
    def get_self_root_cache(the_self):
        prop_name = '_self_cache_'
        if not hasattr(the_self, prop_name):
            setattr(the_self, prop_name, _cache_holder())
        return getattr(the_self, prop_name)

    @classmethod
    def get_self_cache(cls, the_self, key):
        self_root_cache = cls.get_self_root_cache(the_self)
        return self_root_cache[key]

    @staticmethod
    def get_self_cache_lock_map(the_self):
        prop_name = '_self_cache_lock_'
        if not hasattr(the_self, prop_name):
            setattr(the_self, prop_name, _cache_lock_holder())
        return getattr(the_self, prop_name)

    @classmethod
    def get_self_cache_lock(cls, the_self, key):
        lock_map = cls.get_self_cache_lock_map(the_self)
        return lock_map[key]

    @classmethod
    def clear_self_cache(cls, the_self):
        lock_map = cls.get_self_cache_lock_map(the_self)
        lock_map.clear()
        self_root_cache = cls.get_self_root_cache(the_self)
        self_root_cache.clear()

    @classmethod
    def instance_cache(cls, func):
        """ Save the cache to `self`

        This decorator take it for granted that the decorated function
        is a method.  The first argument of the function is `self`.

        :param func: function to decorate
        :return: the decorator
        """

        @functools.wraps(func)
        def func_wrapper(*args, **kwargs):
            if not args:
                raise ValueError('`self` is not available.')
            else:
                the_self = args[0]
            func_key = cls.get_key(func)
            val_cache = cls.get_self_cache(the_self, func_key)
            lock = cls.get_self_cache_lock(the_self, func_key)

            return cls._get_value_from_cache(
                func, val_cache, lock, *args, **kwargs)

        return func_wrapper

    @classmethod
    def clear_instance_cache(cls, func):
        """ clear the instance cache

        Decorate a method of a class, the first parameter is
        supposed to be `self`.
        It clear all items cached by the `instance_cache` decorator.
        :param func: function to decorate
        """

        @functools.wraps(func)
        def func_wrapper(*args, **kwargs):
            if not args:
                raise ValueError('`self` is not available.')
            else:
                the_self = args[0]

            cls.clear_self_cache(the_self)
            return func(*args, **kwargs)

        return func_wrapper


class Persisted(object):
    persist_folder = None

    @classmethod
    def set_persist_folder(cls, folder):
        cls.persist_folder = folder

    @classmethod
    def get_persist_folder(cls):
        if cls.persist_folder:
            ret = cls.persist_folder
        else:
            ret = os.path.join(os.path.expanduser('~'), '.cachez')
        return ret

    @staticmethod
    def get_file_age(filename):
        modified_time = os.path.getmtime(filename)
        modified_time = datetime.fromtimestamp(modified_time)
        current = datetime.now()
        return (current - modified_time).total_seconds()

    @classmethod
    def persisted(cls, seconds=0, minutes=0, hours=0, days=0, weeks=0):
        """ Cache the return of the function for given time.

        Default to 1 day.
        :param weeks: as name
        :param seconds: as name
        :param minutes: as name
        :param hours: as name
        :param days: as name
        :return: return of the function decorated
        """
        days += weeks * 7
        hours += days * 24
        minutes += hours * 60
        seconds += minutes * 60

        if seconds == 0:
            # default to 1 day
            seconds = 24 * 60 * 60

        def get_persisted_file(hash_number):
            folder = cls.get_persist_folder()
            if not os.path.exists(folder):
                os.makedirs(folder)
            return os.path.join(folder, '{}.pickle'.format(hash_number))

        def is_expired(filename):
            if os.path.exists(filename):
                file_age = cls.get_file_age(filename)
                if file_age > seconds:
                    log.debug('persisted cache expired: {}'.format(filename))
                    ret = True
                else:
                    ret = False
            else:
                ret = True
            return ret

        def decorator(func):

            def func_wrapper(*args, **kwargs):
                def _key_gen():
                    string = '{}-{}-{}-{}'.format(
                        func.__module__,
                        func.__name__,
                        args,
                        kwargs.items()
                    )
                    return hashlib.sha256(string.encode('utf-8')).hexdigest()

                key = _key_gen()
                persisted_file = get_persisted_file(key)
                if is_expired(persisted_file):
                    ret = func(*args, **kwargs)
                    with open(persisted_file, 'wb') as f:
                        pickle.dump(ret, f)
                else:
                    with open(persisted_file, 'rb') as f:
                        ret = pickle.load(f)
                return ret

            return func_wrapper

        return decorator


cache = Cache.cache
clear_cache = Cache.clear_cache
instance_cache = Cache.instance_cache
clear_instance_cache = Cache.clear_instance_cache

persisted = Persisted.persisted
set_persist_folder = Persisted.set_persist_folder
