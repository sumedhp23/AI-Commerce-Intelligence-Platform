import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = PROJECT_ROOT / "data-platform" / "synthetic"

if str(SYNTHETIC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTHETIC_DIR))

from config import GeneratorConfig
from fulfillment import SyntheticFulfillmentGenerator
from generator import SyntheticCommerceGenerator
from operational_events import (
    SyntheticOperationalEventGenerator,
)


def make_operational_event_config() -> GeneratorConfig:
    return GeneratorConfig(
        seed=42,
        organizations=3,
        brands_per_organization=2,
        categories_per_organization=2,
        products_per_organization=3,
        skus_per_product=2,
        customers_per_organization=10,
        suppliers_per_organization=2,
        customer_segments_per_organization=2,
        fulfillment_locations_per_organization=3,
        operational_events_per_organization=7,
    )


def build_master_data(
    config: GeneratorConfig,
) -> dict:
    master_data = SyntheticCommerceGenerator(
        config
    ).generate()

    fulfillment_generator = (
        SyntheticFulfillmentGenerator(
            config=config,
            master_data=master_data,
        )
    )

    master_data["fulfillment_locations"] = (
        fulfillment_generator.generate_fulfillment_locations()
    )

    return master_data


def test_operational_event_generation_is_deterministic():
    config = make_operational_event_config()

    master_data_a = build_master_data(config)
    master_data_b = build_master_data(config)

    generator_a = SyntheticOperationalEventGenerator(
        config=config,
        master_data=master_data_a,
    )

    generator_b = SyntheticOperationalEventGenerator(
        config=config,
        master_data=master_data_b,
    )

    assert (
        generator_a.generate()
        == generator_b.generate()
    )


def test_operational_event_count_matches_configuration():
    config = make_operational_event_config()

    master_data = build_master_data(config)

    generator = SyntheticOperationalEventGenerator(
        config=config,
        master_data=master_data,
    )

    data = generator.generate()

    assert len(data["operational_events"]) == (
        config.organizations
        * config.operational_events_per_organization
    )


def test_operational_event_organization_relationships_are_valid():
    config = make_operational_event_config()

    master_data = build_master_data(config)

    generator = SyntheticOperationalEventGenerator(
        config=config,
        master_data=master_data,
    )

    data = generator.generate()

    organization_ids = {
        organization["organization_id"]
        for organization in master_data[
            "organizations"
        ]
    }

    for event in data["operational_events"]:
        assert (
            event["organization_id"]
            in organization_ids
        )


def test_location_references_are_valid():
    config = make_operational_event_config()

    master_data = build_master_data(config)

    generator = SyntheticOperationalEventGenerator(
        config=config,
        master_data=master_data,
    )

    data = generator.generate()

    locations_by_id = {
        location["fulfillment_location_id"]: location
        for location in master_data[
            "fulfillment_locations"
        ]
    }

    organizations_by_id = {
        organization["organization_id"]
        for organization in master_data[
            "organizations"
        ]
    }

    for event in data["operational_events"]:
        assert event["organization_id"] in (
            organizations_by_id
        )

        if event["location_id"] is not None:
            assert event["location_id"] in locations_by_id

            location = locations_by_id[
                event["location_id"]
            ]

            assert (
                location["organization_id"]
                == event["organization_id"]
            )


def test_operational_event_types_are_valid():
    config = make_operational_event_config()

    master_data = build_master_data(config)

    generator = SyntheticOperationalEventGenerator(
        config=config,
        master_data=master_data,
    )

    data = generator.generate()

    allowed_event_types = {
        "WAREHOUSE_OUTAGE",
        "PAYMENT_GATEWAY_OUTAGE",
        "INVENTORY_SYSTEM_FAILURE",
        "DELIVERY_CAPACITY_REDUCTION",
        "PRICING_SYSTEM_CHANGE",
        "PROMOTION_LAUNCH",
        "SUPPLIER_DISRUPTION",
    }

    for event in data["operational_events"]:
        assert event["event_type"] in (
            allowed_event_types
        )


def test_operational_event_severities_are_valid():
    config = make_operational_event_config()

    master_data = build_master_data(config)

    generator = SyntheticOperationalEventGenerator(
        config=config,
        master_data=master_data,
    )

    data = generator.generate()

    allowed_severities = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }

    for event in data["operational_events"]:
        assert event["severity"] in allowed_severities


def test_operational_event_timestamps_are_valid():
    config = make_operational_event_config()

    master_data = build_master_data(config)

    generator = SyntheticOperationalEventGenerator(
        config=config,
        master_data=master_data,
    )

    data = generator.generate()

    for event in data["operational_events"]:
        assert isinstance(
            event["started_at"],
            datetime,
        )

        assert isinstance(
            event["ended_at"],
            datetime,
        )

        assert (
            event["ended_at"]
            > event["started_at"]
        )


def test_operational_event_metadata_is_json_compatible():
    config = make_operational_event_config()

    master_data = build_master_data(config)

    generator = SyntheticOperationalEventGenerator(
        config=config,
        master_data=master_data,
    )

    data = generator.generate()

    for event in data["operational_events"]:
        metadata = event["metadata"]

        assert isinstance(metadata, dict)
        assert metadata["synthetic"] is True
        assert isinstance(
            metadata["event_sequence"],
            int,
        )


def test_operational_event_schema_columns_match():
    config = make_operational_event_config()

    master_data = build_master_data(config)

    generator = SyntheticOperationalEventGenerator(
        config=config,
        master_data=master_data,
    )

    data = generator.generate()

    assert data["operational_events"]

    assert set(
        data["operational_events"][0]
    ) == {
        "operational_event_id",
        "organization_id",
        "event_type",
        "severity",
        "location_id",
        "description",
        "started_at",
        "ended_at",
        "metadata",
    }


def test_location_specific_events_have_location_context():
    config = make_operational_event_config()

    master_data = build_master_data(config)

    generator = SyntheticOperationalEventGenerator(
        config=config,
        master_data=master_data,
    )

    data = generator.generate()

    location_specific_types = {
        "WAREHOUSE_OUTAGE",
        "INVENTORY_SYSTEM_FAILURE",
        "DELIVERY_CAPACITY_REDUCTION",
        "SUPPLIER_DISRUPTION",
    }

    for event in data["operational_events"]:
        if (
            event["event_type"]
            in location_specific_types
        ):
            assert event["location_id"] is not None
            assert (
                "city"
                in event["metadata"]
            )
            assert (
                "state"
                in event["metadata"]
            )