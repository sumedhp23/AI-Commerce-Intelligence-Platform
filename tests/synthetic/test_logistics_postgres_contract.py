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
from fulfillment import SyntheticFulfillmentGenerator
from generator import SyntheticCommerceGenerator
from logistics import SyntheticLogisticsGenerator
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
        organizations=1,
        brands_per_organization=2,
        categories_per_organization=2,
        products_per_organization=3,
        skus_per_product=2,
        customers_per_organization=5,
        suppliers_per_organization=2,
        customer_segments_per_organization=2,
        fulfillment_locations_per_organization=2,
        inventory_snapshot_days=3,
        inventory_movements_per_sku_location=4,
        purchase_orders_per_organization=3,
        purchase_order_items_per_order=2,
        drivers_per_organization=5,
    )

    master_data = SyntheticCommerceGenerator(
        config
    ).generate()

    transaction_data = SyntheticTransactionGenerator(
        config=config,
        master_data=master_data,
    ).generate(
        orders_per_customer=1,
        items_per_order=2,
    )

    fulfillment_data = SyntheticFulfillmentGenerator(
        config=config,
        master_data=master_data,
    ).generate()

    logistics_data = SyntheticLogisticsGenerator(
        config=config,
        master_data=master_data,
        transaction_data=transaction_data,
        fulfillment_data=fulfillment_data,
    ).generate()

    return (
        master_data,
        transaction_data,
        fulfillment_data,
        logistics_data,
    )


def insert_master_data(cursor, data):
    master_data = data

    for organization in master_data["organizations"]:
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

    for category in master_data["categories"]:
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

    for supplier in master_data["suppliers"]:
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

    for customer in master_data["customers"]:
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

    for product in master_data["products"]:
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


