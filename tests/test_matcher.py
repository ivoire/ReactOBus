# -*- coding: utf-8 -*-
# vim: set ts=4

# Copyright 2016 Rémi Duraffort
# This file is part of ReactOBus.
#
# ReactOBus is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ReactOBus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with ReactOBus.  If not, see <http://www.gnu.org/licenses/>

import pytest
import subprocess

from ReactOBus.reactor import Matcher


rule_1 = {"name": "first test",
          "match": {"field": "topic",
                    "pattern": "^org.reactobus.lava"},
          "exec": {"path": "/bin/true",
                   "args": ["topic", "$topic", "username", "$username"],
                   "timeout": 1}}

rule_2 = {"name": "second test",
          "match": {"field": "username",
                    "pattern": ".*kernel.*"},
          "exec": {"path": "/bin/true",
                   "args": ["topic", "$topic", "username", "$username"],
                   "timeout": 1}}

rule_3 = {"name": "data matching",
          "match": {"field": "data.submitter",
                    "pattern": "kernel-ci"},
          "exec": {"path": "/bin/true",
                   "args": ["topic", "$topic", "submitter", "$data.submitter"],
                   "timeout": 1}}

rule_4 = {"name": "non_existing_binary",
          "match": {"field": "topic",
                    "pattern": "^org.reactobus.lava"},
          "exec": {"path": "not_in_path",
                   "args": ["topic", "$topic", "username", "$username"],
                   "timeout": 1}}

rule_5 = {"name": "non_existing_field",
          "match": {"field": "topi",
                    "pattern": "^org.reactobus.lava"},
          "exec": {"path": "/bin/true",
                   "args": ["topic", "$topi", "username", "$username"],
                   "timeout": 1}}

rule_6 = {"name": "empty_in_args",
          "match": {"field": "topic",
                    "pattern": "^org.reactobus.lava"},
          "exec": {"path": "/bin/true",
                   "args": [],
                   "timeout": 1}}

rule_7 = {"name": "stdin",
          "match": {"field": "topic",
                    "pattern": "^org.reactobus.lava"},
          "exec": {"path": "/bin/true",
                   "args": ["stdin", "stdin:hello", "stdin:$topic",
                            "$data.submitter", "stdin:$data.submitter"],
                   "timeout": 4}}


def test_simple_matching():
    m = Matcher(rule_1)

    assert m.match({"topic": "org.reactobus.lava"}, {}) is True
    assert m.match({"topic": "org.reactobus.lava.job"}, {}) is True
    assert m.match({"topic": "reactobus.lava"}, {}) is False
    # Non existing field will return False
    assert m.match({"topi": "reactobus.lava"}, {}) is False


def test_simple_matching_2():
    m = Matcher(rule_2)

    assert m.match({"topic": "something", "username": "a_kernel_"}, {}) is True
    # Non existing field will return False
    assert m.match({"topic": "something", "user": "a_kernel_"}, {}) is False


def test_data_matching():
    m = Matcher(rule_3)

    assert m.match({}, {"submitter": "kernel-ci"}) is True
    assert m.match({}, {"submitter": "kernel"}) is False


def test_lookup():
    assert Matcher.lookup("username", {"username": "kernel"}, {}) == "kernel"
    assert Matcher.lookup("msg",
                          {"username": "kernel",
                           "msg": "hello"}, {}) == "hello"

    assert Matcher.lookup("data", {"msg": "something"}, {}) == {}
    assert Matcher.lookup("data", {"msg": "something"},
                          {"hello": "world"}) == {"hello": "world"}

    assert Matcher.lookup("data.key", {"msg": "something"},
                          {"key": "value"}) == "value"
    assert Matcher.lookup("data.hello", {"msg": "something"},
                          {"hello": "world"}) == "world"

    with pytest.raises(KeyError):
        Matcher.lookup("msg", {}, {})
    with pytest.raises(KeyError):
        Matcher.lookup("msg", {}, {"msg": "value"})
    with pytest.raises(KeyError):
        Matcher.lookup("msg", {"username": "kernel"}, {})
    with pytest.raises(KeyError):
        Matcher.lookup("data.username", {"username": "kernel"}, {})


