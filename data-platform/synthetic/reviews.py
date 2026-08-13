from __future__ import annotations

import random
import uuid
from datetime import timedelta
from typing import Any

from config import GeneratorConfig
from generator import SyntheticCommerceGenerator
from transactions import SyntheticTransactionGenerator


class SyntheticReviewGenerator:
    """
    Deterministic generator for customer reviews.

    Domain flow:

        Customer
            ↓
          Review
          ↙   ↘
        SKU   Order (optional)

    When an order is attached, the reviewed SKU is selected
    from that customer's order items.
    """

    def __init__(
        self,
        config: GeneratorConfig | None = None,
        master_data: dict[str, list[dict[str, Any]]] | None = None,
        transaction_data: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.config = config or GeneratorConfig()
        self.random = random.Random(self.config.seed + 6)

        if master_data is None:
            master_data = SyntheticCommerceGenerator(
                self.config
            ).generate()

        self.master_data = master_data

        if transaction_data is None:
            transaction_data = SyntheticTransactionGenerator(
                config=self.config,
                master_data=master_data,
            ).generate()

        self.transaction_data = transaction_data

    def _uuid(self) -> str:
        return str(
            uuid.UUID(
                int=self.random.getrandbits(128)
            )
        )

    def generate_reviews(
        self,
    ) -> list[dict[str, Any]]:
        reviews = []

        customers = self.master_data["customers"]
        skus = self.master_data["skus"]

        orders = self.transaction_data[
            "customer_orders"
        ]

        order_items = self.transaction_data[
            "order_items"
        ]

        customers_by_id = {
            customer["customer_id"]: customer
            for customer in customers
        }

        orders_by_customer: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for order in orders:
            orders_by_customer.setdefault(
                order["customer_id"],
                [],
            ).append(order)

        order_items_by_order: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for item in order_items:
            order_items_by_order.setdefault(
                item["order_id"],
                [],
            ).append(item)

        organization_skus: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for sku in skus:
            organization_skus.setdefault(
                sku["organization_id"],
                [],
            ).append(sku)

        review_texts = {
            1: "Very disappointing experience.",
            2: "Below expectations.",
            3: "It was okay.",
            4: "Good overall experience.",
            5: "Excellent experience.",
        }

        review_index = 0

        for customer in customers:
            customer_id = customer["customer_id"]
            organization_id = customer[
                "organization_id"
            ]

            customer_orders = orders_by_customer.get(
                customer_id,
                [],
            )

            available_skus = organization_skus.get(
                organization_id,
                [],
            )

            if not available_skus:
                raise ValueError(
                    "No SKUs available for review organization."
                )

            for review_number in range(
                self.config.reviews_per_customer
            ):
                review_order = None

                # Attach the review to an order when one
                # exists. This exercises the optional FK
                # while still producing valid order-linked
                # reviews.
                if customer_orders and (
                    (
                        review_index
                        + review_number
                    )
                    % 4
                    != 0
                ):
                    review_order = customer_orders[
                        (
                            review_index
                            + review_number
                        )
                        % len(customer_orders)
                    ]

                if review_order is not None:
                    order_items_for_order = (
                        order_items_by_order.get(
                            review_order["order_id"],
                            [],
                        )
                    )

                    if not order_items_for_order:
                        raise ValueError(
                            "Review order has no order items."
                        )

                    reviewed_item = (
                        order_items_for_order[
                            (
                                review_index
                                + review_number
                            )
                            % len(
                                order_items_for_order
                            )
                        ]
                    )

                    sku_id = reviewed_item[
                        "sku_id"
                    ]

                    created_at = (
                        review_order["ordered_at"]
                        + timedelta(
                            hours=24
                            + (
                                (
                                    review_index
                                    + review_number
                                )
                                % 120
                            )
                        )
                    )

                    order_id = review_order[
                        "order_id"
                    ]

                else:
                    sku = available_skus[
                        (
                            review_index
                            + review_number
                        )
                        % len(available_skus)
                    ]

                    sku_id = sku["sku_id"]
                    order_id = None

                    # Unlinked reviews still receive a deterministic
                    # timestamp from the existing transaction timeline.
                    reference_orders = self.transaction_data[
                        "customer_orders"
                    ]

                    if not reference_orders:
                        raise ValueError(
                            "Cannot generate review timestamp without orders."
                        )

                    reference_order = reference_orders[
                        review_index % len(reference_orders)
                    ]

                    created_at = (
                        reference_order["ordered_at"]
                        + timedelta(
                            days=1
                        )
                    )

                rating = (
                    1
                    + (
                        (
                            review_index
                            + review_number
                        )
                        % 5
                    )
                )

                reviews.append(
                    {
                        "review_id": self._uuid(),
                        "organization_id": organization_id,
                        "customer_id": customer_id,
                        "sku_id": sku_id,
                        "order_id": order_id,
                        "rating": rating,
                        "review_text": review_texts[
                            rating
                        ],
                        "created_at": created_at,
                    }
                )

                review_index += 1

        return reviews

    def generate(
        self,
    ) -> dict[str, list[dict[str, Any]]]:
        return {
            "reviews": self.generate_reviews(),
        }

    def summary(self) -> dict[str, int]:
        return {
            "reviews": self.config.total_reviews,
        }