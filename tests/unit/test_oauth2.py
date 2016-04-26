# -*- coding: utf-8 -*-
# Copyright 2016 Open Permissions Platform Coalition
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
# 

import calendar
import urllib
import urlparse
from datetime import datetime

import pytest
from mock import patch
from tornado.testing import AsyncTestCase, gen_test
from tornado.gen import coroutine, Return

from chub import oauth2


def test_read():
    obj = oauth2.Read()
    assert str(obj) == 'read'
    assert obj.resource_id is None


def test_read_something():
    obj = oauth2.Read('something')
    assert str(obj) == 'read[something]'
    assert obj.resource_id == 'something'


def test_write_something():
    obj = oauth2.Write('something')
    assert str(obj) == 'write[something]'
    assert obj.resource_id == 'something'


def test_write_nothing():
    with pytest.raises(TypeError):
        oauth2.Write()


def test_delegate_write_something():
    obj = oauth2.Delegate('other', oauth2.Write('something'))
    assert str(obj) == 'delegate[other]:write[something]'
    assert obj.resource_id == 'other'
    assert obj.access == oauth2.Write('something')


def test_delegate_nothing():
    with pytest.raises(TypeError):
        oauth2.Delegate('x')


def test_delegate_noone():
    with pytest.raises(TypeError):
        oauth2.Delegate()


def test_scope():
    scope = oauth2.Scope(oauth2.Read(), oauth2.Write(1),
                         oauth2.Delegate(2, oauth2.Write(3)))

    assert str(scope) == 'delegate[2]:write[3] read write[1]'


def test_scope_add():
    scope = oauth2.Scope(oauth2.Read(), oauth2.Write(1),
                         oauth2.Delegate(2, oauth2.Write(3)))
    scope.add(oauth2.Write(4))

    assert str(scope) == 'delegate[2]:write[3] read write[1] write[4]'


def test_scope_remove():
    scope = oauth2.Scope(oauth2.Read(), oauth2.Write(1),
                         oauth2.Delegate(2, oauth2.Write(3)))
    scope.remove(oauth2.Write(1))

    assert str(scope) == 'delegate[2]:write[3] read'


def test_scope_remove_does_not_exist():
    scope = oauth2.Scope(oauth2.Read(), oauth2.Write(1),
                         oauth2.Delegate(2, oauth2.Write(3)))
    scope.remove(oauth2.Write(5))

    assert str(scope) == 'delegate[2]:write[3] read write[1]'


class TestGetToken(AsyncTestCase):
    api_patch = patch('chub.oauth2.API')
    token = 'this is my token'

    def setUp(self):
        super(TestGetToken, self).setUp()
        self.API = self.api_patch.start()
        self.API().auth.token.post.side_effect = self.post
        self.API.reset_mock()
        oauth2.get_token.reset_cache()

    @coroutine
    def post(self, *args, **kwargs):
        raise Return({'access_token': self.token,
                      'expiry': 1457979984})

    def tearDown(self):
        super(TestGetToken, self).tearDown()
        self.api_patch.stop()

    @gen_test
    def test_get_token(self):
        token = yield oauth2.get_token('https://localhost:8007',
                                       '4225f4774d6874a68565a04130001144',
                                       'FMjU7vNIay5HGNABQVTTghOfEJqbet')

        assert token == self.token
        self.API.assert_called_once_with(
            'https://localhost:8007',
            auth_username='4225f4774d6874a68565a04130001144',
            auth_password='FMjU7vNIay5HGNABQVTTghOfEJqbet')
        self.API().auth.token.post.assert_called_once_with(
            body=urllib.urlencode({'grant_type': oauth2.CLIENT_CREDENTIALS}),
            request_timeout=60,
            headers={'Content-Type': 'application/x-www-form-urlencoded',
                     'Accept': 'application/json'})

    @gen_test
    def test_get_token_with_scope(self):
        token = yield oauth2.get_token('https://localhost:8007',
                                       '4225f4774d6874a68565a04130001144',
                                       'FMjU7vNIay5HGNABQVTTghOfEJqbet',
                                       scope=oauth2.Scope(oauth2.Write(1),
                                                          oauth2.Read()))

        assert token == self.token

        body = self.API().auth.token.post.call_args[1]['body']
        assert urlparse.parse_qs(body) == {
            'grant_type': [oauth2.CLIENT_CREDENTIALS],
            'scope': ['read write[1]']}

    @gen_test
    def test_get_token_with_scope_string(self):
        token = yield oauth2.get_token('https://localhost:8007',
                                       '4225f4774d6874a68565a04130001144',
                                       'FMjU7vNIay5HGNABQVTTghOfEJqbet',
                                       scope='read')

        assert token == self.token

        body = self.API().auth.token.post.call_args[1]['body']
        assert urlparse.parse_qs(body) == {
            'grant_type': [oauth2.CLIENT_CREDENTIALS],
            'scope': ['read']}

    @gen_test
    def test_get_jwt_token(self):
        token = yield oauth2.get_token('https://localhost:8007',
                                       '4225f4774d6874a68565a04130001144',
                                       'FMjU7vNIay5HGNABQVTTghOfEJqbet',
                                       jwt='the client jwt')

        assert token == self.token

        body = self.API().auth.token.post.call_args[1]['body']
        assert urlparse.parse_qs(body) == {'grant_type': [oauth2.JWT_BEARER],
                                           'assertion': ['the client jwt']}

    @gen_test
    def test_get_jwt_token_with_scope(self):
        token = yield oauth2.get_token('https://localhost:8007',
                                       '4225f4774d6874a68565a04130001144',
                                       'FMjU7vNIay5HGNABQVTTghOfEJqbet',
                                       jwt='the client jwt',
                                       scope=oauth2.Scope(oauth2.Write(1),
                                                          oauth2.Read()))

        assert token == self.token

        body = self.API().auth.token.post.call_args[1]['body']
        assert urlparse.parse_qs(body) == {'grant_type': [oauth2.JWT_BEARER],
                                           'assertion': ['the client jwt'],
                                           'scope': ['read write[1]']}


