import multiprocessing


class Pipe(multiprocessing.Process):
    classname = ""

    @classmethod
    def select(cls, classname, name, options, inbound):
        for sub in cls.__subclasses__():
            if sub.classname == classname:
                return sub(name, options, inbound)
        raise NotImplementedError

    def setup(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError
