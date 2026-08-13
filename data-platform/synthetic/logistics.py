from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from config import GeneratorConfig
from generator import SyntheticCommerceGenerator


class SyntheticLogisticsGenerator:
    """
    Deterministic generator for logistics and delivery data.

    Domain flows:

        Customer Order
             ↓
          Delivery
             ↓
           Driver

        Purchase Order
             ↓
          Shipment
    """

    def __init__(
        self,
        config: GeneratorConfig | None = None,
        master_data: dict[str, list[dict[str, Any]]] | None = None,
        transaction_data: dict[str, list[dict[str, Any]]] | None = None,
        fulfillment_data: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.config = config or GeneratorConfig()
        self.random = random.Random(self.config.seed + 3)

        if master_data is None:
            master_data = SyntheticCommerceGenerator(
                self.config
            ).generate()

        self.master_data = master_data
        self.transaction_data = transaction_data
        self.fulfillment_data = fulfillment_data

    def _uuid(self) -> str:
        return str(
            uuid.UUID(
                int=self.random.getrandbits(128)
            )
        )

    def generate_drivers(self) -> list[dict[str, Any]]:
        drivers = []

        cities = [
            "Bengaluru",
            "Mumbai",
            "Delhi",
            "Hyderabad",
        ]

        statuses = [
            "ACTIVE",
            "ACTIVE",
            "ACTIVE",
            "INACTIVE",
            "SUSPENDED",
        ]

        for organization in self.master_data["organizations"]:
            organization_id = organization["organization_id"]

            for index in range(
                1,
                self.config.drivers_per_organization + 1,
            ):
                drivers.append(
                    {
                        "driver_id": self._uuid(),
                        "organization_id": organization_id,
                        "external_driver_id": (
                            f"DRV-{index:06d}"
                        ),
                        "city": cities[
                            (index - 1) % len(cities)
                        ],
                        "status": statuses[
                            (index - 1) % len(statuses)
                        ],
                    }
                )

        return drivers

    def generate_deliveries(
        self,
        drivers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if self.transaction_data is None:
            raise ValueError(
                "Cannot generate deliveries without "
                "transaction_data."
            )

        orders = self.transaction_data.get(
            "customer_orders",
            [],
        )

        if not orders:
            return []

        drivers_by_organization: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for driver in drivers:
            drivers_by_organization.setdefault(
                driver["organization_id"],
                [],
            ).append(driver)

        deliveries = []

        for index, order in enumerate(orders):
            organization_id = order["organization_id"]

            organization_drivers = (
                drivers_by_organization.get(
                    organization_id,
                    [],
                )
            )

            if not organization_drivers:
                raise ValueError(
                    "No drivers available for "
                    "order organization."
                )

            driver = organization_drivers[
                index % len(organization_drivers)
            ]

            ordered_at = order["ordered_at"]

            promised_at = ordered_at + timedelta(
                hours=24 + (index % 24)
            )

            lifecycle = index % 10

            if lifecycle <= 5:
                delivery_status = "DELIVERED"
                dispatched_at = promised_at - timedelta(
                    hours=4 + (index % 4)
                )
                delivered_at = dispatched_at + timedelta(
                    hours=6 + (index % 8)
                )

            elif lifecycle == 6:
                delivery_status = "IN_TRANSIT"
                dispatched_at = promised_at - timedelta(
                    hours=3
                )
                delivered_at = None

            elif lifecycle == 7:
                delivery_status = "ASSIGNED"
                dispatched_at = None
                delivered_at = None

            elif lifecycle == 8:
                delivery_status = "FAILED"
                dispatched_at = promised_at - timedelta(
                    hours=2
                )
                delivered_at = None

            else:
                delivery_status = "CANCELLED"
                dispatched_at = None
                delivered_at = None

            delivery_distance_km = Decimal(
                str(
                    2.5
                    + ((index * 7) % 275) / 10
                )
            ).quantize(
                Decimal("0.1")
            )

            deliveries.append(
                {
                    "delivery_id": self._uuid(),
                    "organization_id": organization_id,
                    "order_id": order["order_id"],
                    "driver_id": driver["driver_id"],
                    "delivery_status": delivery_status,
                    "promised_at": promised_at,
                    "dispatched_at": dispatched_at,
                    "delivered_at": delivered_at,
                    "delivery_distance_km": (
                        delivery_distance_km
                    ),
                }
            )

        return deliveries

    def generate_shipments(self) -> list[dict[str, Any]]:
        if self.fulfillment_data is None:
            raise ValueError(
                "Cannot generate shipments without "
                "fulfillment_data."
            )

        purchase_orders = self.fulfillment_data.get(
            "purchase_orders",
            [],
        )

        shipments = []

        for index, purchase_order in enumerate(
            purchase_orders
        ):
            ordered_at = purchase_order["ordered_at"]
            status = purchase_order["status"]

            shipped_at = ordered_at + timedelta(
                days=2 + (index % 3)
            )

            if status == "RECEIVED":
                shipment_status = "RECEIVED"
                received_at = shipped_at + timedelta(
                    days=2 + (index % 4)
                )
            else:
                shipment_status = (
                    "IN_TRANSIT"
                    if index % 2 == 0
                    else "SHIPPED"
                )
                received_at = None

            shipments.append(
                {
                    "shipment_id": self._uuid(),
                    "organization_id": (
                        purchase_order["organization_id"]
                    ),
                    "purchase_order_id": (
                        purchase_order[
                            "purchase_order_id"
                        ]
                    ),
                    "shipment_status": shipment_status,
                    "shipped_at": shipped_at,
                    "received_at": received_at,
                }
            )

        return shipments

    def generate(
        self,
        transaction_data: dict[
            str,
            list[dict[str, Any]],
        ] | None = None,
        fulfillment_data: dict[
            str,
            list[dict[str, Any]],
        ] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        if transaction_data is not None:
            self.transaction_data = transaction_data

        if fulfillment_data is not None:
            self.fulfillment_data = fulfillment_data

        drivers = self.generate_drivers()

        deliveries = self.generate_deliveries(
            drivers
        )

        shipments = self.generate_shipments()

        return {
            "drivers": drivers,
            "deliveries": deliveries,
            "shipments": shipments,
        }

    def summary(self) -> dict[str, int]:
        return {
            "drivers": (
                self.config.total_drivers
            ),
        }