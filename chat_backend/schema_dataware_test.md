# Database Schema: dataware_test
**Extracted:** 2025-08-21 15:20:29

## Overview
- **Total Tables:** 17

## Table of Contents
- [Tables](#tables)
- [Relationship Paths](#relationship-paths)

## Tables

### `public.dim_campaign`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `campaign_id` | integer | ✗ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `campaign_name` | text | ✓ |
| `start_date` | date | ✓ |
| `end_date` | date | ✓ |
| `platform` | text | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.dim_category`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `category_id` | integer | ✗ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `category_name` | text | ✓ |
| `department` | text | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.dim_country`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `country_id` | integer | ✗ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `country_name` | text | ✓ |
| `continent` | text | ✓ |
| `currency` | text | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.dim_customer`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `customer_id` | integer | ✗ |

**Foreign Keys:**

| Column | Type | References | Nullable |
|--------|------|------------|----------|
| `country_id` | integer | `dim_country.country_id` | ✓ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `first_name` | text | ✓ |
| `last_name` | text | ✓ |
| `gender` | text | ✓ |
| `birth_date` | date | ✓ |
| `email` | text | ✓ |
| `phone` | text | ✓ |
| `registration_date` | date | ✓ |
| `segment` | text | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.dim_date`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `date_id` | integer | ✗ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `full_date` | date | ✗ |
| `day` | integer | ✓ |
| `week` | integer | ✓ |
| `month` | integer | ✓ |
| `month_name` | text | ✓ |
| `quarter` | integer | ✓ |
| `year` | integer | ✓ |
| `is_weekend` | boolean | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.dim_device`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `device_id` | integer | ✗ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `device_type` | text | ✓ |
| `os` | text | ✓ |
| `browser` | text | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.dim_payment_method`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `payment_method_id` | integer | ✗ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `method_name` | text | ✓ |
| `provider` | text | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.dim_product`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `product_id` | integer | ✗ |

**Foreign Keys:**

| Column | Type | References | Nullable |
|--------|------|------------|----------|
| `category_id` | integer | `dim_category.category_id` | ✓ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `product_name` | text | ✓ |
| `sku` | text | ✓ |
| `brand` | text | ✓ |
| `cost_price` | numeric | ✓ |
| `selling_price` | numeric | ✓ |
| `is_active` | boolean | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.dim_shipping`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `shipping_id` | integer | ✗ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `shipping_method` | text | ✓ |
| `carrier` | text | ✓ |
| `shipping_speed` | text | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.dim_store`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `store_id` | integer | ✗ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `store_name` | text | ✓ |
| `store_type` | text | ✓ |
| `location` | text | ✓ |
| `region` | text | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.fact_inventory`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `inventory_id` | integer | ✗ |

**Foreign Keys:**

| Column | Type | References | Nullable |
|--------|------|------------|----------|
| `date_id` | integer | `dim_date.date_id` | ✓ |
| `product_id` | integer | `dim_product.product_id` | ✓ |
| `store_id` | integer | `dim_store.store_id` | ✓ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `stock_level` | integer | ✓ |
| `restock_flag` | boolean | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.fact_marketing`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `marketing_id` | integer | ✗ |

**Foreign Keys:**

| Column | Type | References | Nullable |
|--------|------|------------|----------|
| `date_id` | integer | `dim_date.date_id` | ✓ |
| `campaign_id` | integer | `dim_campaign.campaign_id` | ✓ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `impressions` | integer | ✓ |
| `clicks` | integer | ✓ |
| `conversions` | integer | ✓ |
| `spend` | numeric | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.fact_payments`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `payment_id` | integer | ✗ |

**Foreign Keys:**

| Column | Type | References | Nullable |
|--------|------|------------|----------|
| `sale_id` | integer | `fact_sales.sale_id` | ✓ |
| `payment_method_id` | integer | `dim_payment_method.payment_method_id` | ✓ |
| `date_id` | integer | `dim_date.date_id` | ✓ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `status` | text | ✓ |
| `transaction_fee` | numeric | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.fact_returns`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `return_id` | integer | ✗ |

**Foreign Keys:**

| Column | Type | References | Nullable |
|--------|------|------------|----------|
| `sale_id` | integer | `fact_sales.sale_id` | ✓ |
| `return_date_id` | integer | `dim_date.date_id` | ✓ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `reason` | text | ✓ |
| `refund_amount` | numeric | ✓ |
| `is_fraud` | boolean | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.fact_sales`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `sale_id` | integer | ✗ |

**Foreign Keys:**

| Column | Type | References | Nullable |
|--------|------|------------|----------|
| `date_id` | integer | `dim_date.date_id` | ✓ |
| `customer_id` | integer | `dim_customer.customer_id` | ✓ |
| `product_id` | integer | `dim_product.product_id` | ✓ |
| `store_id` | integer | `dim_store.store_id` | ✓ |
| `shipping_id` | integer | `dim_shipping.shipping_id` | ✓ |
| `payment_method_id` | integer | `dim_payment_method.payment_method_id` | ✓ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `quantity` | integer | ✓ |
| `unit_price` | numeric | ✓ |
| `total_amount` | numeric | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.fact_traffic`

#### Columns

**Primary Keys:**

| Column | Type | Nullable |
|--------|------|----------|
| `traffic_id` | integer | ✗ |

**Foreign Keys:**

| Column | Type | References | Nullable |
|--------|------|------------|----------|
| `date_id` | integer | `dim_date.date_id` | ✓ |
| `customer_id` | integer | `dim_customer.customer_id` | ✓ |
| `device_id` | integer | `dim_device.device_id` | ✓ |

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `page_visited` | text | ✓ |
| `duration_seconds` | integer | ✓ |
| `embedding` | USER-DEFINED | ✓ |

---

### `public.schema_metadata`

#### Columns

**Other Columns:**

| Column | Type | Nullable |
|--------|------|----------|
| `table_name` | text | ✗ |
| `column_name` | text | ✓ |
| `description` | text | ✗ |
| `metadata_type` | text | ✓ |

---

## Relationship Paths

Pre-calculated paths between all tables for query optimization.

### From `dim_campaign`

| Destination | Path |
|-------------|------|
| `dim_date` | `dim_campaign(` campaign_id `) → `public.fact_marketing(` date_id `) → `dim_date(` date_id `)` |
| `public.fact_inventory` | `dim_campaign(` campaign_id `) → `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` date_id `)` |
| `public.fact_marketing` | `dim_campaign(` campaign_id `) → `public.fact_marketing(` campaign_id `)` |
| `public.fact_payments` | `dim_campaign(` campaign_id `) → `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` date_id `)` |
| `public.fact_returns` | `dim_campaign(` campaign_id `) → `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_returns(` return_date_id `)` |
| `public.fact_sales` | `dim_campaign(` campaign_id `) → `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_sales(` date_id `)` |
| `public.fact_traffic` | `dim_campaign(` campaign_id `) → `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` date_id `)` |

### From `dim_category`

| Destination | Path |
|-------------|------|
| `public.dim_product` | `dim_category(` category_id `) → `public.dim_product(` category_id `)` |

### From `dim_country`

| Destination | Path |
|-------------|------|
| `public.dim_customer` | `dim_country(` country_id `) → `public.dim_customer(` country_id `)` |

### From `dim_customer`

| Destination | Path |
|-------------|------|
| `dim_date` | `dim_customer(` customer_id `) → `public.fact_sales(` date_id `) → `dim_date(` date_id `)` |
| `dim_device` | `dim_customer(` customer_id `) → `public.fact_traffic(` device_id `) → `dim_device(` device_id `)` |
| `dim_payment_method` | `dim_customer(` customer_id `) → `public.fact_sales(` payment_method_id `) → `dim_payment_method(` payment_method_id `)` |
| `dim_product` | `dim_customer(` customer_id `) → `public.fact_sales(` product_id `) → `dim_product(` product_id `)` |
| `dim_shipping` | `dim_customer(` customer_id `) → `public.fact_sales(` shipping_id `) → `dim_shipping(` shipping_id `)` |
| `dim_store` | `dim_customer(` customer_id `) → `public.fact_sales(` store_id `) → `dim_store(` store_id `)` |
| `public.fact_inventory` | `dim_customer(` customer_id `) → `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` date_id `)` |
| `public.fact_marketing` | `dim_customer(` customer_id `) → `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_payments` | `dim_customer(` customer_id `) → `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` date_id `)` |
| `public.fact_returns` | `dim_customer(` customer_id `) → `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_returns(` return_date_id `)` |
| `public.fact_sales` | `dim_customer(` customer_id `) → `public.fact_sales(` customer_id `)` |
| `public.fact_traffic` | `dim_customer(` customer_id `) → `public.fact_traffic(` customer_id `)` |

### From `dim_date`

| Destination | Path |
|-------------|------|
| `dim_campaign` | `dim_date(` date_id `) → `public.fact_marketing(` campaign_id `) → `dim_campaign(` campaign_id `)` |
| `dim_customer` | `dim_date(` date_id `) → `public.fact_sales(` customer_id `) → `dim_customer(` customer_id `)` |
| `dim_device` | `dim_date(` date_id `) → `public.fact_traffic(` device_id `) → `dim_device(` device_id `)` |
| `dim_payment_method` | `dim_date(` date_id `) → `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `)` |
| `dim_product` | `dim_date(` date_id `) → `public.fact_inventory(` product_id `) → `dim_product(` product_id `)` |
| `dim_shipping` | `dim_date(` date_id `) → `public.fact_sales(` shipping_id `) → `dim_shipping(` shipping_id `)` |
| `dim_store` | `dim_date(` date_id `) → `public.fact_inventory(` store_id `) → `dim_store(` store_id `)` |
| `fact_sales` | `dim_date(` date_id `) → `public.fact_payments(` sale_id `) → `fact_sales(` sale_id `)` |
| `public.fact_inventory` | `dim_date(` date_id `) → `public.fact_inventory(` date_id `)` |
| `public.fact_marketing` | `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_payments` | `dim_date(` date_id `) → `public.fact_payments(` date_id `)` |
| `public.fact_returns` | `dim_date(` date_id `) → `public.fact_returns(` return_date_id `)` |
| `public.fact_sales` | `dim_date(` date_id `) → `public.fact_sales(` date_id `)` |
| `public.fact_traffic` | `dim_date(` date_id `) → `public.fact_traffic(` date_id `)` |

