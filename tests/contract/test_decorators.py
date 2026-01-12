"""Contract tests for decorators.

These tests verify the public API contract for @command, @query, @entity,
and @screen decorators per the contracts/public-api.md specification.
"""



class TestCommandDecorator:
    """Tests for @command decorator registration (T010)."""

    def test_command_registers_function_with_name(self) -> None:
        """@command registers function with correct name derived from function name."""
        from hive import App, command

        app = App(name="test-app")

        @command(app)
        async def add_task(ctx, title: str) -> dict:
            """Add a new task."""
            return {"title": title}

        # Verify command is registered
        reg = app.registry.get_command("add_task")
        assert reg is not None
        assert reg.name == "add_task"

    def test_command_registers_function_with_custom_name(self) -> None:
        """@command allows overriding command name."""
        from hive import App, command

        app = App(name="test-app")

        @command(app, name="create")
        async def add_task(ctx, title: str) -> dict:
            """Add a new task."""
            return {"title": title}

        reg = app.registry.get_command("create")
        assert reg is not None
        assert reg.name == "create"
        # Original name should not be registered
        assert app.registry.get_command("add_task") is None

    def test_command_captures_docstring(self) -> None:
        """@command extracts docstring for help text."""
        from hive import App, command

        app = App(name="test-app")

        @command(app)
        async def documented(ctx) -> None:
            """This is the help text."""
            pass

        reg = app.registry.get_command("documented")
        assert reg is not None
        assert reg.docstring == "This is the help text."

    def test_command_captures_parameters(self) -> None:
        """@command extracts parameter info from function signature."""
        from hive import App, command

        app = App(name="test-app")

        @command(app)
        async def with_params(
            ctx,
            name: str,
            count: int = 1,
            verbose: bool = False,
        ) -> dict:
            """Command with parameters."""
            return {}

        reg = app.registry.get_command("with_params")
        assert reg is not None
        # Should have 3 parameters (excluding ctx)
        assert len(reg.parameters) == 3

        # Check parameter details
        param_names = [p.name for p in reg.parameters]
        assert "name" in param_names
        assert "count" in param_names
        assert "verbose" in param_names

    def test_command_captures_return_type(self) -> None:
        """@command extracts return type annotation."""
        from pydantic import BaseModel

        from hive import App, command

        app = App(name="test-app")

        class TaskResult(BaseModel):
            id: int
            title: str

        @command(app)
        async def create_task(ctx, title: str) -> TaskResult:
            """Create a task."""
            return TaskResult(id=1, title=title)

        reg = app.registry.get_command("create_task")
        assert reg is not None
        assert reg.return_type == TaskResult

    def test_command_preserves_original_function(self) -> None:
        """@command returns the original function unchanged."""
        from hive import App, command

        app = App(name="test-app")

        @command(app)
        async def my_command(ctx) -> str:
            """A command."""
            return "result"

        # The decorated function should be the same as the original
        assert callable(my_command)
        assert my_command.__name__ == "my_command"

    def test_command_with_entities(self) -> None:
        """@command captures entity references."""
        from sqlmodel import Field, SQLModel

        from hive import App, command

        app = App(name="test-app")

        class Task(SQLModel, table=True):
            __tablename__ = "cmd_task"
            id: int | None = Field(default=None, primary_key=True)
            title: str

        @command(app, entities=[Task])
        async def create_task(ctx, title: str) -> dict:
            """Create a task."""
            return {}

        reg = app.registry.get_command("create_task")
        assert reg is not None
        assert Task in reg.entities

    def test_command_with_aliases(self) -> None:
        """@command captures command aliases."""
        from hive import App, command

        app = App(name="test-app")

        @command(app, aliases=["add", "new"])
        async def create(ctx, title: str) -> dict:
            """Create something."""
            return {}

        reg = app.registry.get_command("create")
        assert reg is not None
        assert "add" in reg.aliases
        assert "new" in reg.aliases


