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
    'field_index',
    'local_index',
    'key',
    'optional',
    'type',
    'predicate',
    'proxy_class',
    'format',
    'get',
    'set',
    'delete',
])


__field_class = Field
__field_index = 0       # 전역적 필드 정의 순서


def Field(key=None, optional=False, type=None, predicate=None, proxy=None,
          format=None):
    '''
    Define a field.

    :param type:
        int, float, str or dict [TODO: list]
    :param predicate:
        validating callable
    '''
    global __field_index
    __field_index += 1

    if type is None and proxy is not None:
        type = proxy.__jsonable_proxy__.wrapped_type
    elif (type is not None and
          proxy is not None and
          type is not proxy.__jsonable_proxy__.wrapped_type):
        raise TypeError()

    return __field_class(
        name=None,
        field_index=__field_index,
        local_index=None,
        key=key,
        optional=optional,
        type=type,
        predicate=predicate,
        get=None,
        set=None,
        delete=None,
        proxy_class=proxy,
        format=format,
    )


class ProxyClassMetadata(object):

    __slots__ = (
        'wrapped_type',
        'field_list',
    )

    def __init__(self, wrapped_type, field_list):
        self.wrapped_type = wrapped_type
        self.field_list = tuple(field_list)

    def validate(self, __jsonable__):
        if not isinstance(__jsonable__, self.wrapped_type):
            raise TypeError()

        for field in self.field_list:
            # getter 및 proxy, format 으로 시험해본다.
            item = field.get(__jsonable__)
            if field.proxy_class is not None:
                if field.optional:
                    if item is not None:
                        field.proxy_class(item)
                else:
                    field.proxy_class(item)
            elif field.format is not None:
                if field.optional:
                    if item is not None:
                        field.format.parse(item)
                else:
                    field.format.parse(item)

        return __jsonable__


def __build_metadata(wrapped_type, cls):
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
    field_list = sorted(field_list, key=lambda field: field.field_index)
    field_list = [
        # 局部的 필드 인덱스 부여
        f._replace(local_index=local_index)
        for local_index, f in enumerate(field_list)
    ]

    field_list = [
        __field_with_get_and_set(wrapped_type, f)
        for f in field_list
    ]
    return ProxyClassMetadata(
        wrapped_type,
        field_list,
    )


def proxy(wrapped_type, init=True, repr_=True, eq=True):

    define_init = init
    define_repr = repr_
    define_eq = eq

    def decorator(cls):
        metadata = __build_metadata(
            wrapped_type,
            cls,
        )

        attrs = dict(cls.__dict__)

        attrs['__jsonable_proxy__'] = metadata

        for field in metadata.field_list:
            attrs[field.name] = __make_property(field)

        attrs['__slots__'] = ('__jsonable__', )

        if ('__init__' not in attrs) and define_init:
            def __init__(self, __jsonable__):
                self.__jsonable__ = metadata.validate(__jsonable__)

            attrs['__init__'] = __init__

        if ('__repr__' not in attrs) and define_repr:
            def __repr__(self):
                params = ', '.join('{}={}'.format(
                    field.name,
                    repr(getattr(self, field.name))
                ) for field in metadata.field_list)

                return '{}({})'.format(
                    cls.__name__,
                    params,
                )

            attrs['__repr__'] = __repr__

        if ('__eq__' not in attrs) and define_eq:
            def __eq__(self, peer):
                return all(getattr(self, field.name) ==
                           getattr(peer, field.name)
                           for field in metadata.field_list)

            attrs['__eq__'] = __eq__

        new_class = type(cls.__name__, cls.__bases__, attrs)
        new_class = implementer(IJsonable)(new_class)
        return new_class
    return decorator


def __field_with_get_and_set(container_type, field):
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

    return field._replace(get=getter, set=setter, delete=deleter)


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


def __make_property(field):

    def getter(self):
        return field.get(self.__jsonable__)

    def setter(self, value):
        field.set(self.__jsonable__, value)

    # getter 는 proxy_class / format 중 하나만 사용한다.
    getting_value = None
    if field.proxy_class is not None:
        getting_value = __proxified_getting_value(field.proxy_class)
    elif field.format is not None:
        getting_value = field.format.parse

    # setter 는 proxy_class / format 둘 다 정의되어 있으면
    # proxy_class 가 아닌 입력도 format으로 변환 시도한다.
    setting_value = None
    if field.proxy_class is not None and field.format is None:
        setting_value = __proxified_setting_value(field.proxy_class)
    elif field.proxy_class is None and field.format is not None:
        # NOTE: format should check valid input
        setting_value = field.format.format
    elif field.proxy_class is not None and field.format is not None:
        def setting_value(value):
            if isinstance(value, field.proxy_class):
                return value.__jsonable__
            try:
                # NOTE: format should check valid input
                return field.format.format(value)
            except Exception:
                raise TypeError()

    if getting_value is not None:
        getter = __decorate_getter(getter, getting_value)
    if setting_value is not None:
        setter = __decorate_setter(setter, setting_value)

    if field.delete is None:
        return property(getter, setter)

    def deleter(self):
        field.delete(self.__jsonable__)

    return property(getter, setter, deleter)


def __decorate_getter(getter, decorator):
    def decorated_getter(self):
        item = getter(self)
        if item is None:
            return None
        return decorator(item)
    return decorated_getter


def __decorate_setter(setter, decorator):
    def decorated_setter(self, item):
        if item is not None:
            item = decorator(item)
        setter(self, item)
    return decorated_setter


def __proxified_getting_value(proxy_class):
    # TODO: # No validation here in the proxy_class.__init__; the item
    # should be already validated
    # proxy = object.__new__(proxy_class)
    # proxy.__jsonable__ = item
    return proxy_class


def __proxified_setting_value(proxy_class):
    def proxified_setting(pval):
        if not isinstance(pval, proxy_class):
            raise TypeError()
        return pval.__jsonable__
    return proxified_setting


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
