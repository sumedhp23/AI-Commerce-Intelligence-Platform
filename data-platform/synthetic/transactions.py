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
        ↓
    Customer Return
        ↓
    Refund
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
            raise ValueError(
                "Cannot generate order items without SKUs."
            )

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
                        "organization_id": (
                            order["organization_id"]
                        ),
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
                    "organization_id": (
                        order["organization_id"]
                    ),
                    "order_id": order["order_id"],
                    "payment_method": payment_methods[
                        index % len(payment_methods)
                    ],
                    "payment_status": "CAPTURED",
                    "amount": order["total_amount"],
                    "transaction_reference": (
                        f"TXN-{index + 1:010d}"
                    ),
                    "paid_at": (
                        order["ordered_at"]
                        + timedelta(minutes=2)
                    ),
                }
            )

        return payments

    def generate_returns(
        self,
        orders: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Deterministic synthetic return policy:

        - Every 5th generated order receives a return.
        - Return statuses alternate between COMPLETED and REJECTED.
        - COMPLETED returns receive completed_at.
        - REJECTED returns have completed_at = None.
        """

        return_reasons = [
            "DAMAGED",
            "WRONG_ITEM",
            "QUALITY_ISSUE",
            "CUSTOMER_CHANGED_MIND",
        ]

        returns = []
        return_index = 0

        for order_number, order in enumerate(
            orders,
            start=1,
        ):
            if order_number % 5 != 0:
                continue

            return_index += 1

            is_completed = return_index % 2 == 1

            requested_at = (
                order["ordered_at"]
                + timedelta(hours=24)
            )

            completed_at = None

            if is_completed:
                completed_at = (
                    requested_at
                    + timedelta(hours=48)
                )

            returns.append(
                {
                    "return_id": self._uuid(),
                    "organization_id": (
                        order["organization_id"]
                    ),
                    "order_id": order["order_id"],
                    "return_status": (
                        "COMPLETED"
                        if is_completed
                        else "REJECTED"
                    ),
                    "reason": return_reasons[
                        (return_index - 1)
                        % len(return_reasons)
                    ],
                    "requested_at": requested_at,
                    "completed_at": completed_at,
                }
            )

        return returns

    def generate_refunds(
        self,
        orders: list[dict[str, Any]],
        payments: list[dict[str, Any]],
        returns: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Deterministic synthetic refund policy:

        - Only COMPLETED returns can produce refunds.
        - Every 2nd COMPLETED return receives a refund.
        - Refund amount alternates between 50% and 100%
          of the order total.
        - Payment linkage is preserved when a refund is generated.
        """

        payments_by_order = {
            payment["order_id"]: payment
            for payment in payments
        }

        orders_by_id = {
            order["order_id"]: order
            for order in orders
        }

        refund_reasons = [
            "RETURN_COMPLETED",
            "CUSTOMER_REFUND",
        ]

        refunds = []
        completed_return_index = 0

        for customer_return in returns:
            if (
                customer_return["return_status"]
                != "COMPLETED"
            ):
                continue

            completed_return_index += 1

            if completed_return_index % 2 != 0:
                continue

            order_id = customer_return["order_id"]
            order = orders_by_id[order_id]
            payment = payments_by_order.get(order_id)

            if payment is None:
                raise ValueError(
                    "Cannot generate refund without payment "
                    "for completed return."
                )

            if completed_return_index % 4 == 0:
                refund_amount = (
                    order["total_amount"]
                )
            else:
                refund_amount = (
                    order["total_amount"]
                    * Decimal("0.50")
                ).quantize(Decimal("0.01"))

            if refund_amount > payment["amount"]:
                raise ValueError(
                    "Refund amount cannot exceed payment amount."
                )

            refunded_at = (
                customer_return["completed_at"]
                + timedelta(hours=2)
            )

            refunds.append(
                {
                    "refund_id": self._uuid(),
                    "organization_id": (
                        order["organization_id"]
                    ),
                    "order_id": order_id,
                    "payment_id": payment["payment_id"],
                    "amount": refund_amount,
                    "reason": refund_reasons[
                        (completed_return_index // 2 - 1)
                        % len(refund_reasons)
                    ],
                    "refunded_at": refunded_at,
                }
            )

        return refunds

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

        returns = self.generate_returns(
            orders=orders,
        )

        refunds = self.generate_refunds(
            orders=orders,
            payments=payments,
            returns=returns,
        )

        return {
            "customer_orders": orders,
            "order_items": order_items,
            "payments": payments,
            "customer_returns": returns,
            "refunds": refunds,
        }