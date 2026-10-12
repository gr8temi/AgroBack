# Finance Categories — Frontend Implementation

## New Endpoint

### `GET /api/finance-categories/`
Requires authentication. Returns all transaction categories grouped by type.

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

Note: `"other"` appears in both lists — it's valid for both income and expense transactions.

## What to implement

### 1. Fetch and cache categories

Call `GET /api/finance-categories/` once on app init (or on first visit to the finance screen). Cache the result in memory/state — the list rarely changes. No need to re-fetch on every screen visit.

### 2. Transaction form — dynamic category dropdown

When creating or editing a transaction, the user first selects a **type** (`income` or `expense`). The **category** dropdown should only show categories for the selected type.

```
User selects type: "expense"
  → Show: Feed, Medication, Equipment, Labor, Utilities, Bird Purchase, Other

User selects type: "income"
  → Show: Egg Sales, Bird Sales, Manure Sales, Other

User switches type from "expense" to "income"
  → Reset the category selection (the previous category may not be valid)
```

Use `key` as the value sent to the API, and `label` as the display text.

### 3. Display in transaction lists and analytics

When showing transactions in lists or analytics breakdowns, use the `label` for display. Map the `category` field from the API response (which is the `key`) to its `label`:

```javascript
// Build a lookup map from the fetched categories
const categoryLabels = {};
[...categories.expense, ...categories.income].forEach(c => {
  categoryLabels[c.key] = c.label;
});

// Usage
const displayName = categoryLabels[transaction.category] || transaction.category;
```

### 4. Screens affected

| Screen | Change |
|--------|--------|
| **Add/Edit Transaction form** | Replace any hardcoded category list with the API-driven one. Filter by selected transaction type. |
| **Transaction list** | Use `label` when displaying the category column/tag. |
| **Analytics/Dashboard** | Category breakdowns (expense_by_category, income_by_category) use `key` values — map to `label` for display. |
| **Filters** | If you have category filters on the transaction list, populate them from this endpoint too. |
