import sys
from decimal import Decimal
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = PROJECT_ROOT / "data-platform" / "synthetic"

if str(SYNTHETIC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTHETIC_DIR))

from config import GeneratorConfig
from transactions import SyntheticTransactionGenerator


def make_transaction_config() -> GeneratorConfig:
    return GeneratorConfig(
        seed=42,
        organizations=2,
        brands_per_organization=2,
        categories_per_organization=3,
        products_per_organization=4,
        skus_per_product=2,
        customers_per_organization=5,
        suppliers_per_organization=2,
        customer_segments_per_organization=3,
    )


def test_transaction_generation_is_deterministic():
    config = make_transaction_config()

    generator_a = SyntheticTransactionGenerator(config)
    generator_b = SyntheticTransactionGenerator(config)

    assert generator_a.generate() == generator_b.generate()


def test_expected_transaction_counts():
    config = make_transaction_config()

    generator = SyntheticTransactionGenerator(config)

    data = generator.generate(
        orders_per_customer=2,
        items_per_order=3,
    )

    expected_orders = (
        config.total_customers * 2
    )

    expected_items = (
        expected_orders * 3
    )

    assert len(data["customer_orders"]) == expected_orders
    assert len(data["order_items"]) == expected_items
    assert len(data["payments"]) == expected_orders


def test_order_relationships_are_valid():
    config = make_transaction_config()

    data = SyntheticTransactionGenerator(
        config
    ).generate()

    customer_ids = {
        customer["customer_id"]
        for customer in SyntheticTransactionGenerator(
            config
        ).master_data["customers"]
    }

    organization_ids = {
        organization["organization_id"]
        for organization in SyntheticTransactionGenerator(
            config
        ).master_data["organizations"]
    }

    for order in data["customer_orders"]:
        assert order["customer_id"] in customer_ids
        assert order["organization_id"] in organization_ids


def test_order_item_relationships_are_valid():
    config = make_transaction_config()

    generator = SyntheticTransactionGenerator(config)
    data = generator.generate()

    order_ids = {
        order["order_id"]
        for order in data["customer_orders"]
    }

    sku_ids = {
        sku["sku_id"]
        for sku in generator.master_data["skus"]
    }

    for item in data["order_items"]:
        assert item["order_id"] in order_ids
        assert item["sku_id"] in sku_ids
        assert item["quantity"] > 0
        assert item["unit_price"] >= Decimal("0.00")


def test_order_totals_match_order_items():
    config = make_transaction_config()

    generator = SyntheticTransactionGenerator(config)

    data = generator.generate(
        orders_per_customer=1,
        items_per_order=2,
    )

    items_by_order = {}

    for item in data["order_items"]:
        items_by_order.setdefault(
            item["order_id"],
            [],
        ).append(item)

    for order in data["customer_orders"]:
        items = items_by_order[order["order_id"]]

        subtotal = sum(
            (
                item["unit_price"]
                * item["quantity"]
            )
            for item in items
        )

        expected_total = (
            subtotal
            + Decimal("40.00")
            + (
                subtotal
                * Decimal("0.18")
            ).quantize(Decimal("0.01"))
        ).quantize(Decimal("0.01"))

        assert order["subtotal_amount"] == subtotal
        assert order["total_amount"] == expected_total


def test_payment_matches_order_total():
    config = make_transaction_config()

    generator = SyntheticTransactionGenerator(config)
    data = generator.generate()

    orders_by_id = {
        order["order_id"]: order
        for order in data["customer_orders"]
    }

    for payment in data["payments"]:
        order = orders_by_id[payment["order_id"]]

        assert payment["amount"] == order["total_amount"]
        assert payment["payment_status"] == "CAPTURED"
        assert payment["paid_at"] > order["ordered_at"]


def test_transaction_schema_column_names():
    config = make_transaction_config()

    data = SyntheticTransactionGenerator(
        config
    ).generate()

    assert set(data["customer_orders"][0]) == {
        "order_id",
        "organization_id",
        "customer_id",
        "fulfillment_location_id",
        "order_number",
        "order_status",
        "currency",
        "subtotal_amount",
        "discount_amount",
        "delivery_fee",
        "tax_amount",
        "total_amount",
        "ordered_at",
        "cancelled_at",
    }

    assert set(data["order_items"][0]) == {
        "order_item_id",
        "organization_id",
        "order_id",
        "sku_id",
        "quantity",
        "unit_price",
        "discount_amount",
    }

    assert set(data["payments"][0]) == {
        "payment_id",
        "organization_id",
        "order_id",
        "payment_method",
        "payment_status",
        "amount",
        "transaction_reference",
        "paid_at",
    }