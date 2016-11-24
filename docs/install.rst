.. index:: installation

Installation
############

Releases
========

ReactOBus official releases are avaiable directly on `pypi
<https://pypi.python.org/pypi/ReactOBus/>`_ and can be installed with::

    pip install ReactOBus

By default, **pip** will not install SQLAlchemy. If need, install it manually
afterward or ask pip to include the right ReactOBus variant with::

    pip install ReactOBus[db]


Development versions
=====================

It's also possible to execute ReactOBus directly from the sources::

    git clone https://github.com/ivoire/ReactOBus.git
    cd ReactOBus
    virtualenv -p python3.5 venv
    source venv/bin/activate
    pip install -r requirements.txt
    python reactobus --level DEBUG --conf share/examples/reactobus.yaml

In this case, **SQLAlchemy** will be installed by default as it's included in
*requirements.txt*.
