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
from uuid import UUID

from zope.interface import implementer
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

    def test_decorator(self):
        from jsonable_objects.interfaces import IJsonable
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            ''' Foo '''

            id = Field()

        self.assertEquals(' Foo ', Foo.__doc__)
        self.assertEquals(__name__, Foo.__module__)

        @proxy(dict)
        class Bar(object):
            foo = Field(key='foo-in-bar', proxy=Foo)

        @proxy(list)
        class Qux(object):
            foo = Field(proxy=Foo)
            bar = Field(proxy=Bar)

        root = [{
            'id': 123,
        }, {
            'foo-in-bar': {
                'id': 456,
            },
        }]

        qux = Qux(root)

        self.assertTrue(
            IJsonable in list(providedBy(qux))
        )
        self.assertTrue(
            qux.__jsonable__ is root
        )
        self.assertEquals(
            qux, Qux(root)
        )
        self.assertEquals(
            'Qux(foo=Foo(id=123), bar=Bar(foo=Foo(id=456)))',
            repr(qux),
        )

        self.assertTrue(
            IJsonable in list(providedBy(qux.foo))
        )
        self.assertTrue(
            qux.foo.__jsonable__ is root[0]
        )
        self.assertEquals(123, qux.foo.id)

        self.assertTrue(
            IJsonable in list(providedBy(qux.bar))
        )
        self.assertTrue(
            qux.bar.__jsonable__ is root[1]
        )

        self.assertTrue(
            IJsonable in list(providedBy(qux.bar.foo))
        )
        self.assertTrue(
            qux.bar.foo.__jsonable__ is root[1]['foo-in-bar']
        )
        self.assertEquals(456, qux.bar.foo.id)

        self.assertRaises(KeyError, Foo, {})


