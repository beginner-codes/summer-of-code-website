import httpx
import jwt
import pytest
from bevy import Context
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from soc.context import create_context
from soc.controllers.authentication import AuthenticationSettings, JWTSettings
from soc.database.config import DatabaseSettings
from soc.database.models.base import BaseModel
from soc.database.models.roles import RoleModel
from soc.site import site, admin_app
from soc.templates.settings import TemplateSettings


@pytest.fixture()
async def context():
    return create_context()


@pytest.fixture(autouse=True)
async def _setup_context(context: Context):
    context.add(
        DatabaseSettings(driver="sqlite+aiosqlite"),
        use_as=DatabaseSettings,
    )
    context.add(
        AuthenticationSettings(jwt=JWTSettings(private_key="TOP SECRET TEST KEY")),
        use_as=AuthenticationSettings,
    )
    context.add(
        TemplateSettings(directory="test_templates"),
        use_as=TemplateSettings,
    )


@pytest.fixture(autouse=True)
async def _setup_tables(context: Context):
    engine = context.create(AsyncEngine)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


@pytest.fixture()
async def client(context):
    site.dependency_overrides[create_context] = lambda: context
    admin_app.dependency_overrides[create_context] = lambda: context
    async with httpx.AsyncClient(app=site, base_url="http://localhost") as client:
        yield client


@pytest.mark.asyncio
async def test_db_page_no_cookie(client, context):
    response = await client.get("/admin/db")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_db_page_invalid_cookie(client, context):
    token = jwt.encode({}, "PRIVATEKEY", "HS256")
    response = await client.get("/admin/db", cookies={"sessionid": token})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_db_page_not_an_admin(client, context):
    token = jwt.encode({"user_id": 1}, "PRIVATEKEY", "HS256")
    response = await client.get("/admin/db", cookies={"sessionid": token})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_db_page_admin(client, context):
    async with context.get(AsyncSession) as session:
        user_model = RoleModel(type="admin", user_id=1)
        session.add(user_model)
        await session.commit()

        settings = context.get(AuthenticationSettings)
        token = jwt.encode(
            {"user_id": 1}, settings.jwt.private_key, settings.jwt.algorithm
        )
        response = await client.get("/admin/db", cookies={"sessionid": token})
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_db_page_admin_email_login(client, context):
    settings = context.get(AuthenticationSettings)
    token = jwt.encode(
        {"email": settings.admin_email},
        settings.jwt.private_key,
        settings.jwt.algorithm,
    )
    response = await client.get("/admin/db", cookies={"sessionid": token})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_db_page_admin_invalid_email_login(client, context):
    settings = context.get(AuthenticationSettings)
    token = jwt.encode(
        {"email": "notzech@zech.com"},
        settings.jwt.private_key,
        settings.jwt.algorithm,
    )
    response = await client.get("/admin/db", cookies={"sessionid": token})
    assert response.status_code == 403
