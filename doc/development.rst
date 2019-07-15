Development
###########

Contributing
============

The source code is available on `GitLab <https://git.lavasoftware.org/ReactOBus/ReactOBus>`_.

You can create an account on this instance for submitting pull-requests or issues.


Testing
=======

In order to test ReactOBus, you should install `py.test <http://docs.pytest.org/en/latest/>`_:

.. code-block:: shell

    apt-get install black python3-pytest

Then run the test with:

.. code-block:: shell

    pytest-3 -v tests

The code should use *black* format:

.. code-block:: shell

    black .


Continuous integration
======================

The tests are run on each push to the gitlab repository using GitLab CI.
