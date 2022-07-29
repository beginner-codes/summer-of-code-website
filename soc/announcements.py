from __future__ import annotations

from bevy import Bevy, Inject
from bevy.providers.function_provider import bevy_method

import soc.entities.submissions as submissions
from soc.events import Events


class Announcements(Bevy):
    @bevy_method
    def __init__(self, events: Events = Inject):
        events.on("submission.status.changed", self.on_submission_status_changed)

    async def on_submission_status_changed(self, submission: submissions.Submission):
        if submission.status.status == submissions.Status.APPROVED:
            print("Submission Approved", submission.description)
