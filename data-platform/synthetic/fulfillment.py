from __future__ import annotations

import random
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from config import GeneratorConfig
from generator import SyntheticCommerceGenerator


class SyntheticFulfillmentGenerator:
    """
    Deterministic generator for fulfillment, inventory, and procurement data.

    Domain flow:

        SKU
         ↓
        Fulfillment Location
         ├── Inventory Snapshot
         └── Inventory Movement

        Supplier
         ↓
        Purchase Order
         ↓
        Purchase Order Item
    """

    def __init__(
        self,
        config: GeneratorConfig | None = None,
        master_data: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.config = config or GeneratorConfig()
        self.random = random.Random(self.config.seed + 2)

        if master_data is None:
            master_data = SyntheticCommerceGenerator(
                self.config
            ).generate()

        self.master_data = master_data

    def _uuid(self) -> str:
        return str(uuid.UUID(int=self.random.getrandbits(128)))

    def generate_fulfillment_locations(
        self,
    ) -> list[dict[str, Any]]:
        locations = []

        location_types = [
            "WAREHOUSE",
            "DARK_STORE",
            "RETAIL_STORE",
            "DISTRIBUTION_CENTER",
        ]

        cities = [
            ("Bengaluru", "KA"),
            ("Mumbai", "MH"),
            ("Delhi", "DL"),
            ("Hyderabad", "TS"),
        ]

        for organization in self.master_data["organizations"]:
            organization_id = organization["organization_id"]

            for index in range(
                1,
                self.config.fulfillment_locations_per_organization + 1,
            ):
                city, state = cities[
                    (index - 1) % len(cities)
                ]

                locations.append(
                    {
                        "fulfillment_location_id": self._uuid(),
                        "organization_id": organization_id,
                        "name": f"Fulfillment Location {index}",
                        "location_type": location_types[
                            (index - 1) % len(location_types)
                        ],
                        "city": city,
                        "state": state,
                        "country_code": "IN",
                        "latitude": Decimal(
                            str(12.9716 + index * 0.01)
                        ),
                        "longitude": Decimal(
                            str(77.5946 + index * 0.01)
                        ),
                        "active": True,
                    }
                )

        return locations

    def generate_inventory_snapshots(
        self,
        fulfillment_locations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        snapshots = []

        skus_by_organization: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for sku in self.master_data["skus"]:
            skus_by_organization.setdefault(
                sku["organization_id"],
                [],
            ).append(sku)

        base_date = date(2026, 1, 1)

        for location in fulfillment_locations:
            organization_id = location["organization_id"]
            organization_skus = skus_by_organization.get(
                organization_id,
                [],
            )

            for sku_index, sku in enumerate(organization_skus):
                for day_index in range(
                    self.config.inventory_snapshot_days
                ):
                    quantity_on_hand = 50 + (
                        (sku_index + day_index) % 151
                    )

                    quantity_reserved = (
                        (sku_index * 3 + day_index)
                        % min(quantity_on_hand + 1, 20)
                    )

                    quantity_available = (
                        quantity_on_hand
                        - quantity_reserved
                    )

                    reorder_point = 30 + (
                        sku_index % 21
                    )

                    safety_stock = 15 + (
                        sku_index % 11
                    )

                    snapshots.append(
                        {
                            "inventory_snapshot_id": self._uuid(),
                            "organization_id": organization_id,
                            "sku_id": sku["sku_id"],
                            "fulfillment_location_id": (
                                location[
                                    "fulfillment_location_id"
                                ]
                            ),
                            "snapshot_date": (
                                base_date
                                + timedelta(days=day_index)
                            ),
                            "quantity_on_hand": quantity_on_hand,
                            "quantity_reserved": quantity_reserved,
                            "quantity_available": (
                                quantity_available
                            ),
                            "reorder_point": reorder_point,
                            "safety_stock": safety_stock,
                        }
                    )

        return snapshots

    def generate_inventory_movements(
        self,
        fulfillment_locations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        movements = []

        movement_types = [
            ("PURCHASE", 1),
            ("SALE", -1),
            ("RETURN", 1),
            ("TRANSFER_IN", 1),
            ("TRANSFER_OUT", -1),
            ("ADJUSTMENT", 0),
            ("DAMAGE", -1),
            ("EXPIRY", -1),
        ]

        skus_by_organization: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for sku in self.master_data["skus"]:
            skus_by_organization.setdefault(
                sku["organization_id"],
                [],
            ).append(sku)

        movement_index = 0

        for location in fulfillment_locations:
            organization_id = location["organization_id"]
            organization_skus = skus_by_organization.get(
                organization_id,
                [],
            )

            for sku_index, sku in enumerate(organization_skus):
                for event_index in range(
                    self.config.inventory_movements_per_sku_location
                ):
                    movement_type, direction = movement_types[
                        event_index % len(movement_types)
                    ]

                    quantity = 1 + (
                        (sku_index + event_index) % 20
                    )

                    if direction == -1:
                        quantity = -quantity
                    elif direction == 0:
                        quantity = (
                            quantity
                            if event_index % 2 == 0
                            else -quantity
                        )

                    occurred_at = datetime(
                        2026,
                        1,
                        1,
                        8,
                        0,
                        tzinfo=timezone.utc,
                    ) + timedelta(
                        days=event_index,
                        minutes=movement_index,
                    )

                    reference_type = None
                    reference_id = None

                    if movement_type == "PURCHASE":
                        reference_type = "PURCHASE_ORDER"

                    movements.append(
                        {
                            "inventory_movement_id": self._uuid(),
                            "organization_id": organization_id,
                            "sku_id": sku["sku_id"],
                            "fulfillment_location_id": (
                                location[
                                    "fulfillment_location_id"
                                ]
                            ),
                            "movement_type": movement_type,
                            "quantity": quantity,
                            "occurred_at": occurred_at,
                            "reference_type": reference_type,
                            "reference_id": reference_id,
                        }
                    )

                    movement_index += 1

        return movements

    def generate_purchase_orders(
        self,
        fulfillment_locations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        purchase_orders = []

        suppliers_by_organization: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for supplier in self.master_data["suppliers"]:
            suppliers_by_organization.setdefault(
                supplier["organization_id"],
                [],
            ).append(supplier)

        locations_by_organization: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for location in fulfillment_locations:
            locations_by_organization.setdefault(
                location["organization_id"],
                [],
            ).append(location)

        order_index = 1

        for organization in self.master_data["organizations"]:
            organization_id = organization["organization_id"]

            suppliers = suppliers_by_organization[
                organization_id
            ]

            locations = locations_by_organization[
                organization_id
            ]

            for index in range(
                self.config.purchase_orders_per_organization
            ):
                ordered_at = datetime(
                    2026,
                    1,
                    1,
                    9,
                    0,
                    tzinfo=timezone.utc,
                ) + timedelta(days=index)

                purchase_orders.append(
                    {
                        "purchase_order_id": self._uuid(),
                        "organization_id": organization_id,
                        "supplier_id": suppliers[
                            index % len(suppliers)
                        ]["supplier_id"],
                        "fulfillment_location_id": locations[
                            index % len(locations)
                        ]["fulfillment_location_id"],
                        "purchase_order_number": (
                            f"PO-{order_index:08d}"
                        ),
                        "status": (
                            "RECEIVED"
                            if index % 3 == 0
                            else "ORDERED"
                        ),
                        "ordered_at": ordered_at,
                        "expected_at": ordered_at
                        + timedelta(days=7),
                    }
                )

                order_index += 1

        return purchase_orders

    def generate_purchase_order_items(
        self,
        purchase_orders: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        items = []

        skus_by_organization: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for sku in self.master_data["skus"]:
            skus_by_organization.setdefault(
                sku["organization_id"],
                [],
            ).append(sku)

        for order_index, order in enumerate(
            purchase_orders
        ):
            organization_skus = skus_by_organization[
                order["organization_id"]
            ]

            for item_index in range(
                self.config.purchase_order_items_per_order
            ):
                sku = organization_skus[
                    (order_index + item_index)
                    % len(organization_skus)
                ]

                quantity_ordered = 10 + (
                    (order_index + item_index) % 41
                )

                unit_cost = Decimal(
                    str(sku["unit_cost"])
                )

                items.append(
                    {
                        "purchase_order_item_id": self._uuid(),
                        "organization_id": (
                            order["organization_id"]
                        ),
                        "purchase_order_id": (
                            order["purchase_order_id"]
                        ),
                        "sku_id": sku["sku_id"],
                        "quantity_ordered": (
                            quantity_ordered
                        ),
                        "unit_cost": unit_cost,
                    }
                )

        return items

    def generate(
        self,
    ) -> dict[str, list[dict[str, Any]]]:
        fulfillment_locations = (
            self.generate_fulfillment_locations()
        )

        inventory_snapshots = (
            self.generate_inventory_snapshots(
                fulfillment_locations
            )
        )

        inventory_movements = (
            self.generate_inventory_movements(
                fulfillment_locations
            )
        )

        purchase_orders = self.generate_purchase_orders(
            fulfillment_locations
        )

        purchase_order_items = (
            self.generate_purchase_order_items(
                purchase_orders
            )
        )

        return {
            "fulfillment_locations": fulfillment_locations,
            "inventory_snapshots": inventory_snapshots,
            "inventory_movements": inventory_movements,
            "purchase_orders": purchase_orders,
            "purchase_order_items": purchase_order_items,
        }

    def summary(self) -> dict[str, int]:
        return {
            "fulfillment_locations": (
                self.config.total_fulfillment_locations
            ),
            "inventory_snapshot_days": (
                self.config.inventory_snapshot_days
            ),
            "purchase_orders": (
                self.config.total_purchase_orders
            ),
        }