import os

from eventsourcing.postgres import PostgresDatastore
from eventsourcing.tests.test_application_with_popo import (
    TIMEIT_FACTOR,
    TestApplicationWithPOPO,
)
from eventsourcing.tests.test_postgres import drop_postgres_table

from eventsourcing_sqlalchemy.datastore import SqlAlchemyDatastore


class TestApplicationWithSqlAlchemy(TestApplicationWithPOPO):
    timeit_number = 5 * TIMEIT_FACTOR
    expected_factory_topic = "eventsourcing_sqlalchemy.factory:Factory"
    sqlalchemy_database_url = "sqlite:///:memory:"

    def setUp(self) -> None:
        super().setUp()
        os.environ["INFRASTRUCTURE_FACTORY"] = "eventsourcing_sqlalchemy.factory:Factory"
        os.environ["SQLALCHEMY_URL"] = self.sqlalchemy_database_url

    def tearDown(self) -> None:
        del os.environ["INFRASTRUCTURE_FACTORY"]
        del os.environ["SQLALCHEMY_URL"]
        super().tearDown()


class TestWithPostgres(TestApplicationWithSqlAlchemy):
    timeit_number = 500 * TIMEIT_FACTOR
    sqlalchemy_database_url = (
        "postgresql://eventsourcing:eventsourcing@localhost:5432/eventsourcing_sqlalchemy"
    )

    def setUp(self) -> None:
        super().setUp()
        self.drop_tables()

    def tearDown(self) -> None:
        self.drop_tables()
        super().tearDown()

    def drop_tables(self):
        datasource = PostgresDatastore(
            dbname="eventsourcing_sqlalchemy",
            host="127.0.0.1",
            port="5432",
            user="eventsourcing",
            password="eventsourcing",
        )
        drop_postgres_table(datasource, "bankaccounts_events")
        drop_postgres_table(datasource, "bankaccounts_events")


del TestApplicationWithPOPO
