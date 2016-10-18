from lib.reactor import Matcher


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
                   "args": ["topic", "$topic", "username", "$username"],
                   "timeout": 1}}

rule_4 = {"name": "non_existing_binary",
          "match": {"field": "topic",
                    "pattern": "^org.reactobus.lava"},
          "exec": {"path": "not_in_path",
                   "args": ["topic", "$topic", "username", "$username"],
                   "timeout": 1}}

rule_6 = {"name": "empty_in_args",
          "match": {"field": "topic",
                    "pattern": "^org.reactobus.lava"},
          "exec": {"path": "/bin/true",
                   "args": [],
                   "timeout": 1}}


def test_simple_matching():
    m = Matcher(rule_1)

    assert m.match({"topic": "org.reactobus.lava"}) is True
    assert m.match({"topic": "org.reactobus.lava.job"}) is True
    assert m.match({"topic": "reactobus.lava"}) is False
    # Non existing field will return False
    assert m.match({"topi": "reactobus.lava"}) is False


def test_simple_matching_2():
    m = Matcher(rule_2)

    assert m.match({"topic": "something", "username": "a_kernel_"}) is True
    # Non existing field will return False
    assert m.match({"topic": "something", "user": "a_kernel_"}) is False


def test_data_matching():
    m = Matcher(rule_3)

    assert m.match({"data": {"submitter": "kernel-ci"}}) is True
    assert m.match({"data": {"submitter": "kernel"}}) is False
