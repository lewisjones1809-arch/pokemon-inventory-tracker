# Pokémon Card Inventory Tracker

A full-stack inventory and price tracking tool for a Pokémon card collection. It ingests card data from a live API, tracks price history over time, records purchases and sales, and computes inventory value, margins, and realised profit using FIFO cost-basis accounting all surfaced through an interactive dashboard.

Tested on my real ~3,800 card for-sale collection. Currently only accepts English cards, but other languages will come later down the line.

<!-- Replace with your actual screenshot. A hero image sells the project instantly. -->
![Dashboard](screenshots/dashboard.png)

## What it does

- **Ingests card data** from the Pokémon TCG API, by set, with pagination.
- **Detects variants** (regular / reverse holo) from the card's price data
- **Tracks price history** as an append-only log, so value can be charted over time.
- **Records purchases and sales** as immutable event logs.
- **Derives current inventory** (held quantity per card variant + condition) from those
  logs rather than storing mutable state to prevent drift.
- **Computes valuation**: current market value, unrealised margin, total sales, and
  realised profit using **FIFO cost-basis accounting** (verified against hand-calculated
  test cases).
- **Bulk-imports** an existing collection from a CSV export.
- **Interactive dashboard** (Streamlit): KPI metrics, a visual card grid with images, and
  a data-entry interface for logging new trades.

## Architecture

The project separates concerns into a UI-agnostic logic layer and a thin presentation layer.

**Data model** — a normalised SQLite schema:

- `allCards` — card reference data (name, set, number, image), one row per card.
- `cardVariants` — a sellable version of a card (e.g. reverse holo), keyed to a card.
- `priceHistory` — append-only price log, one row per variant per capture.
- `purchases` / `sales` — immutable event logs of trades.
- `listedPrices` — user-set asking prices per variant + condition.
- `importedSets` - tracks all sets that have been returned from the API and stored in the database.

Current inventory is *derived* from purchases minus sales, joined to the latest price. This keeps a single source of truth and makes state recomputable.

**Flow:** ingest cards by set -> capture prices -> record trades -> derive inventory -> calculate valuation -> display.

## Tech stack

- **Python** — core logic
- **SQLite** — storage (via the `sqlite3` standard library)
- **pandas** — data transformation and aggregation
- **requests** — API ingestion
- **Streamlit** — dashboard / UI
- **Pokémon TCG API** — card and price data

## How to run

```bash
# 1. Clone and enter the repo
git clone https://github.com/lewisjones1809-arch/pokemon-inventory-tracker
cd pokemon-inventory-tracker

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
#    Open .env.example, paste your API key here:
#    POKEMON_API_KEY=your_key_here
#.   Rename .env.example -> .env

# 5. Set up the database schema
python3 create_db.py       

# 6. Run the dashboard
streamlit run main.py            
```

## Design decisions

A few choices that reflect deliberate engineering rather than defaults:

- **Derived inventory over stored state:** holdings are recomputed from immutable purchase/sale logs, so the data can't silently corrupt and can always be rebuilt.
- **FIFO cost basis:** chosen over average cost because purchase prices vary by an order of magnitude, making average meaningless; verified against hand-calculated cases including multi-lot and out-of-order-date scenarios.
- **Variant detection from price data:** which finishes exist is inferred from which price families are present, rather than from a brittle rarity-based heuristic.
- **Swappable data source:** ingestion is isolated behind a thin layer, so the price/card provider can be changed without touching the rest of the app.

## Use of AI

Claude has been used to assist in this project a handful of times. These are listed below for complete transparency:

- **Card Insert Failure Diagnostic:** 307 cards were not imported correctly from my existing TCGPowerTools inventory, so I tasked Claude with diagnosing the issue. Claude suggested 4 separate fixes, which I then allowed it to implement. These fixes were:
1. A manual mapping of some set names that the API does not recognise
2. Fixing collector numbers for trainer gallery cards and others with letters in the CN
3. Fixed promo imports and spotted a mismatch between my export and reality - Surging Sparks was incorrectly labelled as "Standard Series Promos" returning no results from the API.
4. Reverse holo insert even when API does not believe the card exists: inventory is the source of truth, the API doesn't always have pricing data for cards even when they exist.

## Roadmap

**Working in v1:**
- Card ingestion by set, price-history capture, variant detection
- FIFO valuation and P&L (tested)
- Derived inventory and dashboard
- CSV bulk import (English cards)

**In progress for v2:**
- Multi-language support (Japanese / Korean cards)
- Price-history charting in the UI
- Live card lookup in the purchase form

## Notes

This is a personal project built to manage a real collection. Card data and prices are sourced from third-party APIs; this project stores no copyrighted card text or imagerybeyond linking to the provider's hosted images.