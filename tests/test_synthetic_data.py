import csv
from pathlib import Path

from synthetic_data.generator import Config, generate


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_smoke_generation(tmp_path):
    generate(Config(seed=7, days=3, customers=25, products=10, orders_per_day=20), tmp_path)

    required = {
        "organizations.csv", "regions.csv", "locations.csv", "customers.csv",
        "products.csv", "skus.csv", "orders.csv", "order_items.csv",
        "payments.csv", "inventory_snapshots.csv", "sessions.csv",
        "marketing_events.csv", "deliveries.csv", "ground_truth_scenarios.csv",
    }
    assert required.issubset({p.name for p in tmp_path.iterdir()})
    assert read_csv(tmp_path / "orders.csv")
    assert read_csv(tmp_path / "order_items.csv")


def test_seed_is_reproducible(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    config = Config(seed=123, days=2, customers=20, products=8, orders_per_day=10)
    generate(config, left)
    generate(config, right)

    for name in ["customers.csv", "products.csv", "orders.csv", "inventory_snapshots.csv"]:
        assert (left / name).read_bytes() == (right / name).read_bytes()


def test_foreign_keys_exist_in_generated_orders(tmp_path):
    generate(Config(seed=9, days=2, customers=30, products=12, orders_per_day=25), tmp_path)
    customers = {int(r["customer_id"]) for r in read_csv(tmp_path / "customers.csv")}
    locations = {int(r["location_id"]) for r in read_csv(tmp_path / "locations.csv")}
    skus = {int(r["sku_id"]) for r in read_csv(tmp_path / "skus.csv")}
    orders = read_csv(tmp_path / "orders.csv")
    items = read_csv(tmp_path / "order_items.csv")

    assert all(int(r["customer_id"]) in customers for r in orders)
    assert all(int(r["location_id"]) in locations for r in orders)
    assert all(int(r["sku_id"]) in skus for r in items)
    assert all(int(r["order_id"]) in {int(o["order_id"]) for o in orders} for r in items)
