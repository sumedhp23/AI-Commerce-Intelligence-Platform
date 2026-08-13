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
from reviews import SyntheticReviewGenerator
from transactions import SyntheticTransactionGenerator


DATABASE_NAME = os.getenv(
    "POSTGRES_DB",
    "ai_commerce_intelligence",
)

DATABASE_USER = os.getenv(
    "POSTGRES_USER",
    "sumedh",
)

DATABASE_PASSWORD = os.getenv(
    "POSTGRES_PASSWORD",
)

DATABASE_HOST = os.getenv(
    "POSTGRES_HOST",
    "localhost",
)

DATABASE_PORT = int(
    os.getenv("POSTGRES_PORT", "5432")
)


@pytest.fixture
def connection():
    connection = psycopg2.connect(
        dbname=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        host=DATABASE_HOST,
        port=DATABASE_PORT,
    )

    yield connection

    connection.close()


@pytest.fixture
def generated_data():
    config = GeneratorConfig(
        seed=42,
        organizations=2,
        customers_per_organization=10,
        products_per_organization=10,
        skus_per_product=2,
        reviews_per_customer=1,
    )

    master_data = SyntheticCommerceGenerator(
        config
    ).generate()

    transaction_data = SyntheticTransactionGenerator(
        config=config,
        master_data=master_data,
    ).generate()

    review_data = SyntheticReviewGenerator(
        config=config,
        master_data=master_data,
        transaction_data=transaction_data,
    ).generate()

    return (
        master_data,
        transaction_data,
        review_data,
    )


def insert_master_data(
    cursor,
    master_data,
):
    for organization in master_data[
        "organizations"
    ]:
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

    for segment in master_data[
        "customer_segments"
    ]:
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

    for brand in master_data["brands"]:
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

    for category in master_data[
        "categories"
    ]:
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

    for customer in master_data[
        "customers"
    ]:
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

    for product in master_data[
        "products"
    ]:
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
            VALUES (
                %s, %s, %s, %s, %s, %s
            );
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

    for sku in master_data["skus"]:
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


def insert_orders(
    cursor,
    transaction_data,
):
    for order in transaction_data[
        "customer_orders"
    ]:
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


def insert_order_items(
    cursor,
    transaction_data,
):
    for item in transaction_data[
        "order_items"
    ]:
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
                %s, %s, %s, %s,
                %s, %s, %s
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


def insert_reviews(
    cursor,
    review_data,
):
    for review in review_data["reviews"]:
        cursor.execute(
            """
            INSERT INTO commerce.review (
                review_id,
                organization_id,
                customer_id,
                sku_id,
                order_id,
                rating,
                review_text,
                created_at
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            );
            """,
            (
                review["review_id"],
                review["organization_id"],
                review["customer_id"],
                review["sku_id"],
                review["order_id"],
                review["rating"],
                review["review_text"],
                review["created_at"],
            ),
        )


def test_generated_reviews_can_insert(
    connection,
    generated_data,
):
    (
        master_data,
        transaction_data,
        review_data,
    ) = generated_data

    try:
        with connection.cursor() as cursor:
            insert_master_data(
                cursor,
                master_data,
            )

            insert_orders(
                cursor,
                transaction_data,
            )

            insert_order_items(
                cursor,
                transaction_data,
            )

            insert_reviews(
                cursor,
                review_data,
            )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM commerce.review;
                """
            )

            actual_count = cursor.fetchone()[0]

            expected_count = len(
                review_data["reviews"]
            )

            assert actual_count == expected_count

    finally:
        connection.rollback()