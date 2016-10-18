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

def test_simple_matching():
    m = Matcher(rule_1)

    assert m.match({"topic": "org.reactobus.lava"}) is True
    assert m.match({"topic": "org.reactobus.lava.job"}) is True
    assert m.match({"topic": "reactobus.lava"}) is False
    # Non existing field will return False
    assert m.match({"topi": "reactobus.lava"}) == False


def test_simple_matching_2():
    m = Matcher(rule_2)

    assert m.match({"topic": "something", "username": "a_kernel_"}) is True
    # Non existing field will return False
    assert m.match({"topic": "something", "user": "a_kernel_"}) is False
