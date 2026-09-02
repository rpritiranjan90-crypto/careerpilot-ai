"""Alembic environment configuration.

This config is used by the alembic migration system to connect to the database
and load the SQLAlchemy models so migrations can auto-generate.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

from app.core.config import settings
from app.core.database import Base

# Import all models so Base.metadata sees them
from app.models import *  # noqa: F401, F403

# Alembic Config object
config = context.config

# Set database URL from our app settings.
# Escape % so ConfigParser interpolation doesn't misread %40 as a variable.
if settings.database_url:
    url = settings.database_url.replace("%", "%%")
    config.set_main_option("sqlalchemy.url", url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata for autogenerate support
target_metadata = Base.metadata

# Schema for all CareerPilot tables. Created/managed by the migration runner.
DB_SCHEMA = settings.db_schema.strip() if settings.db_schema else "careerpilot"
if not DB_SCHEMA or DB_SCHEMA == "public":
    DB_SCHEMA = None  # use default schema


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema=DB_SCHEMA,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:  # type: Connection
        # Make sure the target schema exists before any migration runs.
        if DB_SCHEMA:
            connection.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"')
            connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=DB_SCHEMA,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
