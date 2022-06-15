from types import SimpleNamespace

from bevy import Context
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base
import pytest

from soc.database.config import DatabaseSettings
from soc.database.database import DatabaseProvider


@pytest.fixture()
def context():
    context = Context()
    context.add_provider(DatabaseProvider)
    context.add(
        SimpleNamespace(uri="sqlite+aiosqlite://"),
        use_as=DatabaseSettings
    )
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
