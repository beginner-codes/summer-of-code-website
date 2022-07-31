from __future__ import annotations

import asyncio
import re

import pendulum
from bevy import Bevy, Inject
from bevy.providers.function_provider import bevy_method
from fastapi import FastAPI, Request
from httpx import AsyncClient

import soc.entities.submissions as submissions
from soc.database import Database
from soc.database.settings import Settings
from soc.events import Events


class Announcements(Bevy):
    @bevy_method
    def __init__(self, loop=None, events: Events = Inject):
        self._loop = loop or asyncio.get_event_loop()
        self._countdown = None

        self._loop.create_task(self.begin_countdown())
        events.on("submission.status.changed", self.on_submission_status_changed)

    @bevy_method
    async def begin_countdown(self, db: Database = Inject):
        challenges = await db.challenges.get_upcoming_challenges(2)
        match challenges:
            case [challenge, *_] if challenge.start > pendulum.now("UTC"):
                pass
            case [_, challenge]:
                pass
            case _:
                return

        wait = (challenge.start - pendulum.now("UTC")).total_seconds() + 5
        self._countdown = self._loop.call_later(
            wait,
            lambda: self._loop.create_task(self._announce_new_challenge()),
        )

    @bevy_method
    async def _announce_new_challenge(self, db: Database = Inject):
        self._loop.create_task(self.begin_countdown())

        challenge = await db.challenges.get_active()
        if not challenge:
            return

        await self._send_announcement(challenge)

    @bevy_method
    async def _send_announcement(self, challenge, settings: Settings = Inject, app: FastAPI = Inject):
        webhooks = await settings.get("announcement_webhooks")
        if webhooks:
            async with AsyncClient() as session:
                description = challenge.description.strip()
                if len(description) > 250:
                    description = f"{description[:247].rstrip(' !?.:,;)([]{}+-_')}..."

                url = f"https://soc.beginner.codes{app.url_path_for('show-challenge', challenge_id=challenge.id)}"
                end = challenge.end + pendulum.duration(days=1)
                resp = await session.post(
                    webhooks["new_challenge"],
                    json={
                        "embeds": [
                            {
                                "color": 0x4AFF8F,
                                "description": f"{description}\n\nEnds <t:{end.timestamp():.0f}:R>",
                                "title": challenge.title,
                                "url": url
                            }
                        ]
                    },
                )

                print(
                    f"Announce new challenge {resp.content=} {resp.status_code=}"
                )

    @bevy_method
    async def on_submission_status_changed(
        self,
        submission: submissions.Submission,
        request: Request,
        settings: Settings = Inject,
    ):
        webhooks = await settings.get("announcement_webhooks")
        if webhooks and submission.status.status == submissions.Status.APPROVED:
            async with AsyncClient() as session:
                user = await submission.created_by
                description = submission.description.strip()
                url = f"{request.url_for('index')}#submission-{submission.id}"
                short_url = self._create_short_link(submission.link)
                if len(description) > 250:
                    description = f"{description[:247].rstrip(' !?.:,;)([]{}+-_')}..."
                resp = await session.post(
                    webhooks["submission_approved"],
                    json={
                        "embeds": [
                            {
                                "author": {
                                    "icon_url": user.avatar,
                                    "name": user.username,
                                },
                                "color": 0xFFE44A,
                                "description": f"{description}\n\nCheck it out [{short_url}]({url})",
                            }
                        ]
                    },
                )

                print(
                    f"Announce submission approval {resp.content=} {resp.status_code=}"
                )

    def _create_short_link(self, link: str) -> str:
        short = re.match("(?:https?://)?(.+)", link).group(1)
        if len(short) > 32:
            short = f"{short[:32].strip(' /#?')}..."

        return short
