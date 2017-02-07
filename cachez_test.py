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
import os

import time

from cachez import cache, clear_cache, instance_cache, clear_instance_cache, \
    persisted, Persisted, set_persist_folder
from hamcrest import assert_that, equal_to, raises, greater_than, \
    contains_string
from unittest import TestCase

__author__ = 'Cedric Zhuang'


class CacheA(object):
    def __init__(self):
        self.base = 0
        pass

    @cache
    def do(self, a, b):
        return a + b * 2 + self.base

    @cache
    def a(self):
        return self.base

    @cache
    def add_base(self, a):
        return a + self.base

    @staticmethod
    def static():
        pass

    @classmethod
    def clz_method(cls):
        pass


me = 3


@instance_cache
def no_instance_0():
    pass


@clear_instance_cache
def no_instance_1():
    pass


@cache
def cache_me():
    global me
    return me


class CacheB(object):
    def __init__(self):
        self.base = 0
        self.inner_b = self.InnerB()

    @cache
    def do(self, a, b):
        return a + b

    @cache
    def b(self):
        return CacheA().a()

    class InnerB(object):
        def __init__(self):
            self.inner_base = 0

        @instance_cache
        def ib(self):
            return self.inner_base

        @clear_instance_cache
        def clear(self):
            pass


class SelfCacheA(object):
    def __init__(self):
        self.base = 0

    @instance_cache
    def add_base(self, a):
        return a + self.base

    @clear_instance_cache
    def clear_cache(self):
        pass


class CacheTest(TestCase):
    def setUp(self):
        clear_cache()
        self.a = CacheA()
        self.b = CacheB()

    def test_cache(self):
        assert_that(self.a.do(2, 4), equal_to(10))
        self.a.base = 1
        assert_that(self.a.do(2, 4), equal_to(10))

        assert_that(self.b.do(2, 4), equal_to(6))
        self.b.base = 1
        assert_that(self.b.do(2, 4), equal_to(6))

    def test_cache_lock(self):
        assert_that(CacheB().b(), equal_to(0))

    def test_clear_global_function_cache(self):
        assert_that(cache_me(), equal_to(3))
        global me
        me = 5
        # cache hit
        assert_that(cache_me(), equal_to(3))

        # clear cache
        clear_cache()
        assert_that(cache_me(), equal_to(5))

    def test_instance_cache_hit(self):
        sa1 = SelfCacheA()
        assert_that(sa1.add_base(1), equal_to(1))
        sa1.base = 3
        assert_that(sa1.add_base(1), equal_to(1))
        assert_that(sa1.add_base(0), equal_to(3))

    def test_instance_cache_on_instance(self):
        sa1 = SelfCacheA()
        sa1.base = 5
        assert_that(sa1.add_base(1), equal_to(6))
        sa2 = SelfCacheA()
        assert_that(sa2.add_base(1), equal_to(1))

    def test_global_cache_cleared(self):
        self.a.base = 1
        assert_that(self.a.add_base(2), equal_to(3))
        self.a.base = 3
        assert_that(self.a.add_base(2), equal_to(3))
        clear_cache()
        assert_that(self.a.add_base(2), equal_to(5))

    def test_instance_cache_not_cleared(self):
        sa = SelfCacheA()
        sa.base = 1
        assert_that(sa.add_base(2), equal_to(3))
        sa.base = 3
        assert_that(sa.add_base(2), equal_to(3))
        clear_cache()
        assert_that(sa.add_base(2), equal_to(3))

    def test_clear_instance_cache_scope(self):
        sa = SelfCacheA()
        sa.base = 1
        assert_that(sa.add_base(2), equal_to(3))
        sb = SelfCacheA()
        sb.base = 2
        assert_that(sb.add_base(2), equal_to(4))
        sa.base = 5
        sb.base = 6
        # cache hit
        assert_that(sa.add_base(2), equal_to(3))
        assert_that(sb.add_base(2), equal_to(4))
        sa.clear_cache()
        assert_that(sa.add_base(2), equal_to(7))
        assert_that(sb.add_base(2), equal_to(4))

    def test_inner_class_method_cache(self):
        b = CacheB()
        assert_that(b.inner_b.ib(), equal_to(0))

        b.inner_b.inner_base = 5
        assert_that(b.inner_b.ib(), equal_to(0))

        b.inner_b.clear()
        assert_that(b.inner_b.ib(), equal_to(5))

    def test_no_instance_cache(self):
        assert_that(no_instance_0, raises(ValueError, 'not available'))

    def test_no_instance_clear_cache(self):
        assert_that(no_instance_1, raises(ValueError, 'not available'))


class PersistedDemo(object):
    def __init__(self):
        self.base = 1

    @persisted()
    def add(self, x):
        return self.base + x

    @persisted(seconds=0.5)
    def mul(self, x):
        return self.base * x


class PersistedTest(TestCase):
    def setUp(self):
        global call_count
        call_count = 0

    def test_get_file_age(self):
        f = os.path.abspath(__file__)
        delta = Persisted.get_file_age(f)
        assert_that(delta, greater_than(0))

    def test_persisted_valid(self):
        p = PersistedDemo()
        assert_that(p.add(5), equal_to(6))
        assert_that(p.add(6), equal_to(7))

        p.base = 2
        assert_that(p.add(5), equal_to(6))
        assert_that(p.add(6), equal_to(7))

    def test_persisted_expired(self):
        p = PersistedDemo()
        assert_that(p.mul(5), equal_to(5))
        p.base = 2
        assert_that(p.mul(5), equal_to(5))

        time.sleep(1)
        assert_that(p.mul(5), equal_to(10))
        assert_that(p.mul(6), equal_to(12))

    def test_set_persist_folder(self):
        default_folder = Persisted.get_persist_folder()
        assert_that(default_folder, contains_string('.cachez'))

        folder = 'for_test'
        set_persist_folder(folder)
        assert_that(Persisted.get_persist_folder(), equal_to(folder))

        set_persist_folder(default_folder)
