Development
###########

Contributing
============

The source code is available on `GitHub <https://github.com/ivoire/ReactOBus>`_
and on `Framagit <https://framagit.org/ivoire/ReactOBus>`_.

You can use both instances for submitting pull-requests or issues.


Testing
=======

In order to test ReactOBus, you should install `py.test <http://docs.pytest.org/en/latest/>`_:

    pip install pytest

Then run the test with:

    py.test -v tests

The code should be also *pep8* clean:

    pep8 ReactoBus
    pep8 reactobus


Continuous integration
======================

The tests are run on each push to the github repository, thanks to Travis-CI.
The results are:

* `Test results <https://travis-ci.org/ivoire/ReactOBus>`_
* `Coverage report <https://coveralls.io/github/ivoire/ReactOBus>`_
* `Static analysis <https://landscape.io/github/ivoire/ReactOBus>`_