### From `dim_device`

| Destination | Path |
|-------------|------|
| `dim_customer` | `dim_device(` device_id `) → `public.fact_traffic(` customer_id `) → `dim_customer(` customer_id `)` |
| `dim_date` | `dim_device(` device_id `) → `public.fact_traffic(` date_id `) → `dim_date(` date_id `)` |
| `public.fact_inventory` | `dim_device(` device_id `) → `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` date_id `)` |
| `public.fact_marketing` | `dim_device(` device_id `) → `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_payments` | `dim_device(` device_id `) → `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` date_id `)` |
| `public.fact_returns` | `dim_device(` device_id `) → `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_returns(` return_date_id `)` |
| `public.fact_sales` | `dim_device(` device_id `) → `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_sales(` date_id `)` |
| `public.fact_traffic` | `dim_device(` device_id `) → `public.fact_traffic(` device_id `)` |

### From `dim_payment_method`

| Destination | Path |
|-------------|------|
| `dim_customer` | `dim_payment_method(` payment_method_id `) → `public.fact_sales(` customer_id `) → `dim_customer(` customer_id `)` |
| `dim_date` | `dim_payment_method(` payment_method_id `) → `public.fact_payments(` date_id `) → `dim_date(` date_id `)` |
| `dim_product` | `dim_payment_method(` payment_method_id `) → `public.fact_sales(` product_id `) → `dim_product(` product_id `)` |
| `dim_shipping` | `dim_payment_method(` payment_method_id `) → `public.fact_sales(` shipping_id `) → `dim_shipping(` shipping_id `)` |
| `dim_store` | `dim_payment_method(` payment_method_id `) → `public.fact_sales(` store_id `) → `dim_store(` store_id `)` |
| `fact_sales` | `dim_payment_method(` payment_method_id `) → `public.fact_payments(` sale_id `) → `fact_sales(` sale_id `)` |
| `public.fact_inventory` | `dim_payment_method(` payment_method_id `) → `public.fact_payments(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` date_id `)` |
| `public.fact_marketing` | `dim_payment_method(` payment_method_id `) → `public.fact_payments(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_payments` | `dim_payment_method(` payment_method_id `) → `public.fact_payments(` payment_method_id `)` |
| `public.fact_returns` | `dim_payment_method(` payment_method_id `) → `public.fact_payments(` sale_id `) → `fact_sales(` sale_id `) → `public.fact_returns(` sale_id `)` |
| `public.fact_sales` | `dim_payment_method(` payment_method_id `) → `public.fact_sales(` payment_method_id `)` |
| `public.fact_traffic` | `dim_payment_method(` payment_method_id `) → `public.fact_payments(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` date_id `)` |

