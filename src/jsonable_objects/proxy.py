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
from collections import namedtuple
import json

from zope.interface import implementer

from .interfaces import IJsonable


Field = namedtuple('Field', [
    'name',
    'serial_number',
    'local_index',
    'key',
    'optional',
    'type',
    'predicate',
    'proxy_class',
    'format',
    'dops',
    'uops',
    'descriptors',
])


__field_class = Field
__field_serial_number = 0       # 전역적 필드 정의 순서


def Field(key=None, optional=False, type=None, predicate=None, proxy=None,
          format=None):
    '''
    Define a field.

    :param type:
        int, float, str or dict [TODO: list]
    :param predicate:
        validating callable
    '''
    global __field_serial_number
    __field_serial_number += 1

    if type is None and proxy is not None:
        type = proxy.__jsonable_proxy__.wrapped_type
    elif (type is not None and
          proxy is not None and
          type is not proxy.__jsonable_proxy__.wrapped_type):
        raise TypeError()

    return __field_class(
        name=None,
        serial_number=__field_serial_number,
        local_index=None,
        key=key,
        optional=optional,
        type=type,
        predicate=predicate,
        proxy_class=proxy,
        format=format,
        dops=None,
        uops=None,
        descriptors=None,
    )


DownwardOps = namedtuple('DownwardOps', [
    'get',
    'set',
    'delete',
])


UpwardOps = namedtuple('UpwardOps', [
    'get',
    'set',
    'delete',
])


FieldDescriptors = namedtuple('FieldDescriptors', [
    'get',
    'set',
    'delete',
])


Methods = namedtuple('Methods', [
    'init',
    'repr',
    'eq',
    'ne',
    'len',
    'iter',
    'getitem',
    'setitem',
    'delitem',
    'contains',
])


class ProxyClassMetadata(object):

    __slots__ = (
        'wrapped_type',
        'field_list',
        'as_container',
        'keyFormat',
        'itemProxy',
        'itemFormat',
        'methods',
    )

    def __init__(self, wrapped_type, field_list, as_container, keyFormat,
                 itemProxy, itemFormat, methods):
        self.wrapped_type = wrapped_type
        self.field_list = tuple(field_list)
        self.as_container = as_container
        self.keyFormat = keyFormat
        self.itemProxy = itemProxy
        self.itemFormat = itemFormat
        self.methods = methods

    def validate(self, __jsonable__):
        if not isinstance(__jsonable__, self.wrapped_type):
            raise TypeError()

        for field in self.field_list:
            field.uops.get(__jsonable__)

        if self.as_container:

            keyFormat = self.keyFormat
            itemFormat = self.itemFormat
            itemProxy = self.itemProxy

            if issubclass(self.wrapped_type, dict):
                if keyFormat is not None:
                    for key in __jsonable__:
                        keyFormat.parse(key)
                if itemProxy is not None or itemFormat is not None:
                    for value in __jsonable__.values():
                        if itemProxy is not None:
                            itemProxy.__jsonable_proxy__.validate(value)
                        if itemFormat is not None:
                            itemFormat.parse(value)
            else:  # issubclass(self.wrapped_type, list):
                if itemProxy is not None or itemFormat is not None:
                    for value in __jsonable__:
                        if itemProxy is not None:
                            itemProxy.__jsonable_proxy__.validate(value)
                        if itemFormat is not None:
                            itemFormat.parse(value)

        return __jsonable__


def __build_field_list(wrapped_type, cls):
    field_list = []

    # 부모 클래스의 필드 목록을 미리 추가해둔다.
    for base_class in cls.__bases__:
        if not hasattr(base_class, '__jsonable_proxy__'):
            continue
        if base_class.__jsonable_proxy__.wrapped_type is not wrapped_type:
            raise TypeError()
        for field in base_class.__jsonable_proxy__.field_list:
            field_list.append(field)

    for name, attr in cls.__dict__.items():
        if isinstance(attr, __field_class):
            field = attr._replace(name=name)
            if field.key is None:
                # 필드에 key 가 정해지지 않으면 속성 이름을 대신 사용한다.
                field = field._replace(key=name)
            field_list.append(field)

    # 全域的 定意 順으로 整列
    field_list = sorted(field_list, key=lambda field: field.serial_number)
    field_list = [
        # 局部的 필드 인덱스 부여
        f._replace(local_index=local_index)
        for local_index, f in enumerate(field_list)
    ]

    return [
        __field_with_descriptors(wrapped_type, f)
        for f in field_list
    ]


