from __future__ import annotations

from typing import Any

from config import GeneratorConfig
from customer_behavior import SyntheticCustomerBehaviorGenerator
from fulfillment import SyntheticFulfillmentGenerator
from generator import SyntheticCommerceGenerator
from logistics import SyntheticLogisticsGenerator
from marketing import SyntheticMarketingGenerator
from operational_events import SyntheticOperationalEventGenerator
from reviews import SyntheticReviewGenerator
from transactions import SyntheticTransactionGenerator


class SyntheticCommercePipeline:
    """
    Deterministic orchestration layer for the complete synthetic
    commerce data platform.

    Dependency flow:

        Master Data
        ├── Transactions
        │   └── Reviews
        ├── Fulfillment
        │   └── Operational Events
        ├── Marketing
        │   └── Customer Behavior
        └── Transactions + Fulfillment
            └── Logistics

    Individual domain generators remain independently usable.
    This class only coordinates them into one coherent dataset.
    """

    def __init__(
        self,
        config: GeneratorConfig | None = None,
    ) -> None:
        self.config = config or GeneratorConfig()

    def generate(self) -> dict[str, dict[str, list[dict[str, Any]]]]:
        master_data = SyntheticCommerceGenerator(
            config=self.config,
        ).generate()

        transaction_data = SyntheticTransactionGenerator(
            config=self.config,
            master_data=master_data,
        ).generate()

        fulfillment_data = SyntheticFulfillmentGenerator(
            config=self.config,
            master_data=master_data,
        ).generate()

        marketing_data = SyntheticMarketingGenerator(
            config=self.config,
            master_data=master_data,
        ).generate()

        logistics_data = SyntheticLogisticsGenerator(
            config=self.config,
            master_data=master_data,
            transaction_data=transaction_data,
            fulfillment_data=fulfillment_data,
        ).generate()

        customer_behavior_data = (
            SyntheticCustomerBehaviorGenerator(
                config=self.config,
                master_data=master_data,
                marketing_data=marketing_data,
            ).generate()
        )

        review_data = SyntheticReviewGenerator(
            config=self.config,
            master_data=master_data,
            transaction_data=transaction_data,
        ).generate()

        operational_event_data = (
            SyntheticOperationalEventGenerator(
                config=self.config,
                master_data={
                    **master_data,
                    "fulfillment_locations": (
                        fulfillment_data[
                            "fulfillment_locations"
                        ]
                    ),
                },
            ).generate()
        )

        return {
            "master": master_data,
            "transactions": transaction_data,
            "fulfillment": fulfillment_data,
            "marketing": marketing_data,
            "logistics": logistics_data,
            "customer_behavior": customer_behavior_data,
            "reviews": review_data,
            "operational_events": operational_event_data,
        }

    def summary(self) -> dict[str, int]:
        data = self.generate()

        return {
            dataset_name: sum(
                len(rows)
                for rows in dataset.values()
            )
            for dataset_name, dataset in data.items()
        }