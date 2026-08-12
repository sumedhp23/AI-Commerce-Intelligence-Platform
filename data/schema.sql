-- Stage 1 canonical analytical schema.
-- PostgreSQL target. All timestamps are UTC in storage.

CREATE SCHEMA IF NOT EXISTS commerce;

CREATE TABLE commerce.organizations (
    organization_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT NOT NULL CHECK (industry IN ('ecommerce', 'food_delivery', 'quick_commerce')),
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE commerce.regions (
    region_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    country TEXT NOT NULL,
    state TEXT NOT NULL,
    city TEXT NOT NULL,
    UNIQUE (organization_id, country, state, city)
);

CREATE TABLE commerce.locations (
    location_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    region_id BIGINT NOT NULL REFERENCES commerce.regions(region_id),
    location_type TEXT NOT NULL CHECK (location_type IN ('warehouse', 'dark_store', 'restaurant', 'store')),
    name TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE commerce.customer_segments (
    segment_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE commerce.customers (
    customer_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    segment_id BIGINT REFERENCES commerce.customer_segments(segment_id),
    home_region_id BIGINT REFERENCES commerce.regions(region_id),
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE commerce.categories (
    category_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    name TEXT NOT NULL
);

CREATE TABLE commerce.brands (
    brand_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    name TEXT NOT NULL
);

CREATE TABLE commerce.products (
    product_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    category_id BIGINT NOT NULL REFERENCES commerce.categories(category_id),
    brand_id BIGINT NOT NULL REFERENCES commerce.brands(brand_id),
    name TEXT NOT NULL
);

CREATE TABLE commerce.skus (
    sku_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    product_id BIGINT NOT NULL REFERENCES commerce.products(product_id),
    sku_code TEXT NOT NULL,
    unit_cost NUMERIC(12,2) NOT NULL CHECK (unit_cost >= 0),
    list_price NUMERIC(12,2) NOT NULL CHECK (list_price >= 0),
    UNIQUE (organization_id, sku_code)
);

CREATE TABLE commerce.orders (
    order_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    customer_id BIGINT NOT NULL REFERENCES commerce.customers(customer_id),
    location_id BIGINT NOT NULL REFERENCES commerce.locations(location_id),
    ordered_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('completed', 'cancelled', 'returned')),
    channel TEXT NOT NULL CHECK (channel IN ('web', 'app', 'marketplace')),
    subtotal NUMERIC(14,2) NOT NULL CHECK (subtotal >= 0),
    discount_amount NUMERIC(14,2) NOT NULL CHECK (discount_amount >= 0),
    delivery_fee NUMERIC(14,2) NOT NULL CHECK (delivery_fee >= 0),
    net_revenue NUMERIC(14,2) NOT NULL CHECK (net_revenue >= 0)
);

CREATE TABLE commerce.order_items (
    order_item_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES commerce.orders(order_id) ON DELETE CASCADE,
    sku_id BIGINT NOT NULL REFERENCES commerce.skus(sku_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    discount_amount NUMERIC(12,2) NOT NULL CHECK (discount_amount >= 0)
);

CREATE TABLE commerce.payments (
    payment_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES commerce.orders(order_id) ON DELETE CASCADE,
    paid_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('paid', 'failed', 'refunded')),
    method TEXT NOT NULL CHECK (method IN ('card', 'upi', 'wallet', 'cash')),
    amount NUMERIC(14,2) NOT NULL CHECK (amount >= 0)
);

CREATE TABLE commerce.returns (
    return_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES commerce.orders(order_id),
    requested_at TIMESTAMPTZ NOT NULL,
    reason TEXT NOT NULL
);

CREATE TABLE commerce.refunds (
    refund_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES commerce.orders(order_id),
    refunded_at TIMESTAMPTZ NOT NULL,
    amount NUMERIC(14,2) NOT NULL CHECK (amount >= 0)
);

CREATE TABLE commerce.inventory_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    location_id BIGINT NOT NULL REFERENCES commerce.locations(location_id),
    sku_id BIGINT NOT NULL REFERENCES commerce.skus(sku_id),
    snapshot_at TIMESTAMPTZ NOT NULL,
    on_hand_quantity INTEGER NOT NULL CHECK (on_hand_quantity >= 0),
    reserved_quantity INTEGER NOT NULL CHECK (reserved_quantity >= 0),
    inbound_quantity INTEGER NOT NULL CHECK (inbound_quantity >= 0),
    CHECK (reserved_quantity <= on_hand_quantity)
);

CREATE TABLE commerce.purchase_orders (
    purchase_order_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    location_id BIGINT NOT NULL REFERENCES commerce.locations(location_id),
    ordered_at TIMESTAMPTZ NOT NULL,
    expected_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('planned', 'in_transit', 'received', 'delayed', 'cancelled'))
);

CREATE TABLE commerce.purchase_order_items (
    purchase_order_item_id BIGSERIAL PRIMARY KEY,
    purchase_order_id BIGINT NOT NULL REFERENCES commerce.purchase_orders(purchase_order_id) ON DELETE CASCADE,
    sku_id BIGINT NOT NULL REFERENCES commerce.skus(sku_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_cost NUMERIC(12,2) NOT NULL CHECK (unit_cost >= 0)
);

CREATE TABLE commerce.campaigns (
    campaign_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    name TEXT NOT NULL,
    channel TEXT NOT NULL CHECK (channel IN ('search', 'social', 'email', 'affiliate', 'display')),
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    spend NUMERIC(14,2) NOT NULL CHECK (spend >= 0)
);

CREATE TABLE commerce.promotions (
    promotion_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    name TEXT NOT NULL,
    discount_type TEXT NOT NULL CHECK (discount_type IN ('percent', 'fixed', 'bundle')),
    discount_value NUMERIC(10,2) NOT NULL CHECK (discount_value >= 0),
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE commerce.sessions (
    session_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    customer_id BIGINT REFERENCES commerce.customers(customer_id),
    region_id BIGINT REFERENCES commerce.regions(region_id),
    started_at TIMESTAMPTZ NOT NULL,
    device TEXT NOT NULL CHECK (device IN ('mobile', 'desktop', 'tablet')),
    converted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE commerce.marketing_events (
    event_id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES commerce.sessions(session_id) ON DELETE CASCADE,
    campaign_id BIGINT REFERENCES commerce.campaigns(campaign_id),
    event_at TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('impression', 'click', 'add_to_cart', 'checkout'))
);

CREATE TABLE commerce.drivers (
    driver_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    home_region_id BIGINT REFERENCES commerce.regions(region_id),
    active_from TIMESTAMPTZ NOT NULL,
    active_to TIMESTAMPTZ
);

CREATE TABLE commerce.deliveries (
    delivery_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    order_id BIGINT NOT NULL UNIQUE REFERENCES commerce.orders(order_id),
    driver_id BIGINT REFERENCES commerce.drivers(driver_id),
    promised_at TIMESTAMPTZ NOT NULL,
    picked_up_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    delivery_status TEXT NOT NULL CHECK (delivery_status IN ('assigned', 'picked_up', 'delivered', 'failed', 'cancelled')),
    delivery_distance_km NUMERIC(8,2) NOT NULL CHECK (delivery_distance_km >= 0)
);

CREATE TABLE commerce.operational_events (
    event_id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES commerce.organizations(organization_id),
    location_id BIGINT REFERENCES commerce.locations(location_id),
    event_at TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    description TEXT NOT NULL
);

CREATE INDEX idx_orders_org_time ON commerce.orders (organization_id, ordered_at);
CREATE INDEX idx_orders_location_time ON commerce.orders (location_id, ordered_at);
CREATE INDEX idx_order_items_sku ON commerce.order_items (sku_id);
CREATE INDEX idx_inventory_location_sku_time ON commerce.inventory_snapshots (location_id, sku_id, snapshot_at);
CREATE INDEX idx_sessions_region_time ON commerce.sessions (region_id, started_at);
CREATE INDEX idx_marketing_events_campaign_time ON commerce.marketing_events (campaign_id, event_at);
CREATE INDEX idx_operational_events_location_time ON commerce.operational_events (location_id, event_at);
