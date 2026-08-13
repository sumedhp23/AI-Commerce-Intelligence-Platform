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
    customer_segments_per_organization: int = 5
    fulfillment_locations_per_organization: int = 3
    inventory_snapshot_days: int = 30
    inventory_movements_per_sku_location: int = 10
    purchase_orders_per_organization: int = 10
    purchase_order_items_per_order: int = 3
    drivers_per_organization: int = 20
    campaigns_per_organization: int = 5
    promotions_per_organization: int = 5
    coupons_per_promotion: int = 3
    sessions_per_customer: int = 1
    search_events_per_session: int = 2
    click_events_per_session: int = 2
    impressions_per_session: int = 3

    @property
    def total_products(self) -> int:
        return self.organizations * self.products_per_organization

    @property
    def total_skus(self) -> int:
        return self.total_products * self.skus_per_product

    @property
    def total_customers(self) -> int:
        return self.organizations * self.customers_per_organization

    @property
    def total_suppliers(self) -> int:
        return self.organizations * self.suppliers_per_organization

    @property
    def total_customer_segments(self) -> int:
        return (
            self.organizations
            * self.customer_segments_per_organization
        )
    @property
    def total_fulfillment_locations(self) -> int:
        return (
            self.organizations
            * self.fulfillment_locations_per_organization
        )

    @property
    def total_drivers(self) -> int:
        return (
            self.organizations
            * self.drivers_per_organization
        )

    @property
    def total_campaigns(self) -> int:
        return (
            self.organizations
            * self.campaigns_per_organization
        )

    @property
    def total_promotions(self) -> int:
        return (
            self.organizations
            * self.promotions_per_organization
        )

    @property
    def total_coupons(self) -> int:
        return (
            self.total_promotions
            * self.coupons_per_promotion
        )

    @property
    def total_sessions(self) -> int:
        return (
            self.total_customers
            * self.sessions_per_customer
        )

    @property
    def total_search_events(self) -> int:
        return (
            self.total_sessions
            * self.search_events_per_session
        )

    @property
    def total_click_events(self) -> int:
        return (
            self.total_sessions
            * self.click_events_per_session
        )

    @property
    def total_impressions(self) -> int:
        return (
            self.total_sessions
            * self.impressions_per_session
        )

    @property
    def total_purchase_orders(self) -> int:
        return (
            self.organizations
            * self.purchase_orders_per_organization
        )