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
from datetime import datetime
from unittest import TestCase
from uuid import UUID
from uuid import uuid4
import operator

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
            'Qux[foo=Foo[id=123], bar=Bar[foo=Foo[id=456]]]',
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


def createUUIDFormat(self):
    from jsonable_objects.interfaces import IFormat

    @implementer(IFormat)
    class UUIDFormat(object):

        def format(self, pyobj):
            if not isinstance(pyobj, UUID):
                raise TypeError()
            return str(pyobj)

        def parse(self, jsonableval):
            return UUID(jsonableval)

    return UUIDFormat()


def createDateTimeFormat(self):
    from jsonable_objects.interfaces import IFormat

    @implementer(IFormat)
    class DateTimeFormat(object):

        def format(self, pyobj):
            if not isinstance(pyobj, datetime):
                raise TypeError()
            return str(pyobj)

        def parse(self, jvalue):
            year = int(jvalue[0:4])
            month = int(jvalue[5:7])
            day = int(jvalue[8:10])
            hour = int(jvalue[11:13])
            minute = int(jvalue[14:16])
            second = int(jvalue[17:19])
            microseconds = int(jvalue[20:26])
            return datetime(
                year, month, day,
                hour, minute, second,
                microseconds
            )

    return DateTimeFormat()


class ProxyTest(TestCase):

    def test_for_non_dict_and_list(self):
        from jsonable_objects.proxy import proxy

        class Foo(object):
            pass

        self.assertRaises(TypeError, proxy, tuple)
        self.assertRaises(TypeError, proxy, Foo)


