# Frontend Implementation Guide

This document describes recent backend API changes and how to implement them in the frontend.

## New API Endpoints

### `GET /api/currencies/`
Returns the list of supported currencies.

**Response:**
```json
{
  "currencies": [
    {"code": "NGN", "name": "Nigerian Naira", "symbol": "₦"},
    {"code": "USD", "name": "US Dollar", "symbol": "$"},
    {"code": "KES", "name": "Kenyan Shilling", "symbol": "KSh"},
    {"code": "GHS", "name": "Ghanaian Cedi", "symbol": "GH₵"},
    {"code": "ZAR", "name": "South African Rand", "symbol": "R"},
    {"code": "GBP", "name": "British Pound", "symbol": "£"},
    {"code": "EUR", "name": "Euro", "symbol": "€"}
  ]
}
```

### `GET /api/finance-categories/`
Returns transaction categories grouped by type.

**Response:**
```json
{
  "expense": [
    {"key": "feed", "label": "Feed"},
    {"key": "medication", "label": "Medication"},
    {"key": "equipment", "label": "Equipment"},
    {"key": "labor", "label": "Labor"},
    {"key": "utilities", "label": "Utilities"},
    {"key": "bird_purchase", "label": "Bird Purchase"},
    {"key": "other", "label": "Other"}
  ],
  "income": [
    {"key": "egg_sales", "label": "Egg Sales"},
    {"key": "bird_sales", "label": "Bird Sales"},
    {"key": "manure_sales", "label": "Manure Sales"},
    {"key": "other", "label": "Other"}
  ]
}
```

Use this to populate category dropdowns in the transaction form. Filter by the selected transaction type (income/expense) to show only relevant categories. Fetch once on app init and cache locally — categories rarely change.

### `GET /api/exchange-rates/`
Returns the latest exchange rate per currency pair.

**Response:**
```json
{
  "rates": [
    {"base_currency": "USD", "target_currency": "NGN", "rate": "1580.50000000", "fetched_at": "2026-06-14T00:00:00Z"},
    {"base_currency": "USD", "target_currency": "KES", "rate": "129.25000000", "fetched_at": "2026-06-14T00:00:00Z"}
  ]
}
```

## Changed API Responses

### Login (`POST /api/token/`)
The `farm` object in the login response now includes `base_currency`:
```json
{
  "access": "...",
  "refresh": "...",
  "farm": {
    "id": 1,
    "name": "Fortuna Farms",
    "code": "A1B2C3D4",
    "owner": 1,
    "base_currency": "NGN",
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

### Transaction responses
Every transaction now includes `currency`, and when a currency conversion happened on write, `original_amount` and `original_currency` are populated:
```json
{
  "id": 1,
  "amount": "135949.46",
  "currency": "NGN",
  "original_amount": "100.00",
  "original_currency": "USD",
  "type": "expense",
  "category": "feed",
  ...
}
```
When no conversion happened, `original_amount` and `original_currency` are `null`.

### FeedLog / HealthLog responses
These now include `currency` alongside `cost`, plus `original_cost` and `original_currency` when a conversion happened on write. Same pattern as transactions — `null` when no conversion.

### Flock responses
Flocks include a `currency` field for their summary stats (total_feed_cost, total_income, etc.).

## Display Currency Conversion via `?currency=`

All financial endpoints accept an optional `?currency=XXX` query parameter:
- `GET /api/transactions/?currency=USD`
- `GET /api/transactions/analytics/?currency=USD`
- `GET /api/flocks/?currency=USD`
- `GET /api/flocks/cycle_comparison/?currency=USD`
- `GET /api/feed-logs/?currency=USD`
- `GET /api/health-logs/?currency=USD`

When provided, all monetary values are converted to the requested currency. The response includes extra fields when conversion happens:
```json
{
  "id": 1,
  "amount": "126.50",
  "currency": "NGN",
  "display_currency": "USD",
  "original_currency": "NGN",
  ...
}
```

The `analytics` and `cycle_comparison` endpoints include a `currency` field in the response indicating which currency the figures are in.

When `?currency=` is **not** provided, amounts are returned in their original stored currency (default: the farm's base currency).

## Farm Base Currency

The farm owner (superuser) can change the farm's operating currency:
```
PATCH /api/farms/{id}/
{"base_currency": "KES"}
```

New transactions, feed logs, and health logs default to the farm's `base_currency` if no `currency` is specified in the POST body.

---

## Frontend Implementation Steps

### 1. App State

Store these in your global state (Context/Redux/Zustand):
- `farmBaseCurrency`: from the login response `farm.base_currency`
- `displayCurrency`: user's viewing preference, defaults to `farmBaseCurrency`. Persist in `AsyncStorage` so it survives app restarts.
- `supportedCurrencies`: fetched once from `GET /api/currencies/` on app init

### 2. Currency Formatting Utility

Create a `formatCurrency(amount, currencyCode)` function that prepends the symbol and formats with 2 decimal places. Use this everywhere amounts are displayed — replace any hardcoded `₦` symbols.

```javascript
const CURRENCY_SYMBOLS = { NGN: '₦', USD: '$', KES: 'KSh', GHS: 'GH₵', ZAR: 'R', GBP: '£', EUR: '€' };

