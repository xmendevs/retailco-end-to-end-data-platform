# RetailCo Kimball Bus Matrix

| Business Process / Dimension | dim_date | dim_customer | dim_product | dim_store | dim_employee | dim_payment_method |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **fct_sales** (per order line) | ✅ | ✅ | ✅ | ✅ | ✅ | |
| **fct_payments** (per payment) | ✅ | ✅ | | ✅ | | ✅ |
| **fct_inventory_daily** (per product × store × day) | ✅ | | ✅ | ✅ | | |
| **fct_order_lifecycle** (per order) | ✅ | ✅ | | ✅ | ✅ | |

## How to Read This Table
- Each row = a fact table (something that happened in the business)
- Each column = a dimension (who, what, where, when context)
- ✅ = this fact table uses this dimension to add context

## Grain Definitions
- fct_sales: One row per order line item
- fct_payments: One row per payment transaction
- fct_inventory_daily: One row per product per store per day
- fct_order_lifecycle: One row per order (timestamps fill in as status changes)


