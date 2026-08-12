from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratorConfig:
    """Configuration for deterministic synthetic commerce generation."""

    seed: int = 42

    organizations: int = 3
    brands_per_organization: int = 5
    categories_per_organization: int = 20
    products_per_organization: int = 100
    skus_per_product: int = 2
    customers_per_organization: int = 1_000
    suppliers_per_organization: int = 20

    @property
    def total_products(self) -> int:
        return self.organizations * self.products_per_organization

    @property
    def total_skus(self) -> int:
        return self.total_products * self.skus_per_product

    @property
    def total_customers(self) -> int:
        return self.organizations * self.customers_per_organization