class TestQueryDecorator:
    """Tests for @query decorator registration (T011)."""

    def test_query_registers_function_with_name(self) -> None:
        """@query registers function with correct name."""
        from hive import App, query

        app = App(name="test-app")

        @query(app)
        async def list_tasks(ctx) -> list:
            """List all tasks."""
            return []

        reg = app.registry.get_query("list_tasks")
        assert reg is not None
        assert reg.name == "list_tasks"

    def test_query_captures_cache_ttl(self) -> None:
        """@query captures cache_ttl setting."""
        from hive import App, query

        app = App(name="test-app")

        @query(app, cache_ttl=300)
        async def cached_query(ctx) -> list:
            """A cached query."""
            return []

        reg = app.registry.get_query("cached_query")
        assert reg is not None
        assert reg.cache_ttl == 300

    def test_query_default_no_cache(self) -> None:
        """@query defaults to no caching."""
        from hive import App, query

        app = App(name="test-app")

        @query(app)
        async def uncached_query(ctx) -> list:
            """An uncached query."""
            return []

        reg = app.registry.get_query("uncached_query")
        assert reg is not None
        assert reg.cache_ttl is None

    def test_query_captures_parameters(self) -> None:
        """@query extracts parameter info from function signature."""
        from hive import App, query

        app = App(name="test-app")

        @query(app)
        async def search(ctx, term: str, limit: int = 10) -> list:
            """Search with parameters."""
            return []

        reg = app.registry.get_query("search")
        assert reg is not None
        assert len(reg.parameters) == 2

    def test_query_with_entities(self) -> None:
        """@query captures entity references."""
        from sqlmodel import Field, SQLModel

        from hive import App, query

        app = App(name="test-app")

        class Task(SQLModel, table=True):
            __tablename__ = "query_task"
            id: int | None = Field(default=None, primary_key=True)
            title: str

        @query(app, entities=[Task])
        async def get_tasks(ctx) -> list:
            """Get tasks."""
            return []

        reg = app.registry.get_query("get_tasks")
        assert reg is not None
        assert Task in reg.entities


class TestEntityDecorator:
    """Tests for @entity decorator registration (T028-T030)."""

    def test_entity_registers_class_with_name(self) -> None:
        """@entity registers class with correct name derived from class name."""
        from sqlmodel import Field, SQLModel

        from hive import App, entity

        app = App(name="test-app")

        @entity(app)
        class Project(SQLModel, table=True):
            __tablename__ = "entity_project"
            id: int | None = Field(default=None, primary_key=True)
            name: str

        reg = app.registry.get_entity("Project")
        assert reg is not None
        assert reg.name == "Project"
        assert reg.cls == Project

    def test_entity_captures_fields(self) -> None:
        """@entity extracts field information from SQLModel."""
        from sqlmodel import Field, SQLModel

        from hive import App, entity

        app = App(name="test-app")

        @entity(app)
        class Item(SQLModel, table=True):
            __tablename__ = "entity_item"
            id: int | None = Field(default=None, primary_key=True)
            name: str
            description: str | None = None
            count: int = 0

        reg = app.registry.get_entity("Item")
        assert reg is not None

        # Check fields were extracted
        field_names = [f.name for f in reg.fields]
        assert "id" in field_names
        assert "name" in field_names
        assert "description" in field_names
        assert "count" in field_names

    def test_entity_captures_table_name(self) -> None:
        """@entity extracts custom table name if specified."""
        from sqlmodel import Field, SQLModel

        from hive import App, entity

        app = App(name="test-app")

        @entity(app)
        class MyModel(SQLModel, table=True):
            __tablename__ = "custom_table_name"
            id: int | None = Field(default=None, primary_key=True)

        reg = app.registry.get_entity("MyModel")
        assert reg is not None
        assert reg.table_name == "custom_table_name"

    def test_entity_preserves_original_class(self) -> None:
        """@entity returns the original class unchanged."""
        from sqlmodel import Field, SQLModel

        from hive import App, entity

        app = App(name="test-app")

        @entity(app)
        class Widget(SQLModel, table=True):
            __tablename__ = "entity_widget"
            id: int | None = Field(default=None, primary_key=True)
            name: str

        # The decorated class should be the same as the original
        assert Widget.__name__ == "Widget"
        # Should still be a SQLModel
        assert issubclass(Widget, SQLModel)

    def test_entity_list_returns_all_entities(self) -> None:
        """list_entities returns all registered entities."""
        from sqlmodel import Field, SQLModel

        from hive import App, entity

        app = App(name="test-app")

        @entity(app)
        class EntityA(SQLModel, table=True):
            __tablename__ = "entity_a"
            id: int | None = Field(default=None, primary_key=True)

        @entity(app)
        class EntityB(SQLModel, table=True):
            __tablename__ = "entity_b"
            id: int | None = Field(default=None, primary_key=True)

        entities = app.registry.list_entities()
        assert len(entities) == 2
        names = [e.name for e in entities]
        assert "EntityA" in names
        assert "EntityB" in names


