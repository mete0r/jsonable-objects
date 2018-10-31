# -*- coding: utf-8 -*-
#
#   jsonable-objects: JSON-able objects
#   Copyright (C) 2015-2017 mete0r <mete0r@sarangbang.or.kr>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from unittest import TestCase

from zope.interface import providedBy


class JsonableProxyTest(TestCase):

    def test_proxy(self):
        from jsonable_objects.proxy import JsonableProxy
        from jsonable_objects.interfaces import IJsonable

        d = {
            'foo': 1,
            'bar': 'abc',
        }
        jsonable = JsonableProxy.validate(d)

        self.assertEquals(d, jsonable.__jsonable__)
        self.assertTrue(
            IJsonable in list(providedBy(jsonable))
        )

    def test_repr(self):
        from jsonable_objects.proxy import JsonableProxy

        class Foo(JsonableProxy):
            pass

        foo = Foo({
            'foo': 123,
            'bar': 456,
        })
        self.assertEquals(
            'Foo({"bar": 456, "foo": 123})',
            repr(foo)
        )
