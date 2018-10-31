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
import json

from zope.interface import implementer

from .interfaces import IJsonable


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
