# -*- coding: utf-8 -*-
import os
from unittest import TestCase

from eventsourcing.application import Application
from eventsourcing.postgres import PostgresDatastore
from eventsourcing.tests.application import TIMEIT_FACTOR, ExampleApplicationTestCase
from eventsourcing.tests.postgres_utils import drop_postgres_table
from eventsourcing.utils import get_topic


class TestApplicationWithSQLAlchemy(ExampleApplicationTestCase):
    timeit_number = 30 * TIMEIT_FACTOR
    expected_factory_topic = "eventsourcing_sqlalchemy.factory:Factory"
    sqlalchemy_database_url = "sqlite:///:memory:"

    def setUp(self) -> None:
        super().setUp()
        os.environ["PERSISTENCE_MODULE"] = "eventsourcing_sqlalchemy"
        os.environ["SQLALCHEMY_URL"] = self.sqlalchemy_database_url

    def tearDown(self) -> None:
        del os.environ["PERSISTENCE_MODULE"]
        del os.environ["SQLALCHEMY_URL"]
        super().tearDown()


class TestWithPostgres(TestApplicationWithSQLAlchemy):
    timeit_number = 5 * TIMEIT_FACTOR
    sqlalchemy_database_url = (
        "postgresql://eventsourcing:eventsourcing@localhost:5432"
        "/eventsourcing_sqlalchemy"
    )

    def setUp(self) -> None:
        super().setUp()
        self.drop_tables()

    def tearDown(self) -> None:
        self.drop_tables()
        super().tearDown()

    def drop_tables(self) -> None:
        datastore = PostgresDatastore(
            dbname="eventsourcing_sqlalchemy",
            host="127.0.0.1",
            port="5432",
            user="eventsourcing",
            password="eventsourcing",
        )
        drop_postgres_table(datastore, "bankaccounts_events")
        drop_postgres_table(datastore, "bankaccounts_events")


class TestWithConnectionCreatorTopic(TestCase):
    def test(self) -> None:
        class MyCreatorException(Exception):
            pass

        def creator() -> None:
            raise MyCreatorException()

        creator_topic = get_topic(creator)  # type: ignore[arg-type]

        env = {
            "PERSISTENCE_MODULE": "eventsourcing_sqlalchemy",
            "SQLALCHEMY_URL": (
                "postgresql://eventsourcing:eventsourcing@localhost:5432"
                "/eventsourcing_sqlalchemy"
            ),
            "SQLALCHEMY_CONNECTION_CREATOR_TOPIC": creator_topic,
        }
        with self.assertRaises(MyCreatorException):
            Application(env=env)


del ExampleApplicationTestCase