def test_build_args():
    m = Matcher(rule_1)

    # Test for classical substitution
    (args, stdin) = m.build_args("org.reactobus.lava.hello", "uuid", "",
                                 "lavauser", {})
    assert args == [m.binary, "topic", "org.reactobus.lava.hello",
                    "username", "lavauser"]
    assert stdin == ''
    (args, stdin) = m.build_args("org.reactobus.lava.something", "uuid",
                                 "erty", "kernel-ci", {})
    assert args == [m.binary, "topic", "org.reactobus.lava.something",
                    "username", "kernel-ci"]
    assert stdin == ''

    # Test for data.* substitution
    m = Matcher(rule_3)
    (args, stdin) = m.build_args("org.reactobus", "uuid", "", "lavauser",
                                 {"submitter": "health"})
    assert args == [m.binary, "topic", "org.reactobus", "submitter", "health"]
    assert stdin == ''

    # Without args
    m = Matcher(rule_6)
    (args, stdin) = m.build_args("org.reactobus", "uuid", "", "lavauser",
                                 {"submitter": "health"})
    assert args == [m.binary]
    assert stdin == ''

    # With "stdin:" and "$data."
    m = Matcher(rule_7)
    (args, stdin) = m.build_args("org.reactobus", "uuid", "", "",
                                 {"submitter": "kernel-ci", "key": "value"})
    assert args == [m.binary, "stdin", "kernel-ci"]
    assert stdin == "hello\norg.reactobus\nkernel-ci"

    with pytest.raises(KeyError):
        (args, stdin) = m.build_args("org.reactobus", "uuid", "", "",
                                     {"key": "value"})


def test_build_args_errors():
    m = Matcher(rule_5)

    with pytest.raises(KeyError):
        m.build_args("org.reactobus.lava.hello", "uuid", "", "lavauser", {})

    m = Matcher(rule_3)
    with pytest.raises(KeyError):
        m.build_args("org.reactobus", "uuid", "", "lavauser",
                     {"username": "health"})


def test_run(monkeypatch):
    m_args = []
    m_input = ""
    m_timeout = 0

    def mock_check_output(args, stderr, universal_newlines, input, timeout):
        nonlocal m_args
        nonlocal m_input
        nonlocal m_timeout
        m_args = args
        m_input = input
        m_timeout = timeout
        return ""

    monkeypatch.setattr(subprocess, "check_output", mock_check_output)
    m = Matcher(rule_1)

    m.run("org.reactobus", "uuid", "0", "lavauser", {})
    assert m_args == [m.binary, "topic", "org.reactobus", "username",
                      "lavauser"]
    assert m_input == ""
    assert m_timeout == 1

    m.run("org.reactobus.test", "uuid", "0", "kernel", {})
    assert m_args == [m.binary, "topic", "org.reactobus.test", "username",
                      "kernel"]
    assert m_input == ""
    assert m_timeout == 1

    m = Matcher(rule_7)
    m.run("org.reactobus.test", "uuid", "0", "lavaserver",
          {"submitter": "myself"})
    assert m_args == [m.binary, "stdin", "myself"]
    assert m_input == "hello\norg.reactobus.test\nmyself"
    assert m_timeout == 4

    m_args = None
    m.run("org.reactobus.test", "uuid", "0", "lavaserver",
          {"something": "myself"})
    assert m_args is None


def test_run_raise_oserror(monkeypatch):
    def mock_check_output_raise_oserror(args, stderr, universal_newlines,
                                        input, timeout):
        raise OSError
    monkeypatch.setattr(subprocess, "check_output",
                        mock_check_output_raise_oserror)
    m = Matcher(rule_1)
    m.run("org.reactobus.test", "uuid", "0", "lavaserver",
          {"something": "myself"})


def test_run_raise_timeout(monkeypatch):
    def mock_check_output_raise_oserror(args, stderr, universal_newlines,
                                        input, timeout):
        import subprocess
        raise subprocess.TimeoutExpired(args[0], timeout)
    monkeypatch.setattr(subprocess, "check_output",
                        mock_check_output_raise_oserror)
    m = Matcher(rule_1)
    m.run("org.reactobus.test", "uuid", "0", "lavaserver",
          {"something": "myself"})
