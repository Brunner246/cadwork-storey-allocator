class DumpDecorator:
    def __init__(self):
        self.registry = {}

    def register(self, cls):
        self.registry[cls.__name__] = cls
        return cls
