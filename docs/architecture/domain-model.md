# Commerce Domain Model

## Purpose

The commerce domain model provides the canonical relational structure for the AI Commerce Intelligence Platform.

The model supports:

- E-commerce
- Quick commerce
- Food delivery

The same core model is shared across all three verticals. Vertical-specific entities or attributes will only be added when a real product requirement justifies them.

---

## Domain Structure

### Customer Domain

```text
Customer
    |
    ├── Customer Segment
    ├── Session
    ├── Search Event
    ├── Click Event
    └── Review
```

A customer represents an individual or account interacting with the commerce platform.

Customer-related behavioral data is stored separately so that sessions, searches, clicks, and reviews can be analyzed independently.

### Product Domain

```text
Brand
    |
Category
    |
Product
    |
SKU
```

A Product represents the commercial product.

An SKU represents a specific sellable variant of that product.

Example:

```text
Product: Coca-Cola
    |
    ├── SKU: Coca-Cola 500ml
    ├── SKU: Coca-Cola 1L
    └── SKU: Coca-Cola 2L
```

Categories support hierarchical relationships.

Example:

```text
Electronics
├── Computers
│   ├── Laptops
│   └── Desktops
├── Mobile
│   ├── Smartphones
│   └── Accessories
```

### Order Domain

```text
Customer
    |
    └── Order
          |
          ├── Order Item
          ├── Payment
          ├── Refund
          ├── Return
          └── Delivery
```

An Order represents the commercial transaction.

An Order Item represents an individual SKU purchased within an order.

Payments, refunds, returns, and deliveries are separate entities because they have independent lifecycles and analytical requirements.

### Inventory Domain

```text
SKU
 |
 └── Inventory Snapshot
          |
          └── Fulfillment Location
```

Inventory is tracked by SKU and fulfillment location.

A fulfillment location can represent:

- Warehouse
- Dark store
- Retail store
- Restaurant
- Distribution center

Inventory movement records capture changes such as:

- Purchases
- Sales
- Returns
- Transfers
- Adjustments
- Damage
- Expiry

### Supply Chain Domain

```text
Supplier
    |
    └── Purchase Order
           |
           ├── Purchase Order Item
           └── Shipment
```

Purchase orders represent procurement activity.

Purchase order items connect procurement activity to specific SKUs.

This allows future analysis of:

- Supplier performance
- Lead times
- Replenishment
- Purchase costs
- Stockout risk
- Supply disruptions

### Marketing Domain

```text
Campaign
    |
    ├── Promotion
    └── Coupon
```

Marketing entities support analysis of:

- Campaign performance
- Promotion effectiveness
- Coupon usage
- Discount impact
- Revenue impact
- Margin impact

Campaigns can later be connected to customer sessions, impressions, clicks, and orders for attribution analysis.

### Customer Behavior Domain

```text
Customer
    |
    └── Session
          |
          ├── Search Event
          ├── Click Event
          └── Impression
```

These events represent customer interaction with the commerce platform.

They allow analysis of:

- Traffic
- Search behavior
- Product discovery
- Conversion
- Campaign exposure
- Customer engagement

### Fulfillment Domain

```text
Order
 |
 └── Delivery
       |
       └── Driver
```

Delivery information allows investigation of:

- Delivery delays
- Failed deliveries
- Driver capacity
- Regional bottlenecks
- Fulfillment performance
- Delivery cost drivers

### Operational Domain

```text
Operational Event
```

Operational events represent business events that may affect multiple domains.

Examples:

- Warehouse outage
- Payment gateway outage
- Inventory system failure
- Delivery capacity reduction
- Pricing system change
- Promotion launch
- Supplier disruption

Operational events are particularly important for root-cause analysis because they provide contextual evidence around business anomalies.

---

## Organization and Multi-Tenancy

```text
Organization
    |
    ├── Customers
    ├── Products
    ├── Orders
    ├── Inventory
    ├── Marketing
    ├── Supply Chain
    └── Operations
```

The platform is designed for multiple organizations.

Business entities contain an `organization_id` so that data can be associated with the correct tenant.

Tenant isolation will ultimately be enforced through:

- Authentication
- RBAC
- Authorization
- Application-level data access controls
- Database-level controls where appropriate

---

## Core Relationship Paths

### Revenue Investigation

```text
Order
  ↓
Order Item
  ↓
SKU
  ↓
Product
  ↓
Category / Brand
```

```text
Order
  ↓
Customer
  ↓
Customer Segment
```

```text
Order
  ↓
Fulfillment Location
```

### Inventory Investigation

```text
SKU
  ↓
Inventory Snapshot
  ↓
Fulfillment Location
```

```text
SKU
  ↓
Order Item
  ↓
Order
```

This allows the system to compare inventory availability against demand.

### Marketing Investigation

```text
Campaign
  ↓
Impression
  ↓
Session
  ↓
Order
  ↓
Revenue
```

```text
Promotion
  ↓
Order
  ↓
Discount
  ↓
Margin
```

### Delivery Investigation

```text
Order
  ↓
Delivery
  ↓
Driver
```

```text
Order
  ↓
Fulfillment Location
```

This allows investigation of geographic and operational delivery problems.

### Supply Investigation

```text
Supplier
  ↓
Purchase Order
  ↓
Purchase Order Item
  ↓
SKU
  ↓
Inventory
```

This allows investigation of replenishment and supplier-related stockout risks.

---

## Data Modeling Principles

### 1. Normalize core transactional data

Use separate relational entities where they have independent business meaning or lifecycle.

### 2. Use foreign keys

Relationships between entities should be explicitly represented using foreign keys.

### 3. Avoid unnecessary tables

Not every attribute requires its own table.

For example:

```text
Order
    order_status
```

is preferable to creating an `OrderStatus` table unless the status itself requires additional metadata or relationships.

### 4. Preserve historical information

Historical records are required for:

- Trend analysis
- Root-cause investigation
- Forecasting
- Anomaly detection
- Scenario analysis

### 5. Separate transactional and analytical concerns

The initial schema represents the canonical commerce domain.

Analytical models, aggregates, semantic metrics, and derived datasets will be introduced later rather than contaminating the transactional model.

### 6. Prefer explicit business relationships

The AI system should be able to discover reliable relationships through the schema rather than relying entirely on LLM assumptions.

### 7. Design for the three initial verticals

The core model should work across:

- E-commerce
- Quick commerce
- Food delivery

Vertical-specific extensions should only be introduced when justified.

### 8. Extend based on product requirements

The domain model is intentionally extensible.

New entities should be introduced when a concrete workflow requires them rather than because they appear in a generic commerce database diagram.

---

## Initial Domain Model

```text
Organization
│
├── Customer
│   ├── Customer Segment
│   ├── Session
│   ├── Search Event
│   ├── Click Event
│   └── Review
│
├── Product
│   ├── Brand
│   ├── Category
│   └── SKU
│
├── Orders
│   ├── Order
│   ├── Order Item
│   ├── Payment
│   ├── Refund
│   ├── Return
│   └── Delivery
│
├── Inventory
│   ├── Fulfillment Location
│   ├── Inventory Snapshot
│   └── Inventory Movement
│
├── Marketing
│   ├── Campaign
│   ├── Promotion
│   └── Coupon
│
├── Supply Chain
│   ├── Supplier
│   ├── Purchase Order
│   ├── Purchase Order Item
│   └── Shipment
│
└── Operations
    └── Operational Event
```

This is the canonical Stage 1 domain foundation.
