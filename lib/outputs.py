class Output(object):
    name = ""
    @classmethod
    def select(cls, classname):
        for sub in cls.__subclasses__():
            if sub.name == classname:
                return sub()
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

class ZMQPub(Output):
    name = "ZMQPub"
