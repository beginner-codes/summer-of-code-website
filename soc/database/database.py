from bevy import Bevy, Inject

from soc.database.users import Users


class Database(Bevy, inject=Inject.ALL):
    users: Users