class TestScreenDecorator:
    """Tests for @screen decorator registration (T071)."""

    def test_screen_registers_class_with_name(self) -> None:
        """@screen registers class with correct name derived from class name."""
        from hive import App, screen

        app = App(name="test-app")

        @screen(app)
        class DashboardScreen:
            """The main dashboard."""
            pass

        reg = app.registry.get_screen("DashboardScreen")
        assert reg is not None
        assert reg.name == "DashboardScreen"
        assert reg.cls == DashboardScreen

    def test_screen_registers_with_custom_name(self) -> None:
        """@screen allows overriding screen name."""
        from hive import App, screen

        app = App(name="test-app")

        @screen(app, name="dashboard")
        class MainDashboard:
            """Dashboard screen."""
            pass

        reg = app.registry.get_screen("dashboard")
        assert reg is not None
        assert reg.name == "dashboard"
        # Original name should not be registered
        assert app.registry.get_screen("MainDashboard") is None

    def test_screen_captures_default_flag(self) -> None:
        """@screen captures default=True setting."""
        from hive import App, screen

        app = App(name="test-app")

        @screen(app, default=True)
        class HomeScreen:
            """Home screen."""
            pass

        reg = app.registry.get_screen("HomeScreen")
        assert reg is not None
        assert reg.default is True

    def test_screen_default_is_false_by_default(self) -> None:
        """@screen default flag is False by default."""
        from hive import App, screen

        app = App(name="test-app")

        @screen(app)
        class RegularScreen:
            """A regular screen."""
            pass

        reg = app.registry.get_screen("RegularScreen")
        assert reg is not None
        assert reg.default is False

    def test_screen_captures_keybinding(self) -> None:
        """@screen captures keybinding setting."""
        from hive import App, screen

        app = App(name="test-app")

        @screen(app, keybinding="d")
        class DashScreen:
            """Dashboard with keybinding."""
            pass

        reg = app.registry.get_screen("DashScreen")
        assert reg is not None
        assert reg.keybinding == "d"

    def test_screen_captures_docstring(self) -> None:
        """@screen extracts docstring for help text."""
        from hive import App, screen

        app = App(name="test-app")

        @screen(app)
        class DocScreen:
            """This is the screen description."""
            pass

        reg = app.registry.get_screen("DocScreen")
        assert reg is not None
        assert reg.docstring == "This is the screen description."

    def test_screen_preserves_original_class(self) -> None:
        """@screen returns the original class unchanged."""
        from hive import App, screen

        app = App(name="test-app")

        @screen(app, default=True, keybinding="h")
        class HomeView:
            """Home view."""
            pass

        # The decorated class should be the same as the original
        assert HomeView.__name__ == "HomeView"

    def test_screen_list_returns_all_screens(self) -> None:
        """list_screens returns all registered screens."""
        from hive import App, screen

        app = App(name="test-app")

        @screen(app, default=True)
        class ScreenA:
            """Screen A."""
            pass

        @screen(app, keybinding="b")
        class ScreenB:
            """Screen B."""
            pass

        @screen(app)
        class ScreenC:
            """Screen C."""
            pass

        screens = app.registry.list_screens()
        assert len(screens) == 3
        names = [s.name for s in screens]
        assert "ScreenA" in names
        assert "ScreenB" in names
        assert "ScreenC" in names
