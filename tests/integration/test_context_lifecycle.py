"""Integration tests for ExecutionContext lifecycle (T041, T042)."""

import pytest
from sqlmodel import Field, SQLModel


class TestContextDatabaseSession:
    """Tests for context database session (T041)."""

    @pytest.mark.asyncio
    async def test_context_provides_database_session(self, temp_db_url: str) -> None:
        """Context provides a working database session."""
        from hive.runtime.config import AppSettings
        from hive.runtime.context import ExecutionContext

        settings = AppSettings(database_url=temp_db_url)

        async with ExecutionContext(settings=settings) as ctx:
            # Should have a database session
            assert ctx.db is not None

            # Create a table for testing

            engine = ctx.db.get_bind()
            assert engine is not None

    @pytest.mark.asyncio
    async def test_context_commits_on_success(self, temp_db_url: str) -> None:
        """Context commits transaction on successful exit."""
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlmodel import select

        from hive.runtime.config import AppSettings
        from hive.runtime.context import ExecutionContext

        settings = AppSettings(database_url=temp_db_url)

        # Define a test model
        class TestItem(SQLModel, table=True):
            __tablename__ = "test_item_commit"
            id: int | None = Field(default=None, primary_key=True)
            name: str

        # Create tables using a separate engine
        engine = create_async_engine(temp_db_url)
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        await engine.dispose()

        # Insert an item
        async with ExecutionContext(settings=settings) as ctx:
            item = TestItem(name="Test")
            ctx.db.add(item)
            # Commit happens automatically on exit

        # Verify it was committed
        async with ExecutionContext(settings=settings) as ctx:
            result = await ctx.db.execute(select(TestItem))
            items = result.scalars().all()
            assert len(items) == 1
            assert items[0].name == "Test"


class TestContextTransactionRollback:
    """Tests for context transaction rollback on error (T042)."""

    @pytest.mark.asyncio
    async def test_context_rolls_back_on_exception(self, temp_db_url: str) -> None:
        """Context rolls back transaction when exception occurs."""
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlmodel import select

        from hive.runtime.config import AppSettings
        from hive.runtime.context import ExecutionContext

        settings = AppSettings(database_url=temp_db_url)

        # Define a test model
        class TestItem(SQLModel, table=True):
            __tablename__ = "test_item_rollback"
            id: int | None = Field(default=None, primary_key=True)
            name: str

        # Create tables using a separate engine
        engine = create_async_engine(temp_db_url)
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        await engine.dispose()

        # Try to insert then raise an exception
        try:
            async with ExecutionContext(settings=settings) as ctx:
                item = TestItem(name="Should be rolled back")
                ctx.db.add(item)
                raise ValueError("Intentional error")
        except ValueError:
            pass  # Expected

        # Verify it was NOT committed
        async with ExecutionContext(settings=settings) as ctx:
            result = await ctx.db.execute(select(TestItem))
            items = result.scalars().all()
            assert len(items) == 0

    @pytest.mark.asyncio
    async def test_context_reraises_exception(self, temp_db_url: str) -> None:
        """Context re-raises the original exception after rollback."""
        from hive.runtime.config import AppSettings
        from hive.runtime.context import ExecutionContext

        settings = AppSettings(database_url=temp_db_url)

        with pytest.raises(RuntimeError) as exc_info:
            async with ExecutionContext(settings=settings):
                raise RuntimeError("Original error")

        assert str(exc_info.value) == "Original error"
