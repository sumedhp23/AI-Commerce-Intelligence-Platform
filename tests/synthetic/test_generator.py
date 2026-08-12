import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = PROJECT_ROOT / "data-platform" / "synthetic"

if str(SYNTHETIC_DIR) not in sys.path:
    sys.path.insert(0, str(SYNTHETIC_DIR))

from config import GeneratorConfig
from generator import SyntheticCommerceGenerator


def test_default_configuration():
    config = GeneratorConfig()

    assert config.seed == 42
    assert config.organizations == 3
    assert config.products_per_organization == 100
    assert config.customers_per_organization == 1_000


def test_generator_is_deterministic():
    config = GeneratorConfig(
        seed=123,
        organizations=1,
        brands_per_organization=2,
        categories_per_organization=3,
        products_per_organization=5,
        skus_per_product=2,
        customers_per_organization=10,
        suppliers_per_organization=2,
    )

    generator_a = SyntheticCommerceGenerator(config)
    generator_b = SyntheticCommerceGenerator(config)

    assert generator_a.generate() == generator_b.generate()


def test_expected_entity_counts():
    config = GeneratorConfig(
        seed=42,
        organizations=2,
        brands_per_organization=3,
        categories_per_organization=4,
        products_per_organization=5,
        skus_per_product=2,
        customers_per_organization=10,
        suppliers_per_organization=2,
    )

    generator = SyntheticCommerceGenerator(config)
    data = generator.generate()

    assert len(data["organizations"]) == 2
    assert len(data["brands"]) == 6
    assert len(data["categories"]) == 8
    assert len(data["suppliers"]) == 4
    assert len(data["customers"]) == 20
    assert len(data["products"]) == 10
    assert len(data["skus"]) == 20


def test_product_relationships_are_valid():
    config = GeneratorConfig(
        seed=42,
        organizations=1,
        brands_per_organization=2,
        categories_per_organization=2,
        products_per_organization=4,
        skus_per_product=2,
        customers_per_organization=5,
        suppliers_per_organization=2,
    )

    generator = SyntheticCommerceGenerator(config)
    data = generator.generate()

    organization_ids = {
        organization["id"]
        for organization in data["organizations"]
    }

    brand_ids = {
        brand["id"]
        for brand in data["brands"]
    }

    category_ids = {
        category["id"]
        for category in data["categories"]
    }

    for product in data["products"]:
        assert product["organization_id"] in organization_ids
        assert product["brand_id"] in brand_ids
        assert product["category_id"] in category_ids


def test_sku_relationships_are_valid():
    config = GeneratorConfig(
        seed=42,
        organizations=1,
        brands_per_organization=2,
        categories_per_organization=2,
        products_per_organization=4,
        skus_per_product=3,
        customers_per_organization=5,
        suppliers_per_organization=2,
    )

    generator = SyntheticCommerceGenerator(config)
    data = generator.generate()

    product_ids = {
        product["id"]
        for product in data["products"]
    }

    for sku in data["skus"]:
        assert sku["product_id"] in product_ids


def test_summary_matches_generated_data():
    config = GeneratorConfig(
        seed=42,
        organizations=2,
        brands_per_organization=2,
        categories_per_organization=3,
        products_per_organization=4,
        skus_per_product=2,
        customers_per_organization=5,
        suppliers_per_organization=2,
    )

    generator = SyntheticCommerceGenerator(config)

    data = generator.generate()
    summary = generator.summary()

    assert summary["organizations"] == len(data["organizations"])
    assert summary["brands"] == len(data["brands"])
    assert summary["categories"] == len(data["categories"])
    assert summary["suppliers"] == len(data["suppliers"])
    assert summary["customers"] == len(data["customers"])
    assert summary["products"] == len(data["products"])
    assert summary["skus"] == len(data["skus"])