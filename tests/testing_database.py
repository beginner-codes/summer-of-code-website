from datetime import datetime
from types import SimpleNamespace

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base

from soc.config.models.config import DatabaseSettings
from soc.context import create_context
from soc.database import Database
from soc.database.models.base import BaseModel
from tests.fuzzy import FuzzyValue


@pytest.fixture()
def context():
    context = create_context()
    context.add(SimpleNamespace(uri="sqlite+aiosqlite://"), use_as=DatabaseSettings)
    return context


@pytest.fixture()
def table_base():
    return declarative_base()


@pytest.fixture()
def table_a(table_base):
    class A(table_base):
        __tablename__ = "a"

        id = Column(Integer, primary_key=True)
        text = Column(String)

    return A


@pytest.fixture
async def database(context):
    database = context.create(AsyncEngine)
    async with database.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    return database


@pytest.mark.asyncio
async def test_database(context):
    db = context.create(AsyncEngine)
    assert isinstance(db, AsyncEngine)


@pytest.mark.asyncio
async def test_session(context):
    context.create(AsyncEngine)
    session = context.get(AsyncSession)
    assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_connection(context, table_base, table_a):
    database = context.create(AsyncEngine)
    async with database.begin() as conn:
        await conn.run_sync(table_base.metadata.create_all)

    async with context.get(AsyncSession) as session:
        async with session.begin():
            session.add_all(
                [
                    table_a(text="Foo"),
                    table_a(text="bar"),
                ]
            )

        stmt = select(table_a).filter(table_a.text == "Foo")
        result = await session.execute(stmt)
        row = result.scalar()
        assert row.text == "Foo"


@pytest.mark.asyncio
async def test_database_facade(context, database):
    db = context.create(Database)
    user = await db.users.create("Bob", "PASSWORDHASH", "bob@bob.bob")
    assert user.id == FuzzyValue(int)
    assert user.username == "Bob"
    assert user.password == "PASSWORDHASH"
    assert user.email == "bob@bob.bob"
    assert user.joined == FuzzyValue(datetime)
    assert user.banned is False
