# -*- coding: utf-8 -*-
# Copyright 2016 Open Permissions Platform Coalition
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
# 


from chub import API
from tornado.ioloop import IOLoop
from tornado.gen import coroutine


onboarding = API('https://on-stage.copyrighthub.org/v1/onboarding')
accounts = API('https://acc-stage.copyrighthub.org/v1/accounts')


def async_call_callback_style():
    def _process_capability_response(response):
        print 'max_file_size =', response['max_file_size']
        IOLoop.current().stop()

    onboarding.capabilities.get(callback=_process_capability_response)
    IOLoop.instance().start()


@coroutine
def async_call_coroutine_style():
    response = yield onboarding.capabilities.get()
    print 'max_file_size =', response['max_file_size']


@coroutine
def custom_request():
    body = """\
    supplier_id_type,supplier_id,asset_id_types,asset_ids,offer_ids,description
    examplecosupplierid,examplecopicturelibrary,examplecopictureid,100123,1~2~3~4,Sunset over a Caribbean beach
    """
    onboarding.repositories.repo1.assets.prepare_request(
        headers={'Content-Type': 'text/csv'},
        body=body.strip())
    response = yield onboarding.repositories.repo1.assets.post()
    print response


@coroutine
def post_data_as_parameters():
    response = yield accounts.login.post(
        email='john.bull@mycompany.com',
        password='3832j942cu2d')
    print 'token =', response['token']


def main():
    print '-' * 20
    async_call_callback_style()
    print '-' * 20
    IOLoop.instance().run_sync(async_call_coroutine_style)
    print '-' * 20
    IOLoop.instance().run_sync(custom_request)
    print '-' * 20
    IOLoop.instance().run_sync(post_data_as_parameters)


if __name__ == '__main__':
    main()
