import multiprocessing


class Pipe(multiprocessing.Process):
    classname = ""

    @classmethod
    def select(cls, classname, name, options, inbound):
        for sub in cls.subclasses():
            if sub.classname == classname:
                return sub(name, options, inbound)
        raise NotImplementedError

    @classmethod
    def subclasses(cls):
        subcls = []
        for sub in cls.__subclasses__():
            subcls.append(sub)
            child = sub.subclasses()
            if child is not []:
                subcls.extend(child)
        return subcls

    def setup(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError
