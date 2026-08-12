CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE SCHEMA IF NOT EXISTS commerce;

SET search_path TO commerce, public;


-- ============================================================
-- ORGANIZATION
-- ============================================================

CREATE TABLE organization (
    organization_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    country_code CHAR(2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- CUSTOMER DOMAIN
-- ============================================================

CREATE TABLE customer_segment (
    customer_segment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    name VARCHAR(100) NOT NULL,
    description TEXT,

    UNIQUE (organization_id, name)
);


CREATE TABLE customer (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    customer_segment_id UUID REFERENCES customer_segment(customer_segment_id),

    external_customer_id VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    country_code CHAR(2),
    city VARCHAR(100),

    acquisition_channel VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (organization_id, external_customer_id)
);


-- ============================================================
-- PRODUCT DOMAIN
-- ============================================================

CREATE TABLE brand (
    brand_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    name VARCHAR(255) NOT NULL,

    UNIQUE (organization_id, name)
);


CREATE TABLE category (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(organization_id),

    parent_category_id UUID REFERENCES category(category_id),
    name VARCHAR(255) NOT NULL,

    UNIQUE (organization_id, parent_category_id, name)
);


CREATE TABLE product (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    brand_id UUID REFERENCES brand(brand_id),
    category_id UUID REFERENCES category(category_id),

    product_name VARCHAR(255) NOT NULL,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (organization_id, product_name)
);


CREATE TABLE sku (
    sku_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    product_id UUID NOT NULL REFERENCES product(product_id),

    sku_code VARCHAR(100) NOT NULL,
    sku_name VARCHAR(255) NOT NULL,

    unit_cost NUMERIC(12,2) NOT NULL DEFAULT 0,
    list_price NUMERIC(12,2) NOT NULL DEFAULT 0,

    weight_grams NUMERIC(10,2),
    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (organization_id, sku_code)
);


-- ============================================================
-- FULFILLMENT LOCATION
-- ============================================================

CREATE TABLE fulfillment_location (
    fulfillment_location_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(organization_id),

    name VARCHAR(255) NOT NULL,
    location_type VARCHAR(50) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(100),
    country_code CHAR(2),

    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),

    active BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (
        location_type IN (
            'WAREHOUSE',
            'DARK_STORE',
            'RETAIL_STORE',
            'RESTAURANT',
            'DISTRIBUTION_CENTER'
        )
    )
);


-- ============================================================
-- INVENTORY DOMAIN
-- ============================================================

CREATE TABLE inventory_snapshot (
    inventory_snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    sku_id UUID NOT NULL REFERENCES sku(sku_id),
    fulfillment_location_id UUID NOT NULL
        REFERENCES fulfillment_location(fulfillment_location_id),

    snapshot_date DATE NOT NULL,

    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER NOT NULL DEFAULT 0,
    quantity_available INTEGER NOT NULL DEFAULT 0,

    reorder_point INTEGER NOT NULL DEFAULT 0,
    safety_stock INTEGER NOT NULL DEFAULT 0,

    UNIQUE (
        organization_id,
        sku_id,
        fulfillment_location_id,
        snapshot_date
    ),

    CHECK (quantity_on_hand >= 0),
    CHECK (quantity_reserved >= 0),
    CHECK (quantity_available >= 0)
);


CREATE TABLE inventory_movement (
    inventory_movement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    sku_id UUID NOT NULL REFERENCES sku(sku_id),
    fulfillment_location_id UUID NOT NULL
        REFERENCES fulfillment_location(fulfillment_location_id),

    movement_type VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    reference_type VARCHAR(100),
    reference_id UUID,

    CHECK (
        movement_type IN (
            'PURCHASE',
            'SALE',
            'RETURN',
            'TRANSFER_IN',
            'TRANSFER_OUT',
            'ADJUSTMENT',
            'DAMAGE',
            'EXPIRY'
        )
    )
);


-- ============================================================
-- ORDER DOMAIN
-- ============================================================

CREATE TABLE customer_order (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    customer_id UUID NOT NULL REFERENCES customer(customer_id),

    fulfillment_location_id UUID
        REFERENCES fulfillment_location(fulfillment_location_id),

    order_number VARCHAR(100) NOT NULL,

    order_status VARCHAR(50) NOT NULL,

    currency CHAR(3) NOT NULL DEFAULT 'INR',

    subtotal_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    delivery_fee NUMERIC(14,2) NOT NULL DEFAULT 0,
    tax_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_amount NUMERIC(14,2) NOT NULL DEFAULT 0,

    ordered_at TIMESTAMPTZ NOT NULL,
    cancelled_at TIMESTAMPTZ,

    UNIQUE (organization_id, order_number),

    CHECK (
        order_status IN (
            'PENDING',
            'CONFIRMED',
            'PROCESSING',
            'SHIPPED',
            'OUT_FOR_DELIVERY',
            'DELIVERED',
            'CANCELLED',
            'RETURNED'
        )
    )
);


CREATE TABLE order_item (
    order_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    order_id UUID NOT NULL REFERENCES customer_order(order_id),
    sku_id UUID NOT NULL REFERENCES sku(sku_id),

    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0,

    CHECK (quantity > 0),
    CHECK (unit_price >= 0),
    CHECK (discount_amount >= 0)
);


-- ============================================================
-- PAYMENT DOMAIN
-- ============================================================

CREATE TABLE payment (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    order_id UUID NOT NULL REFERENCES customer_order(order_id),

    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(50) NOT NULL,

    amount NUMERIC(14,2) NOT NULL,
    transaction_reference VARCHAR(255),

    paid_at TIMESTAMPTZ,

    CHECK (
        payment_status IN (
            'PENDING',
            'AUTHORIZED',
            'CAPTURED',
            'FAILED',
            'REFUNDED'
        )
    )
);


CREATE TABLE refund (
    refund_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    order_id UUID NOT NULL REFERENCES customer_order(order_id),
    payment_id UUID REFERENCES payment(payment_id),

    amount NUMERIC(14,2) NOT NULL,
    reason VARCHAR(255),

    refunded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (amount >= 0)
);


CREATE TABLE customer_return (
    return_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    order_id UUID NOT NULL REFERENCES customer_order(order_id),

    return_status VARCHAR(50) NOT NULL,
    reason VARCHAR(255),

    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);


-- ============================================================
-- DELIVERY DOMAIN
-- ============================================================

CREATE TABLE driver (
    driver_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),

    external_driver_id VARCHAR(100),
    city VARCHAR(100),

    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',

    CHECK (
        status IN (
            'ACTIVE',
            'INACTIVE',
            'SUSPENDED'
        )
    ),

    UNIQUE (organization_id, external_driver_id)
);


CREATE TABLE delivery (
    delivery_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    order_id UUID NOT NULL REFERENCES customer_order(order_id),
    driver_id UUID REFERENCES driver(driver_id),

    delivery_status VARCHAR(50) NOT NULL,

    promised_at TIMESTAMPTZ,
    dispatched_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,

    delivery_distance_km NUMERIC(10,2),

    CHECK (
        delivery_status IN (
            'PENDING',
            'ASSIGNED',
            'PICKED_UP',
            'IN_TRANSIT',
            'DELIVERED',
            'FAILED',
            'CANCELLED'
        )
    )
);


-- ============================================================
-- MARKETING DOMAIN
-- ============================================================

CREATE TABLE campaign (
    campaign_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),

    name VARCHAR(255) NOT NULL,
    channel VARCHAR(100) NOT NULL,

    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ,

    budget_amount NUMERIC(14,2),

    UNIQUE (organization_id, name)
);


CREATE TABLE promotion (
    promotion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),

    name VARCHAR(255) NOT NULL,
    promotion_type VARCHAR(50) NOT NULL,

    discount_percentage NUMERIC(5,2),
    discount_amount NUMERIC(12,2),

    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ,

    UNIQUE (organization_id, name)
);


CREATE TABLE coupon (
    coupon_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    promotion_id UUID REFERENCES promotion(promotion_id),

    coupon_code VARCHAR(100) NOT NULL,
    usage_limit INTEGER,

    UNIQUE (organization_id, coupon_code)
);


-- ============================================================
-- CUSTOMER BEHAVIOR DOMAIN
-- ============================================================

