# -*- coding: utf-8 -*-
#
#   mete0r_testfixture: a testfixture helper
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
from __future__ import unicode_literals

from unittest import TestCase


class TestFixturesTest(TestCase):

    def test_nothing(self):
        from mete0r_testfixture.testfixture import TestFixtures
        from mete0r_testfixture import tests

        testfixtures = TestFixtures(tests)

        self.assertEquals({
            'Foo': None,
        }, testfixtures.get('Foo'))

        self.assertEquals({
            'Foo': 'foo',
        }, testfixtures.get('Foo', 'foo'))

        self.assertEquals({
            'Bar': {
                'Foo': 'foo',
            }
        }, testfixtures.get('Bar'))
