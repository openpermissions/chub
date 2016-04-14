# -*- coding: utf-8 -*-
# Copyright 2016 Open Permissions Platform Coalition
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
# 

from urlparse import urlparse
import json

from mock import Mock
import pytest

from tornado.httpclient import HTTPRequest
from tornado.ioloop import IOLoop

from chub.handlers import (
    convert, make_request, parse_response, sync_fetch, async_fetch,
    ResponseObject, DEFAULT_HEADERS)


@pytest.mark.parametrize('input,expected', [
    ('foo', 'foo'),
    (u'foo', 'foo'),
    (['foo', u'£'], ['foo', '£']),
    (['foo', '£'], ['foo', '£']),
    ({'foo': u'£'}, {'foo': '£'}),
    ({'foo': [u'£', 'bar']}, {'foo': ['£', 'bar']}),
    ({u'中文': ['你好', u'世界'], 'english': ['hello', 'world']},
     {'中文': ['你好', '世界'], 'english': ['hello', 'world']}),
    ({(u'中文', 'english'): ['你好', 'world']},
     {('中文', 'english'): ['你好', 'world']}),
    (int, int)
])
def test_convert(input, expected):
    assert convert(input) == expected


url = lambda rel: 'http://example.com/{}'.format(rel)
HEADERS = (('User-Agent', 'Python'),
           ('Content-Encoding', 'gzip'))


def test_make_get_request_no_headers():
    request = make_request(url('countries'), 'GET',
                           continent='South America',
                           national_dance='Samba')
    assert isinstance(request, HTTPRequest)
    parsed = urlparse(request.url)
    assert parsed.netloc == 'example.com'
    assert parsed.path == '/countries'
    assert parsed.query == 'national_dance=Samba&continent=South+America'


def test_make_get_request_with_headers():
    request = make_request(url('countries'), 'GET',
                           continent='South America',
                           national_dance='Samba',
                           headers=dict(HEADERS))
    assert isinstance(request, HTTPRequest)
    assert request.headers == dict(HEADERS + DEFAULT_HEADERS)
    parsed = urlparse(request.url)
    assert parsed.netloc == 'example.com'
    assert parsed.path == '/countries'
    assert parsed.query == 'national_dance=Samba&continent=South+America'


def test_make_request_with_default_headers():
    request = make_request(url('countries'), 'GET',
                           continent='South America',
                           national_dance='Samba',
                           headers={'User-Agent': 'firefox'},
                           default_headers=dict(HEADERS))
    assert isinstance(request, HTTPRequest)
    assert request.headers == {'User-Agent': 'firefox',
                               'Content-Encoding': 'gzip'}


def test_make_post_request_with_headers_overlapping_default():
    body = '''\
    name,continent,national dance,national sport
    Brazil,South America,Samba,football'''
    headers = {'Content-Type': 'text/csv'}
    req = HTTPRequest(
        url('countries'), 'POST', headers=headers, body=body)
    request = make_request(req, 'POST')
    assert isinstance(request, HTTPRequest)
    assert request.headers == headers
    parsed = urlparse(request.url)
    assert parsed.netloc == 'example.com'
    assert parsed.path == '/countries'
    assert request.body == body


def test_make_post_request_with_headers_and_params():
    empty_body = ''
    body = '''\
    name,continent,national dance,national sport
    Brazil,South America,Samba,football'''
    headers = {'Content-Type': 'text/csv'}
    req = HTTPRequest(
        url('countries'), 'POST', headers=headers, body=empty_body)
    request = make_request(req, 'POST', body=body)
    assert isinstance(request, HTTPRequest)
    assert request.headers == headers
    parsed = urlparse(request.url)
    assert parsed.netloc == 'example.com'
    assert parsed.path == '/countries'
    assert request.body == body


def test_make_get_request_use_request_object_no_headers():
    req = HTTPRequest(
        url('countries'), 'GET', headers=dict(HEADERS))
    request = make_request(
        req, 'GET', headers={'Content-Type': 'application/json'},
        continent='South America', national_dance='Samba',
    )
    assert isinstance(request, HTTPRequest)
    assert request.headers['Content-Type'] == 'application/json'
    parsed = urlparse(request.url)
    assert parsed.netloc == 'example.com'
    assert parsed.path == '/countries'
    assert parsed.query == 'national_dance=Samba&continent=South+America'


def test_make_post_request_no_headers():
    request = make_request(url('countries'), 'POST',
                           continent='South America',
                           national_dance='Samba')
    assert isinstance(request, HTTPRequest)
    assert request.body == json.dumps(
        {"national_dance": "Samba", "continent": "South America"})
    parsed = urlparse(request.url)
    assert parsed.netloc == 'example.com'
    assert parsed.path == '/countries'


def test_make_post_request_with_headers():
    request = make_request(url('countries'), 'POST',
                           continent='South America',
                           national_dance='Samba',
                           headers=dict(HEADERS))
    assert isinstance(request, HTTPRequest)
    assert request.headers == dict(HEADERS + DEFAULT_HEADERS)
    parsed = urlparse(request.url)
    assert parsed.netloc == 'example.com'
    assert parsed.path == '/countries'
    assert request.body == json.dumps(
        {"national_dance": "Samba", "continent": "South America"})


@pytest.mark.parametrize('content_type', [
    'application/json',
    'application/json; charset=utf-8',
])
def test_parse_response_json_type(content_type):
    response = Mock()
    response.headers = {'Content-Type': 'application/json'}
    data = {'foo': 'bar'}
    response.body = json.dumps(data)
    assert parse_response(response) == data


def test_parse_response_non_json_type():
    response = Mock()
    response.headers = {'Content-Type': 'text/html'}
    data = '<html></html>'
    response.body = data
    assert parse_response(response) == data


def test_sync_fetch():
    params = dict(foo='foo', bar='bar')
    rsp = sync_fetch('http://httpbin.org/get', 'GET', **params)
    assert rsp['args'] == params

    rsp = sync_fetch('http://httpbin.org/post', 'POST', **params)
    assert rsp['json'] == params


def test_async_fetch():
    params = dict(foo='foo', bar='bar')
    func = lambda: async_fetch('http://httpbin.org/get', 'GET', **params)
    rsp = IOLoop.instance().run_sync(func)
    assert rsp['args'] == params


def test_response_object():
    obj = ResponseObject()
    obj['foo'] = 'bar'
    assert obj.foo == 'bar'
