from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from config import GeneratorConfig
from generator import SyntheticCommerceGenerator


class SyntheticTransactionGenerator:
    """
    Deterministic generator for the core commerce transaction flow:

    Customer
        ↓
    Customer Order
        ↓
    Order Item
        ↓
    Payment
    """

    def __init__(
        self,
        config: GeneratorConfig | None = None,
        master_data: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.config = config or GeneratorConfig()
        self.random = random.Random(self.config.seed + 1)

        if master_data is None:
            master_data = SyntheticCommerceGenerator(
                self.config
            ).generate()

        self.master_data = master_data

    def _uuid(self) -> str:
        return str(uuid.UUID(int=self.random.getrandbits(128)))

    def _ordered_at(self, index: int) -> datetime:
        base = datetime(
            2026,
            1,
            1,
            10,
            0,
            tzinfo=timezone.utc,
        )

        return base + timedelta(
            days=index % 90,
            minutes=(index * 17) % 720,
        )

    def generate_orders(
        self,
        orders_per_customer: int = 1,
    ) -> list[dict[str, Any]]:
        customers = self.master_data["customers"]

        orders = []

        order_index = 1

        for customer in customers:
            for _ in range(orders_per_customer):
                ordered_at = self._ordered_at(order_index)

                orders.append(
                    {
                        "order_id": self._uuid(),
                        "organization_id": customer["organization_id"],
                        "customer_id": customer["customer_id"],
                        "fulfillment_location_id": None,
                        "order_number": (
                            f"ORD-{order_index:08d}"
                        ),
                        "order_status": "CONFIRMED",
                        "currency": "INR",
                        "subtotal_amount": Decimal("0.00"),
                        "discount_amount": Decimal("0.00"),
                        "delivery_fee": Decimal("0.00"),
                        "tax_amount": Decimal("0.00"),
                        "total_amount": Decimal("0.00"),
                        "ordered_at": ordered_at,
                        "cancelled_at": None,
                    }
                )

                order_index += 1

        return orders

    def generate_order_items(
        self,
        orders: list[dict[str, Any]],
        items_per_order: int = 2,
    ) -> list[dict[str, Any]]:
        skus = self.master_data["skus"]

        if not skus:
            raise ValueError("Cannot generate order items without SKUs.")

        order_items = []

        for order_index, order in enumerate(orders):
            organization_skus = [
                sku
                for sku in skus
                if sku["organization_id"]
                == order["organization_id"]
            ]

            if not organization_skus:
                raise ValueError(
                    "No SKUs available for order organization."
                )

            for item_index in range(items_per_order):
                sku = organization_skus[
                    (order_index + item_index)
                    % len(organization_skus)
                ]

                quantity = 1 + (
                    (order_index + item_index) % 3
                )

                unit_price = Decimal(
                    str(sku["list_price"])
                )

                discount_amount = Decimal("0.00")

                order_items.append(
                    {
                        "order_item_id": self._uuid(),
                        "organization_id": order["organization_id"],
                        "order_id": order["order_id"],
                        "sku_id": sku["sku_id"],
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "discount_amount": discount_amount,
                    }
                )

        return order_items

    def apply_order_totals(
        self,
        orders: list[dict[str, Any]],
        order_items: list[dict[str, Any]],
    ) -> None:
        items_by_order: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for item in order_items:
            items_by_order.setdefault(
                item["order_id"],
                [],
            ).append(item)

        for order in orders:
            items = items_by_order.get(
                order["order_id"],
                [],
            )

            subtotal = sum(
                (
                    item["unit_price"]
                    * item["quantity"]
                )
                for item in items
            )

            discount = sum(
                (
                    item["discount_amount"]
                    for item in items
                ),
                Decimal("0.00"),
            )

            delivery_fee = Decimal("40.00")

            taxable_amount = subtotal - discount

            tax = (
                taxable_amount
                * Decimal("0.18")
            ).quantize(Decimal("0.01"))

            total = (
                taxable_amount
                + delivery_fee
                + tax
            ).quantize(Decimal("0.01"))

            order["subtotal_amount"] = subtotal.quantize(
                Decimal("0.01")
            )
            order["discount_amount"] = discount.quantize(
                Decimal("0.01")
            )
            order["delivery_fee"] = delivery_fee
            order["tax_amount"] = tax
            order["total_amount"] = total

    def generate_payments(
        self,
        orders: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        payment_methods = [
            "UPI",
            "CARD",
            "NET_BANKING",
            "COD",
        ]

        payments = []

        for index, order in enumerate(orders):
            payments.append(
                {
                    "payment_id": self._uuid(),
                    "organization_id": order["organization_id"],
                    "order_id": order["order_id"],
                    "payment_method": payment_methods[
                        index % len(payment_methods)
                    ],
                    "payment_status": "CAPTURED",
                    "amount": order["total_amount"],
                    "transaction_reference": (
                        f"TXN-{index + 1:010d}"
                    ),
                    "paid_at": order["ordered_at"]
                    + timedelta(minutes=2),
                }
            )

        return payments

    def generate(
        self,
        orders_per_customer: int = 1,
        items_per_order: int = 2,
    ) -> dict[str, list[dict[str, Any]]]:
        orders = self.generate_orders(
            orders_per_customer=orders_per_customer,
        )

        order_items = self.generate_order_items(
            orders=orders,
            items_per_order=items_per_order,
        )

        self.apply_order_totals(
            orders=orders,
            order_items=order_items,
        )

        payments = self.generate_payments(
            orders=orders,
        )

        return {
            "customer_orders": orders,
            "order_items": order_items,
            "payments": payments,
        }