import os
import sys
from pathlib import Path


import psycopg2
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = PROJECT_ROOT / "data-platform" / "synthetic"

if str(SYNTHETIC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTHETIC_DIR))

from config import GeneratorConfig
from generator import SyntheticCommerceGenerator
from transactions import SyntheticTransactionGenerator


DATABASE_NAME = os.getenv(
    "POSTGRES_DB",
    "ai_commerce_intelligence",
)
DATABASE_USER = os.getenv(
    "POSTGRES_USER",
    "sumedh",
)
DATABASE_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DATABASE_HOST = os.getenv(
    "POSTGRES_HOST",
    "localhost",
)
DATABASE_PORT = int(
    os.getenv("POSTGRES_PORT", "5432")
)


@pytest.fixture
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


@pytest.fixture
def generated_data():
    config = GeneratorConfig(
        seed=42,
        organizations=1,
        brands_per_organization=2,
        categories_per_organization=2,
        products_per_organization=3,
        skus_per_product=2,
        customers_per_organization=5,
        suppliers_per_organization=2,
        customer_segments_per_organization=2,
    )

    return SyntheticCommerceGenerator(config).generate()

@pytest.fixture
def transaction_data(generated_data):
    config = GeneratorConfig(
        seed=42,
        organizations=1,
        brands_per_organization=2,
        categories_per_organization=2,
        products_per_organization=3,
        skus_per_product=2,
        customers_per_organization=5,
        suppliers_per_organization=2,
        customer_segments_per_organization=2,
    )

    generator = SyntheticTransactionGenerator(
        config=config,
        master_data=generated_data,
    )

    return generator.generate(
        orders_per_customer=1,
        items_per_order=2,
    )

def insert_master_data(cursor, data):
    for organization in data["organizations"]:
        cursor.execute(
            """
            INSERT INTO commerce.organization (
                organization_id,
                name,
                industry,
                country_code
            )
            VALUES (%s, %s, %s, %s);
            """,
            (
                organization["organization_id"],
                organization["name"],
                organization["industry"],
                organization["country_code"],
            ),
        )

    for segment in data["customer_segments"]:
        cursor.execute(
            """
            INSERT INTO commerce.customer_segment (
                customer_segment_id,
                organization_id,
                name,
                description
            )
            VALUES (%s, %s, %s, %s);
            """,
            (
                segment["customer_segment_id"],
                segment["organization_id"],
                segment["name"],
                segment["description"],
            ),
        )

    for brand in data["brands"]:
        cursor.execute(
            """
            INSERT INTO commerce.brand (
                brand_id,
                organization_id,
                name
            )
            VALUES (%s, %s, %s);
            """,
            (
                brand["brand_id"],
                brand["organization_id"],
                brand["name"],
            ),
        )

    for category in data["categories"]:
        cursor.execute(
            """
            INSERT INTO commerce.category (
                category_id,
                organization_id,
                parent_category_id,
                name
            )
            VALUES (%s, %s, %s, %s);
            """,
            (
                category["category_id"],
                category["organization_id"],
                category["parent_category_id"],
                category["name"],
            ),
        )

    for supplier in data["suppliers"]:
        cursor.execute(
            """
            INSERT INTO commerce.supplier (
                supplier_id,
                organization_id,
                name,
                city,
                country_code
            )
            VALUES (%s, %s, %s, %s, %s);
            """,
            (
                supplier["supplier_id"],
                supplier["organization_id"],
                supplier["name"],
                supplier["city"],
                supplier["country_code"],
            ),
        )

    for customer in data["customers"]:
        cursor.execute(
            """
            INSERT INTO commerce.customer (
                customer_id,
                organization_id,
                customer_segment_id,
                external_customer_id,
                first_name,
                last_name,
                email,
                country_code,
                city,
                acquisition_channel
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            );
            """,
            (
                customer["customer_id"],
                customer["organization_id"],
                customer["customer_segment_id"],
                customer["external_customer_id"],
                customer["first_name"],
                customer["last_name"],
                customer["email"],
                customer["country_code"],
                customer["city"],
                customer["acquisition_channel"],
            ),
        )

    for product in data["products"]:
        cursor.execute(
            """
            INSERT INTO commerce.product (
                product_id,
                organization_id,
                brand_id,
                category_id,
                product_name,
                description
            )
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (
                product["product_id"],
                product["organization_id"],
                product["brand_id"],
                product["category_id"],
                product["product_name"],
                product["description"],
            ),
        )

    for sku in data["skus"]:
        cursor.execute(
            """
            INSERT INTO commerce.sku (
                sku_id,
                organization_id,
                product_id,
                sku_code,
                sku_name,
                unit_cost,
                list_price,
                weight_grams,
                active
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            );
            """,
            (
                sku["sku_id"],
                sku["organization_id"],
                sku["product_id"],
                sku["sku_code"],
                sku["sku_name"],
                sku["unit_cost"],
                sku["list_price"],
                sku["weight_grams"],
                sku["active"],
            ),
        )

def test_generated_master_data_can_insert(
    connection,
    generated_data,
):
    data = generated_data

    try:
        with connection.cursor() as cursor:
            insert_master_data(cursor, data)

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM commerce.organization;
                """
            )

            organization_count = cursor.fetchone()[0]

            assert organization_count == len(
                data["organizations"]
            )
    finally:
        connection.rollback()

