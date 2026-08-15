import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = PROJECT_ROOT / "data-platform" / "synthetic"

if str(SYNTHETIC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTHETIC_DIR))

from config import GeneratorConfig
from pipeline import SyntheticCommercePipeline


def make_pipeline_config() -> GeneratorConfig:
    return GeneratorConfig(
        seed=42,
        organizations=2,
        brands_per_organization=2,
        categories_per_organization=3,
        products_per_organization=5,
        skus_per_product=2,
        customers_per_organization=10,
        suppliers_per_organization=2,
        customer_segments_per_organization=2,
        fulfillment_locations_per_organization=2,
        inventory_snapshot_days=3,
        inventory_movements_per_sku_location=4,
        purchase_orders_per_organization=2,
        purchase_order_items_per_order=2,
        drivers_per_organization=4,
        campaigns_per_organization=2,
        promotions_per_organization=2,
        coupons_per_promotion=2,
        sessions_per_customer=1,
        search_events_per_session=2,
        click_events_per_session=2,
        impressions_per_session=2,
        reviews_per_customer=1,
        operational_events_per_organization=7,
    )


def test_pipeline_generation_is_deterministic():
    config = make_pipeline_config()

    data_a = SyntheticCommercePipeline(
        config
    ).generate()

    data_b = SyntheticCommercePipeline(
        config
    ).generate()

    assert data_a == data_b


def test_pipeline_contains_all_domains():
    config = make_pipeline_config()

    data = SyntheticCommercePipeline(
        config
    ).generate()

    assert set(data) == {
        "master",
        "transactions",
        "fulfillment",
        "marketing",
        "logistics",
        "customer_behavior",
        "reviews",
        "operational_events",
    }


def test_pipeline_master_data_is_complete():
    config = make_pipeline_config()

    data = SyntheticCommercePipeline(
        config
    ).generate()

    master = data["master"]

    assert master["organizations"]
    assert master["customers"]
    assert master["products"]
    assert master["skus"]
    assert master["brands"]
    assert master["categories"]
    assert master["suppliers"]
    assert master["customer_segments"]


def test_pipeline_transaction_flow_is_complete():
    config = make_pipeline_config()

    data = SyntheticCommercePipeline(
        config
    ).generate()

    transactions = data["transactions"]

    assert transactions["customer_orders"]
    assert transactions["order_items"]
    assert transactions["payments"]
    assert transactions["customer_returns"]
    assert transactions["refunds"]


def test_pipeline_fulfillment_flow_is_complete():
    config = make_pipeline_config()

    data = SyntheticCommercePipeline(
        config
    ).generate()

    fulfillment = data["fulfillment"]

    assert fulfillment["fulfillment_locations"]
    assert fulfillment["inventory_snapshots"]
    assert fulfillment["inventory_movements"]
    assert fulfillment["purchase_orders"]
    assert fulfillment["purchase_order_items"]


def test_pipeline_downstream_domains_are_populated():
    config = make_pipeline_config()

    data = SyntheticCommercePipeline(
        config
    ).generate()

    assert data["marketing"]["campaigns"]
    assert data["marketing"]["promotions"]
    assert data["marketing"]["coupons"]

    assert data["logistics"]["drivers"]
    assert data["logistics"]["deliveries"]
    assert data["logistics"]["shipments"]

    assert data["customer_behavior"]["customer_sessions"]
    assert data["customer_behavior"]["search_events"]
    assert data["customer_behavior"]["click_events"]
    assert data["customer_behavior"]["impressions"]

    assert data["reviews"]["reviews"]

    assert data["operational_events"]["operational_events"]


def test_pipeline_preserves_organization_consistency():
    config = make_pipeline_config()

    data = SyntheticCommercePipeline(
        config
    ).generate()

    organization_ids = {
        organization["organization_id"]
        for organization in data["master"]["organizations"]
    }

    for dataset in data.values():
        for rows in dataset.values():
            for row in rows:
                if "organization_id" in row:
                    assert (
                        row["organization_id"]
                        in organization_ids
                    )


def test_pipeline_operational_events_use_pipeline_locations():
    config = make_pipeline_config()

    data = SyntheticCommercePipeline(
        config
    ).generate()

    location_ids = {
        location["fulfillment_location_id"]
        for location in data["fulfillment"][
            "fulfillment_locations"
        ]
    }

    for event in data["operational_events"][
        "operational_events"
    ]:
        if event["location_id"] is not None:
            assert event["location_id"] in location_ids


def test_pipeline_reviews_reference_pipeline_transactions():
    config = make_pipeline_config()

    data = SyntheticCommercePipeline(
        config
    ).generate()

    order_ids = {
        order["order_id"]
        for order in data["transactions"]["customer_orders"]
    }

    for review in data["reviews"]["reviews"]:
        if review["order_id"] is not None:
            assert review["order_id"] in order_ids


def test_pipeline_summary_matches_generated_data():
    config = make_pipeline_config()

    pipeline = SyntheticCommercePipeline(config)

    data = pipeline.generate()
    summary = pipeline.summary()

    expected = {
        dataset_name: sum(
            len(rows)
            for rows in dataset.values()
        )
        for dataset_name, dataset in data.items()
    }

    assert summary == expected