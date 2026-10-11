from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine

from app.core.config import get_settings
from app.db.models import Base
from app.db.session import make_database_url


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = make_database_url(get_settings().database_path)
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    database_path = config.attributes.get("database_path")
    if database_path is None:
        database_path = get_settings().database_path
    database_url = make_database_url(Path(database_path))
    connectable = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
