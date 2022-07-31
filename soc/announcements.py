from __future__ import annotations

import re

from bevy import Bevy, Inject
from bevy.providers.function_provider import bevy_method
from fastapi import Request
from httpx import AsyncClient

import soc.entities.submissions as submissions
from soc.database.settings import Settings
from soc.events import Events


class Announcements(Bevy):
    @bevy_method
    def __init__(self, events: Events = Inject):
        events.on("submission.status.changed", self.on_submission_status_changed)

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