### From `dim_product`

| Destination | Path |
|-------------|------|
| `dim_customer` | `dim_product(` product_id `) → `public.fact_sales(` customer_id `) → `dim_customer(` customer_id `)` |
| `dim_date` | `dim_product(` product_id `) → `public.fact_inventory(` date_id `) → `dim_date(` date_id `)` |
| `dim_payment_method` | `dim_product(` product_id `) → `public.fact_sales(` payment_method_id `) → `dim_payment_method(` payment_method_id `)` |
| `dim_shipping` | `dim_product(` product_id `) → `public.fact_sales(` shipping_id `) → `dim_shipping(` shipping_id `)` |
| `dim_store` | `dim_product(` product_id `) → `public.fact_inventory(` store_id `) → `dim_store(` store_id `)` |
| `public.fact_inventory` | `dim_product(` product_id `) → `public.fact_inventory(` product_id `)` |
| `public.fact_marketing` | `dim_product(` product_id `) → `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_payments` | `dim_product(` product_id `) → `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` date_id `)` |
| `public.fact_returns` | `dim_product(` product_id `) → `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_returns(` return_date_id `)` |
| `public.fact_sales` | `dim_product(` product_id `) → `public.fact_sales(` product_id `)` |
| `public.fact_traffic` | `dim_product(` product_id `) → `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` date_id `)` |

