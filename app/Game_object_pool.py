import copy

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class GamePool(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.size = None
        self.pool = None

    def init_pool(self, data):
        self.size = 20
        self.pool = {'free': [], 'busy': []}
        for i in range(self.size):
            self.pool['free'].append(copy.deepcopy(data))

    def borrow(self, data):
        if not self.pool:
            self.init_pool(data)
        if not self.pool['free']:
            #assert False, "No pool space"
            # TODO remove before tournament
            return None
        else:
            pool_object = self.pool['free'].pop()
            self.pool['busy'].append(pool_object)
            return pool_object

    def return_object(self, pool_object):
        #assert pool_object in self.pool['busy']
        self.pool['busy'].remove(pool_object)
        self.pool['free'].append(pool_object)

