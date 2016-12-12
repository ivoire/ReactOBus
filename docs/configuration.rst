.. _configuration:

Configuration
#############

The configuration file is a YAML dictionary containing:

* *inputs*: a list of input streams
* *outputs*: a list of output streams
* *core*: configuration of the internal sockets
* *reactor*: the reacting part of ReactOBus
* *db*: the database configuration

.. note:: All keys except *core* and *inputs* are optional. If the optional
  keys are not found in the configuration, the corresponding modules won't be
  loaded.

  For instance, if the *outputs* key is not found in the configuration, the
  messages won't be forwarded outside of ReactOBus.

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

If the PUSH sockets are sending encrypted content, you should add the following configuration:

.. code-block:: yaml

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

This class allows to subscribe to a ZMQ PUB socket. The *options* are:

* *url*: the url of the PUB socket

For an encrypted socket, you should add:

.. code-block:: yaml

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

The *reactor* is the module that will execute sub-commands when a given message
is received.

.. include:: reactobus-conf.yaml
     :code: yaml
     :start-after: # reactor
     :end-before: # database

The reactor configuration is made of two keys:

* *workers*: the number of workers that will execute the sub-commands
* *rules*: a list of dictionaries describing the different rules to execute

A rule describes a command to execute when a message matches the rule
conditions.

A rule description is made of:

* *name*: the name used in the logs
* *math*: the matching rule as a dictionary:

  * *field*: the field to match
  * *pattern*: the regular expression that should match the field content

* *exec*: the sub-command as a dictionary:

  * *path*: path to the binary or script to execute
  * *timeout*: timeout for the sub-command
  * *args*: a list of arguments for the sub-command

The available fields are:

* topic
* uuid
* datetime
* username
* data

The available arguments are build using the following algorithm:

* "topic": won't be changed
* "$topic": will be replaced by the content of the corresponding field
* "$data.url": will be replace by the content of data["url"]

If the argument is prefixed by *stdin* then the content will be send to the
sub-command standard input:

* "stdin:something"
* "stdin:$uuid"
* "stdin:$data.is_finished"


Database
========

This module allows to store all the received messages into a database. This
database can then be exported by tools like `ReactOWeb
<https://github.com/ivoire/ReactOWeb>`_.

.. include:: reactobus-conf.yaml
     :code: yaml
     :start-after: # database
     :end-before: # outputs

The only option is the *url* to the database. This url should be a valid
`SQLAlchemy database url
<http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls>`_.


Outputs
=======

The **outputs** key is a list of dictionaries describing the different
destinations for the messages.

.. include:: reactobus-conf.yaml
     :code: yaml
     :start-after: # outputs

In each dictionary, some fields are required:

* *class*: the name of the output class (*ZMQPush* or *ZMQPub*)
* *name*: the name of this output in the logs and for the name of the subprocess
* *options*: dictionary of options, depending on the class


ZMQPush
*******

This class allows to forward the messages to a ZMQ PULL socket. The *options*
dictionary should include:

* *url*: the url of the PULL socket

In order to encrypt the messages, you should add the following configuration:

.. code-block:: yaml

  options:
    url: tcp://*:5554
    encryption:
      self: /etc/reactobus/certs/PrivatePush.key_secret
      server: /etc/reactobus/certs/PrivatePush-server.key

The encryption keys are both mandatory:

* *self*: the path to the secret certificate of this socket
* *clients*: the server's public certificate


ZMQPub
******

This class allows to publish messages to ZMQ SUB sockets. The *options* are:

* *url*: the url of the PUB socket

It's also possible to send heartbeats regularly. This allows listeners to
detect that the network connection break and to reconnect to the publisher.
In order to use heartbeats, add *heartbeat* to the options:

.. code-block:: yaml

    options:
      url: tcp://127.0.0.1:5555
      heartbeat:
        timeout: 2 # in seconds
        topic: org.reactobus.pub.heartbeat

The options are:

* *timeout*: the heartbeat interval
* *topic*: the topic for the heartbeat messages

.. note:: The hearbeat message is a multipart message consisting of the topic
  and the duration since the last heartbeat.

For an encrypted socket, you should add:

.. code-block:: yaml

    options:
      url: tcp://127.0.0.1:5555
      encryption:
        self: /etc/reactobus/certs/Pub.key_secret
        clients: /etc/reactobus/certs/Pub.d/

The encryption keys are both mandatory:

* *self*: the private certificate of this socket
* *clients*: the path to a directory containing the public certificates of the SUB sockets
