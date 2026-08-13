from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from config import GeneratorConfig
from generator import SyntheticCommerceGenerator
from marketing import SyntheticMarketingGenerator


class SyntheticCustomerBehaviorGenerator:
    """
    Deterministic generator for customer behavior data.

    Domain flow:

        Customer
            ↓
        Customer Session
            ├── Search Event
            ├── Click Event → SKU
            └── Impression → SKU + Campaign
    """

    def __init__(
        self,
        config: GeneratorConfig | None = None,
        master_data: dict[str, list[dict[str, Any]]] | None = None,
        marketing_data: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.config = config or GeneratorConfig()
        self.random = random.Random(self.config.seed + 5)

        if master_data is None:
            master_data = SyntheticCommerceGenerator(
                self.config
            ).generate()

        self.master_data = master_data

        if marketing_data is None:
            marketing_data = SyntheticMarketingGenerator(
                config=self.config,
                master_data=master_data,
            ).generate()

        self.marketing_data = marketing_data

    def _uuid(self) -> str:
        return str(
            uuid.UUID(
                int=self.random.getrandbits(128)
            )
        )

    def _session_start(
        self,
        customer_index: int,
        session_index: int,
    ) -> datetime:
        base = datetime(
            2026,
            1,
            1,
            8,
            0,
            tzinfo=timezone.utc,
        )

        return base + timedelta(
            days=customer_index % 90,
            minutes=(
                (customer_index * 11)
                + (session_index * 47)
            ) % 840,
        )

    def generate_sessions(
        self,
    ) -> list[dict[str, Any]]:
        sessions = []

        device_types = [
            "MOBILE",
            "DESKTOP",
            "TABLET",
        ]

        for customer_index, customer in enumerate(
            self.master_data["customers"],
            start=1,
        ):
            customer_id = customer["customer_id"]

            for session_index in range(
                1,
                self.config.sessions_per_customer + 1,
            ):
                started_at = self._session_start(
                    customer_index,
                    session_index,
                )

                duration_minutes = (
                    10
                    + (
                        (
                            customer_index
                            + session_index
                        )
                        % 51
                    )
                )

                ended_at = started_at + timedelta(
                    minutes=duration_minutes
                )

                sessions.append(
                    {
                        "session_id": self._uuid(),
                        "organization_id": (
                            customer["organization_id"]
                        ),
                        "customer_id": customer_id,
                        "started_at": started_at,
                        "ended_at": ended_at,
                        "acquisition_channel": (
                            customer[
                                "acquisition_channel"
                            ]
                        ),
                        "device_type": device_types[
                            (
                                customer_index
                                + session_index
                            )
                            % len(device_types)
                        ],
                        "city": customer["city"],
                    }
                )

        return sessions

    def generate_search_events(
        self,
        sessions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        search_events = []

        search_queries = [
            "shampoo",
            "face wash",
            "wireless earbuds",
            "running shoes",
            "coffee",
            "protein",
            "backpack",
            "sunscreen",
        ]

        for session_index, session in enumerate(
            sessions,
            start=1,
        ):
            for event_index in range(
                1,
                self.config.search_events_per_session + 1,
            ):
                occurred_at = session[
                    "started_at"
                ] + timedelta(
                    minutes=event_index * 2
                )

                search_events.append(
                    {
                        "search_event_id": self._uuid(),
                        "organization_id": (
                            session["organization_id"]
                        ),
                        "session_id": session["session_id"],
                        "customer_id": session["customer_id"],
                        "search_query": search_queries[
                            (
                                session_index
                                + event_index
                            )
                            % len(search_queries)
                        ],
                        "results_count": (
                            5
                            + (
                                session_index
                                + event_index
                            )
                            % 96
                        ),
                        "occurred_at": occurred_at,
                    }
                )

        return search_events

    def generate_click_events(
        self,
        sessions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        click_events = []

        page_types = [
            "SEARCH_RESULTS",
            "PRODUCT_DETAIL",
            "CATEGORY",
            "RECOMMENDATION",
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

        for session_index, session in enumerate(
            sessions,
            start=1,
        ):
            organization_skus = skus_by_organization[
                session["organization_id"]
            ]

            for event_index in range(
                1,
                self.config.click_events_per_session + 1,
            ):
                sku = organization_skus[
                    (
                        session_index
                        + event_index
                    )
                    % len(organization_skus)
                ]

                occurred_at = session[
                    "started_at"
                ] + timedelta(
                    minutes=(
                        3 + event_index * 3
                    )
                )

                click_events.append(
                    {
                        "click_event_id": self._uuid(),
                        "organization_id": (
                            session["organization_id"]
                        ),
                        "session_id": session["session_id"],
                        "customer_id": session["customer_id"],
                        "sku_id": sku["sku_id"],
                        "page_type": page_types[
                            (
                                session_index
                                + event_index
                            )
                            % len(page_types)
                        ],
                        "occurred_at": occurred_at,
                    }
                )

        return click_events

    def generate_impressions(
        self,
        sessions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        impressions = []

        skus_by_organization: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for sku in self.master_data["skus"]:
            skus_by_organization.setdefault(
                sku["organization_id"],
                [],
            ).append(sku)

        campaigns_by_organization: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for campaign in self.marketing_data[
            "campaigns"
        ]:
            campaigns_by_organization.setdefault(
                campaign["organization_id"],
                [],
            ).append(campaign)

        for session_index, session in enumerate(
            sessions,
            start=1,
        ):
            organization_id = session[
                "organization_id"
            ]

            organization_skus = skus_by_organization[
                organization_id
            ]

            organization_campaigns = (
                campaigns_by_organization[
                    organization_id
                ]
            )

            for event_index in range(
                1,
                self.config.impressions_per_session + 1,
            ):
                sku = organization_skus[
                    (
                        session_index
                        + event_index
                    )
                    % len(organization_skus)
                ]

                campaign = organization_campaigns[
                    (
                        session_index
                        + event_index
                    )
                    % len(organization_campaigns)
                ]

                occurred_at = session[
                    "started_at"
                ] + timedelta(
                    minutes=event_index
                )

                impressions.append(
                    {
                        "impression_id": self._uuid(),
                        "organization_id": organization_id,
                        "session_id": session["session_id"],
                        "customer_id": session["customer_id"],
                        "sku_id": sku["sku_id"],
                        "campaign_id": (
                            campaign["campaign_id"]
                        ),
                        "occurred_at": occurred_at,
                    }
                )

        return impressions

    def generate(
        self,
    ) -> dict[str, list[dict[str, Any]]]:
        sessions = self.generate_sessions()

        search_events = self.generate_search_events(
            sessions
        )

        click_events = self.generate_click_events(
            sessions
        )

        impressions = self.generate_impressions(
            sessions
        )

        return {
            "customer_sessions": sessions,
            "search_events": search_events,
            "click_events": click_events,
            "impressions": impressions,
        }

    def summary(self) -> dict[str, int]:
        return {
            "sessions": self.config.total_sessions,
            "search_events": (
                self.config.total_search_events
            ),
            "click_events": (
                self.config.total_click_events
            ),
            "impressions": (
                self.config.total_impressions
            ),
        }