from __future__ import annotations

import random
import uuid
from dataclasses import asdict
from typing import Any

from config import GeneratorConfig


class SyntheticCommerceGenerator:
    """
    Deterministic synthetic generator for schema-aligned master data.

    This slice generates reference/master entities only.
    Transactional data is intentionally handled separately.
    """

    def __init__(self, config: GeneratorConfig | None = None) -> None:
        self.config = config or GeneratorConfig()
        self.random = random.Random(self.config.seed)

    def _uuid(self) -> str:
        return str(uuid.UUID(int=self.random.getrandbits(128)))

    def generate_organizations(self) -> list[dict[str, Any]]:
        organizations = []

        industries = [
            "E_COMMERCE",
            "QUICK_COMMERCE",
            "FOOD_DELIVERY",
        ]

        for index in range(1, self.config.organizations + 1):
            organizations.append(
                {
                    "organization_id": self._uuid(),
                    "name": f"Organization {index}",
                    "industry": industries[(index - 1) % len(industries)],
                    "country_code": "IN",
                }
            )

        return organizations

    def generate_customer_segments(
        self,
        organizations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        segments = []

        segment_names = [
            "NEW",
            "REGULAR",
            "LOYAL",
            "HIGH_VALUE",
            "AT_RISK",
        ]

        for organization in organizations:
            for index in range(
                1,
                self.config.customer_segments_per_organization + 1,
            ):
                segments.append(
                    {
                        "customer_segment_id": self._uuid(),
                        "organization_id": organization["organization_id"],
                        "name": segment_names[(index - 1) % len(segment_names)],
                        "description": (
                            f"Synthetic customer segment {index}"
                        ),
                    }
                )

        return segments

    def generate_brands(
        self,
        organizations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        brands = []

        for organization in organizations:
            for index in range(
                1,
                self.config.brands_per_organization + 1,
            ):
                brands.append(
                    {
                        "brand_id": self._uuid(),
                        "organization_id": organization["organization_id"],
                        "name": f"Brand {index}",
                    }
                )

        return brands

    def generate_categories(
        self,
        organizations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        categories = []

        for organization in organizations:
            for index in range(
                1,
                self.config.categories_per_organization + 1,
            ):
                categories.append(
                    {
                        "category_id": self._uuid(),
                        "organization_id": organization["organization_id"],
                        "parent_category_id": None,
                        "name": f"Category {index}",
                    }
                )

        return categories

    def generate_suppliers(
        self,
        organizations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        suppliers = []

        for organization in organizations:
            for index in range(
                1,
                self.config.suppliers_per_organization + 1,
            ):
                suppliers.append(
                    {
                        "supplier_id": self._uuid(),
                        "organization_id": organization["organization_id"],
                        "name": f"Supplier {index}",
                        "city": "Bengaluru",
                        "country_code": "IN",
                    }
                )

        return suppliers

    def generate_customers(
        self,
        organizations: list[dict[str, Any]],
        customer_segments: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        customers = []

        segments_by_organization: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for segment in customer_segments:
            segments_by_organization.setdefault(
                segment["organization_id"],
                [],
            ).append(segment)

        for organization in organizations:
            organization_id = organization["organization_id"]
            segments = segments_by_organization[organization_id]

            for index in range(
                1,
                self.config.customers_per_organization + 1,
            ):
                segment = segments[(index - 1) % len(segments)]

                customers.append(
                    {
                        "customer_id": self._uuid(),
                        "organization_id": organization_id,
                        "customer_segment_id": (
                            segment["customer_segment_id"]
                        ),
                        "external_customer_id": (
                            f"ORG-{organization_id[:8]}-CUS-{index:06d}"
                        ),
                        "first_name": f"Customer{index}",
                        "last_name": "Synthetic",
                        "email": f"customer{index}@synthetic.example",
                        "country_code": "IN",
                        "city": "Bengaluru",
                        "acquisition_channel": (
                            "ORGANIC"
                            if index % 2
                            else "PAID"
                        ),
                    }
                )

        return customers

    def generate_products(
        self,
        organizations: list[dict[str, Any]],
        brands: list[dict[str, Any]],
        categories: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        products = []

        brands_by_organization: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for brand in brands:
            brands_by_organization.setdefault(
                brand["organization_id"],
                [],
            ).append(brand)

        categories_by_organization: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for category in categories:
            categories_by_organization.setdefault(
                category["organization_id"],
                [],
            ).append(category)

        for organization in organizations:
            organization_id = organization["organization_id"]
            organization_brands = brands_by_organization[organization_id]
            organization_categories = categories_by_organization[
                organization_id
            ]

            for index in range(
                1,
                self.config.products_per_organization + 1,
            ):
                brand = organization_brands[
                    (index - 1) % len(organization_brands)
                ]

                category = organization_categories[
                    (index - 1) % len(organization_categories)
                ]

                products.append(
                    {
                        "product_id": self._uuid(),
                        "organization_id": organization_id,
                        "brand_id": brand["brand_id"],
                        "category_id": category["category_id"],
                        "product_name": f"Product {index}",
                        "description": (
                            f"Synthetic product {index}"
                        ),
                    }
                )

        return products

    def generate_skus(
        self,
        products: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        skus = []

        for product in products:
            for index in range(
                1,
                self.config.skus_per_product + 1,
            ):
                sku_code = (
                    f"SKU-{product['product_id'][:8]}-{index:02d}"
                )

                skus.append(
                    {
                        "sku_id": self._uuid(),
                        "organization_id": product["organization_id"],
                        "product_id": product["product_id"],
                        "sku_code": sku_code,
                        "sku_name": (
                            f"{product['product_name']} Variant {index}"
                        ),
                        "unit_cost": 100.00,
                        "list_price": 150.00,
                        "weight_grams": 500.00,
                        "active": True,
                    }
                )

        return skus

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        organizations = self.generate_organizations()

        customer_segments = self.generate_customer_segments(
            organizations
        )

        brands = self.generate_brands(organizations)
        categories = self.generate_categories(organizations)
        suppliers = self.generate_suppliers(organizations)

        customers = self.generate_customers(
            organizations,
            customer_segments,
        )

        products = self.generate_products(
            organizations,
            brands,
            categories,
        )

        skus = self.generate_skus(products)

        return {
            "organizations": organizations,
            "customer_segments": customer_segments,
            "brands": brands,
            "categories": categories,
            "suppliers": suppliers,
            "customers": customers,
            "products": products,
            "skus": skus,
        }

    def summary(self) -> dict[str, int]:
        return {
            "organizations": self.config.organizations,
            "customer_segments": (
                self.config.total_customer_segments
            ),
            "brands": (
                self.config.organizations
                * self.config.brands_per_organization
            ),
            "categories": (
                self.config.organizations
                * self.config.categories_per_organization
            ),
            "suppliers": self.config.total_suppliers,
            "customers": self.config.total_customers,
            "products": self.config.total_products,
            "skus": self.config.total_skus,
        }

    def configuration_dict(self) -> dict[str, Any]:
        return asdict(self.config)