def test_generated_transaction_data_can_insert(
    connection,
    generated_data,
    transaction_data,
):
    data = generated_data
    transactions = transaction_data

    try:
        with connection.cursor() as cursor:

            insert_master_data(cursor, data)

            # Insert transactional data in dependency order.

            for order in transactions["customer_orders"]:
                cursor.execute(
                    """
                    INSERT INTO commerce.customer_order (
                        order_id,
                        organization_id,
                        customer_id,
                        fulfillment_location_id,
                        order_number,
                        order_status,
                        currency,
                        subtotal_amount,
                        discount_amount,
                        delivery_fee,
                        tax_amount,
                        total_amount,
                        ordered_at,
                        cancelled_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s
                    );
                    """,
                    (
                        order["order_id"],
                        order["organization_id"],
                        order["customer_id"],
                        order["fulfillment_location_id"],
                        order["order_number"],
                        order["order_status"],
                        order["currency"],
                        order["subtotal_amount"],
                        order["discount_amount"],
                        order["delivery_fee"],
                        order["tax_amount"],
                        order["total_amount"],
                        order["ordered_at"],
                        order["cancelled_at"],
                    ),
                )

            for item in transactions["order_items"]:
                cursor.execute(
                    """
                    INSERT INTO commerce.order_item (
                        order_item_id,
                        organization_id,
                        order_id,
                        sku_id,
                        quantity,
                        unit_price,
                        discount_amount
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    );
                    """,
                    (
                        item["order_item_id"],
                        item["organization_id"],
                        item["order_id"],
                        item["sku_id"],
                        item["quantity"],
                        item["unit_price"],
                        item["discount_amount"],
                    ),
                )

            for payment in transactions["payments"]:
                cursor.execute(
                    """
                    INSERT INTO commerce.payment (
                        payment_id,
                        organization_id,
                        order_id,
                        payment_method,
                        payment_status,
                        amount,
                        transaction_reference,
                        paid_at
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s, %s
                    );
                    """,
                    (
                        payment["payment_id"],
                        payment["organization_id"],
                        payment["order_id"],
                        payment["payment_method"],
                        payment["payment_status"],
                        payment["amount"],
                        payment["transaction_reference"],
                        payment["paid_at"],
                    ),
                )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM commerce.customer_order;
                """
            )

            assert cursor.fetchone()[0] == len(
                transactions["customer_orders"]
            )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM commerce.order_item;
                """
            )

            assert cursor.fetchone()[0] == len(
                transactions["order_items"]
            )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM commerce.payment;
                """
            )

            assert cursor.fetchone()[0] == len(
                transactions["payments"]
            )

    finally:
        connection.rollback()