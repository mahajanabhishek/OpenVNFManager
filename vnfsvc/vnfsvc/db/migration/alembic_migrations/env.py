# Copyright 2012 New Dream Network, LLC (DreamHost)
# Copyright 2014 Tata Consultancy Services Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# @author: Mark McClain, DreamHost

from logging import config as logging_config

from alembic import context
from oslo_config import cfg
from oslo_db.sqlalchemy import session
import sqlalchemy as sa
from sqlalchemy import event

from vnfsvc.db.migration.models import head  # noqa
from vnfsvc.db import model_base


MYSQL_ENGINE = None

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
vnfsvc_config = config.vnfsvc_config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
logging_config.fileConfig(config.config_file_name)

plugin_class_path = vnfsvc_config.core_plugin
active_plugins = [plugin_class_path]
#active_plugins += vnfsvc_config.service_plugins

# set the target for 'autogenerate' support
target_metadata = model_base.BASEV2.metadata


def set_mysql_engine():
    try:
        mysql_engine = vnfsvc_config.command.mysql_engine
    except cfg.NoSuchOptError:
        mysql_engine = None

    global MYSQL_ENGINE
    MYSQL_ENGINE = (mysql_engine or
                    model_base.BASEV2.__table_args__['mysql_engine'])


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with either a URL
    or an Engine.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    set_mysql_engine()

    kwargs = dict()
    if vnfsvc_config.database.connection:
        kwargs['url'] = vnfsvc_config.database.connection
    else:
        kwargs['dialect_name'] = vnfsvc_config.database.engine
    context.configure(**kwargs)

    with context.begin_transaction():
        context.run_migrations(active_plugins=active_plugins,
                               options=build_options())


@event.listens_for(sa.Table, 'after_parent_attach')
def set_storage_engine(target, parent):
    if MYSQL_ENGINE:
        target.kwargs['mysql_engine'] = MYSQL_ENGINE


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    set_mysql_engine()
    engine = session.create_engine(vnfsvc_config.database.connection)

    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )

    try:
        with context.begin_transaction():
            context.run_migrations(active_plugins=active_plugins,
                                   options=build_options())
    finally:
        connection.close()


def build_options():
    return


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
