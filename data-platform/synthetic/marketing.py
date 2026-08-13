from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from config import GeneratorConfig
from generator import SyntheticCommerceGenerator


class SyntheticMarketingGenerator:
    """
    Deterministic synthetic generator for marketing-domain data.

    Domain flow:

        Organization
            ├── Campaign
            └── Promotion
                    └── Coupon
    """

    def __init__(
        self,
        config: GeneratorConfig | None = None,
        master_data: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.config = config or GeneratorConfig()
        self.random = random.Random(self.config.seed + 4)

        if master_data is None:
            master_data = SyntheticCommerceGenerator(
                self.config
            ).generate()

        self.master_data = master_data

    def _uuid(self) -> str:
        return str(
            uuid.UUID(
                int=self.random.getrandbits(128)
            )
        )

    def generate_campaigns(
        self,
    ) -> list[dict[str, Any]]:
        campaigns = []

        channels = [
            "EMAIL",
            "SOCIAL",
            "SEARCH",
            "PUSH",
            "SMS",
        ]

        base_start = datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        )

        for organization in self.master_data[
            "organizations"
        ]:
            organization_id = organization[
                "organization_id"
            ]

            for index in range(
                1,
                self.config.campaigns_per_organization + 1,
            ):
                start_at = base_start + timedelta(
                    days=(index - 1) * 14
                )

                end_at = start_at + timedelta(
                    days=7 + (index % 7)
                )

                budget_amount = Decimal(
                    "10000.00"
                ) + Decimal(
                    index * 2500
                )

                campaigns.append(
                    {
                        "campaign_id": self._uuid(),
                        "organization_id": organization_id,
                        "name": (
                            f"Campaign {index}"
                        ),
                        "channel": channels[
                            (index - 1)
                            % len(channels)
                        ],
                        "start_at": start_at,
                        "end_at": end_at,
                        "budget_amount": budget_amount,
                    }
                )

        return campaigns

    def generate_promotions(
        self,
    ) -> list[dict[str, Any]]:
        promotions = []

        promotion_types = [
            "PERCENTAGE",
            "FIXED_AMOUNT",
        ]

        base_start = datetime(
            2026,
            1,
            5,
            tzinfo=timezone.utc,
        )

        for organization in self.master_data[
            "organizations"
        ]:
            organization_id = organization[
                "organization_id"
            ]

            for index in range(
                1,
                self.config.promotions_per_organization + 1,
            ):
                promotion_type = promotion_types[
                    (index - 1)
                    % len(promotion_types)
                ]

                start_at = base_start + timedelta(
                    days=(index - 1) * 10
                )

                end_at = start_at + timedelta(
                    days=10 + (index % 5)
                )

                if promotion_type == "PERCENTAGE":
                    discount_percentage = Decimal(
                        str(5 + ((index - 1) % 5) * 5)
                    )
                    discount_amount = None
                else:
                    discount_percentage = None
                    discount_amount = Decimal(
                        str(50 + ((index - 1) % 5) * 50)
                    )

                promotions.append(
                    {
                        "promotion_id": self._uuid(),
                        "organization_id": organization_id,
                        "name": (
                            f"Promotion {index}"
                        ),
                        "promotion_type": promotion_type,
                        "discount_percentage": (
                            discount_percentage
                        ),
                        "discount_amount": discount_amount,
                        "start_at": start_at,
                        "end_at": end_at,
                    }
                )

        return promotions

    def generate_coupons(
        self,
        promotions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        coupons = []

        for promotion in promotions:
            organization_id = promotion[
                "organization_id"
            ]

            promotion_id = promotion[
                "promotion_id"
            ]

            for index in range(
                1,
                self.config.coupons_per_promotion + 1,
            ):
                coupons.append(
                    {
                        "coupon_id": self._uuid(),
                        "organization_id": organization_id,
                        "promotion_id": promotion_id,
                        "coupon_code": (
                            f"COUPON-{promotion_id[:8]}-"
                            f"{index:03d}"
                        ),
                        "usage_limit": (
                            100 + (index * 50)
                        ),
                    }
                )

        return coupons

    def generate(
        self,
    ) -> dict[str, list[dict[str, Any]]]:
        campaigns = self.generate_campaigns()
        promotions = self.generate_promotions()
        coupons = self.generate_coupons(promotions)

        return {
            "campaigns": campaigns,
            "promotions": promotions,
            "coupons": coupons,
        }

    def summary(self) -> dict[str, int]:
        return {
            "campaigns": self.config.total_campaigns,
            "promotions": self.config.total_promotions,
            "coupons": self.config.total_coupons,
        }