# Stage 1 — Commerce Domain Model

## Design objective

The domain model is intentionally scoped to the three Stage 1 workflows:

1. Business performance investigation
2. Autonomous operational investigation
3. Forecast → decision

It represents shared commerce concepts across e-commerce, food delivery, and quick commerce without pretending that all three industries have identical operations.

## Core entities

### Organization and geography
- `organizations` — tenant/business boundary.
- `regions` — country/state/city hierarchy used for segmentation.
- `locations` — operational fulfillment locations such as warehouse, dark store, restaurant, or store.

### Catalog
- `categories`
- `brands`
- `products`
- `skus`

A product is the commercial concept; an SKU is the inventory/orderable unit.

### Customers
- `customer_segments`
- `customers`

### Commerce
- `orders`
- `order_items`
- `payments`
- `returns`
- `refunds`

Order facts are immutable business events as far as the generator is concerned; status changes are represented by timestamps/status fields rather than overwriting analytical history.

### Inventory
- `inventory_snapshots`
- `purchase_orders`
- `purchase_order_items`

Inventory is location × SKU × time. This is essential for stockout investigations and demand forecasting.

### Marketing and demand signals
- `campaigns`
- `promotions`
- `sessions`
- `marketing_events`

These provide traffic, conversion, discount, and campaign context for performance investigations.

### Fulfillment
- `drivers`
- `deliveries`
- `operational_events`

Delivery/operational data is optional for pure e-commerce scenarios but required to make food-delivery and quick-commerce investigations meaningful.

## Key analytical relationships

```text
Organization
  ├── Regions ── Locations
  ├── Customers ── Customer Segments
  ├── Catalog ── Products ── SKUs
  ├── Orders ── Order Items ── SKUs
  │             └── Payments / Returns / Refunds
  ├── Inventory Snapshots ── Locations × SKUs
  ├── Campaigns / Promotions ── Marketing Events / Sessions
  └── Deliveries ── Orders / Drivers
```

## Intentional omissions in Stage 1

We do not model a full ERP, WMS, accounting system, supplier network, ad-bidding system, or customer-support platform. Those can be represented later through integration adapters if a workflow requires them.

## Synthetic-data realism requirements

The generator must create correlated behavior rather than independent random rows:

- seasonality by date and category
- regional demand differences
- promotion-driven demand changes
- price changes
- stockouts suppressing fulfilled orders
- cancellations and refunds linked to operational conditions
- delivery delays linked to location/time/capacity
- campaign traffic and conversion differences
- deliberate anomalies with known ground truth
- enough noise that root causes are not always trivial

The generator must expose a seed and scenario configuration so every dataset is reproducible.
