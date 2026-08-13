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
        campaigns_per_organization=5,
        promotions_per_organization=5,
        coupons_per_promotion=3,
    )

    master_data = SyntheticCommerceGenerator(
        config
    ).generate()

    marketing_data = SyntheticMarketingGenerator(
        config=config,
        master_data=master_data,
    ).generate()

    return (
        master_data,
        marketing_data,
    )


def insert_organizations(cursor, master_data):
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


def insert_marketing_data(
    cursor,
    marketing_data,
):
    for campaign in marketing_data["campaigns"]:
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

    for promotion in marketing_data["promotions"]:
        cursor.execute(
            """
            INSERT INTO commerce.promotion (
                promotion_id,
                organization_id,
                name,
                promotion_type,
                discount_percentage,
                discount_amount,
                start_at,
                end_at
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            );
            """,
            (
                promotion["promotion_id"],
                promotion["organization_id"],
                promotion["name"],
                promotion["promotion_type"],
                promotion["discount_percentage"],
                promotion["discount_amount"],
                promotion["start_at"],
                promotion["end_at"],
            ),
        )

    for coupon in marketing_data["coupons"]:
        cursor.execute(
            """
            INSERT INTO commerce.coupon (
                coupon_id,
                organization_id,
                promotion_id,
                coupon_code,
                usage_limit
            )
            VALUES (
                %s, %s, %s, %s, %s
            );
            """,
            (
                coupon["coupon_id"],
                coupon["organization_id"],
                coupon["promotion_id"],
                coupon["coupon_code"],
                coupon["usage_limit"],
            ),
        )


def test_generated_marketing_data_can_insert(
    connection,
    generated_data,
):
    master_data, marketing_data = generated_data

    try:
        with connection.cursor() as cursor:
            insert_organizations(
                cursor,
                master_data,
            )

            insert_marketing_data(
                cursor,
                marketing_data,
            )

            expected_counts = {
                "campaign": len(
                    marketing_data["campaigns"]
                ),
                "promotion": len(
                    marketing_data["promotions"]
                ),
                "coupon": len(
                    marketing_data["coupons"]
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