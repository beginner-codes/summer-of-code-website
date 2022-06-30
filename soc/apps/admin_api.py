import subprocess
from typing import Any

from fastapi import Depends

from soc.auth_helpers import bearer_token, validate_bearer_token, require_roles
from soc.context import create_app, inject
from soc.database import Database
from soc.discord import Discord

admin_api = create_app()


@admin_api.get(
    "/db/migrate",
    dependencies=[Depends(validate_bearer_token), Depends(require_roles("ADMIN"))],
)
async def migrate_database(
    session: dict[str, Any] = Depends(bearer_token),
    db: Database = inject(Database),
    discord: Discord = inject(Discord),
):
    output, success = _run_alembic()
    if success and "access_token" in session:
        await _setup_user(session, db, discord)

    return {"output": output, "success": success}


def _run_alembic() -> (str, bool):
    process = subprocess.Popen(
        ["alembic", "upgrade", "head"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    return (stderr or stdout), process.returncode == 0


async def _setup_user(session: dict[str, Any], db: Database, discord: Discord):
    user = await db.users.get_by_email(session["email"])
    if not user:
        user_data = await discord.get_user_data(session["access_token"])
        user = await db.users.create(user_data["username"], "", user_data["email"])

    roles = await user.get_roles()
    if "ADMIN" not in roles:
        await user.set_roles(["ADMIN", *roles])