### From `dim_shipping`

| Destination | Path |
|-------------|------|
| `dim_customer` | `dim_shipping(` shipping_id `) → `public.fact_sales(` customer_id `) → `dim_customer(` customer_id `)` |
| `dim_date` | `dim_shipping(` shipping_id `) → `public.fact_sales(` date_id `) → `dim_date(` date_id `)` |
| `dim_payment_method` | `dim_shipping(` shipping_id `) → `public.fact_sales(` payment_method_id `) → `dim_payment_method(` payment_method_id `)` |
| `dim_product` | `dim_shipping(` shipping_id `) → `public.fact_sales(` product_id `) → `dim_product(` product_id `)` |
| `dim_store` | `dim_shipping(` shipping_id `) → `public.fact_sales(` store_id `) → `dim_store(` store_id `)` |
| `public.fact_inventory` | `dim_shipping(` shipping_id `) → `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` date_id `)` |
| `public.fact_marketing` | `dim_shipping(` shipping_id `) → `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_payments` | `dim_shipping(` shipping_id `) → `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` date_id `)` |
| `public.fact_returns` | `dim_shipping(` shipping_id `) → `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_returns(` return_date_id `)` |
| `public.fact_sales` | `dim_shipping(` shipping_id `) → `public.fact_sales(` shipping_id `)` |
| `public.fact_traffic` | `dim_shipping(` shipping_id `) → `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` date_id `)` |

### From `dim_store`

| Destination | Path |
|-------------|------|
| `dim_customer` | `dim_store(` store_id `) → `public.fact_sales(` customer_id `) → `dim_customer(` customer_id `)` |
| `dim_date` | `dim_store(` store_id `) → `public.fact_inventory(` date_id `) → `dim_date(` date_id `)` |
| `dim_payment_method` | `dim_store(` store_id `) → `public.fact_sales(` payment_method_id `) → `dim_payment_method(` payment_method_id `)` |
| `dim_product` | `dim_store(` store_id `) → `public.fact_inventory(` product_id `) → `dim_product(` product_id `)` |
| `dim_shipping` | `dim_store(` store_id `) → `public.fact_sales(` shipping_id `) → `dim_shipping(` shipping_id `)` |
| `public.fact_inventory` | `dim_store(` store_id `) → `public.fact_inventory(` store_id `)` |
| `public.fact_marketing` | `dim_store(` store_id `) → `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_payments` | `dim_store(` store_id `) → `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` date_id `)` |
| `public.fact_returns` | `dim_store(` store_id `) → `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_returns(` return_date_id `)` |
| `public.fact_sales` | `dim_store(` store_id `) → `public.fact_sales(` store_id `)` |
| `public.fact_traffic` | `dim_store(` store_id `) → `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` date_id `)` |

### From `fact_sales`

| Destination | Path |
|-------------|------|
| `dim_date` | `fact_sales(` sale_id `) → `public.fact_payments(` date_id `) → `dim_date(` date_id `)` |
| `dim_payment_method` | `fact_sales(` sale_id `) → `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `)` |
| `public.fact_inventory` | `fact_sales(` sale_id `) → `public.fact_payments(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` date_id `)` |
| `public.fact_marketing` | `fact_sales(` sale_id `) → `public.fact_payments(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_payments` | `fact_sales(` sale_id `) → `public.fact_payments(` sale_id `)` |
| `public.fact_returns` | `fact_sales(` sale_id `) → `public.fact_returns(` sale_id `)` |
| `public.fact_sales` | `fact_sales(` sale_id `) → `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `) → `public.fact_sales(` payment_method_id `)` |
| `public.fact_traffic` | `fact_sales(` sale_id `) → `public.fact_payments(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` date_id `)` |