def proxy(wrapped_type, as_container=False,
          keyFormat=None, itemProxy=None, itemFormat=None):

    if not issubclass(wrapped_type, (dict, list)):
        raise TypeError()

    if issubclass(wrapped_type, list):
        if keyFormat is not None:
            raise TypeError()

    if keyFormat is not None:
        as_container = True
    elif itemProxy is not None:
        as_container = True
    elif itemFormat is not None:
        as_container = True

    #
    # __init__
    #
    def __init__(self, __jsonable__):
        self.__jsonable__ = self.__jsonable_proxy__.validate(__jsonable__)

    #
    # __eq__
    #
    if as_container:
        if wrapped_type is dict:
            def __eq__(self, peer):
                return (dict((k, self[k]) for k in self) ==
                        dict((k, peer[k]) for k in peer))
        else:  # wrapped_type is list
            def __eq__(self, peer):
                return list(self) == list(peer)
    else:
        def __eq__(self, peer):
            return all(getattr(self, field.name) ==
                       getattr(peer, field.name)
                       for field in self.__jsonable_proxy__.field_list)

    # __ne__
    if as_container:
        if wrapped_type is dict:
            def __ne__(self, peer):
                return (dict((k, self[k]) for k in self) !=
                        dict((k, peer[k]) for k in peer))
        else:  # wrapped_type is list
            def __ne__(self, peer):
                return list(self) != list(peer)
    else:
        def __ne__(self, peer):
            return any(getattr(self, field.name) !=
                       getattr(peer, field.name)
                       for field in self.__jsonable_proxy__.field_list)

    #
    # __repr__
    #
    if as_container:
        def __repr__(self):
            return '{}({})'.format(
                type(self).__name__,
                json.dumps(self.__jsonable__, sort_keys=True),
            )
    else:
        def __repr__(self):
            params = ', '.join('{}={}'.format(
                field.name,
                repr(getattr(self, field.name))
            ) for field in self.__jsonable_proxy__.field_list)

            return '{}[{}]'.format(
                type(self).__name__,
                params,
            )

    methods = Methods(
        init=__init__,
        repr=__repr__,
        eq=__eq__,
        ne=__ne__,
        len=None,
        iter=None,
        getitem=None,
        setitem=None,
        delitem=None,
        contains=None,
    )

    if as_container:
        #
        # __len__
        #
        def __len__(self):
            return len(self.__jsonable__)

        #
        # __iter__
        #
        if issubclass(wrapped_type, dict):
            if keyFormat is not None:
                def __iter__(self):
                    for key in self.__jsonable__:
                        yield keyFormat.parse(key)
            else:
                def __iter__(self):
                    return iter(self.__jsonable__)
        else:  # issubclass(wrapped_type, list):
            if itemProxy is not None:
                def __iter__(self):
                    for item in self.__jsonable__:
                        yield itemProxy(item)
            elif itemFormat is not None:
                def __iter__(self):
                    for item in self.__jsonable__:
                        yield itemFormat.parse(item)
            else:
                def __iter__(self):
                    return iter(self.__jsonable__)

        #
        # __getitem__
        # __setitem__
        #
        if issubclass(wrapped_type, dict):

            if keyFormat is not None:

                if itemProxy is not None:

                    def __getitem__(self, key):
                        key = keyFormat.format(key)
                        val = self.__jsonable__[key]
                        return itemProxy(val)

                    def __setitem__(self, key, value):
                        if not isinstance(value, itemProxy):
                            raise TypeError()
                        key = keyFormat.format(key)
                        self.__jsonable__[key] = value.__jsonable__

                elif itemFormat is not None:

                    def __getitem__(self, key):
                        key = keyFormat.format(key)
                        val = self.__jsonable__[key]
                        return itemFormat.parse(val)

                    def __setitem__(self, key, value):
                        key = keyFormat.format(key)
                        value = itemFormat.format(value)
                        self.__jsonable__[key] = value

                else:

                    def __getitem__(self, key):
                        key = keyFormat.format(key)
                        return self.__jsonable__[key]

                    def __setitem__(self, key, value):
                        key = keyFormat.format(key)
                        self.__jsonable__[key] = value

            else:

                if itemProxy is not None:

                    def __getitem__(self, key):
                        val = self.__jsonable__[key]
                        return itemProxy(val)

                    def __setitem__(self, key, value):
                        if not isinstance(value, itemProxy):
                            raise TypeError()
                        self.__jsonable__[key] = value.__jsonable__

                elif itemFormat is not None:

                    def __getitem__(self, key):
                        val = self.__jsonable__[key]
                        return itemFormat.parse(val)

                    def __setitem__(self, key, value):
                        value = itemFormat.format(value)
                        self.__jsonable__[key] = value

                else:

                    def __getitem__(self, key):
                        return self.__jsonable__[key]

                    def __setitem__(self, key, value):
                        self.__jsonable__[key] = value

        else:  # issubclass(wrapped_type, list):

            if itemProxy is not None:

                def __getitem__(self, index):
                    val = self.__jsonable__[index]
                    if isinstance(index, slice):
                        return [itemProxy(item) for item in val]
                    return itemProxy(val)

                def __setitem__(self, index, value):
                    if isinstance(index, slice):
                        for item in value:
                            if not isinstance(item, itemProxy):
                                raise TypeError()
                        self.__jsonable__[index] = [
                            item.__jsonable__ for item in value
                        ]
                    else:
                        if not isinstance(value, itemProxy):
                            raise TypeError()
                        self.__jsonable__[index] = value.__jsonable__

            elif itemFormat is not None:

                def __getitem__(self, index):
                    val = self.__jsonable__[index]
                    if isinstance(index, slice):
                        return [itemFormat.parse(item) for item in val]
                    return itemFormat.parse(val)

                def __setitem__(self, index, value):
                    if isinstance(index, slice):
                        self.__jsonable__[index] = [
                            itemFormat.format(item)
                            for item in value
                        ]
                    else:
                        value = itemFormat.format(value)
                        self.__jsonable__[index] = value

            else:

                def __getitem__(self, index):
                    return self.__jsonable__[index]

                def __setitem__(self, index, value):
                    self.__jsonable__[index] = value

        #
        # __delitem__
        #
        if issubclass(wrapped_type, dict):
            if keyFormat is not None:
                def __delitem__(self, key):
                    key = keyFormat.format(key)
                    del self.__jsonable__[key]
            else:
                def __delitem__(self, key):
                    del self.__jsonable__[key]
        else:  # issubclass(wrapped_type, list):
            def __delitem__(self, index):
                del self.__jsonable__[index]

        #
        # __contains__
        #
        if issubclass(wrapped_type, dict):
            if keyFormat is not None:
                def __contains__(self, key):
                    key = keyFormat.format(key)
                    return key in self.__jsonable__
            else:
                def __contains__(self, key):
                    return key in self.__jsonable__
        else:  # issubclass(wrapped_type, list):
            if itemProxy is not None:
                def __contains__(self, item):
                    if not isinstance(item, itemProxy):
                        raise TypeError()
                    return item.__jsonable__ in self.__jsonable__
            elif itemFormat is not None:
                def __contains__(self, item):
                    item = itemFormat.format(item)
                    return item in self.__jsonable__
            else:
                def __contains__(self, item):
                    return item in self.__jsonable__

        methods = methods._replace(
            len=__len__,
            iter=__iter__,
            getitem=__getitem__,
            setitem=__setitem__,
            delitem=__delitem__,
            contains=__contains__,
        )

    def decorator(cls):
        field_list = __build_field_list(
            wrapped_type,
            cls,
        )
        metadata = ProxyClassMetadata(
            wrapped_type,
            field_list,
            as_container,
            keyFormat,
            itemProxy,
            itemFormat,
            methods,
        )

        if len(metadata.field_list) > 0 and as_container:
            raise TypeError()

        attrs = dict(cls.__dict__)

        for field in metadata.field_list:
            attrs[field.name] = property(*field.descriptors)

        slots = ('__jsonable__', )
        __slots__ = attrs.get('__slots__', slots)
        if '__jsonable__' not in __slots__:
            __slots__ = slots + __slots__
        attrs['__slots__'] = __slots__

        if '__init__' not in attrs:
            attrs['__init__'] = __init__
        if '__eq__' not in attrs:
            attrs['__eq__'] = __eq__
        if '__ne__' not in attrs:
            attrs['__ne__'] = __ne__
        if '__repr__' not in attrs:
            attrs['__repr__'] = __repr__

        if as_container:
            if '__len__' not in attrs:
                attrs['__len__'] = __len__
            if '__iter__' not in attrs:
                attrs['__iter__'] = __iter__
            if '__getitem__' not in attrs:
                attrs['__getitem__'] = __getitem__
            if '__setitem__' not in attrs:
                attrs['__setitem__'] = __setitem__
            if '__delitem__' not in attrs:
                attrs['__delitem__'] = __delitem__
            if '__contains__' not in attrs:
                attrs['__contains__'] = __contains__

        attrs['__jsonable_proxy__'] = metadata

        new_class = type(cls.__name__, cls.__bases__, attrs)
        new_class = implementer(IJsonable)(new_class)
        return new_class
    return decorator


