from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from config import GeneratorConfig
from generator import SyntheticCommerceGenerator


class SyntheticOperationalEventGenerator:
    """
    Deterministic synthetic generator for operational events.

    Operational events provide cross-domain contextual evidence
    for operational analysis, anomaly detection, and root-cause
    analysis.

    Events may be organization-wide or associated with a specific
    fulfillment location.
    """

    def __init__(
        self,
        config: GeneratorConfig | None = None,
        master_data: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.config = config or GeneratorConfig()
        self.random = random.Random(self.config.seed + 7)

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

    def generate_operational_events(
        self,
    ) -> list[dict[str, Any]]:
        """
        Generate deterministic operational incidents.

        Five events are generated per organization by default.

        Event types are selected from realistic e-commerce
        operational scenarios:

        - WAREHOUSE_OUTAGE
        - PAYMENT_GATEWAY_OUTAGE
        - INVENTORY_SYSTEM_FAILURE
        - DELIVERY_CAPACITY_REDUCTION
        - PRICING_SYSTEM_CHANGE
        - PROMOTION_LAUNCH
        - SUPPLIER_DISRUPTION

        Location-specific events reference a fulfillment location.
        Organization-wide events use a NULL location_id.
        """

        event_definitions = [
            {
                "event_type": "WAREHOUSE_OUTAGE",
                "severity": "HIGH",
                "duration_hours": 8,
                "location_required": True,
                "description": (
                    "Temporary warehouse outage reduced "
                    "fulfillment capacity."
                ),
                "metadata": {
                    "capacity_impact_percent": 65,
                    "operational_area": "WAREHOUSE",
                },
            },
            {
                "event_type": "PAYMENT_GATEWAY_OUTAGE",
                "severity": "CRITICAL",
                "duration_hours": 3,
                "location_required": False,
                "description": (
                    "Payment gateway outage caused "
                    "payment processing failures."
                ),
                "metadata": {
                    "failure_rate_percent": 80,
                    "operational_area": "PAYMENTS",
                },
            },
            {
                "event_type": "INVENTORY_SYSTEM_FAILURE",
                "severity": "HIGH",
                "duration_hours": 5,
                "location_required": True,
                "description": (
                    "Inventory system failure delayed "
                    "stock availability updates."
                ),
                "metadata": {
                    "stock_sync_delay_minutes": 180,
                    "operational_area": "INVENTORY",
                },
            },
            {
                "event_type": "DELIVERY_CAPACITY_REDUCTION",
                "severity": "MEDIUM",
                "duration_hours": 12,
                "location_required": True,
                "description": (
                    "Temporary reduction in delivery capacity "
                    "increased fulfillment pressure."
                ),
                "metadata": {
                    "capacity_reduction_percent": 35,
                    "operational_area": "DELIVERY",
                },
            },
            {
                "event_type": "PRICING_SYSTEM_CHANGE",
                "severity": "LOW",
                "duration_hours": 2,
                "location_required": False,
                "description": (
                    "Pricing configuration change was deployed "
                    "across the commerce platform."
                ),
                "metadata": {
                    "change_scope": "PLATFORM",
                    "operational_area": "PRICING",
                },
            },
            {
                "event_type": "PROMOTION_LAUNCH",
                "severity": "MEDIUM",
                "duration_hours": 24,
                "location_required": False,
                "description": (
                    "Promotional campaign launch increased "
                    "expected customer demand."
                ),
                "metadata": {
                    "expected_demand_lift_percent": 25,
                    "operational_area": "MARKETING",
                },
            },
            {
                "event_type": "SUPPLIER_DISRUPTION",
                "severity": "HIGH",
                "duration_hours": 48,
                "location_required": True,
                "description": (
                    "Supplier disruption affected inbound "
                    "inventory availability."
                ),
                "metadata": {
                    "expected_supply_reduction_percent": 40,
                    "operational_area": "PROCUREMENT",
                },
            },
        ]

        locations_by_organization: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for location in self.master_data.get(
            "fulfillment_locations",
            [],
        ):
            locations_by_organization.setdefault(
                location["organization_id"],
                [],
            ).append(location)

        events = []

        base_datetime = datetime(
            2026,
            1,
            1,
            8,
            0,
            tzinfo=timezone.utc,
        )

        global_event_index = 0

        for organization_index, organization in enumerate(
            self.master_data["organizations"]
        ):
            organization_id = organization[
                "organization_id"
            ]

            organization_locations = (
                locations_by_organization.get(
                    organization_id,
                    [],
                )
            )

            for event_index in range(
                self.config.operational_events_per_organization
            ):
                definition = event_definitions[
                    (
                        organization_index
                        + event_index
                    )
                    % len(event_definitions)
                ]

                started_at = (
                    base_datetime
                    + timedelta(
                        days=(
                            organization_index * 10
                            + event_index * 5
                        ),
                        hours=(
                            organization_index
                            + event_index
                        ),
                    )
                )

                ended_at = (
                    started_at
                    + timedelta(
                        hours=definition[
                            "duration_hours"
                        ]
                    )
                )

                location_id = None
                location_metadata: dict[str, Any] = {}

                if (
                    definition["location_required"]
                    and organization_locations
                ):
                    location = organization_locations[
                        event_index
                        % len(organization_locations)
                    ]

                    location_id = location[
                        "fulfillment_location_id"
                    ]

                    location_metadata = {
                        "location_type": location[
                            "location_type"
                        ],
                        "city": location["city"],
                        "state": location["state"],
                    }

                metadata = {
                    "event_sequence": (
                        global_event_index + 1
                    ),
                    "synthetic": True,
                    **definition["metadata"],
                    **location_metadata,
                }

                events.append(
                    {
                        "operational_event_id": self._uuid(),
                        "organization_id": organization_id,
                        "event_type": definition[
                            "event_type"
                        ],
                        "severity": definition[
                            "severity"
                        ],
                        "location_id": location_id,
                        "description": definition[
                            "description"
                        ],
                        "started_at": started_at,
                        "ended_at": ended_at,
                        "metadata": metadata,
                    }
                )

                global_event_index += 1

        return events

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "operational_events": (
                self.generate_operational_events()
            )
        }