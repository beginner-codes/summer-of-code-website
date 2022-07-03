from bevy import Bevy, Inject

from soc.database.sessions import Sessions
from soc.database.users import Users


class Database(Bevy, inject=Inject.ALL):
    sessions: Sessions
    users: Users
