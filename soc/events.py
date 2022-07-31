import asyncio
from collections import defaultdict
from inspect import isawaitable
from typing import Any, Awaitable, Callable


class Events:
    def __init__(self):
        self._handlers = defaultdict(set)

    def on(self, event_name: str, callback: Callable[[Any], Awaitable | Any]):
        self._handlers[event_name].add(callback)

    def off(self, event_name, callback: Callable[[Any], Awaitable | Any]):
        self._handlers[event_name].remove(callback)

    def dispatch(self, event_name: str, *payload: Any, loop=None) -> asyncio.Future:
        tasks = []
        loop = loop or asyncio.get_event_loop()
        for handler in self._handlers[event_name]:
            result = handler(*payload)
            if isawaitable(result):
                tasks.append(loop.create_task(result))

        return asyncio.gather(*tasks)