### From `public.dim_customer`

| Destination | Path |
|-------------|------|
| `dim_country` | `public.dim_customer(` country_id `) → `dim_country(` country_id `)` |

### From `public.dim_product`

| Destination | Path |
|-------------|------|
| `dim_category` | `public.dim_product(` category_id `) → `dim_category(` category_id `)` |

### From `public.fact_inventory`

| Destination | Path |
|-------------|------|
| `dim_campaign` | `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` campaign_id `) → `dim_campaign(` campaign_id `)` |
| `dim_customer` | `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_sales(` customer_id `) → `dim_customer(` customer_id `)` |
| `dim_date` | `public.fact_inventory(` date_id `) → `dim_date(` date_id `)` |
| `dim_device` | `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` device_id `) → `dim_device(` device_id `)` |
| `dim_payment_method` | `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `)` |
| `dim_product` | `public.fact_inventory(` product_id `) → `dim_product(` product_id `)` |
| `dim_shipping` | `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_sales(` shipping_id `) → `dim_shipping(` shipping_id `)` |
| `dim_store` | `public.fact_inventory(` store_id `) → `dim_store(` store_id `)` |
| `fact_sales` | `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` sale_id `) → `fact_sales(` sale_id `)` |
| `public.fact_marketing` | `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_payments` | `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` date_id `)` |
| `public.fact_returns` | `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_returns(` return_date_id `)` |
| `public.fact_sales` | `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_sales(` date_id `)` |
| `public.fact_traffic` | `public.fact_inventory(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` date_id `)` |

### From `public.fact_marketing`

| Destination | Path |
|-------------|------|
| `dim_campaign` | `public.fact_marketing(` campaign_id `) → `dim_campaign(` campaign_id `)` |
| `dim_customer` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_sales(` customer_id `) → `dim_customer(` customer_id `)` |
| `dim_date` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `)` |
| `dim_device` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` device_id `) → `dim_device(` device_id `)` |
| `dim_payment_method` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `)` |
| `dim_product` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` product_id `) → `dim_product(` product_id `)` |
| `dim_shipping` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_sales(` shipping_id `) → `dim_shipping(` shipping_id `)` |
| `dim_store` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` store_id `) → `dim_store(` store_id `)` |
| `fact_sales` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` sale_id `) → `fact_sales(` sale_id `)` |
| `public.fact_inventory` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` date_id `)` |
| `public.fact_payments` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` date_id `)` |
| `public.fact_returns` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_returns(` return_date_id `)` |
| `public.fact_sales` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_sales(` date_id `)` |
| `public.fact_traffic` | `public.fact_marketing(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` date_id `)` |

### From `public.fact_payments`

