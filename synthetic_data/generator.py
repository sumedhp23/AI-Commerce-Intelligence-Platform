"""Reproducible synthetic commerce data generator for Stage 1.

The generator deliberately creates correlated commerce behavior instead of independent
random rows. It supports a deterministic seed and a small smoke-test scale as well as
larger local datasets.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(frozen=True)
class Config:
    seed: int = 20260812
    days: int = 180
    customers: int = 2_000
    products: int = 80
    orders_per_day: int = 1_000
    inventory_days: int = 180


CITIES = [
    ("India", "Karnataka", "Bengaluru"),
    ("India", "Maharashtra", "Mumbai"),
    ("India", "Telangana", "Hyderabad"),
    ("India", "Tamil Nadu", "Chennai"),
    ("India", "Delhi", "New Delhi"),
]
LOCATION_TYPES = ["warehouse", "dark_store", "restaurant", "store"]
CATEGORIES = ["Grocery", "Beauty", "Electronics", "Home", "Fashion", "Personal Care", "Snacks", "Beverages"]
BRANDS = ["Aster", "Nova", "UrbanLeaf", "Vertex", "Mira", "Pulse", "Nexa", "Orbit"]
SEGMENTS = ["high_value", "regular", "price_sensitive", "new", "at_risk"]
CHANNELS = ["web", "app", "marketplace"]
PAYMENT_METHODS = ["card", "upi", "wallet", "cash"]


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def weighted_choice(rng: random.Random, values: list, weights: list[float]):
    return rng.choices(values, weights=weights, k=1)[0]


def generate(config: Config, output: Path) -> None:
    rng = random.Random(config.seed)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    org_id = 1

    regions = []
    for i, (country, state, city) in enumerate(CITIES, 1):
        regions.append({"region_id": i, "organization_id": org_id, "country": country, "state": state, "city": city})

    locations = []
    for i, region in enumerate(regions, 1):
        for j in range(2):
            location_type = "restaurant" if region["city"] in {"Bengaluru", "Mumbai", "Hyderabad"} and j == 1 else "dark_store"
            locations.append({
                "location_id": i * 10 + j,
                "organization_id": org_id,
                "region_id": region["region_id"],
                "location_type": location_type,
                "name": f"{region['city']} {location_type.replace('_', ' ').title()} {j + 1}",
                "active": True,
            })

    segments = [{"segment_id": i, "organization_id": org_id, "name": name, "description": name.replace("_", " ").title()} for i, name in enumerate(SEGMENTS, 1)]
    customers = []
    for customer_id in range(1, config.customers + 1):
        segment = weighted_choice(rng, segments, [10, 45, 20, 15, 10])
        customers.append({
            "customer_id": customer_id,
            "organization_id": org_id,
            "segment_id": segment["segment_id"],
            "home_region_id": rng.randint(1, len(regions)),
            "created_at": iso(start - timedelta(days=rng.randint(0, 365))),
        })

    categories = [{"category_id": i, "organization_id": org_id, "name": n} for i, n in enumerate(CATEGORIES, 1)]
    brands = [{"brand_id": i, "organization_id": org_id, "name": n} for i, n in enumerate(BRANDS, 1)]
    products = []
    skus = []
    for product_id in range(1, config.products + 1):
        category = rng.choice(categories)
        brand = rng.choice(brands)
        products.append({"product_id": product_id, "organization_id": org_id, "category_id": category["category_id"], "brand_id": brand["brand_id"], "name": f"{brand['name']} {category['name']} {product_id}"})
        base_cost = rng.uniform(40, 1800)
        margin = rng.uniform(1.20, 1.85)
        skus.append({"sku_id": product_id, "organization_id": org_id, "product_id": product_id, "sku_code": f"SKU-{product_id:05d}", "unit_cost": round(base_cost, 2), "list_price": round(base_cost * margin, 2)})

    campaigns = []
    for campaign_id in range(1, 13):
        campaigns.append({
            "campaign_id": campaign_id,
            "organization_id": org_id,
            "name": f"Campaign {campaign_id}",
            "channel": rng.choice(["search", "social", "email", "affiliate"]),
            "start_at": iso(start + timedelta(days=(campaign_id - 1) * 14)),
            "end_at": iso(start + timedelta(days=campaign_id * 14 - 1)),
            "spend": round(rng.uniform(50000, 250000), 2),
        })

    promotions = []
    for promotion_id in range(1, 7):
        promotions.append({
            "promotion_id": promotion_id,
            "organization_id": org_id,
            "name": f"Promo {promotion_id}",
            "discount_type": "percent",
            "discount_value": rng.choice([5, 10, 15, 20]),
            "start_at": iso(start + timedelta(days=(promotion_id - 1) * 30)),
            "end_at": iso(start + timedelta(days=promotion_id * 30 - 1)),
        })

    # Operational ground truth is intentionally explicit so later AI evaluation can
    # distinguish a correct investigation from a plausible but wrong explanation.
    ground_truth = [{
        "scenario_id": "SCN-001",
        "start_at": iso(start + timedelta(days=120)),
        "end_at": iso(start + timedelta(days=145)),
        "region": "Bengaluru",
        "type": "inventory_constraint",
        "expected_effect": "Bengaluru order fulfillment falls because selected high-demand SKUs become unavailable.",
    }]

    orders, order_items, payments, returns, refunds, deliveries = [], [], [], [], [], []
    sessions, marketing_events = [], []
    operational_events = []
    inventory = []
    order_id = payment_id = item_id = delivery_id = session_id = event_id = 1

    sku_stock = {sku["sku_id"]: rng.randint(80, 500) for sku in skus}
    for day_offset in range(config.days):
        day = start + timedelta(days=day_offset)
        seasonal = 1.0 + 0.12 * math.sin(2 * math.pi * day_offset / 30)
        weekend = 1.15 if day.weekday() >= 5 else 0.95
        for _ in range(config.orders_per_day):
            region_id = weighted_choice(rng, list(range(1, len(regions) + 1)), [28, 24, 18, 16, 14])
            customer = rng.choice(customers)
            location = next(l for l in locations if l["region_id"] == region_id)
            # Known anomaly: selected Bengaluru SKUs lose availability during the scenario.
            anomaly = region_id == 1 and 120 <= day_offset <= 145
            sku = rng.choice(skus)
            if anomaly and sku["sku_id"] <= max(3, config.products // 10):
                stock_multiplier = 0.12
            else:
                stock_multiplier = 1.0
            if rng.random() > min(0.98, 0.0014 * seasonal * weekend * stock_multiplier):
                continue

            ordered_at = day + timedelta(minutes=rng.randint(0, 1439))
            quantity = weighted_choice(rng, [1, 2, 3], [0.72, 0.23, 0.05])
            promo = rng.choice(promotions) if rng.random() < 0.22 else None
            discount = (sku["list_price"] * quantity * promo["discount_value"] / 100) if promo else 0
            subtotal = sku["list_price"] * quantity
            cancellation_probability = 0.035 + (0.07 if anomaly else 0) + (0.02 if location["location_type"] == "restaurant" else 0)
            status = "cancelled" if rng.random() < cancellation_probability else "completed"
            net_revenue = max(0, subtotal - discount)
            order = {
                "order_id": order_id, "organization_id": org_id, "customer_id": customer["customer_id"],
                "location_id": location["location_id"], "ordered_at": iso(ordered_at), "status": status,
                "channel": weighted_choice(rng, CHANNELS, [25, 55, 20]), "subtotal": round(subtotal, 2),
                "discount_amount": round(discount, 2), "delivery_fee": round(rng.uniform(0, 120), 2),
                "net_revenue": round(net_revenue, 2),
            }
            orders.append(order)
            order_items.append({"order_item_id": item_id, "order_id": order_id, "sku_id": sku["sku_id"], "quantity": quantity, "unit_price": sku["list_price"], "discount_amount": round(discount, 2)})
            payments.append({"payment_id": payment_id, "order_id": order_id, "paid_at": iso(ordered_at) if status == "completed" else "", "status": "paid" if status == "completed" else "failed", "method": rng.choice(PAYMENT_METHODS), "amount": round(net_revenue, 2)})
            if status == "completed" and rng.random() < 0.045:
                returned_at = ordered_at + timedelta(days=rng.randint(1, 14))
                returns.append({"return_id": len(returns) + 1, "order_id": order_id, "requested_at": iso(returned_at), "reason": rng.choice(["quality", "changed_mind", "wrong_item", "late_delivery"])})
                refunds.append({"refund_id": len(refunds) + 1, "order_id": order_id, "refunded_at": iso(returned_at + timedelta(days=1)), "amount": round(net_revenue, 2)})
            if status == "completed":
                promised = ordered_at + timedelta(minutes=rng.randint(25, 90))
                delay = rng.randint(0, 55) + (30 if anomaly else 0)
                delivered = promised + timedelta(minutes=delay)
                deliveries.append({"delivery_id": delivery_id, "organization_id": org_id, "order_id": order_id, "driver_id": rng.randint(1, 50), "promised_at": iso(promised), "picked_up_at": iso(ordered_at + timedelta(minutes=rng.randint(10, 35))), "delivered_at": iso(delivered), "delivery_status": "delivered", "delivery_distance_km": round(rng.uniform(1, 18), 2)})
                delivery_id += 1
            order_id += 1; payment_id += 1; item_id += 1

        # Daily inventory snapshot. High-demand Bengaluru SKUs intentionally stock out.
        for location in locations:
            for sku in skus:
                demand_pressure = 1.0 + (0.8 if location["region_id"] == 1 and sku["sku_id"] <= max(3, config.products // 10) else 0)
                if location["region_id"] == 1 and 120 <= day_offset <= 145 and sku["sku_id"] <= max(3, config.products // 10):
                    on_hand = rng.randint(0, 8)
                    inbound = 0
                else:
                    base = sku_stock[sku["sku_id"]]
                    on_hand = max(0, int(base / demand_pressure + rng.randint(-25, 25)))
                    inbound = rng.randint(0, 150)
                reserved = min(on_hand, rng.randint(0, max(1, on_hand // 5)))
                inventory.append({"snapshot_id": len(inventory) + 1, "organization_id": org_id, "location_id": location["location_id"], "sku_id": sku["sku_id"], "snapshot_at": iso(day), "on_hand_quantity": on_hand, "reserved_quantity": reserved, "inbound_quantity": inbound})

        # Sessions and marketing events provide traffic/conversion context.
        for _ in range(max(1, config.orders_per_day // 3)):
            region_id = rng.randint(1, len(regions))
            converted = rng.random() < (0.055 * seasonal * weekend)
            sessions.append({"session_id": session_id, "organization_id": org_id, "customer_id": rng.choice(customers)["customer_id"] if rng.random() < 0.7 else "", "region_id": region_id, "started_at": iso(day + timedelta(minutes=rng.randint(0, 1439))), "device": weighted_choice(rng, ["mobile", "desktop", "tablet"], [70, 25, 5]), "converted": converted})
            event_type = "checkout" if converted else weighted_choice(rng, ["impression", "click", "add_to_cart"], [0.45, 0.35, 0.20])
            marketing_events.append({"event_id": event_id, "session_id": session_id, "campaign_id": rng.randint(1, len(campaigns)), "event_at": sessions[-1]["started_at"], "event_type": event_type})
            session_id += 1; event_id += 1

    # Operational events expose the scenario to investigation tooling without directly
    # stating the root cause in user-facing data.
    operational_events.append({"event_id": 1, "organization_id": org_id, "location_id": 10, "event_at": iso(start + timedelta(days=120)), "event_type": "supplier_delay", "severity": "warning", "description": "Inbound replenishment shipment delayed."})

    write_csv(output / "organizations.csv", [{"organization_id": org_id, "name": "Axiom Commerce Synthetic", "industry": "ecommerce", "created_at": iso(start)}], ["organization_id", "name", "industry", "created_at"])
    for name, rows in [
        ("regions", regions), ("locations", locations), ("customer_segments", segments), ("customers", customers),
        ("categories", categories), ("brands", brands), ("products", products), ("skus", skus), ("campaigns", campaigns),
        ("promotions", promotions), ("orders", orders), ("order_items", order_items), ("payments", payments),
        ("returns", returns), ("refunds", refunds), ("inventory_snapshots", inventory), ("sessions", sessions),
        ("marketing_events", marketing_events), ("deliveries", deliveries), ("operational_events", operational_events),
        ("ground_truth_scenarios", ground_truth),
    ]:
        if rows:
            write_csv(output / f"{name}.csv", rows, list(rows[0].keys()))


def parse_args() -> Config:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/generated"))
    parser.add_argument("--seed", type=int, default=Config.seed)
    parser.add_argument("--days", type=int, default=Config.days)
    parser.add_argument("--customers", type=int, default=Config.customers)
    parser.add_argument("--products", type=int, default=Config.products)
    parser.add_argument("--orders-per-day", type=int, default=Config.orders_per_day)
    args = parser.parse_args()
    config = Config(args.seed, args.days, args.customers, args.products, args.orders_per_day, args.days)
    generate(config, args.output)
    return config


if __name__ == "__main__":
    parse_args()
