# -*- coding: utf-8 -*-
# Copyright 2016 Open Permissions Platform Coalition
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
#

"""
this module has some handler utilities for HTTP request and response
"""
import collections
import urllib
import json
from functools import partial

from tornado.httpclient import AsyncHTTPClient, HTTPClient, HTTPRequest
from tornado.gen import coroutine, Return

JSON_TYPE = 'application/json'
DEFAULT_HEADERS = (('Content-Type', 'application/json'),)


def convert(data):
    """
    convert a standalone unicode string or unicode strings in a
    mapping or iterable into byte strings.
    """
    if isinstance(data, unicode):
        return data.encode('utf-8')
    elif isinstance(data, str):
        return data
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data


def make_request(request, method, default_headers=None, **kwargs):
    """
    convert parameters into relevant parts
    of the an http request
    :param request: either url or an HTTPRequest object
    :param method: http request method
    :param default_headers: default headers
    :param kwargs: headers, query string params for GET and DELETE,
    data for POST and PUT
    """
    kwargs = convert(kwargs)
    if not default_headers:
        headers = dict(DEFAULT_HEADERS)
    else:
        headers = default_headers.copy()
    if isinstance(request, HTTPRequest):
        headers.update(request.headers)
    if 'headers' in kwargs:
        headers.update(kwargs.pop('headers'))
    if isinstance(request, HTTPRequest):
        request.method = method
        request.headers.update(headers)
    else:
        request = HTTPRequest(request, method, headers)
    if kwargs:
        if method in ['GET', 'DELETE']:
            request.url = "{}?{}".format(request.url, urllib.urlencode(kwargs))
        elif method in ['POST', 'PUT']:
            if request.headers['Content-Type'] == JSON_TYPE:
                request.body = json.dumps(kwargs)
            elif 'body' in kwargs:
                request.body = kwargs['body']
    return request


class ResponseObject(dict):
    """
    Access the value of in a dictionary by using
    the key as attribute.
    >>> obj = ResponseObject()
    >>> obj['foo'] = 'bar'
    >>> obj.foo
    'bar'
    """
    def __getattr__(self, key):
        return self.__getitem__(key)


def parse_response(response):
    """
    parse response and return a dictionary if the content type.
    is json/application.
    :param response: HTTPRequest
    :return dictionary for json content type otherwise response body
    """
    if response.headers.get('Content-Type', JSON_TYPE).startswith(JSON_TYPE):
        return ResponseObject(json.loads(response.body))
    else:
        return response.body


def sync_fetch(request, method, default_headers=None,
               httpclient=None, **kwargs):
    """
    fetch resource using the synchronous HTTPClient
    :param request: HTTPRequest object or a url
    :param method: HTTP method in string format, e.g. GET, POST
    :param kwargs: query string entities or POST data
    """
    updated_request = make_request(request, method, default_headers, **kwargs)
    if not httpclient:
        httpclient = HTTPClient()
    rsp = httpclient.fetch(updated_request)
    return parse_response(rsp)


@coroutine
def async_fetch(request, method, default_headers=None,
                callback=None, httpclient=None, **kwargs):
    """
    fetch resource using the asynchronous AsyncHTTPClient
    :param request: HTTPRequest object or a url
    :param method: HTTP method in string format, e.g. GET, POST
    :param callback: callback function on the result. it is used
    by the coroutine decorator.
    :param kwargs: query string entities or POST data
    """
    updated_request = make_request(request, method, default_headers, **kwargs)
    if not httpclient:
        httpclient = AsyncHTTPClient()
    rsp = yield httpclient.fetch(updated_request)
    raise Return(parse_response(rsp))


def make_fetch_func(base_url, async, **kwargs):
    """
    make a fetch function based on conditions of
    1) async
    2) ssl
    """
    if async:
        client = AsyncHTTPClient(force_instance=True, defaults=kwargs)
        return partial(async_fetch, httpclient=client)
    else:
        client = HTTPClient(force_instance=True, defaults=kwargs)
        return partial(sync_fetch, httpclient=client)
