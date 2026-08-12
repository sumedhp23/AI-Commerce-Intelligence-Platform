import os

import psycopg2
import pytest


DATABASE_NAME = os.getenv("POSTGRES_DB", "ai_commerce_intelligence")
DATABASE_USER = os.getenv("POSTGRES_USER", "sumedh")
DATABASE_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DATABASE_HOST = os.getenv("POSTGRES_HOST", "localhost")
DATABASE_PORT = int(os.getenv("POSTGRES_PORT", "5432"))


EXPECTED_TABLES = {
    "brand",
    "campaign",
    "category",
    "click_event",
    "coupon",
    "customer",
    "customer_order",
    "customer_return",
    "customer_segment",
    "customer_session",
    "delivery",
    "driver",
    "fulfillment_location",
    "impression",
    "inventory_movement",
    "inventory_snapshot",
    "operational_event",
    "order_item",
    "organization",
    "payment",
    "product",
    "promotion",
    "purchase_order",
    "purchase_order_item",
    "refund",
    "review",
    "search_event",
    "shipment",
    "sku",
    "supplier",
}


@pytest.fixture(scope="session")
def connection():
    conn = psycopg2.connect(
        dbname=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        host=DATABASE_HOST,
        port=DATABASE_PORT,
    )
    yield conn
    conn.close()


def test_commerce_schema_exists(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.schemata
                WHERE schema_name = 'commerce'
            );
            """
        )
        assert cursor.fetchone()[0] is True


def test_expected_tables_exist(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'commerce'
            """
        )
        actual_tables = {row[0] for row in cursor.fetchall()}

    assert EXPECTED_TABLES.issubset(actual_tables)


def test_table_count(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'commerce'
            """
        )
        table_count = cursor.fetchone()[0]

    assert table_count == 30


def test_foreign_key_count(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.table_constraints
            WHERE constraint_schema = 'commerce'
              AND constraint_type = 'FOREIGN KEY'
            """
        )
        foreign_key_count = cursor.fetchone()[0]

    assert foreign_key_count == 68


def test_primary_keys_exist(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.table_constraints
            WHERE constraint_schema = 'commerce'
              AND constraint_type = 'PRIMARY KEY'
            """
        )
        primary_key_count = cursor.fetchone()[0]

    assert primary_key_count == 30


def test_all_expected_tables_have_primary_keys(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.table_constraints
            WHERE constraint_schema = 'commerce'
              AND constraint_type = 'PRIMARY KEY'
            """
        )
        tables_with_primary_keys = {row[0] for row in cursor.fetchall()}

    assert EXPECTED_TABLES == tables_with_primary_keys