def insert_transaction_data(
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

    for payment in transaction_data[
        "payments"
    ]:
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


def insert_fulfillment_data(
    cursor,
    fulfillment_data,
):
    for location in fulfillment_data[
        "fulfillment_locations"
    ]:
        cursor.execute(
            """
            INSERT INTO commerce.fulfillment_location (
                fulfillment_location_id,
                organization_id,
                name,
                location_type,
                city,
                state,
                country_code,
                latitude,
                longitude,
                active
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            );
            """,
            (
                location[
                    "fulfillment_location_id"
                ],
                location["organization_id"],
                location["name"],
                location["location_type"],
                location["city"],
                location["state"],
                location["country_code"],
                location["latitude"],
                location["longitude"],
                location["active"],
            ),
        )

    for snapshot in fulfillment_data[
        "inventory_snapshots"
    ]:
        cursor.execute(
            """
            INSERT INTO commerce.inventory_snapshot (
                inventory_snapshot_id,
                organization_id,
                sku_id,
                fulfillment_location_id,
                snapshot_date,
                quantity_on_hand,
                quantity_reserved,
                quantity_available,
                reorder_point,
                safety_stock
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            );
            """,
            (
                snapshot[
                    "inventory_snapshot_id"
                ],
                snapshot["organization_id"],
                snapshot["sku_id"],
                snapshot[
                    "fulfillment_location_id"
                ],
                snapshot["snapshot_date"],
                snapshot["quantity_on_hand"],
                snapshot["quantity_reserved"],
                snapshot["quantity_available"],
                snapshot["reorder_point"],
                snapshot["safety_stock"],
            ),
        )

    for movement in fulfillment_data[
        "inventory_movements"
    ]:
        cursor.execute(
            """
            INSERT INTO commerce.inventory_movement (
                inventory_movement_id,
                organization_id,
                sku_id,
                fulfillment_location_id,
                movement_type,
                quantity,
                occurred_at,
                reference_type,
                reference_id
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            );
            """,
            (
                movement[
                    "inventory_movement_id"
                ],
                movement["organization_id"],
                movement["sku_id"],
                movement[
                    "fulfillment_location_id"
                ],
                movement["movement_type"],
                movement["quantity"],
                movement["occurred_at"],
                movement["reference_type"],
                movement["reference_id"],
            ),
        )

    for order in fulfillment_data[
        "purchase_orders"
    ]:
        cursor.execute(
            """
            INSERT INTO commerce.purchase_order (
                purchase_order_id,
                organization_id,
                supplier_id,
                fulfillment_location_id,
                purchase_order_number,
                status,
                ordered_at,
                expected_at
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            );
            """,
            (
                order["purchase_order_id"],
                order["organization_id"],
                order["supplier_id"],
                order[
                    "fulfillment_location_id"
                ],
                order["purchase_order_number"],
                order["status"],
                order["ordered_at"],
                order["expected_at"],
            ),
        )

    for item in fulfillment_data[
        "purchase_order_items"
    ]:
        cursor.execute(
            """
            INSERT INTO commerce.purchase_order_item (
                purchase_order_item_id,
                organization_id,
                purchase_order_id,
                sku_id,
                quantity_ordered,
                unit_cost
            )
            VALUES (
                %s, %s, %s, %s, %s, %s
            );
            """,
            (
                item[
                    "purchase_order_item_id"
                ],
                item["organization_id"],
                item["purchase_order_id"],
                item["sku_id"],
                item["quantity_ordered"],
                item["unit_cost"],
            ),
        )


def insert_logistics_data(
    cursor,
    logistics_data,
):
    for driver in logistics_data["drivers"]:
        cursor.execute(
            """
            INSERT INTO commerce.driver (
                driver_id,
                organization_id,
                external_driver_id,
                city,
                status
            )
            VALUES (%s, %s, %s, %s, %s);
            """,
            (
                driver["driver_id"],
                driver["organization_id"],
                driver["external_driver_id"],
                driver["city"],
                driver["status"],
            ),
        )

    for shipment in logistics_data[
        "shipments"
    ]:
        cursor.execute(
            """
            INSERT INTO commerce.shipment (
                shipment_id,
                organization_id,
                purchase_order_id,
                shipment_status,
                shipped_at,
                received_at
            )
            VALUES (
                %s, %s, %s,
                %s, %s, %s
            );
            """,
            (
                shipment["shipment_id"],
                shipment["organization_id"],
                shipment["purchase_order_id"],
                shipment["shipment_status"],
                shipment["shipped_at"],
                shipment["received_at"],
            ),
        )

    for delivery in logistics_data[
        "deliveries"
    ]:
        cursor.execute(
            """
            INSERT INTO commerce.delivery (
                delivery_id,
                organization_id,
                order_id,
                driver_id,
                delivery_status,
                promised_at,
                dispatched_at,
                delivered_at,
                delivery_distance_km
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            );
            """,
            (
                delivery["delivery_id"],
                delivery["organization_id"],
                delivery["order_id"],
                delivery["driver_id"],
                delivery["delivery_status"],
                delivery["promised_at"],
                delivery["dispatched_at"],
                delivery["delivered_at"],
                delivery[
                    "delivery_distance_km"
                ],
            ),
        )


def test_generated_logistics_data_can_insert(
    connection,
    generated_data,
):
    (
        master_data,
        transaction_data,
        fulfillment_data,
        logistics_data,
    ) = generated_data

    try:
        with connection.cursor() as cursor:
            insert_master_data(
                cursor,
                master_data,
            )

            insert_transaction_data(
                cursor,
                transaction_data,
            )

            insert_fulfillment_data(
                cursor,
                fulfillment_data,
            )

            insert_logistics_data(
                cursor,
                logistics_data,
            )

            expected_counts = {
                "driver": len(
                    logistics_data["drivers"]
                ),
                "shipment": len(
                    logistics_data["shipments"]
                ),
                "delivery": len(
                    logistics_data["deliveries"]
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

                actual_count = (
                    cursor.fetchone()[0]
                )

                assert (
                    actual_count
                    == expected_count
                )

    finally:
        connection.rollback()