| Destination | Path |
|-------------|------|
| `dim_campaign` | `public.fact_payments(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` campaign_id `) → `dim_campaign(` campaign_id `)` |
| `dim_customer` | `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `) → `public.fact_sales(` customer_id `) → `dim_customer(` customer_id `)` |
| `dim_date` | `public.fact_payments(` date_id `) → `dim_date(` date_id `)` |
| `dim_device` | `public.fact_payments(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` device_id `) → `dim_device(` device_id `)` |
| `dim_payment_method` | `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `)` |
| `dim_product` | `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `) → `public.fact_sales(` product_id `) → `dim_product(` product_id `)` |
| `dim_shipping` | `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `) → `public.fact_sales(` shipping_id `) → `dim_shipping(` shipping_id `)` |
| `dim_store` | `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `) → `public.fact_sales(` store_id `) → `dim_store(` store_id `)` |
| `fact_sales` | `public.fact_payments(` sale_id `) → `fact_sales(` sale_id `)` |
| `public.fact_inventory` | `public.fact_payments(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` date_id `)` |
| `public.fact_marketing` | `public.fact_payments(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_returns` | `public.fact_payments(` sale_id `) → `fact_sales(` sale_id `) → `public.fact_returns(` sale_id `)` |
| `public.fact_sales` | `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `) → `public.fact_sales(` payment_method_id `)` |
| `public.fact_traffic` | `public.fact_payments(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` date_id `)` |

### From `public.fact_returns`

| Destination | Path |
|-------------|------|
| `dim_campaign` | `public.fact_returns(` return_date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` campaign_id `) → `dim_campaign(` campaign_id `)` |
| `dim_customer` | `public.fact_returns(` return_date_id `) → `dim_date(` date_id `) → `public.fact_sales(` customer_id `) → `dim_customer(` customer_id `)` |
| `dim_date` | `public.fact_returns(` return_date_id `) → `dim_date(` date_id `)` |
| `dim_device` | `public.fact_returns(` return_date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` device_id `) → `dim_device(` device_id `)` |
| `dim_payment_method` | `public.fact_returns(` sale_id `) → `fact_sales(` sale_id `) → `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `)` |
| `dim_product` | `public.fact_returns(` return_date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` product_id `) → `dim_product(` product_id `)` |
| `dim_shipping` | `public.fact_returns(` return_date_id `) → `dim_date(` date_id `) → `public.fact_sales(` shipping_id `) → `dim_shipping(` shipping_id `)` |
| `dim_store` | `public.fact_returns(` return_date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` store_id `) → `dim_store(` store_id `)` |
| `fact_sales` | `public.fact_returns(` sale_id `) → `fact_sales(` sale_id `)` |
| `public.fact_inventory` | `public.fact_returns(` return_date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` date_id `)` |
| `public.fact_marketing` | `public.fact_returns(` return_date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_payments` | `public.fact_returns(` sale_id `) → `fact_sales(` sale_id `) → `public.fact_payments(` sale_id `)` |
| `public.fact_sales` | `public.fact_returns(` return_date_id `) → `dim_date(` date_id `) → `public.fact_sales(` date_id `)` |
| `public.fact_traffic` | `public.fact_returns(` return_date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` date_id `)` |

### From `public.fact_sales`

| Destination | Path |
|-------------|------|
| `dim_campaign` | `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` campaign_id `) → `dim_campaign(` campaign_id `)` |
| `dim_customer` | `public.fact_sales(` customer_id `) → `dim_customer(` customer_id `)` |
| `dim_date` | `public.fact_sales(` date_id `) → `dim_date(` date_id `)` |
| `dim_device` | `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` device_id `) → `dim_device(` device_id `)` |
| `dim_payment_method` | `public.fact_sales(` payment_method_id `) → `dim_payment_method(` payment_method_id `)` |
| `dim_product` | `public.fact_sales(` product_id `) → `dim_product(` product_id `)` |
| `dim_shipping` | `public.fact_sales(` shipping_id `) → `dim_shipping(` shipping_id `)` |
| `dim_store` | `public.fact_sales(` store_id `) → `dim_store(` store_id `)` |
| `fact_sales` | `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` sale_id `) → `fact_sales(` sale_id `)` |
| `public.fact_inventory` | `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` date_id `)` |
| `public.fact_marketing` | `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_payments` | `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` date_id `)` |
| `public.fact_returns` | `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_returns(` return_date_id `)` |
| `public.fact_traffic` | `public.fact_sales(` date_id `) → `dim_date(` date_id `) → `public.fact_traffic(` date_id `)` |

### From `public.fact_traffic`

| Destination | Path |
|-------------|------|
| `dim_campaign` | `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` campaign_id `) → `dim_campaign(` campaign_id `)` |
| `dim_customer` | `public.fact_traffic(` customer_id `) → `dim_customer(` customer_id `)` |
| `dim_date` | `public.fact_traffic(` date_id `) → `dim_date(` date_id `)` |
| `dim_device` | `public.fact_traffic(` device_id `) → `dim_device(` device_id `)` |
| `dim_payment_method` | `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` payment_method_id `) → `dim_payment_method(` payment_method_id `)` |
| `dim_product` | `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` product_id `) → `dim_product(` product_id `)` |
| `dim_shipping` | `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_sales(` shipping_id `) → `dim_shipping(` shipping_id `)` |
| `dim_store` | `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` store_id `) → `dim_store(` store_id `)` |
| `fact_sales` | `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` sale_id `) → `fact_sales(` sale_id `)` |
| `public.fact_inventory` | `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_inventory(` date_id `)` |
| `public.fact_marketing` | `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_marketing(` date_id `)` |
| `public.fact_payments` | `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_payments(` date_id `)` |
| `public.fact_returns` | `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_returns(` return_date_id `)` |
| `public.fact_sales` | `public.fact_traffic(` date_id `) → `dim_date(` date_id `) → `public.fact_sales(` date_id `)` |

---

*This schema documentation was automatically generated for LLM query optimization.*