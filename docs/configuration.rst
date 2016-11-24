.. index:: configuration

Configuration
#############

The configuration file is a YAML dictionary containing:

* *inputs*: a list of input streams
* *outputs*: a list of output streams
* *core*: configuration of the internal sockets
* *reactor*: the reacting part of ReactOBus
* *db*: the database configuration

All keys except *core* and *inputs* are optional. If the optional keys are not
found in the configuration, the corresponding modules won't be loaded.


Inputs
======

The **inputs** key is a list of dictionaries describing the
different sources of messages.

.. include:: reactobus-conf.yaml
     :code: yaml
     :start-after: # inputs
     :end-before: # core

In each dictionary, some fields are required:

* *class*: the name of the input class (*ZMQPull* or *ZMQSub*)
* *name*: the name of this input in the logs and for the name of the subprocess
* *options*: dictionary of options, depending on the class


ZMQPull
*******

This class allows to receive messages from ZMQ PUSH sockets. The *options*
dictionary should include:

* *url*: the url where to bind the socket

If the PUSH sockets are sending encrypted content, you should add the folowing configuration::

  options:
    url: tcp://*:5554
    encryption:
      self: /etc/reactobus/certs/PullIn.key_secret
      clients: /etc/reactobus/certs/PullIn.d/

The encryption keys are both mandatory:

* *self*: the path to the secret certificate of this socket
* *clients*: the path to a directory containing the public certificates of the PUSH sockets


ZMQSub
******

This class allows to subscribe to a ZMQ PUB socket. the *options* are:

* *url*: the url of the PUB socket

For an encrypted socket, you should add::

    options:
      url: tcp://127.0.0.1:5555
      encryption:
        self: /etc/reactobus/certs/SubIn.key_secret
        server: /etc/reactobus/certs/SubIn-server.key

The encryption keys are both mandatory:

* *self*: the private certificate of this socket
* *server*: the server's public key


Core
====

The **core** key is mandatory and should contains two keys:

* *inbound*: internal incoming socket
* *outbound*: internal outgoing socket

.. include:: reactobus-conf.yaml
     :code: yaml
     :start-after: # core
     :end-before: # reactor

These two sockets are used internally by ReactOBus to send messages between the
different stages of the pipeline.
It's import to configure these sockets correctly because two instances of
ReactOBus should not use the same sockets.

Reactor
=======


Database
========


Outputs
=======



