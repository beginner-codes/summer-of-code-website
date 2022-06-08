from bevy import Context

from soc.controller import Controller
from soc.response import Response


class TestController(Controller):
    async def run(self):
        ...


def test_controllers():
    context = Context()
    with context.create(Response, add_to_context=True) as response:
        controller = context.create(TestController, add_to_context=True)
        assert controller.response is response
