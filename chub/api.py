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
this module has classes for converting python method calls
to request on RESTful api
"""
import inspect
from functools import partial
from urlparse import urljoin
from urllib import quote_plus

from tornado.httpclient import HTTPRequest

from .handlers import make_fetch_func, DEFAULT_HEADERS


HTTP_METHODS = ['GET', 'POST', 'HEAD', 'PUT', 'PATCH', 'DELETE',
                'OPTIONS', 'TRACE', 'CONNECT']

API_VERSION = 'v1'


class Resource(object):
    """
    Resource converts python method calls to request on RESTful api
    """

    def __init__(self, path, fetch, resource_map=None,
                 request_class=HTTPRequest, default_headers=None):
        self.path = path
        self.fetch = fetch
        if resource_map is None:
            self.resource_map = {}
        else:
            self.resource_map = resource_map
        self.request_class = request_class
        self.http_request = None
        if not default_headers:
            default_headers = dict(DEFAULT_HEADERS)
        self.default_headers = default_headers

    def __getattr__(self, key):
        if key.upper() in HTTP_METHODS:
            # tornado will take either an HTTPRequest object or a url
            # an HTTPRequest object will be used directly
            # a url will be converted into one by tornado
            request = self.http_request if self.http_request else self.path
            return partial(self.fetch, request=request, method=key.upper(),
                           default_headers=self.default_headers)
        path = '/'.join((self.path, key))
        return self._sub_resource(path)

    def _sub_resource(self, path):
        """
        get or create sub resource
        """
        if path not in self.resource_map:
            self.resource_map[path] = Resource(
                path, self.fetch, self.resource_map,
                default_headers=self.default_headers)
        return self.resource_map[path]

    def __getitem__(self, entity_id):
        path = '/'.join((self.path, quote_plus(entity_id)))
        return self._sub_resource(path)

    def prepare_request(self, *args, **kw):
        """
        creates a full featured HTTPRequest objects
        """
        self.http_request = self.request_class(self.path, *args, **kw)


class API(Resource):
    """
    API takes the base_url and a boolean async . Based on value of async
    an async or sync fetch function is set
    """

    mappings = {}

    def __init__(self, base_url, async=True, api_version=API_VERSION,
                 token=None, **kwargs):
        self.base_url = urljoin(base_url, api_version)
        fetch = make_fetch_func(self.base_url, async, **kwargs)
        super(API, self).__init__(self.base_url, fetch)
        if token:
            self.token = token

    @property
    def token(self):
        """
        get the token
        """
        header = self.default_headers.get('Authorization', '')
        prefex = 'Bearer '
        if header.startswith(prefex):
            token = header[len(prefex):]
        else:
            token = header
        return token

    @token.setter
    def token(self, token):
        """
        set the token
        """
        self.default_headers['Authorization'] = 'Bearer {}'.format(token)

    def _request(self):
        """
        retrieve the caller frame, extract the parameters from
        the caller function, find the matching function,
        and fire the request
        """
        caller_frame = inspect.getouterframes(inspect.currentframe())[1]
        args, _, _, values = inspect.getargvalues(caller_frame[0])
        caller_name = caller_frame[3]
        kwargs = {arg: values[arg] for arg in args if arg != 'self'}
        func = reduce(
            lambda resource, name: resource.__getattr__(name),
            self.mappings[caller_name].split('.'), self)
        return func(**kwargs)


class Accounts(API):
    """
    API client for accounts service
    """

    mappings = {
        'info': 'accounts.get',
        'login': 'accounts.login.post',
        'register_service': 'accounts.services.post'}

    def info(self):
        """
        get service information
        """
        return self._request()

    def login(self, email, password):
        """
        login using email and password
        :param email: email address
        :param password: password
        """
        rsp = self._request()
        self.default_headers['Authorization'] = rsp.data['token']
        return rsp

    def register_service(self, name, location, organisation_id, certificate):
        """
        register a service
        :param name: name of the service
        :param location: url of the service
        :param organisation_id: organisation id
        :param certificate: ssl certificate
        """
        return self._request()
