#!/usr/bin/env python
# -*- coding: utf-8 -*-

# common fixtures for testing

import pytest

from base.db import engine, meta

@pytest.fixture()
def app():
    import wsgi_handler

    wsgi_handler.app.config["TESTING"] = True
    return wsgi_handler.app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db():
    conn = engine.connect()
    for table in meta.tables.values():
        conn.execute(table.delete())
    return conn