def __field_with_descriptors(wrapped_type, field):
    dops = __make_downward_ops(wrapped_type, field)
    field = field._replace(dops=dops)
    uops = __make_upward_ops(field)
    field = field._replace(uops=uops)
    descriptors = __make_field_descriptors(field)
    return field._replace(descriptors=descriptors)


def __make_downward_ops(container_type, field):
    if field.type is not None:
        validate_getting_value = __make_value_type_coercer(field.type)
        validate_setting_value = __make_value_type_checker(field.type)
    else:
        validate_getting_value = None
        validate_setting_value = None

    if field.predicate is not None:
        predicated_validate = __make_predicate_validation(field.predicate)
        validate_getting_value = __chain_validation(
            validate_getting_value, predicated_validate,
        )
        validate_setting_value = __chain_validation(
            validate_setting_value, predicated_validate,
        )

    if container_type is dict:
        if field.optional:
            if validate_getting_value is not None:
                def getter(container):
                    item = container.get(field.key)
                    if item is None:
                        return None
                    return validate_getting_value(item)
            else:
                def getter(container):
                    return container.get(field.key)
        else:
            if validate_getting_value is not None:
                def getter(container):
                    item = container[field.key]
                    if item is None:
                        raise TypeError()
                    return validate_getting_value(item)
            else:
                def getter(container):
                    item = container[field.key]
                    if item is None:
                        raise TypeError()
                    return item

        if field.optional:
            if validate_setting_value is not None:
                def setter(container, item):
                    if item is not None:
                        item = validate_setting_value(item)
                    container[field.key] = item
            else:
                def setter(container, item):
                    container[field.key] = item
        else:
            if validate_setting_value is not None:
                def setter(container, item):
                    item = validate_setting_value(item)
                    container[field.key] = item
            else:
                def setter(container, item):
                    container[field.key] = item
            setter = __nonnullize_set(setter)

        if field.optional:
            def deleter(container):
                try:
                    del container[field.key]
                except KeyError:
                    pass
        else:
            deleter = None

    elif container_type is list:
        if field.optional:
            if validate_getting_value is not None:
                def getter(container):
                    item = container[field.local_index]
                    if item is None:
                        return None
                    return validate_getting_value(item)
            else:
                def getter(container):
                    return container[field.local_index]
        else:
            if validate_getting_value is not None:
                def getter(container):
                    item = container[field.local_index]
                    if item is None:
                        raise TypeError()
                    return validate_getting_value(item)
            else:
                def getter(container):
                    item = container[field.local_index]
                    if item is None:
                        raise TypeError()
                    return item

        if field.optional:
            if validate_setting_value is not None:
                def setter(container, item):
                    if item is not None:
                        item = validate_setting_value(item)
                    container[field.local_index] = item
            else:
                def setter(container, item):
                    container[field.local_index] = item
        else:
            if validate_setting_value is not None:
                def setter(container, item):
                    item = validate_setting_value(item)
                    container[field.local_index] = item
            else:
                def setter(container, item):
                    container[field.local_index] = item

            setter = __nonnullize_set(setter)

        if field.optional:
            def deleter(container):
                container[field.local_index] = None
        else:
            deleter = None
    else:
        raise TypeError()

    return DownwardOps(get=getter, set=setter, delete=deleter)


