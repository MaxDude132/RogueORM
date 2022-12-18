from abc import ABCMeta, abstractmethod


class BaseDatabaseClient(metaclass=ABCMeta):
    _instances = None
    _db_name = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, db_name):
        self._db_name = db_name

        self._connection = None

    @abstractmethod
    def get_connection(self):
        pass

    @abstractmethod
    def execute(self, statement, *args, **kwargs):
        pass

    @abstractmethod
    def close(self):
        pass


class BaseDatabaseSchemaEditor:
    pass
