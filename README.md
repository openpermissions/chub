Open Permissions Platform - Python Client
===========================

An asynchronous client api to interface with the Open Permissions Platform RESTful services

Usage
-----

    from chub import API
    from tornado.ioloop import IOLoop

    # synchronous client post request
    registration = API('https://acc-stage.copyrighthub.org/v1/accounts',
                       async=False)
    user = registration.users.post(first_name='john',
                                   last_name='bull',
                                   email='john.bull@mycompany.com',
                                   username='johnbull',
                                   password='3832j942cu2d')

    # synchronous client get request
    api = API('https://repo-stage.copyrighthub.org/v1/repository',
                     async = False)
    offer = api.offers['OFFER-01'].get()

    # asynchronous client post request
    registration = API('https://acc-stage.copyrighthub.org/v1/accounts',
                       async=True)


    @coroutine
    def async_post_test():
        user = yield registration.users.post(first_name='john',
                                             last_name='bull',
                                             email='john.bull@mycompany.com',
                                             username='johnbull',
                                             password='3832j942cu2d')
        raise Return(user)

    def async_post_test_callback():
        def do_something_with_user(user):
            print user['username']
            # blah
            IOLoop.instance().stop()
        registration.users.post(first_name='john',
                                last_name='bull',
                                email='john.bull@mycompany.com',
                                username='johnbull',
                                password='3832j942cu2d',
                                callback=do_something_with_the_user)
    async_post_test_callback()
    IOLoop.instance().start()


    # asynchronous client get request
    api = API('https://repo-stage.copyrighthub.org/v1/repository',
              async = True)

    @coroutine
    def async_get_test():
        offer = yield api.offers['OFFER-01'].get()
        raise Return(offer)

    def async_get_test_callback():
        def do_something_with_offer(offer):
            print('Offer = ' , offer)
        IOLoop.instance().stop()
        api.offers['OFFER-01'].get(callback=do_something_with_offer)
    async_test()
    IOLoop.instance().start()

Check the examples directory for more.

Documentation
-------------

Documentation generated from the source can be found at http://chub.readthedocs.org/en/stable/