def __make_value_type_coercer(type):
    if issubclass(type, (dict, list)):
        def ensure_container_type(value):
            if not isinstance(value, type):
                raise TypeError()
            return value
        return ensure_container_type
    return type


def __make_value_type_checker(type):
    try:
        long
    except NameError:
        pass
    else:
        if type is int:
            type = (int, long)

    try:
        unicode
    except NameError:
        pass
    else:
        if type is str:
            type = (str, unicode)

    if type is float:
        type = (float, int)

    def type_checker(value):
        if not isinstance(value, type):
            raise TypeError()
        return value
    return type_checker


def __make_predicate_validation(predicate):
    def predicated_validate(value):
        valid = predicate(value)
        if not valid:
            raise ValueError(value)
        return value
    return predicated_validate


def __chain_validation(previous, validate):
    '''
    Chain validation.

    :param previous:
        validation callable. Can be None.
    :param validate:
        validation callable. MUST NOT be None.
    '''
    if previous is None:
        return validate

    def chained_validation(value):
        value = previous(value)
        return validate(value)
    return chained_validation


def __nonnullize_set(setter):
    def nonnullized_set(container, item):
        if item is None:
            raise TypeError()
        setter(container, item)
    return nonnullized_set


def __make_field_descriptors(field):

    uops = field.uops

    def getter(self):
        return uops.get(self.__jsonable__)

    def setter(self, value):
        uops.set(self.__jsonable__, value)

    if uops.delete is None:
        return FieldDescriptors(getter, setter, None)

    def deleter(self):
        uops.delete(self.__jsonable__)

    return FieldDescriptors(getter, setter, deleter)


