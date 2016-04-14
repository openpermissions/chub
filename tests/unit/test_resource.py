# -*- coding: utf-8 -*-
# Copyright 2016 Open Permissions Platform Coalition
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
# 

from mock import Mock

from tornado.httpclient import HTTPRequest

from chub.api import Resource


fetch = Mock()
world = Resource('world', fetch)


def setup_function(function):
    fetch.reset_mock()


def test_root_resource():
    assert world.path == 'world'


def test_one_level_sub_resource():
    countries = world.countries
    assert isinstance(countries, Resource)
    assert countries.path == 'world/countries'


def test_methods():
    country_getter = world.countries.get
    assert not isinstance(country_getter, Resource)
    continent = 'South America'
    national_dance = 'Samba'
    country_getter(continent=continent, national_dance=national_dance)
    kwargs = fetch.call_args[-1]
    min_expected_kwargs = dict(method='GET',
                               request='world/countries',
                               continent=continent,
                               national_dance=national_dance)
    for item in min_expected_kwargs.items():
        assert item in kwargs.items()

    country_setter = world.countries.post
    assert not isinstance(country_setter, Resource)
    name = 'Utopia'
    founder = 'Sir Thomas More'
    country_setter(name=name, founder=founder)
    kwargs = fetch.call_args[-1]
    min_expected_kwargs = dict(method='POST',
                               request='world/countries',
                               name=name,
                               founder=founder)
    for item in min_expected_kwargs.items():
        assert item in kwargs.items()


def test_resource_item():
    uk = world.countries['uk']
    assert isinstance(uk, Resource)
    assert uk.path == 'world/countries/uk'


def test_two_level_sub_resource():
    uk_cities = world.countries['uk'].cities
    assert isinstance(uk_cities, Resource)
    assert uk_cities.path == 'world/countries/uk/cities'

    london = uk_cities['london']
    assert isinstance(london, Resource)
    assert london.path == 'world/countries/uk/cities/london'

    city_getter = uk_cities.get
    assert not isinstance(city_getter, Resource)
    location = 'north'
    dialect = 'geordie'
    city_getter(location=location, dialect=dialect)
    kwargs = fetch.call_args[-1]
    min_expected_kwargs = dict(method='GET',
                               request='world/countries/uk/cities',
                               location=location,
                               dialect=dialect)
    for item in min_expected_kwargs.items():
        assert item in kwargs.items()


def test_resource_with_hyphen():
    world = Resource('world', fetch)

    time_zones = world.countries.us['time-zones']
    assert time_zones.path == 'world/countries/us/time-zones'


def test_resource_url_encode():
    world = Resource('world', fetch)
    bar = world['http://example.com/foo?name=bar']

    assert bar.path == 'world/http%3A%2F%2Fexample.com%2Ffoo%3Fname%3Dbar'


def test_prepare_request():
    world.secrets.prepare_request(auth_username='user',
                                  auth_password='password')
    world.secrets.get(subject='pyramid')
    req = fetch.call_args[-1]['request']
    assert isinstance(req, HTTPRequest)
    assert req.auth_username == 'user'
    assert req.auth_password == 'password'
