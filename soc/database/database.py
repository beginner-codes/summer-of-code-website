from bevy import Bevy, Inject

from soc.database.challenges import Challenges
from soc.database.sessions import Sessions
from soc.database.users import Users


class Database(Bevy, inject=Inject.ALL):
    challenges: Challenges
    sessions: Sessions
    users: Users
