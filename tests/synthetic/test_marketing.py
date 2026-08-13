import sys
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = PROJECT_ROOT / "data-platform" / "synthetic"

if str(SYNTHETIC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTHETIC_DIR))

from config import GeneratorConfig
from generator import SyntheticCommerceGenerator
from marketing import SyntheticMarketingGenerator


def make_marketing_config() -> GeneratorConfig:
    return GeneratorConfig(
        seed=42,
        organizations=2,
        campaigns_per_organization=5,
        promotions_per_organization=5,
        coupons_per_promotion=3,
    )


def build_marketing_data():
    config = make_marketing_config()

    master_data = SyntheticCommerceGenerator(
        config
    ).generate()

    marketing_data = SyntheticMarketingGenerator(
        config=config,
        master_data=master_data,
    ).generate()

    return (
        config,
        master_data,
        marketing_data,
    )


def test_marketing_generation_is_deterministic():
    first = build_marketing_data()[-1]
    second = build_marketing_data()[-1]

    assert first == second


def test_expected_entity_counts():
    (
        config,
        _,
        marketing_data,
    ) = build_marketing_data()

    assert len(marketing_data["campaigns"]) == (
        config.total_campaigns
    )

    assert len(marketing_data["promotions"]) == (
        config.total_promotions
    )

    assert len(marketing_data["coupons"]) == (
        config.total_coupons
    )


def test_campaign_relationships_and_uniqueness():
    (
        _,
        master_data,
        marketing_data,
    ) = build_marketing_data()

    organization_ids = {
        organization["organization_id"]
        for organization in master_data["organizations"]
    }

    campaigns = marketing_data["campaigns"]

    assert all(
        campaign["organization_id"]
        in organization_ids
        for campaign in campaigns
    )

    assert len({
        campaign["campaign_id"]
        for campaign in campaigns
    }) == len(campaigns)

    assert len({
        (
            campaign["organization_id"],
            campaign["name"],
        )
        for campaign in campaigns
    }) == len(campaigns)


def test_campaign_values_and_timestamps_are_valid():
    marketing_data = build_marketing_data()[-1]

    valid_channels = {
        "EMAIL",
        "SOCIAL",
        "SEARCH",
        "PUSH",
        "SMS",
    }

    for campaign in marketing_data["campaigns"]:
        assert campaign["channel"] in valid_channels
        assert campaign["start_at"] < campaign["end_at"]
        assert campaign["budget_amount"] > Decimal("0")


def test_promotion_relationships_and_uniqueness():
    (
        _,
        master_data,
        marketing_data,
    ) = build_marketing_data()

    organization_ids = {
        organization["organization_id"]
        for organization in master_data["organizations"]
    }

    promotions = marketing_data["promotions"]

    assert all(
        promotion["organization_id"]
        in organization_ids
        for promotion in promotions
    )

    assert len({
        promotion["promotion_id"]
        for promotion in promotions
    }) == len(promotions)

    assert len({
        (
            promotion["organization_id"],
            promotion["name"],
        )
        for promotion in promotions
    }) == len(promotions)


def test_promotion_discount_contract():
    marketing_data = build_marketing_data()[-1]

    for promotion in marketing_data["promotions"]:
        assert promotion["start_at"] < promotion["end_at"]

        if promotion["promotion_type"] == "PERCENTAGE":
            assert (
                promotion["discount_percentage"]
                is not None
            )
            assert (
                promotion["discount_percentage"]
                > Decimal("0")
            )
            assert (
                promotion["discount_amount"]
                is None
            )

        elif promotion["promotion_type"] == "FIXED_AMOUNT":
            assert (
                promotion["discount_amount"]
                is not None
            )
            assert (
                promotion["discount_amount"]
                > Decimal("0")
            )
            assert (
                promotion["discount_percentage"]
                is None
            )

        else:
            raise AssertionError(
                "Unexpected promotion type"
            )


def test_coupon_relationships_and_uniqueness():
    marketing_data = build_marketing_data()[-1]

    promotions_by_id = {
        promotion["promotion_id"]: promotion
        for promotion in marketing_data["promotions"]
    }

    coupons = marketing_data["coupons"]

    assert len({
        coupon["coupon_id"]
        for coupon in coupons
    }) == len(coupons)

    assert len({
        (
            coupon["organization_id"],
            coupon["coupon_code"],
        )
        for coupon in coupons
    }) == len(coupons)

    for coupon in coupons:
        promotion = promotions_by_id[
            coupon["promotion_id"]
        ]

        assert (
            coupon["organization_id"]
            == promotion["organization_id"]
        )


def test_coupon_usage_limits_are_valid():
    marketing_data = build_marketing_data()[-1]

    for coupon in marketing_data["coupons"]:
        assert coupon["usage_limit"] is None or (
            coupon["usage_limit"] > 0
        )


def test_marketing_schema_column_names():
    marketing_data = build_marketing_data()[-1]

    assert set(marketing_data["campaigns"][0]) == {
        "campaign_id",
        "organization_id",
        "name",
        "channel",
        "start_at",
        "end_at",
        "budget_amount",
    }

    assert set(marketing_data["promotions"][0]) == {
        "promotion_id",
        "organization_id",
        "name",
        "promotion_type",
        "discount_percentage",
        "discount_amount",
        "start_at",
        "end_at",
    }

    assert set(marketing_data["coupons"][0]) == {
        "coupon_id",
        "organization_id",
        "promotion_id",
        "coupon_code",
        "usage_limit",
    }


def test_summary_matches_generated_data():
    (
        _,
        _,
        marketing_data,
    ) = build_marketing_data()

    generator = SyntheticMarketingGenerator(
        config=make_marketing_config(),
        master_data=SyntheticCommerceGenerator(
            make_marketing_config()
        ).generate(),
    )

    summary = generator.summary()

    assert summary["campaigns"] == len(
        marketing_data["campaigns"]
    )

    assert summary["promotions"] == len(
        marketing_data["promotions"]
    )

    assert summary["coupons"] == len(
        marketing_data["coupons"]
    )