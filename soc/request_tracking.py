from collections import defaultdict, deque
from functools import partial

import pendulum


class RequestTracking:
    def __init__(self):
        self.sessions: defaultdict[int, deque[pendulum.DateTime]] = defaultdict(
            partial(deque, maxlen=50)
        )

    def add_request(self, session_id: int):
        self.sessions[session_id].appendleft(pendulum.now())

    def should_rate_limit(self, session_id: int) -> bool:
        now = pendulum.now()
        last_10_seconds = len(
            [
                1
                for request_time in self.sessions[session_id]
                if (now - request_time) < pendulum.Duration(seconds=10)
            ]
        )
        return last_10_seconds > 20
