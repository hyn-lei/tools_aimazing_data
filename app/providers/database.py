from contextvars import ContextVar

from peewee import _ConnectionState, PostgresqlDatabase
from playhouse.pool import PooledMySQLDatabase

from config.database import settings

db_state_default = {"closed": None, "conn": None, "ctx": None, "transactions": None}
db_state = ContextVar("db_state", default=db_state_default.copy())
db_state2 = ContextVar("db_state", default=db_state_default.copy())


class PeeweeConnectionState(_ConnectionState):
    def __init__(self, **kwargs):
        super().__setattr__("_state", db_state)
        super().__init__(**kwargs)

    def __setattr__(self, name, value):
        self._state.get()[name] = value

    def __getattr__(self, name):
        return self._state.get()[name]


async def reset_db_state():
    db._state._state.set(db_state_default.copy())
    db._state.reset()


db = PostgresqlDatabase(
    settings.DATABASE,
    user=settings.USER,
    host=settings.HOST,
    password=settings.PASSWORD,
    port=settings.PORT,
    options="-c search_path=aimazing",
)

db._state = PeeweeConnectionState()


class PeeweeConnectionState2(_ConnectionState):
    def __init__(self, **kwargs):
        super().__setattr__("_state", db_state2)
        super().__init__(**kwargs)

    def __setattr__(self, name, value):
        self._state.get()[name] = value

    def __getattr__(self, name):
        return self._state.get()[name]


db_blog = PostgresqlDatabase(
    settings.DATABASE,
    user=settings.USER,
    host=settings.HOST,
    password=settings.PASSWORD,
    port=settings.PORT,
    options="-c search_path=blog_1kcode",
)

db_blog._state = PeeweeConnectionState2()
