import sys
from decimal import Decimal
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = PROJECT_ROOT / "data-platform" / "synthetic"

if str(SYNTHETIC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTHETIC_DIR))

from config import GeneratorConfig
from fulfillment import SyntheticFulfillmentGenerator
from generator import SyntheticCommerceGenerator
from logistics import SyntheticLogisticsGenerator
from transactions import SyntheticTransactionGenerator


def make_logistics_config() -> GeneratorConfig:
    return GeneratorConfig(
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


def build_logistics_data():
    config = make_logistics_config()

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
        config,
        master_data,
        transaction_data,
        fulfillment_data,
        logistics_data,
    )


def test_logistics_generation_is_deterministic():
    first = build_logistics_data()[-1]
    second = build_logistics_data()[-1]

    assert first == second


def test_expected_entity_counts():
    (
        config,
        _,
        transaction_data,
        fulfillment_data,
        logistics_data,
    ) = build_logistics_data()

    assert len(logistics_data["drivers"]) == (
        config.total_drivers
    )

    assert len(logistics_data["deliveries"]) == (
        len(transaction_data["customer_orders"])
    )

    assert len(logistics_data["shipments"]) == (
        len(fulfillment_data["purchase_orders"])
    )


def test_driver_relationships_are_valid():
    (
        _,
        master_data,
        _,
        _,
        logistics_data,
    ) = build_logistics_data()

    organization_ids = {
        organization["organization_id"]
        for organization in master_data["organizations"]
    }

    drivers = logistics_data["drivers"]

    assert drivers

    assert all(
        driver["organization_id"]
        in organization_ids
        for driver in drivers
    )

    assert len({
        driver["driver_id"]
        for driver in drivers
    }) == len(drivers)

    assert len({
        (
            driver["organization_id"],
            driver["external_driver_id"],
        )
        for driver in drivers
    }) == len(drivers)


def test_driver_statuses_are_valid():
    valid_statuses = {
        "ACTIVE",
        "INACTIVE",
        "SUSPENDED",
    }

    logistics_data = build_logistics_data()[-1]

    assert all(
        driver["status"] in valid_statuses
        for driver in logistics_data["drivers"]
    )


def test_delivery_relationships_are_valid():
    (
        _,
        master_data,
        transaction_data,
        _,
        logistics_data,
    ) = build_logistics_data()

    organization_ids = {
        organization["organization_id"]
        for organization in master_data["organizations"]
    }

    order_by_id = {
        order["order_id"]: order
        for order in transaction_data[
            "customer_orders"
        ]
    }

    driver_by_id = {
        driver["driver_id"]: driver
        for driver in logistics_data["drivers"]
    }

    deliveries = logistics_data["deliveries"]

    assert all(
        delivery["organization_id"]
        in organization_ids
        for delivery in deliveries
    )

    assert all(
        delivery["order_id"] in order_by_id
        for delivery in deliveries
    )

    assert all(
        delivery["driver_id"] in driver_by_id
        for delivery in deliveries
    )

    for delivery in deliveries:
        order = order_by_id[
            delivery["order_id"]
        ]

        driver = driver_by_id[
            delivery["driver_id"]
        ]

        assert (
            delivery["organization_id"]
            == order["organization_id"]
        )

        assert (
            delivery["organization_id"]
            == driver["organization_id"]
        )


def test_delivery_statuses_are_valid():
    valid_statuses = {
        "PENDING",
        "ASSIGNED",
        "PICKED_UP",
        "IN_TRANSIT",
        "DELIVERED",
        "FAILED",
        "CANCELLED",
    }

    logistics_data = build_logistics_data()[-1]

    assert all(
        delivery["delivery_status"]
        in valid_statuses
        for delivery in logistics_data[
            "deliveries"
        ]
    )


def test_delivery_timestamps_are_valid():
    (
        _,
        _,
        transaction_data,
        _,
        logistics_data,
    ) = build_logistics_data()

    orders_by_id = {
        order["order_id"]: order
        for order in transaction_data[
            "customer_orders"
        ]
    }

    for delivery in logistics_data[
        "deliveries"
    ]:
        order = orders_by_id[
            delivery["order_id"]
        ]

        assert (
            delivery["promised_at"]
            >= order["ordered_at"]
        )

        if delivery["dispatched_at"] is not None:
            assert (
                delivery["dispatched_at"]
                >= order["ordered_at"]
            )

        if delivery["delivered_at"] is not None:
            assert (
                delivery["dispatched_at"]
                is not None
            )

            assert (
                delivery["delivered_at"]
                >= delivery["dispatched_at"]
            )


def test_delivery_distances_are_valid():
    logistics_data = build_logistics_data()[-1]

    assert all(
        delivery["delivery_distance_km"]
        > Decimal("0.0")
        for delivery in logistics_data[
            "deliveries"
        ]
    )


def test_shipment_relationships_are_valid():
    (
        _,
        master_data,
        _,
        fulfillment_data,
        logistics_data,
    ) = build_logistics_data()

    organization_ids = {
        organization["organization_id"]
        for organization in master_data["organizations"]
    }

    purchase_orders_by_id = {
        order["purchase_order_id"]: order
        for order in fulfillment_data[
            "purchase_orders"
        ]
    }

    shipments = logistics_data["shipments"]

    assert all(
        shipment["organization_id"]
        in organization_ids
        for shipment in shipments
    )

    assert all(
        shipment["purchase_order_id"]
        in purchase_orders_by_id
        for shipment in shipments
    )

    for shipment in shipments:
        purchase_order = purchase_orders_by_id[
            shipment["purchase_order_id"]
        ]

        assert (
            shipment["organization_id"]
            == purchase_order["organization_id"]
        )


def test_shipment_statuses_are_valid():
    valid_statuses = {
        "SHIPPED",
        "IN_TRANSIT",
        "RECEIVED",
    }

    logistics_data = build_logistics_data()[-1]

    assert all(
        shipment["shipment_status"]
        in valid_statuses
        for shipment in logistics_data[
            "shipments"
        ]
    )


def test_shipment_timestamps_are_valid():
    (
        _,
        _,
        _,
        fulfillment_data,
        logistics_data,
    ) = build_logistics_data()

    purchase_orders_by_id = {
        order["purchase_order_id"]: order
        for order in fulfillment_data[
            "purchase_orders"
        ]
    }

    for shipment in logistics_data[
        "shipments"
    ]:
        purchase_order = purchase_orders_by_id[
            shipment["purchase_order_id"]
        ]

        assert (
            shipment["shipped_at"]
            >= purchase_order["ordered_at"]
        )

        if shipment["received_at"] is not None:
            assert (
                shipment["received_at"]
                >= shipment["shipped_at"]
            )


def test_logistics_schema_column_names():
    logistics_data = build_logistics_data()[-1]

    assert set(logistics_data["drivers"][0]) == {
        "driver_id",
        "organization_id",
        "external_driver_id",
        "city",
        "status",
    }

    assert set(logistics_data["deliveries"][0]) == {
        "delivery_id",
        "organization_id",
        "order_id",
        "driver_id",
        "delivery_status",
        "promised_at",
        "dispatched_at",
        "delivered_at",
        "delivery_distance_km",
    }

    assert set(logistics_data["shipments"][0]) == {
        "shipment_id",
        "organization_id",
        "purchase_order_id",
        "shipment_status",
        "shipped_at",
        "received_at",
    }