def __make_upward_ops(field):

    #
    # getter
    #
    # proxy_class / format 중 하나만 사용한다.
    if field.proxy_class is not None:

        def getter(__jsonable__):
            value = field.dops.get(__jsonable__)
            if value is not None:
                return field.proxy_class(value)

    elif field.format is not None:

        def getter(__jsonable__):
            value = field.dops.get(__jsonable__)
            if value is not None:
                return field.format.parse(value)

    else:

        getter = field.dops.get

    #
    # setter
    #
    # proxy_class / format 둘 다 정의되어 있으면
    # proxy_class 가 아닌 입력도 format으로 변환 시도한다.
    if field.proxy_class is not None and field.format is None:

        def setter(__jsonable__, value):
            if value is None:
                field.dops.set(__jsonable__, None)
                return
            if not isinstance(value, field.proxy_class):
                raise TypeError()
            field.dops.set(__jsonable__, value.__jsonable__)

    elif field.proxy_class is None and field.format is not None:

        def setter(__jsonable__, value):
            if value is None:
                field.dops.set(__jsonable__, None)
                return
            # NOTE: format should check valid input
            value = field.format.format(value)
            field.dops.set(__jsonable__, value)

    elif field.proxy_class is not None and field.format is not None:

        def setter(__jsonable__, value):
            if value is None:
                field.dops.set(__jsonable__, None)
                return
            if isinstance(value, field.proxy_class):
                field.dops.set(__jsonable__, value.__jsonable__)
                return
            try:
                value = field.format.format(value)
            except Exception:
                raise TypeError()
            else:
                field.dops.set(__jsonable__, value)

    else:

        setter = field.dops.set

    #
    # deleter
    #
    deleter = field.dops.delete

    return UpwardOps(getter, setter, deleter)


@implementer(IJsonable)
class JsonableProxy(object):

    __slots__ = ['__jsonable__']

    def __init__(self, jsonable):
        self.__jsonable__ = jsonable

    def __repr__(self):
        return '{}({})'.format(
            type(self).__name__,
            json.dumps(
                self.__jsonable__,
                sort_keys=True,
            )
        )

    @classmethod
    def validate(cls, jsonable):
        return cls(jsonable)