CREATE TABLE customer_session (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    customer_id UUID REFERENCES customer(customer_id),

    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,

    acquisition_channel VARCHAR(100),
    device_type VARCHAR(50),
    city VARCHAR(100)
);


CREATE TABLE search_event (
    search_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    session_id UUID REFERENCES customer_session(session_id),
    customer_id UUID REFERENCES customer(customer_id),

    search_query TEXT NOT NULL,
    results_count INTEGER,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE click_event (
    click_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    session_id UUID REFERENCES customer_session(session_id),
    customer_id UUID REFERENCES customer(customer_id),
    sku_id UUID REFERENCES sku(sku_id),

    page_type VARCHAR(100),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE impression (
    impression_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    session_id UUID REFERENCES customer_session(session_id),
    customer_id UUID REFERENCES customer(customer_id),
    sku_id UUID REFERENCES sku(sku_id),
    campaign_id UUID REFERENCES campaign(campaign_id),

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- REVIEWS
-- ============================================================

CREATE TABLE review (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    customer_id UUID NOT NULL REFERENCES customer(customer_id),
    sku_id UUID NOT NULL REFERENCES sku(sku_id),
    order_id UUID REFERENCES customer_order(order_id),

    rating INTEGER NOT NULL,
    review_text TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (rating BETWEEN 1 AND 5)
);


-- ============================================================
-- SUPPLY CHAIN DOMAIN
-- ============================================================

CREATE TABLE supplier (
    supplier_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),

    name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    country_code CHAR(2),

    UNIQUE (organization_id, name)
);


CREATE TABLE purchase_order (
    purchase_order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    supplier_id UUID NOT NULL REFERENCES supplier(supplier_id),
    fulfillment_location_id UUID
        REFERENCES fulfillment_location(fulfillment_location_id),

    purchase_order_number VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,

    ordered_at TIMESTAMPTZ NOT NULL,
    expected_at TIMESTAMPTZ,

    UNIQUE (organization_id, purchase_order_number)
);


CREATE TABLE purchase_order_item (
    purchase_order_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    purchase_order_id UUID NOT NULL
        REFERENCES purchase_order(purchase_order_id),
    sku_id UUID NOT NULL REFERENCES sku(sku_id),

    quantity_ordered INTEGER NOT NULL,
    unit_cost NUMERIC(12,2) NOT NULL,

    CHECK (quantity_ordered > 0),
    CHECK (unit_cost >= 0)
);


CREATE TABLE shipment (
    shipment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),
    purchase_order_id UUID REFERENCES purchase_order(purchase_order_id),

    shipment_status VARCHAR(50) NOT NULL,

    shipped_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ
);


-- ============================================================
-- OPERATIONAL EVENTS
-- ============================================================

CREATE TABLE operational_event (
    operational_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    organization_id UUID NOT NULL REFERENCES organization(organization_id),

    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,

    location_id UUID
        REFERENCES fulfillment_location(fulfillment_location_id),

    description TEXT,

    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,

    metadata JSONB NOT NULL DEFAULT '{}'::JSONB
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_customer_organization
    ON customer (organization_id);

CREATE INDEX idx_order_customer
    ON customer_order (customer_id);

CREATE INDEX idx_order_ordered_at
    ON customer_order (ordered_at);

CREATE INDEX idx_order_location
    ON customer_order (fulfillment_location_id);

CREATE INDEX idx_order_item_order
    ON order_item (order_id);

CREATE INDEX idx_order_item_sku
    ON order_item (sku_id);

CREATE INDEX idx_inventory_sku_location_date
    ON inventory_snapshot (
        sku_id,
        fulfillment_location_id,
        snapshot_date
    );

CREATE INDEX idx_inventory_movement_sku_time
    ON inventory_movement (
        sku_id,
        occurred_at
    );

CREATE INDEX idx_delivery_order
    ON delivery (order_id);

CREATE INDEX idx_delivery_status
    ON delivery (delivery_status);

CREATE INDEX idx_campaign_time
    ON campaign (start_at, end_at);

CREATE INDEX idx_session_customer
    ON customer_session (customer_id);

CREATE INDEX idx_search_time
    ON search_event (occurred_at);

CREATE INDEX idx_operational_event_time
    ON operational_event (started_at);