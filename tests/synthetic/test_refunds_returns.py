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
        organizations=1,
        brands_per_organization=2,
        categories_per_organization=2,
        products_per_organization=3,
        skus_per_product=2,
        customers_per_organization=10,
        suppliers_per_organization=2,
        customer_segments_per_organization=2,
    )


def test_refund_return_generation_is_deterministic():
    config = make_transaction_config()

    generator_a = SyntheticTransactionGenerator(config)
    generator_b = SyntheticTransactionGenerator(config)

    data_a = generator_a.generate()
    data_b = generator_b.generate()

    assert data_a["customer_returns"] == data_b[
        "customer_returns"
    ]
    assert data_a["refunds"] == data_b["refunds"]


def test_returns_are_generated_for_every_fifth_order():
    config = make_transaction_config()

    generator = SyntheticTransactionGenerator(config)

    data = generator.generate()

    expected_returns = (
        len(data["customer_orders"]) // 5
    )

    assert len(data["customer_returns"]) == expected_returns


def test_return_status_policy_is_valid():
    config = make_transaction_config()

    generator = SyntheticTransactionGenerator(config)

    data = generator.generate()

    for index, customer_return in enumerate(
        data["customer_returns"],
        start=1,
    ):
        assert customer_return["return_status"] in {
            "REQUESTED",
            "COMPLETED",
            "REJECTED",
        }

        if index % 2 == 1:
            assert (
                customer_return["return_status"]
                == "COMPLETED"
            )
            assert (
                customer_return["completed_at"]
                is not None
            )
        else:
            assert (
                customer_return["return_status"]
                == "REJECTED"
            )
            assert (
                customer_return["completed_at"]
                is None
            )


def test_return_timestamps_are_valid():
    config = make_transaction_config()

    generator = SyntheticTransactionGenerator(config)

    data = generator.generate()

    orders_by_id = {
        order["order_id"]: order
        for order in data["customer_orders"]
    }

    for customer_return in data["customer_returns"]:
        order = orders_by_id[
            customer_return["order_id"]
        ]

        assert (
            customer_return["requested_at"]
            > order["ordered_at"]
        )

        if customer_return["completed_at"] is not None:
            assert (
                customer_return["completed_at"]
                > customer_return["requested_at"]
            )


def test_refunds_only_reference_completed_returns():
    config = make_transaction_config()

    generator = SyntheticTransactionGenerator(config)

    data = generator.generate()

    returns_by_order = {
        customer_return["order_id"]: customer_return
        for customer_return in data["customer_returns"]
    }

    for refund in data["refunds"]:
        customer_return = returns_by_order[
            refund["order_id"]
        ]

        assert (
            customer_return["return_status"]
            == "COMPLETED"
        )


def test_refund_amounts_are_valid():
    config = make_transaction_config()

    generator = SyntheticTransactionGenerator(config)

    data = generator.generate()

    orders_by_id = {
        order["order_id"]: order
        for order in data["customer_orders"]
    }

    payments_by_id = {
        payment["payment_id"]: payment
        for payment in data["payments"]
    }

    for refund in data["refunds"]:
        order = orders_by_id[refund["order_id"]]
        payment = payments_by_id[
            refund["payment_id"]
        ]

        assert refund["amount"] >= Decimal("0.00")
        assert (
            refund["amount"]
            <= order["total_amount"]
        )
        assert (
            refund["amount"]
            <= payment["amount"]
        )


def test_refund_relationships_are_valid():
    config = make_transaction_config()

    generator = SyntheticTransactionGenerator(config)

    data = generator.generate()

    order_ids = {
        order["order_id"]
        for order in data["customer_orders"]
    }

    payment_by_id = {
        payment["payment_id"]: payment
        for payment in data["payments"]
    }

    for refund in data["refunds"]:
        assert refund["order_id"] in order_ids

        payment = payment_by_id[
            refund["payment_id"]
        ]

        assert (
            payment["order_id"]
            == refund["order_id"]
        )
        assert (
            payment["organization_id"]
            == refund["organization_id"]
        )


def test_refund_timestamp_is_after_return_completion():
    config = make_transaction_config()

    generator = SyntheticTransactionGenerator(config)

    data = generator.generate()

    returns_by_order = {
        customer_return["order_id"]: customer_return
        for customer_return in data["customer_returns"]
    }

    for refund in data["refunds"]:
        customer_return = returns_by_order[
            refund["order_id"]
        ]

        assert (
            customer_return["completed_at"]
            is not None
        )

        assert (
            refund["refunded_at"]
            >= customer_return["completed_at"]
        )


def test_refund_and_return_schema_column_names():
    config = make_transaction_config()

    generator = SyntheticTransactionGenerator(config)

    data = generator.generate()

    if data["customer_returns"]:
        assert set(
            data["customer_returns"][0]
        ) == {
            "return_id",
            "organization_id",
            "order_id",
            "return_status",
            "reason",
            "requested_at",
            "completed_at",
        }

    if data["refunds"]:
        assert set(data["refunds"][0]) == {
            "refund_id",
            "organization_id",
            "order_id",
            "payment_id",
            "amount",
            "reason",
            "refunded_at",
        }