class TestTokenCache(AsyncTestCase):
    api_patch = patch('chub.oauth2.API')
    token1 = 'this is my first token'
    token2 = 'this is my second token'

    def setUp(self):
        super(TestTokenCache, self).setUp()
        self.API = self.api_patch.start()
        self.API().auth.token.post.side_effect = self.post
        self.API.reset_mock()
        self.request_count = 0
        self.expiry = (calendar.timegm(datetime.utcnow().timetuple()) +
                       oauth2.RequestToken.max_until_expired * 2)
        oauth2.get_token.reset_cache()

    @coroutine
    def post(self, *args, **kwargs):
        token = self.token1 if self.request_count == 0 else self.token2
        self.request_count += 1

        raise Return({
            'access_token': token,
            'expiry': self.expiry
        })

    def tearDown(self):
        super(TestTokenCache, self).tearDown()
        self.api_patch.stop()

    @gen_test
    def test_cache(self):
        token1 = yield oauth2.get_token('https://localhost:8007',
                                        '4225f4774d6874a68565a04130001144',
                                        'FMjU7vNIay5HGNABQVTTghOfEJqbet')

        assert token1 == self.token1

        token2 = yield oauth2.get_token('https://localhost:8007',
                                        '4225f4774d6874a68565a04130001144',
                                        'FMjU7vNIay5HGNABQVTTghOfEJqbet')

        assert token2 == token1, 'Should receive a cached token'

    @gen_test
    def test_no_cache(self):
        token1 = yield oauth2.get_token('https://localhost:8007',
                                        '4225f4774d6874a68565a04130001144',
                                        'FMjU7vNIay5HGNABQVTTghOfEJqbet')

        assert token1 == self.token1

        token2 = yield oauth2.get_token('https://localhost:8007',
                                        '4225f4774d6874a68565a04130001144',
                                        'FMjU7vNIay5HGNABQVTTghOfEJqbet',
                                        cache=False)

        assert token2 == self.token2, 'Should not receive a cached token'

    @gen_test
    def test_expired_token(self):
        self.expiry = self.expiry - oauth2.RequestToken.max_until_expired * 3

        token1 = yield oauth2.get_token('https://localhost:8007',
                                        '4225f4774d6874a68565a04130001144',
                                        'FMjU7vNIay5HGNABQVTTghOfEJqbet')

        assert token1 == self.token1

        token2 = yield oauth2.get_token('https://localhost:8007',
                                        '4225f4774d6874a68565a04130001144',
                                        'FMjU7vNIay5HGNABQVTTghOfEJqbet')

        assert token2 == self.token2, 'Should not use an expired cached token'

    def test_purge_cache(self):
        n = oauth2.get_token.max_cache_size
        expired_time = self.expiry - oauth2.RequestToken.max_until_expired * 3
        expired_items = [(i, {'expiry': expired_time})
                         for i in range(int(n * 1.5))]

        unexpired_items = [(i, {'expiry': self.expiry + i})
                           for i in range(int(n * 1.5), n * 2)]

        oauth2.get_token._cache = dict(expired_items + unexpired_items)
        oauth2.get_token.purge_cache()

        assert oauth2.get_token._cache == dict(unexpired_items)

    def test_purge_cache_with_many_unexpired(self):
        n = oauth2.get_token.max_cache_size
        items = [(i, {'expiry': self.expiry + i}) for i in range(n * 2)]

        oauth2.get_token._cache = dict(items)
        oauth2.get_token.purge_cache()

        assert oauth2.get_token._cache == dict(items[n:])

    def test_purge_cache_with_few_unexpired(self):
        items = {i: {'expiry': self.expiry + i} for i in range(10)}

        oauth2.get_token._cache = items
        oauth2.get_token.purge_cache()

        assert oauth2.get_token._cache == items
