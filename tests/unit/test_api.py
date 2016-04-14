# -*- coding: utf-8 -*-
# Copyright 2016 Open Permissions Platform Coalition
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
# 

from tornado.httpclient import AsyncHTTPClient, HTTPClient
from chub import API
from chub.api import API_VERSION
from mock import patch
import pytest


def test_async_api():
    api = API('http://example.com')
    assert api.base_url == 'http://example.com/' + API_VERSION
    isinstance(api.fetch.keywords['httpclient'], AsyncHTTPClient)


def test_sync_api():
    api = API('http://example.com', async=False)
    assert api.base_url == 'http://example.com/' + API_VERSION
    isinstance(api.fetch.keywords['httpclient'], HTTPClient)


def test_base_url_ends_with_slash():
    api = API('http://example.com/')
    assert api.base_url == 'http://example.com/' + API_VERSION


def test_without_token():
    api = API('http://example.com/')
    assert api.token == ''
    assert 'Authorization' not in api.default_headers


@pytest.mark.parametrize('header,token', [
    ('Bearer a token', 'a token'),
    ('Bearer some other token', 'some other token'),
    ('Bearer Bearer a token', 'Bearer a token'),
])
def test_with_token(header, token):
    api = API('http://example.com/', token=token)
    assert api.token == token
    assert api.default_headers['Authorization'] == header


@patch('chub.api.partial')
def test_request(mock_partial):

    class MyAPI(API):
        mappings = {'foo': 'foo.get',
                    'bar_baz': 'bar.baz.get'}

        def foo(self, arg1, arg2, arg3, arg4):
            return self._request()

        def bar_baz(self, arg1, arg2, arg3, arg4):
            return self._request()

    my_api = MyAPI('http://example.com', async=False)
    my_api.foo(1, 2, arg3=3, arg4=4)
    kwargs = mock_partial.call_args[1]
    assert kwargs['request'] == 'http://example.com/v1/foo'
    assert kwargs['method'] == 'GET'
    assert mock_partial.return_value.call_args[1] == {
        'arg1': 1, 'arg2': 2, 'arg3': 3, 'arg4': 4}

    mock_partial.reset()

    my_api.bar_baz(1, 2, arg3=3, arg4=4)
    kwargs = mock_partial.call_args[1]
    assert kwargs['request'] == 'http://example.com/v1/bar/baz'
    assert kwargs['method'] == 'GET'
    assert mock_partial.return_value.call_args[1] == {
        'arg1': 1, 'arg2': 2, 'arg3': 3, 'arg4': 4}
