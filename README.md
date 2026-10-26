# Shelf Performance Dashboard

Descriptive analytics dashboard for a 200-item retail store, built for the
**FOBA Final Project** at José Rizal University by **Mark Emmanuel Sagarino**
and **Carl Angelo Patano**.

**Audience:** the store manager, who controls assortment and reorder
quantities.

**The question it answers:** how should 200 shelf facings be divided across
eight categories and three price tiers so the shelf earns as much revenue as
possible per peso of capital tied up in stock?

---

## What is on each page

| Page | Business question |
|---|---|
| Shelf performance | Which price tier earns most per shelf facing, and do any categories deserve different treatment? |
| Demand and price | Do customers buy less when an item costs more, and is any tier taking more shelf than it earns? |
| Trend | When does the revenue arrive, and is the shelf decision seasonal? |
| Shelf optimiser | How much more would the shelf earn if the mix changed, and what does each extra peso of stock buy? |
| Data | The aggregates behind every chart, downloadable as CSV |

Four headline figures sit above every page. Three filters — date, category and
price tier — recompute everything, including the note under each chart.

The **Shelf optimiser** page deliberately always uses the whole store,
whatever the filters are set to: the shelf is allocated as one decision across
all 200 facings, so optimising a filtered slice would recommend a mix the
manager could not actually put on the shelf. The page says so on screen.

---

## Running it locally

```
pip install -r requirements.txt
streamlit run app.py
```

On Windows use `py -m pip install -r requirements.txt` and
`py -m streamlit run app.py`. Streamlit is a server, so `python app.py` and
VS Code's Run button will not work.

Keep `app.py` and the `data` folder together — the app resolves the dataset
relative to its own location.

---

## Data

`data/retail_store_sales_model_ready.csv` — 12,575 transactions,
1 January 2022 to 18 January 2025, 48 columns.

604 transactions carry no quantity and therefore no revenue. They are
**excluded from every revenue figure rather than imputed**, and the exclusion
is flagged on screen. The gaps are spread evenly across categories
(χ² = 5.7750, p = 0.5663) and price tiers (χ² = 0.4071, p = 0.8158), so
dropping them does not bias any group.

Capital figures rest on two stated assumptions that are **not** in the
dataset: a shelf facing holds 40 units of stock regardless of price, and
wholesale cost is 70% of shelf price. Both are declared in the sidebar.
