from bevy import Bevy, Inject
from soc.response import Response


class Controller(Bevy):
    response: Response = Inject

    async def run(self):
        ...
