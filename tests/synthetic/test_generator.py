import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = PROJECT_ROOT / "data-platform" / "synthetic"

if str(SYNTHETIC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTHETIC_DIR))

from config import GeneratorConfig
from generator import SyntheticCommerceGenerator


def make_small_config() -> GeneratorConfig:
    return GeneratorConfig(
        seed=42,
        organizations=2,
        brands_per_organization=3,
        categories_per_organization=4,
        products_per_organization=5,
        skus_per_product=2,
        customers_per_organization=10,
        suppliers_per_organization=2,
        customer_segments_per_organization=5,
    )


def test_default_configuration():
    config = GeneratorConfig()

    assert config.seed == 42
    assert config.organizations == 3
    assert config.products_per_organization == 100
    assert config.customers_per_organization == 1_000


def test_generator_is_deterministic():
    config = make_small_config()

    generator_a = SyntheticCommerceGenerator(config)
    generator_b = SyntheticCommerceGenerator(config)

    assert generator_a.generate() == generator_b.generate()


def test_expected_entity_counts():
    config = make_small_config()

    data = SyntheticCommerceGenerator(config).generate()

    assert len(data["organizations"]) == 2
    assert len(data["customer_segments"]) == 10
    assert len(data["brands"]) == 6
    assert len(data["categories"]) == 8
    assert len(data["suppliers"]) == 4
    assert len(data["customers"]) == 20
    assert len(data["products"]) == 10
    assert len(data["skus"]) == 20


def test_customer_relationships_are_valid():
    data = SyntheticCommerceGenerator(
        make_small_config()
    ).generate()

    organization_ids = {
        row["organization_id"]
        for row in data["organizations"]
    }

    segment_ids = {
        row["customer_segment_id"]
        for row in data["customer_segments"]
    }

    for customer in data["customers"]:
        assert customer["organization_id"] in organization_ids
        assert customer["customer_segment_id"] in segment_ids


def test_product_relationships_are_valid():
    data = SyntheticCommerceGenerator(
        make_small_config()
    ).generate()

    organization_ids = {
        row["organization_id"]
        for row in data["organizations"]
    }

    brand_ids = {
        row["brand_id"]
        for row in data["brands"]
    }

    category_ids = {
        row["category_id"]
        for row in data["categories"]
    }

    for product in data["products"]:
        assert product["organization_id"] in organization_ids
        assert product["brand_id"] in brand_ids
        assert product["category_id"] in category_ids


def test_sku_relationships_are_valid():
    data = SyntheticCommerceGenerator(
        make_small_config()
    ).generate()

    product_ids = {
        row["product_id"]
        for row in data["products"]
    }

    organization_ids = {
        row["organization_id"]
        for row in data["organizations"]
    }

    for sku in data["skus"]:
        assert sku["product_id"] in product_ids
        assert sku["organization_id"] in organization_ids


def test_schema_aligned_column_names():
    data = SyntheticCommerceGenerator(
        make_small_config()
    ).generate()

    assert set(data["organizations"][0]) == {
        "organization_id",
        "name",
        "industry",
        "country_code",
    }

    assert set(data["customers"][0]) == {
        "customer_id",
        "organization_id",
        "customer_segment_id",
        "external_customer_id",
        "first_name",
        "last_name",
        "email",
        "country_code",
        "city",
        "acquisition_channel",
    }

    assert set(data["products"][0]) == {
        "product_id",
        "organization_id",
        "brand_id",
        "category_id",
        "product_name",
        "description",
    }

    assert set(data["skus"][0]) == {
        "sku_id",
        "organization_id",
        "product_id",
        "sku_code",
        "sku_name",
        "unit_cost",
        "list_price",
        "weight_grams",
        "active",
    }


def test_summary_matches_generated_data():
    config = make_small_config()

    generator = SyntheticCommerceGenerator(config)
    data = generator.generate()
    summary = generator.summary()

    assert summary["organizations"] == len(data["organizations"])
    assert summary["customer_segments"] == len(data["customer_segments"])
    assert summary["brands"] == len(data["brands"])
    assert summary["categories"] == len(data["categories"])
    assert summary["suppliers"] == len(data["suppliers"])
    assert summary["customers"] == len(data["customers"])
    assert summary["products"] == len(data["products"])
    assert summary["skus"] == len(data["skus"])