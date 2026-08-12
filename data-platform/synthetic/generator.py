from __future__ import annotations

import random
import uuid
from dataclasses import asdict
from typing import Any

from config import GeneratorConfig


class SyntheticCommerceGenerator:
    """
    Deterministic synthetic commerce data generator.

    Stage 1 initially focuses on generating clean canonical
    entities in memory. Database persistence will be added
    after the generator contract is validated.
    """

    def __init__(self, config: GeneratorConfig | None = None) -> None:
        self.config = config or GeneratorConfig()
        self.random = random.Random(self.config.seed)

    def _uuid(self) -> str:
        """Generate a deterministic UUID from the generator RNG."""
        return str(uuid.UUID(int=self.random.getrandbits(128)))

    def generate_organizations(self) -> list[dict[str, Any]]:
        organizations = []

        for index in range(1, self.config.organizations + 1):
            organizations.append(
                {
                    "id": self._uuid(),
                    "name": f"Organization {index}",
                    "external_id": f"ORG-{index:04d}",
                }
            )

        return organizations

    def generate_brands(
        self,
        organizations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        brands = []

        for organization in organizations:
            for index in range(1, self.config.brands_per_organization + 1):
                brands.append(
                    {
                        "id": self._uuid(),
                        "organization_id": organization["id"],
                        "name": f"Brand {index}",
                        "external_id": (
                            f"{organization['external_id']}-BR-{index:04d}"
                        ),
                    }
                )

        return brands

    def generate_categories(
        self,
        organizations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        categories = []

        for organization in organizations:
            for index in range(1, self.config.categories_per_organization + 1):
                categories.append(
                    {
                        "id": self._uuid(),
                        "organization_id": organization["id"],
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
            for index in range(1, self.config.suppliers_per_organization + 1):
                suppliers.append(
                    {
                        "id": self._uuid(),
                        "organization_id": organization["id"],
                        "name": f"Supplier {index}",
                        "external_id": (
                            f"{organization['external_id']}-SUP-{index:04d}"
                        ),
                    }
                )

        return suppliers

    def generate_customers(
        self,
        organizations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        customers = []

        for organization in organizations:
            for index in range(1, self.config.customers_per_organization + 1):
                customers.append(
                    {
                        "id": self._uuid(),
                        "organization_id": organization["id"],
                        "external_customer_id": (
                            f"{organization['external_id']}-CUS-{index:06d}"
                        ),
                        "first_name": f"Customer{index}",
                        "last_name": "Synthetic",
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

        brands_by_organization: dict[str, list[dict[str, Any]]] = {}

        for brand in brands:
            brands_by_organization.setdefault(
                brand["organization_id"],
                [],
            ).append(brand)

        categories_by_organization: dict[str, list[dict[str, Any]]] = {}

        for category in categories:
            categories_by_organization.setdefault(
                category["organization_id"],
                [],
            ).append(category)

        for organization in organizations:
            organization_brands = brands_by_organization[organization["id"]]
            organization_categories = categories_by_organization[
                organization["id"]
            ]

            for index in range(1, self.config.products_per_organization + 1):
                brand = organization_brands[
                    (index - 1) % len(organization_brands)
                ]

                category = organization_categories[
                    (index - 1) % len(organization_categories)
                ]

                products.append(
                    {
                        "id": self._uuid(),
                        "organization_id": organization["id"],
                        "brand_id": brand["id"],
                        "category_id": category["id"],
                        "name": f"Product {index}",
                        "external_product_id": (
                            f"{organization['external_id']}-PROD-{index:06d}"
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
            for index in range(1, self.config.skus_per_product + 1):
                skus.append(
                    {
                        "id": self._uuid(),
                        "product_id": product["id"],
                        "sku_code": (
                            f"{product['external_product_id']}-SKU-{index:02d}"
                        ),
                        "name": f"{product['name']} Variant {index}",
                    }
                )

        return skus

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        organizations = self.generate_organizations()
        brands = self.generate_brands(organizations)
        categories = self.generate_categories(organizations)
        suppliers = self.generate_suppliers(organizations)
        customers = self.generate_customers(organizations)
        products = self.generate_products(
            organizations,
            brands,
            categories,
        )
        skus = self.generate_skus(products)

        return {
            "organizations": organizations,
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
            "brands": (
                self.config.organizations
                * self.config.brands_per_organization
            ),
            "categories": (
                self.config.organizations
                * self.config.categories_per_organization
            ),
            "suppliers": (
                self.config.organizations
                * self.config.suppliers_per_organization
            ),
            "customers": self.config.total_customers,
            "products": self.config.total_products,
            "skus": self.config.total_skus,
        }

    def configuration_dict(self) -> dict[str, Any]:
        return asdict(self.config)