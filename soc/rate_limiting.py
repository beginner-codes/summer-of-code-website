from collections import defaultdict, deque
from functools import partial
from typing import Any, Awaitable

import pendulum
from bevy import Inject
from bevy.providers.function_provider import bevy_method
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

import soc.auth_helpers as auth_helpers
import soc.context as context
from soc.config.models.authentication import AuthenticationSettings
from soc.database import Database


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


class RateLimitMiddleware:
    def __init__(self, app: FastAPI):
        self.app = app
        self.tracking = RequestTracking()
        self.bevy = self.app.dependency_overrides.get(
            context.create_context, context.create_context
        )()

    def __call__(self, request: Request, call_next) -> Awaitable[Response]:
        session_info = self._get_session_info(request)
        session_id = session_info.get("session_id", 0)
        if session_id:
            self.tracking.add_request(session_id)
            if self.tracking.should_rate_limit(session_id):
                return self._send_rate_limit_response(session_info)

        return call_next(request)

    @bevy_method
    def _get_session_info(
        self, request: Request, auth_settings: AuthenticationSettings = Inject
    ) -> dict[str, Any]:
        auth_header = request.headers.get("Authorization", "")
        if "bearer" not in auth_header.casefold():
            return {}

        _, session_token = auth_header.split(" ", maxsplit=1)
        return auth_helpers.parse_token(session_token, auth_settings)

    @bevy_method
    async def _send_rate_limit_response(
        self, session_info: dict[str, Any], db: Database = Inject
    ) -> Response:
        session = await auth_helpers.get_session_data(session_info, db)
        session.revoked = True
        await session.sync()
        return JSONResponse({"detail": "Too Many Requests"}, status_code=429)