class ProxyForDictTest(TestCase):

    uuidFormat = property(createUUIDFormat)
    datetimeFormat = property(createDateTimeFormat)

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

    def test_slots(self):
        from jsonable_objects.proxy import proxy

        @proxy(dict)
        class Foo(object):
            pass

        foo = Foo({})
        self.assertRaises(AttributeError, setattr, foo, 'bar', 1)

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
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        uuidFormat = self.uuidFormat

        @proxy(dict)
        class Foo(object):
            uuid = Field(type=str, format=uuidFormat)

        self.assertRaises(KeyError, Foo, {})

        d = {
            'uuid': 'invalid',
        }
        self.assertRaises(ValueError, Foo, d)

        d = {
            'uuid': '27d861ac-f27e-4ef5-81af-99d2fcd976a6',
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

    def test_format_optional(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        uuidFormat = self.uuidFormat

        @proxy(dict)
        class Foo(object):
            uuid = Field(type=str, optional=True, format=uuidFormat)

        d = {
        }
        foo = Foo(d)
        self.assertEquals(None, foo.uuid)

        d = {
            'uuid': 'invalid',
        }
        self.assertRaises(ValueError, Foo, d)

        d = {
            'uuid': '27d861ac-f27e-4ef5-81af-99d2fcd976a6',
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

        foo.uuid = None
        self.assertEquals(None, foo.uuid)
        self.assertEquals(None, d['uuid'])
        del foo.uuid
        self.assertEquals(None, foo.uuid)
        self.assertTrue('uuid' not in d)

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
        bar = Bar(b)
        self.assertEquals(bar, Bar({
            'id': 2,
        }))
        self.assertTrue(bar == Bar({
            'id': 2,
        }))
        self.assertTrue(bar != Bar({
            'id': 1,
        }))
        self.assertFalse(bar == Bar({
            'id': 1,
        }))
        self.assertFalse(bar != Bar({
            'id': 2,
        }))

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

    def test_proxy_and_format(self):
        from jsonable_objects.interfaces import IFormat
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Bar(object):
            id = Field(type=int)

        class BarRecord(object):

            def __init__(self, id):
                self.id = int(id)

        @implementer(IFormat)
        class BarRecordFormat(object):

            def format(self, pobj):
                return {
                    'id': pobj.id,
                }

            def parse(self, jobj):
                id = jobj['id']
                return BarRecord(id)

        barFormat = BarRecordFormat()

        @proxy(dict)
        class Foo(object):
            bar = Field(type=dict, optional=True, proxy=Bar, format=barFormat)

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

        foo.bar = BarRecord(3)
        self.assertEquals(3, foo.bar.id)
        self.assertEquals(3, d['bar']['id'])

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

    def test_not_specified_as_container(self):
        from jsonable_objects.proxy import proxy

        @proxy(dict)
        class NonMapping(object):
            pass

        self.assertRaises(AttributeError, getattr, NonMapping, '__len__')
        self.assertRaises(AttributeError, getattr, NonMapping, '__iter__')
        self.assertRaises(AttributeError, getattr, NonMapping, '__getitem__')
        self.assertRaises(AttributeError, getattr, NonMapping, '__setitem__')
        self.assertRaises(AttributeError, getattr, NonMapping, '__delitem__')
        self.assertRaises(AttributeError, getattr, NonMapping, '__contains__')

    def test_specified_as_container(self):
        from jsonable_objects.proxy import proxy

        @proxy(dict, as_container=True)
        class Mapping(object):
            pass

        d = {
            'foo': 1,
            'bar': 2,
        }
        mapping = Mapping(d)
        self.assertEquals(2, len(mapping))
        self.assertEquals(['bar', 'foo'], list(sorted(mapping)))
        self.assertEquals(1, mapping['foo'])
        self.assertEquals(2, mapping['bar'])
        self.assertRaises(KeyError, operator.getitem, mapping, 'qux')
        self.assertEquals(
            'Mapping({"bar": 2, "foo": 1})',
            repr(mapping),
        )
        mapping['qux'] = 3
        self.assertEquals(3, d['qux'])
        del mapping['bar']
        self.assertEquals({
            'foo': 1,
            'qux': 3,
        }, d)
        self.assertRaises(KeyError, operator.delitem, mapping, 'bar')
        self.assertTrue('foo' in mapping)
        self.assertTrue('bar' not in mapping)

        self.assertEquals(mapping, Mapping(d))
        self.assertTrue(mapping != Mapping({}))
        self.assertFalse(mapping == Mapping({}))

    def test_you_cannot_mix_fieldset_and_container(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        decorator = proxy(dict, as_container=True)

        class Foo(object):
            id = Field()

        self.assertRaises(TypeError, decorator, Foo)

    def test_not_override_user_defined_container(self):
        from jsonable_objects.proxy import proxy

        @proxy(dict, as_container=True)
        class Mapping(object):

            def __len__(self):
                raise RuntimeError('len')

            def __iter__(self):
                raise RuntimeError('iter')

            def __getitem__(self, key):
                raise RuntimeError('getitem')

            def __setitem__(self, key, value):
                raise RuntimeError('setitem')

            def __delitem__(self, key):
                raise RuntimeError('delitem')

            def __contains__(self, key):
                raise RuntimeError('contains')

        mapping = Mapping({
            'foo': 1,
            'bar': 2,
        })
        self.assertRaises(RuntimeError, len, mapping)
        self.assertRaises(RuntimeError, iter, mapping)
        self.assertRaises(RuntimeError, operator.getitem, mapping, 'foo')
        self.assertRaises(RuntimeError, operator.setitem, mapping, 'qux', 3)
        self.assertRaises(RuntimeError, operator.delitem, mapping, 'bar')
        self.assertRaises(RuntimeError, operator.contains, mapping, 'foo')

    def test_proxy_keyFormat(self):
        from jsonable_objects.proxy import proxy

        @proxy(dict, keyFormat=self.uuidFormat)
        class Mapping(object):
            pass

        uuid1 = UUID('058dd15b-39d4-4189-acf3-a376efeeeebd')
        uuid2 = UUID('51bff41d-95e8-4fb8-9923-e72741725fd0')
        uuid3 = UUID('2add6da2-4615-4690-b4a9-73dbae2d83dd')
        d = {}
        mapping = Mapping(d)
        mapping[uuid1] = 'foo'
        mapping[uuid2] = 'bar'

        self.assertEquals({
            str(uuid1): 'foo',
            str(uuid2): 'bar',
        }, d)

        # validate
        mapping = Mapping(d)

        self.assertEquals('foo', mapping[uuid1])
        self.assertEquals('bar', mapping[uuid2])
        self.assertEquals([
            uuid1, uuid2,
        ], list(sorted(mapping)))

        self.assertRaises(KeyError, operator.getitem, mapping, uuid4())
        self.assertRaises(TypeError, operator.setitem, mapping, 'QUX', 'qux')
        self.assertTrue(uuid1 in mapping)
        self.assertTrue(uuid2 in mapping)
        self.assertTrue(uuid3 not in mapping)

    def test_proxy_keyFormat_and_itemFormat(self):
        from jsonable_objects.proxy import proxy

        @proxy(dict, keyFormat=self.uuidFormat, itemFormat=self.datetimeFormat)
        class Mapping(object):
            pass

        uuid1 = UUID('058dd15b-39d4-4189-acf3-a376efeeeebd')
        uuid2 = UUID('51bff41d-95e8-4fb8-9923-e72741725fd0')
        datetime1 = datetime.utcnow()
        datetime2 = datetime.utcnow()
        d = {}
        mapping = Mapping(d)
        mapping[uuid1] = datetime1
        mapping[uuid2] = datetime2

        self.assertEquals({
            str(uuid1): str(datetime1),
            str(uuid2): str(datetime2),
        }, d)

        # validate
        mapping = Mapping(d)

        self.assertEquals(datetime1, mapping[uuid1])
        self.assertEquals(datetime2, mapping[uuid2])
        self.assertEquals([
            uuid1, uuid2,
        ], list(sorted(mapping)))

        self.assertRaises(KeyError, operator.getitem, mapping, uuid4())
        self.assertRaises(
            TypeError,
            operator.setitem,
            mapping, 'QUX', datetime.utcnow()
        )
        self.assertRaises(
            TypeError,
            operator.setitem,
            mapping, uuid4(), 'qux',
        )

    def test_proxy_keyFormat_and_itemProxy(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            id = Field(type=int)

        @proxy(dict, keyFormat=self.uuidFormat, itemProxy=Foo)
        class Mapping(object):
            pass

        uuid1 = UUID('058dd15b-39d4-4189-acf3-a376efeeeebd')
        uuid2 = UUID('51bff41d-95e8-4fb8-9923-e72741725fd0')
        foo1 = {
            'id': 1,
        }
        foo2 = {
            'id': 2,
        }
        d = {}
        mapping = Mapping(d)
        mapping[uuid1] = Foo(foo1)
        mapping[uuid2] = Foo(foo2)

        # validate
        mapping = Mapping(d)

        self.assertTrue(d[str(uuid1)] is foo1)
        self.assertTrue(d[str(uuid2)] is foo2)

        self.assertEquals(1, mapping[uuid1].id)
        self.assertEquals(2, mapping[uuid2].id)
        self.assertEquals(Foo(foo1), mapping[uuid1])
        self.assertEquals(Foo(foo2), mapping[uuid2])

        self.assertEquals([
            uuid1, uuid2,
        ], list(sorted(mapping)))

        self.assertRaises(KeyError, operator.getitem, mapping, uuid4())
        self.assertRaises(
            TypeError,
            operator.setitem,
            mapping, 'QUX', Foo({'id': 3}),
        )
        self.assertRaises(
            TypeError,
            operator.setitem,
            mapping, uuid4(), 'qux',
        )

        del mapping[uuid1]
        self.assertEquals({
            str(uuid2): foo2,
        }, d)
        self.assertRaises(KeyError, operator.delitem, mapping, uuid1)

    def test_proxy_itemFormat(self):
        from jsonable_objects.proxy import proxy

        @proxy(dict, itemFormat=self.datetimeFormat)
        class Mapping(object):
            pass

        datetime1 = datetime.utcnow()
        datetime2 = datetime.utcnow()
        d = {}
        mapping = Mapping(d)
        mapping['foo'] = datetime1
        mapping['bar'] = datetime2

        self.assertEquals({
            'foo': str(datetime1),
            'bar': str(datetime2),
        }, d)

        self.assertEquals(datetime1, mapping['foo'])
        self.assertEquals(datetime2, mapping['bar'])
        self.assertEquals([
            'bar', 'foo',
        ], list(sorted(mapping)))

        self.assertRaises(KeyError, operator.getitem, mapping, uuid4())
        self.assertRaises(
            TypeError,
            operator.setitem,
            mapping, 'qux', 'QUX',
        )

    def test_proxy_itemProxy(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            id = Field(type=int)

        @proxy(dict, itemProxy=Foo)
        class Mapping(object):
            pass

        uuid1 = UUID('058dd15b-39d4-4189-acf3-a376efeeeebd')
        uuid2 = UUID('51bff41d-95e8-4fb8-9923-e72741725fd0')
        foo1 = {
            'id': 1,
        }
        foo2 = {
            'id': 2,
        }
        d = {}
        mapping = Mapping(d)
        mapping[uuid1] = Foo(foo1)
        mapping[uuid2] = Foo(foo2)

        self.assertTrue(d[uuid1] is foo1)
        self.assertTrue(d[uuid2] is foo2)

        self.assertEquals(1, mapping[uuid1].id)
        self.assertEquals(2, mapping[uuid2].id)
        self.assertEquals(Foo(foo1), mapping[uuid1])
        self.assertEquals(Foo(foo2), mapping[uuid2])

        self.assertEquals([
            uuid1, uuid2,
        ], list(sorted(mapping)))

        self.assertRaises(KeyError, operator.getitem, mapping, uuid4())
        self.assertRaises(
            TypeError,
            operator.setitem,
            mapping, uuid4(), 'qux',
        )


class ProxyForListTest(TestCase):

    uuidFormat = property(createUUIDFormat)
    datetimeFormat = property(createDateTimeFormat)

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

    def test_slots(self):
        from jsonable_objects.proxy import proxy

        @proxy(list)
        class Foo(object):
            pass

        foo = Foo([])
        self.assertRaises(AttributeError, setattr, foo, 'bar', 1)

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
            'invalid',
        ]
        self.assertRaises(ValueError, Foo, d)

        d = [
            '27d861ac-f27e-4ef5-81af-99d2fcd976a6',
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

    def test_format_optional(self):
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
            uuid = Field(type=str, optional=True, format=uuidFormat)

        self.assertRaises(IndexError, Foo, [])

        d = [
            'invalid',
        ]
        self.assertRaises(ValueError, Foo, d)

        d = [
            '27d861ac-f27e-4ef5-81af-99d2fcd976a6',
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

        foo.uuid = None
        self.assertEquals(None, foo.uuid)
        self.assertEquals(None, d[0])
        del foo.uuid
        self.assertEquals(None, foo.uuid)
        self.assertEquals(None, d[0])

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
        bar = Bar(b)
        self.assertEquals(bar, Bar([2]))
        self.assertTrue(bar == Bar([2]))
        self.assertTrue(bar != Bar([1]))
        self.assertFalse(bar == Bar([1]))
        self.assertFalse(bar != Bar([2]))

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

    def test_not_specified_as_container(self):
        from jsonable_objects.proxy import proxy

        @proxy(list)
        class NonSeq(object):
            pass

        self.assertRaises(AttributeError, getattr, NonSeq, '__len__')
        self.assertRaises(AttributeError, getattr, NonSeq, '__iter__')
        self.assertRaises(AttributeError, getattr, NonSeq, '__getitem__')
        self.assertRaises(AttributeError, getattr, NonSeq, '__setitem__')
        self.assertRaises(AttributeError, getattr, NonSeq, '__delitem__')
        self.assertRaises(AttributeError, getattr, NonSeq, '__contains__')

    def test_specified_as_container(self):
        from jsonable_objects.proxy import proxy

        @proxy(list, as_container=True)
        class Seq(object):
            pass

        lst = [
            'foo',
            'bar',
        ]
        seq = Seq(lst)
        self.assertEquals(2, len(seq))
        self.assertEquals(lst, list(seq))
        self.assertEquals('foo', seq[0])
        self.assertEquals('bar', seq[1])
        self.assertEquals(
            'Seq(["foo", "bar"])',
            repr(seq),
        )

        seq[1] = 'qux'
        self.assertEquals('qux', lst[1])
        self.assertEquals([
            'foo',
            'qux',
        ], lst)

        del seq[0]
        self.assertEquals(['qux'], lst)
        self.assertRaises(IndexError, operator.delitem, seq, 10)
        self.assertTrue('qux' in seq)
        self.assertTrue('foo' not in seq)

        self.assertEquals(seq, Seq(lst))
        self.assertTrue(seq != Seq([]))
        self.assertFalse(seq == Seq([]))

        lst = list('012345')
        seq = Seq(lst)
        self.assertEquals(['0', '2', '4'], seq[0::2])

    def test_you_cannot_mix_fieldset_and_container(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        decorator = proxy(list, as_container=True)

        class Seq(object):
            foo = Field()

        self.assertRaises(TypeError, decorator, Seq)

    def test_not_override_user_defined_container(self):
        from jsonable_objects.proxy import proxy

        @proxy(list, as_container=True)
        class Seq(object):

            def __len__(self):
                raise RuntimeError('len')

            def __iter__(self):
                raise RuntimeError('iter')

            def __getitem__(self, index):
                raise RuntimeError('getitem')

            def __setitem__(self, index, value):
                raise RuntimeError('setitem')

            def __delitem__(self, index):
                raise RuntimeError('delitem')

            def __contains__(self, index):
                raise RuntimeError('contains')

        lst = [
            'foo',
            'bar',
        ]
        seq = Seq(lst)
        self.assertRaises(RuntimeError, len, seq)
        self.assertRaises(RuntimeError, iter, seq)
        self.assertRaises(RuntimeError, operator.getitem, seq, 0)
        self.assertRaises(RuntimeError, operator.setitem, seq, 0, 'qux')
        self.assertRaises(RuntimeError, operator.delitem, seq, 0)
        self.assertRaises(RuntimeError, operator.contains, seq, 'foo')

    def test_keyFormat(self):
        from jsonable_objects.proxy import proxy

        self.assertRaises(
            TypeError,
            proxy, list, keyFormat=self.uuidFormat
        )

    def test_itemFormat(self):
        from jsonable_objects.proxy import proxy

        @proxy(list, itemFormat=self.uuidFormat)
        class Seq(object):
            pass

        lst = [
            '058dd15b-39d4-4189-acf3-a376efeeeebd',
            '51bff41d-95e8-4fb8-9923-e72741725fd0',
        ]
        seq = Seq(lst)

        uuid1 = UUID('058dd15b-39d4-4189-acf3-a376efeeeebd')
        uuid2 = UUID('51bff41d-95e8-4fb8-9923-e72741725fd0')
        uuid3 = UUID('2add6da2-4615-4690-b4a9-73dbae2d83dd')
        self.assertEquals([
            uuid1, uuid2,
        ], list(seq))
        self.assertEquals(uuid1, seq[0])
        self.assertEquals(uuid2, seq[1])

        seq[1] = uuid3
        self.assertEquals(uuid3, seq[1])
        self.assertEquals([
            uuid1, uuid3,
        ], list(seq))
        self.assertEquals([
            '058dd15b-39d4-4189-acf3-a376efeeeebd',
            '2add6da2-4615-4690-b4a9-73dbae2d83dd',
        ], lst)
        self.assertTrue(uuid1 in seq)
        self.assertTrue(uuid2 not in seq)
        self.assertTrue(uuid3 in seq)

        seq[1:1] = [uuid2]
        self.assertEquals([
            '058dd15b-39d4-4189-acf3-a376efeeeebd',
            '51bff41d-95e8-4fb8-9923-e72741725fd0',
            '2add6da2-4615-4690-b4a9-73dbae2d83dd',
        ], lst)
        seq = Seq(lst)
        self.assertEquals([uuid1, uuid2], seq[0:2])
        self.assertEquals([uuid1, uuid3], seq[0::2])

    def test_itemProxy(self):
        from jsonable_objects.proxy import proxy
        from jsonable_objects.proxy import Field

        @proxy(dict)
        class Foo(object):
            id = Field(type=int)

        @proxy(list, itemProxy=Foo)
        class FooSeq(object):
            pass

        foo1 = {
            'id': 1
        }
        foo2 = {
            'id': 2,
        }
        foo3 = {
            'id': 3
        }
        lst = [
            foo1,
            foo3,
        ]
        seq = FooSeq(lst)
        self.assertEquals(1, seq[0].id)
        self.assertEquals(3, seq[1].id)
        self.assertEquals(Foo({'id': 1}), seq[0])
        self.assertEquals(Foo({'id': 3}), seq[1])
        self.assertEquals([
            Foo({'id': 1}),
            Foo({'id': 3}),
        ], list(seq))
        self.assertTrue(Foo(foo1) in seq)
        self.assertTrue(Foo(foo2) not in seq)
        self.assertTrue(Foo(foo3) in seq)
        self.assertRaises(TypeError, operator.contains, seq, foo1)

        seq[1] = Foo(foo2)
        self.assertTrue(lst[1] is foo2)
        self.assertRaises(
            TypeError,
            operator.setitem, seq, 1, 'qux',
        )

        seq[len(seq):] = [Foo(foo3)]
        self.assertEquals([foo1, foo2, foo3], lst)
        self.assertTrue(lst[1] is foo2)

        self.assertEquals(
            [Foo(foo1), Foo(foo2)],
            seq[0:2],
        )
        self.assertEquals(
            [Foo(foo1), Foo(foo3)],
            seq[0::2],
        )

        self.assertRaises(
            TypeError,
            operator.setitem, seq, slice(0, 0), ['qux']
        )