class ProxyForDictTest(TestCase):

    def test_jsonable(self):
        from jsonable_objects.interfaces import IJsonable
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            bar = Field()

        d = {
            'bar': 123,
        }

        self.assertTrue(
            IJsonable in list(providedBy(Foo(d)))
        )
        self.assertTrue(
            Foo(d).__jsonable__ is d
        )

    def test_basic(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            bar = Field()

        self.assertRaises(TypeError, Foo, [])
        self.assertRaises(KeyError, Foo, {})

        d = {
            'bar': None,
        }
        self.assertRaises(TypeError, Foo, d)

        d = {
            'bar': 123,
        }
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        foo.bar = 456
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d['bar'])
        self.assertRaises(TypeError, setattr, foo, 'bar', None)
        self.assertRaises(AttributeError, delattr, foo, 'bar')

    def test_optional(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            bar = Field(optional=True)

        d = {
        }
        foo = Foo(d)
        self.assertEquals(None, foo.bar)
        foo.bar = 123
        self.assertEquals(123, foo.bar)
        self.assertEquals(123, d['bar'])

        self.assertEquals(123, foo.bar)
        foo.bar = 456
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d['bar'])
        foo.bar = None
        self.assertEquals(None, foo.bar)
        self.assertEquals(None, d['bar'])
        del foo.bar
        self.assertEquals(None, foo.bar)
        self.assertTrue('bar' not in d)
        del foo.bar
        self.assertEquals(None, foo.bar)
        self.assertTrue('bar' not in d)

    def test_type_int(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            bar = Field(type=int)

        d = {
        }
        self.assertRaises(KeyError, Foo, d)

        d = {
            'bar': None,
        }
        self.assertRaises(TypeError, Foo, d)

        d = {
            'bar': 123,
        }
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        foo.bar = 456
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d['bar'])
        try:
            long
        except NameError:
            long = int
        foo.bar = long(456)
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d['bar'])

        d = {
            'bar': 123.1,
        }
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', 456.1)

        d = {
            'bar': '123',
        }
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', '456')

    def test_type_int_optional(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            bar = Field(type=int, optional=True)

        d = {
        }
        foo = Foo(d)
        self.assertEquals(None, foo.bar)

        d = {
            'bar': None,
        }
        foo = Foo(d)
        self.assertEquals(None, foo.bar)

        d = {
            'bar': 123,
        }
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        foo.bar = 456
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d['bar'])

        d = {
            'bar': 123.1,
        }
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', 456.1)

        d = {
            'bar': '123',
        }
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', '456')

        foo.bar = None
        self.assertEquals(None, foo.bar)
        self.assertEquals(None, d['bar'])

        del foo.bar
        self.assertEquals(None, foo.bar)
        self.assertTrue('bar' not in d)

    def test_type_float(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            bar = Field(type=float)

        d = {
        }
        self.assertRaises(KeyError, Foo, d)

        d = {
            'bar': 123.1,
        }
        foo = Foo(d)
        self.assertEquals(123.1, foo.bar)
        foo.bar = 456.1
        self.assertEquals(456.1, foo.bar)
        self.assertEquals(456.1, d['bar'])

        d = {
            'bar': 123,
        }
        foo = Foo(d)
        self.assertEquals(123.0, foo.bar)
        foo.bar = 456
        self.assertTrue(isinstance(foo.bar, float))
        self.assertEquals(456.0, foo.bar)
        self.assertEquals(456.0, d['bar'])

        d = {
            'bar': '123.1',
        }
        foo = Foo(d)
        self.assertEquals(123.1, foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', '456')

    def test_type_str(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            bar = Field(type=str)

        d = {
        }
        self.assertRaises(KeyError, Foo, d)

        d = {
            'bar': '123',
        }
        foo = Foo(d)
        self.assertEquals('123', foo.bar)
        foo.bar = '456'
        self.assertEquals('456', foo.bar)
        self.assertEquals('456', d['bar'])

        d = {
            'bar': 123,
        }
        foo = Foo(d)
        self.assertEquals('123', foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', 456)

        d = {
            'bar': 123.1,
        }
        foo = Foo(d)
        self.assertEquals('123.1', foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', 456.1)

    def test_type_dict(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Bar(object):
            id = Field(type=int)

        @proxy(dict)
        class Foo(object):
            bar = Field(type=dict)

        d = {
        }
        self.assertRaises(KeyError, Foo, d)

        d = {
            'bar': 'bar',
        }
        self.assertRaises(TypeError, Foo, d)

        d = {
            'bar': {
                'id': 1,
            },
        }
        foo = Foo(d)
        self.assertTrue(foo.bar is d['bar'])
        b = {
            'id': 2,
        }
        foo.bar = b
        self.assertTrue(b is foo.bar)
        self.assertTrue(b is d['bar'])

        self.assertRaises(TypeError, setattr, foo, 'bar', 123)
        self.assertRaises(TypeError, setattr, foo, 'bar', [])

    def test_predicate(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            bar = Field(predicate=lambda value: value >= 0)

        d = {
        }
        self.assertRaises(KeyError, Foo, d)

        d = {
            'bar': 123
        }
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        foo.bar = 456
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d['bar'])
        self.assertRaises(ValueError, setattr, foo, 'bar', -456)

        d = {
            'bar': -123,
        }
        self.assertRaises(ValueError, Foo, d)

    def test_predicate_int(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            bar = Field(type=int, predicate=lambda value: value >= 0)

        d = {
        }
        self.assertRaises(KeyError, Foo, d)

        d = {
            'bar': 123
        }
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        foo.bar = 456
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d['bar'])
        self.assertRaises(ValueError, setattr, foo, 'bar', -456)

        d = {
            'bar': -123,
        }
        self.assertRaises(ValueError, Foo, d)

    def test_format(self):
        from jsonable_objects.interfaces import IFormat
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @implementer(IFormat)
        class UUIDFormat(object):

            def format(self, pyobj):
                return str(pyobj)

            def parse(self, jsonableval):
                return UUID(jsonableval)

        uuidFormat = UUIDFormat()

        @proxy(dict)
        class Foo(object):
            uuid = Field(type=str, format=uuidFormat)

        self.assertRaises(KeyError, Foo, {})

        d = {
            'uuid': '27d861ac-f27e-4ef5-81af-99d2fcd976a6'
        }
        foo = Foo(d)
        self.assertEquals(
            UUID('27d861ac-f27e-4ef5-81af-99d2fcd976a6'),
            foo.uuid,
        )
        uuid = UUID('b827a618-ac92-4de7-a12a-29c457de3000')
        foo.uuid = uuid
        self.assertEquals(uuid, foo.uuid)
        self.assertEquals('b827a618-ac92-4de7-a12a-29c457de3000', d['uuid'])

    def test_proxy_type_mismatch(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            id = Field(type=int)

        self.assertRaises(TypeError, Field, type=int, proxy=Foo)

    def test_proxy_autotype(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            id = Field(type=int)

        foo = Field(proxy=Foo)
        self.assertTrue(foo.type is dict)

    def test_proxy(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Bar(object):
            id = Field(type=int)

        @proxy(dict)
        class Foo(object):
            bar = Field(type=dict, proxy=Bar)

        d = {
        }
        self.assertRaises(KeyError, Foo, d)

        d = {
            'bar': {
                'id': 1,
            },
        }
        foo = Foo(d)
        self.assertEquals(1, foo.bar.id)

        b = {
            'id': 2,
        }
        foo.bar = Bar(b)
        self.assertEquals(2, foo.bar.id)
        self.assertTrue(b is d['bar'])

        self.assertRaises(TypeError, setattr, foo, 'bar', 123)
        self.assertRaises(TypeError, setattr, foo, 'bar', [])

    def test_proxy_optional(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Bar(object):
            id = Field(type=int)

        @proxy(dict)
        class Foo(object):
            bar = Field(type=dict, optional=True, proxy=Bar)

        d = {
        }
        foo = Foo(d)
        self.assertEquals(None, foo.bar)

        d = {
            'bar': None,
        }
        foo = Foo(d)
        self.assertEquals(None, foo.bar)

        d = {
            'bar': {
                'id': 1,
            },
        }
        foo = Foo(d)
        self.assertEquals(1, foo.bar.id)

        b = {
            'id': 2,
        }
        foo.bar = Bar(b)
        self.assertEquals(2, foo.bar.id)
        self.assertTrue(b is d['bar'])

        self.assertRaises(TypeError, setattr, foo, 'bar', 123)
        self.assertRaises(TypeError, setattr, foo, 'bar', [])

        foo.bar = None
        self.assertEquals(None, foo.bar)
        self.assertEquals(None, d['bar'])

        del foo.bar
        self.assertEquals(None, foo.bar)
        self.assertTrue('bar' not in d)

    def test_inheritance_incompatible(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            id = Field(type=int)

        try:
            @proxy(list)
            class Bar(Foo):
                pass
        except TypeError:
            pass
        else:
            raise AssertionError('TypeError expected')

    def test_inheritance_single(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Node(object):
            id = Field(type=int)

        @proxy(dict)
        class User(Node):
            name = Field(type=str)

        d = {
            'id': 123,
        }
        node = Node(d)
        self.assertEquals(123, node.id)
        self.assertRaises(KeyError, User, d)

        d = {
            'id': 123,
            'name': 'foo',
        }
        user = User(d)
        self.assertEquals(123, user.id)
        self.assertEquals('foo', user.name)
        user.id = 456
        user.name = 'bar'
        self.assertEquals(456, user.id)
        self.assertEquals('bar', user.name)
        self.assertEquals(456, d['id'])
        self.assertEquals('bar', d['name'])

    def test_inheritance_multi(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Node(object):
            id = Field(type=int)

        @proxy(dict)
        class User(Node):
            name = Field(type=str)

        try:
            @proxy(dict)
            class Content(Node, User):
                content = Field(type=str)
        except TypeError:
            pass
        else:
            raise AssertionError('TypeError expected')


class ProxyForListTest(TestCase):

    def test_jsonable(self):
        from jsonable_objects.interfaces import IJsonable
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Foo(object):
            bar = Field()

        d = [123]

        self.assertTrue(
            IJsonable in list(providedBy(Foo(d)))
        )
        self.assertTrue(
            Foo(d).__jsonable__ is d
        )

    def test_basic(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Foo(object):
            bar = Field()

        self.assertRaises(TypeError, Foo, {})
        self.assertRaises(IndexError, Foo, [])

        d = [None]
        self.assertRaises(TypeError, Foo, d)

        d = [123]
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        foo.bar = 456
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d[0])
        self.assertRaises(TypeError, setattr, foo, 'bar', None)
        self.assertRaises(AttributeError, delattr, foo, 'bar')

    def test_optional(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Foo(object):
            bar = Field(optional=True)

        d = [None]
        foo = Foo(d)
        self.assertEquals(None, foo.bar)
        foo.bar = 123
        self.assertEquals(123, foo.bar)
        self.assertEquals(123, d[0])

        self.assertEquals(123, foo.bar)
        foo.bar = 456
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d[0])
        foo.bar = None
        self.assertEquals(None, foo.bar)
        self.assertEquals(None, d[0])
        del foo.bar
        self.assertEquals(None, foo.bar)
        self.assertEquals(None, d[0])

    def test_type_int(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Foo(object):
            bar = Field(type=int)

        d = []
        self.assertRaises(IndexError, Foo, d)

        d = [None]
        self.assertRaises(TypeError, Foo, d)

        d = [123]
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        foo.bar = 456
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d[0])
        try:
            long
        except NameError:
            long = int
        foo.bar = long(456)
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d[0])

        d = [123.1]
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', 456.1)

        d = ['123']
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', '456')

    def test_type_int_optional(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Foo(object):
            bar = Field(type=int, optional=True)

        self.assertRaises(IndexError, Foo, [])

        d = [None]
        foo = Foo(d)
        self.assertEquals(None, foo.bar)

        d = [123]
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        foo.bar = 456
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d[0])

        d = [123.1]
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', 456.1)

        d = ['123']
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', '456')

        foo.bar = None
        self.assertEquals(None, foo.bar)
        self.assertEquals(None, d[0])

        del foo.bar
        self.assertEquals(None, foo.bar)
        self.assertEquals(None, d[0])

    def test_type_float(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Foo(object):
            bar = Field(type=float)

        self.assertRaises(IndexError, Foo, [])

        d = [123.1]
        foo = Foo(d)
        self.assertEquals(123.1, foo.bar)
        foo.bar = 456.1
        self.assertEquals(456.1, foo.bar)
        self.assertEquals(456.1, d[0])

        d = [123]
        foo = Foo(d)
        self.assertEquals(123.0, foo.bar)
        foo.bar = 456
        self.assertTrue(isinstance(foo.bar, float))
        self.assertEquals(456.0, foo.bar)
        self.assertEquals(456.0, d[0])

        d = ['123.1']
        foo = Foo(d)
        self.assertEquals(123.1, foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', '456')

    def test_type_str(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Foo(object):
            bar = Field(type=str)

        self.assertRaises(IndexError, Foo, [])

        d = ['123']
        foo = Foo(d)
        self.assertEquals('123', foo.bar)
        foo.bar = '456'
        self.assertEquals('456', foo.bar)
        self.assertEquals('456', d[0])

        d = [123]
        foo = Foo(d)
        self.assertEquals('123', foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', 456)

        d = [123.1]
        foo = Foo(d)
        self.assertEquals('123.1', foo.bar)
        self.assertRaises(TypeError, setattr, foo, 'bar', 456.1)

    def test_type_dict(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Bar(object):
            id = Field(type=int)

        @proxy(list)
        class Foo(object):
            bar = Field(type=list)

        self.assertRaises(IndexError, Foo, [])

        d = ['bar']
        self.assertRaises(TypeError, Foo, d)

        d = [[1]]
        foo = Foo(d)
        self.assertTrue(foo.bar is d[0])
        b = [2]
        foo.bar = b
        self.assertTrue(b is foo.bar)
        self.assertTrue(b is d[0])

        self.assertRaises(TypeError, setattr, foo, 'bar', 123)
        self.assertRaises(TypeError, setattr, foo, 'bar', {})

    def test_predicate(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Foo(object):
            bar = Field(predicate=lambda value: value >= 0)

        self.assertRaises(IndexError, Foo, [])

        d = [123]
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        foo.bar = 456
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d[0])
        self.assertRaises(ValueError, setattr, foo, 'bar', -456)

        d = [-123]
        self.assertRaises(ValueError, Foo, d)

    def test_predicate_int(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Foo(object):
            bar = Field(type=int, predicate=lambda value: value >= 0)

        self.assertRaises(IndexError, Foo, [])

        d = [123]
        foo = Foo(d)
        self.assertEquals(123, foo.bar)
        foo.bar = 456
        self.assertEquals(456, foo.bar)
        self.assertEquals(456, d[0])
        self.assertRaises(ValueError, setattr, foo, 'bar', -456)

        d = [-123]
        self.assertRaises(ValueError, Foo, d)

    def test_format(self):
        from jsonable_objects.interfaces import IFormat
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @implementer(IFormat)
        class UUIDFormat(object):

            def format(self, pyobj):
                return str(pyobj)

            def parse(self, jsonableval):
                return UUID(jsonableval)

        uuidFormat = UUIDFormat()

        @proxy(list)
        class Foo(object):
            uuid = Field(type=str, format=uuidFormat)

        self.assertRaises(IndexError, Foo, [])

        d = [
            '27d861ac-f27e-4ef5-81af-99d2fcd976a6'
        ]
        foo = Foo(d)
        self.assertEquals(
            UUID('27d861ac-f27e-4ef5-81af-99d2fcd976a6'),
            foo.uuid,
        )
        uuid = UUID('b827a618-ac92-4de7-a12a-29c457de3000')
        foo.uuid = uuid
        self.assertEquals(uuid, foo.uuid)
        self.assertEquals('b827a618-ac92-4de7-a12a-29c457de3000', d[0])

    def test_proxy_type_mismatch(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Foo(object):
            id = Field(type=int)

        self.assertRaises(TypeError, Field, type=int, proxy=Foo)

    def test_proxy_autotype(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Foo(object):
            id = Field(type=int)

        foo = Field(proxy=Foo)
        self.assertTrue(foo.type is list)

    def test_proxy(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Bar(object):
            id = Field(type=int)

        @proxy(list)
        class Foo(object):
            bar = Field(type=list, proxy=Bar)

        self.assertRaises(IndexError, Foo, [])

        d = [[1]]
        foo = Foo(d)
        self.assertEquals(1, foo.bar.id)

        b = [2]
        foo.bar = Bar(b)
        self.assertEquals(2, foo.bar.id)
        self.assertTrue(b is d[0])

        self.assertRaises(TypeError, setattr, foo, 'bar', 123)
        self.assertRaises(TypeError, setattr, foo, 'bar', [])

    def test_proxy_optional(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(list)
        class Bar(object):
            id = Field(type=int)

        @proxy(list)
        class Foo(object):
            bar = Field(type=list, optional=True, proxy=Bar)

        self.assertRaises(IndexError, Foo, [])

        d = [None]
        foo = Foo(d)
        self.assertEquals(None, foo.bar)

        d = [[1]]
        foo = Foo(d)
        self.assertEquals(1, foo.bar.id)

        b = [2]
        foo.bar = Bar(b)
        self.assertEquals(2, foo.bar.id)
        self.assertTrue(b is d[0])

        self.assertRaises(TypeError, setattr, foo, 'bar', 123)
        self.assertRaises(TypeError, setattr, foo, 'bar', [])

        foo.bar = None
        self.assertEquals(None, foo.bar)
        self.assertEquals(None, d[0])

        del foo.bar
        self.assertEquals(None, foo.bar)
        self.assertEquals(None, d[0])
