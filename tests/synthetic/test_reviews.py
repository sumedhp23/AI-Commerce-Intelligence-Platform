import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = PROJECT_ROOT / "data-platform" / "synthetic"

if str(SYNTHETIC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTHETIC_DIR))

from config import GeneratorConfig
from generator import SyntheticCommerceGenerator
from reviews import SyntheticReviewGenerator
from transactions import SyntheticTransactionGenerator


def make_reviews_config() -> GeneratorConfig:
    return GeneratorConfig(
        seed=42,
        organizations=2,
        customers_per_organization=10,
        products_per_organization=10,
        skus_per_product=2,
        reviews_per_customer=1,
    )


def build_review_data():
    config = make_reviews_config()

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
        config,
        master_data,
        transaction_data,
        review_data,
    )


def test_review_generation_is_deterministic():
    first = build_review_data()[-1]
    second = build_review_data()[-1]

    assert first == second


def test_expected_review_count():
    (
        config,
        _,
        _,
        review_data,
    ) = build_review_data()

    assert len(review_data["reviews"]) == (
        config.total_reviews
    )


def test_review_relationships_are_valid():
    (
        _,
        master_data,
        transaction_data,
        review_data,
    ) = build_review_data()

    customers_by_id = {
        customer["customer_id"]: customer
        for customer in master_data["customers"]
    }

    skus_by_id = {
        sku["sku_id"]: sku
        for sku in master_data["skus"]
    }

    orders_by_id = {
        order["order_id"]: order
        for order in transaction_data[
            "customer_orders"
        ]
    }

    order_items_by_order: dict[
        str,
        list[dict],
    ] = {}

    for item in transaction_data[
        "order_items"
    ]:
        order_items_by_order.setdefault(
            item["order_id"],
            [],
        ).append(item)

    for review in review_data["reviews"]:
        customer = customers_by_id[
            review["customer_id"]
        ]

        sku = skus_by_id[
            review["sku_id"]
        ]

        assert (
            review["organization_id"]
            == customer["organization_id"]
        )

        assert (
            review["organization_id"]
            == sku["organization_id"]
        )

        if review["order_id"] is not None:
            order = orders_by_id[
                review["order_id"]
            ]

            assert (
                order["organization_id"]
                == review["organization_id"]
            )

            assert (
                order["customer_id"]
                == review["customer_id"]
            )

            order_sku_ids = {
                item["sku_id"]
                for item in order_items_by_order[
                    order["order_id"]
                ]
            }

            assert review["sku_id"] in (
                order_sku_ids
            )


def test_review_ratings_are_valid():
    review_data = build_review_data()[-1]

    for review in review_data["reviews"]:
        assert 1 <= review["rating"] <= 5


def test_review_timestamps_are_valid():
    (
        _,
        master_data,
        transaction_data,
        review_data,
    ) = build_review_data()

    customers_by_id = {
        customer["customer_id"]: customer
        for customer in master_data["customers"]
    }

    orders_by_id = {
        order["order_id"]: order
        for order in transaction_data[
            "customer_orders"
        ]
    }

    for review in review_data["reviews"]:
        if review["order_id"] is not None:
            order = orders_by_id[
                review["order_id"]
            ]

            assert (
                review["created_at"]
                >= order["ordered_at"]
            )
        else:
            assert review["created_at"] is not None


def test_review_text_matches_rating():
    review_data = build_review_data()[-1]

    expected_text = {
        1: "Very disappointing experience.",
        2: "Below expectations.",
        3: "It was okay.",
        4: "Good overall experience.",
        5: "Excellent experience.",
    }

    for review in review_data["reviews"]:
        assert review["review_text"] == (
            expected_text[review["rating"]]
        )


def test_review_ids_are_unique():
    review_data = build_review_data()[-1]

    review_ids = {
        review["review_id"]
        for review in review_data["reviews"]
    }

    assert len(review_ids) == len(
        review_data["reviews"]
    )


def test_schema_column_names():
    review_data = build_review_data()[-1]

    assert set(review_data["reviews"][0]) == {
        "review_id",
        "organization_id",
        "customer_id",
        "sku_id",
        "order_id",
        "rating",
        "review_text",
        "created_at",
    }


def test_summary_matches_generated_data():
    (
        config,
        _,
        _,
        review_data,
    ) = build_review_data()

    generator = SyntheticReviewGenerator(
        config=config,
    )

    summary = generator.summary()

    assert summary["reviews"] == len(
        review_data["reviews"]
    )