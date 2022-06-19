from bevy import Bevy, Inject
from soc.database.database.users import Users


class Database(Bevy, inject=Inject.ALL):
    users: Users
