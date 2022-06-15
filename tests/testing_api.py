import httpx
import pytest
from bevy import Context
from sqlalchemy.ext.asyncio import AsyncEngine

from fuzzy import FuzzyValue
from soc.api import api_app
from soc.context import context as _context
from soc.database.config import DatabaseSettings
from soc.database.models.base import BaseModel


@pytest.fixture()
async def context():
    return _context()


@pytest.fixture(autouse=True)
async def _connect_db(context: Context):
    context.add(
        DatabaseSettings(driver="sqlite+aiosqlite"),
        use_as=DatabaseSettings,
    )


@pytest.fixture(autouse=True)
async def _setup_tables(context: Context):
    engine = context.create(AsyncEngine)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


@pytest.fixture()
async def client(context):
    api_app.dependency_overrides[_context] = lambda: context
    async with httpx.AsyncClient(app=api_app, base_url="http://localhost") as client:
        yield client


@pytest.mark.asyncio
async def test_authentication_invalid_user(client):
    response = await client.post(
        "/authenticate", data={"username": "Bob", "password": "PASSWORD"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid user"}


@pytest.mark.asyncio
async def test_registration_authentication(client):
    response = await client.post(
        "/register",
        data={"username": "Bob", "password": "PASSWORD", "email": "bob@gmail.com"},
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "User successfully registered"}

    response = await client.post(
        "/authenticate", data={"username": "Bob", "password": "PASSWORD"}
    )
    assert response.status_code == 200
    assert response.json() == {"access-token": FuzzyValue(str)}