export function formatCurrency(amount, currencyCode) {
  const symbol = CURRENCY_SYMBOLS[currencyCode] || currencyCode;
  return `${symbol}${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
```

### 3. API Call Pattern

When the user's `displayCurrency` differs from `farmBaseCurrency`, append `?currency=<displayCurrency>` to all financial API calls. When they match, omit the param (backend returns base currency values by default).

```javascript
function buildFinancialUrl(baseUrl, params = {}) {
  const url = new URL(baseUrl);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  if (displayCurrency !== farmBaseCurrency) {
    url.searchParams.set('currency', displayCurrency);
  }
  return url.toString();
}
```

### 4. Currency Selector Component

Build a reusable `CurrencyPicker` component (dropdown/bottom sheet) showing the supported currencies list. Used in two places:

**A) Farm Settings screen** — lets the farm owner (superuser only) change the farm's operating currency. Sends `PATCH /api/farms/{id}/` with `{ "base_currency": "KES" }`. This is a one-time setup, not frequently changed.

**B) Display currency switcher** — a small pill/icon in the dashboard header or a global setting. Lets any user switch the display currency for viewing. This does NOT change the farm's base currency — it only changes the `?currency=` param on API requests. Store in `AsyncStorage`.

### 5. Forms (Creating Transactions, Feed Logs, Health Logs)

- The amount/cost input field should show the farm's base currency symbol next to it
- Default the currency to the farm's base currency — do NOT add a currency picker to every form
- For the rare case of foreign-currency entries (e.g., importing feed paid in USD), add an optional "Currency" selector below the amount field that defaults to the farm's base currency
- Send the `currency` field in the POST body when it differs from the default

### 6. Display When Conversion Is Active

When the backend returns `display_currency` and `original_currency` in a response (meaning conversion happened), show a subtle indicator:
- Prefix converted amounts with "≈" (approximately)
- Show a banner or note on the screen: "Amounts shown in USD (converted from NGN)"
- Optionally show the original amount on tap/long-press

### 7. Screens to Update

| Screen | What changes |
|--------|-------------|
| **Dashboard** | Add currency switcher in header. All income/expense totals use `formatCurrency()`. Re-fetch data when currency changes. Show "All amounts in XXX" label. |
| **Transaction list** | Each row shows amount with currency symbol. All amounts convert when display currency is active. |
| **Transaction form** | Amount field shows currency symbol. Optional currency picker for foreign entries. |
| **Flock detail** | Summary stats (feed cost, health cost, income, expense) use `formatCurrency()`. |
| **Cycle comparison** | All financial columns formatted with currency. Include currency in column headers. |
| **Feed log / Health log forms** | Cost field shows currency symbol. |
| **Feed log / Health log lists** | Cost column uses `formatCurrency()`. |
| **Farm settings** | New "Base Currency" picker (superuser only). |
| **Analytics/charts** | Y-axis labels and tooltips use `formatCurrency()`. Include currency code in chart title. |
| **Reports/exports** | If generating PDF/CSV, include currency code in column headers. |

### 8. Edge Cases

- **No exchange rates yet** (fresh deployment or API down): the `?currency=` conversion will fail. Handle gracefully — fall back to showing amounts in their original currency with a message like "Exchange rates unavailable".
- **Mixed currencies in a farm**: possible if the farm owner changes base currency mid-operation. Old records keep their original currency, new ones get the new base. Display conversion works regardless since each record stores its own currency.
- **Offline**: cache the last-known currency preference and supported currencies list locally. Conversion only works via API calls, so offline mode shows original currencies.
- **Currency change on farm**: when a superuser changes the farm's `base_currency`, update `farmBaseCurrency` in app state. New records will use the new currency. Old records are unaffected.
