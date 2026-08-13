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
from customer_behavior import (
    SyntheticCustomerBehaviorGenerator,
)
from generator import SyntheticCommerceGenerator
from marketing import SyntheticMarketingGenerator


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
        campaigns_per_organization=3,
        promotions_per_organization=2,
        coupons_per_promotion=2,
        sessions_per_customer=2,
        search_events_per_session=2,
        click_events_per_session=2,
        impressions_per_session=3,
    )

    master_data = SyntheticCommerceGenerator(
        config
    ).generate()

    marketing_data = SyntheticMarketingGenerator(
        config=config,
        master_data=master_data,
    ).generate()

    behavior_data = SyntheticCustomerBehaviorGenerator(
        config=config,
        master_data=master_data,
        marketing_data=marketing_data,
    ).generate()

    return (
        master_data,
        marketing_data,
        behavior_data,
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


def insert_campaigns(
    cursor,
    marketing_data,
):
    for campaign in marketing_data[
        "campaigns"
    ]:
        cursor.execute(
            """
            INSERT INTO commerce.campaign (
                campaign_id,
                organization_id,
                name,
                channel,
                start_at,
                end_at,
                budget_amount
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s
            );
            """,
            (
                campaign["campaign_id"],
                campaign["organization_id"],
                campaign["name"],
                campaign["channel"],
                campaign["start_at"],
                campaign["end_at"],
                campaign["budget_amount"],
            ),
        )


def insert_behavior_data(
    cursor,
    behavior_data,
):
    for session in behavior_data[
        "customer_sessions"
    ]:
        cursor.execute(
            """
            INSERT INTO commerce.customer_session (
                session_id,
                organization_id,
                customer_id,
                started_at,
                ended_at,
                acquisition_channel,
                device_type,
                city
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            );
            """,
            (
                session["session_id"],
                session["organization_id"],
                session["customer_id"],
                session["started_at"],
                session["ended_at"],
                session["acquisition_channel"],
                session["device_type"],
                session["city"],
            ),
        )

    for event in behavior_data[
        "search_events"
    ]:
        cursor.execute(
            """
            INSERT INTO commerce.search_event (
                search_event_id,
                organization_id,
                session_id,
                customer_id,
                search_query,
                results_count,
                occurred_at
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s
            );
            """,
            (
                event["search_event_id"],
                event["organization_id"],
                event["session_id"],
                event["customer_id"],
                event["search_query"],
                event["results_count"],
                event["occurred_at"],
            ),
        )

    for event in behavior_data[
        "click_events"
    ]:
        cursor.execute(
            """
            INSERT INTO commerce.click_event (
                click_event_id,
                organization_id,
                session_id,
                customer_id,
                sku_id,
                page_type,
                occurred_at
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s
            );
            """,
            (
                event["click_event_id"],
                event["organization_id"],
                event["session_id"],
                event["customer_id"],
                event["sku_id"],
                event["page_type"],
                event["occurred_at"],
            ),
        )

    for impression in behavior_data[
        "impressions"
    ]:
        cursor.execute(
            """
            INSERT INTO commerce.impression (
                impression_id,
                organization_id,
                session_id,
                customer_id,
                sku_id,
                campaign_id,
                occurred_at
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s
            );
            """,
            (
                impression["impression_id"],
                impression["organization_id"],
                impression["session_id"],
                impression["customer_id"],
                impression["sku_id"],
                impression["campaign_id"],
                impression["occurred_at"],
            ),
        )


def test_generated_customer_behavior_can_insert(
    connection,
    generated_data,
):
    (
        master_data,
        marketing_data,
        behavior_data,
    ) = generated_data

    try:
        with connection.cursor() as cursor:
            insert_master_data(
                cursor,
                master_data,
            )

            insert_campaigns(
                cursor,
                marketing_data,
            )

            insert_behavior_data(
                cursor,
                behavior_data,
            )

            expected_counts = {
                "customer_session": len(
                    behavior_data[
                        "customer_sessions"
                    ]
                ),
                "search_event": len(
                    behavior_data[
                        "search_events"
                    ]
                ),
                "click_event": len(
                    behavior_data[
                        "click_events"
                    ]
                ),
                "impression": len(
                    behavior_data[
                        "impressions"
                    ]
                ),
            }

            for table, expected_count in (
                expected_counts.items()
            ):
                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM commerce.{table};
                    """
                )

                actual_count = cursor.fetchone()[0]

                assert (
                    actual_count
                    == expected_count
                )

    finally:
        connection.rollback()