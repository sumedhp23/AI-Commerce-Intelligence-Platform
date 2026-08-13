from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = PROJECT_ROOT / "data-platform" / "synthetic"

if str(SYNTHETIC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTHETIC_DIR))

from config import GeneratorConfig
from fulfillment import SyntheticFulfillmentGenerator
from generator import SyntheticCommerceGenerator


@pytest.fixture
def config():
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
    )


@pytest.fixture
def master_data(config):
    return SyntheticCommerceGenerator(config).generate()


@pytest.fixture
def fulfillment_data(config, master_data):
    return SyntheticFulfillmentGenerator(
        config=config,
        master_data=master_data,
    ).generate()


def test_generator_is_deterministic(
    config,
    master_data,
):
    first = SyntheticFulfillmentGenerator(
        config=config,
        master_data=master_data,
    ).generate()

    second = SyntheticFulfillmentGenerator(
        config=config,
        master_data=master_data,
    ).generate()

    assert first == second


def test_expected_entity_counts(
    config,
    fulfillment_data,
):
    assert (
        len(fulfillment_data["fulfillment_locations"])
        == config.total_fulfillment_locations
    )

    assert (
        len(fulfillment_data["inventory_snapshots"])
        == (
            config.total_fulfillment_locations
            * config.total_skus
            * config.inventory_snapshot_days
        )
    )

    assert (
        len(fulfillment_data["inventory_movements"])
        == (
            config.total_fulfillment_locations
            * config.total_skus
            * config.inventory_movements_per_sku_location
        )
    )

    assert (
        len(fulfillment_data["purchase_orders"])
        == config.total_purchase_orders
    )

    assert (
        len(fulfillment_data["purchase_order_items"])
        == (
            config.total_purchase_orders
            * config.purchase_order_items_per_order
        )
    )


def test_fulfillment_locations_are_valid(
    fulfillment_data,
):
    valid_types = {
        "WAREHOUSE",
        "DARK_STORE",
        "RETAIL_STORE",
        "RESTAURANT",
        "DISTRIBUTION_CENTER",
    }

    locations = fulfillment_data[
        "fulfillment_locations"
    ]

    assert locations

    assert all(
        location["location_type"] in valid_types
        for location in locations
    )

    assert all(
        location["active"] is True
        for location in locations
    )

    assert len({
        location["fulfillment_location_id"]
        for location in locations
    }) == len(locations)


def test_inventory_snapshots_are_valid(
    fulfillment_data,
):
    snapshots = fulfillment_data[
        "inventory_snapshots"
    ]

    assert snapshots

    assert all(
        snapshot["quantity_on_hand"] >= 0
        for snapshot in snapshots
    )

    assert all(
        snapshot["quantity_reserved"] >= 0
        for snapshot in snapshots
    )

    assert all(
        snapshot["quantity_available"] >= 0
        for snapshot in snapshots
    )

    assert all(
        snapshot["quantity_available"]
        == (
            snapshot["quantity_on_hand"]
            - snapshot["quantity_reserved"]
        )
        for snapshot in snapshots
    )

    unique_keys = {
        (
            snapshot["organization_id"],
            snapshot["sku_id"],
            snapshot["fulfillment_location_id"],
            snapshot["snapshot_date"],
        )
        for snapshot in snapshots
    }

    assert len(unique_keys) == len(snapshots)


def test_inventory_movements_are_valid(
    fulfillment_data,
):
    valid_types = {
        "PURCHASE",
        "SALE",
        "RETURN",
        "TRANSFER_IN",
        "TRANSFER_OUT",
        "ADJUSTMENT",
        "DAMAGE",
        "EXPIRY",
    }

    movements = fulfillment_data[
        "inventory_movements"
    ]

    assert movements

    assert all(
        movement["movement_type"] in valid_types
        for movement in movements
    )

    for movement in movements:
        if movement["movement_type"] in {
            "PURCHASE",
            "RETURN",
            "TRANSFER_IN",
        }:
            assert movement["quantity"] > 0

        elif movement["movement_type"] in {
            "SALE",
            "TRANSFER_OUT",
            "DAMAGE",
            "EXPIRY",
        }:
            assert movement["quantity"] < 0

        else:
            assert movement["quantity"] != 0


def test_purchase_orders_reference_valid_master_data(
    master_data,
    fulfillment_data,
):
    supplier_ids = {
        supplier["supplier_id"]
        for supplier in master_data["suppliers"]
    }

    location_ids = {
        location["fulfillment_location_id"]
        for location in fulfillment_data[
            "fulfillment_locations"
        ]
    }

    orders = fulfillment_data[
        "purchase_orders"
    ]

    assert all(
        order["supplier_id"] in supplier_ids
        for order in orders
    )

    assert all(
        order["fulfillment_location_id"] in location_ids
        for order in orders
    )

    assert len({
        (
            order["organization_id"],
            order["purchase_order_number"],
        )
        for order in orders
    }) == len(orders)


def test_purchase_order_items_are_valid(
    master_data,
    fulfillment_data,
):
    order_ids = {
        order["purchase_order_id"]
        for order in fulfillment_data[
            "purchase_orders"
        ]
    }

    sku_ids = {
        sku["sku_id"]
        for sku in master_data["skus"]
    }

    items = fulfillment_data[
        "purchase_order_items"
    ]

    assert all(
        item["purchase_order_id"] in order_ids
        for item in items
    )

    assert all(
        item["sku_id"] in sku_ids
        for item in items
    )

    assert all(
        item["quantity_ordered"] > 0
        for item in items
    )

    assert all(
        item["unit_cost"] >= 0
        for item in items
    )


def test_organization_relationships_are_valid(
    master_data,
    fulfillment_data,
):
    organization_ids = {
        organization["organization_id"]
        for organization in master_data[
            "organizations"
        ]
    }

    for location in fulfillment_data[
        "fulfillment_locations"
    ]:
        assert location["organization_id"] in organization_ids

    for snapshot in fulfillment_data[
        "inventory_snapshots"
    ]:
        assert snapshot["organization_id"] in organization_ids

    for movement in fulfillment_data[
        "inventory_movements"
    ]:
        assert movement["organization_id"] in organization_ids

    for order in fulfillment_data[
        "purchase_orders"
    ]:
        assert order["organization_id"] in organization_ids

    for item in fulfillment_data[
        "purchase_order_items"
    ]:
        assert item["organization_id"] in organization_ids