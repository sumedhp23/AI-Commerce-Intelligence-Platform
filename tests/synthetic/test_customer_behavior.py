import sys
from datetime import timedelta
from pathlib import Path

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


def make_customer_behavior_config() -> GeneratorConfig:
    return GeneratorConfig(
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


def build_customer_behavior_data():
    config = make_customer_behavior_config()

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
        config,
        master_data,
        marketing_data,
        behavior_data,
    )


def test_customer_behavior_generation_is_deterministic():
    first = build_customer_behavior_data()[-1]
    second = build_customer_behavior_data()[-1]

    assert first == second


def test_expected_entity_counts():
    (
        config,
        _,
        _,
        behavior_data,
    ) = build_customer_behavior_data()

    assert len(
        behavior_data["customer_sessions"]
    ) == config.total_sessions

    assert len(
        behavior_data["search_events"]
    ) == config.total_search_events

    assert len(
        behavior_data["click_events"]
    ) == config.total_click_events

    assert len(
        behavior_data["impressions"]
    ) == config.total_impressions


def test_session_relationships_are_valid():
    (
        _,
        master_data,
        _,
        behavior_data,
    ) = build_customer_behavior_data()

    customers_by_id = {
        customer["customer_id"]: customer
        for customer in master_data["customers"]
    }

    sessions = behavior_data[
        "customer_sessions"
    ]

    assert len({
        session["session_id"]
        for session in sessions
    }) == len(sessions)

    for session in sessions:
        customer = customers_by_id[
            session["customer_id"]
        ]

        assert (
            session["organization_id"]
            == customer["organization_id"]
        )

        assert (
            session["started_at"]
            < session["ended_at"]
        )


def test_event_relationships_are_valid():
    (
        _,
        master_data,
        marketing_data,
        behavior_data,
    ) = build_customer_behavior_data()

    sessions_by_id = {
        session["session_id"]: session
        for session in behavior_data[
            "customer_sessions"
        ]
    }

    customers_by_id = {
        customer["customer_id"]: customer
        for customer in master_data["customers"]
    }

    skus_by_id = {
        sku["sku_id"]: sku
        for sku in master_data["skus"]
    }

    campaigns_by_id = {
        campaign["campaign_id"]: campaign
        for campaign in marketing_data[
            "campaigns"
        ]
    }

    for event_group, session_key in [
        (
            behavior_data["search_events"],
            "session_id",
        ),
        (
            behavior_data["click_events"],
            "session_id",
        ),
        (
            behavior_data["impressions"],
            "session_id",
        ),
    ]:
        for event in event_group:
            session = sessions_by_id[
                event[session_key]
            ]

            customer = customers_by_id[
                event["customer_id"]
            ]

            assert (
                event["organization_id"]
                == session["organization_id"]
            )

            assert (
                event["customer_id"]
                == session["customer_id"]
            )

            assert (
                customer["organization_id"]
                == session["organization_id"]
            )

            assert (
                session["started_at"]
                <= event["occurred_at"]
                <= session["ended_at"]
            )

    for event in behavior_data["click_events"]:
        sku = skus_by_id[event["sku_id"]]

        assert (
            sku["organization_id"]
            == event["organization_id"]
        )

    for impression in behavior_data[
        "impressions"
    ]:
        sku = skus_by_id[
            impression["sku_id"]
        ]

        campaign = campaigns_by_id[
            impression["campaign_id"]
        ]

        assert (
            sku["organization_id"]
            == impression["organization_id"]
        )

        assert (
            campaign["organization_id"]
            == impression["organization_id"]
        )


def test_search_results_are_valid():
    behavior_data = build_customer_behavior_data()[-1]

    for event in behavior_data[
        "search_events"
    ]:
        assert event["search_query"].strip()
        assert event["results_count"] >= 0


def test_session_values_are_valid():
    behavior_data = build_customer_behavior_data()[-1]

    valid_devices = {
        "MOBILE",
        "DESKTOP",
        "TABLET",
    }

    for session in behavior_data[
        "customer_sessions"
    ]:
        assert session["device_type"] in valid_devices
        assert session["acquisition_channel"] in {
            "ORGANIC",
            "PAID",
        }
        assert session["city"]


def test_click_values_are_valid():
    behavior_data = build_customer_behavior_data()[-1]

    valid_page_types = {
        "SEARCH_RESULTS",
        "PRODUCT_DETAIL",
        "CATEGORY",
        "RECOMMENDATION",
    }

    for event in behavior_data[
        "click_events"
    ]:
        assert event["page_type"] in valid_page_types


def test_event_timestamps_stay_inside_sessions():
    behavior_data = build_customer_behavior_data()[-1]

    sessions_by_id = {
        session["session_id"]: session
        for session in behavior_data[
            "customer_sessions"
        ]
    }

    for events in (
        behavior_data["search_events"],
        behavior_data["click_events"],
        behavior_data["impressions"],
    ):
        for event in events:
            session = sessions_by_id[
                event["session_id"]
            ]

            assert (
                session["started_at"]
                <= event["occurred_at"]
                <= session["ended_at"]
            )


def test_schema_column_names():
    behavior_data = build_customer_behavior_data()[-1]

    assert set(
        behavior_data["customer_sessions"][0]
    ) == {
        "session_id",
        "organization_id",
        "customer_id",
        "started_at",
        "ended_at",
        "acquisition_channel",
        "device_type",
        "city",
    }

    assert set(
        behavior_data["search_events"][0]
    ) == {
        "search_event_id",
        "organization_id",
        "session_id",
        "customer_id",
        "search_query",
        "results_count",
        "occurred_at",
    }

    assert set(
        behavior_data["click_events"][0]
    ) == {
        "click_event_id",
        "organization_id",
        "session_id",
        "customer_id",
        "sku_id",
        "page_type",
        "occurred_at",
    }

    assert set(
        behavior_data["impressions"][0]
    ) == {
        "impression_id",
        "organization_id",
        "session_id",
        "customer_id",
        "sku_id",
        "campaign_id",
        "occurred_at",
    }


def test_summary_matches_generated_data():
    (
        config,
        _,
        _,
        behavior_data,
    ) = build_customer_behavior_data()

    generator = SyntheticCustomerBehaviorGenerator(
        config=config,
    )

    summary = generator.summary()

    assert summary["sessions"] == len(
        behavior_data["customer_sessions"]
    )

    assert summary["search_events"] == len(
        behavior_data["search_events"]
    )

    assert summary["click_events"] == len(
        behavior_data["click_events"]
    )

    assert summary["impressions"] == len(
        behavior_data["impressions"]
    )