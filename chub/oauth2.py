# -*- coding: utf-8 -*-
# Copyright 2016 Open Permissions Platform Coalition
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
# 

import logging
import calendar
import urllib
from datetime import datetime

from tornado.gen import coroutine, Return

from . import API

CLIENT_CREDENTIALS = 'client_credentials'
JWT_BEARER = 'urn:ietf:params:oauth:grant-type:jwt-bearer'


class Read(object):
    """Object representing a read scope"""
    def __init__(self, resource_id=None):
        """
        Scope for reading a resource or all resources

        :param resource_id: (optional) the resource ID e.g. service or
            repository ID. If resource_id is not provided the scope will be
            "read"
        """
        self.resource_id = resource_id

    def __repr__(self):
        return '<{}>'.format(str(self))

    def __str__(self):
        if self.resource_id is None:
            return 'read'
        else:
            return 'read[{}]'.format(self.resource_id)

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)

    def __hash__(self):
        return hash(str(self))


class Write(object):
    """Object representing a write scope"""
    def __init__(self, resource_id):
        """
        Scope for writing to a resource

        :param resource_id: the resource ID e.g. service or repository ID
        """
        self.resource_id = resource_id

    def __repr__(self):
        return '<{}>'.format(str(self))

    def __str__(self):
        return 'write[{}]'.format(self.resource_id)

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)

    def __hash__(self):
        return hash(str(self))


class Delegate(object):
    """Object representing a delegate scope"""
    def __init__(self, resource_id, access):
        """
        Scope for delegating access to a resource

        :param resource_id: the resource ID e.g. service or repository ID
        :param access: a Read or Write object, or an appropriate string (e.g.
            "write:1234")
        """
        self.resource_id = resource_id
        self.access = access

    def __repr__(self):
        return '<{}>'.format(str(self))

    def __str__(self):
        return 'delegate[{}]:{}'.format(self.resource_id, self.access)

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)

    def __hash__(self):
        return hash(str(self))


class Scope(object):
    def __init__(self, *scopes):
        """
        A scope object representing a space separated list of scopes

        :param scopes: Read, Write or Delegate objects
        """
        self._scopes = set(scopes)

    def add(self, scope):
        """Add a scope"""
        self._scopes.add(scope)

    def remove(self, scope):
        """Remove a scope """
        try:
            self._scopes.remove(scope)
        except KeyError:
            pass

    def __repr__(self):
        return '<Scope "{}">'.format(str(self))

    def __str__(self):
        return ' '.join(map(str, sorted(self._scopes)))

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)


class RequestToken(object):
    """
    Function object for making token requests with simple caching of the
    responses

    NOTE: errors are not cached
    """
    # Don't re-use a token with less than this many seconds remaining
    max_until_expired = 60
    max_cache_size = 100

    def __init__(self):
        self._cache = {}

    @coroutine
    def __call__(self, base_url, client_id, client_secret, scope=None,
                 jwt=None, cache=True, **kwargs):
        """
        Get an OAuth token

        Example Usage:
            >>> token = get_token('https://localhost:8007',
                                'a service id',
                                'the client secret')

        With a scope:
            >>> token = get_token('https://localhost:8007',
                                'a service id',
                                'the client secret',
                                scope=Scope(Write('another service'),
                                            Write('yet another service')))

            >>> token = get_token('https://localhost:8007',
                                'a service id',
                                'the client secret',
                                scope=Write('just one service'))

        Scope can also just be a string:
            >>> token = get_token('https://localhost:8007',
                                'a service id',
                                'the client secret',
                                scope='delegate:1234:write:5678')

        Exchange a delegate token:
            >>> delegate_token = get_token('https://localhost:8007',
                                        'a service id',
                                        'the client secret',
                                        scope='delegate:1234:write:5678')
            >>> token = get_token('https://localhost:8007',
                                '1234',
                                '1234 secret',
                                jwt=delegate_token,
                                scope='write:5678')


        :param base_url: base auth serivce URL
        :param client_id: the client ID
        :param client_secret: the client secret
        :param scope: (optional) a scope object or string
        :param jwt: (optional) a JWT for the jwt-bearer grant
        :param cache: whether or not to use the in-memory cache
        :param ca_certs: (optional) a CA certificate file
        """
        parameters = {'grant_type': CLIENT_CREDENTIALS}

        if scope is not None:
            parameters['scope'] = str(scope)

        if jwt is not None:
            parameters['grant_type'] = JWT_BEARER
            parameters['assertion'] = jwt

        if cache:
            response = yield self._cached_request(base_url, client_id,
                                                  client_secret, parameters,
                                                  **kwargs)
        else:
            response = yield self._request(base_url, client_id,
                                           client_secret, parameters,
                                           **kwargs)

        raise Return(response['access_token'])

    @coroutine
    def _request(self, base_url, client_id, client_secret,
                 parameters, **kwargs):
        """Make an API request to get the token"""
        logging.debug('Getting an OAuth token for client "%s" with scope "%s"',
                      client_id, parameters.get('scope'))
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'Accept': 'application/json'}

        api = API(base_url,
                  auth_username=client_id,
                  auth_password=client_secret,
                  **kwargs)
        endpoint = api.auth.token

        response = yield endpoint.post(body=urllib.urlencode(parameters),
                                       request_timeout=60,
                                       headers=headers)

        logging.debug('Received token: %s', response.get('access_token'))
        raise Return(response)

    @staticmethod
    def _now():
        return calendar.timegm(datetime.utcnow().timetuple())

    def _expired(self, cached_item):
        max_expiry = self._now() + self.max_until_expired
        return cached_item.get('expiry') < max_expiry

    @coroutine
    def _cached_request(self, base_url, client_id, client_secret,
                        parameters, **kwargs):
        """Cache the token request and use cached responses if available"""
        key = (base_url, client_id, tuple(parameters.items()))
        cached = self._cache.get(key, {})

        if not cached.get('access_token') or self._expired(cached):
            cached = yield self._request(base_url, client_id, client_secret,
                                         parameters, **kwargs)
            self._cache[key] = cached
            # Purge cache when adding a new item so it doesn't grow too large
            # It's assumed the cache size is small enough that it's OK to loop
            # over the whole cache regularly. If not, could change this to
            # just pop off the oldest one
            self.purge_cache()

        logging.debug('Using a cached token: %s', cached.get('access_token'))
        raise Return(cached)

    def reset_cache(self):
        """Reset the token cache"""
        self._cache = {}

    def purge_cache(self):
        """
        Purge expired cached tokens and oldest tokens if more than cache_size
        """
        if len(self._cache) > self.max_cache_size:
            items = sorted(self._cache.items(), key=lambda (k, v): v['expiry'])
            self._cache = {k: v for k, v in items[self.max_cache_size:]
                           if not self._expired(v)}

get_token = RequestToken()
